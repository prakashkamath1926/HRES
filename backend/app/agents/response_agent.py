from pydantic import BaseModel, Field
from backend.app.core.state import HRESGraphState
from backend.app.core.schemas import ActionProposal, EventType
from backend.app.integrations.llm import LLMService
from backend.app.services.routing_service import get_nearest_facilities
import logging

logger = logging.getLogger("hres.response_agent")


class ResponseGuidance(BaseModel):
    responder_alert: str = Field(description="Headline alert details for responders")
    primary_route_recommendation: str = Field(description="Primary access route suggestion for ambulance/fire trucks")
    alternate_route_recommendation: str = Field(description="Alternate secondary route suggestion in case of roadblock")
    dispatch_notes: list[str] = Field(description="Special operational safety guidelines for emergency response personnel")


def get_response_fallback() -> ResponseGuidance:
    return ResponseGuidance(
        responder_alert="DISPATCH ADVISORY - HEAT RESILIENCE EVENT IN PROGRESS",
        primary_route_recommendation="Use nearest available route to the incident site.",
        alternate_route_recommendation="Use alternate route if primary is blocked.",
        dispatch_notes=[
            "Monitor team core temperature and rotate duties every 20 minutes.",
            "Bring portable cooling shields and hydration stations.",
            "Establish unified command post at nearest open area."
        ]
    )


def response_agent_node(state: HRESGraphState) -> dict:
    incident_id = state["incident_id"]
    risk = state["risk"]
    severity = risk.severity if risk else "UNKNOWN"
    score = risk.score if risk else 0.0

    # Check for active roadblock
    has_blockage = any(e for e in state["events"] if e.event_type == EventType.ROAD_BLOCK)
    blockage_info = "Main route BLOCKED" if has_blockage else "Routes clear"

    # Get real location from latest observation
    observations = state.get("observations", [])
    lat, lon, address = 26.9124, 75.7873, "Current monitored location"
    if observations:
        last_obs = observations[-1]
        lat = last_obs.location.latitude
        lon = last_obs.location.longitude
        address = last_obs.location.address or address

    # Live facility + route lookup (Overpass + OSRM)
    facilities = {}
    try:
        logger.info(f"Response Agent: Looking up facilities near ({lat}, {lon})")
        facilities = get_nearest_facilities(lat, lon)
    except Exception as e:
        logger.warning(f"Facility lookup failed: {e}")

    # Build facility-aware prompt
    hospital_info = "unknown location"
    fire_station_info = "unknown location"
    if facilities.get("hospital"):
        h = facilities["hospital"]
        dist = f"{h['route']['distance_km']} km away" if h.get("route") else "nearby"
        hospital_info = f"{h['name']} ({dist})"
    if facilities.get("fire_station"):
        fs = facilities["fire_station"]
        dist = f"{fs['route']['distance_km']} km away" if fs.get("route") else "nearby"
        fire_station_info = f"{fs['name']} ({dist})"

    prompt = (
        f"Draft operational guidance for emergency responders (Ambulance, Fire, Campus Security).\n"
        f"Incident Context:\n"
        f"- Risk Level: {severity} (Score: {score:.0f}/100)\n"
        f"- Route Constraints: {blockage_info}\n"
        f"- Location: {address} (lat={lat:.4f}, lon={lon:.4f})\n"
        f"- Nearest Hospital: {hospital_info}\n"
        f"- Nearest Fire Station: {fire_station_info}\n"
        f"Generate precise, calm, and actionable guidance for responders using the real facility info above.\n"
        f"IMPORTANT: You MUST explicitly list the Nearest Hospital and Nearest Fire Station in your guidance. Do not use ** markdown bolding anywhere."
    )

    guidance = LLMService.generate_structured(
        prompt=prompt,
        schema_class=ResponseGuidance,
        fallback_factory=get_response_fallback
    )

    # Build action with real facility data embedded
    proposal = state["action_proposal"]
    actions = list(proposal.actions) if proposal else []

    action_detail = {
        "primary_route": guidance.primary_route_recommendation,
        "alternate_route": guidance.alternate_route_recommendation,
        "dispatch_notes": guidance.dispatch_notes,
    }

    # Inject real facility data into the action
    if facilities.get("hospital"):
        h = facilities["hospital"]
        action_detail["hospital"] = {
            "name": h["name"],
            "lat": h["lat"],
            "lon": h["lon"],
            "distance_km": h["route"]["distance_km"] if h.get("route") else None,
            "duration_min": h["route"]["duration_min"] if h.get("route") else None,
            "route_geojson": h["route"]["geometry"] if h.get("route") else None,
        }

    if facilities.get("fire_station"):
        fs = facilities["fire_station"]
        action_detail["fire_station"] = {
            "name": fs["name"],
            "lat": fs["lat"],
            "lon": fs["lon"],
            "distance_km": fs["route"]["distance_km"] if fs.get("route") else None,
            "duration_min": fs["route"]["duration_min"] if fs.get("route") else None,
            "route_geojson": fs["route"]["geometry"] if fs.get("route") else None,
        }

    actions.append({
        "type": "responder_guidance",
        "title": guidance.responder_alert,
        "details": action_detail
    })

    # Record routes in state
    routes = list(state.get("routes", []))
    route_entry = {
        "version": len(routes) + 1,
        "reason": "ROAD_BLOCK" if has_blockage else "NORMAL",
        "primary": guidance.primary_route_recommendation,
    }
    if has_blockage:
        route_entry["alternate"] = guidance.alternate_route_recommendation
    if facilities.get("hospital") and facilities["hospital"].get("route"):
        route_entry["hospital_route_geojson"] = facilities["hospital"]["route"]["geometry"]
    if facilities.get("fire_station") and facilities["fire_station"].get("route"):
        route_entry["fire_station_route_geojson"] = facilities["fire_station"]["route"]["geometry"]
    routes.append(route_entry)

    reasoning = list(proposal.reasoning) if proposal else []
    reasoning.append(
        f"Response Agent: Prepared responder guidance. "
        f"Hospital: {hospital_info}. Fire station: {fire_station_info}."
    )

    new_proposal = ActionProposal(
        actions=actions,
        status="Guidance generated",
        reasoning=reasoning,
        approval_status=proposal.approval_status if proposal else "pending"
    )

    return {
        "action_proposal": new_proposal,
        "routes": routes
    }
