from datetime import datetime
from backend.app.repositories.database import get_db_connection, execute_query


def save_after_action_report(incident_id: str, content: str):
    conn, dialect = get_db_connection()
    cursor = conn.cursor()
    now = datetime.utcnow()

    if dialect == "postgres":
        cursor.execute(
            """
            INSERT INTO after_action_reports (incident_id, content, generated_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (incident_id) DO UPDATE
            SET content = EXCLUDED.content, generated_at = EXCLUDED.generated_at
            """,
            (incident_id, content, now)
        )
    else:
        execute_query(cursor,
            """
            INSERT OR REPLACE INTO after_action_reports (incident_id, content, generated_at)
            VALUES (?, ?, ?)
            """,
            (incident_id, content, now),
            dialect=dialect
        )
    conn.commit()
    conn.close()


def get_after_action_report(incident_id: str) -> dict | None:
    conn, dialect = get_db_connection()
    cursor = conn.cursor()
    execute_query(cursor,
        """
        SELECT incident_id, content, generated_at
        FROM after_action_reports
        WHERE incident_id = ?
        """,
        (incident_id,),
        dialect=dialect
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    gen_at = row["generated_at"]
    gen_at_str = gen_at.isoformat() if isinstance(gen_at, datetime) else str(gen_at)

    return {
        "incident_id": row["incident_id"],
        "content": row["content"],
        "generated_at": gen_at_str
    }
