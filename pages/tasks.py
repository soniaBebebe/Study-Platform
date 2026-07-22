import streamlit as st
import pandas as pd
from app import load_df, run_query, days_left

from datetime import datetime, date
from database.db import run_query, load_df

def show():
    st.title("Task Manager")
    with st.form("add_task"):
        title=st.text_input("Name")
        course=st.text_input("subject")
        priority=st.selectbox("Priority", ["High", "Medium", "Low"])
        deadline=st.date_input("Deadline")
        status=st.selectbox("status", ["Open", "In Progress", "Done"])

        if st.form_submit_button("Add"):
            if title:
                run_query(
                    "INSERT INTO tasks(title,course,priority,deadline, status, created_at) VALUES(?,?,?,?,?,?)",
                    (title, course, priority, deadline.isoformat(), status, datetime.now().isoformat())
                )
                st.success("The task was added")
                st.rerun()
    df=load_df()

    urgent_tasks=[]

    for _, row in df.iterrows():
        dl=days_left(row["deadline"])

        if dl is not None and row["status"]!="Done":
            if dl <= 1:
                urgent_tasks.append((row, dl))
    if not urgent_tasks:
        st.success("No urgent Tasks!")
    else:
        for row, dl in urgent_tasks:
            if dl <0:
                st.error(f"{row['title']} (is late for {abs(dl)} days.)")
            elif dl==0:
                st.warning(f"{row['title']} (due today)")
            else:
                st.info(f"{row['title']} (due tomorrow)")

    if df.empty:
        st.info("No tasks")
    else:
        for _, row in df.iterrows():
            with st.expander(f"{row['title']} | {row['status']}"):
                new_title=st.text_input("Name", value=row["title"], key=f"title_{row['id']}")
                new_course=st.text_input("Subject", value=row["course"], key=f"course_{row['id']}")
                new_priority=st.selectbox(
                    "Priority", ["High", "Medium", "Low"],
                    index=["High", "Medium", "Low"].index(row["priority"].capitalize()),
                    key=f"priority_{row['id']}"
                )
                new_status=st.selectbox(
                    "status", ["Open", "In Progress", "Done"],
                    index=["Open", "In Progress", "Done"].index(row["status"]),
                    key=f"status_{row['id']}"
                )
                new_deadline=st.date_input(
                    "Deadline",
                    value=date.fromisoformat(row["deadline"]) if row["deadline"] else date.today(),
                    key=f"deadline_{row['id']}"
                )
                col1, col2=st.columns(2)
                if col1.button("Save", key=f"save_{row['id']}"):
                    run_query(
                        """UPDATE tasks
                        SET title=?, course=?, priority=?, status=?, deadline=?
                        WHERE id=?""",
                        (
                            new_title,
                            new_course,
                            new_priority,
                            new_status,
                            new_deadline.isoformat(),
                            row["id"]
                        )
                    )
                    st.success("Updated!")
                    st.rerun()
                with col2:
                    with stylable_container(
                        key=f"task_delete_container_{row['id']}",
                        css_styles="""
                        button{
                            background-color:#990000;
                            color:white;
                        }
                        """
                    ):
                        if st.button("Delete", key=f"delete_{row['id']}"):
                            run_query("DELETE FROM tasks WHERE id=?", (row["id"],))
                            st.warning("Deleted!")
                            st.rerun()