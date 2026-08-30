# HRES — Product Requirements Document

## 1. Product Name

**HRES — Heat Response Emergency System**

## 2. Vision

HRES is an agentic, human-supervised emergency response system that continuously monitors a user's surroundings for heat and related environmental risks, verifies events using multiple information sources, prioritizes risk and vulnerable/exposed populations, recommends and coordinates appropriate responses, and dynamically replans when conditions change.

The core loop is:

> **Perceive → Normalize → Verify → Prioritize → Decide → Approve → Act → Monitor → Replan → Remember → Learn**

## 3. Problem

Extreme heat can become an emergency when high temperature combines with exposure, vulnerable populations, changing environmental conditions, traffic/access constraints, or a verified fire/emergency event.

Most simple heat applications only display temperature or provide a static warning. HRES aims to reduce the human effort required to understand what is happening and decide what to do next.

The system should proactively answer:

- Is something wrong around me?
- How serious is it?
- How confident are we?
- Who/what is most at risk?
- What should civilians do?
- What route is safer?
- What should responders know?
- Has anything changed since the last decision?

## 4. Target Users

### Primary
- Civilians/users monitoring their current surroundings.
- Users checking another location such as a college, workplace, home, or public facility.

### Secondary
- Emergency-response coordinators.
- Campus/security administrators.
- Government/NGO/public-safety teams.

### Demo/MVP Context
A controlled simulated emergency scenario will be used for high-impact actions. HRES must not automatically place real emergency calls.

## 5. Core User Experience

### Automatic location mode
1. User grants location permission.
2. HRES obtains the current location.
3. HRES observes the surrounding area using configured data sources.
4. HRES continuously evaluates the current state.
5. If risk crosses configured thresholds, HRES creates/updates an incident and presents an actionable alert.

### Search location mode
1. User searches for another location.
2. HRES analyzes that location.
3. HRES displays heat/risk conditions, incidents, nearby relevant facilities, and recommended actions.
4. The user can compare or inspect locations without physically being there.

## 6. Functional Requirements

### FR-01 Location Context
- Support automatic current location with explicit user permission.
- Support manual/search location.
- Store location with timestamp and source.
- Clearly indicate data age and location mode.

### FR-02 Multi-Source Perception
Initial sources:
- FortyGuard Temperature API.
- Weather/environmental source.
- Map/traffic/routing source.
- User reports.
- Simulated sensor/fire signals for the hackathon demo.

The architecture must allow additional sources later.

### FR-03 Event Normalization
Every incoming event should be converted into a common structure containing at minimum:
- event_id
- event_type
- location
- timestamp
- source(s)
- observed values
- confidence
- status

### FR-04 Verification
The Verification Agent should:
- cross-check independent sources;
- identify duplicate reports;
- identify conflicting information;
- reduce confidence when data is stale or unavailable;
- prevent a single unverified signal from automatically triggering high-impact external actions.

### FR-05 Risk + Vulnerability Prioritization
Risk prioritization combines:
- severity;
- exposure;
- population/vulnerability;
- confidence;
- duration/rate of change;
- accessibility/route constraints where applicable.

Vulnerability and exposure are treated together as a prioritization concern rather than separate major systems.

### FR-06 Supervisor Agent
A LangGraph-based Supervisor coordinates the workflow:
- chooses the next step;
- invokes specialized agents/tools;
- handles exceptions;
- enforces approval boundaries;
- receives replanning feedback;
- maintains workflow state.

### FR-07 Response Agent
The Response Agent can:
- prepare responder information;
- calculate/suggest firefighter routes;
- calculate/suggest ambulance routes;
- coordinate simulated emergency notifications;
- update response plans.

### FR-08 Civilian Agent
The Civilian Agent can:
- issue severity-appropriate alerts;
- provide calm, actionable guidance;
- identify cooling centers;
- identify suitable nearby hospitals;
- recommend safer routes;
- provide conservative heat-safety guidance.

### FR-09 Civic Agent
The Civic Agent can:
- generate structured incident reports;
- prepare NGO/government notifications;
- summarize affected area and response state.

### FR-10 Human Approval
High-impact actions must pass a human approval gate in the MVP:
- approve;
- modify;
- reject;
- escalate.

The system is decision support, not a replacement for emergency authorities.

### FR-11 Continuous Monitoring
HRES must be able to receive new observations after an action.

### FR-12 Dynamic Replanning
If important conditions change:
- create a replan event;
- send the new state directly to the Supervisor;
- generate an updated plan;
- update routes and alerts;
- record the change in the audit log.

### FR-13 Memory and Audit
Store:
- current live state;
- incident history;
- decisions;
- approvals;
- actions;
- feedback;
- route changes;
- timestamps.

Memory is used for contextual continuity and historical review; automatic model retraining is out of MVP scope.

### FR-14 After-Action Report
After incident resolution, generate an After-Action Report containing:
- incident timeline;
- sources;
- confidence changes;
- risk decisions;
- actions taken;
- approvals;
- route changes;
- outcome;
- lessons/improvement points.

### FR-15 What-if Simulation
Provide controlled simulations for demo/testing, such as:
- sudden temperature increase;
- smoke report;
- route blockage;
- wind/condition change;
- secondary hazard.

## 7. Non-Functional Requirements

- Secure API-key handling.
- Input validation.
- Structured errors.
- Timeouts and retries for external APIs.
- Observability and audit logging.
- Deterministic rules for safety-critical thresholds where possible.
- LLM outputs must be validated before use.
- High-impact actions require explicit approval.
- Graceful degradation when an external API is unavailable.
- Clear distinction between observed data, inferred risk, and generated guidance.

## 8. MVP Scope

The first polished demo should focus on one end-to-end scenario:

1. Automatic/current or selected location.
2. FortyGuard heat data.
3. Additional environmental source.
4. Event normalization.
5. Verification.
6. Risk + vulnerability/exposure prioritization.
7. Supervisor decision.
8. Simulated emergency/fire signal.
9. Human approval.
10. Civilian alert and guidance.
11. Responder and ambulance route recommendation.
12. Hospital/cooling-center lookup.
13. Continuous monitoring.
14. Dynamic replan back to Supervisor.
15. Live state/audit log.
16. After-Action Report.

## 9. Explicit Non-Goals

For the hackathon MVP:
- No autonomous real emergency calls.
- No autonomous dispatch of real firefighters/ambulances.
- No claim that temperature alone proves a fire.
- No automatic medical diagnosis.
- No automatic model retraining.
- No dependence on an LLM for deterministic safety thresholds.
- No unnecessarily large microservice architecture.

## 10. Success Criteria

A successful demo should show:

> A location is monitored → a meaningful event is detected → multiple sources are checked → risk is prioritized → a plan is created → a human approves it → actions/alerts are prepared → conditions change → HRES replans through the Supervisor → the incident is resolved → an AAR is generated.

## 11. Product Principle

**Minimum human effort, maximum appropriate human control.**

HRES should automate observation, correlation, planning, communication preparation, and replanning while keeping high-impact decisions under human supervision.
