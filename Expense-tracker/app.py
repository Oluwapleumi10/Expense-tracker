import streamlit as st
import pandas as pd
from api_connect import fetch_users,fetch_tx,supabase
from datetime import datetime
import time
import layout
import string
import os



st.title("Expense Tracker")
if "username" not in st.session_state:
    st.session_state.username = {}
if "reg_counter" not in st.session_state:
    st.session_state.reg_counter = 0
if not st.session_state.username:
   tabs1,tabs2 = st.tabs(["Login","Registration"])
   with tabs1:
       users = fetch_users()
       username = st.text_input("Username",key="Username")
       password = st.text_input("Password",key="Password",type="password")
       if st.button("Login"):
           if any(u["Username"] == username and u["Password"] == password for u in users):
              st.session_state.username = username
              st.rerun()
           else:
               st.error("Wrong password or username")
   with tabs2:
       new_username = st.text_input("New username",key=f"Username{st.session_state.reg_counter}")
       new_password = st.text_input("New password",key=f"Password{st.session_state.reg_counter}",type="password")
       if st.button("Register"):
           if len(new_password) < 9 or  not any( char in new_password for char  in string.punctuation):
               st.error("Password can't be lesser than 9 characters and must contain a special character")
               time.sleep(2.5)
               st.rerun()
           else:
            if any(u["Username"] == new_username for u in users):
                st.error("Username already taken")
            else:
                supabase.table("Users").insert({"Username" : new_username , "Password" : new_password}).execute()
                st.success("Account successfully created , go to login page")
                time.sleep(1.5)
                st.session_state.reg_counter += 1
                st.rerun()
   st.stop()

layout.show_sidebar()


s_username = st.session_state.username
file_df = fetch_tx(username=s_username)
if not file_df:
    file_df =  {"Date" : ["2000-01-01"],
         "Item" : [""],
         "Amount" : [0],
         "Type" : [""],
          "Username" : [s_username]}  
file_df = pd.DataFrame(file_df)
#file_df.columns = [col.capitalize() for col in file_df.columns]
df = file_df
st.session_state.df = df

st.session_state.df["Date"] = pd.to_datetime(st.session_state.df["Date"],format="mixed").dt.date
st.session_state.df = st.session_state.df.sort_values(by="Date" , ascending=False).reset_index(drop=True)
initial = st.session_state.df[st.session_state.df["Type"] == "Initial balance"]["Amount"].sum()
total_income = st.session_state.df[st.session_state.df["Type"] == "Income"]["Amount"].sum()
total_expense = st.session_state.df[st.session_state.df["Type"] == "Expense"]["Amount"].sum()
balance = (total_income+initial) - total_expense
st.metric(label="Balance" ,value=f"₦ {balance:,.2f}", delta="balance",delta_arrow="off")
def add_transaction(dates,items,amounts,typess):
    new_entry = {"Date" : str(dates),
         "Item" : items,
         "Amount" : amounts,
         "Type" : typess,
         "Username" : s_username,} 
    supabase.table("Transactions").insert(new_entry).execute()
with st.form("Transaction form", clear_on_submit=True):  
    tx_types = ["Expense" , "Income" ,"Budget"]
    if "Initial balance" not in st.session_state.df["Type"].unique():
        tx_types.append("Initial balance")

    date = st.date_input("Date",key="choose_date")
    types = st.selectbox("Type",tx_types,key="types")
    if types == "Initial balance":
        item = "Starting balance"
    else:
        item = st.text_input("Item",key="tx_item")
    amount = st.number_input("Amount",step=100.0,key="tx_amount")
    if st.form_submit_button("Add transactions"):
        if amount > 0 and item:
            add_transaction(date,item,amount,types)
            st.success("Added!")
            fetch_tx.clear()
            time.sleep(1)
            st.rerun()
        else:
            st.warning("Enter an amount and item")
            time.sleep(2.5)
            st.rerun()
        
if "view_date_value" not in st.session_state:
    st.session_state.view_date_value = pd.Timestamp.today().date()

select_date = st.date_input(
    "Select a date", 
    value=st.session_state.view_date_value,  # ← Use the saved value!
    key="view_date"
)

# Update session state whenever the user changes it
st.session_state.view_date_value = select_date
daily_table = st.session_state.df[st.session_state.df["Date"] == select_date].drop(columns="Date")
day_out = daily_table[daily_table["Type"] == "Expense"].reset_index(drop=True)
day_in = daily_table[daily_table["Type"] == "Income"].reset_index(drop=True)
budget = daily_table[daily_table["Type"] == "Budget"].reset_index(drop=True)
if "editor_switch" not in st.session_state:
    st.session_state.editor_switch = False
toggle = st.toggle("Edit mode", key="editor_switch")
if not st.session_state.editor_switch:
    col1,col2 = st.columns(2)
    with col1:
        st.title("Income")
        st.dataframe(day_in[["Item" , "Amount"]])
        money_made = day_in["Amount"].sum()
        if money_made > 0:
            st.success(f"Total money in today is:  ₦{money_made:,.2f} ")
        else:
            st.write(f"Total money in today is:  ₦{money_made:,.2f} ")
    with col2:
        st.title("Expense")
        st.dataframe(day_out[["Item" ,"Amount"]])
        money_lost = day_out["Amount"].sum()
        if money_lost > 0:
            st.error(f"Total money out today is: ₦{money_lost:,.2f} ")
        else:
            st.write(f"Total money out today is: ₦{money_lost:,.2f} ")
elif st.session_state.editor_switch:
    edited_data = st.session_state.df[st.session_state.df["Date"] == select_date]
    edited_data = edited_data.reset_index(drop=True)
    old_ids = set(edited_data["id"].to_list())
    excluded_data = st.session_state.df[st.session_state.df["Date"] != select_date]
    final_edited = st.data_editor(edited_data, num_rows="dynamic", column_config={"id": None, "created_at": None, "Date": None, "Username": None}, hide_index=True,
                                 key="et_editor" )
    new_ids = set(final_edited["id"].to_list())
    if st.button("Save"):
        final_edited["Date"] = select_date.strftime("%Y-%m-%d")
        final_edited["Username"] = s_username
        delete_ids = list(old_ids - new_ids)
        merged_data = pd.concat([final_edited, excluded_data], ignore_index=True)
        for_upsert = final_edited.dropna(subset=["id"])
        for_upsert = for_upsert.to_dict(orient="records")
        new_rows = final_edited[final_edited["id"].isna()].drop(columns=["id","created_at"])
        added_rows = new_rows.to_dict(orient="records")
        st.write(added_rows)
        if added_rows:
         supabase.table("Transactions").insert(added_rows).execute()
        if for_upsert:
         supabase.table("Transactions").upsert(for_upsert).execute()
        if delete_ids:
         supabase.table("Transactions").delete().in_("id", delete_ids).execute()
        st.session_state.df = merged_data
        st.success("Saved!")
        fetch_tx.clear()
        time.sleep(1.5)
        st.rerun()


st.title("Budget")
st.dataframe(budget[["Item" , "Amount"]])


















































