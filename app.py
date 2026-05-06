import sqlite3
from datetime import datetime, date
import pandas as pd
from pathlib import Path
import streamlit as st
import calendar
import streamlit.components.v1 as components

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
        if st.session_state.cal_month ==1:
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

    if col3.button("Next ->"):
        if st.session_state.cal_month ==12:
            st.session_state.cal_month=1
            st.session_state.cal_year +=1
        else:
            st.session_state.cal_month +=1
        st.rerun()

    tasks_by_date={}

    if not df.empty:
        
        for _, row in df.iterrows():
            if row["deadline"]:
                task_date=row["deadline"] 
                if task_date not in tasks_by_date:
                    tasks_by_date[task_date]=[]
                tasks_by_date[task_date].append({
                    "title": row["title"],
                    "course": row["course"],
                    "priority": row["priority"],
                    "status": row["status"]
                })
    week_days=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    cols=st.columns(7)
    for i, day_name in enumerate(week_days):
        cols[i].markdown(f"**{day_name}**")

    cal=calendar.Calendar(firstweekday=0)
    month_days=cal.monthdayscalendar(st.session_state.cal_year, st.session_state.cal_month)

    for week in month_days:
        week_cols=st.columns(7)

        for i, day_num in enumerate(week):
                with week_cols[i]:
                    if day_num==0:
                        st.markdown(
                            """
                            <div style="height:140px;
                            border: 1px solid #222;
                            border-radius: 12px;
                            background-color:#0f0f0f;
                            "></div>
                            """,
                            unsafe_allow_html=True
                        )   
                    else:
                        current_date=date(
                            st.session_state.cal_year,
                            st.session_state.cal_month,
                            day_num
                        ).isoformat()

                        day_tasks = tasks_by_date.get(current_date, [])

                        html = f"""
                        <div style="
                        min-height:140px;
                        border: 1px solid #333;
                        border-radius: 12px;
                        padding:10px;
                        margin-bottom:8px;
                        background-color:#111;
                        ">
                        <div style="
                        font-weight:bold;
                        font-size:18px;
                        margin-bottom:8px;
                        ">{day_num}</div>
                        """
                        for task in day_tasks:
                            if task["status"]=="Done":
                                color="#1f7a1f"
                                emoji="🟢"
                            elif task["status"] == "In Progress":
                                color="#9a7b00"
                                emoji="🟡"
                            else:
                                color="#8b1e1e"
                                emoji="🔴"
                            html += f"""
                            <div style="
                            background:{color};
                            color:white;
                            padding:6px 8px;
                            border-radius:8px;
                            margin-bottom:6px;
                            font-size:12px;
                            line-height:1.3;
                            ">
                            {emoji} {task['title']}<br>
                            <span style="opacity:0.9;">
                            {task['course']}
                            </span>
                            </div>
                            """
                            html += "</div>"
                        # st.markdown(html, unsafe_allow_html=True)
                        components.html(html, height=160)

if page=="Tasks":
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
                if col2.button("Delete", key=f"delete_{row['id']}"):
                    run_query("DELETE FROM tasks WHERE id=?", (row["id"],))
                    st.warning("Deleted!")
                    st.rerun()