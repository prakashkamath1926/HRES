import React from "react";
import { IncidentState } from "../types/incident";

interface SourceGridProps {
  incident: IncidentState | null;
}

const MODE_STYLES: Record<string, { color: string; label: string }> = {
  live:        { color: "#10b981", label: "LIVE" },
  cached:      { color: "#3b82f6", label: "CACHED" },
  simulated:   { color: "#f97316", label: "SIMULATED" },
  unavailable: { color: "#4d6080", label: "UNAVAIL" },
  error:       { color: "#ef4444", label: "ERROR" },
  available:   { color: "#8b5cf6", label: "ACTIVE" },
};

const SOURCES = [
  { name: "FortyGuard",   desc: "High-res temperature heatmap API",  icon: "🌡️" },
  { name: "Open-Meteo",   desc: "Live regional weather (free API)",   icon: "☁️" },
  { name: "User Report",  desc: "Crowdsourced incident inputs",       icon: "👤" },
  { name: "Maps",         desc: "Routing & access telemetry",         icon: "🗺️" },
  { name: "HRES Agent",   desc: "AI guidance synthesis",              icon: "🤖" },
];

export const SourceGrid: React.FC<SourceGridProps> = ({ incident }) => {
  const obs = incident?.observations || [];

  const getSourceInfo = (name: string) => {
    if (name === "HRES Agent") {
      const active = incident?.action_proposal ? "available" : "unavailable";
      return { mode: active, icon: "✓", conf: incident?.action_proposal ? 1.0 : null };
    }
    if (name === "Maps") {
      const active = incident?.routes && incident.routes.length > 0 ? "live" : "unavailable";
      return { mode: active, icon: "✓", conf: incident?.routes?.length ? 1.0 : null };
    }
    if (name === "User Report") {
      const hasReports = incident?.events?.some(e => e.false_alarm_report || e.status === "likely");
      return { mode: hasReports ? "live" : "unavailable", icon: "✓", conf: hasReports ? 0.9 : null };
    }

    const matching = obs.filter(o => o.source.toLowerCase() === name.toLowerCase());
    if (matching.length === 0) {
      return { mode: "unavailable", icon: "—", conf: null };
    }
    const latest = matching.reduce((a, b) =>
      new Date(a.observed_at) > new Date(b.observed_at) ? a : b
    );
    return {
      mode: latest.data_mode,
      icon: "✓",
      conf: latest.confidence,
    };
  };

  return (
    <div className="card">
      <div className="panel-title">
        <span className="panel-title-icon">📡</span>
        Source Verification Status
      </div>
      <table className="sources-table">
        <thead>
          <tr>
            <th>Source</th>
            <th style={{ textAlign: "center" }}>Status</th>
            <th style={{ textAlign: "center" }}>Mode</th>
            <th style={{ textAlign: "right" }}>Confidence</th>
          </tr>
        </thead>
        <tbody>
          {SOURCES.map(src => {
            const info = getSourceInfo(src.name);
            const style = MODE_STYLES[info.mode] || MODE_STYLES.unavailable;
            const hasData = info.mode !== "unavailable";
            return (
              <tr key={src.name}>
                <td>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ fontSize: 14 }}>{src.icon}</span>
                    <div>
                      <div className="source-name">{src.name}</div>
                      <div className="source-desc">{src.desc}</div>
                    </div>
                  </div>
                </td>
                <td className="source-status-icon">
                  <span style={{ color: style.color, fontSize: 14, fontWeight: 600 }}>
                    {hasData ? "✓" : "—"}
                  </span>
                </td>
                <td style={{ textAlign: "center" }}>
                  <span
                    className="mode-tag"
                    style={{ color: style.color, borderColor: `${style.color}44`, background: `${style.color}10` }}
                  >
                    {style.label}
                  </span>
                </td>
                <td>
                  {info.conf !== null ? (
                    <div className="confidence-bar-wrap" style={{ alignItems: "flex-end" }}>
                      <div className="confidence-bar-bg" style={{ marginLeft: "auto" }}>
                        <div
                          className="confidence-bar-fill"
                          style={{ width: `${(info.conf * 100).toFixed(0)}%`, background: style.color }}
                        />
                      </div>
                      <span className="confidence-pct" style={{ color: style.color }}>
                        {(info.conf * 100).toFixed(0)}%
                      </span>
                    </div>
                  ) : (
                    <span className="text-xs text-muted" style={{ float: "right" }}>—</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
