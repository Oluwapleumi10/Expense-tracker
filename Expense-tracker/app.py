import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
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
  user_db = st.secrets["Users"]
   with tabs1:
       username = st.text_input("Username",key="Username")
       password = st.text_input("Password",key="Password",type="password")
       if st.button("Login"):
           if  username in user_db and user_db["username"] == password:
              st.session_state.username = username
              st.rerun()
           else:
               st.error("Wrong password or username")
   with tabs2:
       new_username = st.text_input("New username",key=f"Username{st.session_state.reg_counter}")
       new_password = st.text_input("New password",key=f"Passowrd{st.session_state.reg_counter}",type="password")
       if st.button("Register"):
           if len(new_password) < 9 or  not any( char in new_password for char  in string.punctuation):
               st.error("Password can't be lesser than 9 characters and must contain a special character")
               time.sleep(2.5)
               st.rerun()
           else:
            if new_username  in user_db:
                st.error("Username already taken")
            else: 
                    st.success("Account successfully created , go to login page")
                    time.sleep(1.5)
                    st.session_state.reg_counter += 1
                    st.rerun()
   st.stop()

layout.show_sidebar()
        
    

try:
    file_df = pd.read_csv(f"{st.session_state.username}_expense.csv")
except:
    file_df = pd.DataFrame(
      {"Date" : [],
         "Item" : [],
         "Amount" : [],
         "Type" : [] }  
    )

if "df" not in st.session_state:
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
    new_entry = pd.DataFrame(
        {"Date" : [dates],
         "Item" : [items],
         "Amount" : [amounts],
         "Type" : [typess] } )
    st.session_state.df = pd.concat([st.session_state.df,new_entry] , ignore_index=True)
    return  st.session_state.df
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
        saved_df.to_csv(f"{st.session_state.username}_expense.csv",index=False)
        st.success("Added!")
        if types == "Initial balance":
            item = "Starting balance"
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
if "toggle" not in st.session_state:
   toggle = st.toggle("Edit mode",key="editor_switch")
if not st.session_state.editor_switch:
    col1,col2 = st.columns(2)
    with col1:
        st.title("Income")
        st.dataframe(day_in.drop(columns= ["Month","Type","Week","Day"],errors="ignore"))
        money_made = day_in["Amount"].sum()
        if money_made > 0:
            st.success(f"Total money in today is:  ₦{money_made:,.2f} ")
        else:
            st.write(f"Total money in today is:  ₦{money_made:,.2f} ")
    with col2:
        st.title("Expense")
        st.dataframe(day_out.drop(columns= ["Month","Type","Week","Day"],errors="ignore"))
        money_lost = day_out["Amount"].sum()
        if money_lost > 0:
            st.error(f"Total money out today is: ₦{money_lost:,.2f} ")
        else:
            st.write(f"Total money out today is: ₦{money_lost:,.2f} ")
elif st.session_state.editor_switch:
    edited_data = st.session_state.df[st.session_state.df["Date"] == select_date ].drop(columns= ["Month","Week","Day"],errors="ignore")
    exculded_data = st.session_state.df[st.session_state.df["Date"] != select_date ].drop(columns= ["Month","Week","Day"],errors="ignore")
    final_edited = st.data_editor(edited_data,num_rows="dynamic")
    if st.button("Save"):
        final_edited = pd.DataFrame(final_edited)
        final_excluded = pd.DataFrame(exculded_data)
        final_data = pd.concat([final_edited,final_excluded],ignore_index=True)
        final_data.to_csv(f"{st.session_state.username}_expense.csv",index=False)
        st.session_state.df = final_data
        st.success("Saved!")
        time.sleep(1.5)
        st.rerun()
        
        


st.title("Budget")
st.dataframe(budget.drop(columns= ["Month","Type","Week","Day"],errors="ignore"))












