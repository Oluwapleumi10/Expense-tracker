import streamlit as st
from api_connect import fetch_user,supasafe,change_currency
from utils import verify_password,button_move,change_password,backup_setup,reset_state,change_phase,clear_cache
import time
if "settings_nav" not in st.session_state:
    st.session_state.settings_nav = {
        "phase" : 0,
        "period" : 0
}
if "password_check" not in st.session_state:
   st.session_state.password_check = False
if st.session_state.password_check == False:
    is_valid = verify_password(st.session_state.username)
    if is_valid:
      st.session_state.password_check = True
      st.rerun()
elif st.session_state.password_check == True:
   if st.session_state.settings_nav["phase"] == 0:
      st.subheader("Settings⚙")
      button_move("Change password",1,["settings_nav","phase"])
      button_move("Change username",2,["settings_nav","phase"])
      button_move("Change Security Question",3,["settings_nav","phase"])
      button_move("Factory_reset",4,["settings_nav","phase"])
      button_move("Change currency",5,["settings_nav","phase"])
   if st.session_state.settings_nav["phase"] > 0:
     if st.button("Menu"):
      reset_state(["settings_nav"])
   if st.session_state.settings_nav["phase"] == 1:
      if st.session_state.settings_nav["period"] == 0:
         change_password(st.session_state.username,["settings_nav"])
   if st.session_state.settings_nav["phase"] == 2:
      if st.session_state.settings_nav["period"] == 0:
         controller = st.session_state.controller
         change_username = st.text_input("Change Username")
         already_exists = fetch_user(change_username)
         if st.button("Change"):
           if not already_exists:
               supasafe.table("Users").update({"Username" : change_username}).eq("Username",st.session_state.username).execute()
               st.session_state.username = change_username
               controller.set("saved_username",value=change_username)
               st.success("Username changed")
               clear_cache()
               time.sleep(1)
               reset_state(["settings_nav"])
           else:
               st.warning("Username already taken!")
   if st.session_state.settings_nav["phase"] == 3:
      if st.session_state.settings_nav["period"] == 0:
         st.subheader("Change Security Question")
         change_question = backup_setup(st.session_state.username)
         if change_question:
            reset_state(["settings_nav"])
   if st.session_state.settings_nav["phase"] == 4:
      if st.session_state.settings_nav["period"] == 0:
         st.write("You are about to reset all your data do you want to proceed")
         button_move("Okay",1,["settings_nav","period"])
      if st.session_state.settings_nav["period"] == 1:
         st.warning("Are you sure you want to reset account")
         if st.button("Yes"):
            response = supasafe.rpc("factory_reset_user",{"target_username":st.session_state.username}).execute()
            if response.data:
               st.success("Factory Reset successful")
               clear_cache()
               time.sleep(1)
               reset_state(["settings_nav"])
            else:
               st.warning("Factory reset un successful")
   if st.session_state.settings_nav["phase"] == 5:
      currency_list = {"Dollars" :"$","Naira" : " ₦","Pounds" : "£","Rupees" : "₹","Cedis" : "₵ ", "CFA" : "F.CFA", "Euro" : "€"}
      currencies = currency_list.keys()
      currency_options = st.selectbox("Select currency",currencies,key="currency_options")
      currency_symbol = currency_list.get(st.session_state.currency_options)
      if st.session_state.currency != currency_symbol:
         st.button("Save",on_click=change_currency,args=(currency_symbol,st.session_state.username))
   if st.session_state.settings_nav["period"] > 0:
      st.button("Back",on_click=change_phase,args=(-1,["settings_nav","period"],"+"))
