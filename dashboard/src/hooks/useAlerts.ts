/**
 * AlertEngine — browser sound, voice TTS, and notification alerts
 * Fires automatically when risk crosses HIGH → CRITICAL threshold.
 */
import { useEffect, useRef, useCallback } from "react";
import { IncidentState } from "../types/incident";

const SEVERITY_ORDER = ["LOW", "MODERATE", "HIGH", "CRITICAL"];

function severityIndex(s: string): number {
  return SEVERITY_ORDER.indexOf(s ?? "LOW");
}

// --- Web Audio API Alert Sound ---
function playAlertTone(severity: string) {
  try {
    const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
    if (!AudioContext) return;
    const ctx = new AudioContext();

    const isCritical = severity === "CRITICAL";
    const baseFreq = isCritical ? 880 : 660;
    const duration = isCritical ? 2.5 : 1.5;
    const pulses = isCritical ? 4 : 2;

    for (let i = 0; i < pulses; i++) {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.type = isCritical ? "sawtooth" : "sine";
      osc.frequency.setValueAtTime(baseFreq, ctx.currentTime + i * 0.6);
      if (isCritical) osc.frequency.linearRampToValueAtTime(baseFreq * 1.5, ctx.currentTime + i * 0.6 + 0.2);

      gain.gain.setValueAtTime(0, ctx.currentTime + i * 0.6);
      gain.gain.linearRampToValueAtTime(isCritical ? 0.8 : 0.5, ctx.currentTime + i * 0.6 + 0.05);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + i * 0.6 + 0.5);

      osc.start(ctx.currentTime + i * 0.6);
      osc.stop(ctx.currentTime + i * 0.6 + 0.5);
    }

    setTimeout(() => ctx.close(), (duration + 0.5) * 1000);
  } catch (e) {
    console.warn("HRES Alert sound failed:", e);
  }
}

// --- Web Speech API TTS ---
function speakAlert(text: string) {
  try {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    utter.rate = 0.85;
    utter.pitch = 1.0;
    utter.volume = 1.0;
    // Try to get a clear English voice
    const voices = window.speechSynthesis.getVoices();
    const enVoice = voices.find(v => v.lang.startsWith("en") && !v.name.includes("("))?? voices[0];
    if (enVoice) utter.voice = enVoice;
    window.speechSynthesis.speak(utter);
  } catch (e) {
    console.warn("HRES TTS failed:", e);
  }
}

// --- Browser Notification API ---
async function showBrowserNotification(title: string, body: string, severity: string) {
  try {
    if (!("Notification" in window)) return;
    if (Notification.permission === "default") {
      await Notification.requestPermission();
    }
    if (Notification.permission === "granted") {
      const icon = severity === "CRITICAL" ? "🔥" : "🌡️";
      new Notification(`${icon} HRES: ${title}`, {
        body,
        tag: "hres-alert",
        renotify: true,
        requireInteraction: severity === "CRITICAL",
      });
    }
  } catch (e) {
    console.warn("Browser notification failed:", e);
  }
}

interface UseAlertsOptions {
  muted?: boolean;
}

export function useAlerts(incident: IncidentState | null, options: UseAlertsOptions = {}) {
  const prevSeverityRef = useRef<string>("LOW");
  const prevStatusRef = useRef<string>("");
  const { muted = false } = options;

  const triggerAlert = useCallback((severity: string, voiceText: string, notifTitle: string, notifBody: string) => {
    if (muted) return;
    playAlertTone(severity);
    showBrowserNotification(notifTitle, notifBody, severity);
    setTimeout(() => speakAlert(voiceText), 800);
  }, [muted]);

  useEffect(() => {
    if (!incident) return;

    const currentSeverity = incident.risk?.severity ?? "LOW";
    const currentStatus = incident.status ?? "";
    const prevSeverity = prevSeverityRef.current;
    const prevStatus = prevStatusRef.current;

    // Risk escalation alert
    if (severityIndex(currentSeverity) > severityIndex(prevSeverity)) {
      const isCritical = currentSeverity === "CRITICAL";

      // Find voice announcement from civilian agent action
      const civilianAction = incident.action_proposal?.actions?.find(a => a.type === "civilian_alert");
      const voiceText = civilianAction?.voice_announcement
        || (isCritical
          ? "Attention! HRES Critical Alert. Extreme heat or fire has been detected. Do not panic. Stay calm. Move to a cool, shaded area immediately. Drink water and await further instructions."
          : "Attention. HRES Heat Warning. Elevated temperatures detected in your area. Please move to shade, drink water, and stay calm."
        );

      const temperature = incident.events?.find(e => e.event_type === "heat")?.value?.temperature;
      const tempStr = temperature ? ` Temperature: ${temperature.toFixed(1)}°C.` : "";

      triggerAlert(
        currentSeverity,
        voiceText,
        `${currentSeverity} RISK ALERT`,
        `Heat risk has escalated to ${currentSeverity}.${tempStr} Check the HRES dashboard.`
      );
    }

    // Fire/smoke detection alert
    const hasFireEvent = incident.events?.some(e =>
      (e.event_type === "possible_fire" || e.event_type === "smoke_report") && e.status !== "unverified"
    );
    const prevHadFireEvent = prevStatusRef.current !== "possible_fire_active";

    if (hasFireEvent && prevHadFireEvent && currentStatus !== prevStatus) {
      triggerAlert(
        "CRITICAL",
        "Attention! Fire or smoke has been detected near your location by HRES. Do not panic. Evacuate calmly using the nearest exit. Do not use elevators. Move to the designated assembly point.",
        "🔥 FIRE / SMOKE DETECTED",
        "HRES has detected possible fire or smoke near your location. Follow evacuation instructions."
      );
    }

    // Approval required alert (softer)
    if (currentStatus === "awaiting_approval" && prevStatus !== "awaiting_approval" && !muted) {
      playAlertTone("HIGH");
      showBrowserNotification(
        "Operator Action Required",
        "HRES has generated a response plan that requires your approval before deployment.",
        "HIGH"
      );
    }

    prevSeverityRef.current = currentSeverity;
    prevStatusRef.current = currentStatus;
  }, [incident?.risk?.severity, incident?.status, incident?.events?.length, triggerAlert]);

  // Request notification permission on mount
  useEffect(() => {
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission();
    }
  }, []);

  return { triggerAlert };
}
