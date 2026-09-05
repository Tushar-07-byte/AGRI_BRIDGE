# AgriBridge AI
# Ultra Crop Monitoring + IoT Telemetry
# FINAL AI/ML → BACKEND HANDOFF

======================================================================
PROJECT STATUS
======================================================================

AI/ML monitoring subsystem: READY
Backend integration contract: READY
Backend-callable engine: READY
Marketplace pre-harvest integration: READY

======================================================================
SYSTEM CAPABILITIES
======================================================================

1. Dynamic Crop Stage Engine
2. Stage-Specific Crop Management
3. Daily Monitoring Decision Engine
4. Live Weather Integration
5. IoT Telemetry Processing
6. Irrigation Decision
7. Disease Risk Detection
8. Pest Risk Detection
9. Weather Stress Detection
10. Fertilizer/Nutrition Scheduling
11. Dynamic Notification Engine
12. Notification State Management
13. Gemini Farmer Guidance
14. Farmer Dashboard Payload
15. Harvest Management
16. Pre-Harvest Marketplace Listing Reminder
17. Backend API Contract
18. JSON Schemas
19. Backend Integration Examples

======================================================================
PRE-HARVEST MARKETPLACE FLOW
======================================================================

Harvest prediction
       ↓
days_to_harvest
       ↓
6 days → FIRST marketplace listing reminder
3 days → FOLLOW-UP marketplace reminder
1 day  → FINAL marketplace reminder
       ↓
Backend marketplace

If marketplace.crop_listed = true, the AI/ML engine
does not generate another listing reminder.

AI/ML calculates harvest timing and reminder timing.
Backend owns the actual marketplace listing and database.
Frontend owns the listing UI/UX.

======================================================================
DYNAMIC INPUTS
======================================================================

farm_id
field_id
telemetry_id
state
district
village
latitude
longitude
crop_name
planting_date
crop_stage_mode
crop_stage
telemetry
marketplace.crop_listed

======================================================================
CROP STAGE MODES
======================================================================

AUTO:
Crop age and stage are calculated dynamically from
planting_date and the crop-stage database.

MANUAL:
Backend can provide crop_stage directly.

======================================================================
WEATHER
======================================================================

Source: LIVE_REAL
Provider: Open-Meteo
Weather is dynamically retrieved using farm coordinates.

======================================================================
IoT TELEMETRY
======================================================================

Current hackathon mode:
SYNTHETIC_HACKATHON_DEMO

No physical IoT sensor is represented as connected.

physical_sensor_connected = false

======================================================================
LLM
======================================================================

Provider: Google Gemini

Role:
Explanation and farmer guidance only.

Gemini does not override deterministic monitoring decisions.

======================================================================
BACKEND ENTRY POINT
======================================================================

File:
backend_handoff/engine/dynamic_monitoring_engine.py

Usage:

from dynamic_monitoring_engine import run_monitoring

result = run_monitoring(request)

======================================================================
API CONTRACT
======================================================================

POST /api/v1/monitoring/analyze

POST /api/v1/monitoring/notification/action

Detailed contract:
backend_handoff/schemas/api_contract.json

======================================================================
RESPONSIBILITY SPLIT
======================================================================

AI/ML:
- crop stage calculation
- monitoring intelligence
- weather processing
- telemetry processing
- risk decisions
- harvest timing
- marketplace reminder timing
- farmer guidance

Backend:
- authentication
- farmer management
- farm/field management
- telemetry ingestion
- API routing
- persistence
- marketplace listing
- notification delivery
- buyer/transaction management

Frontend:
- dashboard
- charts
- maps
- notifications
- marketplace UI
- crop listing form
- farmer interaction

======================================================================
PRODUCTION NOTES
======================================================================

1. Do not hardcode farm, field, farmer or location data.

2. Use actual farm coordinates for live weather.

3. Synthetic IoT is for hackathon demonstration only.

4. Disease/pest risk indicates monitoring priority and
   does not confirm an actual infestation.

5. Fertilizer and crop-protection recommendations should
   be validated against applicable local guidance, product
   labels, crop stage and regulations before production use.

6. Gemini must not silently override the decision engine.

7. Marketplace listing status is owned by the backend.

======================================================================
FINAL STATUS
======================================================================

✓ Monitoring Engine
✓ Dynamic Crop Stage
✓ Live Weather
✓ IoT Telemetry
✓ Decision Engine
✓ Notifications
✓ Gemini Guidance
✓ Harvest Management
✓ 6-Day Marketplace Reminder
✓ Backend API Contract
✓ Backend-Callable Python Engine

AgriBridge AI — AI/ML → Backend Final Handoff
