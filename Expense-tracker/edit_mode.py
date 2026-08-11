import streamlit as st
import pandas as pd
from api_connect import check_users,fetch_tx,supabase,fetch_budget,fetch_categories,edit_transaction
from datetime import datetime
import time
import layout
import string
import os
from utils import format_date

def editor_toggle(trans_type):
    def to_supabase(data):
        data["Date"] = data["Month"].dt.strftime("%Y-%m-01")
        data = data.drop(columns="Month")
        return data

    s_username = st.session_state.username
    select_date = st.session_state.master_date
    b_df = st.session_state.b_df
    
    st.session_state.b_df["Month"] = pd.to_datetime(st.session_state.b_df["Date"]).dt.to_period("M") 
    b_months = st.session_state.b_df["Month"].unique()

    # SAFETY NET 1: Defusing the "First Budget" Date Crash
    if len(b_months) == 0:
        current_month = pd.Period(datetime.now(), freq="M")
        b_months = [current_month]

    cate_raw = fetch_categories(username=s_username)
    cate_data = list(cate_raw.keys())
    opt = None
    if trans_type == "Budget":
        opt = st.selectbox("Select month" ,b_months, key="budget_months",format_func=format_date) 
        
    type_data = {
        "Transaction" : {"session_state" : st.session_state.df , "date" : select_date, "table" : "Transaction_v2",
        "session_date" : "Date"},
        "Budget" : {"session_state" : st.session_state.b_df , "date" : opt, "table" : "Budget",
        "session_date" : "Month"}
    }
    
    usage = type_data.get(trans_type)
    edited_data = usage["session_state"][usage["session_state"][usage["session_date"]] == usage["date"]]
    edited_data = edited_data.reset_index(drop=True)

    # SAFETY NET 2: Fix KeyError 'id' for completely empty transactions
    if "id" not in edited_data.columns:
        edited_data["id"] = None
        
    old_ids = set(edited_data["id"].dropna().to_list())
    excluded_data = usage["session_state"][usage["session_state"][usage["session_date"]] != usage["date"]]
    
    # Base configuration for both data editors
    dynamic_config = {
        "id": None, 
        "created_at": None, 
        "Date": None, 
        "Username": None,
        "Category" : st.column_config.SelectboxColumn(options=cate_data)
    }

    # SAFETY NET 3: Intelligent Type Restriction (Mirroring app.py)
    valid_types = []
    if trans_type == "Transaction":
        if "Initial balance" not in usage["session_state"]["Type"].unique():
            valid_types = ["Initial balance"]
        else:
            valid_types = ["Income", "Expense"]
            
        dynamic_config["Type"] = st.column_config.SelectboxColumn(options=valid_types)
    
    final_edited = st.data_editor(
        edited_data, 
        num_rows="dynamic", 
        column_config=dynamic_config, 
        hide_index=True,
        key="et_editor" 
    )
    
    if "id" not in final_edited.columns:
        final_edited["id"] = None
    new_ids = set(final_edited["id"].dropna().to_list())
    
    if st.button("Save"):
        # SAFETY NET 4: Validate Empty Categories and Invalid Types
        if "Category" in final_edited.columns and (final_edited["Category"].isnull().any() or (final_edited["Category"] == "").any()):
            st.warning("You have an empty category. Please fill out all categories before saving.")
            st.stop()
            
        if trans_type == "Transaction" and "Type" in final_edited.columns:
            if final_edited["Type"].isnull().any() or (final_edited["Type"] == "").any():
                st.warning("'Type' cannot be empty.")
                st.stop()
            if not final_edited["Type"].isin(valid_types).all():
                st.warning("Invalid 'Type' detected. Please select from the dropdown.")
                st.stop()

        final_edited["Date"] = select_date.strftime("%Y-%m-%d")
        final_edited["Username"] = s_username
        
        if "Category" in final_edited.columns:
            final_edited["Category"] = final_edited["Category"].map(cate_raw)
            final_edited = final_edited.rename(columns={"Category":"Categories_id"})
        
        delete_ids = list(old_ids - new_ids)
        for_upsert = final_edited.dropna(subset=["id"])
        
        new_rows = final_edited[final_edited["id"].isna()].drop(columns=["id","created_at"], errors="ignore")
        
        if trans_type == "Budget":
            new_rows["Month"] = opt
            for_upsert = to_supabase(for_upsert)
            new_rows = to_supabase(new_rows)
            
        for_upsert = for_upsert.to_dict(orient="records")
        added_rows = new_rows.to_dict(orient="records")
        edit_transaction(usage["table"],trans_type,added_rows,for_upsert,delete_ids)
        st.success("Saved!")
        time.sleep(0.5)
        st.rerun()