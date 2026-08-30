import os
import json
from datetime import datetime
from backend.app.core.config import settings

# Determine dialect
IS_POSTGRES = settings.DATABASE_URL.startswith("postgres")


def get_db_connection():
    if IS_POSTGRES:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn = psycopg2.connect(settings.DATABASE_URL, cursor_factory=RealDictCursor)
        return conn, "postgres"
    else:
        import sqlite3
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn, "sqlite"


def execute_query(cursor, query: str, params: tuple = (), dialect: str = "sqlite"):
    if dialect == "postgres":
        # Replace ? placeholders with %s
        pg_query = query.replace("?", "%s")
        # Convert SQLite INSERT OR REPLACE to PostgreSQL INSERT ... ON CONFLICT DO NOTHING
        if "INSERT OR REPLACE INTO" in pg_query:
            pg_query = pg_query.replace("INSERT OR REPLACE INTO", "INSERT INTO")
            # Append ON CONFLICT DO NOTHING after the closing VALUES parenthesis
            pg_query = pg_query.rstrip()
            if not pg_query.upper().endswith("DO NOTHING"):
                pg_query += " ON CONFLICT DO NOTHING"
        cursor.execute(pg_query, params)
    else:
        cursor.execute(query, params)


def _column_exists(cursor, table: str, column: str, dialect: str) -> bool:
    """Check if a column exists in a table (for safe migrations)."""
    if dialect == "postgres":
        cursor.execute(
            "SELECT 1 FROM information_schema.columns WHERE table_name=%s AND column_name=%s",
            (table, column)
        )
        return cursor.fetchone() is not None
    else:
        rows = cursor.execute(f"PRAGMA table_info({table})").fetchall()
        return any(r[1] == column for r in rows)


def _table_exists(cursor, table: str, dialect: str) -> bool:
    """Check if a table exists."""
    if dialect == "postgres":
        cursor.execute(
            "SELECT 1 FROM information_schema.tables WHERE table_name=%s",
            (table,)
        )
        return cursor.fetchone() is not None
    else:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        return cursor.fetchone() is not None


def init_db():
    conn, dialect = get_db_connection()
    cursor = conn.cursor()

    if dialect == "sqlite":
        autoincrement_pk = "INTEGER PRIMARY KEY AUTOINCREMENT"
        on_conflict = "ON DELETE CASCADE"
    else:
        autoincrement_pk = "SERIAL PRIMARY KEY"
        on_conflict = "ON DELETE CASCADE"

    # ── Users table ───────────────────────────────────────────────────────────
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS users (
        id {autoincrement_pk},
        email TEXT UNIQUE NOT NULL,
        name TEXT,
        password_hash TEXT,
        google_sub TEXT,
        role TEXT NOT NULL DEFAULT 'civilian',
        org_type TEXT,
        org_id TEXT,
        org_mail TEXT,
        employee_id TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    );
    """)

    # ── Incidents table ────────────────────────────────────────────────────────
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        incident_id TEXT PRIMARY KEY,
        status TEXT NOT NULL,
        risk TEXT,
        action_proposal TEXT,
        routes TEXT,
        created_at TIMESTAMP NOT NULL,
        updated_at TIMESTAMP NOT NULL
    );
    """)

    # ── Observations table ─────────────────────────────────────────────────────
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS observations (
        observation_id TEXT PRIMARY KEY,
        incident_id TEXT NOT NULL,
        source TEXT NOT NULL,
        data_mode TEXT NOT NULL,
        event_type TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        address TEXT,
        location_source TEXT NOT NULL,
        location_timestamp TIMESTAMP NOT NULL,
        observed_at TIMESTAMP NOT NULL,
        received_at TIMESTAMP NOT NULL,
        value TEXT NOT NULL,
        confidence REAL NOT NULL,
        raw_payload TEXT
    );
    """)

    # ── Normalized Events table ────────────────────────────────────────────────
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS normalized_events (
        event_id TEXT PRIMARY KEY,
        incident_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        address TEXT,
        location_source TEXT NOT NULL,
        location_timestamp TIMESTAMP NOT NULL,
        status TEXT NOT NULL,
        confidence REAL NOT NULL,
        value TEXT NOT NULL,
        supporting_observations TEXT NOT NULL,
        web_verification TEXT,
        false_alarm_report TEXT
    );
    """)

    # ── Approvals table ────────────────────────────────────────────────────────
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS approvals (
        incident_id TEXT PRIMARY KEY,
        decision TEXT NOT NULL,
        comment TEXT,
        operator_id TEXT,
        proposal_version INTEGER NOT NULL,
        timestamp TIMESTAMP NOT NULL
    );
    """)

    # ── Audit Events table ─────────────────────────────────────────────────────
    if dialect == "sqlite":
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            event_type TEXT NOT NULL,
            message TEXT NOT NULL,
            payload TEXT
        );
        """)
    else:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_events (
            id SERIAL PRIMARY KEY,
            incident_id TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            event_type TEXT NOT NULL,
            message TEXT NOT NULL,
            payload TEXT
        );
        """)

    # ── After-Action Reports table ─────────────────────────────────────────────
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS after_action_reports (
        incident_id TEXT PRIMARY KEY,
        content TEXT NOT NULL,
        generated_at TIMESTAMP NOT NULL
    );
    """)

    # ── Safe migrations: add columns if they don't exist ──────────────────────
    if dialect == "sqlite":
        existing = {row[1] for row in cursor.execute("PRAGMA table_info(normalized_events)").fetchall()}
        if "web_verification" not in existing:
            cursor.execute("ALTER TABLE normalized_events ADD COLUMN web_verification TEXT;")
        if "false_alarm_report" not in existing:
            cursor.execute("ALTER TABLE normalized_events ADD COLUMN false_alarm_report TEXT;")
            
        existing_users = {row[1] for row in cursor.execute("PRAGMA table_info(users)").fetchall()}
        if "org_mail" not in existing_users:
            cursor.execute("ALTER TABLE users ADD COLUMN org_mail TEXT;")
        if "employee_id" not in existing_users:
            cursor.execute("ALTER TABLE users ADD COLUMN employee_id TEXT;")
    else:
        # PostgreSQL migrations
        if not _column_exists(cursor, "normalized_events", "web_verification", dialect):
            cursor.execute("ALTER TABLE normalized_events ADD COLUMN web_verification TEXT;")
        if not _column_exists(cursor, "normalized_events", "false_alarm_report", dialect):
            cursor.execute("ALTER TABLE normalized_events ADD COLUMN false_alarm_report TEXT;")
            
        if not _column_exists(cursor, "users", "org_mail", dialect):
            cursor.execute("ALTER TABLE users ADD COLUMN org_mail TEXT;")
        if not _column_exists(cursor, "users", "employee_id", dialect):
            cursor.execute("ALTER TABLE users ADD COLUMN employee_id TEXT;")

    conn.commit()
    conn.close()
