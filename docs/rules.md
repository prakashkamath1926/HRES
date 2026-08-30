# HRES — Engineering Rules

## 1. Core Rule

**Understand first, automate second, productionize third.**

The learning implementation should remain understandable. Production refactoring must preserve behavior and improve reliability rather than obscure the system.

## 2. Libraries — Use

### Core
- Python
- FastAPI
- Pydantic
- LangGraph
- requests initially
- python-dotenv
- pytest

### Data/Infrastructure
- PostgreSQL
- Redis only when a concrete need exists
- Docker for production packaging

### Frontend
- React
- WebSockets for live updates where required

### Documents
- ReportLab for AAR PDF generation

## 3. Libraries — Avoid Unless Justified

Do not add a library simply because it is popular.

Avoid:
- multiple overlapping HTTP clients without a reason;
- multiple agent frameworks;
- unnecessary vector databases;
- unnecessary orchestration/queue systems;
- heavyweight ML frameworks when deterministic Python is sufficient;
- Streamlit as the final product UI;
- scraping when an official API exists;
- hidden/global state;
- deprecated packages.

Every new dependency should answer:
1. What problem does it solve?
2. Why can't existing dependencies solve it?
3. Does it increase operational complexity?
4. Is it maintained and compatible with the project?

## 4. API Key Rules

Never hard-code secrets.

Use:
```text
.env
```

and environment variables.

Never:
- commit `.env`;
- print secrets;
- return secrets from API endpoints;
- include secrets in screenshots/logs;
- place keys in frontend code.

## 5. Error Handling

External calls must use:
- timeout;
- explicit status handling;
- bounded retries where safe;
- structured errors;
- logging without secrets;
- fallback/degraded behavior where possible.

Never:
```python
except Exception:
    pass
```

Do not silently swallow errors.

Prefer specific exceptions and meaningful error messages.

## 6. AI Boundaries

The LLM must NOT be the sole authority for:
- emergency severity thresholds;
- whether a fire is actually confirmed;
- medical diagnosis;
- emergency-service dispatch authorization;
- legal/regulatory decisions;
- raw numerical calculations that can be deterministic.

Use deterministic code/rules for safety-critical checks.

Use the LLM for:
- synthesis;
- explanation;
- classification where appropriate;
- planning proposals;
- report generation;
- natural-language communication.

## 7. AI Output Validation

Never directly trust an LLM response.

Use:
- Pydantic schemas;
- enums;
- constrained fields;
- confidence/source metadata;
- validation before tool execution.

Invalid AI output must be rejected or safely converted to a review state.

## 8. Human-in-the-Loop Boundary

Human approval is required before high-impact external actions in the MVP.

The system may:
- detect;
- analyze;
- propose;
- prepare;
- simulate.

The system must not autonomously:
- call real emergency services;
- dispatch real responders;
- issue official evacuation orders;
- diagnose medical emergencies.

## 9. Fire Detection Boundary

Heat alone does not prove a fire.

Fire-related events require independent evidence such as:
- authorized sensor;
- camera/smoke signal;
- verified report;
- official emergency information;
- controlled simulation for demo.

The UI must distinguish:
- possible;
- likely;
- verified.

## 10. Medical Boundary

HRES is not a medical diagnostic system.

Guidance must be:
- conservative;
- actionable;
- non-diagnostic;
- escalation-oriented for severe symptoms.

For serious symptoms, direct the user toward emergency/medical assistance.

Do not invent medication, dosage, or treatment.

## 11. Routing Boundary

Never fabricate:
- route;
- ETA;
- road status;
- hospital availability.

If the routing provider fails, clearly show that route data is unavailable or use an explicitly defined fallback.

## 12. Confidence Rules

Confidence should represent evidence quality, not AI certainty.

Confidence must consider:
- number of independent sources;
- source reliability;
- freshness;
- agreement/conflict;
- missing information.

A low-confidence event must not automatically trigger a high-impact action.

## 13. Data Freshness

Every external observation should have:
- source;
- timestamp;
- retrieval time;
- data age where possible.

Stale data lowers confidence.

## 14. State and Memory

Short-term workflow state belongs in LangGraph state.

Durable incident history belongs in persistent storage.

Do not confuse:
- memory with training;
- historical records with automatic model learning.

## 15. Replanning

When important state changes:

```text
New observation
    ↓
Update state
    ↓
REPLAN
    ↓
Supervisor
    ↓
New plan
```

REPLAN must feed directly to the Supervisor.

## 16. Logging and Audit

Log:
- event ID;
- workflow transition;
- tool used;
- decision;
- approval;
- error;
- timestamp.

Never log:
- API keys;
- passwords;
- unnecessary personal information.

## 17. Privacy

Location is sensitive operational data.

Use:
- explicit permission;
- minimal retention;
- clear user controls;
- secure transport/storage;
- no unnecessary sharing.

## 18. Testing Rules

Test:
- normal flow;
- API failure;
- stale data;
- conflicting sources;
- duplicate events;
- invalid AI output;
- route failure;
- replan;
- human rejection;
- incident resolution.

Safety boundaries require deterministic tests.

## 19. Production Rule

Prototype first, productionize second.

Antigravity may refactor after a feature is understood and working. Production refactoring must not introduce:
- hidden behavior;
- unnecessary abstractions;
- unbounded agent loops;
- uncontrolled external actions.

## 20. Definition of Done

A feature is done when:
1. It works.
2. Its behavior is understood.
3. Errors are handled.
4. Inputs/outputs are validated.
5. It has tests where appropriate.
6. It does not expose secrets.
7. It respects HRES safety boundaries.
8. It can be observed/debugged.
