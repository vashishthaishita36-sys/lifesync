import os

import sqlite3
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "lifesync.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date TEXT NOT NULL UNIQUE,
            bedtime TEXT NOT NULL,
            bedtime_num REAL NOT NULL,
            sleep_hours REAL NOT NULL,
            study_hours REAL NOT NULL,
            tasks_planned INTEGER NOT NULL,
            tasks_completed INTEGER NOT NULL,
            exercise_minutes INTEGER NOT NULL,
            screen_hours REAL NOT NULL,
            spending REAL NOT NULL,
            productivity_score INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def bedtime_to_number(bedtime):
    hour, minute = map(int, bedtime.split(":"))
    value = hour + minute / 60
    if value < 18:
        value += 24
    return round(value - 18, 2)


def save_entry(e):
    conn = get_connection()
    conn.execute("""
        INSERT INTO daily_logs
        (entry_date, bedtime, bedtime_num, sleep_hours, study_hours,
         tasks_planned, tasks_completed, exercise_minutes,
         screen_hours, spending, productivity_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(entry_date) DO UPDATE SET
            bedtime=excluded.bedtime,
            bedtime_num=excluded.bedtime_num,
            sleep_hours=excluded.sleep_hours,
            study_hours=excluded.study_hours,
            tasks_planned=excluded.tasks_planned,
            tasks_completed=excluded.tasks_completed,
            exercise_minutes=excluded.exercise_minutes,
            screen_hours=excluded.screen_hours,
            spending=excluded.spending,
            productivity_score=excluded.productivity_score
    """, (
        e["entry_date"], e["bedtime"], bedtime_to_number(e["bedtime"]),
        e["sleep_hours"], e["study_hours"], e["tasks_planned"],
        e["tasks_completed"], e["exercise_minutes"], e["screen_hours"],
        e["spending"], e["productivity_score"],
    ))
    conn.commit()
    conn.close()


def get_all_entries():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM daily_logs ORDER BY entry_date DESC"
    ).fetchall()
    conn.close()
    return rows


if __name__ == "__main__":
    init_db()
    save_entry({
        "entry_date": "2026-10-28", "bedtime": "23:30",
        "sleep_hours": 6.5, "study_hours": 4, "tasks_planned": 5,
        "tasks_completed": 4, "exercise_minutes": 30,
        "screen_hours": 3, "spending": 150, "productivity_score": 7,
    })
    for row in get_all_entries():
        print(dict(row))