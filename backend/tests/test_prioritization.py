from datetime import datetime
from backend.app.core.schemas import NormalizedEvent, EventType, LocationContext
from backend.app.services.prioritization import calculate_risk_assessment


def test_risk_low_and_moderate():
    loc = LocationContext(
        latitude=26.9124,
        longitude=75.7873,
        source="gps",
        timestamp=datetime.utcnow()
    )

    # Low temperature (e.g. 28 degrees C)
    heat_evt = NormalizedEvent(
        event_id="evt-1",
        event_type=EventType.HEAT,
        location=loc,
        status="verified",
        confidence=1.0,
        value={"temperature": 28.0}
    )

    risk = calculate_risk_assessment([heat_evt])
    assert risk.severity == "LOW"
    assert risk.score < 25.0

    # Moderate temperature (e.g. 35 degrees C)
    heat_evt_mod = NormalizedEvent(
        event_id="evt-2",
        event_type=EventType.HEAT,
        location=loc,
        status="verified",
        confidence=1.0,
        value={"temperature": 35.0}
    )

    risk_mod = calculate_risk_assessment([heat_evt_mod])
    assert risk_mod.severity in ["LOW", "MODERATE"]


def test_risk_fire_override():
    loc = LocationContext(
        latitude=26.9124,
        longitude=75.7873,
        source="gps",
        timestamp=datetime.utcnow()
    )

    heat_evt = NormalizedEvent(
        event_id="evt-1",
        event_type=EventType.HEAT,
        location=loc,
        status="verified",
        confidence=1.0,
        value={"temperature": 45.0}
    )

    fire_evt = NormalizedEvent(
        event_id="evt-2",
        event_type=EventType.POSSIBLE_FIRE,
        location=loc,
        status="likely",  # verified/likely fire
        confidence=0.8,
        value={"smoke_detected": True}
    )

    risk = calculate_risk_assessment([heat_evt, fire_evt])
    # Should override to CRITICAL and score 95.0
    assert risk.severity == "CRITICAL"
    assert risk.score == 95.0
    assert any("Escalated to CRITICAL fire threat" in r for r in risk.reasoning)


def test_roadblock_override():
    loc = LocationContext(
        latitude=26.9124,
        longitude=75.7873,
        source="gps",
        timestamp=datetime.utcnow()
    )

    heat_evt = NormalizedEvent(
        event_id="evt-1",
        event_type=EventType.HEAT,
        location=loc,
        status="verified",
        confidence=1.0,
        value={"temperature": 46.0}
    )

    road_evt = NormalizedEvent(
        event_id="evt-3",
        event_type=EventType.ROAD_BLOCK,
        location=loc,
        status="active",
        confidence=1.0,
        value={"status": "blocked"}
    )

    risk = calculate_risk_assessment([heat_evt, road_evt])
    # Extreme heat (>45) + road blockage override
    assert risk.severity == "CRITICAL"
    assert risk.score >= 85.0
    assert any("Extreme heat (>45°C) combined with active road blockage" in r for r in risk.reasoning)
