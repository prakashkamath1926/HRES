"""
HRES Agent Chatbot API — Streaming chat endpoint using Xkiro LLM.
The HRES Agent is context-aware: it reads the current incident state
and provides intelligent, tool-aware responses to user queries.
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import logging

from backend.app.integrations.llm import LLMService
from backend.app.services.monitoring import get_or_create_active_incident
from backend.app.repositories.incidents import get_incident_state

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger("hres.chat")


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    include_incident_context: bool = True


_facility_cache = {}

def _get_facility_context(lat: float, lon: float) -> dict:
    """Query Overpass/OSRM for nearest facilities with simple caching to prevent chat lag."""
    key = f"{lat:.3f}_{lon:.3f}"
    if key in _facility_cache:
        return _facility_cache[key]
    try:
        from backend.app.services.routing_service import get_nearest_facilities
        res = get_nearest_facilities(lat, lon)
        _facility_cache[key] = res
        return res
    except Exception as e:
        logger.warning(f"Facility lookup for chat failed: {e}")
        return {}

def _build_system_prompt(incident=None) -> str:
    base = """You are HRES Agent — the AI assistant for the Heat Response Emergency System.

Your role:
- Help users understand the current heat/fire situation in plain, calm language
- Give EXACT facility names, distances and GPS coordinates when you have them — do not say "I don't know" if the context has that data
- Give clear safety instructions
- Explain what the HRES pipeline found (observations, verification, risk score)
- Answer questions about routes, hospitals, fire stations, and cooling centers WITH REAL DATA from context
- Explain what actions HRES has proposed and why
- Help operators understand the approval gate decisions

Personality: Calm, authoritative, concise. Like an experienced emergency coordinator.
Always give specific answers when facility data is in context. Never say "I don't know" if the data is provided below.

Heat safety rules you always know:
- Move to shade or air-conditioned space immediately
- Drink cool water (not ice cold) — small sips frequently
- Loosen tight clothing
- Apply cool wet cloth to neck, wrists, armpits
- If someone collapses: lay them down, fan them, call for help
- Signs of heat stroke: no sweating despite heat, confusion — this is an emergency"""

    if not incident:
        return base

    status = incident.status or "unknown"
    risk = incident.risk
    events = incident.events or []
    obs = incident.observations or []
    proposal = incident.action_proposal
    audit_count = len(incident.audit_log or [])

    # Base location
    lat, lon = 26.9124, 75.7873
    address = "HeatShield Campus Zone, Jaipur"
    if obs:
        last_obs = obs[-1]
        lat = last_obs.location.latitude
        lon = last_obs.location.longitude
        address = last_obs.location.address or address

    context_lines = [
        "\n\n=== CURRENT INCIDENT CONTEXT ===",
        f"Incident ID: {incident.incident_id}",
        f"Status: {status.upper()}",
        f"Current Location: {address}",
        f"GPS Coordinates: lat={lat:.5f}, lon={lon:.5f}",
    ]

    if risk:
        context_lines.append(f"Risk Level: {risk.severity} (Score: {risk.score:.0f}/100)")
        if risk.reasoning:
            context_lines.append(f"Risk Reasoning: {'; '.join(risk.reasoning[:3])}")

    if obs:
        last_obs = obs[-1]
        temp = last_obs.value.get("temperature")
        context_lines.append(f"Latest Reading: {last_obs.source} — {f'{temp:.1f}°C' if temp else 'N/A'} ({last_obs.data_mode})")

    if events:
        event_summary = ", ".join([f"{e.event_type} ({e.status}, {e.confidence*100:.0f}% confidence)" for e in events])
        context_lines.append(f"Events Detected: {event_summary}")

    # ── Extract facility data from action proposal ──────────────────────────────
    facility_found = False
    if proposal and proposal.actions:
        responder = next((a for a in proposal.actions if a.get("type") == "responder_guidance"), None)
        if responder:
            details = responder.get("details", {})
            if details.get("hospital"):
                h = details["hospital"]
                dist = f"{h.get('distance_km', '?')} km" if h.get("distance_km") else "nearby"
                mins = f", {h.get('duration_min', '?')} min drive" if h.get("duration_min") else ""
                context_lines.append(f"NEAREST HOSPITAL: {h.get('name', 'Unknown')} — {dist} away{mins} — lat={h.get('lat', '?')}, lon={h.get('lon', '?')}")
                facility_found = True
            if details.get("fire_station"):
                fs = details["fire_station"]
                dist = f"{fs.get('distance_km', '?')} km" if fs.get("distance_km") else "nearby"
                mins = f", {fs.get('duration_min', '?')} min drive" if fs.get("duration_min") else ""
                context_lines.append(f"NEAREST FIRE STATION: {fs.get('name', 'Unknown')} — {dist} away{mins} — lat={fs.get('lat', '?')}, lon={fs.get('lon', '?')}")
                facility_found = True
            if details.get("primary_route"):
                context_lines.append(f"Primary Responder Route: {details['primary_route']}")
            if details.get("dispatch_notes"):
                notes = details["dispatch_notes"]
                if isinstance(notes, list):
                    context_lines.append(f"Dispatch Notes: {'; '.join(notes[:3])}")

        civilian = next((a for a in proposal.actions if a.get("type") == "civilian_alert"), None)
        if civilian:
            details = civilian.get("details", {})
            if details.get("cooling_center"):
                context_lines.append(f"Nearest Cooling Center: {details['cooling_center']}")

    # ── If no facility data in proposal, do a live lookup ──────────────────────
    if not facility_found:
        facilities = _get_facility_context(lat, lon)
        if facilities.get("hospital"):
            h = facilities["hospital"]
            dist = f"{h['route']['distance_km']} km" if h.get("route") else "nearby"
            context_lines.append(f"NEAREST HOSPITAL: {h['name']} — {dist} away — lat={h['lat']:.5f}, lon={h['lon']:.5f}")
        if facilities.get("fire_station"):
            fs = facilities["fire_station"]
            dist = f"{fs['route']['distance_km']} km" if fs.get("route") else "nearby"
            context_lines.append(f"NEAREST FIRE STATION: {fs['name']} — {dist} away — lat={fs['lat']:.5f}, lon={fs['lon']:.5f}")
        if facilities.get("cooling_center"):
            cc = facilities["cooling_center"]
            context_lines.append(f"NEAREST COOLING CENTER: {cc['name']}")

    if proposal:
        context_lines.append(f"Action Proposal Status: {proposal.approval_status}")

    context_lines.append(f"Audit Events: {audit_count} entries")
    context_lines.append("=== END CONTEXT ===")
    base += "\n".join(context_lines)
    return base


@router.post("/stream")
async def stream_chat(request: ChatRequest):
    """Streaming HRES Agent chat endpoint."""
    system_prompt = _build_system_prompt()
    if request.include_incident_context:
        try:
            incident_obj = get_or_create_active_incident()
            state = get_incident_state(incident_obj.incident_id)
            system_prompt = _build_system_prompt(state)
        except Exception as e:
            logger.warning(f"Could not fetch incident for chat context: {e}")

    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    def generate():
        try:
            for chunk in LLMService.stream_chat(messages, system_prompt=system_prompt):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            yield f"data: {json.dumps({'content': f'[HRES Agent error: {str(e)}]', 'done': True})}\n\n"
        finally:
            yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("")
async def chat(request: ChatRequest):
    """Non-streaming fallback chat endpoint."""
    system_prompt = _build_system_prompt()
    if request.include_incident_context:
        try:
            incident_obj = get_or_create_active_incident()
            state = get_incident_state(incident_obj.incident_id)
            system_prompt = _build_system_prompt(state)
        except Exception:
            pass

    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    prompt_text = system_prompt + "\n\nConversation:\n"
    for msg in messages:
        role_label = "User" if msg["role"] == "user" else "HRES Agent"
        prompt_text += f"{role_label}: {msg['content']}\n"
    prompt_text += "HRES Agent:"

    try:
        reply = LLMService.generate(prompt_text)
        return {"reply": reply}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {"reply": "I'm having trouble connecting right now. Please try again in a moment. The monitoring system is still running."}
