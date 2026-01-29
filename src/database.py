import sqlite3
import os
from datetime import datetime

DB_NAME = "ausentismo.db"

def get_connection():
    """Establece y devuelve una conexión a la base de datos SQLite."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa la base de datos con el esquema requerido."""
    schema = """
    CREATE TABLE IF NOT EXISTS agents (
      agent_id INTEGER PRIMARY KEY AUTOINCREMENT,
      acdid TEXT,
      payroll_number TEXT,
      last_name TEXT,
      first_name TEXT,
      mail TEXT,
      rut TEXT,
      site TEXT,
      status TEXT,
      hire_date TEXT,
      scheduled_hours REAL,
      raw_row_json TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS attendance_events (
      event_id INTEGER PRIMARY KEY AUTOINCREMENT,
      agent_id INTEGER,
      date TEXT,
      status_code TEXT,
      status_detail TEXT,
      source TEXT,
      created_by TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(agent_id) REFERENCES agents(agent_id)
    );

    CREATE TABLE IF NOT EXISTS login_logout (
      ll_id INTEGER PRIMARY KEY AUTOINCREMENT,
      agent_id INTEGER,
      date TEXT,
      login_time TEXT,
      logout_time TEXT,
      duration_minutes INTEGER,
      source_file TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(agent_id) REFERENCES agents(agent_id)
    );

    CREATE TABLE IF NOT EXISTS feedbacks (
      feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
      agent_id INTEGER,
      date TEXT,
      type TEXT,
      notes TEXT,
      created_by TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(agent_id) REFERENCES agents(agent_id)
    );

    CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance_events(date);
    CREATE INDEX IF NOT EXISTS idx_attendance_agent ON attendance_events(agent_id);
    CREATE INDEX IF NOT EXISTS idx_attendance_status ON attendance_events(status_code);
    """

    with get_connection() as conn:
        conn.executescript(schema)
        conn.commit()

if __name__ == "__main__":
    init_db()
    print("Base de datos inicializada correctamente.")
