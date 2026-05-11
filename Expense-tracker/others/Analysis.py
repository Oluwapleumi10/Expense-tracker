import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px 
from datetime import datetime
from api_connect import fetch_tx
import layout


#This is where the work starts 

if "username" not in st.session_state or st.session_state.username == {}:
    st.stop()
st.title("Analysis")
layout.show_sidebar()
s_username = st.session_state.username
file_df = fetch_tx(s_username)
if not file_df.empty:
    if "df" not in st.session_state:
        df = file_df
        st.session_state.df = df
        st.session_state.df["Date"] = pd.to_datetime(st.session_state.df["Date"],format="mixed").dt.date
        st.session_state.df = st.session_state.df.sort_values(by="Date" , ascending=False).reset_index(drop=True)
else:
 st.subheader("Make a transaction to unlock this page")
 st.stop()


#Editing the datasets, changing date from string to date format
df = st.session_state.df
df["Item"] = df["Item"].astype(str).str.lower().str.strip()
df["Date"] = pd.to_datetime(df["Date"],format="mixed")
df["Week"] = df["Date"].dt.to_period("W")
df["Month"] = df["Date"].dt.to_period("M")
df["Day"] = df["Date"].dt.day_name()

def format_date(date_period):
    return date_period.strftime("%B %Y")
def format_week(week_period,no_year=False):
    if no_year == False:
        start_date = week_period.start_time.strftime("%d %b %Y")
        end_date = week_period.end_time.strftime("%d %b %Y")
    else:
        start_date = week_period.start_time.strftime("%d %b")
        end_date = week_period.end_time.strftime("%d %b") 
    return f"{start_date} - {end_date}"
current_month = pd.Period(datetime.now(), freq="M")
current_day = datetime.now().day
joined_date = st.session_state.df["Date"].min()
joined_month = joined_date.to_period("M")
joined_day = joined_date.day




graph_info = {
            "Income" : {"color" :"green","y":"Income", "x":"Total Amount","Month_title":"Monthly Income",
                        "Week_title":"Weekly Income","message":"earning","message2":"Income"},
            "Expense" : {"color":"red","y":"Expenses","x":"Total Amount","Month_title":"Monthly Expenses",
                        "Week_title":"Weekly Expenses","message":"spending","message2":"Expense"}
            }





def select_mode(mode,tx_type):
     if mode == "Week":
            available_weeks = df["Week"].unique()
            option = st.selectbox("Select a week" , available_weeks,key=f"{tx_type}_week",format_func=format_week)
            filter_df = df[df["Week"] == option]
            week_days = filter_df["Day"]
            week_days = week_days.unique()
            filtered_df = filter_df[filter_df["Type"] == tx_type]
     elif mode == "Month":
            available_months = df["Month"].unique()
            option = st.selectbox("Select a month",available_months,key=f"{tx_type}_month",format_func=format_date)
            filter_df = df[df["Month"] == option]
            filtered_df = filter_df[filter_df["Type"]== tx_type]
     return filtered_df,option


def graph_type(data,g_type,mode):
    data_type = data
    graph = graph_info.get(g_type)
    graphs = ["bar chart" ,"donut chart" ,"time series" ,"multiple bar chart"]
    graph_options = st.selectbox("Selet graph" ,graphs, key=f"{g_type}different_graphs")
    category_grouped_data = data_type.groupby("Category")["Amount"].sum()
    if graph_options == "bar chart":
        category_grouped_data = category_grouped_data.reset_index()
        if mode == "Week":
            title_val = graph["Week_title"]
        elif mode == "Month":
            title_val = graph["Month_title"]
        sample = category_grouped_data
        fig = px.bar(sample,x="Amount", y="Category", orientation="h",hover_data={"Category" :False}, title=title_val, color_discrete_sequence=[graph["color"]])
    elif graph_options == "donut chart":
        sorted_data = category_grouped_data.sort_values(ascending=False)
        top5 = sorted_data[0:5]
        the_rest = sorted_data[5: ].sum()
        if the_rest > 0:
             others = pd.Series([the_rest],index=["others"])
             donut_data = pd.concat([top5,others])
        else:
             donut_data = top5
        if mode == "Week":
             title_val = f"Top 5 {graph["Week_title"]}"
        elif mode == "Month":
             title_val = f"Top 5 {graph["Month_title"]}"
        sample = donut_data
        values_val = donut_data.values
        name_val = donut_data.index
        fig = px.pie(sample,names=name_val , values=values_val , title=title_val , hole=0.5)
    elif graph_options == "time series":
        if mode == "Week":
            series_data = data.groupby("Date")["Amount"].sum().reset_index()
            series_data["Date"] = pd.to_datetime(series_data["Date"]).strftime("%a %d %b")
            x_val = series_data["Date"]
        elif mode == "Month":
             series_data = data.groupby("Week")["Amount"].sum().reset_index()
             series_data["Days interval"] = series_data["Week"].apply(format_week,no_year=True)
             x_val = series_data["Days interval"]
        y_val = series_data["Amount"]
        title_val = f"{mode}ly trend"
        fig = px.line(series_data , x=x_val, y=y_val , title=title_val , markers=True)
    elif graph_options == "multiple bar chart":
        alls = ["All categories"]
        categories = data["Category"].unique().tolist()
        all_categories = alls + categories
        user_choice = st.selectbox("Select a category" , all_categories )
        if user_choice == "All categories":
             cate_data = data.groupby("Category")["Amount"].sum().reset_index()
             y_val = cate_data["Category"]
             x_val = cate_data["Amount"]
             title_val = f"{user_choice} Analysis"
             fig = px.bar(cate_data,x=x_val,y=y_val,title=title_val,color_discrete_sequence=[graph["color"]])
        else:
             user_data = data[data["Category"] == user_choice]
             cate_data = user_data.groupby("Item")["Amount"].sum().reset_index()
             y_val = cate_data["Item"]
             x_val = cate_data["Amount"]
             title_val = f"{user_choice} Analysis"
             fig = px.bar(cate_data,x=x_val,y=y_val,title=title_val,color_discrete_sequence=[graph["color"]])
    fig.update_layout(dragmode=False)
    st.plotly_chart(fig) 
    #Metric logic

    
def metrics(opt,mode,type,data):
    graph = graph_info.get(type)
    if mode == "Week":
        total = data["Amount"].sum()
        answer = round(total/7)
        score_board = data["Category"].value_counts()

    if mode == "Month":
         if opt == joined_month:
                  if joined_month == current_month:
                        days_amount = (current_day-joined_day ) + 1
                  elif joined_month != current_month:
                        days_amount = pd.Period(option).days_in_month         
                    
         elif opt != current_month:
                    days_amount = pd.Period(option).days_in_month
         elif opt == current_month:
                    days_amount = current_day
                
         total = data["Amount"].sum()
         answer = round(total/days_amount)
         score_board = data["Category"].value_counts()


    col1,col2 ,col3= st.columns(3)

    col1.metric(label=f"Average Daily {graph["message"].title()}",value=f"₦{answer:,.2f}")
    if len(score_board) > 0: 
        frequent_category = score_board.index[0]
        frequent_category = str(frequent_category).replace("_"," ")
        item_times = score_board.values[0]
        col2.metric(f"Most frequent {graph["message2"]} ",value=f"{frequent_category}" ,
                    delta = f"x{item_times}" , delta_arrow="off")
    else:
     col2.metric(f"Most frequent {graph["message2"]} ","Null")

    col3.metric(f"Total {graph["message2"]}",f"₦{total:,.2f}")

            
        
#Creating Expenses and income tabs 
modes = st.radio("View By",["Month","Week"],key="radio") 
tabs1,tabs2,tabs3 = st.tabs(["Overview","Income","Expenses"])
income = st.session_state.df[st.session_state.df["Type"] == "Income"]
expense = st.session_state.df[st.session_state.df["Type"] == "Expense"]
with tabs1:
     st.title("Overview")
  


with tabs2:
      #modes = st.radio("View By",["Month","Week"],key=tabs1)
      filtered_data,option = select_mode(mode=modes,tx_type="Income")
      graph_type(filtered_data,"Income",mode=modes)
      metrics(option,modes,"Income",data=filtered_data)
with tabs3:
    #modes = st.radio("View By",["Month","Week"],key=tabs2)
    filter_data,options = select_mode(mode=modes,tx_type="Expense")
    graph_type(filter_data,"Expense",mode=modes)
    metrics(options,modes,"Expense" ,data=filter_data)











