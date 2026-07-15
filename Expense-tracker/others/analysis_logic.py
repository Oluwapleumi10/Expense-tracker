import pandas as pd
from datetime import datetime
from api_connect import fetch_tx
import plotly.express as px
from stylist import simple_date
from utils import merge_column,analysis_column

#A global with helps functions navigate labels
GRAPH_INFO = {
            "Income" : {"color" :"green","y":"Income", "x":"Total Amount","Month_title":"Monthly Income",
                        "Week_title":"Weekly Income","message":"earning","message2":"Income"},
            "Expense" : {"color":"red","y":"Expenses","x":"Total Amount","Month_title":"Monthly Expenses",
                        "Week_title":"Weekly Expenses","message":"spending","message2":"Expense"}
            }


#create a dynamic date formatter for both month and weeks
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

#Date formatter for specifically months
def format_date(date):
    return date.strftime("%B %Y")
#Date formatter for specifically Weeks    
def format_week(week_period,no_year=False):
    if no_year == False:
        start_date = week_period.start_time.strftime("%d %b %Y")
        end_date = week_period.end_time.strftime("%d %b %Y")
    else:
        start_date = week_period.start_time.strftime("%d %b")
        end_date = week_period.end_time.strftime("%d %b") 
    return f"{start_date} - {end_date}"

def graph_type(data,option,mode,g_type,user_choice=None):
   graph = GRAPH_INFO.get(g_type)
   category_grouped_data = data.groupby("Category")["Amount"].sum()
   graph_options = option
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
   return fig

def metric_logic(data,opt,mode):
    current_month = pd.Period(datetime.now(), freq="M")
    current_day = datetime.now().day
    joined_date = data["Date"].min()
    joined_month = joined_date.to_period("M")
    joined_day = joined_date.day
    if mode == "Week":
        total = data["Amount"].sum()
        answer = round(total/7)
        score_board = data["Category"].value_counts()

    if mode == "Month":
         if opt == joined_month:
                  if joined_month == current_month:
                        days_amount = (current_day-joined_day ) + 1
                  elif joined_month != current_month:
                        days_amount = pd.Period(opt).days_in_month         
                    
         elif opt != current_month:
                    days_amount = pd.Period(opt).days_in_month
         elif opt == current_month:
                    days_amount = current_day
                
         total = data["Amount"].sum()
         answer = round(total/days_amount)
         score_board = data["Category"].value_counts()
    return total,answer,score_board

def rename_duplicates(data):
     grouped_data = data.groupby(["Type","Category"])["Amount"].sum().reset_index()
     duplicated_data = grouped_data.duplicated(subset="Category")    
     grouped_data.loc[duplicated_data,"Category"] = grouped_data["Category"]+"(" + grouped_data["Type"]+")"
     return grouped_data


def min_max_date(data,date_column,period:list):
    if len(period) > 0:
       option = [min(period),max(period)]
       data_a = data[data[date_column] == option[0]]
       data_b = data[data[date_column] == option[1]]
       return data_a,data_b,option

def all_categories(data):
     unique_categories = data["Category"].unique()
     all_categories = ["All categories"] + list(unique_categories)
     return all_categories

def income_vs_expense(data:list,periods:list,date_mode,date_column):
     data_0 = data[0][data[0]["Type"].isin(["Income","Expense"])]
     data_1 = data[1][data[1]["Type"].isin(["Income","Expense"])]
     baseline = simple_date(periods[0],mode=date_mode)
     subject = simple_date(periods[1],mode=date_mode)
     types_a = data_0.groupby("Type")["Amount"].sum().reset_index()
     types_b = data_1.groupby("Type")["Amount"].sum().reset_index()
     types_a[date_column] = baseline
     types_b[date_column] = subject
     overview_data = pd.concat([types_a,types_b],ignore_index=True)
     return overview_data,subject,baseline



def merge_periods(data:list):
     data_a,data_b = data[0],data[1]
     grouped_a = rename_duplicates(data_a)
     grouped_b = rename_duplicates(data_b)
     merged_period = pd.merge(grouped_a,grouped_b,how="outer",on="Category")
     merge_column(merged_period,["Type_x","Type_y"],"Type")
     merged_period = merged_period.fillna({"Amount_x" : 0,"Amount_y" : 0})
     merged_period["Analysis"] = merged_period.apply(analysis_column,axis=1)
     return merged_period

