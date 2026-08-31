from api_connect import supabase,fetch_categories
import streamlit as st
import pandas as pd 
from layout import clean_input
import app_logic as lg
#Fetch all historical transactions from the Supabase database
transactions = supabase.table("Transactions").select("*").execute().data

#Master dictionary grouping all unique, cleaned items (spaces removed, title-cased) into their respective categories.
categories_item = {"Food/Groceries" : ['Food', 'Bokku','Pastrie','Water','Egg','Drink','Fruit','Genngafoodstuff',
                                       'Gbengafoodstuff','Sweet','Snack','Groundnut','Tomato','Foodstuff',
                                       'Bread','Oil','Purewater','Bean','Pasterie'],
                   "Loans/Debts" : ['Loan','Loanrepay','Payback','Dadloan','Loanpayback'],
                   "Airtime/Data": ['Data','Airtime'],
                  "Savings/Investment" : ['Saving'],
                   "Salary" : ['Salary'],
                   "Travel" : ['Hotel'],
                   "Academics/School" : ['Printout','Book','Printing','Manual','Lamination'],
                   "Transport/Fuel" : ['Transport'],
                   "Gifts/Charity" : ['Giveaway','Birthday','Brithday'],
                   "Entertainment/Recreation" : ['Outing','Football'],
                   "Charges" : ['Transfer','Stampduty','Charge'],
                   "Others" : ['Cashback','Missing','Junk','Service','Keepbag','Uncategorised','Change','Bagrepair','Ga','Other','Control'],
                   "Business" : ['Sale'],
                   "Starting balance" : ['Startingbalance'],
                   "Scholarship" : ['Scholarship'],
                   "Tech events" : ['Hackaton'],
                   "Shopping/Personal items" : ['Earpiece','Airpod','Screenprotector','Sock','Vervecard'],
                   "Subscriptions" : ['Spotify'],
                   "Allowance" : ['Allowance','Companyallowance'],
                   "Personal care" : ['Soap','Haircut','Sunscreen'],
                   "Health/Medical" : ['Vitaminc'],
                   "Housing/Utilities" : []}
#Flips the dictionary to achieve a 1-to-1 mapping of individual items to their parent category. 
items_to_category = lg.item_to_category(categories_item)
old_transaction = pd.DataFrame(transactions)

#Apply cleaning function to generate a standardized 'Uniform_items' column , created using the item column
old_transaction["Uniform_items"] = lg.unify_column(old_transaction,"Item")
unique_uniform = old_transaction["Uniform_items"].unique()
st.write(len(unique_uniform))
master_cabinent = {}

unique_users = old_transaction["Username"].unique()
unique_users = unique_users.tolist()

#Create a nested dictionary ("master_cabinet") giving each user a dedicated section mapping their categories to their unique IDs
for users in unique_users:
    user_category = fetch_categories(users)
    master_cabinent[users] = user_category
#Cleaned the item column , stripped it and made it title to make it more uniform
lg.clean_column(old_transaction,"Item")
#Map each row of uniform items to a category , creating a "Category" column in the process
old_transaction["Category"] = old_transaction["Uniform_items"].map(items_to_category)

# Check for any row that didn't get a category mapped to it 
unmapped_items = old_transaction[old_transaction["Category"].isna()]
st.write("Missing from Dictionary:", unmapped_items["Uniform_items"].unique())
if unmapped_items.empty:
    #Map the category to categories_id specific to each user
    old_transaction["Categories_id"] = old_transaction.apply(lambda x : master_cabinent[x["Username"]][x["Category"]], axis=1)

    #Remove all the columns that wont be needed to send to supabase
    old_transaction = old_transaction.drop(columns=["Category","Uniform_items","id"])
    st.write(old_transaction)
    #upload_trans = old_transaction.to_dict(orient="records")
    #supabase.table("Transaction_v2").insert(upload_trans).execute()

    

