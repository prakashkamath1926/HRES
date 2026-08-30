import json
import logging
import hashlib
from datetime import datetime
from typing import Optional

logger = logging.getLogger("hres.users")

# Try to import bcrypt for strong password hashing
try:
    import bcrypt as _bcrypt
    _HAS_BCRYPT = True
except ImportError:
    _HAS_BCRYPT = False
    logger.warning("bcrypt not installed — using SHA-256 fallback (run: pip install bcrypt for production)")


def _hash_password(password: str) -> str:
    if _HAS_BCRYPT:
        return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()
    return hashlib.sha256(password.encode()).hexdigest()


def _verify_password(password: str, hashed: str) -> bool:
    if _HAS_BCRYPT:
        try:
            return _bcrypt.checkpw(password.encode(), hashed.encode())
        except Exception:
            pass
    return hashlib.sha256(password.encode()).hexdigest() == hashed


def create_user(
    email: str,
    name: str,
    role: str = "civilian",
    org_type: Optional[str] = None,
    org_id: Optional[str] = None,
    password: Optional[str] = None,
    google_sub: Optional[str] = None,
    org_mail: Optional[str] = None,
    employee_id: Optional[str] = None,
) -> dict:
    """Create a new user. Returns the created user dict."""
    from backend.app.repositories.database import get_db_connection, execute_query
    conn, dialect = get_db_connection()
    cursor = conn.cursor()
    now = datetime.utcnow()

    password_hash = _hash_password(password) if password else None

    try:
        if dialect == "postgres":
            cursor.execute(
                """
                INSERT INTO users (email, name, password_hash, google_sub, role, org_type, org_id, org_mail, employee_id, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (email) DO NOTHING
                RETURNING id, email, name, role, org_type, org_id, org_mail, employee_id, created_at
                """,
                (email, name, password_hash, google_sub, role, org_type, org_id, org_mail, employee_id, now)
            )
            row = cursor.fetchone()
        else:
            cursor.execute(
                """
                INSERT OR IGNORE INTO users (email, name, password_hash, google_sub, role, org_type, org_id, org_mail, employee_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (email, name, password_hash, google_sub, role, org_type, org_id, org_mail, employee_id, now)
            )
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()

        conn.commit()
        if row:
            return _row_to_dict(row)
        return {}
    finally:
        conn.close()


def get_user_by_email(email: str) -> Optional[dict]:
    from backend.app.repositories.database import get_db_connection, execute_query
    conn, dialect = get_db_connection()
    cursor = conn.cursor()
    try:
        execute_query(cursor, "SELECT * FROM users WHERE email = ?", (email,), dialect=dialect)
        row = cursor.fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def get_user_by_google_sub(google_sub: str) -> Optional[dict]:
    from backend.app.repositories.database import get_db_connection, execute_query
    conn, dialect = get_db_connection()
    cursor = conn.cursor()
    try:
        execute_query(cursor, "SELECT * FROM users WHERE google_sub = ?", (google_sub,), dialect=dialect)
        row = cursor.fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def upsert_google_user(email: str, name: str, google_sub: str, picture: Optional[str] = None) -> dict:
    """Create or update a user who signed in with Google."""
    existing = get_user_by_email(email)
    if existing:
        # Update last_login and google_sub
        from backend.app.repositories.database import get_db_connection, execute_query
        conn, dialect = get_db_connection()
        cursor = conn.cursor()
        try:
            execute_query(cursor,
                "UPDATE users SET last_login = ?, google_sub = ? WHERE email = ?",
                (datetime.utcnow(), google_sub, email),
                dialect=dialect
            )
            conn.commit()
        finally:
            conn.close()
        existing["google_sub"] = google_sub
        return existing
    else:
        return create_user(email=email, name=name, google_sub=google_sub, role="civilian")


def authenticate_email_password(email: str, password: str) -> Optional[dict]:
    """Returns user dict if credentials valid, None otherwise."""
    from backend.app.repositories.database import get_db_connection, execute_query
    conn, dialect = get_db_connection()
    cursor = conn.cursor()
    try:
        execute_query(cursor, "SELECT * FROM users WHERE email = ?", (email,), dialect=dialect)
        row = cursor.fetchone()
        if not row or not row["password_hash"]:
            return None
        if _verify_password(password, row["password_hash"]):
            _update_last_login(email)
            return _row_to_dict(row)
        return None
    finally:
        conn.close()


def _update_last_login(email: str):
    from backend.app.repositories.database import get_db_connection, execute_query
    conn, dialect = get_db_connection()
    cursor = conn.cursor()
    try:
        execute_query(cursor,
            "UPDATE users SET last_login = ? WHERE email = ?",
            (datetime.utcnow(), email),
            dialect=dialect
        )
        conn.commit()
    finally:
        conn.close()


def _row_to_dict(row) -> dict:
    if hasattr(row, "keys"):
        d = dict(row)
    else:
        # sqlite3.Row
        d = {k: row[k] for k in row.keys()}
    # Remove sensitive fields
    d.pop("password_hash", None)
    return d

def update_user_profile(email: str, org_mail: Optional[str] = None, employee_id: Optional[str] = None) -> Optional[dict]:
    """Update user's profile information."""
    from backend.app.repositories.database import get_db_connection, execute_query
    conn, dialect = get_db_connection()
    cursor = conn.cursor()
    try:
        execute_query(cursor,
            "UPDATE users SET org_mail = ?, employee_id = ? WHERE email = ?",
            (org_mail, employee_id, email),
            dialect=dialect
        )
        conn.commit()
        return get_user_by_email(email)
    finally:
        conn.close()
