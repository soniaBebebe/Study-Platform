import streamlit as st
import pandas as pd
from utils.helpers import days_left

from datetime import datetime, date
from database.db import load_df
from components.ui import dashboard_card

st.title("Study OS Dashboard")
df=load_df("""SELECT * FROM tasks""")
total_tasks=len(df)

if df.empty:
    st.info("No Data Yet")
else:
    done_tasks = len(df[df["status"]=="Done"])
    open_tasks = len(df[df["status"]!="Done"])

    urgent=0
    overdue=0

    for _, row in df.iterrows():
        dl=days_left(row["deadline"])
        if dl is not None and row["status"]!= "Done":
            if dl<0:
                overdue+=1
            elif dl<=1:
                urgent +=1
    
    col1, col2, col3, col4=st.columns(4)

    # col1.metric("Total Tasks", total_tasks)
    # col2.metric("Done", done_tasks)
    # col3.metric("Urgent", urgent)
    # col4.metric("Overdue", overdue)

    dashboard_card(
        col1,
        "Total Tasks",
        total_tasks,
        "All created tasks",
    )
    dashboard_card(
        col2,
        "Done",
        done_tasks,
        "Completed tasks",
    )
    dashboard_card(
        col3,
        "Urgent",
        urgent,
        "Due today or tomorrow",
    )
    dashboard_card(
        col4,
        "Overdue",
        overdue,
        "Missed deadlines",
    )

    st.divider()

    st.subheader("Activity Chart")

    if not df.empty:
        df["created_at"] = pd.to_datetime(df["created_at"])

        activity = df.groupby(df["created_at"].dt.date).size()

        st.line_chart(activity)
    else: 
        st.info("No activity yet")

    st.subheader("Recent Tasks")
    recent = df.sort_values(by="created_at", ascending=False).head(5)

    for _, row in recent.iterrows():
        st.markdown(f"""
        **{row['title']}**
        {row['course']} | {row['deadline']} | {row['status']}            
        """)
