import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px 
from datetime import datetime
from api_connect import fetch_tx
from utils import display_expander,merge_column,analysis_column,format_amount
import layout
from stylist import simple_date,format_df

if "username" not in st.session_state or st.session_state.username == {}:
    st.stop()
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
 st.subheader("🔒 Locked")
 st.markdown("Make a transaction to unlock this page")
 st.stop()


#Editing the datasets, changing date from string to date format
df = st.session_state.df
df["Item"] = df["Item"].astype(str).str.lower().str.strip()
df["Date"] = pd.to_datetime(df["Date"],format="mixed")
df["Week"] = df["Date"].dt.to_period("W")
df["Month"] = df["Date"].dt.to_period("M")
df["Day"] = df["Date"].dt.day_name()
df["Period"] = df["Date"].dt.date

def format_multi(date,mode,no_year=False):
    if mode == "Month":
     return date.strftime("%B %Y")
    elif mode == "Week":
      if no_year == False:
        start_date = date.start_time.strftime("%d %b %Y")
        end_date = date.end_time.strftime("%d %b %Y")
      else:
        start_date = date.start_time.strftime("%d %b")
        end_date = date.end_time.strftime("%d %b") 
    return f"{start_date} - {end_date}"


def format_date(date):
    return date.strftime("%B %Y")
    
    
    


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





def select_mode(mode,data,tx_type):
     if mode == "Week":
            available_weeks = data["Week"].unique()
            option = st.selectbox("Select a week" , available_weeks,key=f"{tx_type}_week",format_func=format_week)
            filtered_df = data[data["Week"] == option]
            week_days = filtered_df["Day"]
            week_days = week_days.unique()
     elif mode == "Month":
            available_months = data["Month"].unique()
            option = st.selectbox("Select a month",available_months,key=f"{tx_type}_month",format_func=format_date)
            filtered_df = data[data["Month"] == option]
     return filtered_df,option


def graph_type(data,g_type,mode):
    graph = graph_info.get(g_type)
    graphs = ["bar chart" ,"donut chart" ,"time series" ,"multiple bar chart"]
    graph_options = st.selectbox("Selet graph" ,graphs, key=f"{g_type}different_graphs")
    category_grouped_data = data.groupby("Category")["Amount"].sum()
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
             title_val = f"Top {graph["Week_title"]}"
        elif mode == "Month":
             title_val = f"Top {graph["Month_title"]}"
        sample = donut_data
        values_val = donut_data.values
        name_val = donut_data.index
        fig = px.pie(sample,names=name_val , values=values_val , title=title_val , hole=0.5)
    elif graph_options == "time series":
        if mode == "Week":
            series_data = data.groupby("Date")["Amount"].sum().reset_index()
            series_data["Date"] = pd.to_datetime(series_data["Date"]).dt.strftime("%a %d %b")
            x_val = "Date"
        elif mode == "Month":
             series_data = data.groupby("Week")["Amount"].sum().reset_index()
             series_data["Days interval"] = series_data["Week"].apply(format_week,no_year=True)
             x_val = "Days interval"
        y_val = "Amount"
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

    col1.metric(label=f"Average Daily {graph["message"].title()}",value=format_amount(answer,2))
    if len(score_board) > 0: 
        frequent_category = score_board.index[0]
        frequent_category = str(frequent_category).replace("_"," ")
        item_times = score_board.values[0]
        col2.metric(f"Most frequent {graph["message2"]} ",value=f"{frequent_category}" ,
                    delta = f"x{item_times}" , delta_arrow="off")
    else:
     col2.metric(f"Most frequent {graph["message2"]} ","Null")

    col3.metric(f"Total {graph["message2"]}",value=format_amount(total,2))



            
def rename_duplicates(data):
     grouped_data = data.groupby(["Type","Category"])["Amount"].sum().reset_index()
     duplicated_data = grouped_data.duplicated(subset="Category")    
     grouped_data.loc[duplicated_data,"Category"] = grouped_data["Category"]+"(" + grouped_data["Type"]+")"
     return grouped_data

def multi_select(mode,data):
    data["Timeline"] = data[mode]
    available_periods = data["Timeline"].unique()
    select_period = st.multiselect(f"Compare {mode}s",available_periods,max_selections=2,key=f"select_{mode}",format_func= lambda x : format_multi(x,modes))
    if len(select_period) == 2:
        date_a,date_b = select_period
        option = [min(date_a,date_b),max(date_a,date_b)]
        data_a = data[data["Timeline"] == option[0]]
        data_b = data[data["Timeline"] == option[1]]
        return data_a,data_b,option
    

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
            format_df(st_day,2,"Amount",hide_index=True)
#Creating Expenses and income tabs 
modes = st.radio("View By",["Month","Week"],key="radio",horizontal=True) 
tabs1,tabs2,tabs3 = st.tabs(["Overview","Income","Expenses"])
income = st.session_state.df[st.session_state.df["Type"] == "Income"]
expense = st.session_state.df[st.session_state.df["Type"] == "Expense"]
with tabs1:
     if "h2h_switch" not in st.session_state:
          st.session_state.h2h_switch = False
     h2h_toggle = st.toggle("H2h mode",key="h2h_switch")
     if not st.session_state.h2h_switch:
        filtered_data,options = select_mode(mode=modes,data=df,tx_type="Overview")
        st.subheader("Daily breakdown")
        unique_dates = filtered_data["Period"].unique()
        display_expander(unique_dates,filtered_data)
     elif st.session_state.h2h_switch:
          st.subheader("Compare modes")
          values_select = multi_select(modes,df)
          if  values_select:
               data_a,data_b,option = values_select
               data_a = data_a[data_a["Type"].isin(["Income","Expense"])]
               data_b = data_b[data_b["Type"].isin(["Income","Expense"])]
               baseline = simple_date(option[0],mode=modes)
               subject = simple_date(option[1],mode=modes)
               types_a = data_a.groupby("Type")["Amount"].sum().reset_index()
               types_b = data_b.groupby("Type")["Amount"].sum().reset_index()
               types_a["Period"] = baseline
               types_b["Period"] = subject
               overview_data = pd.concat([types_a,types_b],ignore_index=True)
               title_months = f"{subject} vs {baseline}"
               view = px.bar(overview_data,"Type","Amount",title=title_months,color="Period",barmode="group",hover_data={"Type" : False})
               view.update_layout(dragmode=False)
               st.plotly_chart(view)
               
               grouped_a = rename_duplicates(data_a)
               grouped_b = rename_duplicates(data_b)
               merged_period = pd.merge(grouped_a,grouped_b,how="outer",on="Category")
               merge_column(merged_period,["Type_x","Type_y"],"Type")
               merged_period = merged_period.fillna({"Amount_x" : 0,"Amount_y" : 0})
               merged_period["Analysis"] = merged_period.apply(analysis_column,axis=1)
               analysis_sum = merged_period["Analysis"].sum()
               merged_period.rename(columns={"Amount_x":f"{baseline}","Amount_y" : f"{subject}"},inplace=True )
               st.dataframe(merged_period.style.format(lambda x : format_amount(x,2),subset=[f"{baseline}",
                                        f"{subject}"]).format(lambda x : format_amount(x,2,with_emoji=True),
                                        subset=["Analysis"]),column_config={"Type" : None})
               analysis_sum = merged_period["Analysis"].sum()
               format_sum = format_amount(abs(analysis_sum),2)
               if analysis_sum > 0:
                 st.success(f"Looking at {subject}, You performed better than {baseline} by {format_sum}")
               elif analysis_sum < 0:
                 st.error(f"Looking at {subject} , You performed worse compared to {baseline} by {format_sum}")
               else:
                 st.write(f"Looking at {subject} , {subject} and {baseline} are tied !")
                    


with tabs2:
      #modes = st.radio("View By",["Month","Week"],key=tabs1)
      filtered_data,option = select_mode(mode=modes,data=df,tx_type="Income")
      filtered_df = filtered_data[filtered_data["Type"] == "Income"]
      graph_type(filtered_df,"Income",mode=modes)
      metrics(option,modes,"Income",data=filtered_df)
with tabs3:
    #modes = st.radio("View By",["Month","Week"],key=tabs2)
    filtered_data,options = select_mode(mode=modes,data=df,tx_type="Expense")
    filtered_df = filtered_data[filtered_data["Type"]== "Expense"]
    graph_type(filtered_df,"Expense",mode=modes)
    metrics(options,modes,"Expense" ,data=filtered_df)











