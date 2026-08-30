import { IncidentState } from "../types/incident";

const BASE_URL = import.meta.env.VITE_API_URL || "/api";

export async function fetchCurrentIncident(): Promise<IncidentState> {
  const response = await fetch(`${BASE_URL}/incidents/current`);
  if (!response.ok) {
    throw new Error("Failed to fetch current incident status");
  }
  return response.json();
}

export async function updateLocation(latitude: number, longitude: number, address?: string): Promise<IncidentState> {
  const response = await fetch(`${BASE_URL}/location`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ latitude, longitude, address })
  });
  if (!response.ok) {
    throw new Error("Failed to update monitored location");
  }
  return response.json();
}

export async function triggerSimulation(scenario: string): Promise<IncidentState> {
  const response = await fetch(`${BASE_URL}/simulations/${scenario}`, {
    method: "POST"
  });
  if (!response.ok) {
    throw new Error(`Failed to trigger simulation scenario: ${scenario}`);
  }
  return response.json();
}

export async function submitApproval(
  incidentId: string,
  payload: { decision: string; comment?: string; operator_id?: string; proposal_version?: number }
): Promise<IncidentState> {
  const response = await fetch(`${BASE_URL}/incidents/${incidentId}/approval`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error("Failed to submit operator decision");
  }
  return response.json();
}

export async function resolveIncident(incidentId: string): Promise<IncidentState> {
  const response = await fetch(`${BASE_URL}/incidents/${incidentId}/resolve`, {
    method: "POST"
  });
  if (!response.ok) {
    throw new Error("Failed to resolve incident");
  }
  return response.json();
}

export async function downloadAfterActionReport(incidentId: string): Promise<string> {
  const response = await fetch(`${BASE_URL}/incidents/${incidentId}/aar`);
  if (!response.ok) {
    throw new Error("Failed to download After-Action Report");
  }
  return response.text();
}

// Chat — returns raw Response for streaming SSE
export async function streamChat(
  messages: { role: string; content: string }[]
): Promise<Response> {
  const response = await fetch(`${BASE_URL}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, include_incident_context: true }),
  });
  if (!response.ok) {
    throw new Error(`Chat API error: ${response.status}`);
  }
  return response;
}
