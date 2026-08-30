/**
 * AgentStatusPanel — DESIGN.md Section 10
 * Shows operational status of each agent/pipeline stage derived from incident state.
 */
import React from "react";
import { IncidentState } from "../types/incident";

interface AgentStatusPanelProps {
  incident: IncidentState | null;
}

type AgentStatus = "done" | "active" | "waiting" | "pending" | "required";

interface AgentDef {
  key: string;
  name: string;
  icon: string;
  getStatus: (incident: IncidentState | null) => AgentStatus;
  getNote?: (incident: IncidentState | null) => string;
}

const AGENTS: AgentDef[] = [
  {
    key: "perception",
    name: "Perception",
    icon: "📡",
    getStatus: (inc) => {
      if (!inc) return "pending";
      return inc.observations && inc.observations.length > 0 ? "done" : "active";
    },
    getNote: (inc) => inc?.observations?.length ? `${inc.observations.length} obs` : "Awaiting",
  },
  {
    key: "verification",
    name: "Verification",
    icon: "🔍",
    getStatus: (inc) => {
      if (!inc) return "pending";
      if (!inc.observations?.length) return "pending";
      if (inc.events?.length > 0) return "done";
      return "active";
    },
    getNote: (inc) => inc?.events?.length ? `${inc.events.length} events` : "Pending",
  },
  {
    key: "risk",
    name: "Risk Assessment",
    icon: "⚡",
    getStatus: (inc) => {
      if (!inc) return "pending";
      if (!inc.events?.length) return "pending";
      return inc.risk ? "done" : "active";
    },
    getNote: (inc) => inc?.risk ? inc.risk.severity : "Pending",
  },
  {
    key: "supervisor",
    name: "Supervisor",
    icon: "🧭",
    getStatus: (inc) => {
      if (!inc || !inc.risk) return "pending";
      if (inc.status === "planning") return "active";
      if (inc.status === "replanning") return "active";
      if (["monitoring", "awaiting_approval", "active"].includes(inc.status || "")) return "done";
      return "waiting";
    },
    getNote: (inc) => {
      if (!inc) return "—";
      if (inc.status === "replanning") return "Replanning";
      if (inc.status === "planning") return "Planning";
      if (inc.status === "monitoring") return "Monitoring";
      return inc.status?.replace(/_/g, " ") || "—";
    },
  },
  {
    key: "response",
    name: "Response Agent",
    icon: "🚒",
    getStatus: (inc) => {
      if (!inc) return "pending";
      const hasRes = inc.action_proposal?.actions?.some(a => a.type === "responder_guidance");
      if (hasRes) return "done";
      if (inc.risk?.severity === "CRITICAL" && inc.status === "planning") return "active";
      return "pending";
    },
    getNote: (inc) => {
      const hasRes = inc?.action_proposal?.actions?.some(a => a.type === "responder_guidance");
      return hasRes ? "Ready" : "Standby";
    },
  },
  {
    key: "civilian",
    name: "Civilian Agent",
    icon: "👥",
    getStatus: (inc) => {
      if (!inc) return "pending";
      const hasAlert = inc.action_proposal?.actions?.some(a => a.type === "civilian_alert");
      if (hasAlert) return "done";
      if (["HIGH", "CRITICAL"].includes(inc.risk?.severity || "") && inc.status === "planning") return "active";
      return "pending";
    },
    getNote: (inc) => {
      const hasAlert = inc?.action_proposal?.actions?.some(a => a.type === "civilian_alert");
      return hasAlert ? "Alert Ready" : "Standby";
    },
  },
  {
    key: "civic",
    name: "Civic Agent",
    icon: "🏛️",
    getStatus: (inc) => {
      if (!inc) return "pending";
      const hasCivic = inc.action_proposal?.actions?.some(a => a.type === "civic_report");
      if (hasCivic) return "done";
      return "pending";
    },
    getNote: (inc) => {
      const hasCivic = inc?.action_proposal?.actions?.some(a => a.type === "civic_report");
      return hasCivic ? "Report Ready" : "Standby";
    },
  },
  {
    key: "approval",
    name: "Approval Gate",
    icon: "🛡️",
    getStatus: (inc) => {
      if (!inc || !inc.action_proposal) return "pending";
      const s = inc.action_proposal.approval_status;
      if (s === "approved") return "done";
      if (s === "pending") return inc.status === "awaiting_approval" ? "required" : "waiting";
      if (s === "not_required") return "done";
      return "pending";
    },
    getNote: (inc) => {
      const s = inc?.action_proposal?.approval_status;
      if (!s || s === "not_required") return "Not Required";
      return s.replace(/_/g, " ").toUpperCase();
    },
  },
];

const STATUS_LABELS: Record<AgentStatus, string> = {
  done:     "✓  Complete",
  active:   "●  Active",
  waiting:  "◌  Waiting",
  pending:  "—  Standby",
  required: "⏳  Required",
};

export const AgentStatusPanel: React.FC<AgentStatusPanelProps> = ({ incident }) => {
  return (
    <div className="card">
      <div className="panel-title">
        <span className="panel-title-icon">🤖</span>
        Agent Pipeline Status
      </div>
      <div className="agent-status-list">
        {AGENTS.map(agent => {
          const status = agent.getStatus(incident);
          const note = agent.getNote?.(incident);
          return (
            <div key={agent.key} className="agent-row">
              <div className="agent-name">
                <span className="agent-icon">{agent.icon}</span>
                {agent.name}
                {note && (
                  <span style={{ fontSize: 10, color: "var(--text-muted)", marginLeft: 4 }}>
                    · {note}
                  </span>
                )}
              </div>
              <span className={`agent-status-badge ${status}`}>
                {STATUS_LABELS[status]}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
