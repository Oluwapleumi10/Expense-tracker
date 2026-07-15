import pandas as pd 
import streamlit as st
from datetime import datetime,timedelta
from layout import clean_input
from api_connect import fetch_categories,add_category,add_transaction,fetch_user

BUDGET = "Budget"
TRANSACTION = "Transaction_v2"




default_time = datetime.now().date()

#To get a section of your dataframe
def get_filter_data(data,by_column,parameter):
    data = data[data[by_column] == parameter].reset_index(drop=True)
    return data

def sort_data(data,date_column="Date"):
    data[date_column] = pd.to_datetime(data[date_column],format="mixed").dt.date
    data = data.sort_values(by="Date",ascending=False).reset_index(drop=True)
    return data


#Logic created to calculate balance by substracting total expense from income 
@st.cache_data
def calculate_balance(data,type_column="Type",income_column="Income",expense_column="Expense",bal_column="Initial balance"):
    initial = data[data[type_column] == bal_column]["Amount"].sum()
    total_income = data[data[type_column] == income_column]["Amount"].sum()
    total_expense = data[data[type_column] == expense_column]["Amount"].sum()
    balance = (total_income + initial) - total_expense
    return balance,total_income,total_expense


#Create an empty file ,to be able to make calculations for users that have empty transaction
def default_file(types):
    if types == "Tx":
      file_df =  {"Date" : [default_time],
         "Category" : [""],
         "Item" : [""],
         "Amount" : [0],
         "Type" : [""],
          "Username" : [""]} 
    elif types == "Budget":
       file_df = {"Date" : [f"{default_time}"],
                 "Amount" : [0],
                 "Category" : [""],
                 "Username" : [""],}
    file_df = pd.DataFrame(file_df) 
    return file_df 


#Organize all the data entry points the user inputed into a dictionary
def data_clean(dates,items,amounts,typess,category,username):
    new_entry = {"Date" : str(dates),
        "Categories_id" : category,
         "Item" : clean_input(items),
         "Type" : typess,
         "Amount" : amounts,
         "Username" : username,} 
    return new_entry



def transaction_logic(date,item,amount,types,category,username):
    if types == "Budget":
      table_loc = BUDGET
    else:
       table_loc = TRANSACTION
    cate_raw = fetch_categories(username)
    cate_data = list(cate_raw.keys())
    if amount > 0:
      if category not in cate_data:
        new_category = {"Category_name" : category,"Username" : username}   
        category_id = add_category(new_category)
      else:
        category_id = cate_raw[category]
      transaction_data = data_clean(date,item,amount,types,category_id,username=username)
      add_transaction(transaction_data,table_loc)
      return True
    else:
        return False
    


def filtered_transaction(date,data,transaction_type,date_column="Date"):
    filtered_data = data[data[date_column] == date]
    if transaction_type == "Budget":
       return filtered_data,None,None
    else:
       filtered_in = filtered_data[filtered_data["Type"] == "Income"].reset_index(drop=True)
       filtered_out = filtered_data[filtered_data["Type"] == "Expense"].reset_index(drop=True)
       return filtered_data,filtered_in,filtered_out
