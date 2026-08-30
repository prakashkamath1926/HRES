import React from "react";
import { IncidentState } from "../types/incident";

interface RiskIndicatorProps {
  incident: IncidentState | null;
}

const SEVERITY_CONFIG = {
  LOW:      { color: "#10b981", glow: "rgba(16,185,129,0.15)", label: "LOW RISK",       desc: "Environmental conditions within safe parameters." },
  MODERATE: { color: "#3b82f6", glow: "rgba(59,130,246,0.15)",  label: "MODERATE RISK",  desc: "Precautionary monitoring escalated. Avoid prolonged exposure." },
  HIGH:     { color: "#f59e0b", glow: "rgba(245,158,11,0.18)",  label: "HIGH RISK",      desc: "Active warning. Safety protocols recommended immediately." },
  CRITICAL: { color: "#ef4444", glow: "rgba(239,68,68,0.22)",   label: "CRITICAL ALERT", desc: "Emergency response workflow activated. Evacuate if advised." },
};

function formatAge(isoStr?: string): string {
  if (!isoStr) return "—";
  const diff = Math.floor((Date.now() - new Date(isoStr).getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

export const RiskIndicator: React.FC<RiskIndicatorProps> = ({ incident }) => {
  const risk = incident?.risk;
  const severity = (risk?.severity ?? "LOW") as keyof typeof SEVERITY_CONFIG;
  const cfg = SEVERITY_CONFIG[severity] || SEVERITY_CONFIG.LOW;
  const score = risk?.score ?? 0;

  // Temperature from heat event
  const heatEvt = incident?.events?.find(e => e.event_type === "heat");
  const temp = heatEvt?.value?.temperature ?? null;
  const confidence = heatEvt?.confidence ?? null;

  // Freshness from latest observation
  const lastObs = incident?.observations?.[incident.observations.length - 1];
  const freshLabel = formatAge(lastObs?.observed_at);

  // SVG gauge
  const R = 36, C = 2 * Math.PI * R;
  const dashOffset = C - (C * score) / 100;

  return (
    <div className="card risk-card" style={{ boxShadow: `0 0 30px ${cfg.glow}`, borderColor: `${cfg.color}33` }}>
      <div className="panel-title">
        <span className="panel-title-icon">⚡</span>
        Operations Priority Console
      </div>

      <div className="risk-severity-row">
        {/* Gauge */}
        <div className="risk-gauge-wrap">
          <svg viewBox="0 0 90 90" style={{ transform: "rotate(-90deg)" }}>
            <circle cx="45" cy="45" r={R} fill="none" stroke="rgba(56,89,140,0.25)" strokeWidth="7" />
            <circle
              cx="45" cy="45" r={R}
              fill="none"
              stroke={cfg.color}
              strokeWidth="7"
              strokeDasharray={C}
              strokeDashoffset={dashOffset}
              strokeLinecap="round"
              style={{ transition: "stroke-dashoffset 0.8s cubic-bezier(0.4,0,0.2,1), stroke 0.4s" }}
            />
          </svg>
          <div className="gauge-center-label">
            <span className="gauge-score tabular" style={{ color: cfg.color }}>{Math.round(score)}</span>
            <span className="gauge-unit">SCORE</span>
          </div>
        </div>

        {/* Info */}
        <div className="risk-info">
          <div className="risk-severity-label" style={{ color: cfg.color }}>
            {cfg.label}
          </div>
          <p className="risk-desc">{cfg.desc}</p>

          <div className="risk-metrics-row">
            {temp !== null && (
              <div className="metric-chip">
                <span className="metric-chip-label">Temperature</span>
                <span className="metric-chip-value tabular" style={{ color: cfg.color }}>
                  {temp.toFixed(1)}°C
                </span>
              </div>
            )}
            {confidence !== null && (
              <div className="metric-chip">
                <span className="metric-chip-label">Confidence</span>
                <span className="metric-chip-value tabular">{(confidence * 100).toFixed(0)}%</span>
              </div>
            )}
            {risk?.exposure !== undefined && (
              <div className="metric-chip">
                <span className="metric-chip-label">Exposure</span>
                <span className="metric-chip-value tabular">{risk.exposure.toFixed(0)}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Freshness */}
      <div className="freshness-row">
        <div className="freshness-dot" style={{ background: lastObs ? cfg.color : "#4d6080" }} />
        <span className="freshness-text">Last observation: {freshLabel}</span>
        {lastObs && (
          <span className="freshness-text" style={{ marginLeft: "auto" }}>
            via {lastObs.source}
          </span>
        )}
      </div>

      {/* Reasoning */}
      {risk?.reasoning && risk.reasoning.length > 0 && (
        <div className="reasoning-section">
          <span className="reasoning-title">Assessment Rationale</span>
          <ul className="reasoning-list">
            {risk.reasoning.slice(0, 4).map((r, i) => (
              <li key={i} className="reasoning-item">{r}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
