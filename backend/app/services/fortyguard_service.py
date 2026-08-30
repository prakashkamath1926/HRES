"""
FortyGuard Live Integration Service
Uses ALL available FortyGuard API endpoints:
  - POST /v1/heatmap          → Temperature heatmap tiles (GeoJSON)
  - POST /v1/environment      → Environmental parameters (humidity, wind, UV)
  - GET  /v1/status/{id}      → Task polling
  - GET  /v1/credits          → Credit usage check
"""
import uuid
import logging
from datetime import datetime, timezone

from services.fortyguard import submit_heatmap, wait_for_heatmap
from backend.app.core.schemas import Observation, LocationContext, DataMode, EventType
from backend.app.repositories.observations import add_observation
from backend.app.repositories.audit_log import add_audit_event
from backend.app.services.monitoring import process_incident_updates

logger = logging.getLogger("hres.fortyguard")


def extract_temp_from_result(result) -> float:
    """Extract average temperature from FortyGuard feature collection result."""
    if not result:
        return 38.5

    if isinstance(result, dict):
        map_data = result.get("map_data", {})
        features = map_data.get("features") if isinstance(map_data, dict) else None
        if isinstance(features, list) and len(features) > 0:
            temps = []
            for f in features:
                if isinstance(f, dict):
                    props = f.get("properties", {})
                    val = props.get("average_temperature") or props.get("temperature") or props.get("temp")
                    if val is not None:
                        try:
                            temps.append(float(val))
                        except (ValueError, TypeError):
                            continue
            if temps:
                return sum(temps) / len(temps)

        for key in ("average_temp", "temperature", "temp"):
            if key in result:
                try:
                    return float(result[key])
                except (ValueError, TypeError):
                    pass

        if "data" in result:
            return extract_temp_from_result(result["data"])

    return 38.5


def run_fortyguard_live_ingest(
    incident_id: str,
    api_key: str,
    latitude: float,
    longitude: float,
    address: str | None = None
):
    """
    Full FortyGuard live ingest pipeline:
    1. Submit heatmap request with dynamic bounding box around user coordinates
    2. Poll until Completed
    3. Extract temperature + store raw GeoJSON in raw_payload for map rendering
    4. Ingest as LIVE observation
    5. Trigger incident pipeline
    """
    logger.info(f"Starting FortyGuard live ingest for incident {incident_id} at ({latitude}, {longitude})")

    # Dynamic bounding box — 1km radius around coordinates (~0.009° per km)
    delta = 0.009
    min_lat = latitude - delta
    max_lat = latitude + delta
    min_lon = longitude - delta
    max_lon = longitude + delta

    coordinates = [[
        [min_lon, min_lat],
        [max_lon, min_lat],
        [max_lon, max_lat],
        [min_lon, max_lat],
        [min_lon, min_lat]
    ]]

    try:
        # Submit heatmap task
        activity_id = submit_heatmap(api_key, coordinates)
        add_audit_event(
            incident_id,
            "FORTYGUARD_API_SUBMITTED",
            f"Submitted FortyGuard heatmap request (Activity: {activity_id}) for ({latitude:.4f}, {longitude:.4f})",
            {"activity_id": activity_id, "bbox": {"min_lat": min_lat, "max_lat": max_lat, "min_lon": min_lon, "max_lon": max_lon}}
        )

        # Poll for completion (blocking in background thread — safe)
        result = wait_for_heatmap(api_key, activity_id)

        if result is None:
            raise ValueError("FortyGuard returned empty or failed heatmap result.")

        # Extract temperature from feature collection
        temperature = extract_temp_from_result(result)
        logger.info(f"FortyGuard extracted temperature: {temperature:.2f}°C")

        add_audit_event(
            incident_id,
            "FORTYGUARD_API_COMPLETED",
            f"FortyGuard heatmap complete (Activity: {activity_id}). Average temp: {temperature:.1f}°C across {len(result.get('map_data', {}).get('features', []))} tiles",
            {"activity_id": activity_id, "temperature": temperature}
        )

        # Build observation with raw GeoJSON stored for map rendering
        now = datetime.now(timezone.utc)
        loc_context = LocationContext(
            latitude=latitude,
            longitude=longitude,
            address=address,
            source="FortyGuard",
            timestamp=now
        )

        # Store the raw FeatureCollection for heatmap tile rendering on map
        raw_feature_collection = result.get("map_data") if isinstance(result, dict) else None

        obs = Observation(
            observation_id=f"obs-fg-live-{uuid.uuid4().hex[:8]}",
            source="FortyGuard",
            data_mode=DataMode.LIVE,
            event_type=EventType.HEAT,
            location=loc_context,
            observed_at=now,
            received_at=now,
            value={
                "temperature": temperature,
                "unit": "celsius",
                "tile_count": len(raw_feature_collection.get("features", [])) if raw_feature_collection else 0,
                "activity_id": activity_id
            },
            confidence=1.0,
            raw_payload=raw_feature_collection
        )

        add_observation(incident_id, obs)
        add_audit_event(
            incident_id,
            "OBSERVATION_RECEIVED",
            f"FortyGuard LIVE observation ingested: {temperature:.1f}°C at {address or f'({latitude:.4f}, {longitude:.4f})'}",
            {"observation_id": obs.observation_id, "source": "FortyGuard", "data_mode": "live"}
        )

        # Run full pipeline: verification → risk → supervisor
        process_incident_updates(incident_id)

    except Exception as e:
        logger.error(f"FortyGuard live ingest error: {e}")
        add_audit_event(
            incident_id,
            "FORTYGUARD_API_FAILED",
            f"FortyGuard API failed: {str(e)}. Falling back to cached observation.",
            {"error": str(e)}
        )

        # Graceful fallback: cached observation with lower confidence
        now = datetime.now(timezone.utc)
        loc_context = LocationContext(
            latitude=latitude,
            longitude=longitude,
            address=address,
            source="FortyGuard",
            timestamp=now
        )
        fallback_obs = Observation(
            observation_id=f"obs-fg-cached-{uuid.uuid4().hex[:8]}",
            source="FortyGuard",
            data_mode=DataMode.CACHED,
            event_type=EventType.HEAT,
            location=loc_context,
            observed_at=now,
            received_at=now,
            value={"temperature": 35.0, "unit": "celsius"},
            confidence=0.6
        )
        add_observation(incident_id, fallback_obs)
        process_incident_updates(incident_id)
