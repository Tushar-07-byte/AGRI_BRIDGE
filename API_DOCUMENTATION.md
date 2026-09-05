# AgriBridge — Master REST API Documentation
**Smart Horizon 2026 | OpenAPI Specification: /docs | Route Prefix: /api**

---

## 1. Authentication & Role Isolation (`/api/auth`)
- `POST /api/auth/register`: Register new user (`farmer`, `field_agent`, `buyer`).
- `POST /api/auth/login`: Authenticate credentials, receive stateless JWT bearer token.
- `GET /api/auth/me`: Retrieve authenticated user profile and permissions.

## 2. AI Crop Disease Diagnosis (`/api/ai`)
- `POST /api/ai/predict`: Upload leaf image (multipart/form-data) + farm context JSON.
  - Returns: Pathogen diagnosis, confidence score, ICAR organic treatment, weather spray window, and generated Action Plan ID.
  - If confidence < 65%: Automatically creates Field Agent Escalation.

## 3. Autonomous Orchestration (`/api/orchestration`)
- `POST /api/orchestration/tasks/{task_id}/status`: Update task state (`pending`, `acknowledged`, `in_progress`, `completed`).
- `POST /api/orchestration/tasks/{task_id}/recheck-weather`: Dynamic rain recheck and rescheduling.
- `GET /api/orchestration/plans/{plan_id}`: Retrieve action plan and associated trackable tasks.

## 4. Ultra Dynamic Crop Monitoring (`/api/monitoring/v1`)
- `POST /api/monitoring/v1/analyze`: Submit real-time IoT soil metrics & stage info.
  - Returns: Multi-signal evaluation, NPK fertility status, and structured 4-question farmer advisory.

## 5. Kisan Saathi Voice Companion (`/api/voice`)
- `POST /api/voice/saathi`: Master multi-turn Saathi voice endpoint. Accepts audio webm or JSON text, language hint, and UI context.
- `GET /api/voice/saathi/intro`: Get canonical intro in any of 14 supported languages.
- `GET /api/voice/audio/{filename}`: Stream synthesized spoken audio MP3.

## 6. Field Agent Escalation & Verifications (`/api/field-agents`, `/api/verifications`)
- `GET /api/field-agents/dashboard`: Agent metrics and pending review counts.
- `GET /api/verifications/pending`: List all escalated disease records needing human verification.
- `POST /api/verifications/disease-scans/{record_id}/approve`: Confirm diagnosis and release held action plan.
- `POST /api/verifications/disease-scans/{record_id}/reject`: Reject diagnosis with officer corrective notes.

## 7. Marketplace & Bidding (`/api/crop-listings`, `/api/bidding`)
- `POST /api/crop-listings`: Farmer lists crop harvest with quantity and base price.
- `GET /api/crop-listings`: Public marketplace feed with mandi comparison bands.
- `POST /api/bidding/bids`: Buyer submits competitive bid on active crop listing.
- `POST /api/bidding/bids/{bid_id}/accept`: Farmer accepts highest bid.

## 8. Weather & Spray Timing (`/api/weather`, `/api/spray-timing`)
- `GET /api/weather/current`: Live weather for district/state.
- `GET /api/weather/forecast`: 15-day localized Open-Meteo forecast.
- `GET /api/spray-timing/advice`: Safe spray window calculation based on rain and wind thresholds.
