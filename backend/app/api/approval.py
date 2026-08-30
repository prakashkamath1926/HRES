import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from backend.app.core.schemas import IncidentState, ApprovalStatus, IncidentStatus, ActionProposal
from backend.app.repositories.incidents import get_incident_state, update_incident_state_data
from backend.app.repositories.approvals import add_approval
from backend.app.repositories.audit_log import add_audit_event

router = APIRouter(prefix="/incidents", tags=["approvals"])


class ApprovalPayload(BaseModel):
    decision: str
    comment: str | None = None
    operator_id: str | None = None
    proposal_version: int = 1


@router.post("/{incident_id}/approval", response_model=IncidentState)
def submit_approval(incident_id: str, payload: ApprovalPayload):
    incident = get_incident_state(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if not incident.action_proposal:
        raise HTTPException(status_code=400, detail="No active action proposal to approve")

    # Map decision string to ApprovalStatus enum
    decision_map = {
        "approved": ApprovalStatus.APPROVED,
        "modified": ApprovalStatus.MODIFIED,
        "rejected": ApprovalStatus.REJECTED,
        "escalated": ApprovalStatus.ESCALATED
    }
    
    status_enum = decision_map.get(payload.decision.lower())
    if not status_enum:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid decision '{payload.decision}'. Allowed values: approved, modified, rejected, escalated."
        )

    # Save to approvals table
    add_approval(
        incident_id=incident_id,
        decision=status_enum.value,
        comment=payload.comment,
        operator_id=payload.operator_id,
        proposal_version=payload.proposal_version
    )

    # Resume the LangGraph workflow with decision details
    from backend.app.services.monitoring import resume_approval
    resumed_state = resume_approval(
        incident_id=incident_id,
        payload={
            "decision": payload.decision,
            "comment": payload.comment,
            "operator_id": payload.operator_id,
            "proposal_version": payload.proposal_version
        }
    )

    return resumed_state
