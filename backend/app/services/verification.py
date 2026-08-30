import math
import uuid
from datetime import datetime, timezone
from backend.app.core.schemas import (
    Observation, NormalizedEvent, EventType, LocationContext, DataMode
)

# Constants for source reliability
SOURCE_RELIABILITY = {
    "FortyGuard": 0.95,
    "Open-Meteo": 0.90,
    "Maps": 0.95,
    "User Report": 0.70,
}

def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt



def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Earth's radius in meters
    R = 6371000.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2

    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def get_freshness_score(observed_at: datetime) -> float:
    # Handle both offset-naive and offset-aware datetimes
    now = datetime.now(timezone.utc)
    observed_at_utc = ensure_utc(observed_at)
    diff_seconds = (now - observed_at_utc).total_seconds()
    diff_minutes = diff_seconds / 60.0

    if diff_minutes <= 5:
        return 1.0
    elif diff_minutes <= 15:
        return 0.6
    elif diff_minutes <= 30:
        return 0.3
    else:
        return 0.1


def filter_latest_by_source(obs_list: list[Observation]) -> list[Observation]:
    latest = {}
    for o in obs_list:
        if o.source not in latest or ensure_utc(o.observed_at) >= ensure_utc(latest[o.source].observed_at):
            latest[o.source] = o
    return list(latest.values())


def verify_observations(incident_id: str, observations: list[Observation]) -> list[NormalizedEvent]:
    if not observations:
        return []

    # Group observations by event type
    heat_obs = [o for o in observations if o.event_type == EventType.HEAT]
    smoke_obs = [o for o in observations if o.event_type == EventType.SMOKE_REPORT]
    road_obs = [o for o in observations if o.event_type == EventType.ROAD_BLOCK]

    # Filter latest per source to avoid old data dragging down averages
    heat_obs = filter_latest_by_source(heat_obs)
    smoke_obs = filter_latest_by_source(smoke_obs)
    road_obs = filter_latest_by_source(road_obs)

    normalized_events = []
    
    # 1. Process Heat Events
    if heat_obs:
        # Sort by observed_at descending to get freshest first
        heat_obs.sort(key=lambda x: ensure_utc(x.observed_at), reverse=True)
        primary_obs = heat_obs[0]
        
        # Calculate average temperature
        temps = []
        for o in heat_obs:
            temp = o.value.get("temperature")
            if temp is not None:
                temps.append(temp)
        avg_temp = sum(temps) / len(temps) if temps else 0.0

        # Calculate confidence components
        rel_scores = [SOURCE_RELIABILITY.get(o.source, 0.5) for o in heat_obs]
        reliability = max(rel_scores) if rel_scores else 0.5
        
        fresh_scores = [get_freshness_score(o.observed_at) for o in heat_obs]
        freshness = max(fresh_scores) if fresh_scores else 0.5

        # Consensus exists if both FortyGuard and Open-Meteo have fresh reports within 15 minutes
        has_fg = any(o.source == "FortyGuard" and get_freshness_score(o.observed_at) > 0.5 for o in heat_obs)
        has_om = any(o.source == "Open-Meteo" and get_freshness_score(o.observed_at) > 0.5 for o in heat_obs)
        consensus = 1.0 if (has_fg and has_om) else 0.5

        # Check location match between first two heat observations
        loc_match = 1.0
        if len(heat_obs) > 1:
            dist = haversine_distance(
                heat_obs[0].location.latitude, heat_obs[0].location.longitude,
                heat_obs[1].location.latitude, heat_obs[1].location.longitude
            )
            if dist > 500:
                loc_match = 0.5

        # Confidence calculation
        confidence = (reliability * 0.40) + (freshness * 0.25) + (consensus * 0.25) + (loc_match * 0.10)
        confidence = min(max(confidence, 0.0), 1.0)

        status = "verified" if confidence > 0.75 else "likely"

        normalized_events.append(NormalizedEvent(
            event_id=f"evt-heat-{incident_id[:8]}",
            event_type=EventType.HEAT,
            location=primary_obs.location,
            status=status,
            confidence=confidence,
            value={"temperature": avg_temp, "unit": "celsius"},
            supporting_observations=[o.observation_id for o in heat_obs]
        ))

    # 2. Process Smoke & Possible Fire
    if smoke_obs:
        smoke_obs.sort(key=lambda x: ensure_utc(x.observed_at), reverse=True)
        primary_smoke = smoke_obs[0]

        # Check if there is an active heat escalation (temperature > 40 degrees C)
        extreme_heat = False
        heat_evt = next((e for e in normalized_events if e.event_type == EventType.HEAT), None)
        if heat_evt and heat_evt.value.get("temperature", 0) > 40.0:
            extreme_heat = True

        rel_scores = [SOURCE_RELIABILITY.get(o.source, 0.5) for o in smoke_obs]
        reliability = max(rel_scores) if rel_scores else 0.5
        freshness = get_freshness_score(primary_smoke.observed_at)
        
        # Consensus: if smoke report is supported by extreme heat
        consensus = 1.0 if extreme_heat else 0.0
        loc_match = 1.0 if extreme_heat else 0.5

        confidence = (reliability * 0.40) + (freshness * 0.25) + (consensus * 0.25) + (loc_match * 0.10)
        confidence = min(max(confidence, 0.0), 1.0)

        # Heat alone does not prove fire, but smoke report + extreme heat does
        if extreme_heat:
            status = "likely" if confidence > 0.7 else "possible"
            event_type = EventType.POSSIBLE_FIRE
        else:
            status = "unverified"
            event_type = EventType.POSSIBLE_FIRE

        normalized_events.append(NormalizedEvent(
            event_id=f"evt-fire-{incident_id[:8]}",
            event_type=event_type,
            location=primary_smoke.location,
            status=status,
            confidence=confidence,
            value={
                "smoke_detected": True,
                "description": primary_smoke.value.get("description", ""),
                "extreme_heat_confirmed": extreme_heat
            },
            supporting_observations=[o.observation_id for o in smoke_obs]
        ))

    # 3. Process Road Blocks
    if road_obs:
        road_obs.sort(key=lambda x: ensure_utc(x.observed_at), reverse=True)
        primary_road = road_obs[0]

        rel_scores = [SOURCE_RELIABILITY.get(o.source, 0.5) for o in road_obs]
        reliability = max(rel_scores) if rel_scores else 0.5
        freshness = get_freshness_score(primary_road.observed_at)
        consensus = 1.0  # Maps road block is self-consistent
        loc_match = 1.0

        confidence = (reliability * 0.40) + (freshness * 0.25) + (consensus * 0.25) + (loc_match * 0.10)
        confidence = min(max(confidence, 0.0), 1.0)

        normalized_events.append(NormalizedEvent(
            event_id=f"evt-roadblock-{incident_id[:8]}",
            event_type=EventType.ROAD_BLOCK,
            location=primary_road.location,
            status="active",
            confidence=confidence,
            value=primary_road.value,
            supporting_observations=[o.observation_id for o in road_obs]
        ))

    return normalized_events
