import datetime

def get_current_week() -> int:
    now = datetime.datetime.now()
    year, week, _ = now.isocalendar()

    return year * 100 + week