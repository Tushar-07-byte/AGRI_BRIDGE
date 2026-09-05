
# AgriBridge AI — Ultra Crop Monitoring

## AI/ML → Backend Handoff Documentation

Version: 1.0
Generated: 2026-09-03

---

## 1. Purpose

The AgriBridge AI Ultra Crop Monitoring module provides dynamic
crop monitoring and decision support.

The backend sends farm, field, location, crop and telemetry
information to the AI/ML monitoring engine.

The engine evaluates:

- Crop growth stage
- Stage-specific management
- Live weather
- IoT telemetry
- Irrigation requirement
- Disease risk
- Pest risk
- Weather stress
- Fertilizer scheduling
- Notifications
- Harvest timing
- Farmer guidance through Google Gemini

The frontend should NOT implement agricultural decision logic.

---

## 2. Architecture

Backend
   |
   | POST /api/v1/monitoring/analyze
   v
AgriBridge AI Monitoring Engine
   |
   +---- Crop Knowledge Base
   |
   +---- Dynamic Stage Engine
   |
   +---- LIVE Weather
   |
   +---- IoT Telemetry
   |
   +---- Daily Decision Engine
   |
   +---- Notification Engine
   |
   +---- Gemini Farmer Guidance
   |
   v
Structured JSON Response
   |
   v
Backend
   |
   v
Frontend UI/UX

---

## 3. Dynamic Farm Identification

The system supports multiple:

- Farms
- Fields
- Telemetry devices/records
- States
- Districts
- Villages
- Crops

Required identifiers:

- farm_id
- field_id
- telemetry_id

Location fields:

- state
- district
- village
- latitude
- longitude

State, district and village are identification/location fields.

Latitude and longitude should be supplied whenever possible because
live weather services use geographic coordinates.

---

## 4. Dynamic Crop Configuration

Crop input contains:

- crop_name
- planting_date
- crop_stage_mode
- crop_stage

The system supports two stage modes.

### AUTO

Use:

crop_stage_mode = AUTO

The monitoring engine calculates crop age from the planting date
and determines the current crop stage using the AgriBridge crop-stage
knowledge base.

Flow:

Planting Date
    |
    v
Monitoring Date
    |
    v
Crop Age
    |
    v
Dynamic Stage Engine
    |
    v
Current Crop Stage

### MANUAL

Use:

crop_stage_mode = MANUAL

and provide:

crop_stage

Manual stage mode is useful when the backend or field operator
already knows the crop's current stage.

---

## 5. Supported Crop Information

The current AgriBridge monitoring knowledge base contains:

- Wheat
- Rice
- Corn
- Potato
- Soybean
- Tomato
- Pepper
- Squash
- Strawberry
- Raspberry
- Grape
- Apple
- Peach
- Cherry
- Blueberry
- Orange

The backend should send the crop name according to the configured
AgriBridge crop master.

Do not hardcode one crop in the backend.

---

## 6. IoT Telemetry

Supported telemetry fields:

- soil_moisture_percent
- soil_temperature_c
- air_temperature_c
- relative_humidity_percent
- rainfall_mm
- leaf_wetness
- soil_ec_ds_m
- soil_ph
- light_hours
- wind_speed_kmh

The hackathon configuration currently uses:

SYNTHETIC_HACKATHON_DEMO

Synthetic telemetry MUST NOT be represented as physical sensor data.

Production hardware can later replace synthetic telemetry.

---

## 7. Weather

Weather source:

LIVE_REAL

The weather service should use field latitude and longitude.

The system should clearly distinguish:

LIVE_REAL

from:

SYNTHETIC_HACKATHON_DEMO

If live weather is unavailable, the backend should preserve
data-source transparency instead of presenting unavailable data
as live weather.

---

## 8. Monitoring Decisions

The monitoring engine produces decisions for:

### Irrigation

Uses:

- Soil moisture
- Rainfall
- Rain probability
- Temperature
- Crop stage

### Disease Risk

Uses environmental conditions such as:

- Relative humidity
- Rainfall
- Leaf wetness

Important:

Disease risk does NOT mean confirmed disease.

### Pest Risk

Uses environmental conditions to determine when additional
scouting is appropriate.

Important:

Pest risk does NOT mean confirmed pest infestation.

### Weather Stress

Considers:

- Temperature
- Humidity
- Wind
- Rainfall

### Fertilizer

Uses crop-stage management information and weather conditions.

Chemical dosage information must not be invented by the LLM.

---

## 9. Notification System

Supported notification states:

- SCHEDULED
- DUE
- ALERT
- POSTPONED
- RESCHEDULED
- COMPLETED
- CANCELLED

Typical lifecycle:

SCHEDULED
    |
    v
DUE
    |
    v
COMPLETED

Alternative:

DUE
    |
    v
POSTPONED
    |
    v
RESCHEDULED
    |
    v
DUE

Backend should use the notification action API rather than
directly modifying notification state.

---

## 10. API Contract

### Analyze Monitoring

Method:

POST

Endpoint:

/api/v1/monitoring/analyze

Request schema:

schemas/monitoring_input_schema.json

Response schema:

schemas/monitoring_output_schema.json

Purpose:

Runs the complete dynamic monitoring pipeline.

---

### Notification Action

Method:

POST

Endpoint:

/api/v1/monitoring/notification/action

Request schema:

schemas/notification_action_schema.json

Supported actions:

- COMPLETE
- POSTPONE
- RESCHEDULE
- CANCEL

---

## 11. LLM Integration

Current provider:

Google Gemini

Current role:

Explanation layer.

Gemini receives verified monitoring-engine context and converts
the results into simple farmer-friendly guidance.

Gemini MUST NOT:

- Override monitoring decisions
- Invent telemetry
- Invent weather
- Invent crop stages
- Treat risk as confirmed disease
- Treat risk as confirmed pest infestation
- Invent pesticide dosage
- Invent fertilizer dosage
- Claim synthetic IoT is physical sensor data

---

## 12. Data Transparency

Every monitoring response should preserve the source of data.

Current hackathon configuration:

Weather:
LIVE_REAL

IoT:
SYNTHETIC_HACKATHON_DEMO

Physical sensor:
False

This distinction is mandatory for the hackathon implementation.

---

## 13. Frontend Responsibilities

The frontend/UI team owns:

- Farm selection
- Field selection
- State selection
- District selection
- Village selection
- Crop selection
- Crop stage selection
- Monitoring dashboard
- Risk cards
- Notification cards
- Farmer actions
- Charts
- Maps
- UX/UI

Frontend should consume backend JSON.

Frontend should NOT duplicate agricultural decision logic.

---

## 14. Backend Responsibilities

Backend owns:

- Authentication
- Farmer/user management
- Farm management
- Field management
- Telemetry ingestion
- API routing
- Calling AI/ML monitoring engine
- Persisting monitoring results
- Notification delivery
- Frontend integration
- Database integration

---

## 15. AI/ML Responsibilities

AI/ML owns:

- Crop-stage calculation
- Stage-specific management lookup
- Weather integration
- Telemetry processing
- Irrigation decision
- Disease-risk assessment
- Pest-risk assessment
- Weather-stress assessment
- Fertilizer scheduling
- Notification generation
- Farmer-guidance context
- Gemini farmer guidance

---

## 16. Example Files

AUTO stage request:

examples/monitoring_request_auto_stage.json

MANUAL stage request:

examples/monitoring_request_manual_stage.json

Notification actions:

examples/notification_action_examples.json

---

## 17. Important Production Notes

The current IoT telemetry can be synthetic for the hackathon.

It MUST be labeled:

SYNTHETIC_HACKATHON_DEMO

It must never be presented as data generated by physical sensors.

Agricultural fertilizer and crop-protection recommendations should
be validated against applicable local agronomic guidance, product
labels and regulations before real-world farmer deployment.

---

## 18. No Hardcoded Farm

The backend MUST NOT hardcode:

- One farm
- One field
- One telemetry device
- One state
- One district
- One village
- Wheat
- 33 crop days
- CRI stage
- One weather location

Those values are examples only.

The production request should dynamically provide the relevant
farm, field, location, crop, stage mode and telemetry information.

---

## 19. Handoff Summary

The AI/ML monitoring module should be treated as a service.

Backend sends:

farm_id
field_id
telemetry_id
location
crop
planting_date
crop_stage_mode
crop_stage when required
telemetry

AI/ML returns:

crop stage
weather
IoT interpretation
irrigation decision
disease risk
pest risk
weather stress
fertilizer status
notifications
farmer guidance
harvest information
data transparency

The frontend consumes the backend response and handles UI/UX.

---

## End of AgriBridge AI AI/ML → Backend Handoff


## PRE-HARVEST MARKETPLACE LISTING

AgriBridge proactively recommends marketplace listing BEFORE
the expected harvest date.

Reminder schedule:

- 6 days before harvest -> FIRST listing reminder
- 3 days before harvest -> FOLLOW-UP reminder
- 1 day before harvest -> FINAL reminder

The AI/ML engine calculates days_to_harvest dynamically.

The backend supplies marketplace listing state:

    marketplace.crop_listed = true/false

If crop_listed is true, no marketplace listing reminder is
generated.

AI/ML owns:

- harvest timing
- listing reminder timing
- notification generation

Backend owns:

- marketplace listing database state
- actual crop listing
- buyer information
- marketplace transactions

Frontend owns:

- List Crop button
- marketplace listing form
- listing status display
- buyer/marketplace UI
