# HRES — Application Flow

## 1. Startup

```text
Open HRES
   ↓
Check permissions/configuration
   ↓
Get current location if permitted
   ↓
Load monitoring state
   ↓
Start perception
```

## 2. Current Location Flow

```text
Current GPS
   ↓
Location Context
   ↓
FortyGuard
   ↓
Weather
   ↓
Maps/other configured sources
   ↓
Normalize observations
   ↓
Verification
   ↓
Risk + vulnerability/exposure priority
   ↓
Supervisor
```

## 3. Normal Condition

```text
Low risk
  ↓
Show status
  ↓
Continue monitoring
  ↓
New observation
  ↓
Recalculate
```

## 4. High-Risk Condition

```text
High risk
   ↓
Supervisor
   ↓
Civilian guidance
   ↓
Cooling center / hospital / safe route
   ↓
Human approval if high-impact action is proposed
   ↓
Notification/action
   ↓
Monitor
```

## 5. Possible Fire Flow

```text
Heat anomaly / smoke report
          ↓
Verification
          ↓
Independent evidence?
     ┌────┴────┐
    NO         YES
     │          │
 Monitor    Increase confidence
     │          │
     └────┬─────┘
          ↓
     Risk priority
          ↓
      Supervisor
          ↓
     Action proposal
          ↓
   Human approval
          ↓
   Simulated/authorized action
          ↓
 Continuous monitoring
```

## 6. Ambulance/Hospital Flow

```text
Severe user condition / emergency incident
              ↓
Civilian Agent
              ↓
Need medical assistance?
              ↓
             YES
              ↓
Find suitable nearby hospital
              ↓
Routing tool
              ↓
Fastest safe route
              ↓
Prepare ambulance/medical notification
              ↓
Human approval where required
```

## 7. Replanning Flow

```text
Active incident
     ↓
Monitor
     ↓
New observation
     ↓
Important change?
   ┌──┴──┐
  NO     YES
  │       │
State     REPLAN
update      ↓
        SUPERVISOR
            ↓
        New decision
            ↓
       New plan/routes
            ↓
       Updated alerts
            ↓
        Continue
```

## 8. Search Location Flow

```text
User searches "College"
        ↓
Resolve location
        ↓
Set temporary analysis context
        ↓
Collect sources
        ↓
Analyze
        ↓
Display remote location state
```

## 9. Incident Resolution

```text
Conditions normalize
      ↓
Supervisor verifies resolution
      ↓
Mark incident resolved
      ↓
Persist final state
      ↓
Generate AAR
      ↓
Store lessons/improvement observations
```
