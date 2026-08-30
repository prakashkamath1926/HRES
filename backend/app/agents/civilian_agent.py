from pydantic import BaseModel, Field
from backend.app.core.state import HRESGraphState
from backend.app.core.schemas import ActionProposal
from backend.app.integrations.llm import LLMService
from backend.app.services.routing_service import get_nearest_facilities
from backend.app.services.web_verify import generate_false_alarm_report
from backend.app.repositories.audit_log import add_audit_event
import logging
from datetime import datetime

logger = logging.getLogger("hres.civilian_agent")


class CivilianGuidance(BaseModel):
    alert_title: str = Field(description="Actionable alarm headline for civilians")
    alert_message: str = Field(description="Short calm description of the event and risk zone location")
    cooling_center_recommendation: str = Field(description="Cooling center name and directions")
    hospital_recommendation: str = Field(description="Hospital name, distance, and route recommendation")
    safety_tips: list[str] = Field(description="List of 4-6 conservative, safety-critical tips for heat safety")
    voice_announcement: str = Field(description="Short calming voice announcement text (2-3 sentences max) to read aloud")


def get_civilian_fallback() -> CivilianGuidance:
    return CivilianGuidance(
        alert_title="HEAT RISK ALARM ACTIVE",
        alert_message="Elevated temperatures have been detected in your area. Please stay calm and follow these safety guidelines.",
        cooling_center_recommendation="Move to the nearest air-conditioned building — a library, mall, or community center.",
        hospital_recommendation="For heat illness symptoms, locate your nearest hospital immediately.",
        safety_tips=[
            "Do not panic. Move to shade or an air-conditioned space immediately.",
            "Drink cool water — small sips frequently. Avoid ice-cold drinks.",
            "Loosen tight clothing and apply cool wet cloth to neck and wrists.",
            "If someone collapses: lay them flat, fan them, call for medical help.",
            "Do not leave children or pets in vehicles.",
            "Alert staff or neighbours if you feel dizzy, confused or stop sweating."
        ],
        voice_announcement=(
            "Attention. HRES has detected extreme heat in your area. Please stay calm. "
            "Move to a cool shaded area and drink water. Help is being coordinated."
        )
    )


def civilian_agent_node(state: HRESGraphState) -> dict:
    incident_id = state["incident_id"]
    risk = state["risk"]
    severity = risk.severity if risk else "UNKNOWN"
    score = risk.score if risk else 0.0

    # Get location
    observations = state.get("observations", [])
    lat, lon, address = 26.9124, 75.7873, "Current location"
    if observations:
        last_obs = observations[-1]
        lat = last_obs.location.latitude
        lon = last_obs.location.longitude
        address = last_obs.location.address or address

    # Live facility lookup for cooling centers + hospital
    facilities = {}
    try:
        facilities = get_nearest_facilities(lat, lon)
    except Exception as e:
        logger.warning(f"Civilian facility lookup failed: {e}")

    # Build real facility strings
    cooling_info = "Nearest air-conditioned public building (library, mall, or community center)"
    hospital_info = "Nearest hospital — call emergency services if needed"

    if facilities.get("cooling_center"):
        cc = facilities["cooling_center"]
        dist = f"{cc['route']['distance_km']} km" if cc.get("route") else "nearby"
        cooling_info = f"{cc['name']} ({dist} away)"

    if facilities.get("hospital"):
        h = facilities["hospital"]
        dist_text = ""
        if h.get("route"):
            dist_text = f" — {h['route']['distance_km']} km, approx {h['route']['duration_min']} min"
        hospital_info = f"{h['name']}{dist_text}"

    # Check for false alarm events
    false_alarm_events = [
        e for e in state.get("events", [])
        if e.status == "unverified" and e.confidence < 0.25
    ]

    # LLM guidance generation
    prompt = (
        f"Generate public safety guidance for a heat emergency.\n"
        f"Incident Context:\n"
        f"- Risk Level: {severity} (Score: {score:.0f}/100)\n"
        f"- Location: {address}\n"
        f"- Nearest Cooling Center: {cooling_info}\n"
        f"- Nearest Hospital: {hospital_info}\n"
        f"Create clear, CALM and reassuring guidance. Start the voice_announcement with 'Attention.' and tell people not to panic."
    )

    guidance = LLMService.generate_structured(
        prompt=prompt,
        schema_class=CivilianGuidance,
        fallback_factory=get_civilian_fallback
    )

    proposal = state["action_proposal"]
    actions = list(proposal.actions) if proposal else []
    reasoning = list(proposal.reasoning) if proposal else []

    # Build civilian alert action with real facility data
    civilian_action = {
        "type": "civilian_alert",
        "title": guidance.alert_title,
        "message": guidance.alert_message,
        "voice_announcement": guidance.voice_announcement,
        "details": {
            "cooling_center": cooling_info,
            "hospital": hospital_info,
            "safety_tips": guidance.safety_tips,
        }
    }

    # Embed cooling center + hospital map data
    if facilities.get("cooling_center"):
        cc = facilities["cooling_center"]
        civilian_action["details"]["cooling_center_coords"] = {"lat": cc["lat"], "lon": cc["lon"]}
        if cc.get("route"):
            civilian_action["details"]["cooling_center_route"] = cc["route"]["geometry"]

    if facilities.get("hospital"):
        h = facilities["hospital"]
        civilian_action["details"]["hospital_coords"] = {"lat": h["lat"], "lon": h["lon"]}
        if h.get("route"):
            civilian_action["details"]["hospital_route"] = h["route"]["geometry"]

    actions.append(civilian_action)

    # Handle false alarm events — file law enforcement report
    for evt in false_alarm_events:
        logger.info(f"False alarm detected for event {evt.event_id} — filing law enforcement report")
        false_report = generate_false_alarm_report(
            event_type=evt.event_type,
            location=address,
            lat=lat,
            lon=lon,
            reported_at=datetime.utcnow().isoformat(),
            web_result={"corroborated": False, "summary": "Event not corroborated by web sources"}
        )
        actions.append({
            "type": "law_enforcement_report",
            "title": "⚖️ False Alarm Report Filed",
            "details": false_report
        })
        add_audit_event(
            incident_id,
            "FALSE_ALARM_FILED",
            f"False alarm law enforcement report filed for {evt.event_type} at {address}. Low confidence ({evt.confidence:.0%}) event flagged.",
            {"event_id": evt.event_id, "confidence": evt.confidence, "location": address}
        )
        reasoning.append(
            f"Civilian Agent: ⚖️ False alarm report filed for {evt.event_type} (confidence: {evt.confidence:.0%}). Logged for law enforcement review."
        )

    reasoning.append(
        f"Civilian Agent: Synthesized civilian guidance. Cooling: {cooling_info}. Hospital: {hospital_info}."
    )

    new_proposal = ActionProposal(
        actions=actions,
        status="Guidance generated",
        reasoning=reasoning,
        approval_status=proposal.approval_status if proposal else "pending"
    )

    return {"action_proposal": new_proposal}
