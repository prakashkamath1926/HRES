import React from "react";

interface SimulationConsoleProps {
  triggerScenario: (scenario: string) => Promise<void>;
}

const SCENARIOS = [
  {
    key: "normal_conditions",
    label: "Normal Conditions",
    desc: "Baseline heat monitoring (32°C)",
    cls: "normal",
    icon: "🟢",
  },
  {
    key: "heat_escalation",
    label: "Escalate Heat",
    desc: "Inject extreme heat anomaly (48°C)",
    cls: "escalate",
    icon: "🌡️",
  },
  {
    key: "smoke_report",
    label: "Smoke Report",
    desc: "Crowdsourced smoke near campus dorms",
    cls: "smoke",
    icon: "🔥",
  },
  {
    key: "road_blockage",
    label: "Block Main Route",
    desc: "Main gate blocked — triggers replan",
    cls: "blockage",
    icon: "🚧",
  },
];

export const SimulationConsole: React.FC<SimulationConsoleProps> = ({ triggerScenario }) => {
  return (
    <div className="card">
      <div className="panel-title">
        <span className="panel-title-icon">🎛️</span>
        Demo Simulation Console
      </div>
      <p className="text-xs text-muted" style={{ marginBottom: 12 }}>
        Inject environmental anomalies to drive real-time agent verification, risk escalation, and LangGraph routing decisions.
      </p>

      <div className="sim-grid">
        {SCENARIOS.map(sc => (
          <button
            key={sc.key}
            className={`btn-sim ${sc.cls}`}
            onClick={() => triggerScenario(sc.key)}
          >
            <span className="sim-btn-label">{sc.icon} {sc.label}</span>
            <span className="sim-btn-desc">{sc.desc}</span>
          </button>
        ))}
        <button className="btn-sim reset" onClick={() => triggerScenario("reset")}>
          <span className="sim-btn-label">↺ Reset Scenario</span>
          <span className="sim-btn-desc">Resolve incident, wipe context, start fresh</span>
        </button>
      </div>
    </div>
  );
};
