import { useState, useEffect, useCallback, useRef } from "react";
import { IncidentState } from "../types/incident";
import * as api from "../services/api";

const POLL_INTERVAL_MS = 2000;
const MAX_BACKOFF_MS = 16000;

export function useIncident() {
  const [incident, setIncident] = useState<IncidentState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const failCountRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const refresh = useCallback(async (silent = false) => {
    try {
      const data = await api.fetchCurrentIncident();
      setIncident(data);
      setError(null);
      failCountRef.current = 0;
    } catch (e: any) {
      failCountRef.current += 1;
      setError(e.message || "Failed to fetch current incident status");
    } finally {
      if (!silent) setLoading(false);
    }
  }, []);

  // Polling with exponential backoff on errors
  useEffect(() => {
    let mounted = true;

    const tick = async () => {
      if (!mounted) return;
      await refresh(true);
      if (!mounted) return;

      const backoff = Math.min(
        POLL_INTERVAL_MS * Math.pow(2, Math.max(0, failCountRef.current - 1)),
        MAX_BACKOFF_MS
      );
      const delay = failCountRef.current > 0 ? backoff : POLL_INTERVAL_MS;
      timerRef.current = setTimeout(tick, delay);
    };

    // Initial load
    refresh().then(() => {
      if (mounted) timerRef.current = setTimeout(tick, POLL_INTERVAL_MS);
    });

    return () => {
      mounted = false;
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [refresh]);

  const triggerScenario = useCallback(async (scenario: string) => {
    setLoading(true);
    try {
      const updated = await api.triggerSimulation(scenario);
      setIncident(updated);
      setError(null);
    } catch (e: any) {
      setError(e.message || `Failed to trigger scenario: ${scenario}`);
    } finally {
      setLoading(false);
    }
  }, []);

  const changeLocation = useCallback(async (lat: number, lon: number, address?: string) => {
    setLoading(true);
    try {
      const updated = await api.updateLocation(lat, lon, address);
      setIncident(updated);
      setError(null);
    } catch (e: any) {
      setError(e.message || "Failed to update monitored location");
    } finally {
      setLoading(false);
    }
  }, []);

  const submitDecision = useCallback(async (decision: string, comment?: string) => {
    if (!incident) return;
    setLoading(true);
    try {
      const updated = await api.submitApproval(incident.incident_id, {
        decision,
        comment,
        operator_id: "demo-admin",
        proposal_version: 1,
      });
      setIncident(updated);
      setError(null);
    } catch (e: any) {
      setError(e.message || "Failed to submit approval decision");
    } finally {
      setLoading(false);
    }
  }, [incident]);

  const handleResolve = useCallback(async () => {
    if (!incident) return;
    setLoading(true);
    try {
      const updated = await api.resolveIncident(incident.incident_id);
      setIncident(updated);
      setError(null);
    } catch (e: any) {
      setError(e.message || "Failed to resolve incident");
    } finally {
      setLoading(false);
    }
  }, [incident]);

  return {
    incident,
    loading,
    error,
    refresh,
    triggerScenario,
    changeLocation,
    submitDecision,
    handleResolve,
  };
}
