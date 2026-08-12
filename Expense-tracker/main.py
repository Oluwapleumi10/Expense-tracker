import streamlit as st
from streamlit_cookies_controller import CookieController
import time
from api_connect import fetch_user
from utils import backup_setup

#Initializing the pages of the app , using files
app = st.Page("app.py" , title="App")
analysis = st.Page("others/Analysis.py" , title="Analysis📊")
log_in = st.Page("login.py")
settings = st.Page("settings.py", title="Settings⚙")

#Initialized a session state attempt for checking cookie delays
if "attempt" not in st.session_state:
    st.session_state.attempt = 0
#Created a cookie controller object and saved it to session state
controller = CookieController()
if "controller" not in st.session_state:
    st.session_state.controller = controller

#Attempt to get saved_username cookie from the browser
if "username" not in st.session_state:
    try:
      saved_cookie = controller.get("saved_username")
      if saved_cookie:
        st.session_state.username = saved_cookie
    except TypeError:
        st.write("Error Occured")
        time.sleep(1)
        st.session_state.username = None

#If no cookie was found ,try again several times incase of browser delay
if st.session_state.attempt < 5:
    with st.spinner("Loading"):
        time.sleep(0.5)
        st.session_state.attempt += 1
        st.rerun()
#After several attempts and username wasn't found, then set the username to empty
elif st.session_state.get("username") == None and st.session_state.attempt == 5:
    st.session_state.username = {}

if st.session_state.username == {}:
    log = st.navigation([log_in])
    log.run()
else:
#If username was found,get users info 
    username = st.session_state.username
    data = fetch_user(username,mode="verification")
    if "currency" not in st.session_state:
       st.session_state.currency = data[0]["Currency"]
    if not data[0]["Security Question"]:
        st.subheader("Set Security Question")
        backup_setup(username)
    else:
        pages = st.navigation([app,analysis,settings])
        #If user isnot in the settings page , lock the settings page
        if pages.title != "Settings⚙":
           st.session_state.password_check = False
        pages.run()
