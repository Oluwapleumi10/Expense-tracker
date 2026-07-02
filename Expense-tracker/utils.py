import datetime as date
import bcrypt
import streamlit as st
from api_connect import supasafe,fetch_user,fetch_tx,fetch_budget,fetch_categories
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
            supasafe.table("Users").update({"Security Question" : question_box, "Security Answer" : security_answer}).eq("Username",value=username).execute()
            st.success("Security question succesfully set")
            return True

def change_phase(step,target,by="="):
    if by == "=":
       st.session_state[target[0]][target[1]]= step
    elif by == "+":
        st.session_state[target[0]][target[1]] += step


def display_next(target_list):
    st.button("Next",on_click=change_phase,args=(1,[target_list[0],target_list[1]],"+"))

def next_settings(target):
    if st.button("Next"):
      st.session_state.settings_nav[target] += 1
      st.rerun()

def verify_password(username):
    get_user = fetch_user(username,"verification")
    user_password = get_user[0]["Password"]
    ask_pass = st.text_input("What is your password",type="password",key="ask_pass")
    is_valid = validate_password(user_password,ask_pass)
    if is_valid:
        return True
    elif ask_pass:
          st.warning("Incorrect password")
    
def button_move(name,step,target):
    st.button(name,on_click=change_phase,args=(step,target),type="tertiary")

def change_password(username,state_list):
     st.subheader("change password")
     attempt1 = st.text_input("Change Password",type="password")
     if attempt1:
        if len(attempt1) < 9 or  not any( char in attempt1 for char  in string.punctuation):
            st.toast("Your password doesnt meet the citeria , try again !")
        else:
            attempt2 = st.text_input("Confirm password",type="password")
            if  attempt2:
                if attempt1 == attempt2:
                    if st.button("Confirm"):
                        st.success("Password reset")
                        changed_password = hash_decode(attempt2)
                        supasafe.table("Users").update({"Password":changed_password}).eq("Username",username).execute()
                        states = state_list
                        for state in states:
                          if state in st.session_state:
                            del st.session_state[state]
                            time.sleep(1)
                            st.rerun()
                else:
                    st.toast("Password doesnt match")
     st.warning("Your password should be at least 9 digits long and must contian a special character")
def reset_state(state_list):
     states = state_list
     for state in states:
        if state in st.session_state:
          del st.session_state[state]
          st.rerun()
def clear_cache():
    fetch_tx.clear()
    fetch_budget.clear()

def format_amount(amount,format_lenght,with_emoji=False):
    thousand = 1 * 10**3
    million = 1 * 10**6 
    billion = 1 * 10**9
    trillion = 1 * 10**12
    amounted = abs(amount)
    if amount < 0:
        symbol = f"\u2011{st.session_state.currency}"
    else:
        symbol = st.session_state.currency
    

    if with_emoji:
            if amount > 0:
                emoji = "🟢"
            elif amount < 0:
                emoji = "🔴"
            else:
                emoji = ""
    else:
        emoji = ""
    
        
    if amounted >= trillion:
        amount_fx,figure = [amounted/trillion,"t"]
    elif amounted >= billion:
        amount_fx,figure = [amounted/billion,"b"]
    elif amounted >= million:
        amount_fx,figure = [amounted/million,"m"]
    elif amounted >= thousand:
        amount_fx,figure = [amounted/thousand,"k"]
    else:
        amount_fx,figure = [amounted,""]
    
    if format_lenght == 0:
        display_amount = amounted
        figure = None
    elif format_lenght == 1:
       display_amount = amount_fx
    elif format_lenght == 2:
         if amounted >= 100000:
            display_amount = amount_fx
         else:
            display_amount = amounted
            figure = None

    if figure:
       format_fx = f"{emoji}{symbol}{display_amount:,.2f}{figure}"
    else:
        format_fx = f"{emoji}{symbol}{display_amount:,.2f}"
    return format_fx
    
def display_expander(dates,data):
    for date in dates:
        day = data[data["Period"] == date]
        total_income =  day[day["Type"] == "Income"]["Amount"].sum()
        total_expense = day[day["Type"] =="Expense"]["Amount"].sum()
        balance = total_income - total_expense
        formatted_in = format_amount(total_income,1)
        formatted_out = format_amount(total_expense,1)
        formatted_bal = format_amount(balance,1)
        with st.expander( f"{date} \u2003🟢{formatted_in} \u2003🔴{formatted_out}\u2003 ➡\u00A0{formatted_bal}"):
            st_day = day[["Category","Amount","Type"]]
            st.dataframe(st_day,hide_index=True)
def merge_column(data,columnss,name):
    column_a = columnss[0]
    column_b = columnss[1]
    data[name] = data[column_a].combine_first(data[column_b])
    data.drop(columns=[column_a,column_b],inplace=True)

def analysis_column(row):
        difference = None
        if row["Type"] == "Income":
            difference =  row["Amount_y"] - row["Amount_x"]
        elif row["Type"] == "Expense":
            difference = row["Amount_x"] - row["Amount_y"]
        return difference

def arrange_category(cate,tx_type):
    income_cate = ["Salary","Allowance","Savings/Investment"]
    expense_cate = ["Food/Groceries","Housing/Utilities","Transport/Fuel","Personal care","Health/Medical",
                    "Shopping/Personal items", "Airtime/Data","Subscriptions","Academics/School","Gifts/Charity",
                    "Entertainment/Recreation","Loans/Debts","Charges"]
    if tx_type == "Initial balance":
        cate_data = ["Starting balance"]
    else:
        if tx_type == "Income":
          cate_data = income_cate + expense_cate
        else:
          cate_data = expense_cate + income_cate
        for cat in cate:
          if cat not in cate_data and cat != "Starting balance":
            cate_data.append(cat)
        cate_data.append("Add Category")
    return cate_data






'''if difference:
    if difference < 0:
        return f"🔴{difference}"
    elif difference == 0:
        return f"🔘{difference}"
    else:
        return f"🟢+{difference}" $   ₦'''
      
