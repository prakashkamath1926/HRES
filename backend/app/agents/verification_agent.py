"""
Verification Agent — HRES LangGraph Pipeline Node
TOOL-USING AGENT: Calls DuckDuckGo web search for fire/smoke/roadblock events.

Pipeline:
  1. Run deterministic multi-source sensor verification
  2. Web Search Tool (DuckDuckGo) for each non-heat event
  3. Apply web confidence boost / false alarm detection
  4. Generate law enforcement report if confirmed false alarm
  5. LLM evidence synthesis including web results
"""
import logging
from datetime import datetime, timezone

from pydantic import BaseModel, Field
from backend.app.core.state import HRESGraphState
from backend.app.core.schemas import NormalizedEvent, EventType
from backend.app.services.verification import verify_observations
from backend.app.services.web_verify import web_verify_event, generate_false_alarm_report
from backend.app.integrations.llm import LLMService
from backend.app.repositories.audit_log import add_audit_event

logger = logging.getLogger("hres.verification_agent")

# Which event types get web-searched
WEB_VERIFY_TYPES = {EventType.POSSIBLE_FIRE, EventType.SMOKE_REPORT, EventType.ROAD_BLOCK}


class VerificationSynthesis(BaseModel):
    evidence_summary: str = Field(
        description="2-sentence factual summary of verified events, confidence levels, and web corroboration status"
    )
    risk_escalation_flag: bool = Field(
        description="True if web search corroborated the event with high confidence"
    )


def get_verification_fallback() -> VerificationSynthesis:
    return VerificationSynthesis(
        evidence_summary="Sensor verification complete. Observations corroborated across FortyGuard and weather sensors.",
        risk_escalation_flag=False
    )


def verification_agent_node(state: HRESGraphState) -> dict:
    incident_id = state["incident_id"]
    observations = state["observations"]

    # ── Step 1: Deterministic sensor verification (all event types) ────
    events: list[NormalizedEvent] = verify_observations(incident_id, observations)

    add_audit_event(
        incident_id,
        "VERIFICATION_SENSOR",
        f"Sensor verification: {len(events)} event(s) from {len(observations)} observation(s) — types: {[e.event_type.value for e in events]}",
        {"event_count": len(events), "obs_count": len(observations)}
    )

    # ── Step 2: Web Search Tool for fire/smoke/roadblock events ────────
    enriched_events: list[NormalizedEvent] = []

    for event in events:
        # Heat events don't need web search — sensor data is authoritative
        if event.event_type not in WEB_VERIFY_TYPES:
            enriched_events.append(event)
            continue

        lat = event.location.latitude
        lon = event.location.longitude
        address = event.location.address

        # Log the tool call so it's visible in agent pipeline
        add_audit_event(
            incident_id,
            "TOOL_CALL_WEB_SEARCH",
            f"🔍 Tool: DuckDuckGo search for '{event.event_type.value}' near {address or f'({lat:.3f}, {lon:.3f})'}",
            {"event_id": event.event_id, "event_type": event.event_type.value, "location": address}
        )

        # Execute web search
        web_result = web_verify_event(
            event_type=event.event_type.value,
            location_address=address,
            lat=lat,
            lon=lon
        )

        # Log the tool result
        add_audit_event(
            incident_id,
            "TOOL_RESULT_WEB_SEARCH",
            f"🌐 Web Result: {web_result['summary']} | Corroborated: {web_result['corroborated']} | Sources: {len(web_result.get('sources', []))}",
            {
                "event_id": event.event_id,
                "corroborated": web_result["corroborated"],
                "confidence_boost": web_result["confidence_boost"],
                "false_alarm_risk": web_result["false_alarm_risk"],
                "sources": web_result.get("sources", []),
                "query": web_result.get("query", "")
            }
        )

        # Apply confidence boost from web corroboration
        new_confidence = min(1.0, event.confidence + web_result["confidence_boost"])
        updated_status = event.status
        if web_result["corroborated"] and new_confidence > 0.7 and event.status in ("possible", "unverified"):
            updated_status = "likely"

        # Generate false alarm report if event is unverified AND web says no evidence
        false_alarm_report = None
        if (
            web_result["false_alarm_risk"]
            and new_confidence < 0.35
            and event.status in ("unverified", "possible")
        ):
            false_alarm_report = generate_false_alarm_report(
                event_type=event.event_type.value,
                location=address or f"({lat:.4f}, {lon:.4f})",
                lat=lat,
                lon=lon,
                reported_at=datetime.now(timezone.utc).isoformat(),
                web_result=web_result,
            )
            add_audit_event(
                incident_id,
                "FALSE_ALARM_FILED",
                f"⚖️ False Alarm Report: {event.event_type.value} — confidence {new_confidence:.0%}, no web corroboration. Flagged for law enforcement.",
                {"event_id": event.event_id, "confidence": new_confidence}
            )

        enriched_events.append(NormalizedEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            location=event.location,
            status=updated_status,
            confidence=new_confidence,
            value=event.value,
            supporting_observations=event.supporting_observations,
            web_verification=web_result,
            false_alarm_report=false_alarm_report
        ))

    # ── Step 3: LLM evidence synthesis ────────────────────────────────
    sources_set = {o.source for o in observations}
    event_summaries = [
        {
            "type": e.event_type.value,
            "status": e.status,
            "confidence": round(e.confidence, 2),
            "web": e.web_verification.get("corroborated") if e.web_verification else "N/A"
        }
        for e in enriched_events
    ]

    prompt = (
        f"You are HRES Verification Agent. Summarize evidence for the emergency operator.\n"
        f"Sources: {', '.join(sources_set) or 'None'}\n"
        f"Events: {event_summaries}\n"
        f"Write exactly 2 factual sentences. If web-corroborated, name the source. "
        f"If false alarm suspected, state it clearly."
    )
    synthesis = LLMService.generate_structured(
        prompt=prompt,
        schema_class=VerificationSynthesis,
        fallback_factory=get_verification_fallback
    )

    add_audit_event(
        incident_id,
        "VERIFICATION_SYNTHESIS",
        f"🧠 Agent Synthesis: {synthesis.evidence_summary}",
        {"risk_escalation": synthesis.risk_escalation_flag}
    )

    return {"events": enriched_events, "next_step": "risk"}
