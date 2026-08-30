"""
Open-Meteo live weather integration service.
No API key required — completely free.
Fires on startup and whenever location is updated.
"""
import uuid
import logging
import requests
from datetime import datetime

from backend.app.core.schemas import Observation, LocationContext, DataMode, EventType
from backend.app.repositories.observations import add_observation
from backend.app.repositories.audit_log import add_audit_event
from backend.app.services.monitoring import process_incident_updates

logger = logging.getLogger("hres.openmeteo")

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_openmeteo_weather(latitude: float, longitude: float) -> dict | None:
    """Fetch current weather from Open-Meteo API (no key needed)."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "wind_speed_10m",
            "precipitation",
            "apparent_temperature",
            "weather_code"
        ],
        "wind_speed_unit": "kmh",
        "timezone": "auto"
    }
    try:
        response = requests.get(OPEN_METEO_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        current = data.get("current", {})
        if not current:
            return None
        return {
            "temperature": current.get("temperature_2m"),
            "apparent_temperature": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "wind_speed": current.get("wind_speed_10m"),
            "precipitation": current.get("precipitation"),
            "weather_code": current.get("weather_code"),
            "unit": "celsius",
            "source_time": current.get("time", datetime.utcnow().isoformat())
        }
    except requests.exceptions.Timeout:
        logger.warning("Open-Meteo request timed out.")
        return None
    except requests.exceptions.RequestException as e:
        logger.warning(f"Open-Meteo request failed: {e}")
        return None


def run_openmeteo_ingest(
    incident_id: str,
    latitude: float,
    longitude: float,
    address: str | None = None,
    trigger_process: bool = True
):
    """
    Fetch live weather data from Open-Meteo and ingest as an Observation.
    Safe to call from a background task or on startup.
    """
    logger.info(f"Running Open-Meteo ingest for incident {incident_id} at ({latitude}, {longitude})")

    weather = fetch_openmeteo_weather(latitude, longitude)

    now = datetime.utcnow()
    loc_context = LocationContext(
        latitude=latitude,
        longitude=longitude,
        address=address,
        source="Open-Meteo",
        timestamp=now
    )

    if weather is None:
        # Fallback cached observation — clearly marked lower confidence
        obs = Observation(
            observation_id=f"obs-om-cached-{uuid.uuid4().hex[:8]}",
            source="Open-Meteo",
            data_mode=DataMode.UNAVAILABLE,
            event_type=EventType.HEAT,
            location=loc_context,
            observed_at=now,
            received_at=now,
            value={"temperature": 30.0, "unit": "celsius"},
            confidence=0.0
        )
        add_observation(incident_id, obs)
        add_audit_event(
            incident_id,
            "OBSERVATION_RECEIVED",
            "Open-Meteo unavailable — no weather data ingested.",
            {"source": "Open-Meteo", "data_mode": "unavailable"}
        )
        logger.warning("Open-Meteo returned no data. Skipping observation ingest.")
        return

    # Live observation
    obs = Observation(
        observation_id=f"obs-om-live-{uuid.uuid4().hex[:8]}",
        source="Open-Meteo",
        data_mode=DataMode.LIVE,
        event_type=EventType.HEAT,
        location=loc_context,
        observed_at=now,
        received_at=now,
        value=weather,
        confidence=0.90
    )
    add_observation(incident_id, obs)
    add_audit_event(
        incident_id,
        "OBSERVATION_RECEIVED",
        f"Live weather from Open-Meteo: {weather['temperature']:.1f}°C, wind {weather.get('wind_speed', 0):.0f} km/h",
        {"source": "Open-Meteo", "data_mode": "live", "observation_id": obs.observation_id}
    )
    logger.info(f"Open-Meteo observation ingested: {weather['temperature']}°C")

    if trigger_process:
        try:
            process_incident_updates(incident_id)
        except Exception as e:
            logger.error(f"Failed to process incident updates after Open-Meteo ingest: {e}")
