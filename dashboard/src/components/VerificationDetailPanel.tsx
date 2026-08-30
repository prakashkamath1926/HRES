/**
 * VerificationDetailPanel — Shows per-event evidence including:
 * - Sensor confidence with color-coded bar
 * - 🌐 Web verification tool results (DuckDuckGo)
 * - Clickable source links
 * - ⚖️ False alarm / law enforcement report
 */
import React, { useMemo } from "react";
import { IncidentState } from "../types/incident";

interface Props { incident: IncidentState | null; }

const EVENT_CFG: Record<string, { label: string; icon: string; color: string }> = {
  heat:          { label: "Heat",          icon: "🌡️", color: "#f59e0b" },
  possible_fire: { label: "Possible Fire", icon: "🔥", color: "#ef4444" },
  road_block:    { label: "Road Block",    icon: "🚧", color: "#f97316" },
  smoke_report:  { label: "Smoke Report",  icon: "💨", color: "#8b5cf6" },
};

const STATUS_CFG: Record<string, { color: string; bg: string; label: string }> = {
  verified:   { color: "#10b981", bg: "rgba(16,185,129,0.1)",  label: "✅ Verified"   },
  likely:     { color: "#f59e0b", bg: "rgba(245,158,11,0.1)",  label: "⚠️ Likely"    },
  possible:   { color: "#f97316", bg: "rgba(249,115,22,0.1)",  label: "🔶 Possible"  },
  unverified: { color: "#6b7280", bg: "rgba(107,114,128,0.1)", label: "❓ Unverified" },
  active:     { color: "#ef4444", bg: "rgba(239,68,68,0.1)",   label: "🔴 Active"    },
};

function confColor(c: number) { return c >= 0.75 ? "#10b981" : c >= 0.5 ? "#f59e0b" : "#ef4444"; }

function fmtValue(evt: any): string {
  const v = evt.value;
  if (!v) return "—";
  if (v.temperature != null) return `${Number(v.temperature).toFixed(1)}°C`;
  if (v.smoke_detected) return v.extreme_heat_confirmed ? "Smoke + Extreme Heat" : "Smoke Reported";
  if (v.blocked != null) return v.blocked ? "Blocked" : "Clear";
  return JSON.stringify(v).slice(0, 40);
}

export const VerificationDetailPanel: React.FC<Props> = React.memo(({ incident }) => {
  const events = incident?.events || [];
  const obs = incident?.observations || [];

  const enriched = useMemo(() =>
    events.map(evt => ({
      evt,
      sources: obs.filter(o => o.event_type === evt.event_type),
      webVerify: (evt as any).web_verification as any | null,
      falseAlarm: (evt as any).false_alarm_report as any | null,
    })),
    [events, obs]
  );

  if (enriched.length === 0) {
    return (
      <div className="card">
        <div className="panel-title"><span className="panel-title-icon">🔍</span>Verification Evidence</div>
        <p className="text-muted text-sm" style={{ padding: "16px 0" }}>
          No events yet. Awaiting observations from data sources.
        </p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="panel-title">
        <span className="panel-title-icon">🔍</span>
        Verification Evidence
        <span style={{ marginLeft: "auto", fontSize: 10, color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
          {enriched.length} event{enriched.length !== 1 ? "s" : ""}
        </span>
      </div>

      <div className="verification-events">
        {enriched.map(({ evt, sources, webVerify, falseAlarm }) => {
          const cfg = EVENT_CFG[evt.event_type] || { label: evt.event_type, icon: "📊", color: "#3b82f6" };
          const ss = STATUS_CFG[evt.status] || STATUS_CFG.unverified;
          const conf = evt.confidence ?? 0;

          return (
            <div key={evt.event_id} className="event-card" style={{ borderColor: `${cfg.color}22` }}>
              {/* Header */}
              <div className="event-card-header">
                <div className="event-type-badge" style={{ color: cfg.color }}>{cfg.icon} {cfg.label}</div>
                <span className="event-status-pill"
                  style={{ color: ss.color, background: ss.bg, borderColor: `${ss.color}44` }}>
                  {ss.label}
                </span>
              </div>

              {/* Value */}
              <div className="event-value-row">
                <span className="event-value-num" style={{ color: cfg.color }}>{fmtValue(evt)}</span>
              </div>

              {/* Confidence bar */}
              <div className="confidence-row" style={{ marginTop: 8 }}>
                <span className="confidence-label">Confidence</span>
                <div className="confidence-track">
                  <div className="confidence-fill"
                    style={{ width: `${(conf * 100).toFixed(0)}%`, background: confColor(conf) }} />
                </div>
                <span className="confidence-num" style={{ color: confColor(conf) }}>
                  {(conf * 100).toFixed(0)}%
                </span>
              </div>

              {/* Sensor sources */}
              {sources.length > 0 && (
                <div style={{ marginTop: 8, display: "flex", flexWrap: "wrap", gap: 4 }}>
                  {sources.map(s => (
                    <span key={s.observation_id} style={{
                      fontSize: 10, padding: "2px 7px", borderRadius: 99,
                      border: "1px solid var(--border-dim)", color: "var(--text-muted)",
                      display: "flex", alignItems: "center", gap: 3,
                    }}>
                      <span style={{
                        width: 5, height: 5, borderRadius: "50%", display: "inline-block",
                        background: s.data_mode === "live" ? "#10b981" : s.data_mode === "simulated" ? "#f97316" : "#3b82f6",
                      }} />
                      {s.source}
                    </span>
                  ))}
                </div>
              )}

              {/* 🌐 Web Verification Block */}
              {webVerify && (
                <div style={{
                  marginTop: 10, padding: "8px 10px", borderRadius: 8,
                  background: webVerify.corroborated ? "rgba(16,185,129,0.06)" : "rgba(107,114,128,0.06)",
                  border: `1px solid ${webVerify.corroborated ? "rgba(16,185,129,0.2)" : "rgba(107,114,128,0.2)"}`,
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
                    <span style={{ fontSize: 11, fontWeight: 600, color: webVerify.corroborated ? "#10b981" : "#6b7280" }}>
                      🌐 {webVerify.corroborated ? "Web Corroborated" : "Web Search"}
                    </span>
                    {webVerify.corroborated
                      ? <span style={{ fontSize: 9, color: "#10b981", background: "rgba(16,185,129,0.1)", padding: "1px 6px", borderRadius: 99, border: "1px solid rgba(16,185,129,0.3)" }}>
                          +{Math.round(webVerify.confidence_boost * 100)}% boost
                        </span>
                      : webVerify.false_alarm_risk
                        ? <span style={{ fontSize: 9, color: "#f97316", background: "rgba(249,115,22,0.1)", padding: "1px 6px", borderRadius: 99, border: "1px solid rgba(249,115,22,0.3)" }}>
                            ⚠️ False alarm risk
                          </span>
                        : null
                    }
                  </div>
                  <p style={{ fontSize: 10, color: "var(--text-muted)", margin: 0, lineHeight: 1.4 }}>
                    {webVerify.summary}
                  </p>
                  {webVerify.query && (
                    <p style={{ fontSize: 9, color: "#4d6080", margin: "3px 0 0", fontFamily: "var(--font-mono)" }}>
                      Query: "{webVerify.query}"
                    </p>
                  )}
                  {webVerify.sources?.length > 0 && (
                    <div style={{ marginTop: 6, display: "flex", gap: 5, flexWrap: "wrap" }}>
                      {webVerify.sources.map((src: any, i: number) => (
                        <a key={i} href={src.url || "#"} target="_blank" rel="noreferrer"
                          style={{ fontSize: 9, padding: "2px 7px", borderRadius: 99,
                            background: "rgba(59,130,246,0.1)", border: "1px solid rgba(59,130,246,0.25)",
                            color: "#3b82f6", textDecoration: "none" }}>
                          🔗 {src.source || `Source ${i + 1}`}
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* ⚖️ False Alarm Report */}
              {falseAlarm && (
                <div style={{
                  marginTop: 8, padding: "7px 10px", borderRadius: 8,
                  background: "rgba(239,68,68,0.06)", border: "1px solid rgba(239,68,68,0.25)",
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span style={{ fontSize: 12 }}>⚖️</span>
                    <span style={{ fontSize: 11, fontWeight: 600, color: "#ef4444" }}>False Alarm Report Filed</span>
                    <span style={{ fontSize: 9, marginLeft: "auto", color: "#6b7280" }}>{falseAlarm.status}</span>
                  </div>
                  <p style={{ fontSize: 10, color: "#fca5a5", margin: "4px 0 0", lineHeight: 1.4 }}>
                    {falseAlarm.law_enforcement_note}
                  </p>
                  <p style={{ fontSize: 9, color: "#6b7280", margin: "3px 0 0" }}>
                    Est. resources wasted: {falseAlarm.estimated_resources_wasted}
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
});

VerificationDetailPanel.displayName = "VerificationDetailPanel";
