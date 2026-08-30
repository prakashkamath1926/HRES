import React, { useState, useEffect } from "react";
import { Header } from "./Header";
import { useAuth } from "../hooks/useAuth";
import "../styles/global.css"; // Ensure styles are imported

interface HistoryEvent {
  incident_id: string;
  timestamp: string;
  event_type: string;
  last_message: string;
}

export const ProfilePage: React.FC = () => {
  const { user } = useAuth();
  const [orgMail, setOrgMail] = useState(user?.org_mail || "");
  const [employeeId, setEmployeeId] = useState(user?.employee_id || "");
  const [history, setHistory] = useState<HistoryEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (user) {
      setOrgMail(user.org_mail || "");
      setEmployeeId(user.employee_id || "");
    }
  }, [user]);

  useEffect(() => {
    setLoading(true);
    const token = localStorage.getItem("hres_token");
    fetch("/api/auth/history", {
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      }
    })
      .then((res) => res.json())
      .then((data) => setHistory(data.history || []))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const token = localStorage.getItem("hres_token");
      const res = await fetch("/api/auth/profile", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ org_mail: orgMail, employee_id: employeeId })
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to update profile");
      }
      const data = await res.json();
      // update local storage with new user details
      localStorage.setItem("hres_user", JSON.stringify(data));
      alert("Profile updated successfully!");
    } catch (err: any) {
      alert("Error updating profile: " + err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="dashboard-root" style={{ background: "var(--bg-base)" }}>
      <Header incident={null} onLocationChange={() => {}} />
      
      <main id="main-content" style={{ padding: "32px", display: "flex", gap: "32px", maxWidth: "1200px", margin: "0 auto", width: "100%" }}>
        
        {/* Left Column: Profile Editor */}
        <div className="card" style={{ flex: 1, padding: "24px" }}>
          <h2 style={{ marginBottom: "20px", color: "var(--text-primary)", fontSize: "20px" }}>User Profile</h2>
          
          <div style={{ marginBottom: "24px", background: "var(--bg-surface)", padding: "16px", borderRadius: "8px" }}>
            <p><strong>Name:</strong> {user?.name}</p>
            <p><strong>Email:</strong> {user?.email}</p>
            <p><strong>Role:</strong> {user?.role.toUpperCase()}</p>
            <p><strong>Organization Type:</strong> {user?.org_type || "N/A"}</p>
          </div>

          <form onSubmit={handleSave} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div>
              <label className="meta-label">Organization Email</label>
              <input 
                type="email" 
                value={orgMail}
                onChange={(e) => setOrgMail(e.target.value)}
                placeholder="e.g. jdoe@ngo.org"
                style={{ width: "100%", padding: "8px", background: "var(--bg-input)", border: "1px solid var(--border-dim)", color: "white", borderRadius: "4px", marginTop: "4px" }}
              />
            </div>
            <div>
              <label className="meta-label">Employee ID</label>
              <input 
                type="text" 
                value={employeeId}
                onChange={(e) => setEmployeeId(e.target.value)}
                placeholder="e.g. EMP-9382"
                style={{ width: "100%", padding: "8px", background: "var(--bg-input)", border: "1px solid var(--border-dim)", color: "white", borderRadius: "4px", marginTop: "4px" }}
              />
            </div>
            
            <button 
              type="submit" 
              disabled={saving}
              style={{ padding: "10px", background: "var(--color-primary)", border: "none", color: "white", fontWeight: "bold", borderRadius: "6px", cursor: "pointer", marginTop: "8px" }}
            >
              {saving ? "Saving..." : "Save Profile"}
            </button>
          </form>
        </div>

        {/* Right Column: Incident History */}
        <div className="card" style={{ flex: 2, padding: "24px" }}>
          <h2 style={{ marginBottom: "20px", color: "var(--text-primary)", fontSize: "20px" }}>Your Incident History</h2>
          {loading ? (
            <div className="replan-spinner" />
          ) : history.length === 0 ? (
            <p style={{ color: "var(--text-muted)" }}>No incident history found for your account.</p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {history.map((h, idx) => (
                <div key={idx} style={{ padding: "12px", background: "var(--bg-surface)", border: "1px solid var(--border-dim)", borderRadius: "8px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                    <strong style={{ color: "var(--text-primary)" }}>Incident: {h.incident_id.split("-")[0]}...</strong>
                    <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>{new Date(h.timestamp).toLocaleString()}</span>
                  </div>
                  <div style={{ fontSize: "12px", color: "var(--text-primary)", marginBottom: "4px" }}>
                    <span style={{ color: "var(--color-info)", fontWeight: 600 }}>[{h.event_type}]</span> {h.last_message}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};
