export type EventType = "heat" | "possible_fire" | "smoke_report" | "road_block" | "medical_risk";
export type DataMode = "live" | "cached" | "simulated" | "unavailable" | "error";
export type IncidentStatus = 
  | "received"
  | "verifying"
  | "monitoring"
  | "planning"
  | "awaiting_approval"
  | "active"
  | "replanning"
  | "resolved";
export type ApprovalStatus = "not_required" | "pending" | "approved" | "modified" | "rejected" | "escalated";

export interface LocationContext {
  latitude: number;
  longitude: number;
  address: string | null;
  source: string;
  timestamp: string;
}

export interface Observation {
  observation_id: string;
  source: string;
  data_mode: DataMode;
  event_type: EventType;
  location: LocationContext;
  observed_at: string;
  received_at: string;
  value: Record<string, any>;
  confidence: number;
  raw_payload?: Record<string, any> | null;
}

export interface NormalizedEvent {
  event_id: string;
  event_type: EventType;
  location: LocationContext;
  status: string;
  confidence: number;
  value: Record<string, any>;
  supporting_observations: string[];
}

export interface RiskAssessment {
  score: number;
  severity: string;
  exposure: number;
  priority: string;
  reasoning: string[];
}

export interface ActionProposal {
  actions: Array<Record<string, any>>;
  status: string;
  reasoning: string[];
  approval_status: ApprovalStatus;
  approved_by: string | null;
  approved_at: string | null;
}

export interface IncidentState {
  incident_id: string;
  status: IncidentStatus;
  observations: Observation[];
  events: NormalizedEvent[];
  risk: RiskAssessment | null;
  action_proposal: ActionProposal | null;
  routes: Array<Record<string, any>>;
  audit_log: Array<{
    timestamp: string;
    event_type: string;
    message: string;
    payload?: Record<string, any> | null;
  }>;
}
