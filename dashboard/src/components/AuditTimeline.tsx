import React, { useMemo } from "react";
import { IncidentState } from "../types/incident";

interface AuditTimelineProps {
  incident: IncidentState | null;
}

const EVENT_COLORS: Record<string, string> = {
  INCIDENT_CREATED:           "#10b981",
  LOCATION_UPDATED:           "#3b82f6",
  OBSERVATION_RECEIVED:       "#22d3ee",
  SUPERVISOR_ROUTING:         "#8b5cf6",
  GRAPH_ERROR:                "#ef4444",
  OPERATOR_DECISION:          "#f59e0b",
  INCIDENT_RESOLVED:          "#4d6080",
  VERIFICATION_SENSOR:        "#22d3ee",
  VERIFICATION_SYNTHESIS:     "#10b981",
  TOOL_CALL_WEB_SEARCH:       "#8b5cf6",
  TOOL_RESULT_WEB_SEARCH:     "#3b82f6",
  FALSE_ALARM_FILED:          "#f97316",
  LAW_ENFORCEMENT_ESCALATION: "#ef4444",
  FORTYGUARD_API_SUBMITTED:   "#f59e0b",
  FORTYGUARD_API_COMPLETED:   "#10b981",
  FORTYGUARD_API_FAILED:      "#ef4444",
};

const EVENT_ICONS: Record<string, string> = {
  TOOL_CALL_WEB_SEARCH:       "🔍",
  TOOL_RESULT_WEB_SEARCH:     "🌐",
  FALSE_ALARM_FILED:          "⚖️",
  LAW_ENFORCEMENT_ESCALATION: "🚔",
  FORTYGUARD_API_SUBMITTED:   "📡",
  FORTYGUARD_API_COMPLETED:   "✅",
  FORTYGUARD_API_FAILED:      "❌",
  VERIFICATION_SYNTHESIS:     "🧠",
  SUPERVISOR_ROUTING:         "🔀",
  OPERATOR_DECISION:          "👤",
  GRAPH_ERROR:                "❌",
  INCIDENT_RESOLVED:          "✅",
};

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    return iso.slice(11, 19) || "—";
  }
}

// Memoized wrapper to prevent re-renders unless audit_log actually changes
export const AuditTimeline: React.FC<AuditTimelineProps> = React.memo(({ incident }) => {
  const log = incident?.audit_log || [];

  // useMemo: formatTime + sort only recalculate when log changes, not every parent render
  const sortedItems = useMemo(() => {
    return [...log]
      .reverse()
      .slice(0, 30)
      .map(entry => ({
        ...entry,
        displayTime: formatTime(entry.timestamp),
        dotColor: EVENT_COLORS[entry.event_type] || "#374151",
        icon: EVENT_ICONS[entry.event_type] ?? null,
        isTool: entry.event_type.startsWith("TOOL_"),
        isFalseAlarm: entry.event_type.includes("FALSE_ALARM") || entry.event_type.includes("LAW_ENFORCE"),
        sanitizedMessage: entry.message.replace(/\*\*(.*?)\*\*/g, '$1'),
      }));
  }, [log]);

  return (
    <div className="card">
      <div className="panel-title">
        <span className="panel-title-icon">📋</span>
        Audit Timeline
        {log.length > 0 && (
          <span style={{ marginLeft: "auto", fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
            {log.length} events
          </span>
        )}
      </div>

      {sortedItems.length === 0 ? (
        <p className="text-sm text-muted" style={{ padding: "8px 0" }}>No audit events recorded yet.</p>
      ) : (
        <div className="audit-timeline">
          {sortedItems.map((entry, idx) => (
            <div
              key={`${entry.timestamp}-${idx}`}
              className={`audit-entry${idx === 0 ? " recent" : ""}`}
              style={entry.isTool ? {
                background: "rgba(139,92,246,0.04)",
                borderLeft: `2px solid ${entry.dotColor}33`,
                paddingLeft: 8,
                marginLeft: -2,
              } : undefined}
            >
              <div className="audit-dot" style={{ background: entry.dotColor }} />
              <div className="audit-meta" style={{ flex: 1, minWidth: 0 }}>
                <span className="audit-event" style={{ color: entry.dotColor }}>
                  {entry.icon && <span style={{ marginRight: 3 }}>{entry.icon}</span>}
                  {entry.event_type.replace(/_/g, " ")}
                </span>
                <span className="audit-msg">{entry.sanitizedMessage}</span>

                {/* Show clickable web sources inline for tool results */}
                {entry.event_type === "TOOL_RESULT_WEB_SEARCH" && entry.payload?.sources?.length > 0 && (
                  <div style={{ marginTop: 3, display: "flex", gap: 5, flexWrap: "wrap" }}>
                    {entry.payload.sources.map((src: any, si: number) => (
                      src.url ? (
                        <a key={si} href={src.url} target="_blank" rel="noreferrer"
                          style={{ fontSize: 9, color: "#3b82f6", textDecoration: "underline" }}>
                          🔗 {src.source || `Source ${si + 1}`}
                        </a>
                      ) : (
                        <span key={si} style={{ fontSize: 9, color: "#4d6080" }}>{src.source || `Source ${si + 1}`}</span>
                      )
                    ))}
                  </div>
                )}

                {entry.isFalseAlarm && (
                  <span style={{ fontSize: 9, color: "#f97316", display: "block", marginTop: 2 }}>
                    Logged for law enforcement review
                  </span>
                )}
              </div>
              <span className="audit-time">{entry.displayTime}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
});

AuditTimeline.displayName = "AuditTimeline";
