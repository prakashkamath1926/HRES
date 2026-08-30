import React, { useState } from "react";
import { IncidentState } from "../types/incident";

interface ReportCenterProps {
  incident: IncidentState | null;
  handleResolve: () => Promise<void>;
}

export const ReportCenter: React.FC<ReportCenterProps> = ({ incident, handleResolve }) => {
  const [downloading, setDownloading] = useState(false);

  const handleDownloadAAR = async () => {
    if (!incident) return;
    setDownloading(true);
    try {
      // Correct URL: /api/incidents/{id}/aar (not /api/reports/)
      const res = await fetch(`/api/incidents/${incident.incident_id}/aar`);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "AAR not available. Resolve the incident first.");
      }
      const contentType = res.headers.get("content-type") || "";
      const isHtml = contentType.includes("text/html");
      const extension = isHtml ? "html" : "pdf";
      
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `HRES_AAR_${incident.incident_id}.${extension}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e: any) {
      alert(e.message || "Failed to download AAR. Resolve the incident first.");
    } finally {
      setDownloading(false);
    }
  };

  const isActive = incident && incident.status !== "resolved";
  const isResolved = incident?.status === "resolved";

  return (
    <div className="card">
      <div className="panel-title">
        <span className="panel-title-icon">📄</span>
        Incident Control
      </div>

      <div style={{ marginBottom: 12, fontSize: 12, color: "var(--text-muted)", lineHeight: 1.5 }}>
        {isResolved ? (
          <span style={{ color: "var(--color-success)" }}>✓ Incident resolved. After-Action Report available.</span>
        ) : (
          "Resolve the incident to archive it and generate the After-Action Report (AAR)."
        )}
      </div>

      <div className="report-actions">
        <button
          className="btn-action resolve"
          onClick={handleResolve}
          disabled={!isActive}
          title="Mark this incident as resolved"
        >
          ✕ Resolve Incident
        </button>

        <button
          className="btn-action"
          onClick={handleDownloadAAR}
          disabled={downloading || !incident}
          title="Download After-Action Report PDF"
        >
          {downloading ? "⟳ Generating…" : "↓ Download AAR"}
        </button>
      </div>

      {incident && (
        <div style={{ marginTop: 14, paddingTop: 14, borderTop: "1px solid var(--border-dim)" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            <div>
              <div style={{ fontSize: 9, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 2 }}>Events</div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 18, fontWeight: 700, color: "var(--text-primary)" }}>
                {incident.events?.length ?? 0}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 9, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 2 }}>Observations</div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 18, fontWeight: 700, color: "var(--text-primary)" }}>
                {incident.observations?.length ?? 0}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 9, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 2 }}>Audit Log</div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 18, fontWeight: 700, color: "var(--text-primary)" }}>
                {incident.audit_log?.length ?? 0}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 9, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 2 }}>Status</div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 13, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase" }}>
                {incident.status?.replace(/_/g, " ") || "—"}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
