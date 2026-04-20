import sqlite3
from datetime import datetime, date
import pandas as pd
from pathlib import Path
import streamlit as st
import calendar

DB_PATH="study_os.db"

def get_conn():
    conn=sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory=sqlite3.Row
    return conn

def init_db():
    conn=get_conn()
    cur=conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                course TEXT,
                priority TEXT,
                deadline TEXT,
                status TEXT,
                notes TEXT,
                created_at TEXT
                )
                """)
    conn.commit()
    conn.close()

init_db()

def days_left(deadline_str):
    if not deadline_str:
        return None
    d=datetime.strptime(deadline_str, "%Y-%m-%d").date()
    return (d-date.today()).days

def run_query(query, params=(), fetch=False):
    conn=get_conn()
    cur=conn.cursor()
    cur.execute(query,params)
    rows=cur.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return rows

def load_df():
    conn=get_conn()
    df=pd.read_sql_query("SELECT * FROM tasks", conn)
    conn.close()
    return df

st.set_page_config(page_title="Study OS", layout="wide")

st.sidebar.title("Study OS")
page=st.sidebar.radio("Navigation",  ["Dashboard", "Tasks", "Calendar"])

if page=="Dashboard":
    st.title("Study OS Dashboard")
    df=load_df()
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

        col1.metric("Total Tasks", total_tasks)
        col2.metric("Done", done_tasks)
        col3.metric("Urgent", urgent)
        col4.metric("Overdue", overdue)

        st.divider()

        st.subheader("Activity Cahrt")

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

if page=="Calendar":
    st.title("calendar")

    df=load_df()

    if "cal_month" not in st.session_state:
        st.session_state.cal_month = date.today().month
    if "cal_year" not in st.session_state:
        st.session_state.cal_year = date.today().year

    col1, col2, col3 = st.columns([1,2,1])

    if col1.button("<- Previous"):
        if st.session_state.cal_mont ==1:
            st.session_state.cal_month =12
            st.session_state.cal_year-=1
        else:
            st.session_state.cal_month-=1
        st.rerun()

    with col2:
        month_name=calendar.month_name[st.session_state.cal_month]
        st.markdown(
            f"<h2 style='text-align:center;'> {month_name} {st.session_state.cal_year} </h2>",
            unsafe_allow_html=True
        )

    if df.empty:
        st.info("No tasks with dates")
    else:
        events=[]
        
        for _, row in df.iterrows():
            if row["deadline"]:
                events.append({
                    "Date": row["deadline"],
                    "Task": row["title"],
                    "Course": row["course"],
                    "Priority": row["priority"],
                    "Status": row["status"]
                })
        
        if events:
            cal_df=pd.DataFrame(events)
            cal_df=cal_df.sort_values(by="Date")

            st.subheader("Upcoming Tasks")
            st.dataframe(cal_df, use_container_width=True)

            st.subheader("By Date")

            grouped=cal_df.groupby("Date")

            for date_key, group in grouped:
                st.markdown(f"### {date_key}")

                for _, task in group.iterrows():
                    if task["Status"]=="Done":
                        color="🟢"
                    elif task["Status"] == "In Progress":
                        color="🟡"
                    else:
                        color="🔴"
                    st.markdown(f"""
                    - **{task['Task']}**
                    {task['Course']} | {task['Priority']} | {task['Status']}            
                    """)
        
        else:
            st.info("no deadlines yet")

if page=="Tasks":
    st.title("Task Manager")
    with st.form("add_task"):
        title=st.text_input("Name")
        course=st.text_input("subject")
        priority=st.selectbox("Priority", ["high", "Medium", "Low"])
        deadline=st.date_input("Deadline")
        status=st.selectbox("Status", ["Open", "In Progress", "Done"])

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
                    "Status", ["Open", "In Progress", "Done"],
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
                if col2.button("Delete", key=f"delete_{row['id']}"):
                    run_query("DELETE FROM tasks WHERE id=?", (row["id"],))
                    st.warning("Deleted!")
                    st.rerun()