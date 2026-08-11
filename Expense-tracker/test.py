import pandas as pd 
import streamlit as st
from datetime import datetime,timedelta
from difflib import get_close_matches
from api_connect import fetch_categories
def arrange_category(user,tx_type):
    income_cate = ["Salary","Allowance","Savings/Investment"]
    expense_cate = ["Food/Groceries","Housing/Utilities","Transport/Fuel","Personal care","Health/Medical",
                    "Shopping/Personal items", "Airtime/Data","Subscriptions","Academics/School","Gifts/Charity",
                    "Entertainment/Recreation","Loans/Debts","Charges"]
    cate_raw = fetch_categories(user)
    cate = list(cate_raw.keys())
    if tx_type == "Income":
        income_cate.extend(expense_cate)
        cate_data = income_cate
    else:
        cate_data = expense_cate.extend(income_cate)
        cate_data = expense_cate
    for cat in cate:
        if cat not in cate_data:
            cate_data.append(cat)
    cate_data.remove("Starting balance")
    cate_data.insert("Add Category")
    return cate_data
