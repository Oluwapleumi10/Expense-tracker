from api_connect import supabase,fetch_categories
import streamlit as st
import pandas as pd 
transactions = supabase.table("Transactions").select("*").execute().data
item_to_category = {
    "Starting balance": "Starting balance",
    "Transport": "Transport/Fuel",
    "Airtime": "Airtime/Data",
    "Data": "Airtime/Data",
    "Spotify": "Subscriptions",
    "Allowance": "Allowance",
    "Company Allowance": "Allowance",
    "Cash back": "Cash back",
    "Cashback": "Cash back",
    "Salary": "Salary",
    "Savings": "Savings/Investment",
    "Give away": "Give away",
    "Giveaway": "Give away",
    "food": "Food/Groceries",
    "Food": "Food/Groceries",
    "Drinks": "Food/Groceries",
    "drink": "Food/Groceries",
    "Fruit": "Food/Groceries",
    "Egg": "Food/Groceries",
    "Snack": "Food/Groceries",
    "Pastries": "Food/Groceries",
    "Sweets": "Food/Groceries",
    "Gbenga food stuff": "Food/Groceries",
    "Gennga foodstuffs": "Food/Groceries",
    "Bokku": "Food/Groceries",
    "Pure water": "Essentials",
    "Water": "Essentials",
    "Earpiece": "Essentials",
    "Dad loan": "Loans/debts",
    "Loan": "Loans/debts",
    "Loan repay": "Loans/debts",
    "Loan Repay": "Loans/debts",
    "Payback": "Loans/debts",
    "Stamp duty": "Charges",
    "Transfer": "Charges",
    "Hackaton": "Tech Events",
    "Scholarship": "Scholarship",
    "Junk": "Junk",
    "Hotel": "Travel",
    "Sales": "Business",
    "outing": "Entertainment",
    "Birthday": "Entertainment",
    "Football": "Entertainment",
    "Print out": "Academics/School",
    "Keep Bag": "Others",
    "Missing": "Others",
    "Uncategorised": "Others"
}
master_cabinent = {}
old_trans = pd.DataFrame(transactions)
unique_users = old_trans["Username"].unique()
unique_users = unique_users.tolist()
for users in unique_users:
    user_category = fetch_categories(users)
    master_cabinent[users] = user_category
old_trans["Item"] = old_trans["Item"].str.strip()
old_trans["Category"] = old_trans["Item"].map(item_to_category)
# Add these two lines 
unmapped_items = old_trans[old_trans["Category"].isna()]
st.write("Missing from Dictionary:", unmapped_items["Item"].unique())
old_trans["Categories_id"] = old_trans.apply(lambda x : master_cabinent[x["Username"]][x["Category"]], axis=1)
old_trans = old_trans.drop(columns="Category")
st.write(old_trans)
# upload_trans = old_trans.to_dict(orient="records")
# supabase.table("Transaction_v2").insert(upload_trans).execute()
    

