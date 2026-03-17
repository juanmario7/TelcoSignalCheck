import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "reports.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            phone       TEXT NOT NULL,
            address     TEXT,
            lat         REAL,
            lng         REAL,
            location_method TEXT,  -- 'gps' or 'address'
            description TEXT,
            created_at  TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_report(phone: str, address: str, lat: float, lng: float,
                location_method: str, description: str):
    conn = get_connection()
    conn.execute("""
        INSERT INTO reports (phone, address, lat, lng, location_method, description, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (phone, address, lat, lng, location_method, description, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def get_all_reports():
    conn = get_connection()
    rows = conn.execute("""
        SELECT id, phone, address, lat, lng, location_method, description, created_at
        FROM reports
        ORDER BY created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats():
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    by_method = conn.execute("""
        SELECT location_method, COUNT(*) as count
        FROM reports GROUP BY location_method
    """).fetchall()
    conn.close()
    return {"total": total, "by_method": [dict(r) for r in by_method]}
