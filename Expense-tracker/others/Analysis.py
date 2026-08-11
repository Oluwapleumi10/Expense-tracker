import pandas as pd
import streamlit as st
import plotly.express as px 
from api_connect import fetch_tx
import layout
from stylist import format_df,expander_format,format_amount
import analysis_logic as alg
import app_logic as lg
from analysis_logic import GRAPH_INFO

s_username = st.session_state.username
s_currency = st.session_state.currency
if "df" not in st.session_state:
        file_df = fetch_tx(s_username)
        st.session_state.df = lg.sort_data(file_df)
if st.session_state.df.empty:
 st.subheader("🔒 Locked")
 layout.show_sidebar()
 st.markdown("Make a transaction to unlock this page")
 st.stop()


#Editing the datasets, changing date from string to date format

if "h2h_switch" not in st.session_state:
    st.session_state.h2h_switch = False

def analysis_metric(currency,total,daily_average,most_frequent,types):
  graph = GRAPH_INFO.get(types)
  col1,col2 ,col3= st.columns(3)
  col1.metric(label=f"Average Daily {graph["message"].title()}",value=format_amount(daily_average,2,currency))
  if len(most_frequent)>0: 
      frequent_category = most_frequent.index[0]
      frequent_category = str(frequent_category).replace("_"," ")
      item_times = most_frequent.values[0]
      col2.metric(f"Most frequent {graph["message2"]} ",value=f"{frequent_category}" ,
            delta = f"x{item_times}" , delta_arrow="off")
  else:
    col2.metric(f"Most frequent {graph["message2"]} ","Null")
  col3.metric(f"Total {graph["message2"]}",value=format_amount(total,2,currency))




df = st.session_state.df

df["Date"] = pd.to_datetime(df["Date"],format="mixed")
df["Week"] = df["Date"].dt.to_period("W")
df["Month"] = df["Date"].dt.to_period("M")
df["Day"] = df["Date"].dt.day_name()
df["Period"] = df["Date"].dt.date
 
modes = layout.analysis_sidebar("h2h_switch")
layout.show_sidebar()
graph_options = ["bar chart","donut chart","time series","multiple bar chart"]
graph_info = GRAPH_INFO
available_dates,box_name = alg.get_availabe_dates(df,modes)
option = st.selectbox(box_name,available_dates,key="tabs1",format_func=lambda x : alg.format_multi(x,modes),disabled=st.session_state.h2h_switch)
filtered_df = df[df[modes] == option]

tabs1,tabs2,tabs3 = st.tabs(["Overview","Income","Expenses"])
with tabs1:
     #h2h_toggle = st.toggle("H2h mode",key="h2h_switch")
     if not st.session_state.h2h_switch:
        #Periodic Net balance logic should be here 👇
        net_balance,_,_ = lg.calculate_balance(filtered_df)
        st.subheader(f"{alg.format_multi(option,modes)}:")
        net_balance_metric = st.metric(label="Net balance" ,value=format_amount(net_balance,0,s_currency))
        unique_dates = filtered_df["Period"].unique()
        for date in unique_dates:
            day = filtered_df[filtered_df["Period"] == date]
            balance,total_income,total_expense = lg.calculate_balance(day)
            formatted_in,formatted_out,formatted_bal = expander_format(total_income,total_expense,balance=balance)
            with st.expander( f"{date} \u2003🟢{formatted_in} \u2003🔴{formatted_out}\u2003 ➡\u00A0{formatted_bal}"):  #Expander
               st_day = day[["Category","Amount","Type"]]
               format_df(st_day,2,"Amount",hide_index=True)
     elif st.session_state.h2h_switch:
        df["Timeline"] = df[modes]
        available_periods = df["Timeline"].unique()
        select_period = st.multiselect(f"Compare {modes}s",available_periods,max_selections=2,key=f"select_{modes}",format_func= lambda x : alg.format_multi(x,modes))
        if len(select_period) == 2:
          data_a,data_b,period_date = alg.min_max_date(df,"Timeline",select_period)
          overview_data,subject,baseline = alg.income_vs_expense([data_a,data_b],period_date,date_mode=modes,date_column="Timeline")
          title_months = f"{subject} vs {baseline}"
          view = px.bar(overview_data,"Type","Amount",title=title_months,color="Timeline",barmode="group",hover_data={"Type" : False})
          view.update_layout(dragmode=False)
          st.plotly_chart(view)
          merged_period = alg.merge_periods([data_a,data_b])
          merged_period.rename(columns={"Amount_x":f"{baseline}","Amount_y" : f"{subject}"},inplace=True )
          st.dataframe(merged_period.style.format(lambda x : format_amount(x,2,s_currency),subset=[f"{baseline}",
                                        f"{subject}"]).format(lambda x : format_amount(x,2,s_currency,with_emoji=True),
                                        subset=["Analysis"]),column_config={"Type" : None})
          analysis_sum = merged_period["Analysis"].sum()
          format_sum = format_amount(abs(analysis_sum),2,s_currency)
          if analysis_sum > 0:
              st.success(f"The Net Balance for {subject} is {format_sum} higher than {baseline}")    
          elif analysis_sum < 0:
              st.error(f"The Net Balance for {subject} is {format_sum} lower than {baseline}") 
          else:
              st.write(f"The Net Balance remained unchanged between {subject} and {baseline}")            
with tabs2:
    filtered_data = filtered_df[filtered_df["Type"] == "Income"]
    selected_graph = st.selectbox("Select graph",graph_options,key="select_income_graph")
    if selected_graph == "multiple bar chart":
        all_categories = alg.all_categories(filtered_data)
        category_choice = st.selectbox("Categories",all_categories,key="select_income_category")
        fig = alg.graph_type(filtered_data,selected_graph,modes,"Income",category_choice)
    else:
        fig = alg.graph_type(filtered_data,selected_graph,modes,"Income")
    fig.update_layout(dragmode=False)
    st.plotly_chart(fig) 
    total_in,answer_in,score_board_in = alg.metric_logic(filtered_data,option,modes)
    analysis_metric(s_currency,total_in,answer_in,score_board_in,"Income")
with tabs3:
    filtered_data = filtered_df[filtered_df["Type"]== "Expense"]
    selected_graph = st.selectbox("Select graph",graph_options,key="select_expense_graph")
    if selected_graph == "multiple bar chart":
        all_categories = alg.all_categories(filtered_data)
        category_choice = st.selectbox("Categories",all_categories,key="select_expense_category")
        fig = alg.graph_type(filtered_data,selected_graph,modes,"Expense",category_choice)
    else:
        fig = alg.graph_type(filtered_data,selected_graph,modes,"Expense")
    fig.update_layout(dragmode=False)
    st.plotly_chart(fig) 
    total_ex,answer_ex,score_board_ex = alg.metric_logic(filtered_data,option,modes)
    analysis_metric(s_currency,total_ex,answer_ex,score_board_ex,"Expense")