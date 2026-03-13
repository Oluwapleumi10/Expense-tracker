import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from supabase import create_client
from datetime import datetime
import os
import layout
if "username" not in st.session_state or st.session_state.username == {}:
    st.stop()
st.title("Analysis")
supabase = create_client(st.secrets["SUPABASE_URL"],st.secrets["SUPABASE_KEY"]) 
s_username = st.session_state.username
file_df = supabase.table("Transactions").select("*").eq("Username" ,s_username) .execute().data
if  file_df:
    if "df" not in st.session_state:
        df = pd.Dataframe(file_df)
        st.session_state.df = df
        st.session_state.df["Date"] = pd.to_datetime(st.session_state.df["Date"],format="mixed").dt.date
        st.session_state.df = st.session_state.df.sort_values(by="Date" , ascending=False).reset_index(drop=True)
else:
 st.subheader("Make a transaction to unlock this page")
 st.stop()

layout.show_sidebar()

#Editing the datasets, changing date from string to date format
df = st.session_state.df
df["Item"] = df["Item"].astype(str).str.lower().str.strip()
df["Date"] = pd.to_datetime(df["Date"],format="mixed")
df["Week"] = df["Date"].dt.to_period("W")
df["Month"] = df["Date"].dt.to_period("M")
df["Day"] = df["Date"].dt.day_name()

def format_date(date_period):
    return date_period.strftime("%B %Y")
def format_week(week_period):
    start_date = week_period.start_time.strftime("%d %b %Y")
    end_date = week_period.end_time.strftime("%d %b %Y")
    return f"{start_date} - {end_date}"
current_month = pd.Period(datetime.now(), freq="M")
current_day = datetime.now().day
joined_date = st.session_state.df["Date"].min()
joined_month = joined_date.to_period("M")
joined_day = joined_date.day




#Creating a function to plot graph for both income and expenses
def plot_graph(graph_type,mode):
        graph_info = {
            "Income" : {"color" :"green","y":"Income", "x":"Total Amount","Month_title":"Monthly Income",
                        "Week_title":"Weekly Income","message":"earning","message2":"Income"},
            "Expense" : {"color":"red","y":"Expenses","x":"Total Amount","Month_title":"Monthly Expenses",
                        "Week_title":"Weekly Expenses","message":"spending","message2":"Expense"}
            }
        graph = graph_info.get(graph_type)
        fig , ax =plt.subplots()
#The code for weekly graph
        if mode == "Week":
            available_weeks = df["Week"].unique()
            opt = st.selectbox("Select a week" , available_weeks,key=graph_type+"_week",format_func=format_week)
            filterw_df = df[df["Week"] == opt]
            week_days = filterw_df["Day"]
            week_days = week_days.unique()
            weekly = filterw_df[filterw_df["Type"] == graph_type]
            if weekly.empty:
                 st.warning("There's no data to be analysed for this section")
            elif not weekly.empty:
                weekly_stats = weekly.groupby("Item")["Amount"].sum()
                ax = plt.barh(weekly_stats.index,weekly_stats.values,color=graph["color"])
                plt.xlabel(graph["x"])
                plt.ylabel(graph["y"])
                plt.title(graph["Week_title"])
                st.pyplot(fig)
                total = weekly["Amount"].sum()
                answer = round(total/7)
                score_board = weekly["Item"].value_counts()
                col1,col2,col3, = st.columns(3)

                col1.metric(label=f"Average Daily {graph["message"].title()}",value=f"₦{answer:,.2f}")
                if len(score_board) > 0: 
                    frequent_item = score_board.index[0]
                    frequent_item = str(frequent_item).replace("_"," ")
                    item_times = score_board.values[0] 
                    col2.metric(f"Most frequent {graph["message2"]} ",value=f"{frequent_item}" ,
                                delta = f"x{item_times}" , delta_arrow="off")
                else:
                    col2.metric(f"Most Frequent {graph["message2"]} ","Null")
                
                col3.metric(f"Total {graph["message2"]}",f"₦{total:,.2f}")
#The code for monthly graph           
        elif mode == "Month":
            available_months = df["Month"].unique()
            option = st.selectbox("Select a month",available_months,key=graph_type+"_month",format_func=format_date)
            filtered_df = df[df["Month"] == option]
            month = filtered_df[filtered_df["Type"]== graph_type]
            if month.empty:
                 st.warning("There's no data to be analysed for this section")
            elif not month.empty:
                monthly_stats = month.groupby("Item")["Amount"].sum()
                ax = plt.barh(monthly_stats.index,monthly_stats.values,color=graph["color"])
                plt.xlabel(graph["x"])
                plt.ylabel(graph["y"])
                plt.title(graph["Month_title"])
                st.pyplot(fig)
                # The block for metrics for the graph
                if option == joined_month:
                  if joined_month == current_month:
                        days_amount = (current_day-joined_day ) + 1
                  elif joined_month != current_month:
                        days_amount = pd.Period(option).days_in_month         
                    
                elif option != current_month:
                    days_amount = pd.Period(option).days_in_month
                elif option == current_month:
                    days_amount = current_day
                
                total = month["Amount"].sum()
                answer = round(total/days_amount)
                score_board = month["Item"].value_counts()


                col1,col2 ,col3= st.columns(3)

                col1.metric(label=f"Average Daily {graph["message"].title()}",value=f"₦{answer:,.2f}")
                if len(score_board) > 0: 
                    frequent_item = score_board.index[0]
                    frequent_item = str(frequent_item).replace("_"," ")
                    item_times = score_board.values[0]
                    col2.metric(f"Most frequent {graph["message2"]} ",value=f"{frequent_item}" ,
                                delta = f"x{item_times}" , delta_arrow="off")
                    
                else:
                    col2.metric(f"Most frequent {graph["message2"]} ","Null")
                
                col3.metric(f"Total {graph["message2"]}",f"₦{total:,.2f}")
                    

            
        
#Creating Expenses and income tabs  
tabs1,tabs2 = st.tabs(["Income","Expenses"])
income = st.session_state.df[st.session_state.df["Type"] == "Income"]
expense = st.session_state.df[st.session_state.df["Type"] == "Expense"]

with tabs1:
      st.title("Income Analysis")
      modes = st.radio("View By",["Month","Week"],key=tabs1)
      if modes == "Week":
        plot_graph("Income",mode=modes)
      elif modes == "Month":
        plot_graph("Income",mode=modes)
grouped_data = df.groupby("Item")["Amount"].sum()
with tabs2:
    st.title("Expense Analysis")
    modes = st.radio("View By",["Month","Week"],key=tabs2)
    if modes == "Week":
        plot_graph("Expense",mode=modes)
    elif modes == "Month":
        plot_graph("Expense",mode=modes)










