import streamlit as st
import pandas as pd
from api_connect import check_users,fetch_tx,supabase,fetch_budget,fetch_categories
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
    select_date = st.session_state.view_date_value
    b_df = st.session_state.b_df

    st.session_state.b_df["Month"] = st.session_state.b_df["Date"].dt.to_period("M")  
    b_months = st.session_state.b_df["Month"].unique()



    cate_raw = fetch_categories(username=s_username)
    cate_data = list(cate_raw.keys())
    cate_data.insert(1,"Add a Category")

    opt = None
    if trans_type == "Budget":
      opt = st.selectbox("Select month" ,b_months, key="budget_months",format_func=format_date) 
    type_data = {
      "Transaction" : {"session_state" : st.session_state.df , "date" : select_date, "table" : "Transaction_v2","clear" : fetch_tx.clear(),
                       "session_date" : "Date"},
      "Budget" : {"session_state" : st.session_state.b_df , "date" : opt, "table" : "Budget","clear" : fetch_budget.clear(),
                  "session_date" : "Month"}
    }
    usage = type_data.get(trans_type)
    edited_data= usage["session_state"][usage["session_state"][usage["session_date"]] == usage["date"]]
    edited_data = edited_data.reset_index(drop=True)
    old_ids = set(edited_data["id"].to_list())
    excluded_data = usage["session_state"][usage["session_state"][usage["session_date"]] != usage["date"]]
    final_edited = st.data_editor(edited_data, num_rows="dynamic", column_config={"id": None, "created_at": None, "Date": None, "Username": None,
                                  "Category" : st.column_config.SelectboxColumn(options=cate_data)}, hide_index=True,
                                  key="et_editor" )
    new_ids = set(final_edited["id"].to_list())
    if st.button("Save"):
        final_edited["Date"] = select_date.strftime("%Y-%m-%d")
        final_edited["Username"] = s_username
        final_edited["Category"] = final_edited["Category"].map(cate_raw)
        final_edited = final_edited.rename(columns={"Category":"Categories_id"})
        excluded_data["Category"] = excluded_data["Category"].map(cate_raw)
        excluded_data = excluded_data.rename(columns={"Category":"Categories_id"})
        delete_ids = list(old_ids - new_ids)
        merged_data = pd.concat([final_edited, excluded_data],ignore_index=True)
        for_upsert = final_edited.dropna(subset=["id"])
        new_rows = final_edited[final_edited["id"].isna()].drop(columns=["id","created_at"])
       
        #we do the editings for the budget right before upload
        if trans_type == "Budget":
          new_rows["Month"] = opt
          for_upsert = to_supabase(for_upsert)
          new_rows = to_supabase(new_rows)
        for_upsert = for_upsert.to_dict(orient="records")
        added_rows = new_rows.to_dict(orient="records")
        if added_rows:
         supabase.table(usage["table"]).insert(added_rows).execute()
        if for_upsert:
         supabase.table(usage["table"]).upsert(for_upsert).execute()
        if delete_ids:
         supabase.table(usage["table"]).delete().in_("id", delete_ids).execute()
        usage["session_state"] = merged_data
        st.success("Saved!")
        usage["clear"]
        time.sleep(1)
        st.rerun()