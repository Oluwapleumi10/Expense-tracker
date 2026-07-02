from datetime import datetime 
import streamlit as st
from utils import format_amount,fetch_tx

def simple_date(date,mode):
    if mode == "Week":
        start_format = date.start_time.strftime("%d-%b")
        end_format = date.end_time.strftime("%d-%b")
        return f"{start_format}/{end_format}"
    elif mode == "Month":
        simple = date.strftime("%b %Y")
        return simple
     
def format_df(data,length,*target_column,need_emoji=False,**kwargs):
    if need_emoji:
        st.dataframe(data.style.format(formatter= lambda x : format_amount(x,length,True),subset=list(target_column)),**kwargs)
    else:
       st.dataframe(data.style.format(formatter= lambda x : format_amount(x,length),subset=list(target_column)),**kwargs)






