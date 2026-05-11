from streamlit_cookies_controller import CookieController
import time
import streamlit as st
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