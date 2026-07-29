from datetime import datetime, date

def days_left(deadline_str):
    if not deadline_str:
        return None

    d=datetime.strptime(deadline_str, "%Y-%m-%d").date()
    return (d-date.today()).days