import streamlit as st
import pandas as pd
from supabase import create_client

supabase = create_client(st.secrets["SUPABASE_URL"],st.secrets["SUPABASE_KEY"]) 

@st.cache_data
def fetch_users():
    fetch = supabase.table("Users").select("*").execute().data
    return fetch

@st.cache_data
def fetch_tx(username):
    raw_data = supabase.table("Transactions").select("*").eq("Username" ,username).execute().data
    return raw_data 
