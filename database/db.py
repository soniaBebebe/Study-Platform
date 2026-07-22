import sqlite3
import pandas as pd

DB_NAME = "study_os.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def run_query(query, params=()):
    with get_connection() as conn:
        cur=conn.cursor()
        cur.execute(query, params)
        conn.commit()

def load_df(query, params=()):
    with get_connection() as conn:
        return pd.read_sql(query, conn, params=params)