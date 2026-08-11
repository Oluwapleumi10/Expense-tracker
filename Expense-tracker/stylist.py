from datetime import datetime 
import streamlit as st

def simple_date(date,mode):
    if mode == "Week":
        start_format = date.start_time.strftime("%d-%b")
        end_format = date.end_time.strftime("%d-%b")
        return f"{start_format}/{end_format}"
    elif mode == "Month":
        simple = date.strftime("%b %Y")
        return simple
     
def format_df(data,length,*target_column,need_emoji=False,**kwargs):
    CURRENCY = st.session_state.currency
    if need_emoji:
        st.dataframe(data.style.format(formatter= lambda x : format_amount(x,length,CURRENCY,True),subset=list(target_column)),**kwargs)
    else:
       st.dataframe(data.style.format(formatter= lambda x : format_amount(x,length,CURRENCY),subset=list(target_column)),**kwargs)


def expander_format(income,expense,balance):
    CURRENCY = st.session_state.currency
    #Only filter income and expense
    formatted_in = format_amount(income,1,CURRENCY)
    formatted_out = format_amount(expense,1,CURRENCY)
    formatted_bal = format_amount(balance,1,CURRENCY)
    return formatted_in,formatted_out,formatted_bal

def format_amount(amount,format_lenght,currency,with_emoji=False):
    thousand = 1 * 10**3
    million = 1 * 10**6 
    billion = 1 * 10**9
    trillion = 1 * 10**12
    amounted = abs(amount)
    if amount < 0:
        symbol = f"\u2011{currency}"
    else:
        symbol = currency
    

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
    
def format_date(date_period):
    return date_period.strftime("%B %Y")









