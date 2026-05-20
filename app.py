import sqlite3
from datetime import datetime, date
import pandas as pd
from pathlib import Path
import streamlit as st
import calendar
import streamlit.components.v1 as components
import base64

DB_PATH="study_os.db"

def get_conn():
    conn=sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory=sqlite3.Row
    return conn

def play_sound(file_path):
    with open(file_path, "rb") as audio_file:
        audio_bytes=audio_file.read()
    
    b64=base64.b64encode(audio_bytes).decode()

    md=f"""
        <audio autoplay>
            <source src="data:audio/mp3; base64,{b64}" type="audio/mp3">
        </audio>
        """
    st.markdown(md, unsafe_allow_html=True)

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
    
    cur.execute("""
                CREATE TABLE IF NOT EXISTS notes(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
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
st.markdown("""
            <style>
            
            .stApp{
            background:linear-gradient(
            180deg,
            #0b0f19 0%,
            #111827 100%
            );
            color:white;
            }
            
            section[data-testid="stSidebar"]{
            background-color: #0f172a;
            border-right:1px solid #1e293b;
            }

            section[data-testid="stSidebar"]*{
            color:white !important;
            }

            .stButton>button{
            width:100%;
            border-radius:12px;
            border:1px solid #334155;
            background-color:#111827;
            color:white;
            transitin: all 0.2s ease-in-out;
            }

            .stButton>button:hover{
            transform:translateY(-2px);
            background-color:#1e293b;
            border-color:#60a5fa;
            box-shadow: 0 4px 12px rgba(96,165,250,0.25);
            }

            .stTextInput input, 
            .stTextArea textarea{
            border-radius:12px !important;
            background-color:#111827 !important;
            color:white !important;
            border:1px solid #334155 !important;
            }

            .stSelectbox div[data-baseweb="select"]{
            background-color:#111827 !important;
            border-redius:12px !important;
            }

            [data-testid="stMetric"]{
            background:rgba(17,24,39,0.7);
            border:1px solid #334155;
            padding:16px;
            border-redius:16px;
            background-filter:blur(12px);
            }

            .streamlit-expanderHeader{
            background-color:#111827;
            border-radius:10px;
            }

            div[data-testid="column"]>div{
            transition:all 0.2s easi-in-out;
            }

            div[data-testid="column"]>div:hover{
            transform:scale(1.02);
            }

            ::-webkit-scrollbar{
            width:10px;
            }

            ::-webkit-scrollbar-track{
            background:#0f172a;
            }

            ::-webkit-scrollbar-thumb{
            background:#334155;
            border-radius:10px;
            }

            ::-webkit-scrollbar-thumb:hover{
            background:#475569;
            }
            )
            </style>
            """,
            unsafe_allow_html=True)

st.sidebar.title("Study OS")
page=st.sidebar.radio("Navigation",  ["Dashboard", "Tasks", "Calendar", "Files", "Notes", "Focus"])

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

if page=="Files":
    st.title("File Manager")

    upload_dir=Path("uploads")
    upload_dir.mkdir(exist_ok=True)

    uploaded_file=st.file_uploader(
        "Upload lecture notes or PDFs",
        type=["pdf", "txt", "docx", "png", "jpg"]
    )

    if uploaded_file is not None:
        save_path=upload_dir/uploaded_file.name
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"Uploaded: {uploaded_file.name}")
    
    st.divider()

    files=list(upload_dir.glob("*"))

    if not files:
        st.info("No uploaded files")
    else:
        st.subheader("Your Files")

        for file in files:
            col1,col2,col3, col4=st.columns([4,1,1,1])
            col1.markdown(f"{file.name}")

            with open(file,"rb") as f:
                col2.download_button(
                    "Download",
                    data=f,
                    file_name=file.name,
                    key=f"download_{file.name}"
                )
            if file.suffix==".pdf":
                if col3.button("Preview", key=f"preview_{file.name}"):

                    with open(file,"rb") as pdf_file:
                        base64_pdf=base64.b64encode(pdf_file.read()).decode("utf-8")
                    pdf_display=f"""
                    <iframe
                    src="data:application/pdf;base64,{base64_pdf}"
                    width="100%"
                    height="800px"
                    type="application/pdf">
                    </iframe>
                    """
                    st.markdown(pdf_display, unsafe_allow_html=True)

            if col3.button("Delete", key=f"delete_{file.name}"):
                file.unlink()
                st.rerun()

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
if page=="Notes":
    st.title("Notes System")
    st.subheader("Create Note")

    note_title=st.text_input("Note Title")

    note_content=st.text_area(
        "Markdown Content",
        height=300
    )
    col1, col2 = st.columns(2)

    if col1.button("Save Note"):
        if note_title:
            run_query(
                """
                INSERT INTO notes(title,content,created_at)
                VALUES(?,?,?)
                """,
                (
                    note_title,
                    note_content,
                    datetime.now().isoformat()
                )
            )
            st.success("Note saved!!")
            st.rerun()

    st.subheader("Live Preview")
    st.markdown(note_content)
    st.divider()

    notes_df=pd.read_sql_query(
        "SELECT * FROM notes ORDER BY created_at DESC",
        get_conn()
    )

    st.subheader("Your Notes")

    if notes_df.empty:
        st.info("No notes yet :(")
    else:
        for _, note in notes_df.iterrows():
            with st.expander(f"{note['title']}"):
                st.markdown(note["content"])
                col1,col2=st.columns(2)

                if col2.button(
                    "Delete",
                    key=f"delete_note_{note['id']}"
                ):
                    run_query(
                        "DELETE FROM notes WHERE id=?",
                        (note["id"],)
                    )

                    st.rerun()

if page=="Focus":
    st.title("Focus Mode")
    st.subheader("Pomodoro Timer")

    if "focus_running" not in st.session_state:
        st.session_state.focus_running=False
    
    if "focus_seconds" not in st.session_state:
        st.session_state.focus_seconds=0.1*60
    
    if "focus_sessions" not in st.session_state:
        st.session_state.focus_sessions=0

    minutes=st.session_state.focus_seconds //60
    seconds = st.session_state.focus_seconds %60

    st.markdown(
        f"""
        <h1 style='text-align:center;
            font-size:80px;'>
            {minutes:02}:{seconds:02}
        </h1>
        """,
        unsafe_allow_html=True
    )

    col1,col2,col3=st.columns(3)

    if col1.button("Start"):
        st.session_state.focus_running=True
    
    if col2.button("Pause"):
        st.session_state.focus_running=False
    
    if col3.button("Reset"):
        st.session_state.focus_running=False
        st.session_state.focus_seconds=0.1*60

    if st.session_state.focus_running:
        import time

        time.sleep(1)

        st.session_state.focus_seconds-=1
        if st.session_state.focus_seconds<=0:
            st.session_state.focus_running=False
            st.session_state.focus_sessions +=1

            st.success("Focus Session Completed!")
            play_sound("sounds/barkfart.mp3")
            st.balloons()
            st.session_state.focus_seconds=0.5*60
        
        st.rerun()
    
    st.divider()
    st.subheader("Focus Statistics")

    st.metric(
        "Completed Sessions",
        st.session_state.focus_sessions
    )