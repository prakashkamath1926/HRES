# HRES — Product and UX Design

## 1. Design Goal

HRES should feel like a calm emergency operations assistant, not a chatbot.

Primary design principle:

> **Minimum human work, maximum appropriate human control.**

The user should not need to repeatedly ask HRES what is happening.

---

## 2. Core Modes

### Mode A — Current Location

Default experience.

```text
📍 Using your current location
```

The system automatically monitors the user's surroundings after location permission is granted.

### Mode B — Search Location

The user can search for:
- college;
- home;
- workplace;
- hospital;
- public location;
- other supported place.

The selected location becomes the analysis context.

---

## 3. Main Dashboard

Recommended layout:

```text
┌─────────────────────────────────────────────┐
│ HRES                                      🟢 System Active    │
├───────────────────────┬──────────────────────────────────────┤
│ CURRENT RISK          │                                      │
│                       │             LIVE MAP                 │
│ 🟢 LOW                │                                      │
│ 34°C                  │        heat / incidents / routes     │
│                       │                                      │
│ Data: 2 min ago       │                                      │
├───────────────────────┴──────────────────────────────────────┤
│ INCIDENTS                                                   │
│ No active incidents / Active incident                      │
├───────────────────────────┬──────────────────────────────────┤
│ SOURCES                   │ RECOMMENDED ACTION               │
│ FortyGuard ✓              │ Stay indoors                     │
│ Weather ✓                 │ Cooling center 1.8 km           │
│ Reports ✓                 │ Hospital 3.2 km                  │
└───────────────────────────┴──────────────────────────────────┘
```

---

## 4. Risk States

Use clear visual severity:

- **LOW** — normal monitoring.
- **MODERATE** — precautions.
- **HIGH** — active warning and recommended action.
- **CRITICAL** — urgent response workflow and approval/escalation.

Avoid making every event visually alarming.

---

## 5. Alert Design

Every alert should answer:

1. What happened?
2. Where?
3. How serious?
4. What should I do?

Example:

> **HIGH HEAT ALERT**  
> Elevated heat conditions detected near your current location.  
> Move to a cool/shaded area and reduce outdoor activity.  
> Nearest suitable cooling facility: 1.8 km.

Critical alerts may use a high-priority sound/voice notification in the application.

The prototype must not create unnecessary panic.

---

## 6. Incident View

Show:

- incident ID;
- location;
- event type;
- severity;
- confidence;
- sources;
- timeline;
- affected area;
- current plan;
- route;
- hospital/cooling-center options;
- approval state;
- agent status;
- latest update.

---

## 7. Verification View

Example:

```text
EVENT: Possible Fire

FortyGuard heat      ✓ Extreme
Weather              ✓ High wind
User report          ✓ Smoke reported
Sensor               ? Not available

Confidence: 0.86

Status: LIKELY / Awaiting confirmation
```

Do not represent confidence as certainty.

---

## 8. Human Approval View

Example:

```text
┌─────────────────────────────────────┐
│ ACTION PROPOSAL                     │
│                                     │
│ Severity: CRITICAL                  │
│ Confidence: 0.91                    │
│                                     │
│ Proposed actions:                   │
│ • Alert affected users              │
│ • Prepare responder route           │
│ • Prepare ambulance route           │
│ • Notify administrator              │
│                                     │
│ [ APPROVE ] [ MODIFY ]              │
│ [ REJECT ]  [ ESCALATE ]            │
└─────────────────────────────────────┘
```

---

## 9. Replanning View

When the environment changes:

```text
⚠ CONDITIONS CHANGED

Previous route:
Route A

Reason:
Road blockage + expanding hazard zone

HRES is replanning...

Supervisor:
New plan generated

New responder route:
Route B

New civilian guidance:
Move toward Cooling Center 2
```

The user should clearly see that the system adapted.

---

## 10. Agent Status

Do not expose internal chain-of-thought.

Instead show safe operational status:

```text
Perception       ✓ Complete
Verification     ✓ Complete
Risk Assessment  ✓ Complete
Supervisor       ● Planning
Response         ✓ Ready
Civilian         ✓ Ready
Civic            ✓ Ready
Approval         ⏳ Required
```

---

## 11. Privacy UX

Show:
- location permission state;
- current monitoring location;
- option to stop monitoring;
- clear distinction between current and searched location.

Do not silently track locations.

---

## 12. Offline / Poor Network Design

The product may provide a limited degraded mode:

- cached emergency instructions;
- cached last-known state with timestamp;
- local alerting for already-known conditions;
- queued non-critical updates.

It must clearly say when data is stale.

A future optional peer-to-peer/mesh mode may share approved emergency information between nearby devices, but this is **not part of the initial MVP** and must not be presented as implemented unless actually built and tested.

---

## 13. Tone

HRES communication should be:
- calm;
- direct;
- short during emergencies;
- transparent about uncertainty;
- actionable;
- non-diagnostic.

Avoid:
- dramatic language;
- unexplained AI terminology;
- false certainty;
- excessive notifications.

---

## 14. Design Principle for AI

The interface should show:

**Evidence → Assessment → Recommendation → Approval → Action**

not:

**AI says so → action**

This makes HRES understandable and trustworthy.
