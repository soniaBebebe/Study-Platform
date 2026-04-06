import sqlite3
from datetime import datetime, date
import pandas as pd
from pathlib import Path

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

