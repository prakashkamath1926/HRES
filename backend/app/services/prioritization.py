from backend.app.core.schemas import RiskAssessment, NormalizedEvent, EventType


def calculate_risk_assessment(events: list[NormalizedEvent]) -> RiskAssessment:
    reasoning = []

    # Find the verified heat event
    heat_evt = next((e for e in events if e.event_type == EventType.HEAT), None)
    temp = heat_evt.value.get("temperature", 30.0) if heat_evt else 30.0
    heat_confidence = heat_evt.confidence if heat_evt else 0.0

    # 1. Heat Severity Score
    if temp <= 30.0:
        heat_severity_score = 0.0
    elif temp >= 50.0:
        heat_severity_score = 100.0
    else:
        heat_severity_score = (temp - 30.0) / (50.0 - 30.0) * 100.0

    reasoning.append(f"Temperature observed: {temp:.1f}°C (Severity score: {heat_severity_score:.1f})")

    # 2. Exposure & Vulnerability Scores (Jaipur Campus defaults, scaled by hazard severity)
    factor = heat_severity_score / 100.0
    exposure_score = 80.0 * factor
    vulnerability_score = 70.0 * factor
    reasoning.append(f"Setting context: high-density educational campus zone (Exposure: {exposure_score:.1f}, Vulnerability: {vulnerability_score:.1f})")

    # 3. Confidence Score
    confidence_score = heat_confidence * 100.0
    reasoning.append(f"Verification confidence: {confidence_score:.1f}%")

    # 4. Access Constraint Score (Road Blockages)
    has_roadblock = any(e for e in events if e.event_type == EventType.ROAD_BLOCK)
    access_constraint_score = 100.0 if has_roadblock else 0.0
    if has_roadblock:
        reasoning.append("Access constraint active: Road blockage detected on main campus route (Access constraint score: 100.0)")

    # Base Priority Score Calculation
    priority_score = (
        (heat_severity_score * 0.35) +
        (exposure_score * 0.20) +
        (vulnerability_score * 0.20) +
        (confidence_score * 0.15) +
        (access_constraint_score * 0.10)
    )

    # Classify severity
    if priority_score < 25.0:
        severity = "LOW"
    elif priority_score < 50.0:
        severity = "MODERATE"
    elif priority_score < 75.0:
        severity = "HIGH"
    else:
        severity = "CRITICAL"

    priority = severity

    # --- Deterministic Safety Overrides ---

    # Fire event check
    fire_evt = next((e for e in events if e.event_type == EventType.POSSIBLE_FIRE), None)
    if fire_evt:
        if fire_evt.status == "likely":
            priority_score = 95.0
            severity = "CRITICAL"
            priority = "CRITICAL"
            reasoning.append("OVERRIDE: Active smoke report verified by extreme temperature. Escalated to CRITICAL fire threat.")
        elif fire_evt.status == "unverified":
            reasoning.append("MONITORING: Smoke report received but remains unverified (no local temperature anomaly). Awaiting operator review.")

    # Extreme heat access override
    if temp > 45.0 and has_roadblock:
        priority_score = max(priority_score, 85.0)
        severity = "CRITICAL"
        priority = "CRITICAL"
        reasoning.append("OVERRIDE: Extreme heat (>45°C) combined with active road blockage escalated to CRITICAL.")

    # Clamp priority score
    priority_score = min(max(priority_score, 0.0), 100.0)

    return RiskAssessment(
        score=round(priority_score, 2),
        severity=severity,
        exposure=exposure_score,
        priority=priority,
        reasoning=reasoning
    )
