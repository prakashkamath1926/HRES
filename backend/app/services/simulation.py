import json
import os
from datetime import datetime, timezone
from backend.app.core.schemas import Observation, LocationContext, DataMode, EventType, IncidentState
from backend.app.repositories.observations import add_observation
from backend.app.repositories.audit_log import add_audit_event
from backend.app.services.monitoring import get_or_create_active_incident, process_incident_updates

SIMULATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "simulations")


def run_simulation_scenario(scenario_name: str) -> IncidentState:
    # 1. Check if scenario file exists
    filename = f"{scenario_name}.json"
    filepath = os.path.join(SIMULATIONS_DIR, filename)
    if not os.path.exists(filepath):
        raise ValueError(f"Simulation scenario '{scenario_name}' not found at {filepath}")

    # 2. Get active incident
    incident = get_or_create_active_incident()
    incident_id = incident.incident_id

    # 3. Read observations from file
    with open(filepath, "r") as f:
        observations_data = json.load(f)

    # Log injection
    add_audit_event(
        incident_id,
        "SIMULATION_INJECTED",
        f"Injected simulation scenario: {scenario_name}",
        {"scenario": scenario_name, "observations_count": len(observations_data)}
    )

    # 4. Ingest observations with fresh timestamps
    now = datetime.utcnow()
    for obs_dict in observations_data:
        # Create fresh timestamps so verification freshness calculations work
        loc_data = obs_dict["location"]
        loc = LocationContext(
            latitude=loc_data["latitude"],
            longitude=loc_data["longitude"],
            address=loc_data.get("address"),
            source=loc_data["source"],
            timestamp=now
        )
        
        obs = Observation(
            observation_id=obs_dict["observation_id"],
            source=obs_dict["source"],
            data_mode=DataMode(obs_dict["data_mode"]),
            event_type=EventType(obs_dict["event_type"]),
            location=loc,
            observed_at=now,
            received_at=now,
            value=obs_dict["value"],
            confidence=obs_dict["confidence"],
            raw_payload=obs_dict.get("raw_payload")
        )

        add_observation(incident_id, obs)
        add_audit_event(
            incident_id,
            "OBSERVATION_RECEIVED",
            f"Observation received from {obs.source} ({obs.event_type.value})",
            {"source": obs.source, "observation_id": obs.observation_id, "data_mode": obs.data_mode.value}
        )

    # 5. Process updates (verification + risk)
    updated_state = process_incident_updates(incident_id)
    return updated_state
