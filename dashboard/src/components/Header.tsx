import React, { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { IncidentState } from "../types/incident";

interface HeaderProps {
  incident: IncidentState | null;
  onLocationChange: (lat: number, lon: number, address?: string, mode?: string) => void;
}

const STATUS_COLORS: Record<string, string> = {
  received:         "#3b82f6",
  verifying:        "#f59e0b",
  monitoring:       "#10b981",
  planning:         "#8b5cf6",
  awaiting_approval:"#f97316",
  active:           "#ef4444",
  replanning:       "#f59e0b",
  resolved:         "#4d6080",
};

export const Header: React.FC<HeaderProps> = ({ incident, onLocationChange }) => {
  const navigate = useNavigate();
  const [searchVal, setSearchVal] = useState("");
  const [locationMode, setLocationMode] = useState<"default" | "gps" | "custom">("default");
  const [gpsLoading, setGpsLoading] = useState(false);

  const storedUser = localStorage.getItem("hres_user");
  const user = storedUser ? JSON.parse(storedUser) : null;

  const handleLogout = useCallback(async () => {
    const token = localStorage.getItem("hres_token");
    try {
      await fetch("/api/auth/logout", {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
    } catch { /* ignore network errors on logout */ }
    localStorage.removeItem("hres_token");
    localStorage.removeItem("hres_user");
    window.location.href = "/login";
  }, []);

  const lastObs = incident?.observations?.[incident.observations.length - 1];
  const displayAddress = lastObs?.location.address || "HeatShield Campus Zone, Jaipur";
  const coords = lastObs
    ? `${lastObs.location.latitude.toFixed(4)}°N ${lastObs.location.longitude.toFixed(4)}°E`
    : "26.9124°N 75.7873°E";

  const statusLabel = incident?.status
    ? incident.status.replace(/_/g, " ").toUpperCase()
    : "STANDBY";
  const statusColor = incident?.status ? (STATUS_COLORS[incident.status] || "#4d6080") : "#10b981";

  const handleGPS = useCallback(() => {
    if (!navigator.geolocation) return;
    setGpsLoading(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setGpsLoading(false);
        setLocationMode("gps");
        onLocationChange(pos.coords.latitude, pos.coords.longitude, "GPS Location", "gps");
      },
      () => {
        setGpsLoading(false);
        alert("Location permission denied. Please allow location access.");
      },
      { timeout: 10000, maximumAge: 60000 }
    );
  }, [onLocationChange]);

  const handleSearch = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    const q = searchVal.trim();
    if (!q) return;
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(q)}&format=json&limit=1`
      );
      const data = await res.json();
      if (data.length > 0) {
        const { lat, lon, display_name } = data[0];
        setLocationMode("custom");
        setSearchVal("");
        onLocationChange(parseFloat(lat), parseFloat(lon), display_name.split(",")[0], "search");
      } else {
        alert("Location not found. Try a more specific query.");
      }
    } catch {
      alert("Geocoding failed — check network connection.");
    }
  }, [searchVal, onLocationChange]);

  return (
    <header className="hres-header">
      {/* Brand */}
      <div className="header-brand">
        <div className="pulse-ring" />
        <div>
          <div className="brand-name">HRES</div>
          <div className="brand-sub">Heat Response Emergency System</div>
        </div>
      </div>

      {/* Location Bar */}
      <div className="header-location-bar">
        <span className={`location-mode-badge ${locationMode}`}>
          {locationMode === "gps" ? "📍 GPS" : locationMode === "custom" ? "📍 Custom" : "📍 Default"}
        </span>

        <form className="location-search-form" onSubmit={handleSearch}>
          <input
            className="location-search-input"
            type="text"
            placeholder="Search location — e.g. 'Jaipur Airport'"
            value={searchVal}
            onChange={(e) => setSearchVal(e.target.value)}
          />
          <button className="btn-location" type="submit">Search</button>
        </form>

        <button
          className="btn-location gps"
          onClick={handleGPS}
          disabled={gpsLoading}
          title="Use browser GPS"
        >
          {gpsLoading ? "⟳" : "GPS"}
        </button>
      </div>

      {/* Meta */}
      <div className="header-meta">
        <div style={{ display: "flex", gap: "8px", marginRight: "16px" }}>
          <button onClick={() => navigate("/")} className="btn-location" style={{ background: "transparent", color: "var(--text-primary)" }}>Dashboard</button>
          <button onClick={() => navigate("/email")} className="btn-location" style={{ background: "transparent", color: "var(--text-primary)" }}>Email</button>
          <button onClick={() => navigate("/profile")} className="btn-location" style={{ background: "transparent", color: "var(--text-primary)" }}>Profile</button>
        </div>

        <div className="meta-item">
          <span className="meta-label">Monitoring</span>
          <span className="meta-value" title={displayAddress} style={{ maxWidth: 160, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {displayAddress}
          </span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Status</span>
          <span
            className="status-chip"
            style={{ color: statusColor, borderColor: `${statusColor}66`, background: `${statusColor}11` }}
          >
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: statusColor, display: "inline-block" }} />
            {statusLabel}
          </span>
        </div>
        {user && (
          <div className="meta-item" style={{ gap: 6 }}>
            <span className="meta-label">Signed in as</span>
            <span className="meta-value" style={{ fontSize: 11, maxWidth: 120, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={user.email}>
              {user.name || user.email}
            </span>
            <button
              onClick={handleLogout}
              style={{
                background: "rgba(239,68,68,0.12)",
                border: "1px solid rgba(239,68,68,0.35)",
                color: "#fca5a5",
                borderRadius: 4,
                padding: "2px 7px",
                fontSize: 10,
                cursor: "pointer",
                fontFamily: "var(--font-sans)",
                letterSpacing: "0.03em",
              }}
              title="Sign out"
            >
              Sign out
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
