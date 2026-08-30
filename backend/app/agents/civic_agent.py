"""
Civic Agent — Final pipeline node before approval gate.
Reads false_alarm_report from verification agent events,
escalates to law enforcement action, and generates official civic summaries.
"""
import logging
from pydantic import BaseModel, Field
from backend.app.core.state import HRESGraphState
from backend.app.core.schemas import ActionProposal
from backend.app.integrations.llm import LLMService
from backend.app.repositories.audit_log import add_audit_event
from backend.app.services.email_service import send_incident_report_email

logger = logging.getLogger("hres.civic_agent")


class CivicGuidance(BaseModel):
    incident_summary: str = Field(description="Structured summary for official records")
    stakeholder_notifications: list[dict] = Field(
        description="List with 'recipient' and 'message' fields for each stakeholder"
    )


def get_civic_fallback() -> CivicGuidance:
    return CivicGuidance(
        incident_summary="HRES Incident active. Verification protocols triggered. High heat risk detected.",
        stakeholder_notifications=[
            {"recipient": "Campus Administration", "message": "HRES Heat Resilience alert active. Monitoring in progress."},
            {"recipient": "Local Health Authority / NGO", "message": "Alert: Extreme environmental conditions monitored. Cooling guidelines prepared."}
        ]
    )


def civic_agent_node(state: HRESGraphState) -> dict:
    incident_id = state["incident_id"]
    risk = state["risk"]
    severity = risk.severity if risk else "UNKNOWN"
    score = risk.score if risk else 0.0
    events = state.get("events", [])

    proposal = state["action_proposal"]
    actions = list(proposal.actions) if proposal else []
    reasoning = list(proposal.reasoning) if proposal else []

    # ── Escalate false alarm reports from verification agent ──────────
    false_alarm_events = [e for e in events if getattr(e, "false_alarm_report", None)]

    for evt in false_alarm_events:
        report = evt.false_alarm_report
        logger.warning(f"Civic Agent: escalating false alarm for {evt.event_id}")
        actions.append({
            "type": "law_enforcement_report",
            "title": "⚖️ False Alarm Report Filed",
            "details": report
        })
        reasoning.append(
            f"Civic Agent: ⚖️ False alarm filed for {evt.event_type.value} "
            f"(confidence {evt.confidence:.0%}) — referred for law enforcement review."
        )
        add_audit_event(
            incident_id,
            "LAW_ENFORCEMENT_ESCALATION",
            f"⚖️ False alarm escalated for {evt.event_type.value} to law enforcement log.",
            {"event_id": evt.event_id, "confidence": evt.confidence}
        )

    # ── LLM civic guidance ────────────────────────────────────────────
    fa_note = (
        f"\nNOTE: {len(false_alarm_events)} false alarm(s) detected. "
        f"Include misinformation risk in summary and refer to law enforcement log."
        if false_alarm_events else ""
    )

    prompt = (
        f"Generate official civic summaries and stakeholder notifications.\n"
        f"Incident ID: {incident_id}\n"
        f"Risk: {severity} ({score:.0f}/100)\n"
        f"Events: {[e.event_type.value for e in events]}\n"
        f"False Alarms: {len(false_alarm_events)}{fa_note}\n"
        f"Draft professional updates for campus administration and health NGOs."
    )
    guidance = LLMService.generate_structured(
        prompt=prompt,
        schema_class=CivicGuidance,
        fallback_factory=get_civic_fallback
    )

    actions.append({
        "type": "civic_report",
        "title": "Official Civic Dispatch",
        "details": {
            "summary": guidance.incident_summary,
            "notifications": guidance.stakeholder_notifications,
            "false_alarm_count": len(false_alarm_events),
        }
    })
    reasoning.append(
        f"Civic Agent: Civic notifications generated. "
        f"{f'{len(false_alarm_events)} false alarm(s) escalated.' if false_alarm_events else 'No false alarms.'}"
    )

    # ── Dispatch emails to stakeholders ────────────────────────────────
    # We will send a single consolidated email to the mock recipients for demonstration.
    recipients = ["police@example.com", "hospital@example.com", "fire@example.com"]
    email_body = f"Summary: {guidance.incident_summary}\n\nNotifications:\n"
    for notif in guidance.stakeholder_notifications:
        email_body += f"- To {notif['recipient']}: {notif['message']}\n"
    
    if false_alarm_events:
        email_body += f"\nLaw Enforcement Notice: {len(false_alarm_events)} false alarms reported and logged."
        
    send_incident_report_email(incident_id, severity, email_body, recipients)
    
    add_audit_event(
        incident_id,
        "EMAIL_DISPATCHED",
        f"📧 Automated incident report emailed to stakeholders.",
        {"recipients": recipients}
    )

    return {
        "action_proposal": ActionProposal(
            actions=actions,
            status="Guidance generated",
            reasoning=reasoning,
            approval_status=proposal.approval_status if proposal else "pending"
        )
    }
