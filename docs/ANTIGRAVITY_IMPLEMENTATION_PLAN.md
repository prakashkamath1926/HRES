# HRES — Antigravity Implementation Plan

## Heat Response Emergency System

HRES is a human-supervised, event-driven, multi-agent heat emergency coordination system.

The system continuously observes heat and environmental conditions, combines multiple data sources, verifies events, deterministically calculates risk, uses LangGraph to coordinate specialized agents, proposes response actions, waits for human approval for high-impact actions, replans when conditions change, and maintains a complete audit trail.

The system is designed primarily for a reliable hackathon demonstration.

---

# 1. CORE PRODUCT PRINCIPLE

HRES is NOT an autonomous emergency dispatch system.

HRES is:

> A human-supervised AI system for heat-risk detection, verification, prioritization, response planning, and dynamic replanning.

AI may:

- summarize information
- explain risk
- generate civilian communication
- generate responder guidance drafts
- generate civic reports
- suggest routes
- suggest response plans

AI must NOT independently:

- determine emergency severity
- override deterministic safety rules
- dispatch real emergency services
- contact real emergency services
- make medical diagnoses
- fabricate sensor readings
- fabricate live API data
- bypass human approval for high-impact actions

All safety-critical decisions must remain deterministic and auditable.

---

# 2. PRIMARY DEMO SCENARIO

Use a fictionalized college-campus heat emergency scenario in Jaipur.

Example:

Location:

"HeatShield Campus Zone, Jaipur"

Do NOT claim that a real emergency is occurring.

Use clearly labelled simulated coordinates/data if real campus permission is unavailable.

Demo sequence:

1. Normal conditions
2. Heat begins increasing
3. FortyGuard heat data confirms elevated heat
4. Weather data provides supporting environmental context
5. System calculates increasing risk
6. Simulated smoke report appears
7. Verification engine checks multiple sources
8. Risk becomes HIGH/CRITICAL according to deterministic rules
9. Supervisor activates required agents
10. Agents generate response proposal
11. Human approval gate appears
12. Human approves response
13. Simulated civilian/responder actions are executed
14. Main route becomes blocked
15. System detects route change
16. Supervisor triggers replanning
17. New safer route is proposed
18. Incident is resolved
19. After-Action Report is generated

This complete scenario must work even when external APIs are unavailable.

---

# 3. TECHNOLOGY STACK

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Backend | FastAPI |
| Agent orchestration | LangGraph |
| Validation | Pydantic |
| Configuration | pydantic-settings |
| Heat intelligence | FortyGuard Temperature API |
| Weather | Open-Meteo |
| Maps | Google Maps Platform if configured |
| LLM | Gemini API |
| LLM SDK | google-genai or langchain-google-genai |
| Database | SQLite for MVP |
| Production DB | PostgreSQL later |
| Cache | Redis only if genuinely required |
| Frontend | Vite + React + TypeScript |
| Styling | Vanilla CSS |
| Realtime | WebSocket |
| Reports | ReportLab |
| Testing | pytest |
| HTTP client | httpx |
| Deployment | Frontend: Vercel |
| Backend deployment | Keep deployment-independent; do NOT require Docker |

Do not introduce additional frameworks unless there is a reason.

---

# 4. IMPORTANT DEPLOYMENT DECISION

Docker is NOT required for the MVP.

Do not build the project around Docker.

The frontend should be deployable to Vercel.

The FastAPI backend may run locally during the hackathon/demo.

If backend cloud deployment is required later, use a platform suitable for long-running FastAPI/WebSocket services.

Do NOT redesign the application around Vercel serverless functions merely to force the backend onto Vercel.

The architecture must remain deployment-independent.

---

# 5. ARCHITECTURE

High-level architecture:

```text
                    ┌───────────────────────┐
                    │     React Dashboard   │
                    │ Vite + TS + Vanilla CSS│
                    └───────────┬───────────┘
                                │
                         REST + WebSocket
                                │
                                ▼
                    ┌───────────────────────┐
                    │       FastAPI         │
                    │       API Layer       │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   LangGraph Supervisor│
                    │    Orchestration      │
                    └───────────┬───────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
       Verification        Risk Engine       Planning
          Agent          Deterministic        Agents
                              │
                              │
               ┌──────────────┼──────────────┐
               │              │              │
               ▼              ▼              ▼
           Civilian        Response         Civic
             Agent           Agent          Agent
               │              │              │
               └──────────────┼──────────────┘
                              ▼
                    ┌───────────────────────┐
                    │ Human Approval Gate   │
                    └───────────┬───────────┘
                                │
                                ▼
                    Simulated Actions
                                │
                                ▼
                    Audit + Incident Store
```

---

# 6. DATA FLOW

```text
External Sources
     │
     ├── FortyGuard
     ├── Open-Meteo
     ├── Maps
     └── User Reports / Simulation
              │
              ▼
       Perception Layer
              │
              ▼
       Raw Observations
              │
              ▼
      Normalization
              │
              ▼
        Verification
              │
              ▼
       Risk Calculation
       (Deterministic)
              │
              ▼
      LangGraph Supervisor
              │
       ┌──────┼───────┐
       ▼      ▼       ▼
   Civilian Response Civic
     Agent    Agent   Agent
       │      │       │
       └──────┼───────┘
              ▼
       Action Proposal
              │
              ▼
       Human Approval
              │
              ▼
      Simulated Action
              │
              ▼
          Audit Log
              │
              ▼
       Dashboard Update
```

---

# 7. PROJECT STRUCTURE

```text
HRES/
│
├── backend/
│   ├── app/
│   │   │
│   │   ├── agents/
│   │   │   ├── supervisor.py
│   │   │   ├── verification_agent.py
│   │   │   ├── civilian_agent.py
│   │   │   ├── response_agent.py
│   │   │   └── civic_agent.py
│   │   │
│   │   ├── api/
│   │   │   ├── incidents.py
│   │   │   ├── approval.py
│   │   │   ├── simulation.py
│   │   │   ├── location.py
│   │   │   ├── reports.py
│   │   │   └── websocket.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── schemas.py
│   │   │   ├── state.py
│   │   │   └── constants.py
│   │   │
│   │   ├── integrations/
│   │   │   ├── fortyguard.py
│   │   │   ├── weather.py
│   │   │   ├── maps.py
│   │   │   ├── llm.py
│   │   │   └── notifications.py
│   │   │
│   │   ├── services/
│   │   │   ├── verification.py
│   │   │   ├── prioritization.py
│   │   │   ├── routing.py
│   │   │   ├── monitoring.py
│   │   │   ├── reporting.py
│   │   │   └── audit.py
│   │   │
│   │   ├── repositories/
│   │   │   ├── database.py
│   │   │   ├── incidents.py
│   │   │   ├── observations.py
│   │   │   ├── approvals.py
│   │   │   └── audit_log.py
│   │   │
│   │   ├── simulations/
│   │   │   ├── normal_conditions.json
│   │   │   ├── heat_escalation.json
│   │   │   ├── smoke_report.json
│   │   │   └── road_blockage.json
│   │   │
│   │   └── main.py
│   │
│   ├── tests/
│   │   ├── test_verification.py
│   │   ├── test_prioritization.py
│   │   ├── test_workflow.py
│   │   ├── test_api.py
│   │   └── test_simulation.py
│   │
│   ├── requirements.txt
│   └── .env.example
│
├── dashboard/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.tsx
│   │   │   ├── RiskIndicator.tsx
│   │   │   ├── SourceGrid.tsx
│   │   │   ├── IncidentPanel.tsx
│   │   │   ├── ApprovalPanel.tsx
│   │   │   ├── AuditTimeline.tsx
│   │   │   ├── SimulationConsole.tsx
│   │   │   ├── MapPanel.tsx
│   │   │   └── ReportCenter.tsx
│   │   │
│   │   ├── pages/
│   │   │   └── Dashboard.tsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── useIncident.ts
│   │   │   └── useWebSocket.ts
│   │   │
│   │   ├── services/
│   │   │   └── api.ts
│   │   │
│   │   ├── types/
│   │   │   └── incident.ts
│   │   │
│   │   ├── styles/
│   │   │   └── global.css
│   │   │
│   │   ├── App.tsx
│   │   └── main.tsx
│   │
│   ├── package.json
│   └── vite.config.ts
│
├── docs/
│   ├── PRD.md
│   ├── architecture.md
│   ├── rules.md
│   ├── phases.md
│   ├── design.md
│   └── ANTIGRAVITY_IMPLEMENTATION_PLAN.md
│
├── data/
│   └── hres.db
│
├── .env.example
├── README.md
└── .gitignore
```

---

# 8. CORE DATA MODELS

Use Pydantic models.

## LocationContext

```python
class LocationContext(BaseModel):
    latitude: float
    longitude: float
    address: str | None = None
    source: str
    timestamp: datetime
```

## Observation

Raw information received from a source.

```python
class Observation(BaseModel):
    observation_id: str
    source: str
    data_mode: DataMode
    event_type: EventType
    location: LocationContext
    observed_at: datetime
    received_at: datetime
    value: dict
    confidence: float
    raw_payload: dict | None = None
```

## NormalizedEvent

Represents the verified/normalized interpretation of observations.

```python
class NormalizedEvent(BaseModel):
    event_id: str
    event_type: EventType
    location: LocationContext
    status: str
    confidence: float
    value: dict
    supporting_observations: list[str]
```

## RiskAssessment

```python
class RiskAssessment(BaseModel):
    score: float
    severity: str
    exposure: float
    priority: str
    reasoning: list[str]
```

## ActionProposal

```python
class ActionProposal(BaseModel):
    actions: list[dict]
    status: str
    reasoning: list[str]
    approval_status: str
    approved_by: str | None = None
    approved_at: datetime | None = None
```

## IncidentState

```python
class IncidentState(BaseModel):
    incident_id: str
    status: str
    observations: list[Observation]
    events: list[NormalizedEvent]
    risk: RiskAssessment | None
    action_proposal: ActionProposal | None
    routes: list[dict]
    audit_log: list[dict]
```

---

# 9. ENUMS

Use explicit enums.

```python
class EventType(str, Enum):
    HEAT = "heat"
    POSSIBLE_FIRE = "possible_fire"
    SMOKE_REPORT = "smoke_report"
    ROAD_BLOCK = "road_block"
    MEDICAL_RISK = "medical_risk"


class DataMode(str, Enum):
    LIVE = "live"
    CACHED = "cached"
    SIMULATED = "simulated"
    UNAVAILABLE = "unavailable"


class IncidentStatus(str, Enum):
    RECEIVED = "received"
    VERIFYING = "verifying"
    MONITORING = "monitoring"
    PLANNING = "planning"
    AWAITING_APPROVAL = "awaiting_approval"
    ACTIVE = "active"
    REPLANNING = "replanning"
    RESOLVED = "resolved"


class ApprovalStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    MODIFIED = "modified"
    REJECTED = "rejected"
    ESCALATED = "escalated"
```

---

# 10. PERCEPTION LAYER

Create adapters for each external source.

## FortyGuard

`integrations/fortyguard.py`

Responsibilities:

* call FortyGuard API
* normalize response
* return Observation
* preserve raw response
* record timestamps
* identify LIVE/CACHED/UNAVAILABLE
* timeout safely
* never fabricate heat values

Important:

The existing FortyGuard API has previously produced:

* `ConnectionResetError`
* `SSLEOFError`
* connection failures

Therefore the application MUST NOT crash when FortyGuard fails.

Fallback order:

```text
FortyGuard LIVE
      ↓ failure
Cached FortyGuard response
      ↓ unavailable
Explicit SIMULATION scenario
      ↓
UNAVAILABLE
```

Never silently convert failure into fake LIVE data.

The dashboard must show the actual data mode.

Example:

```text
FORTYGUARD
● LIVE
```

or:

```text
FORTYGUARD
● SIMULATED
```

---

# 11. WEATHER

Use Open-Meteo where possible.

Collect:

* temperature
* apparent temperature
* humidity
* wind speed
* precipitation
* forecast context

Open-Meteo does not require an API key for the MVP.

Fallback:

```text
LIVE
→ cached
→ simulated
→ unavailable
```

---

# 12. MAPS

Use Google Maps only if configured.

Potential functions:

* route calculation
* alternate routes
* facility coordinates
* cooling centers
* hospitals
* route blockage simulation

If Google Maps is unavailable:

Use static demo routes.

The UI MUST explicitly show:

> Simulation route — not live traffic aware

Never present simulated routes as live emergency routes.

---

# 13. VERIFICATION ENGINE

`services/verification.py`

This must be deterministic Python.

The verification engine:

* deduplicates observations
* checks freshness
* checks source agreement
* calculates confidence
* detects conflicts
* determines whether an event is sufficiently supported

Example:

```text
FortyGuard:
Extreme heat

Open-Meteo:
High temperature

User report:
Smoke detected

↓

Verification

Heat:
SUPPORTED

Smoke:
UNVERIFIED / PARTIALLY VERIFIED
```

Verification must NOT be delegated to the LLM.

---

# 14. CONFIDENCE

Use an explainable confidence model.

Example:

```text
confidence =
    source_reliability * 0.40
    + freshness * 0.25
    + source_consensus * 0.25
    + location_match * 0.10
```

Clamp result to:

```text
0.0 → 1.0
```

The exact weights may be adjusted, but the calculation must remain deterministic and documented.

---

# 15. RISK ENGINE

`services/prioritization.py`

Risk classification MUST be deterministic.

Suggested score:

```text
priority_score =
    heat_severity_score * 0.35
    + exposure_score * 0.20
    + vulnerability_score * 0.20
    + confidence_score * 0.15
    + access_constraint_score * 0.10
```

Normalize to 0–100.

Classification:

```text
0–24     LOW
25–49    MODERATE
50–74    HIGH
75–100   CRITICAL
```

Additional deterministic safety rules may override normal scoring.

Example:

```python
if fire_verified and people_at_risk > 0:
    severity = "CRITICAL"
```

But:

```python
if only_one_unverified_smoke_report:
    severity = existing_risk
    status = "MONITORING"
    requires_human_review = True
```

The LLM cannot modify these rules.

---

# 16. LANGGRAPH ORCHESTRATION

LangGraph manages workflow/state.

The Supervisor is responsible for routing.

Do NOT execute every agent for every event.

Example:

```text
Verified high heat
    ↓
Civilian Agent
    +
Civic Agent


Possible verified fire
    ↓
Response Agent
    +
Civilian Agent
    +
Civic Agent


Unverified smoke report
    ↓
Verification
    ↓
Monitor


Road blockage
    ↓
Routing
    ↓
Civilian Agent
    +
Response Agent
    ↓
REPLAN
```

This demonstrates genuine agent orchestration rather than simply calling multiple LLMs sequentially.

---

# 17. AGENTS

## Verification Agent

Purpose:

* coordinate verification workflow
* consume deterministic verification engine
* summarize verification result

The agent does not decide safety thresholds.

---

## Risk Agent

Purpose:

* execute deterministic prioritization engine
* explain score
* return structured RiskAssessment

The actual calculation is Python.

---

## Supervisor Agent

Purpose:

* manage LangGraph state
* decide which agents are necessary
* detect replanning conditions
* route workflow
* manage approval state

Supervisor must not override deterministic safety rules.

---

## Civilian Agent

Purpose:

* generate civilian-friendly guidance
* explain current risk
* suggest safe routes
* suggest cooling centers
* produce concise alerts

LLM allowed.

Output must be structured and validated.

---

## Response Agent

Purpose:

* draft responder guidance
* suggest responder routes
* suggest hospital/cooling-center destinations
* explain operational considerations

No real dispatch.

All actions are simulated.

---

## Civic Agent

Purpose:

* create official-style incident summary
* generate notification drafts
* create report content
* summarize audit history

No automatic external publication.

---

# 18. LLM BOUNDARY

Gemini is used only for:

* explanation
* summarization
* communication generation
* draft response plans
* report writing

Gemini MUST NOT determine:

* LOW/MODERATE/HIGH/CRITICAL
* whether evidence is verified
* whether an emergency is real
* whether human approval is required
* whether an action is safe
* whether external services should be contacted

All LLM outputs must be Pydantic validated.

Use structured output where possible.

LLM provider must be behind an abstraction:

```text
LLMService
    ↓
GeminiProvider
```

Do not scatter direct Gemini API calls throughout the application.

If Gemini fails:

```text
Gemini unavailable
       ↓
Deterministic fallback templates
```

The application must continue functioning.

---

# 19. HUMAN APPROVAL

Human approval must be risk-based.

Do NOT require approval for every harmless action.

Example:

### LOW

Informational dashboard update.

```text
approval = NOT_REQUIRED
```

### MODERATE

Civilian safety recommendation.

```text
approval = NOT_REQUIRED
```

### HIGH

High-impact simulated response plan.

```text
approval = PENDING
```

### CRITICAL

Emergency response proposal.

```text
approval = PENDING
```

Human actions:

```text
APPROVE
MODIFY
REJECT
ESCALATE
```

Approval state:

```text
not_required
pending
approved
modified
rejected
escalated
```

The UI must clearly show:

```text
AI PROPOSAL
       ↓
HUMAN REVIEW
       ↓
APPROVE / MODIFY / REJECT / ESCALATE
       ↓
SIMULATED ACTION
```

---

# 20. REPLANNING

Dynamic replanning is a major HRES feature.

Example:

```text
Current Route
     ↓
Road Blockage Detected
     ↓
Supervisor
     ↓
Routing Service
     ↓
Alternative Route
     ↓
Civilian + Response Agents
     ↓
New Action Proposal
```

The old plan must remain in the audit log.

The new plan must have a new version.

Example:

```text
Plan v1
Plan v2 — replanned due to ROAD_BLOCK
```

---

# 21. PERSISTENCE

Use SQLite for MVP.

Separate persistence concepts:

```text
SQLite
│
├── incidents
├── observations
├── normalized_events
├── risk_assessments
├── action_proposals
├── approvals
├── audit_events
└── after_action_reports
```

Do not create one vague "memory" object.

Incident state, audit history, and completed scenario history must be logically separate.

PostgreSQL can be introduced later.

Redis should NOT be introduced unless actually required.

---

# 22. AUDIT LOG

Every important transition must be recorded.

Example:

```text
10:32:01
FortyGuard observation received

10:32:03
Weather observation received

10:32:05
Heat event verified

10:32:06
Risk changed MODERATE → HIGH

10:32:07
Supervisor activated Civilian Agent

10:32:09
Action proposal generated

10:32:10
Human approval requested

10:32:20
Operator APPROVED

10:32:22
Simulated response activated

10:34:10
Road blockage detected

10:34:11
REPLAN triggered

10:34:14
Route v2 generated
```

Audit events should be immutable.

---

# 23. API

Use REST + WebSocket.

## Location

```http
POST /api/location
```

Set monitored location.

---

## Current Incident

```http
GET /api/incidents/current
```

Return:

* incident
* observations
* risk
* action proposal
* routes
* audit timeline

---

## Specific Incident

```http
GET /api/incidents/{incident_id}
```

---

## Approval

```http
POST /api/incidents/{incident_id}/approval
```

Payload:

```json
{
  "decision": "approved",
  "comment": "Approved for simulation"
}
```

---

## Simulation

```http
POST /api/simulations/{scenario}
```

Available:

```text
normal_conditions
heat_escalation
smoke_report
road_blockage
```

---

## Resolve

```http
POST /api/incidents/{incident_id}/resolve
```

---

## After Action Report

```http
GET /api/incidents/{incident_id}/aar
```

Generate/download PDF.

---

## WebSocket

```text
/ws/incidents/{incident_id}
```

Push:

* risk updates
* new observations
* agent status
* approval state
* route changes
* audit events

---

# 24. SIMULATION SYSTEM

Simulation must be a first-class system feature.

It must not be treated as an embarrassing fallback.

Dashboard should contain:

```text
SIMULATION CONSOLE

[ Normal Conditions ]

[ Escalate Heat ]

[ Inject Smoke Report ]

[ Block Main Route ]

[ Reset Scenario ]
```

Every simulation event must visibly contain:

```text
Data Mode: SIMULATED
```

Simulation scenarios must be deterministic and reproducible.

---

# 25. FRONTEND

Use:

```text
Vite
React
TypeScript
Vanilla CSS
```

Do not use a large UI framework unless necessary.

Dashboard sections:

```text
┌─────────────────────────────────────────────┐
│ HRES HEADER                                 │
│ System Status | Data Mode | Incident ID    │
├───────────────────┬─────────────────────────┤
│                   │                         │
│     LIVE MAP      │    RISK INDICATOR      │
│                   │                         │
├───────────────────┼─────────────────────────┤
│ SOURCE            │ INCIDENT / AGENTS       │
│ VERIFICATION      │                         │
├───────────────────┼─────────────────────────┤
│ AUDIT TIMELINE    │ HUMAN APPROVAL         │
├───────────────────┴─────────────────────────┤
│ SIMULATION CONSOLE                          │
└─────────────────────────────────────────────┘
```

---

# 26. DESIGN

Visual style:

* dark operational command-center interface
* premium but readable
* subtle glassmorphism
* clear information hierarchy
* restrained micro-animations
* high contrast
* no unnecessary decorative elements

Risk colors should communicate meaning consistently.

Risk indicator:

```text
LOW
MODERATE
HIGH
CRITICAL
```

The user should understand system state within 2–3 seconds.

Do not overdesign.

Functionality is more important than visual effects.

---

# 27. SOURCE VERIFICATION GRID

Show:

```text
SOURCE              STATUS       MODE

FortyGuard          ✓            LIVE
Open-Meteo          ✓            LIVE
User Report         ✓            SIMULATED
Maps                ✓            SIMULATED
Gemini              ✓            AVAILABLE
```

Possible states:

```text
LIVE
CACHED
SIMULATED
UNAVAILABLE
ERROR
```

Never hide simulated data.

---

# 28. ERROR HANDLING

All external API calls must have explicit:

* connection timeout
* read timeout
* error handling
* fallback behavior
* logging

Use `httpx.AsyncClient`.

Recommended timeout:

```text
connect timeout
read timeout
write timeout
overall reasonable timeout
```

Retries:

* GET/read operations may retry
* use exponential backoff
* limit retry count

Never blindly retry:

* approval
* notification
* action execution

Those operations must be idempotent or require explicit confirmation.

---

# 29. FORTYGUARD ERROR HANDLING

Known possible failures include:

```text
ConnectionResetError
SSLEOFError
TimeoutError
ConnectionError
HTTP errors
```

These must never crash the application.

Bad:

```text
requests.get(...)
# application crashes if API fails
```

Good:

```text
try
    request live API
except
    mark source unavailable
    use cache/simulation
    continue workflow
```

Never claim:

```text
LIVE
```

when the API failed.

---

# 30. FALLBACK POLICY

Every external dependency must have a clear fallback.

## FortyGuard

```text
LIVE
→ CACHE
→ SIMULATION
→ UNAVAILABLE
```

## Weather

```text
LIVE
→ CACHE
→ SIMULATION
→ UNAVAILABLE
```

## Maps

```text
LIVE
→ STATIC SIMULATION ROUTE
→ UNAVAILABLE
```

## Gemini

```text
Gemini
→ deterministic template
```

## Database

If database fails:

* read-only mode where possible
* disable approval/external action simulation
* continue safety guidance if possible
* log failure

---

# 31. NO FABRICATION RULE

Never fabricate:

* temperature
* sensor readings
* GPS position
* traffic
* hospital availability
* emergency service availability
* API responses

If data is simulated, label it:

```text
SIMULATED
```

If cached:

```text
CACHED — timestamp
```

If unavailable:

```text
UNAVAILABLE
```

---

# 32. AFTER-ACTION REPORT

Generate PDF using ReportLab.

Include:

```text
HRES AFTER-ACTION REPORT

Incident ID
Location
Start time
End time

Timeline

Observed conditions

Sources

Verification results

Risk progression

Agent actions

Human approvals

Route changes

Replanning events

Final response

System limitations

Data modes
```

The report must clearly distinguish:

```text
LIVE
CACHED
SIMULATED
```

If PDF generation fails, provide a readable HTML/Markdown fallback.

---

# 33. TESTING

Use pytest.

Minimum tests:

### Verification

* duplicate detection
* stale data penalty
* source consensus
* source conflict
* confidence calculation

### Risk

* score calculation
* LOW
* MODERATE
* HIGH
* CRITICAL
* deterministic override rules

### Workflow

* correct LangGraph routing
* approval state transitions
* rejection
* modification
* escalation
* replanning

### Simulation

* heat escalation
* smoke report
* road blockage
* reset

### API

* endpoints
* invalid payloads
* error handling
* WebSocket state updates

---

# 34. IMPLEMENTATION PHASES

## Phase 1 — Foundation

Build:

* project structure
* configuration
* Pydantic schemas
* SQLite
* FastAPI
* basic health endpoint

Do NOT start with UI polish.

---

## Phase 2 — Simulation

Build:

* scenario files
* simulation engine
* incident state
* observations
* audit log

The entire demo must work without external APIs.

---

## Phase 3 — Deterministic Intelligence

Build:

* verification.py
* prioritization.py
* confidence calculation
* risk calculation
* conflict handling

Test thoroughly.

---

## Phase 4 — LangGraph

Build:

* state graph
* supervisor
* verification node
* risk node
* civilian agent
* response agent
* civic agent

Use Gemini only where appropriate.

---

## Phase 5 — Human Approval

Build:

* approval endpoint
* approval state machine
* approve
* modify
* reject
* escalate

Only high-impact actions should require approval.

---

## Phase 6 — Replanning

Build:

* route blockage simulation
* route recalculation
* plan versioning
* audit history

---

## Phase 7 — Dashboard

Build:

* risk indicator
* map
* source grid
* incident panel
* agent status
* audit timeline
* approval panel
* simulation console
* report center

---

## Phase 8 — External APIs

Only after simulation works:

* FortyGuard
* Open-Meteo
* Google Maps

Every integration must preserve fallback behavior.

---

## Phase 9 — Hardening

Test:

* API failures
* timeouts
* invalid LLM output
* unavailable database
* duplicate events
* stale events
* conflicting sources
* WebSocket disconnects

---

## Phase 10 — Demo

Final demo:

```text
START
 ↓
Normal Conditions
 ↓
Heat Escalation
 ↓
Verification
 ↓
HIGH/CRITICAL Risk
 ↓
Smoke Report
 ↓
Cross-source Verification
 ↓
Action Proposal
 ↓
Human Approval
 ↓
Simulated Response
 ↓
Road Blockage
 ↓
REPLAN
 ↓
New Route
 ↓
Resolve
 ↓
AAR PDF
```

---

# 35. MVP BOUNDARY

Do NOT build:

* real emergency dispatch
* real ambulance calls
* real fire department communication
* real SMS emergency broadcasts
* medical diagnosis
* autonomous emergency decisions
* complex authentication
* multi-tenant architecture
* Kubernetes
* microservices
* Redis unless required
* PostgreSQL unless SQLite becomes a blocker
* complex route optimization algorithms
* unnecessary AI agents
* unnecessary external APIs

The goal is a convincing, reliable hackathon prototype.

---

# 36. DEFINITION OF DONE

HRES is considered complete when:

1. Application starts successfully.
2. Dashboard loads.
3. Simulation can create an incident.
4. Heat observations are displayed.
5. Weather observations are displayed.
6. Data modes are visible.
7. Verification works deterministically.
8. Risk score is deterministic.
9. Risk level updates in real time.
10. LangGraph routes agents conditionally.
11. Gemini generates structured explanations/actions.
12. Gemini failure does not break the system.
13. Human approval works.
14. Road blockage triggers replanning.
15. New route is displayed.
16. Audit timeline records all major events.
17. Incident can be resolved.
18. PDF After-Action Report is generated.
19. External API failure does not crash the demo.
20. No simulated data is presented as live data.

---

# 37. ANTIGRAVITY CODING RULES

When implementing this project:

1. Read all files in `/docs` before modifying architecture.
2. Treat this document as the implementation source of truth.
3. Do not randomly introduce libraries.
4. Do not rewrite working modules without reason.
5. Keep integrations isolated.
6. Keep deterministic safety logic separate from LLM logic.
7. Keep simulation separate from live integrations.
8. Every external API needs timeout and fallback handling.
9. Every LLM response must be validated.
10. Every important state transition must be auditable.
11. Never hide simulated data.
12. Never fabricate unavailable live data.
13. Do not add Docker unless explicitly requested.
14. Do not add PostgreSQL/Redis unless required.
15. Do not build real emergency dispatch functionality.
16. Prefer simple working code over premature abstraction.
17. Complete the simulation MVP before polishing external integrations.
18. Run tests after every major backend change.
19. Keep the frontend connected to real backend APIs rather than hardcoded UI state.
20. Do not claim a feature is complete unless it has been tested.

---

# 38. PRIORITY ORDER

When time is limited, prioritize in this exact order:

```text
P0
Simulation
Deterministic risk engine
FastAPI
Incident state
Dashboard
Audit timeline

P1
LangGraph
Human approval
Replanning
AAR PDF

P2
FortyGuard live integration
Open-Meteo live integration
Google Maps integration

P3
Visual polish
Micro animations
Additional features
```

A fully working P0/P1 system is better than a half-working system containing every API.

---

# 39. FINAL ARCHITECTURAL PRINCIPLE

The central HRES pipeline must remain:

```text
PERCEIVE
   ↓
NORMALIZE
   ↓
VERIFY
   ↓
PRIORITIZE
   ↓
PLAN
   ↓
HUMAN APPROVAL
   ↓
SIMULATED ACTION
   ↓
MONITOR
   ↓
REPLAN IF REQUIRED
   ↓
AUDIT
```

The most important separation is:

```text
                    ┌─────────────────────┐
                    │ DETERMINISTIC CORE  │
                    │                     │
                    │ Verification       │
                    │ Risk               │
                    │ Safety Rules       │
                    │ Approval Policy    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     LANGGRAPH       │
                    │                     │
                    │ Orchestration       │
                    │ Agent Routing       │
                    │ State Management    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │        LLM          │
                    │                     │
                    │ Explanation         │
                    │ Communication       │
                    │ Draft Plans         │
                    │ Reports             │
                    └─────────────────────┘
```

The LLM assists the system.

The LLM does not control the safety-critical system.
