import streamlit as st
from streamlit_cookies_controller import CookieController
import time
from api_connect import fetch_user
from utils import backup_setup
import app_logic as lg

app = st.Page("app.py" , title="App")
analysis = st.Page("others/Analysis.py" , title="Analysis📊")
log_in = st.Page("login.py")
settings = st.Page("settings.py", title="Settings⚙")

if "attempt" not in st.session_state:
    st.session_state.attempt = 0
    

controller = CookieController()
if "controller" not in st.session_state:
    st.session_state.controller = controller
if "username" not in st.session_state:
    try:
      saved_cookie = controller.get("saved_username")
      if saved_cookie:
        st.session_state.username = saved_cookie
    except TypeError:
        st.session_state.username = None   
if st.session_state.attempt == 0:
    with st.spinner("Loading"):
        time.sleep(0.5)
        st.session_state.attempt += 1
        st.rerun()
elif st.session_state.get("username") == None and st.session_state.attempt == 1:
    st.session_state.username = {}

if st.session_state.username == {}:
    log = st.navigation([log_in])
    log.run()
else:
    username = st.session_state.username
    data = fetch_user(username,mode="verification")
    if "currency" not in st.session_state:
       st.session_state.currency = data[0]["Currency"]
    if not data[0]["Security Question"]:
        st.subheader("Set Security Question")
        backup_setup(username)
    else:
        pages = st.navigation([app,analysis,settings])
        pages.run()
