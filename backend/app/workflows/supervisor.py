from datetime import datetime
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from backend.app.core.state import HRESGraphState
from backend.app.core.schemas import (
    IncidentStatus, ApprovalStatus, RiskAssessment, ActionProposal, EventType
)
from backend.app.agents.verification_agent import verification_agent_node
from backend.app.agents.civilian_agent import civilian_agent_node
from backend.app.agents.response_agent import response_agent_node
from backend.app.agents.civic_agent import civic_agent_node
from backend.app.services.prioritization import calculate_risk_assessment
from backend.app.repositories.audit_log import add_audit_event


def risk_node(state: HRESGraphState) -> dict:
    risk = calculate_risk_assessment(state["events"])
    return {"risk": risk}


def supervisor_node(state: HRESGraphState) -> dict:
    risk = state["risk"]
    severity = risk.severity if risk else "LOW"

    # Auto-initialize action proposal if not present
    proposal = state.get("action_proposal")
    if not proposal:
        proposal = ActionProposal(
            actions=[],
            status="Draft initialized",
            reasoning=["Supervisor initialized new response draft."],
            approval_status=ApprovalStatus.PENDING if severity in ["HIGH", "CRITICAL"] else ApprovalStatus.NOT_REQUIRED
        )

    # Decide conditional path based on risk severity
    if severity in ["LOW", "MODERATE"]:
        add_audit_event(
            state["incident_id"],
            "SUPERVISOR_ROUTING",
            f"Risk is {severity}. No immediate responder routing required.",
            {"severity": severity}
        )
        proposal.approval_status = ApprovalStatus.NOT_REQUIRED
        return {
            "next_step": "end",
            "status": IncidentStatus.MONITORING,
            "action_proposal": proposal
        }

    # If HIGH or CRITICAL, check route blockage or fire to route specialized response
    has_fire = any(e for e in state["events"] if e.event_type == EventType.POSSIBLE_FIRE and e.status == "likely")
    has_roadblock = any(e for e in state["events"] if e.event_type == EventType.ROAD_BLOCK)

    if has_fire or has_roadblock:
        add_audit_event(
            state["incident_id"],
            "SUPERVISOR_ROUTING",
            f"Risk is {severity} with active fire or roadblock. Activating full response flow.",
            {"has_fire": has_fire, "has_roadblock": has_roadblock}
        )
        return {
            "next_step": "response",
            "status": IncidentStatus.PLANNING,
            "action_proposal": proposal
        }
    else:
        add_audit_event(
            state["incident_id"],
            "SUPERVISOR_ROUTING",
            f"Risk is {severity}. Activating civilian alert flow.",
            {"has_fire": has_fire, "has_roadblock": has_roadblock}
        )
        return {
            "next_step": "civilian",
            "status": IncidentStatus.PLANNING,
            "action_proposal": proposal
        }


def conditional_supervisor_edge(state: HRESGraphState) -> str:
    return state["next_step"]


def approval_gate_node(state: HRESGraphState) -> dict:
    proposal = state.get("action_proposal")
    if not proposal:
        return {}

    # Skip approval if not required (LOW/MODERATE)
    if proposal.approval_status == ApprovalStatus.NOT_REQUIRED:
        return {"status": IncidentStatus.ACTIVE}

    # If it reached here during execution, the operator decision has already been merged into proposal.
    # We update the status to ACTIVE if the operator approved, otherwise keep it AWAITING_APPROVAL.
    status_enum = proposal.approval_status
    new_status = IncidentStatus.ACTIVE if status_enum == ApprovalStatus.APPROVED else IncidentStatus.AWAITING_APPROVAL

    return {
        "status": new_status,
        "action_proposal": proposal
    }


# Assemble State Graph
workflow = StateGraph(HRESGraphState)

# Add Nodes
workflow.add_node("verification", verification_agent_node)
workflow.add_node("risk", risk_node)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("civilian", civilian_agent_node)
workflow.add_node("response", response_agent_node)
workflow.add_node("civic", civic_agent_node)
workflow.add_node("approval_gate", approval_gate_node)

# Set Entry Edge
workflow.add_edge(START, "verification")
workflow.add_edge("verification", "risk")
workflow.add_edge("risk", "supervisor")

# Set Conditional Routing Edge from Supervisor
workflow.add_conditional_edges(
    "supervisor",
    conditional_supervisor_edge,
    {
        "response": "response",
        "civilian": "civilian",
        "end": END
    }
)

# Linear flows
# Full flow: response -> civilian -> civic -> approval_gate -> END
workflow.add_edge("response", "civilian")
workflow.add_edge("civilian", "civic")
workflow.add_edge("civic", "approval_gate")
workflow.add_edge("approval_gate", END)

# Compile graph with classic checkpointer interrupt configured before approval_gate
memory_checkpointer = MemorySaver()
app_graph = workflow.compile(
    checkpointer=memory_checkpointer,
    interrupt_before=["approval_gate"]
)
