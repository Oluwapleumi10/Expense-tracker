import time
import streamlit as st
from difflib import get_close_matches
from st_keyup import st_keyup
from datetime import datetime,timedelta
from utils import arrange_category
def clean_input(input):
   clean = input.strip()
   if clean == "":
    clean = "Others"
   return clean.title()


def change_state(state,value):
    st.session_state[state] = value
    st.session_state[f"{state}_counter"] += 1


def my_search_box(label,keys,data,**kwargs):
    if f"{keys}_counter"not in st.session_state:
        st.session_state[f"{keys}_counter"] = 0
    # The Wrench: This tells the browser to pull the suggestions up, closing the gap
    keyup = st_keyup(label,st.session_state.get(keys,""),key=f"keyup_{st.session_state[f"{keys}_counter"]}",**kwargs)
    matching_list = []
    if keyup:
      uniform_data = []
      for datum in data.unique():
        datum = datum.title()
        uniform_data.append(datum)
        if keyup.title() in datum:
          matching_list.append(datum)
          close_matches = get_close_matches(keyup.title(),uniform_data,cutoff=0.7)
          matching_list.extend(close_matches)
      match_unique = list(set(matching_list))
      display_container = get_close_matches(keyup,match_unique,cutoff=1)
      pixels = len(match_unique)
      if pixels <= 3:
        height = pixels * 60
      else:
        height = 180
      if match_unique and not display_container:
        with st.container(height=height):
          for item in match_unique:
            st.button(f"{item}",type="tertiary",use_container_width=True,on_click= change_state,args=(keys,item),key=f"{item}")
    return keyup

@st.fragment
def data_entry(key,data,tx_types,cat_data):
  default_time = datetime.now().date()
  if "master_date" not in st.session_state:
    st.session_state.master_date = default_time
  col_a,col_b,col_c = st.columns([1,2,1],gap="small")
  def date_stepper(step):
      if step == "+":
          st.session_state.master_date += timedelta(days=1)
      elif step == "-":
          st.session_state.master_date -= timedelta(days=1)
  with col_a:
      st.button("◀",on_click=date_stepper,args=("-",))
  with col_b:
      date = st.date_input("Date",key="master_date",label_visibility="collapsed")
  with col_c:
      st.button("▶",on_click=date_stepper,args=("+",))
  types = st.selectbox("Type",tx_types,key="types")
  category_data = arrange_category(cat_data,types)
  category = st.selectbox("Categories",category_data,key="categories")
  if category == "Add Category":
      category = st.text_input("New Category",key="new_category")  
  item = my_search_box("Item",key,data,placeholder="Optional")
  amount = st.number_input("Amount",step=100.0,key=f"tx_amount{+ st.session_state.tx_counter}")
  return  date ,types , category , item , amount





def show_sidebar():
   with st.sidebar:
         controller = st.session_state.controller
         st.write(f"You are logged in as {st.session_state.get("username","username")}")
         if st.button("Log out"):
            controller.set("saved_username" , "", max_age = 0)
            time.sleep(1)
            st.session_state.username = {}
            preserved = ["username","controller"]
            for key in st.session_state.keys():
              if key not in preserved:
                del key
            st.rerun()