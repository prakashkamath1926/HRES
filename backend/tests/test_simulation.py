import os
import sqlite3
from datetime import datetime
from backend.app.repositories.database import init_db, get_db_connection
from backend.app.repositories.incidents import get_incident_state
from backend.app.services.monitoring import reset_active_incident, get_or_create_active_incident
from backend.app.services.simulation import run_simulation_scenario


def test_database_initialization():
    init_db()
    conn, dialect = get_db_connection()
    cursor = conn.cursor()
    
    # Check that tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r["name"] for r in cursor.fetchall()]
    conn.close()

    assert "incidents" in tables
    assert "observations" in tables
    assert "normalized_events" in tables
    assert "approvals" in tables
    assert "audit_events" in tables


def test_simulation_scenario_normal():
    # Make sure we start with a clean db / active incident
    init_db()
    reset_active_incident()

    # Trigger normal_conditions simulation
    state = run_simulation_scenario("normal_conditions")
    assert state is not None
    assert len(state.observations) == 2
    assert len(state.events) == 1
    assert state.risk is not None
    # Normal temperature (around 32 degrees C) -> LOW/MODERATE risk
    assert state.risk.severity in ["LOW", "MODERATE"]
    
    # Audit log should have entries
    assert len(state.audit_log) > 0
    assert any(log["event_type"] == "SIMULATION_INJECTED" for log in state.audit_log)


def test_simulation_escalation_to_critical():
    init_db()
    reset_active_incident()

    # Trigger normal
    run_simulation_scenario("normal_conditions")
    
    # Trigger heat escalation
    state1 = run_simulation_scenario("heat_escalation")
    assert state1.risk.severity in ["HIGH", "CRITICAL"]

    # Trigger smoke report
    state2 = run_simulation_scenario("smoke_report")
    # Due to smoke report + heat escalation, it overrides to CRITICAL
    assert state2.risk.severity == "CRITICAL"
    assert state2.risk.score == 95.0
    
    # Trigger roadblock
    state3 = run_simulation_scenario("road_blockage")
    assert state3.risk.severity == "CRITICAL"
    
    # Read the incident state back from database to verify persistence
    persisted_state = get_incident_state(state3.incident_id)
    assert persisted_state.incident_id == state3.incident_id
    assert persisted_state.risk.severity == "CRITICAL"
    assert len(persisted_state.observations) == 6  # 2 normal, 2 escalation, 1 smoke, 1 roadblock
