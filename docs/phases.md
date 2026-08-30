# HRES — Development Phases

## Development Strategy

HRES will be built in three passes:

1. **Learning prototype** — Prakash writes the core feature step-by-step and understands it.
2. **Functional MVP** — connect features into an end-to-end demo.
3. **Production hardening** — Antigravity refactors/hardens; the resulting code is reviewed and explained again.

Do not build the entire final architecture before the previous layer works.

---

## Phase 0 — Planning

Status: **Completed**

- Define HRES concept.
- Freeze architecture.
- Define MVP.
- Define safety boundaries.
- Define technology stack.
- Define user experience.

---

## Phase 1 — Foundation

Goal:

> Python → FortyGuard → normalized HRES data.

Tasks:
1. Project/venv setup.
2. `.env` and secret handling.
3. Install `requests` and `python-dotenv`.
4. Connect to FortyGuard.
5. Understand API response.
6. Create a basic HRES event.
7. Add location context.
8. Support fixed test location before automatic location.

Milestone:

```text
Location → FortyGuard → HRES Event
```

---

## Phase 2 — Perception + Verification

Goal:

> Turn multiple observations into trustworthy event information.

Tasks:
1. Add weather source.
2. Create source adapters.
3. Normalize source responses.
4. Compare sources.
5. Detect duplicate reports.
6. Handle conflicting/stale data.
7. Calculate confidence.

Milestone:

```text
Multiple Sources → Verification → Confidence
```

---

## Phase 3 — Risk + Prioritization

Goal:

> Decide how serious an event is and what needs attention first.

Tasks:
1. Deterministic heat-risk rules.
2. Exposure calculation.
3. Vulnerability/exposure prioritization.
4. Severity levels.
5. Risk score.
6. Explainable reason for each priority.
7. Pydantic risk model.

Milestone:

```text
Event → Risk + Priority + Explanation
```

---

## Phase 4 — FastAPI Foundation

Goal:

> Expose HRES functionality through a backend API.

Tasks:
1. FastAPI app.
2. Health endpoint.
3. Location endpoint.
4. Heat/risk endpoint.
5. Incident endpoint.
6. Pydantic request/response schemas.
7. Error handling.

Milestone:

```text
Client → FastAPI → HRES services
```

---

## Phase 5 — LangGraph Supervisor

Goal:

> Convert the pipeline into an agentic stateful workflow.

Tasks:
1. Understand graph/state/node/edge.
2. Create HRES state.
3. Add perception node.
4. Add verification node.
5. Add risk node.
6. Add Supervisor.
7. Add conditional routing.
8. Add tool calls.
9. Add safe termination.

Milestone:

```text
State → Nodes → Decisions → Supervisor
```

---

## Phase 6 — Multi-Agent Response

Goal:

> Introduce specialized agents.

Tasks:
1. Verification Agent.
2. Response Agent.
3. Civilian Agent.
4. Civic Agent.
5. Tool boundaries.
6. Shared state.
7. Structured outputs.

Milestone:

```text
Supervisor
 ├─ Response
 ├─ Civilian
 └─ Civic
```

---

## Phase 7 — Routing + Facilities

Goal:

> Provide actionable routes and facilities.

Tasks:
1. Maps integration.
2. Civilian route.
3. Responder route.
4. Ambulance route.
5. Hospital lookup.
6. Cooling-center lookup.
7. Route risk scoring.
8. Route failure fallback.

Milestone:

```text
Incident → Safe/fast route + Hospital/Cooling Center
```

---

## Phase 8 — Human-in-the-Loop

Goal:

> Put a clear control boundary before high-impact action.

Tasks:
1. Action proposal.
2. Approval state.
3. Approve.
4. Modify.
5. Reject.
6. Escalate.
7. Audit every decision.

Milestone:

```text
AI Proposal → Human → Action
```

---

## Phase 9 — Continuous Monitoring + Replanning

Goal:

> Make HRES genuinely adaptive.

Tasks:
1. Monitoring loop.
2. New observation ingestion.
3. State update.
4. Change detection.
5. REPLAN.
6. REPLAN → Supervisor.
7. Updated routes.
8. Updated alerts.
9. Incident resolution.

Milestone:

```text
Monitor → Change → Replan → Supervisor → New Plan
```

---

## Phase 10 — Memory + AAR

Goal:

> Preserve incident history and produce useful post-event analysis.

Tasks:
1. Persistent incident storage.
2. Audit log.
3. Feedback storage.
4. Historical context.
5. Incident resolution.
6. After-Action Report.
7. PDF generation.

Milestone:

```text
Incident → History → AAR → Learn/Improve
```

---

## Phase 11 — What-if Simulation

Goal:

> Make the hackathon demo controllable and repeatable.

Simulations:
- extreme heat;
- sudden heat increase;
- smoke report;
- conflicting reports;
- route blockage;
- changing environmental condition;
- hospital/cooling-center route change.

Milestone:

```text
Scenario → Agents → Approval → Response → Replan
```

---

## Phase 12 — Frontend

Goal:

> Build the HRES operational dashboard.

Panels:
- current location;
- searched location;
- heat/risk card;
- map;
- incidents;
- source verification;
- confidence;
- agent state;
- proposed actions;
- approval controls;
- live timeline;
- route information;
- report download.

---

## Phase 13 — Production Hardening

Tasks:
- architecture refactor;
- async external calls where appropriate;
- database;
- authentication/authorization;
- rate limiting;
- retries/timeouts;
- structured logging;
- metrics;
- tests;
- Docker;
- deployment;
- security review;
- dependency review.

---

## Phase 14 — Final Hackathon Demo

Demo sequence:

```text
1. User location detected
2. HRES shows current heat state
3. Incident/simulated fire signal appears
4. Multiple sources are checked
5. Risk + vulnerability priority is calculated
6. Supervisor creates a plan
7. Routes/hospital/cooling center are generated
8. Human approves
9. Alerts/actions are shown
10. Condition changes
11. HRES replans
12. Supervisor issues updated plan
13. Incident resolves
14. AAR is generated
```
