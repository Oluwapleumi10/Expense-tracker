
import streamlit as st
import pandas as pd
from supabase import create_client
#For creating streamlit connetions with supabase
supabase = create_client(st.secrets["SUPABASE_URL"],st.secrets["SUPABASE_KEY"]) 

@st.cache_data
def fetch_users():
    fetch = supabase.table("Users").select("*").execute().data
    return fetch


@st.cache_data
def fetch_tx(username):
    raw_data = supabase.table("Transaction_v2").select("id,created_at,Date,Item,Type,Amount,Username,Categories(Category_name)").eq("Username" ,username).execute().data
    flat_data = pd.json_normalize(raw_data)
    flat_data = flat_data.rename(columns={"Categories.Category_name" : "Category"})
    return flat_data


@st.cache_data
def fetch_budget(username):
    raw_data = supabase.table("Budget").select("id,created_at,Date,Item,Type,Amount,Username,Categories(Category_name)").eq("Username",username).execute().data
    budget_data = pd.json_normalize(raw_data)
    budget_data = budget_data.rename(columns={"Categories.Category_name":"Category"})
    return budget_data


def fetch_categories(username):
    raw_data = supabase.table("Categories").select("id","Category_name").in_("Username",["System",username]).execute().data
    category_data = {box["Category_name"]:box["id"] for box in raw_data}
    return category_data
