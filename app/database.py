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
            problem_type    TEXT,
            frequency       TEXT,
            address         TEXT,
            lat             DOUBLE PRECISION,
            lng             DOUBLE PRECISION,
            location_method TEXT,
            description     TEXT,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    # Migración segura para instancias ya existentes
    for col, typedef in [
        ("problem_type", "TEXT"),
        ("frequency", "TEXT"),
        ("voice_rating", "SMALLINT"),
        ("data_rating", "SMALLINT"),
        ("has_problem", "BOOLEAN"),
    ]:
        cur.execute(f"ALTER TABLE reports ADD COLUMN IF NOT EXISTS {col} {typedef}")
    conn.commit()
    cur.close()
    conn.close()


def save_report(phone: str, voice_rating: int, data_rating: int,
                has_problem: bool, problem_type: str, frequency: str,
                address: str, lat: float, lng: float,
                location_method: str, description: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO reports (phone, voice_rating, data_rating, has_problem,
                             problem_type, frequency, address, lat, lng, location_method, description)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (phone, voice_rating, data_rating, has_problem,
          problem_type, frequency, address, lat, lng, location_method, description))
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
        SELECT id, phone, voice_rating, data_rating, has_problem,
               problem_type, frequency, address, lat, lng,
               location_method, description,
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
    # where_problem filtra solo los que tienen problemas
    problem_cond = "has_problem = TRUE"
    where_problem = ("WHERE " + problem_cond) if not where else (where + " AND " + problem_cond)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(f"SELECT COUNT(*) FROM reports {where}", params)
    total = cur.fetchone()[0]

    cur.execute(f"SELECT COUNT(*) FROM reports {where_problem}", params)
    with_problems = cur.fetchone()[0]

    cur.execute(f"SELECT ROUND(AVG(voice_rating), 1) FROM reports {where}", params)
    avg_voice = float(cur.fetchone()[0] or 0)

    cur.execute(f"SELECT ROUND(AVG(data_rating), 1) FROM reports {where}", params)
    avg_data = float(cur.fetchone()[0] or 0)

    # Distribución calificaciones voz (1-10)
    voice_cond = "voice_rating IS NOT NULL"
    where_voice = ("WHERE " + voice_cond) if not where else (where + " AND " + voice_cond)
    cur.execute(f"""
        SELECT voice_rating, COUNT(*) as count FROM reports {where_voice}
        GROUP BY voice_rating ORDER BY voice_rating
    """, params)
    voice_dist = {str(r[0]): r[1] for r in cur.fetchall()}

    # Distribución calificaciones datos (1-10)
    data_cond = "data_rating IS NOT NULL"
    where_data = ("WHERE " + data_cond) if not where else (where + " AND " + data_cond)
    cur.execute(f"""
        SELECT data_rating, COUNT(*) as count FROM reports {where_data}
        GROUP BY data_rating ORDER BY data_rating
    """, params)
    data_dist = {str(r[0]): r[1] for r in cur.fetchall()}

    # Distribución tipo de problema (solo con problemas)
    where_prob_type = where_problem + " AND problem_type IS NOT NULL"
    cur.execute(f"""
        SELECT problem_type, COUNT(*) as count FROM reports {where_prob_type}
        GROUP BY problem_type ORDER BY count DESC
    """, params)
    by_problem = [{"label": r[0], "count": r[1]} for r in cur.fetchall()]

    # Distribución frecuencia (solo con problemas)
    where_freq = where_problem + " AND frequency IS NOT NULL"
    cur.execute(f"""
        SELECT frequency, COUNT(*) as count FROM reports {where_freq}
        GROUP BY frequency ORDER BY count DESC
    """, params)
    by_frequency = [{"label": r[0], "count": r[1]} for r in cur.fetchall()]

    cur.close()
    conn.close()
    return {
        "total": total,
        "with_problems": with_problems,
        "avg_voice": avg_voice,
        "avg_data": avg_data,
        "voice_dist": voice_dist,
        "data_dist": data_dist,
        "by_problem": by_problem,
        "by_frequency": by_frequency,
    }
