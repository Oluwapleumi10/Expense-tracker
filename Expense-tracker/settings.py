import streamlit as st
from api_connect import fetch_user,supasafe,update_user_info
from utils import verify_password,button_move,change_password,backup_setup,reset_state,change_phase,clear_cache
import time

USER_TABLE = "Users"
USER_COLUMN = "Username"
USER_NAME = st.session_state.username

def update_interphase(update_column,update_value,msg,session_state=None,refresh=True):
    update_user_info(USER_TABLE,{update_column:update_value},USER_COLUMN,USER_NAME)
    if session_state != None:
      st.session_state[session_state] = update_value
    st.success(msg)
    time.sleep(1)
    reset_state(["settings_nav"],rerun=refresh)


#Settings nav for navigating the settings phase
if "settings_nav" not in st.session_state:
    st.session_state.settings_nav = {
        "phase" : 0,
        "period" : 0
}
#Check if user should be checked 
if "password_check" not in st.session_state:
   st.session_state.password_check = False
#If they should be checked, ask  them to verify password
if st.session_state.password_check == False:
    is_valid = verify_password(st.session_state.username)
    if is_valid:
      st.session_state.password_check = True
      st.rerun()
#If password verification was successful , show them phase_0 of the settings -> the main tab for settings
elif st.session_state.password_check == True:
   if st.session_state.settings_nav["phase"] == 0:
      st.subheader("Settings⚙")
      #-> button move is a function designed to change the navigation phase when clicked
      button_move("Change password",1,["settings_nav","phase"])
      button_move("Change username",2,["settings_nav","phase"])
      button_move("Change Security Question",3,["settings_nav","phase"])
      button_move("Factory_reset",4,["settings_nav","phase"])
      button_move("Change currency",5,["settings_nav","phase"])
   if st.session_state.settings_nav["phase"] > 0:
     if st.button("Menu"):
      reset_state(["settings_nav"])
   #Navigation phase 1 for changing password
   if st.session_state.settings_nav["phase"] == 1:
      if st.session_state.settings_nav["period"] == 0:
         #Run the change password function
         change_password(st.session_state.username,["settings_nav"])
   #Navigation phase 2 for changing username
   if st.session_state.settings_nav["phase"] == 2:
      if st.session_state.settings_nav["period"] == 0:
         controller = st.session_state.controller
         change_username = st.text_input("Change Username")
         already_exists = fetch_user(change_username)
         if st.button("Change"):
           if not already_exists:
               #Update username on supabase,session state and cookies
               update_interphase(USER_COLUMN,change_username,"Username Changed","username")
               controller.set("saved_username",value=change_username)
               clear_cache()
           else:
               st.warning("Username already taken!")
   #Navigation phase 3 for changing security question
   if st.session_state.settings_nav["phase"] == 3:
      if st.session_state.settings_nav["period"] == 0:
         st.subheader("Change Security Question")
         change_question = backup_setup(st.session_state.username)#<- Run the function for setting up security questions
         if change_question:
            reset_state(["settings_nav"])
   #Navigation phase 4 for reseting user data
   if st.session_state.settings_nav["phase"] == 4:
      if st.session_state.settings_nav["period"] == 0:
         st.write("YOU ARE ABOUT TO RESET ALL YOUR DATA DO YOU WANT TO PROCEED")
         button_move("Okay",1,["settings_nav","period"])
      if st.session_state.settings_nav["period"] == 1:
         st.warning("ARE YOU SURE YOU WANT TO RESET ACCOUNT")
         if st.button("Yes"):
            #Send a signal to supabase to run the factory reset program
            response = supasafe.rpc("factory_reset_user",{"target_username":st.session_state.username}).execute()
            #if supabase responded back update and clear cache
            if response.data:
               st.success("Factory Reset successful")
               clear_cache()
               time.sleep(1)
               reset_state(["settings_nav"])
            else:
               st.warning("Factory reset un successful")
   #Navigation phase 5 , for changing currency
   if st.session_state.settings_nav["phase"] == 5:
      currency_list = {"Dollars" :"$","Naira" : " ₦","Pounds" : "£","Rupees" : "₹","Cedis" : "₵ ", "CFA" : "F.CFA", "Euro" : "€"}
      currencies = currency_list.keys()
      currency_options = st.selectbox("Select currency",currencies,key="currency_options")
      currency_symbol = currency_list.get(st.session_state.currency_options)
      if st.session_state.currency != currency_symbol:
         if st.button("Save"):
           update_interphase("Currency",currency_symbol,"Currency Changed","currency")
   if st.session_state.settings_nav["period"] > 0:
      st.button("Back",on_click=change_phase,args=(-1,["settings_nav","period"],"+"))
