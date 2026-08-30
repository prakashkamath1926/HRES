import uuid
from datetime import datetime
from backend.app.core.schemas import (
    IncidentState, IncidentStatus, Observation, NormalizedEvent, RiskAssessment, ApprovalStatus
)
from backend.app.repositories.incidents import (
    create_incident, get_current_incident, update_incident_state_data, update_incident_status
)
from backend.app.repositories.observations import (
    add_observation, get_observations_for_incident, add_normalized_event, clear_normalized_events, get_normalized_events_for_incident
)
from backend.app.repositories.audit_log import add_audit_event
from backend.app.services.verification import verify_observations
from backend.app.services.prioritization import calculate_risk_assessment


def get_or_create_active_incident() -> IncidentState:
    current = get_current_incident()
    if current:
        return current

    # Create a new incident if none active
    incident_id = f"inc-{uuid.uuid4().hex[:12]}"
    incident = create_incident(incident_id, IncidentStatus.RECEIVED)
    
    add_audit_event(
        incident_id,
        "INCIDENT_CREATED",
        f"New heat monitoring context initialized: {incident_id}"
    )
    return incident


def reset_active_incident() -> IncidentState:
    # Mark ALL current active/unresolved incidents as resolved
    from backend.app.repositories.database import get_db_connection, execute_query
    conn, dialect = get_db_connection()
    cursor = conn.cursor()
    
    execute_query(cursor,
        "SELECT incident_id FROM incidents WHERE status != ?",
        (IncidentStatus.RESOLVED.value,),
        dialect=dialect
    )
    active_rows = cursor.fetchall()
    
    for row in active_rows:
        inc_id = row["incident_id"]
        add_audit_event(
            inc_id,
            "INCIDENT_RESOLVED",
            "Incident manually resolved and archived during scenario reset."
        )
        
    execute_query(cursor,
        "UPDATE incidents SET status = ? WHERE status != ?",
        (IncidentStatus.RESOLVED.value, IncidentStatus.RESOLVED.value),
        dialect=dialect
    )
    conn.commit()
    conn.close()

    # Create new fresh active incident
    return get_or_create_active_incident()


def process_incident_updates(incident_id: str) -> IncidentState:
    from backend.app.repositories.incidents import get_incident_state
    incident = get_incident_state(incident_id)
    if not incident:
        raise ValueError(f"Incident {incident_id} not found")

    # 1. Fetch observations and run deterministic verification
    observations = get_observations_for_incident(incident_id)
    normalized_events = verify_observations(incident_id, observations)
    
    # Save normalized events to SQLite
    clear_normalized_events(incident_id)
    for event in normalized_events:
        add_normalized_event(incident_id, event)

    # Re-fetch events to ensure consistency
    normalized_events = get_normalized_events_for_incident(incident_id)

    # 2. Construct state for LangGraph invocation
    initial_state = {
        "incident_id": incident.incident_id,
        "status": incident.status,
        "observations": observations,
        "events": normalized_events,
        "risk": incident.risk,
        "action_proposal": incident.action_proposal,
        "routes": incident.routes,
        "audit_log": [],
        "next_step": ""
    }

    from backend.app.workflows.supervisor import app_graph
    config = {"configurable": {"thread_id": incident_id}}

    try:
        # Invoke compiled StateGraph
        app_graph.invoke(initial_state, config)
    except Exception as e:
        add_audit_event(
            incident_id,
            "GRAPH_ERROR",
            f"LangGraph execution encountered an error: {str(e)}"
        )

    # 3. Fetch updated state values from checkpointer
    graph_state = app_graph.get_state(config)
    values = graph_state.values

    # Determine status & risk update
    new_status = values.get("status", incident.status)
    risk = values.get("risk", incident.risk)
    action_proposal = values.get("action_proposal", incident.action_proposal)
    routes = values.get("routes", incident.routes)

    # If the graph has paused at the approval gate, transition status to AWAITING_APPROVAL
    if "approval_gate" in graph_state.next:
        new_status = IncidentStatus.AWAITING_APPROVAL
        if action_proposal and action_proposal.approval_status != ApprovalStatus.APPROVED:
            action_proposal.approval_status = ApprovalStatus.PENDING

    # 4. Persistence to SQLite DB
    update_incident_state_data(incident_id, new_status, risk, action_proposal, routes)

    return get_incident_state(incident_id)


def resume_approval(incident_id: str, payload: dict) -> IncidentState:
    from backend.app.workflows.supervisor import app_graph
    from backend.app.repositories.incidents import get_incident_state

    config = {"configurable": {"thread_id": incident_id}}
    
    # Retrieve current cached incident state to merge decision details
    incident = get_incident_state(incident_id)
    proposal = incident.action_proposal
    if not proposal:
        raise ValueError("No active action proposal to approve")

    decision_map = {
        "approved": ApprovalStatus.APPROVED,
        "modified": ApprovalStatus.MODIFIED,
        "rejected": ApprovalStatus.REJECTED,
        "escalated": ApprovalStatus.ESCALATED
    }
    status_enum = decision_map.get(payload["decision"].lower(), ApprovalStatus.APPROVED)

    proposal.approval_status = status_enum
    proposal.approved_by = payload.get("operator_id")
    proposal.approved_at = datetime.utcnow()

    # Update checkpointer state by writing the approved proposal details
    app_graph.update_state(config, {"action_proposal": proposal}, as_node="approval_gate")

    # Resume the paused gate node in LangGraph (runs approval_gate and completes)
    app_graph.invoke(None, config)

    # Retrieve post-resumption values
    graph_state = app_graph.get_state(config)
    values = graph_state.values

    new_status = values.get("status", IncidentStatus.ACTIVE)
    risk = values.get("risk", incident.risk)
    routes = values.get("routes", incident.routes)

    # Enforce active status if approved
    if status_enum == ApprovalStatus.APPROVED:
        new_status = IncidentStatus.ACTIVE

    # Update SQLite database
    update_incident_state_data(incident_id, new_status, risk, proposal, routes)

    add_audit_event(
        incident_id,
        "OPERATOR_DECISION",
        f"Operator decision: {status_enum.value}",
        payload
    )

    return get_incident_state(incident_id)
