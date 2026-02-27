import pandas as pd
import streamlit as st

def show_sidebar():
    with st.sidebar:
      st.write(f"You are logged in as {st.session_state.get("username","username")}")
      if st.button("Log out"):
        st.session_state.username = {}
        del st.session_state.df
        st.rerun()