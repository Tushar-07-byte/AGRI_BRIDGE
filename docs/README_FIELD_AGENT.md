# AgriBridge Field Agent Human-in-the-Loop Architecture

## 1. System Mission
The AgriBridge Field Agent module integrates human-in-the-loop agronomic expertise into the automated AI monitoring pipeline. Rather than replacing the AI or overwhelming agents with routine data, it acts as a selective verification and safety layer for:
1. **Low-Confidence Disease Detections**: Gating chemical recommendations until verified in the field.
2. **IoT Sensor Anomalies**: Investigating impossible readings, missing signals, or zero values without naive assumptions.
3. **Critical Multi-Farm Risks**: Validating high-severity regional pest/disease outbreaks.

---

## 2. Core Operational Flow
```
AI Engine / IoT Sensors
         ↓
Confidence Gate / Anomaly Filter
         │
         ├── NORMAL / HIGH CONFIDENCE → Standard Automated Advisory
         │
         └── UNCERTAIN / ANOMALY → Field Agent Escalation Task (PENDING)
                                          ↓
                                    [ ACCEPT / REJECT ]
                                          ↓
                                     Field Visit
                                          ↓
                                  Verification Report
                                          ↓
                              Unlocked Verified Advisory
```

---

## 3. Directory Layout
- `backend/app/field_agent/config/`: Configurable thresholds and routing rules.
- `backend/app/field_agent/schemas/`: Formal JSON schemas for tasks, reports, events, and statuses.
- `backend/app/field_agent/examples/`: Canonical JSON examples for high/low confidence, anomalies, accept/reject, and delivery.
- `backend/app/services/field_agent_engine.py`: Engine evaluating confidence, telemetry, and managing task lifecycles.
- `backend/app/services/notification_delivery_service.py`: Real-time notification lifecycle and delivery tracking service.

