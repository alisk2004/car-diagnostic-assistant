import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "car_diagnostic.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def is_seeded():
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) AS c FROM faults").fetchone()
    conn.close()
    return row["c"] > 0
