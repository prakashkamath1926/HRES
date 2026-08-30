import React, { useState, useCallback } from "react";
import { useAuth } from "./hooks/useAuth";
import { useIncident } from "./hooks/useIncident";
import { useAlerts } from "./hooks/useAlerts";
import { Header } from "./components/Header";
import { RiskIndicator } from "./components/RiskIndicator";
import { SourceGrid } from "./components/SourceGrid";
import { VerificationDetailPanel } from "./components/VerificationDetailPanel";
import { AgentStatusPanel } from "./components/AgentStatusPanel";
import { ApprovalPanel } from "./components/ApprovalPanel";
import { AuditTimeline } from "./components/AuditTimeline";
import { SimulationConsole } from "./components/SimulationConsole";
import { MapPanel } from "./components/MapPanel";
import { ReportCenter } from "./components/ReportCenter";
import { ChatPanel } from "./components/ChatPanel";

const App: React.FC = () => {
  const { user } = useAuth();
  const {
    incident,
    loading,
    error,
    refresh,
    triggerScenario,
    changeLocation,
    submitDecision,
    handleResolve,
  } = useIncident();

  const [alertsMuted, setAlertsMuted] = useState(false);

  // Alert engine — sound + voice + browser notifications
  useAlerts(incident, { muted: alertsMuted });

  const handleLocationChange = useCallback((lat: number, lon: number, address?: string) => {
    changeLocation(lat, lon, address);
  }, [changeLocation]);

  const isReplanning = incident?.status === "replanning";
  const isCritical = incident?.risk?.severity === "CRITICAL";

  return (
    <div className="dashboard-root">
      {/* ── Sticky Header ──────────────────────────── */}
      <Header incident={incident} onLocationChange={handleLocationChange} />

      {/* ── System Banners ─────────────────────────── */}
      {error && (
        <div className="error-banner">
          <span>⚠</span>
          <span><strong>Operational Error:</strong> {error}</span>
          <button className="error-retry-btn" onClick={() => refresh()}>Retry</button>
        </div>
      )}

      {isReplanning && (
        <div className="replan-banner">
          <div className="replan-spinner" />
          <div>
            <strong>CONDITIONS CHANGED</strong> — HRES Supervisor is generating an updated response plan.
          </div>
        </div>
      )}

      {/* ── Critical Alert Banner ───────────────────── */}
      {isCritical && (
        <div style={{
          margin: "0 16px 0",
          padding: "10px 16px",
          background: "rgba(239,68,68,0.1)",
          border: "1px solid rgba(239,68,68,0.4)",
          borderRadius: 10,
          display: "flex",
          alignItems: "center",
          gap: 12,
          fontSize: 12,
          color: "#fca5a5",
          animation: "slide-in 0.3s ease",
        }}>
          <span style={{ fontSize: 18 }}>🚨</span>
          <span>
            <strong style={{ color: "#ef4444" }}>CRITICAL ALERT ACTIVE</strong> — Emergency response plan is being generated.
            Voice alerts and browser notifications are active.
          </span>
          <button
            onClick={() => setAlertsMuted(m => !m)}
            style={{
              marginLeft: "auto",
              padding: "4px 10px",
              borderRadius: 6,
              border: "1px solid rgba(239,68,68,0.4)",
              background: "transparent",
              color: alertsMuted ? "#4d6080" : "#ef4444",
              fontSize: 11,
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            {alertsMuted ? "🔇 Unmute Alerts" : "🔊 Mute Alerts"}
          </button>
        </div>
      )}

      {/* ── Main Grid ──────────────────────────────── */}
      <main id="main-content" className="dashboard-body">
        {/* Left Column */}
        <div className="col-left">
          <MapPanel incident={incident} />
          <SimulationConsole triggerScenario={triggerScenario} />
          <VerificationDetailPanel incident={incident} />
          {user?.role !== "civilian" && (
            <ReportCenter incident={incident} handleResolve={handleResolve} />
          )}
        </div>

        {/* Right Column */}
        <div className="col-right">
          <RiskIndicator incident={incident} />
          <SourceGrid incident={incident} />
          <AgentStatusPanel incident={incident} />
          {user?.role !== "civilian" && (
            <ApprovalPanel incident={incident} submitDecision={submitDecision} />
          )}
          <AuditTimeline incident={incident} />
        </div>
      </main>

      {/* ── Floating HRES Agent Chatbot ─────────────── */}
      <ChatPanel />
    </div>
  );
};

export default App;
