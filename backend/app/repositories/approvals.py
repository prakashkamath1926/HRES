from datetime import datetime
from backend.app.repositories.database import get_db_connection, execute_query


def add_approval(incident_id: str, decision: str, comment: str | None, operator_id: str | None, proposal_version: int):
    conn, dialect = get_db_connection()
    cursor = conn.cursor()
    now = datetime.utcnow()

    execute_query(cursor,
        """
        INSERT OR REPLACE INTO approvals (incident_id, decision, comment, operator_id, proposal_version, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (incident_id, decision, comment, operator_id, proposal_version, now),
        dialect=dialect
    )
    conn.commit()
    conn.close()


def get_approval(incident_id: str) -> dict | None:
    conn, dialect = get_db_connection()
    cursor = conn.cursor()
    execute_query(cursor,
        """
        SELECT incident_id, decision, comment, operator_id, proposal_version, timestamp
        FROM approvals
        WHERE incident_id = ?
        """,
        (incident_id,),
        dialect=dialect
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    ts = row["timestamp"]
    ts_str = ts.isoformat() if isinstance(ts, datetime) else str(ts)

    return {
        "incident_id": row["incident_id"],
        "decision": row["decision"],
        "comment": row["comment"],
        "operator_id": row["operator_id"],
        "proposal_version": row["proposal_version"],
        "timestamp": ts_str
    }
