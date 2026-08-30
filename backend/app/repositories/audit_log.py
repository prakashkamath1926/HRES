import json
from datetime import datetime
from backend.app.repositories.database import get_db_connection, execute_query


def add_audit_event(incident_id: str, event_type: str, message: str, payload: dict | None = None):
    conn, dialect = get_db_connection()
    cursor = conn.cursor()
    now = datetime.utcnow()
    payload_json = json.dumps(payload) if payload else None

    execute_query(cursor,
        """
        INSERT INTO audit_events (incident_id, timestamp, event_type, message, payload)
        VALUES (?, ?, ?, ?, ?)
        """,
        (incident_id, now, event_type, message, payload_json),
        dialect=dialect
    )
    conn.commit()
    conn.close()


def get_audit_log_for_incident(incident_id: str) -> list[dict]:
    conn, dialect = get_db_connection()
    cursor = conn.cursor()
    execute_query(cursor,
        """
        SELECT timestamp, event_type, message, payload
        FROM audit_events
        WHERE incident_id = ?
        ORDER BY timestamp ASC
        """,
        (incident_id,),
        dialect=dialect
    )
    rows = cursor.fetchall()
    conn.close()

    logs = []
    for r in rows:
        ts = r["timestamp"]
        # Format timestamp to ISO format string if it is datetime object
        ts_str = ts.isoformat() if isinstance(ts, datetime) else str(ts)
        logs.append({
            "timestamp": ts_str,
            "event_type": r["event_type"],
            "message": r["message"],
            "payload": json.loads(r["payload"]) if r["payload"] else None
        })
    return logs
