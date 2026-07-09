import streamlit as st
import pandas as pd
from api_connect import fetch_tx,supasafe,fetch_budget,fetch_categories,add_category,add_transaction
from datetime import datetime,timedelta
import time
import layout
from layout import clean_input,change_state,data_entry
from utils import format_date,format_amount
from edit_mode import editor_toggle
from stylist import format_df
import app_logic as lg
layout.show_sidebar()

s_username = st.session_state.username
file_df = fetch_tx(username=s_username)
if file_df.empty:
    file_df = lg.default_file("Tx")
#file_df.columns = [col.capitalize() for col in file_df.columns]
df = file_df
st.session_state.df = df
st.session_state.df["Date"] = pd.to_datetime(st.session_state.df["Date"],format="mixed").dt.date
st.session_state.df = st.session_state.df.sort_values(by="Date" , ascending=False).reset_index(drop=True)
initial = st.session_state.df[st.session_state.df["Type"] == "Initial balance"]["Amount"].sum()
total_income = st.session_state.df[st.session_state.df["Type"] == "Income"]["Amount"].sum()
total_expense = st.session_state.df[st.session_state.df["Type"] == "Expense"]["Amount"].sum()
balance = (total_income+initial) - total_expense
st.metric(label="Balance" ,value=format_amount(balance,0), delta="balance",delta_arrow="off")
#Budget df 
default_time = datetime.now().date()
budget_df = fetch_budget(username=s_username)
if budget_df.empty:
    budget_df = {"Date" : [f"{default_time}"],
                 "Amount" : [0],
                 "Category" : [""],
                 "Username" : [""],}
    budget_df = pd.DataFrame(budget_df)


b_df = budget_df
st.session_state.b_df = b_df
st.session_state.b_df["Date"] = pd.to_datetime(st.session_state.b_df["Date"],format="mixed")#.dt.date
st.session_state.b_df = st.session_state.b_df.sort_values(by="Date" , ascending=False).reset_index(drop=True)
#Creating the add transaction function
def data_clean(dates,items,amounts,typess,category):
    new_entry = {"Date" : str(dates),
        "Categories_id" : category,
         "Item" : clean_input(items),
         "Type" : typess,
         "Amount" : amounts,
         "Username" : s_username,} 
    return new_entry
cate_raw = fetch_categories(s_username)
cate_data = list(cate_raw.keys())
tx_types = ["Expense" , "Income" ,"Budget"]
if "Initial balance" not in st.session_state.df["Type"].unique():
    tx_types = ["Initial balance"]
    st.markdown("You need to  record an initial balance before making transactions")
if "tx_counter" not in st.session_state:
    st.session_state.tx_counter = 0
if "master_date" not in st.session_state:
    st.session_state.master_date = default_time
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
item_key = "item_box"
types,category,item,amount = data_entry(item_key,st.session_state.df["Item"],tx_types,cate_data)
if st.button("Add transactions"):
    if amount > 0 :
        if types == "Budget":
            table_loc = "Budget"
        else:
            table_loc = "Transaction_v2"
        if category not in cate_data:
            new_category = {"Category_name":category,"Username":s_username}
            category = add_category(new_category)#<- i didnt add the second parameter
        else:
            category = cate_raw[category]
        transaction_data = data_clean(date,item,amount,types,category)
        add_transaction(transaction_data,table_loc)
        st.success("Added!")
        st.session_state.tx_counter += 1
        change_state(item_key,"")
        time.sleep(0.5)
        st.rerun()
    else:
        st.warning("Enter an amount")
        time.sleep(0.5)
        st.rerun()
        
#if "view_date_value" not in st.session_state:
    #st.session_state.view_date_value = pd.Timestamp.today().date()

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
        st.subheader("Income")
        format_df(day_in[["Category","Amount"]],2,"Amount")
        money_made = day_in["Amount"].sum()
        if money_made > 0:
            st.success(f"Money In: {format_amount(money_made,0)} ")
        else:
            st.write(f"Money In: {format_amount(money_made,0)} ")
    with col2:
        st.subheader("Expense")
        format_df(day_out[["Category","Amount"]],2,"Amount")
        money_lost = day_out["Amount"].sum()
        if money_lost > 0:
            st.error(f"Money Out: {format_amount(money_lost,0)} ")
        else:
            st.write(f"Money Out: {format_amount(money_lost,0)} ")
elif st.session_state.editor_switch:
    editor_toggle("Transaction")


b_df = st.session_state.b_df
b_df["Month"] = b_df["Date"].dt.to_period("M")  
b_months = b_df["Month"].unique() 
if "budget_toggle" not in st.session_state:
    st.session_state.budget_toggle = False 
b_toggle = st.toggle("Edit Budget" , key="budget_toggle", disabled=st.session_state.get("editor_switch",False))
if not st.session_state.budget_toggle:
    st.subheader("Budget")
    opt = st.selectbox("Select month" ,b_months, key="budget_months_for_app",format_func=format_date)              
    display_df = b_df[b_df["Month"] == opt]
    st.dataframe(display_df[["Category" , "Amount"]].style.format(formatter = lambda x : format_amount(x,2),subset=["Amount"]))
elif st.session_state.budget_toggle:
    editor_toggle("Budget")




















































