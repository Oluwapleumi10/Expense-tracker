import streamlit as st
import pandas as pd
from api_connect import fetch_tx,supabase,fetch_budget,fetch_categories
from datetime import datetime,timedelta
import time
import layout
from utils import format_date
from edit_mode import editor_toggle


st.title("Expense Tracker")
layout.show_sidebar()

s_username = st.session_state.username
file_df = fetch_tx(username=s_username)
if file_df.empty:
    file_df =  {"Date" : ["2000-01-01"],
         "Category" : [""],
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
#Budget df 
budget_df = fetch_budget(username=s_username)
if budget_df.empty:
    budget_df = {"Date" : ["2000-01-01"],
                 "Amount" : [0],
                 "Category" : [""],
                 "Username" : [""],}
    budget_df = pd.DataFrame(budget_df)
b_df = budget_df
st.session_state.b_df = b_df
st.session_state.b_df["Date"] = pd.to_datetime(st.session_state.b_df["Date"],format="mixed")#.dt.date
st.session_state.b_df = st.session_state.b_df.sort_values(by="Date" , ascending=False).reset_index(drop=True)
#Creating the add transaction function
def add_transaction(dates,items,amounts,typess,category):
    new_entry = {"Date" : str(dates),
        "Categories_id" : category,
         "Item" : items,
         "Type" : typess,
         "Amount" : amounts,
         "Username" : s_username,} 
    if new_entry["Type"] == "Budget":
      new_entry["Date"] = dates.strftime("%Y-%m-01")
      new_entry.pop("Item",None)
      new_entry.pop("Type",None)
      supabase.table("Budget").insert(new_entry).execute()
    else:
      supabase.table("Transaction_v2").insert(new_entry).execute()
cate_raw = fetch_categories(username=s_username)
cate_data = list(cate_raw.keys())
cate_data.insert(1,"Add a Category")
cate_data.remove("Starting balance")
 
tx_types = ["Expense" , "Income" ,"Budget"]
if "Initial balance" not in st.session_state.df["Type"].unique():
    tx_types = ["Initial balance"]
    cate_data = ["Starting balance"]
    st.write("You need to  record an initial balance first to start making transaction")
if "tx_counter" not in st.session_state:
    st.session_state.tx_counter = 0
if "master_date" not in st.session_state:
    st.session_state.master_date = datetime.now().date()

col_a,col_b,col_c = st.columns([1,2,1],gap="small")
def date_stepper(step):
    if step == "+":
        st.session_state.master_date += timedelta(days=1)
    elif step == "-":
        st.session_state.master_date -= timedelta(days=1)
with col_a:
    st.button("◀",on_click=date_stepper,args=("-",))
with col_b:
    date = st.date_input("Date",key="master_date",label_visibility="collapsed")
with col_c:
    st.button("▶",on_click=date_stepper,args=("+",))
types = st.selectbox("Type",tx_types,key="types")
category = st.selectbox("Categories",cate_data,key="categories")
if category == "Add a Category":
    category = st.text_input("New Category",key="new_category")
item = st.text_input("Item(Optional)",placeholder="A short description of the category",key=f"tx_item{+ st.session_state.tx_counter}")
amount = st.number_input("Amount",step=100.0,key=f"tx_amount{+ st.session_state.tx_counter}")
if st.button("Add transactions"):
    if amount > 0 :
        if category not in cate_data:
            new_category = {"Category_name":category,"Username":s_username}
            new_cate_data = supabase.table("Categories").insert(new_category).execute().data
            category = new_cate_data[0]["id"]
        else:
            category = cate_raw[category]
        add_transaction(date,item,amount,types,category)
        st.success("Added!")
        fetch_tx.clear()
        fetch_budget.clear()
        st.session_state.tx_counter += 1
        time.sleep(1)
        st.rerun()
    else:
        st.warning("Enter an amount and item")
        time.sleep(1)
        st.rerun()
        
if "view_date_value" not in st.session_state:
    st.session_state.view_date_value = pd.Timestamp.today().date()

select_date = st.session_state.master_date
daily_table = st.session_state.df[st.session_state.df["Date"] == select_date].drop(columns="Date")
day_out = daily_table[daily_table["Type"] == "Expense"].reset_index(drop=True)
day_in = daily_table[daily_table["Type"] == "Income"].reset_index(drop=True)
if "editor_switch" not in st.session_state:
    st.session_state.editor_switch = False
toggle = st.toggle("Edit mode", key="editor_switch",disabled=st.session_state.get("budget_toggle",False))
if not st.session_state.editor_switch:
    col1,col2 = st.columns(2)
    with col1:
        st.title("Income")
        st.dataframe(day_in[["Category","Amount",]])
        money_made = day_in["Amount"].sum()
        if money_made > 0:
            st.success(f"Total money in today is:  ₦{money_made:,.2f} ")
        else:
            st.write(f"Total money in today is:  ₦{money_made:,.2f} ")
    with col2:
        st.title("Expense")
        st.dataframe(day_out[["Category","Amount"]])
        money_lost = day_out["Amount"].sum()
        if money_lost > 0:
            st.error(f"Total money out today is: ₦{money_lost:,.2f} ")
        else:
            st.write(f"Total money out today is: ₦{money_lost:,.2f} ")
elif st.session_state.editor_switch:
    editor_toggle("Transaction")


b_df = st.session_state.b_df
b_df["Month"] = b_df["Date"].dt.to_period("M")  
b_months = b_df["Month"].unique() 
if "budget_toggle" not in st.session_state:
    st.session_state.budget_toggle = False 
b_toggle = st.toggle("Edit Budget" , key="budget_toggle", disabled=st.session_state.get("editor_switch",False))
if not st.session_state.budget_toggle:
    st.title("Budget")
    opt = st.selectbox("Select month" ,b_months, key="budget_months_for_app",format_func=format_date)              
    display_df = b_df[b_df["Month"] == opt]
    st.dataframe(display_df[["Category" , "Amount"]])
elif st.session_state.budget_toggle:
    editor_toggle("Budget")




















































