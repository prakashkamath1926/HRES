import json
from datetime import datetime
from backend.app.core.schemas import (
    IncidentState, IncidentStatus, RiskAssessment, ActionProposal, LocationContext,
    Observation, NormalizedEvent, DataMode, EventType, ApprovalStatus
)
from backend.app.repositories.database import get_db_connection, execute_query
from backend.app.repositories.observations import get_observations_for_incident, get_normalized_events_for_incident
from backend.app.repositories.audit_log import get_audit_log_for_incident


def create_incident(incident_id: str, status: IncidentStatus) -> IncidentState:
    conn, dialect = get_db_connection()
    cursor = conn.cursor()
    now = datetime.utcnow()
    execute_query(cursor,
        """
        INSERT INTO incidents (incident_id, status, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        (incident_id, status.value, now, now),
        dialect=dialect
    )
    conn.commit()
    conn.close()

    return IncidentState(
        incident_id=incident_id,
        status=status,
        observations=[],
        events=[],
        risk=None,
        action_proposal=None,
        routes=[],
        audit_log=[]
    )


def update_incident_status(incident_id: str, status: IncidentStatus):
    conn, dialect = get_db_connection()
    cursor = conn.cursor()
    now = datetime.utcnow()
    execute_query(cursor,
        """
        UPDATE incidents
        SET status = ?, updated_at = ?
        WHERE incident_id = ?
        """,
        (status.value, now, incident_id),
        dialect=dialect
    )
    conn.commit()
    conn.close()


def update_incident_state_data(
    incident_id: str,
    status: IncidentStatus,
    risk: RiskAssessment | None,
    action_proposal: ActionProposal | None,
    routes: list[dict]
):
    conn, dialect = get_db_connection()
    cursor = conn.cursor()
    now = datetime.utcnow()
    risk_json = risk.model_dump_json() if risk else None
    action_proposal_json = action_proposal.model_dump_json() if action_proposal else None
    routes_json = json.dumps(routes)

    execute_query(cursor,
        """
        UPDATE incidents
        SET status = ?, risk = ?, action_proposal = ?, routes = ?, updated_at = ?
        WHERE incident_id = ?
        """,
        (status.value, risk_json, action_proposal_json, routes_json, now, incident_id),
        dialect=dialect
    )
    conn.commit()
    conn.close()


def get_incident_state(incident_id: str) -> IncidentState | None:
    conn, dialect = get_db_connection()
    cursor = conn.cursor()
    execute_query(cursor,
        """
        SELECT incident_id, status, risk, action_proposal, routes, created_at, updated_at
        FROM incidents
        WHERE incident_id = ?
        """,
        (incident_id,),
        dialect=dialect
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    # Load child entities
    observations = get_observations_for_incident(incident_id)
    events = get_normalized_events_for_incident(incident_id)
    audit_log = get_audit_log_for_incident(incident_id)

    # Deserialize JSON fields with try-except to avoid Pydantic ValidationError on legacy/corrupted DB records
    risk = None
    if row["risk"]:
        try:
            risk_data = json.loads(row["risk"])
            risk = RiskAssessment(**risk_data)
        except Exception:
            risk = None

    action_proposal = None
    if row["action_proposal"]:
        try:
            action_data = json.loads(row["action_proposal"])
            action_proposal = ActionProposal(**action_data)
        except Exception:
            action_proposal = None

    routes = []
    if row["routes"]:
        try:
            routes = json.loads(row["routes"])
        except Exception:
            routes = []

    return IncidentState(
        incident_id=row["incident_id"],
        status=IncidentStatus(row["status"]),
        observations=observations,
        events=events,
        risk=risk,
        action_proposal=action_proposal,
        routes=routes,
        audit_log=audit_log
    )


def get_current_incident() -> IncidentState | None:
    conn, dialect = get_db_connection()
    cursor = conn.cursor()
    # Get latest active incident (i.e. not resolved, ordered by created_at desc)
    execute_query(cursor,
        """
        SELECT incident_id
        FROM incidents
        WHERE status != ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (IncidentStatus.RESOLVED.value,),
        dialect=dialect
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return get_incident_state(row["incident_id"])
    return None
