# HRES — Architecture

## 1. Architecture Principle

HRES is a stateful, event-driven, multi-agent system.

The system is not a chatbot. It is a closed-loop workflow:

```text
Perceive
   ↓
Normalize
   ↓
Verify
   ↓
Prioritize
   ↓
Supervisor
   ↓
Specialized Agents
   ↓
Human Approval
   ↓
Action / Notification
   ↓
Continuous Monitoring
   ↓
Replan → Supervisor
   ↓
Live State + Audit
   ↓
Incident Resolved
   ↓
After-Action Report
```

## 2. High-Level Architecture

```text
                         HRES
                          │
                          ▼
                ┌─────────────────────┐
                │ LOCATION CONTEXT    │
                │ Auto GPS / Search   │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ MULTI-SOURCE        │
                │ PERCEPTION          │
                │ FortyGuard          │
                │ Weather / Sensors   │
                │ User Reports        │
                │ Maps / Traffic      │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ EVENT NORMALIZATION  │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ VERIFICATION AGENT  │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ RISK + VULNERABILITY│
                │ PRIORITIZATION      │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ SUPERVISOR AGENT    │
                │ LangGraph           │
                └──────────┬──────────┘
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
       Response Agent  Civilian Agent  Civic Agent
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                ┌─────────────────────┐
                │ HUMAN APPROVAL GATE │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ NOTIFICATION/ACTION │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ CONTINUOUS MONITOR  │
                └──────────┬──────────┘
                           │
                    Condition changed?
                      ┌────┴────┐
                     NO         YES
                      │          │
                      ▼          ▼
                 Update State  REPLAN
                                  │
                                  ▼
                             SUPERVISOR
                                  │
                                  ▼
                            Updated Plan
                                  │
                                  ▼
                           Updated Alerts
```

## 3. Main Components

### Location Context
- Automatic browser/device location with permission.
- Search/manual location for remote monitoring.
- Produces a normalized location context.

### Perception Layer
Adapters for external information sources.

### Event Normalizer
Converts heterogeneous source responses into HRES domain events.

### Verification Agent
Cross-source validation, duplicate detection, stale-data handling, and confidence adjustment.

### Risk + Vulnerability Prioritizer
Produces risk/severity/priority using deterministic rules plus carefully bounded AI reasoning.

### Supervisor Agent
LangGraph orchestration layer. Owns workflow transitions and replanning.

### Specialized Agents
- Response Agent
- Civilian Agent
- Civic Agent

### Human Approval Gate
A mandatory boundary for high-impact actions.

### Continuous Monitoring
Polls/subscribes to new observations depending on the source.

### Replan
Feeds changed state directly back to the Supervisor.

### Live State + Audit Log
Preserves the current incident state and immutable decision/action history.

### After-Action Report
Summarizes the complete incident lifecycle.

## 4. Agent Boundaries

### Supervisor
Responsible for:
- orchestration;
- selecting next workflow step;
- delegating;
- exception routing;
- approval gating;
- replanning.

Not responsible for:
- directly calling every external API;
- inventing sensor data;
- making unsupported medical claims.

### Verification Agent
Responsible for evidence correlation and confidence.

### Response Agent
Responsible for response planning and route/tool preparation.

### Civilian Agent
Responsible for user-facing safety communication and facility/route recommendations.

### Civic Agent
Responsible for structured institutional reporting.

## 5. State Model

Conceptual state:

```python
{
    "incident_id": "...",
    "location": {...},
    "observations": [...],
    "normalized_event": {...},
    "verification": {...},
    "risk": {...},
    "plan": {...},
    "approval": {...},
    "actions": [...],
    "feedback": [...],
    "status": "...",
    "audit": [...]
}
```

LangGraph owns workflow state; PostgreSQL persists durable application state.

## 6. Data Flow

```text
External Source
      ↓
Adapter/Tool
      ↓
Raw Observation
      ↓
Normalizer
      ↓
HRES Event
      ↓
Verification
      ↓
Risk/Priority
      ↓
Supervisor
      ↓
Agent/Tool
      ↓
Action Proposal
      ↓
Human Approval
      ↓
Action
      ↓
New Observation
      ↓
Replan if needed
```

## 7. Failure Boundaries

External API failure must not crash the workflow.

Examples:
- FortyGuard unavailable → use cached/secondary data and lower confidence.
- Weather unavailable → continue with available sources and mark missing evidence.
- Maps unavailable → no fabricated ETA; use a fallback or clearly state route unavailable.
- LLM unavailable → deterministic safety rules continue where possible.
- Database unavailable → fail safely and surface operational error; never silently lose critical audit events.

## 8. Technology Stack

| Layer | Technology |
|---|---|
| Language | Python |
| API backend | FastAPI |
| Agent orchestration | LangGraph |
| Data validation | Pydantic |
| LLM | Configurable Gemini/OpenAI/local model |
| Heat intelligence | FortyGuard Temperature API |
| Weather | Open-Meteo or configured weather provider |
| Routing/maps | Google Maps Platform / configured routing provider |
| Database | PostgreSQL |
| Cache/queue (as needed) | Redis |
| Real-time frontend updates | WebSockets |
| Frontend | React |
| PDF/AAR | ReportLab |
| Configuration | python-dotenv / environment variables |
| HTTP client | requests initially; async client for production where appropriate |
| Testing | pytest |
| Packaging/deployment | Docker |

## 9. Project Structure

```text
HRES/
├── app/
│   ├── main.py
│   ├── api/
│   ├── core/
│   ├── agents/
│   ├── services/
│   ├── tools/
│   ├── models/
│   └── workflows/
├── frontend/
├── tests/
├── docs/
├── scripts/
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── PRD.md
├── ARCHITECTURE.md
├── RULES.md
├── PHASES.md
└── DESIGN.md
```

The learning prototype may begin with fewer files and be refactored later.
