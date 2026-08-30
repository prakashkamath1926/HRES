import React, { useState } from "react";
import { Header } from "./Header";
import { useAuth } from "../hooks/useAuth";
import "../styles/global.css";

export const EmailComposer: React.FC = () => {
  const { user } = useAuth();
  const [to, setTo] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [attachAar, setAttachAar] = useState(false);
  const [incidentId, setIncidentId] = useState("");
  const [sending, setSending] = useState(false);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    setSending(true);
    try {
      const recipients = to.split(",").map(s => s.trim()).filter(Boolean);
      const token = localStorage.getItem("hres_token");
      const res = await fetch("/api/email/send", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          recipients,
          subject,
          body,
          incident_id: attachAar ? incidentId : undefined
        })
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to send email");
      }
      alert("Email sent successfully!");
      setTo("");
      setSubject("");
      setBody("");
      setAttachAar(false);
      setIncidentId("");
    } catch (err: any) {
      alert("Error sending email: " + err.message);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="dashboard-root" style={{ background: "var(--bg-base)" }}>
      <Header incident={null} onLocationChange={() => {}} />
      
      <main id="main-content" style={{ padding: "32px", display: "flex", justifyContent: "center" }}>
        <div className="card" style={{ width: "100%", maxWidth: "600px", padding: "24px" }}>
          <h2 style={{ marginBottom: "20px", color: "var(--text-primary)", fontSize: "20px" }}>Compose Email</h2>
          
          <form onSubmit={handleSend} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div>
              <label className="meta-label">To (comma-separated)</label>
              <div style={{ fontSize: "11px", color: "var(--color-warning)", marginBottom: "4px" }}>
                * For demo purposes, you can only send to: prakashwork1004@gmail.com
              </div>
              <input 
                type="text" 
                required
                value={to}
                onChange={(e) => setTo(e.target.value)}
                placeholder="prakashwork1004@gmail.com (e.g. Agency@gov, hospital@health.org)"
                style={{ width: "100%", padding: "8px", background: "var(--bg-input)", border: "1px solid var(--border-dim)", color: "white", borderRadius: "4px", marginTop: "4px" }}
              />
            </div>
            
            <div>
              <label className="meta-label">Subject</label>
              <input 
                type="text" 
                required
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="Emergency Update: Heatwave Alert"
                style={{ width: "100%", padding: "8px", background: "var(--bg-input)", border: "1px solid var(--border-dim)", color: "white", borderRadius: "4px", marginTop: "4px" }}
              />
            </div>
            
            <div>
              <label className="meta-label">Body</label>
              <textarea 
                required
                value={body}
                onChange={(e) => setBody(e.target.value)}
                rows={6}
                placeholder="Write your message here..."
                style={{ width: "100%", padding: "8px", background: "var(--bg-input)", border: "1px solid var(--border-dim)", color: "white", borderRadius: "4px", marginTop: "4px", resize: "vertical" }}
              />
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "8px", padding: "12px", background: "rgba(34, 211, 238, 0.05)", border: "1px solid rgba(34, 211, 238, 0.2)", borderRadius: "8px" }}>
              <label style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--text-primary)", fontSize: "14px", cursor: "pointer" }}>
                <input 
                  type="checkbox" 
                  checked={attachAar}
                  onChange={(e) => setAttachAar(e.target.checked)}
                />
                Attach After-Action Report (AAR)
              </label>
              
              {attachAar && (
                <input 
                  type="text"
                  required
                  value={incidentId}
                  onChange={(e) => setIncidentId(e.target.value)}
                  placeholder="Enter Incident ID (e.g. 562a19...)"
                  style={{ width: "100%", padding: "6px", background: "var(--bg-input)", border: "1px solid var(--border-dim)", color: "white", borderRadius: "4px", fontSize: "12px" }}
                />
              )}
            </div>
            
            <button 
              type="submit" 
              disabled={sending}
              style={{ padding: "12px", background: "var(--color-primary)", border: "none", color: "white", fontWeight: "bold", borderRadius: "6px", cursor: "pointer", marginTop: "8px" }}
            >
              {sending ? "Sending..." : "Send Email"}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
};
