# AgriBridge — System Architecture Specification
**Smart Horizon 2026 | Problem Statement: SH-AGR-001 / AGR-001**

---

## 1. Architectural Philosophy & Core Tenets

AgriBridge follows a layered, multi-agent architecture where AI models serve as diagnostic advisors, but **only the deterministic policy engine possesses execution authority**.

### Fundamental Architectural Rules:
1. **Sole Decision Authority**: The MultiSignalPolicyEngine evaluates all agronomic signals deterministically. LLMs and deep learning models cannot create executable spray/irrigation tasks directly.
2. **Immutable Farm Context**: Signals are captured as traceable objects (TraceableSignal) with timestamp, confidence, and source metadata, ensuring 100% auditability.
3. **Strict 4-State PlanTask Lifecycle**: Plan tasks strictly progress through PENDING -> ACKNOWLEDGED -> IN_PROGRESS -> COMPLETED.
4. **Human-in-the-Loop Safety**: Diagnostic confidence below 65% triggers automatic escalation to human field agents, freezing autonomous execution.
5. **Truth Hierarchy in Voice Guidance**: Kisan Saathi strictly follows:
   - Level 1: Latest active replanned decision
   - Level 2: Latest trusted telemetry / weather
   - Level 3: Active plan steps
   - Level 4: Historical advisory

---

## 2. Multi-Layer Component Overview

### Layer 1: Ingestion & Telemetry
- **IoT Sensors**: Ingests soil moisture (%), soil temperature (°C), NPK values, electrical conductivity.
- **Weather API (Open-Meteo)**: Fetches real-time temperature, precipitation probability, humidity, and wind speed.
- **Computer Vision Engine**: EfficientNet-B0 architectures for Wheat, Rice, Tomato, and Potato leaf pathology.

### Layer 2: Deterministic Decision Core (MultiSignalPolicyEngine)
Evaluates:
- Pathogen Severity + Confidence Score
- Soil Moisture vs Critical Crop Thresholds (e.g. Wheat CRI stage: 45-65%)
- 24-48h Rainfall & Wind Speed Forecasts
- Growth Stage Constraints (e.g. Flowering, Tillering, Maturity)

Outputs one of four deterministic decisions:
- ALLOWED: Autonomous execution permitted; generates scheduled tasks.
- DEFERRED: Unfavorable conditions (e.g. rain predicted); reschedules with reason.
- BLOCKED: Extreme hazard (e.g. severe waterlogging); forbids action.
- ESCALATED: Borderline confidence (<65%); routes to Field Agent Queue.

### Layer 3: Orchestration & Lifecycle Engine
- Automatically maintains task queues.
- Polls for weather updates and dynamically recalculates spray windows.
- Resolves conflicts between newly generated plans and legacy tasks.

### Layer 4: Human-in-the-Loop Escalation
- Field Agent review dashboard (ield-agent-dashboard.html).
- One-click approve/reject/override with immutable audit logs.

### Layer 5: Multilingual Voice Companion (Kisan Saathi)
- 14 Indian languages + Hinglish.
- Automatic script-based and phoneme language detection.
- Context-aware UI screen navigation and button explanation.
- Zero-hallucination boundary defense against chemical/out-of-scope queries.

---

## 3. Database Schema Overview (14 Relational Models)

1. users: Authentication, bcrypt password hashes, roles (armer, ield_agent, uyer, dmin).
2. armers: Farmer profile, primary district, state, acreage, contact info.
3. ields: Field parcels, soil type, irrigation infrastructure, geo-coordinates.
4. disease_records: Vision diagnosis logs, predicted pathogen, confidence, image URI, verification status.
5. ction_plans: Generated agronomic plans, crop ID, decision JSON, versioning.
6. plan_tasks: Concrete actionable steps, 4-state status, due dates, execution logs.
7. ield_agent_escalations: Borderline reviews, assigned officer, resolution notes, override values.
8. crop_listings: Farmer marketplace listings, quantity, base price, harvested date.
9. ids: Buyer bids, price per quintal, status (pending, ccepted, 
ejected).
10. sensor_telemetry: IoT sensor data streams, timestamps, battery health.
11. weather_logs: Cached weather forecasts and rain alerts.
12. 
otifications: Actionable farmer alerts and SMS/push dispatch logs.
13. udit_logs: Immutable security and decision audit events.
14. oice_sessions: Multi-turn voice interaction histories and detected contexts.
