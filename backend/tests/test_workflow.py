from datetime import datetime
from backend.app.core.schemas import IncidentStatus, ApprovalStatus
from backend.app.repositories.database import init_db
from backend.app.services.monitoring import reset_active_incident, get_or_create_active_incident, resume_approval
from backend.app.services.simulation import run_simulation_scenario
from backend.app.workflows.supervisor import app_graph


def test_langgraph_flow_moderate():
    init_db()
    reset_active_incident()

    # Ingest normal conditions (low temp / moderate)
    state = run_simulation_scenario("normal_conditions")
    
    # Low / moderate risk should NOT trigger response agents or approval gate
    # Incident status should be MONITORING and approval should be NOT_REQUIRED
    assert state.status == IncidentStatus.MONITORING
    assert state.action_proposal is not None
    assert state.action_proposal.approval_status == ApprovalStatus.NOT_REQUIRED


def test_langgraph_flow_critical_approval_gate():
    init_db()
    reset_active_incident()

    # Trigger heat escalation
    run_simulation_scenario("heat_escalation")
    # Trigger smoke report to override risk to CRITICAL
    state = run_simulation_scenario("smoke_report")

    # Due to CRITICAL risk, LangGraph must run up to approval_gate and pause.
    # Incident status must be AWAITING_APPROVAL and action proposal must be pending approval.
    assert state.status == IncidentStatus.AWAITING_APPROVAL
    assert state.action_proposal is not None
    assert state.action_proposal.approval_status == ApprovalStatus.PENDING
    assert len(state.action_proposal.actions) > 0

    # Verify that civilian safety tips and notifications are present
    civilian_action = next((a for a in state.action_proposal.actions if a["type"] == "civilian_alert"), None)
    assert civilian_action is not None
    assert "safety_tips" in civilian_action["details"]

    # Verify that civic notification drafts are present
    civic_action = next((a for a in state.action_proposal.actions if a["type"] == "civic_report"), None)
    assert civic_action is not None

    # Check that LangGraph has a pending interrupt in the checkpointer
    config = {"configurable": {"thread_id": state.incident_id}}
    graph_state = app_graph.get_state(config)
    assert len(graph_state.next) > 0
    assert graph_state.next[0] == "approval_gate"

    # Resume the gate with an operator decision
    payload = {
        "decision": "approved",
        "comment": "Operator verified fire report",
        "operator_id": "operator-007",
        "proposal_version": 1
    }
    updated_state = resume_approval(state.incident_id, payload)

    # Post-resumption state checks
    assert updated_state.status == IncidentStatus.ACTIVE
    assert updated_state.action_proposal.approval_status == ApprovalStatus.APPROVED
    assert updated_state.action_proposal.approved_by == "operator-007"
    
    # Audit log should log resumption
    assert any("Operator decision: approved" in log["message"] for log in updated_state.audit_log)
