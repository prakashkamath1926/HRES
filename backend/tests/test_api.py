from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.repositories.database import init_db

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_api_location_endpoint():
    init_db()
    payload = {
        "latitude": 26.9124,
        "longitude": 75.7873,
        "address": "Test Campus, Jaipur",
        "source": "user"
    }
    response = client.post("/api/location", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "incident_id" in data
    assert len(data["audit_log"]) > 0
    assert any("Test Campus, Jaipur" in log["message"] for log in data["audit_log"])


def test_api_simulations_and_incidents():
    init_db()
    # Trigger simulation reset
    response = client.post("/api/simulations/reset")
    assert response.status_code == 200
    data = response.json()
    incident_id = data["incident_id"]

    # Trigger normal_conditions
    response = client.post("/api/simulations/normal_conditions")
    assert response.status_code == 200
    data = response.json()
    assert len(data["observations"]) == 2

    # Get current incident
    response = client.get("/api/incidents/current")
    assert response.status_code == 200
    assert response.json()["incident_id"] == incident_id

    # Resolve incident
    response = client.post(f"/api/incidents/{incident_id}/resolve")
    assert response.status_code == 200
    assert response.json()["status"] == "resolved"


def test_api_approval_gate():
    init_db()
    # Trigger reset and then heat_escalation to generate an action proposal
    client.post("/api/simulations/reset")
    client.post("/api/simulations/heat_escalation")
    
    current_resp = client.get("/api/incidents/current")
    current_data = current_resp.json()
    incident_id = current_data["incident_id"]
    
    assert current_data["action_proposal"] is not None
    assert current_data["action_proposal"]["approval_status"] == "pending"

    # Submit operator approval
    approval_payload = {
        "decision": "approved",
        "comment": "Operator approved for simulation demo",
        "operator_id": "test-admin",
        "proposal_version": 1
    }
    response = client.post(f"/api/incidents/{incident_id}/approval", json=approval_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["action_proposal"]["approval_status"] == "approved"
    assert data["action_proposal"]["approved_by"] == "test-admin"
    assert data["status"] == "active"
    assert any("Operator approved for simulation demo" in log["message"] or "test-admin" in str(log["payload"]) for log in data["audit_log"])
