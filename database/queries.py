from database.db import run_query, load_df

def get_tasks():
    return load_df(
        """
        SELECT * FROM tasks ORDER BY due_date
        """
    )

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
        (task_id),
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