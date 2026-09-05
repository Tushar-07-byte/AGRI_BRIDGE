# AgriBridge — Security, Safety & Key Hygiene Notes
**Smart Horizon 2026**

---

## 1. Zero-Credential Exposure Policy
- All secrets, API keys (`GEMINI_API_KEY`, `JWT_SECRET`), and database connection URIs are loaded exclusively from `.env` or operating system environment variables.
- Automated repository audit confirmed zero plaintext keys committed to source control.

## 2. Deterministic Safety Boundaries
- **No Direct AI Execution**: LLMs and vision classifiers cannot independently trigger consequential field actions (chemical sprays, irrigation valves).
- **Execution Authority**: Every action must pass the deterministic validation of `MultiSignalPolicyEngine`.

## 3. Role-Based Access Control (RBAC)
- Strict JWT role claim verification on sensitive routes:
  - `/api/verifications/*` -> `field_agent` or `admin` only.
  - `/api/bidding/bids` -> `buyer` only.
  - `/api/crop-listings` (create) -> `farmer` only.

## 4. Signal Integrity & Validation
- Sensor inputs and farm payloads are validated against Pydantic schemas with bounding checks (e.g. soil moisture 0-100%, pH 0-14, confidence 0.0-100.0%).
