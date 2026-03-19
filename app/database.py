import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id              SERIAL PRIMARY KEY,
            phone           TEXT NOT NULL,
            address         TEXT,
            lat             DOUBLE PRECISION,
            lng             DOUBLE PRECISION,
            location_method TEXT,
            description     TEXT,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def save_report(phone: str, address: str, lat: float, lng: float,
                location_method: str, description: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO reports (phone, address, lat, lng, location_method, description)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (phone, address, lat, lng, location_method, description))
    conn.commit()
    cur.close()
    conn.close()


def _build_where(date_from, date_to):
    conditions = []
    params = []
    if date_from:
        conditions.append("created_at >= %s")
        params.append(date_from)
    if date_to:
        conditions.append("created_at <= %s")
        params.append(date_to + "T23:59:59")
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    return where, params


def get_all_reports(date_from: str = None, date_to: str = None):
    where, params = _build_where(date_from, date_to)
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(f"""
        SELECT id, phone, address, lat, lng, location_method, description,
               to_char(created_at AT TIME ZONE 'America/Bogota', 'YYYY-MM-DD"T"HH24:MI:SS') AS created_at
        FROM reports {where}
        ORDER BY created_at DESC
    """, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


def get_stats(date_from: str = None, date_to: str = None):
    where, params = _build_where(date_from, date_to)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM reports {where}", params)
    total = cur.fetchone()[0]
    cur.execute(f"""
        SELECT location_method, COUNT(*) as count
        FROM reports {where}
        GROUP BY location_method
    """, params)
    by_method = [{"location_method": r[0], "count": r[1]} for r in cur.fetchall()]
    cur.close()
    conn.close()
    return {"total": total, "by_method": by_method}
