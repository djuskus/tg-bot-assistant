import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(os.environ.get("BRAIN_DB", "/app/data/brain.db"))


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                day TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                message TEXT NOT NULL,
                day TEXT NOT NULL
            )
        """)


def current_day() -> str:
    now = datetime.now()
    if now.hour < 3:
        now -= timedelta(days=1)
    return now.strftime("%Y-%m-%d")


def add_log(message: str) -> str:
    now = datetime.now()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO logs (timestamp, message, day) VALUES (?, ?, ?)",
            (now.isoformat(timespec="seconds"), message, current_day()),
        )
    return now.strftime("%H:%M")


def add_plan(title: str, start_time: str, end_time: str, day: str = None):
    day = day or current_day()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO plans (title, start_time, end_time, day) VALUES (?, ?, ?, ?)",
            (title, start_time, end_time, day),
        )


def get_plans(day: str = None) -> list:
    day = day or current_day()
    with get_conn() as conn:
        return conn.execute(
            "SELECT title, start_time, end_time FROM plans WHERE day = ? ORDER BY start_time",
            (day,),
        ).fetchall()


def get_logs(day: str = None) -> list:
    day = day or current_day()
    with get_conn() as conn:
        return conn.execute(
            "SELECT timestamp, message FROM logs WHERE day = ? ORDER BY timestamp",
            (day,),
        ).fetchall()
