from fastapi import APIRouter, HTTPException
from backend.app.core.schemas import IncidentState, IncidentStatus
from backend.app.repositories.incidents import get_current_incident, get_incident_state, update_incident_status
from backend.app.repositories.audit_log import add_audit_event
from backend.app.services.monitoring import get_or_create_active_incident

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("/current", response_model=IncidentState)
def get_current_active_incident():
    incident = get_current_incident()
    if not incident:
        # Auto-create active incident context on check
        incident = get_or_create_active_incident()
    return incident


@router.get("/{incident_id}", response_model=IncidentState)
def get_incident_by_id(incident_id: str):
    incident = get_incident_state(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/{incident_id}/resolve", response_model=IncidentState)
def resolve_incident(incident_id: str):
    incident = get_incident_state(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    update_incident_status(incident_id, IncidentStatus.RESOLVED)
    add_audit_event(
        incident_id,
        "INCIDENT_RESOLVED",
        "Incident marked as RESOLVED and archived."
    )

    # Generate full LLM After-Action Report
    from backend.app.repositories.reports import save_after_action_report
    from backend.app.integrations.llm import LLMService
    from datetime import datetime

    obs_count = len(incident.observations or [])
    event_count = len(incident.events or [])
    audit_count = len(incident.audit_log or [])
    risk_sev = incident.risk.severity if incident.risk else "UNKNOWN"
    risk_score = incident.risk.score if incident.risk else 0
    actions_taken = [a.get("type", "unknown") for a in (incident.action_proposal.actions or [])] if incident.action_proposal else []
    false_alarm_count = sum(1 for e in (incident.events or []) if getattr(e, "false_alarm_report", None))

    aar_prompt = (
        f"Generate a formal After-Action Report (AAR) for an emergency incident.\n\n"
        f"Incident ID: {incident_id}\n"
        f"Resolved At: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"Peak Risk: {risk_sev} ({risk_score:.0f}/100)\n"
        f"Observations Collected: {obs_count}\n"
        f"Events Normalized: {event_count}\n"
        f"Audit Log Entries: {audit_count}\n"
        f"Actions Executed: {', '.join(actions_taken) if actions_taken else 'None'}\n"
        f"False Alarms Detected: {false_alarm_count}\n"
        f"Agent Reasoning: {'; '.join((incident.action_proposal.reasoning or [])[:4]) if incident.action_proposal else 'N/A'}\n\n"
        f"Write a structured AAR with sections: Executive Summary, Timeline, Risk Analysis, "
        f"Response Actions, Lessons Learned, Recommendations. "
        f"Be factual, professional, highly detailed, and comprehensive (800-1200 words)."
    )

    try:
        report_content = LLMService.generate(aar_prompt)
        report_content = f"HRES AFTER-ACTION REPORT\n{'='*50}\n{report_content}"
    except Exception:
        report_content = (
            f"HRES AFTER-ACTION REPORT\n{'='*50}\n"
            f"Incident ID: {incident_id}\n"
            f"Resolved: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"Peak Risk: {risk_sev} ({risk_score:.0f}/100)\n"
            f"Observations: {obs_count} | Events: {event_count} | Audit Entries: {audit_count}\n"
            f"Actions: {', '.join(actions_taken) or 'None'}\n"
            f"False Alarms: {false_alarm_count}\n\n"
            f"This incident has been resolved and archived. All sensor data, agent decisions, "
            f"and operator actions have been logged in the audit trail."
        )

    save_after_action_report(incident_id, report_content)
    return get_incident_state(incident_id)
