import streamlit as st
import pandas as pd
from api_connect import fetch_tx,fetch_budget,fetch_categories
from datetime import timedelta
import time
import layout
from layout import change_state,my_search_box
from edit_mode import editor_toggle
from stylist import format_df,format_amount,format_date
import app_logic as lg
from utils import arrange_category


layout.show_sidebar()

s_username = st.session_state.username
s_currency = st.session_state.currency
file_df = fetch_tx(username=s_username)
if file_df.empty:
    file_df = lg.default_file("Tx")
    tx_types = ["Initial balance"]
    st.markdown("You need to  record an initial balance before making transactions")
else:
    tx_types = ["Expense" , "Income" ,"Budget"]
st.session_state.df = file_df
st.session_state.df = lg.sort_data(st.session_state.df)
balance,_,_ = lg.calculate_balance(st.session_state.df)
balancd_metric = st.metric(label="Balance" ,value=format_amount(balance,0,s_currency), delta="balance",delta_arrow="off")

#Budget df 
budget_df = fetch_budget(username=s_username)
if budget_df.empty:
    budget_df = lg.default_file("Budget")
st.session_state.b_df = budget_df
st.session_state.b_df = lg.sort_data(st.session_state.b_df)

#Data entry interphase
if "tx_counter" not in st.session_state:
    st.session_state.tx_counter = 0
if "master_date" not in st.session_state:
    st.session_state.master_date = lg.get_default_time()

def date_stepper(step,date_value):
    if step == "+":
        st.session_state[date_value] += timedelta(days=1)
    elif step == "-":
          st.session_state[date_value] -= timedelta(days=1)
col_a,col_b,col_c = st.columns([1,2,1],gap="small")
with col_a:
    st.button("◀",on_click=date_stepper,args=("-","master_date"))
with col_b:
    date = st.date_input("Date",key="master_date",label_visibility="collapsed")
with col_c:
    st.button("▶",on_click=date_stepper,args=("+","master_date"))
item_key = "item_box"
cate_raw = fetch_categories(s_username)
cate_data = list(cate_raw.keys())
types = st.selectbox("Type",tx_types,key="types")
category_data = arrange_category(cate_data,types)
category = st.selectbox("Categories",category_data,key="categories")
if category == "Add Category":
    category = st.text_input("New Category",key="new_category")
item = my_search_box("Item",item_key,st.session_state.df["Item"],placeholder="Optional")
amount = st.number_input("Amount",step=100.0,key=f"tx_amount{+ st.session_state.tx_counter}")

if st.button("Add transactions"):
    valid_transaction = lg.transaction_logic(date,item,amount,types,category,s_username)
    if valid_transaction:
        st.success("Added!")
        st.session_state.tx_counter += 1
        change_state(item_key,"")
        time.sleep(0.5)
        st.rerun()
    else:
        st.warning("Enter an amount")
        time.sleep(0.5)
        st.rerun()

select_date = st.session_state.master_date
daily_table,day_in,day_out = lg.filtered_transaction(select_date,st.session_state.df,types)
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
            st.success(f"Money In: {format_amount(money_made,0,s_currency)} ")
        else:
            st.write(f"Money In: {format_amount(money_made,0,s_currency)} ")
    with col2:
        st.subheader("Expense")
        format_df(day_out[["Category","Amount"]],2,"Amount")
        money_lost = day_out["Amount"].sum()
        if money_lost > 0:
            st.error(f"Money Out: {format_amount(money_lost,0,s_currency)} ")
        else:
            st.write(f"Money Out: {format_amount(money_lost,0,s_currency)} ")
elif st.session_state.editor_switch:
    editor_toggle("Transaction")


b_df = st.session_state.b_df
b_df["Month"] = pd.to_datetime(b_df["Date"]).dt.to_period("M")  
b_months = b_df["Month"].unique() 
if "budget_toggle" not in st.session_state:
    st.session_state.budget_toggle = False 
b_toggle = st.toggle("Edit Budget" , key="budget_toggle", disabled=st.session_state.get("editor_switch",False))
if not st.session_state.budget_toggle:
    st.subheader("Budget")
    opt = st.selectbox("Select month" ,b_months, key="budget_months_for_app",format_func=format_date) 
    month_budget,_,_ = lg.filtered_transaction(opt,b_df,"Budget","Month")
    st.dataframe(month_budget[["Category" , "Amount"]].style.format(formatter = lambda x : format_amount(x,2,s_currency),subset=["Amount"]))
elif st.session_state.budget_toggle:
    editor_toggle("Budget")


















































