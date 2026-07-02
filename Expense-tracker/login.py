import streamlit as st
from api_connect import supasafe,fetch_user
import time
import string
from utils import hash_decode,validate_password,backup_setup,change_phase,display_next,change_password,reset_state
if "navigation" not in st.session_state:
    st.session_state.navigation = {
        "phase" : 0,
        "period" : 0,
    }
if "auth" not in st.session_state:
    st.session_state.auth = {
        "new_username" : None,
        "hpass" : None,
        "validate" : None,}
if "period2" not in st.session_state:
    st.session_state.period2 = {
        "username" : None,
        "question" : None,
        "answer" : None,
        "attempt1" : None,
        "attempt2" : None
    }
if "check_user" not in st.session_state:
    st.session_state.check_user = None
controller = st.session_state.controller
if "reg_counter" not in st.session_state:
    st.session_state.reg_counter = 0
if st.session_state.navigation["phase"] == 0:
    tabs1,tabs2 = st.tabs(["Login","Registration"])
    with tabs1:
        username = st.text_input("Username",key="Username")
        password = st.text_input("Password",key="Password",type="password")
        auth = fetch_user(username,mode="verification")
        if st.button("Login"):
            if auth:
                auth_password = auth[0]["Password"]
                if "$2b$" in auth_password:
                    is_valid = validate_password(auth_password,password)
                else:
                    send_to_supabase = hash_decode(auth_password)
                    is_valid = validate_password(send_to_supabase,password)
                    if is_valid:
                      supasafe.table("Users").update({"Password" : send_to_supabase}).eq("Username",username).execute()
                if is_valid:
                  controller.set("saved_username",value=username,max_age=1382400)
                  st.session_state.username = username
                  time.sleep(1)
                  st.rerun()
                else:
                    st.error("Incorrect password")
            else:
                st.error("Wrong username")
        st.button("Forget Password",type="tertiary",on_click=change_phase,args=(2,["navigation","phase"]))
    with tabs2:
        new_username = st.text_input("New username",key=f"Username{st.session_state.reg_counter}")
        st.session_state.auth["new_username"] = new_username
        new_password = st.text_input("New password",key=f"Password{st.session_state.reg_counter}",type="password")
        if st.button("Confirm"):
            username_exist = fetch_user(usern=new_username)
            if not username_exist:
                if len(new_password) < 9 or  not any( char in new_password for char  in string.punctuation):
                    st.error("Password can't be lesser than 9 characters and must contain a special character")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.session_state.auth["hpass"] = hash_decode(new_password)
                    supasafe.table("Users").insert({"Username" : new_username,"Password" :st.session_state.auth["hpass"] }).execute()
                    st.success("Account created successfully!")
                    st.session_state.navigation["phase"] = 1
                    st.session_state.reg_counter += 1
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("Username already taken")
elif st.session_state.navigation["phase"] == 1:
            st.subheader("Set a recovery question")
            set_security = backup_setup(st.session_state.auth["new_username"])
            if set_security:
                time.sleep(0.7)
                reset_state(["navigation"])
elif st.session_state.navigation["phase"] == 2:
    st.button("Go back",on_click=change_phase ,args=(0,["navigation","phase"]))
    st.subheader("Forgot password")
    st.warning("Please always click enter when you are done")
    if st.session_state.navigation["period"] == 0:
       st.session_state.period2["username"] = st.text_input("Whats your username")
       st.session_state.check_user= fetch_user(st.session_state.period2["username"],mode="verification")
       if st.session_state.check_user:
           display_next(["navigation","period"])
       elif st.session_state.period2["username"]:
           st.warning("Username doesnt exist !")
    if st.session_state.navigation["period"] == 1:
        if st.session_state.check_user[0]["Security Question"] == None:
            st.write("You havent set up a security question yet...")
            backup_setup( st.session_state.period2["username"])
            st.session_state.navigation["period"] =2
            time.sleep(1)
            st.rerun()
        else:
            st.session_state.period2["question"] = st.markdown(st.session_state.check_user[0]["Security Question"])
            st.session_state.period2["answer"] = st.text_input("Answer")
            st.session_state.auth["validate"] = validate_password(st.session_state.check_user[0]["Security Answer"],st.session_state.period2["answer"].lower())
            if st.session_state.auth["validate"]:
                display_next(["navigation","period"])
            elif st.session_state.period2["answer"]:
                st.warning("Your answer is incorrect!")
    if st.session_state.navigation["period"] == 2:
        change_password(st.session_state.period2["username"],["navigation","check_user","period2"])
        
    if st.session_state.navigation["period"] > 0:
      st.button("Back",on_click=change_phase,args=(-1,["navigation","period"],"+"))