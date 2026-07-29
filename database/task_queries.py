from database.db import load_df, run_query
from datetime import datetime

def get_tasks():
    return load_df("""
        SELECT *
        FROM tasks
        ORDER BY created_at DESC
    """)

def add_task(title, priority, due_date):
    run_query(
        """
        INSERT INTO tasks(
            title,
            priority,
            due_date
        )
        VALUES(?,?,?)
        """,
        (title, priority, due_date),
    )

def delete_task(task_id):
    run_query(
        """
        DELETE FROM tasks
        WHERE id=?
        """,
        (task_id,)
    )

def complete_task(task_id):
    run_query(
        """
        UPDATE tasks
        SET status='Done'
        WHERE id=?
        """,
        (task_id)
    )