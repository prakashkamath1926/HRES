from typing import TypedDict
from backend.app.core.schemas import (
    IncidentStatus, Observation, NormalizedEvent, RiskAssessment, ActionProposal
)


class HRESGraphState(TypedDict):
    incident_id: str
    status: IncidentStatus
    observations: list[Observation]
    events: list[NormalizedEvent]
    risk: RiskAssessment | None
    action_proposal: ActionProposal | None
    routes: list[dict]
    audit_log: list[dict]
    
    # Orchestration control
    next_step: str
