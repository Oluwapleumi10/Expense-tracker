import datetime as date
import pandas as pd
import bcrypt
import streamlit as st
from api_connect import supabase,fetch_user
import time
import string
def format_date(date_period):
    return date_period.strftime("%B %Y")

def hash_decode(password):
    encoded_pass = bcrypt.hashpw(password.encode("utf-8"),bcrypt.gensalt())
    decoded_pass = encoded_pass.decode("utf-8")
    return decoded_pass

def validate_password(validating_password,typed_password):
    val_password = validating_password.encode("utf-8")
    typed_password = typed_password.encode("utf-8")
    is_valid = bcrypt.checkpw(typed_password,val_password)
    return is_valid
def backup_setup(username):
    questions = ["What is your best friends name","What's your mothers maiden name","create a question"]
    question_box = st.selectbox("Security questions",questions)
    if question_box == "create a question":
        question_box = st.text_input("Create Question")
    answer = st.text_input("Answer")
    if st.button("Set Question"):
        if not answer:
            st.warning("You must input an answer")
        else:
            security_answer = hash_decode(answer.lower())
            supabase.table("Users").update({"Security Question" : question_box, "Security Answer" : security_answer}).eq("Username",value=username).execute()
            st.success("Security question succesfully set")
            if st.session_state.navigation["period"] == 1:
                st.session_state.navigation["period"] =2
            else:
                st.session_state.navigation["phase"] = 0
            time.sleep(1.5)
            st.rerun()

def change_phase(step,target,by="="):
    if by == "=":
       st.session_state.navigation[target] = step
    if by == "+":
        st.session_state.navigation[target] += step


def display_next():
    st.button("Next",on_click=change_phase,args=(1,"period","+"))
