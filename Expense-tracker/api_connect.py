import streamlit as st
import pandas as pd
from supabase import create_client
import time
import httpx
import traceback
#For creating streamlit connetions with supabase
supabase = create_client(st.secrets["SUPABASE_URL"],st.secrets["SUPABASE_KEY"]) 

class SupaSafe:
   def __init__(self,supabase_client):
      self.db = supabase_client
      self.query = self.db
   
   def __getattr__(self, method_name):
      if not  hasattr(self.query,method_name):
       self.query = self.db
      def ghost_messenger(*args,**kwargs):
         self.query = getattr(self.query,method_name)(*args,**kwargs)
         return self 
    
      return ghost_messenger
   def execute(self):
      try:
        response = self.query.execute()
        self.query = self.db
        return response
      except httpx.RequestError:
         st.error("Your are offline")
         st.button("Try again",type="tertiary")
         self.query = self.db
         st.stop()
      except Exception as e:
         st.error("Something went wrong !")
         traceback.print_exc()
         st.button("Try again",type="tertiary")
         self.query = self.db
         st.stop()
supasafe = SupaSafe(supabase)

def check_users(user,password=None,mode=None):
    if mode == "verify":
      data = supasafe.table("Users").select("*").eq("Username",user).execute().data
    else:
        data = supasafe.table("Users").select("*").eq("Username",user).eq("Password",password).execute().data
    return data

def fetch_user(usern,mode=None):
    if mode == "verification":
       data = supasafe.table("Users").select("*").eq("Username",usern).execute().data
    else:
        data = supasafe.table("Users").select("id,Username").eq("Username",usern).execute().data
    return data


@st.cache_data
def fetch_tx(username):
    raw_data = supasafe.table("Transaction_v2").select("id,created_at,Date,Item,Type,Amount,Username,Categories(Category_name)").eq("Username" ,username).execute().data
    flat_data = pd.json_normalize(raw_data)
    flat_data = flat_data.rename(columns={"Categories.Category_name" : "Category"})
    return flat_data


@st.cache_data
def fetch_budget(username):
    raw_data = supasafe.table("Budget").select("id,created_at,Date,Amount,Username,Categories(Category_name)").eq("Username",username).execute().data
    budget_data = pd.json_normalize(raw_data)
    budget_data = budget_data.rename(columns={"Categories.Category_name":"Category"})
    return budget_data

@st.cache_data
def fetch_categories(username):
    raw_data = supasafe.table("Categories").select("id","Category_name").in_("Username",["System",username]).execute().data
    category_data = {box["Category_name"]:box["id"] for box in raw_data}
    return category_data

def change_currency(to,username):
    change = supasafe.table("Users").update({"Currency":to}).eq("Username",username).execute().data
    if change:
     st.session_state.currency = to
     st.success("Currency changed")
    else:
     st.warning("An error occured")
    time.sleep(0.7)

def add_transaction(transaction,table):
   if transaction["Type"] == "Budget":
      transaction["Date"] = transaction["Date"].strftime("%Y-%m-01")
      transaction.pop("Item",None)
      transaction.pop("Type",None)
      supasafe.table(table).insert(transaction).execute()
      fetch_budget.clear()
   else:
      supasafe.table(table).insert(transaction).execute()
      fetch_tx.clear()
def add_category(category,table):
   new_category_id = supasafe.table(table).insert(category).execute().data
   fetch_categories.clear()
   return new_category_id[0]["id"]

def edit_transaction(table,types,insert=None,upsert=None,delete_id=None):
    if insert:
        supasafe.table(table).insert(insert).execute()
    if upsert:
        supasafe.table(table).upsert(upsert).execute()
    if delete_id:
        supasafe.table(table).delete().in_("id", delete_id).execute()
    if types == "Budget":
        fetch_budget.clear()
    else:
        fetch_tx.clear()