from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class EventType(str, Enum):
    HEAT = "heat"
    POSSIBLE_FIRE = "possible_fire"
    SMOKE_REPORT = "smoke_report"
    ROAD_BLOCK = "road_block"
    MEDICAL_RISK = "medical_risk"


class DataMode(str, Enum):
    LIVE = "live"
    CACHED = "cached"
    SIMULATED = "simulated"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class IncidentStatus(str, Enum):
    RECEIVED = "received"
    VERIFYING = "verifying"
    MONITORING = "monitoring"
    PLANNING = "planning"
    AWAITING_APPROVAL = "awaiting_approval"
    ACTIVE = "active"
    REPLANNING = "replanning"
    RESOLVED = "resolved"


class ApprovalStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    MODIFIED = "modified"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class LocationContext(BaseModel):
    latitude: float
    longitude: float
    address: str | None = None
    source: str
    timestamp: datetime


class Observation(BaseModel):
    observation_id: str
    source: str
    data_mode: DataMode
    event_type: EventType
    location: LocationContext
    observed_at: datetime
    received_at: datetime
    value: dict
    confidence: float
    raw_payload: dict | None = None


class NormalizedEvent(BaseModel):
    event_id: str
    event_type: EventType
    location: LocationContext
    status: str
    confidence: float
    value: dict
    supporting_observations: list[str] = Field(default_factory=list)
    web_verification: dict | None = None   # DuckDuckGo web corroboration
    false_alarm_report: dict | None = None  # Law enforcement report


class RiskAssessment(BaseModel):
    score: float
    severity: str
    exposure: float
    priority: str
    reasoning: list[str] = Field(default_factory=list)


class ActionProposal(BaseModel):
    actions: list[dict] = Field(default_factory=list)
    status: str
    reasoning: list[str] = Field(default_factory=list)
    approval_status: ApprovalStatus
    approved_by: str | None = None
    approved_at: datetime | None = None


class IncidentState(BaseModel):
    incident_id: str
    status: IncidentStatus
    observations: list[Observation] = Field(default_factory=list)
    events: list[NormalizedEvent] = Field(default_factory=list)
    risk: RiskAssessment | None = None
    action_proposal: ActionProposal | None = None
    routes: list[dict] = Field(default_factory=list)
    audit_log: list[dict] = Field(default_factory=list)
