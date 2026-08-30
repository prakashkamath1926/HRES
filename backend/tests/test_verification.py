import uuid
from datetime import datetime, timedelta
from backend.app.core.schemas import Observation, LocationContext, DataMode, EventType
from backend.app.services.verification import verify_observations, get_freshness_score


def test_freshness_score():
    # Fresh observation
    assert get_freshness_score(datetime.utcnow()) == 1.0

    # 10 minutes old observation
    assert get_freshness_score(datetime.utcnow() - timedelta(minutes=10)) == 0.6

    # 40 minutes old observation
    assert get_freshness_score(datetime.utcnow() - timedelta(minutes=40)) == 0.1


def test_verification_heat_consensus():
    incident_id = "test-incident-123"
    loc = LocationContext(
        latitude=26.9124,
        longitude=75.7873,
        source="gps",
        timestamp=datetime.utcnow()
    )

    # 1. FortyGuard heat observation
    fg_obs = Observation(
        observation_id="fg-1",
        source="FortyGuard",
        data_mode=DataMode.LIVE,
        event_type=EventType.HEAT,
        location=loc,
        observed_at=datetime.utcnow(),
        received_at=datetime.utcnow(),
        value={"temperature": 40.0, "unit": "celsius"},
        confidence=1.0
    )

    # 2. Open-Meteo heat observation
    om_obs = Observation(
        observation_id="om-1",
        source="Open-Meteo",
        data_mode=DataMode.LIVE,
        event_type=EventType.HEAT,
        location=loc,
        observed_at=datetime.utcnow(),
        received_at=datetime.utcnow(),
        value={"temperature": 38.0, "unit": "celsius"},
        confidence=1.0
    )

    # Calculate verify_observations with BOTH
    events = verify_observations(incident_id, [fg_obs, om_obs])
    assert len(events) == 1
    heat_evt = events[0]
    assert heat_evt.event_type == EventType.HEAT
    assert heat_evt.value["temperature"] == 39.0  # Average of 40 and 38
    # Confidence should be high due to consensus (1.0), freshness (1.0), and reliability
    assert heat_evt.confidence > 0.8
    assert heat_evt.status == "verified"


def test_verification_smoke_without_heat():
    incident_id = "test-incident-123"
    loc = LocationContext(
        latitude=26.9124,
        longitude=75.7873,
        source="gps",
        timestamp=datetime.utcnow()
    )

    smoke_obs = Observation(
        observation_id="smoke-1",
        source="User Report",
        data_mode=DataMode.SIMULATED,
        event_type=EventType.SMOKE_REPORT,
        location=loc,
        observed_at=datetime.utcnow(),
        received_at=datetime.utcnow(),
        value={"smoke_detected": True, "description": "Smoke near dorms"},
        confidence=0.8
    )

    events = verify_observations(incident_id, [smoke_obs])
    # Should create a POSSIBLE_FIRE event
    fire_evt = next((e for e in events if e.event_type == EventType.POSSIBLE_FIRE), None)
    assert fire_evt is not None
    assert fire_evt.status == "unverified"  # No heat to corroborate it
    assert fire_evt.confidence < 0.6  # Low consensus score (0.5)


def test_verification_smoke_with_extreme_heat():
    incident_id = "test-incident-123"
    loc = LocationContext(
        latitude=26.9124,
        longitude=75.7873,
        source="gps",
        timestamp=datetime.utcnow()
    )

    fg_obs = Observation(
        observation_id="fg-1",
        source="FortyGuard",
        data_mode=DataMode.LIVE,
        event_type=EventType.HEAT,
        location=loc,
        observed_at=datetime.utcnow(),
        received_at=datetime.utcnow(),
        value={"temperature": 46.0, "unit": "celsius"},
        confidence=1.0
    )

    smoke_obs = Observation(
        observation_id="smoke-1",
        source="User Report",
        data_mode=DataMode.SIMULATED,
        event_type=EventType.SMOKE_REPORT,
        location=loc,
        observed_at=datetime.utcnow(),
        received_at=datetime.utcnow(),
        value={"smoke_detected": True, "description": "Smoke near dorms"},
        confidence=0.8
    )

    events = verify_observations(incident_id, [fg_obs, smoke_obs])
    fire_evt = next((e for e in events if e.event_type == EventType.POSSIBLE_FIRE), None)
    assert fire_evt is not None
    assert fire_evt.status == "likely"  # Heat is extreme, so consensus is high (1.0)
    assert fire_evt.confidence > 0.7
