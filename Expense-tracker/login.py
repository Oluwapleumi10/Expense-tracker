import streamlit as st
from api_connect import supasafe,fetch_user,create_user
import time
import string
from utils import hash_decode,validate_password,backup_setup,change_phase,display_next,change_password,reset_state,password_citeria

#Created a navigation state for navigating through different sections of the login
if "navigation" not in st.session_state:
    st.session_state.navigation = {
        "phase" : 0,
        "period" : 0,
    }

#Created auth session_state variables 
if "auth" not in st.session_state:
    st.session_state.auth = {
        "new_username" : None,
        "hpass" : None,
        "validate" : None,}
    
#Created period2 session_state variables to preserve period2 variables
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

#Registration counter for creating new widgets "onclick"
if "reg_counter" not in st.session_state:
    st.session_state.reg_counter = 0
if st.session_state.navigation["phase"] == 0:
    tabs1,tabs2 = st.tabs(["Login","Registration"])
    with tabs1:
        #Registration tab
        username = st.text_input("Username",key="Username")
        password = st.text_input("Password",key="Password",type="password")
        auth = fetch_user(username,mode="verification")
        if st.button("Login"):
            if auth:
                auth_password = auth[0]["Password"]
                #check if user passsword password has been hashed if not , hash it 
                if "$2b$" in auth_password:
                    is_valid = validate_password(auth_password,password)
                else:#<-Temporary change until all user's password has been hashed
                    send_to_supabase = hash_decode(auth_password)
                    is_valid = validate_password(send_to_supabase,password)
                    if is_valid:
                      supasafe.table("Users").update({"Password" : send_to_supabase}).eq("Username",username).execute()
                if is_valid:
                  #Create a cookie for autologin
                  controller.set("saved_username",value=username,max_age=1382400)
                  st.session_state.username = username
                  st.success("Login Sucessfully")
                  time.sleep(1) #<- a time sleep to sync cookie with python
                  st.rerun()
                else:
                    st.error("Incorrect password")
            else:
                st.error("Wrong username")
        st.button("Forget Password",type="tertiary",on_click=change_phase,args=(2,["navigation","phase"]))
    with tabs2:
        #Registration tab
        new_username = st.text_input("Username",key=f"Username{st.session_state.reg_counter}")
        st.session_state.auth["new_username"] = new_username
        new_password = st.text_input("Password",key=f"Password{st.session_state.reg_counter}",type="password")
        if st.button("Confirm"):
            #Check if username already exists
            username_exist = fetch_user(usern=new_username)
            #If it doesnt exist yet , check their password  
            if not username_exist:
                #Check if the user password meets the citeria of  9 charaters and a special character
                valid_pass,pass_message = password_citeria(new_password,new_username)
                if not valid_pass:
                    st.error(pass_message)
                    time.sleep(1)
                    st.rerun()
                else:
                    #If citeria was met , hash the users password for security purposes
                    st.session_state.auth["hpass"] = hash_decode(new_password)
                    #Create the users profile on supabase , send the hashed passowrd
                    create_user({"Username" : new_username,"Password" : st.session_state.auth["hpass"]},"Users")
                    st.success("Account created successfully!")
                    st.session_state.navigation["phase"] = 1
                    st.session_state.reg_counter += 1
                    time.sleep(0.7)
                    st.rerun()
            else:
                st.error("Username already taken")


#navigation phase1 for users to set recovery question
elif st.session_state.navigation["phase"] == 1:
            st.subheader("Set a recovery question")
            set_security = backup_setup(st.session_state.auth["new_username"])
            if set_security:
                time.sleep(0.7)
                reset_state(["navigation"])

#navigation phase2 for users that forgot their passwords
elif st.session_state.navigation["phase"] == 2:
    st.button("Go back",on_click =change_phase ,args=(0,["navigation","phase"]))
    st.subheader("Forgot password")
    #Period0 of phase 2, designed to check for the provided username
    if st.session_state.navigation["period"] == 0:
       st.warning("Please always click enter when you are done")
       #Check if username is valid 
       st.session_state.period2["username"] = st.text_input("What's your username")
       st.session_state.check_user= fetch_user(st.session_state.period2["username"],mode="verification")
       if st.session_state.check_user:
           #display_next button desiged to navigate user into the next navigation phase
           display_next(["navigation","period"])
        #If not found update!
       elif st.session_state.period2["username"]:
           st.warning("Username doesnt exist !")

    #Period1 of phase2, verify their recovery question
    if st.session_state.navigation["period"] == 1:
        #If username was found but they havent setup recovery question yet
        if st.session_state.check_user[0]["Security Question"] == None:
            st.error("OOPS.... YOU DON'T HAVE A SECURITY QUESTION\n\n"
               "[Email Admin](mailto:raheemahmadoski@gmail.com)\n\n"
               "[Call Admin](tel:+2349013496351)")
            st.stop()
        else:
            #Veify the user, by detecting if they got their security question right
            st.warning("Please always click enter when you are done")
            st.session_state.period2["question"] = st.markdown(st.session_state.check_user[0]["Security Question"])
            st.session_state.period2["answer"] = st.text_input("Answer")
            st.session_state.auth["validate"] = validate_password(st.session_state.check_user[0]["Security Answer"],st.session_state.period2["answer"].lower())
            if st.session_state.auth["validate"]:
                display_next(["navigation","period"])
            elif st.session_state.period2["answer"]:
                st.warning("Your answer is incorrect!")
    #If verification was correct we navigate to the final step , password change
    if st.session_state.navigation["period"] == 2:
        change_password(st.session_state.period2["username"],["navigation","check_user","period2"])

    #A conditional statement that takes user to the previous navigation period    
    if st.session_state.navigation["period"] > 0:
      st.button("Back",on_click=change_phase,args=(-1,["navigation","period"],"+"))
