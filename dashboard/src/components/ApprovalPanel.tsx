import React, { useState } from "react";
import { IncidentState } from "../types/incident";

interface ApprovalPanelProps {
  incident: IncidentState | null;
  submitDecision: (decision: string, comment?: string) => Promise<void>;
}

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  not_required: { label: "AUTONOMOUS",        color: "#10b981" },
  pending:      { label: "PENDING REVIEW",    color: "#f97316" },
  approved:     { label: "APPROVED",          color: "#10b981" },
  modified:     { label: "MODIFIED",          color: "#3b82f6" },
  rejected:     { label: "REJECTED",          color: "#ef4444" },
  escalated:    { label: "ESCALATED",         color: "#8b5cf6" },
};

export const ApprovalPanel: React.FC<ApprovalPanelProps> = ({ incident, submitDecision }) => {
  const proposal = incident?.action_proposal;
  const isAwaiting = incident?.status === "awaiting_approval";
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState<string | null>(null);

  if (!proposal) {
    return (
      <div className="card">
        <div className="panel-title">
          <span className="panel-title-icon">🛡️</span>
          Human-in-the-Loop Gate
        </div>
        <div className="approval-empty">
          <div className="shield-icon">🛡️</div>
          <p className="text-sm text-muted">
            No action proposals pending approval. System running in autonomous monitoring mode.
          </p>
        </div>
      </div>
    );
  }

  const cfg = STATUS_CONFIG[proposal.approval_status] || { label: "UNKNOWN", color: "#4d6080" };

  const handleAction = async (decision: string) => {
    setSubmitting(decision);
    try {
      await submitDecision(decision, comment || undefined);
      setComment("");
    } catch (err) {
      console.error("Approval submission failed:", err);
    } finally {
      setSubmitting(null);
    }
  };

  return (
    <div className="card" style={{ borderColor: isAwaiting ? `rgba(249,115,22,0.3)` : undefined }}>
      <div className="approval-header">
        <div>
          <div className="panel-title" style={{ marginBottom: 2 }}>
            <span className="panel-title-icon">🛡️</span>
            Human-in-the-Loop Gate
          </div>
          <p className="text-xs text-muted">Mandatory review before high-impact deployments.</p>
        </div>
        <span
          className="approval-status-tag"
          style={{ color: cfg.color, borderColor: `${cfg.color}44`, background: `${cfg.color}10` }}
        >
          {cfg.label}
        </span>
      </div>

      {/* Action proposals */}
      {proposal.actions && proposal.actions.length > 0 && (
        <div>
          <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 8 }}>
            Proposed Actions
          </div>
          <div className="actions-list">
            {proposal.actions.map((act, i) => (
              <div key={i} className="action-item">
                <span className={`action-type-tag ${act.type}`}>{act.type?.replace(/_/g, " ").toUpperCase()}</span>
                {act.title && <div className="action-title">{act.title}</div>}
                {act.type === "civilian_alert" && act.details && (
                  <>
                    {act.message && <div className="text-xs text-secondary" style={{ marginTop: 2 }}>{act.message}</div>}
                    {act.details.cooling_center && (
                      <div className="action-detail-line">
                        <span className="action-detail-key">❄️ Cooling Center:</span>
                        <span>{act.details.cooling_center}</span>
                      </div>
                    )}
                    {act.details.hospital && (
                      <div className="action-detail-line">
                        <span className="action-detail-key">🏥 Hospital:</span>
                        <span>{act.details.hospital}</span>
                      </div>
                    )}
                  </>
                )}
                {act.type === "responder_guidance" && act.details && (
                  <>
                    {act.details.primary_route && (
                      <div className="action-detail-line">
                        <span className="action-detail-key">🧭 Route:</span>
                        <span>{act.details.primary_route}</span>
                      </div>
                    )}
                    {act.details.alternate_route && (
                      <div className="action-detail-line">
                        <span className="action-detail-key">🔄 Alternate:</span>
                        <span>{act.details.alternate_route}</span>
                      </div>
                    )}
                  </>
                )}
                {act.type === "civic_report" && act.details?.summary && (
                  <div className="text-xs text-secondary" style={{ marginTop: 2 }}>{act.details.summary}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Reasoning */}
      {proposal.reasoning && proposal.reasoning.length > 0 && (
        <div style={{ marginTop: 8, marginBottom: 12 }}>
          <div style={{ fontSize: 10, color: "var(--text-muted)", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 600 }}>
            Agent Reasoning
          </div>
          {proposal.reasoning.slice(0, 3).map((r, i) => (
            <div key={i} style={{ fontSize: 11, color: "var(--text-muted)", paddingLeft: 12, position: "relative", lineHeight: 1.4, marginBottom: 3 }}>
              <span style={{ position: "absolute", left: 0, color: "var(--border-bright)" }}>›</span>
              {r}
            </div>
          ))}
        </div>
      )}

      {/* Operator controls */}
      {isAwaiting && (
        <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid var(--border-dim)" }}>
          <span className="operator-memo-label">Operator Memo (optional)</span>
          <textarea
            className="operator-textarea"
            placeholder="Enter operational remarks, override details, or escalation notes..."
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            disabled={submitting !== null}
          />
          <div className="approval-btn-grid">
            <button className="btn-approve" disabled={submitting !== null} onClick={() => handleAction("approved")}>
              {submitting === "approved" ? "⟳ Approving..." : "✓ Approve Dispatch"}
            </button>
            <button className="btn-modify" disabled={submitting !== null} onClick={() => handleAction("modified")}>
              {submitting === "modified" ? "⟳ Modifying..." : "✎ Modify Actions"}
            </button>
            <button className="btn-reject" disabled={submitting !== null} onClick={() => handleAction("rejected")}>
              {submitting === "rejected" ? "⟳ Rejecting..." : "✕ Reject / Cancel"}
            </button>
            <button className="btn-escalate" disabled={submitting !== null} onClick={() => handleAction("escalated")}>
              {submitting === "escalated" ? "⟳ Escalating..." : "↑ Escalate Command"}
            </button>
          </div>
        </div>
      )}

      {/* Operator signature */}
      {proposal.approved_by && (
        <div className="operator-sig">
          Reviewed by <strong style={{ color: "var(--text-secondary)" }}>{proposal.approved_by}</strong>
          {proposal.approved_at && (
            <> · {new Date(proposal.approved_at).toLocaleString()}</>
          )}
        </div>
      )}
    </div>
  );
};
