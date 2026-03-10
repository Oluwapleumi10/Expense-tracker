import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from supabase import create_client
import time
import layout
import string
import os



st.title("Expense Tracker")
supabase = create_client(st.secrets["SUPABASE_URL"],st.secrets["SUPABASE_KEY"])   
if "username" not in st.session_state:
    st.session_state.username = {}
if "reg_counter" not in st.session_state:
    st.session_state.reg_counter = 0
if not st.session_state.username:
   tabs1,tabs2 = st.tabs(["Login","Registration"])
   with tabs1:
       users = supabase.table("Users").select("*").execute().data
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
file_df = supabase.table("Transactions").select("*").eq("Username" ,s_username) .execute().data
if not file_df:
    file_df =  {"Date" : ["2000-01-01"],
         "Item" : [""],
         "Amount" : [0],
         "Type" : [""],
          "Username" : [s_username]}  
file_df = pd.DataFrame(file_df)
file_df.columns = [col.capitalize() for col in file_df.columns]
#if "df" not in st.session_state:
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
    st.rerun()
tx_types = ["Expense" , "Income" ,"Budget"]
if "tx_counter" not in st.session_state:
    st.session_state.tx_counter = 0
if "Initial balance" not in st.session_state.df["Type"].unique():
    tx_types.append("Initial balance")

date = st.date_input("Date")
types = st.selectbox("Type",tx_types)
if types == "Initial balance":
    item = "Starting balance"
else:
    item = st.text_input("Item",key= 0 + st.session_state.tx_counter)
amount = st.number_input("Amount",step=100.0,key= 1000 + st.session_state.tx_counter)

    



if st.button("Add transactions"):
    if amount > 0 and item:
        saved_df = add_transaction(date,item,amount,types)
        st.success("Added!")
        #if types == "Initial balance":
            #item = "Starting balance"
        st.session_state.tx_counter += 1
        time.sleep(1.5)
        st.rerun()
    else:
        st.warning("Enter an amount and item")
        time.sleep(2.5)
        st.rerun()



select_date = st.date_input("Select a date")
daily_table = st.session_state.df[st.session_state.df["Date"] == select_date ].drop(columns="Date")
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
    edited_data = st.session_state.df[st.session_state.df["Date"] == select_date][["Item" ,"Amount" , "Type"]]
    excluded_data = st.session_state.df[st.session_state.df["Date"] != select_date ][["Item" , "Amount" , "Type"]]
    final_edited = st.data_editor(edited_data,num_rows="dynamic")
    if st.button("Save"):
        final_data = pd.concat([final_edited,excluded_data],ignore_index=True)
        supabase.table("Transactions").delete().eq("Username", s_username).eq("Date" , str(select_date)).execute()
        edited_rows = final_edited[["Date" ,"Item" ,"Amount" , "Type" , "Username" ]].to_dict(orient="records")
        supabase.table("Transactions").insert(edited_rows).execute()
        st.session_state.df = final_data
        st.success("Saved!")
        time.sleep(1.5)
        st.rerun()
        
        

st.dataframe(final_edited)
st.title("Budget")
st.dataframe(budget[["Item" , "Amount"]])












































