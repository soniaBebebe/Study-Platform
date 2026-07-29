from database.db import load_df, run_query
from datetime import datetime

def get_tasks():
    return load_df("""
        SELECT *
        FROM tasks
        ORDER BY created_at DESC
    """)