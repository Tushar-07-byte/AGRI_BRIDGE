# AgriBridge — Judge Demo & Walkthrough Guide
**Smart Horizon 2026 | Demonstration Scenarios A through J**

---

### 🚀 Canonical System Startup
1. **Seed Demo Accounts (One-Time / Reset)**:
   ```bash
   python scripts/seed_demo_users.py
   ```
2. **Start Backend API Server**:
   ```bash
   python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
   ```
3. **Open Stakeholder Dashboards**:
   - Farmer Dashboard: `http://127.0.0.1:8000/frontend/pages/farmer-dashboard.html`
   - Kisan Saathi Voice: `http://127.0.0.1:8000/frontend/pages/voice-assistant.html`
   - Field Agent Portal: `http://127.0.0.1:8000/frontend/pages/field-agent-dashboard.html`
   - Buyer Marketplace: `http://127.0.0.1:8000/frontend/pages/buyer-dashboard.html`
   - Crop Listings: `http://127.0.0.1:8000/frontend/pages/crop-listings.html`
   - Login Screen: `http://127.0.0.1:8000/frontend/pages/login.html`

---

### 🔑 Verified Demo Credentials

| Role | Mobile Number | Password | Target Dashboard |
| :--- | :--- | :--- | :--- |
| **Farmer** | `9876500001` | `SecurePassword@123` | `farmer-dashboard.html` |
| **Field Agent** | `9876500002` | `SecurePassword@123` | `field-agent-dashboard.html` |
| **Buyer / FPO** | `9876500003` | `SecurePassword@123` | `buyer-dashboard.html` |
| **Admin** | `9876500004` | `SecurePassword@123` | `admin-dashboard.html` |

---

### 🧪 Judge Demonstration Scenarios (A through J)

#### Scenario A — SAFE / ALLOWED
- **Input**: Valid Wheat Leaf Image (`sample_wheat_rust.jpg`), calibrated confidence = 94.2%, clear weather (Rain = 0%, Wind = 8 km/h).
- **Engine Decision**: `ALLOWED`.
- **Expected Outcome**: `ActionPlan` generated with exactly 1 executable chemical spray / bio-fungicide `PlanTask` (`PENDING`). Farmer can click *Acknowledge* -> *Start* -> *Complete*.

#### Scenario B — RAIN / DEFERRED
- **Input**: Valid Wheat Leaf Rust diagnosis, but weather forecast indicates 75% precipitation probability in the next 3 hours.
- **Engine Decision**: `DEFERRED`.
- **Expected Outcome**: Zero unsafe executable tasks generated. UI displays weather constraint badge: *"Chemical spray deferred: Rain probability 75% > threshold 60%"*. Non-blocking recheck timer scheduled.

#### Scenario C — HIGH WIND / DEFERRED
- **Input**: Valid Tomato Late Blight diagnosis, ambient wind speed = 28 km/h (> 20 km/h threshold).
- **Engine Decision**: `DEFERRED`.
- **Expected Outcome**: Zero unsafe spray tasks. UI alerts farmer to excessive wind drift risk; safe application window tracked.

#### Scenario D — BORDERLINE / HUMAN REVIEW
- **Input**: Ambiguous leaf image (`1_healthy_tomato_leaf.jpg`), AI confidence = 51.7% (< 65% threshold).
- **Engine Decision**: `REQUIRES_HUMAN_REVIEW`.
- **Expected Outcome**: Zero executable tasks created. Prescription lock engaged on farmer UI. Automatic escalation ticket dispatched to the Field Agent Portal.

#### Scenario E — HUMAN VERIFICATION & RE-EVALUATION
- **Input**: Field Agent logs into `field-agent-portal.html`, inspects ticket, reviews high-resolution photo, and confirms *Tomato Late Blight*.
- **Engine Decision**: Agent verification submitted -> Context rebuilt with verified diagnosis -> `MultiSignalPolicyEngine` re-evaluated.
- **Expected Outcome**: Context transitions cleanly to verified state and unlocks deterministic action planning.

#### Scenario F — VERIFIED + UNSAFE WEATHER
- **Input**: Field Agent verifies diagnosis, but current weather is raining heavily (85% rain).
- **Engine Decision**: `DEFERRED`.
- **Expected Outcome**: Proves that human verification does NOT blindly force `ALLOWED`. Weather safety gates remain active and defer application until weather clears.

#### Scenario G — BLOCKED (Invalid Agronomic Combination)
- **Input**: Soil pH = 3.5 (severe acidity) or sensor hardware anomaly detected.
- **Engine Decision**: `BLOCKED`.
- **Expected Outcome**: Zero executable tasks generated. Red alert on dashboard advising soil remediation before chemical treatment.

#### Scenario H — SIMULATED DATA PROVENANCE
- **Input**: Test sensor telemetry or simulated weather feed.
- **Expected Outcome**: UI visibly displays `[SIMULATED]` / `[DEMO DATA]` provenance badge. Never falsely mislabeled as `[LIVE IOT]`.

#### Scenario I — WEATHER CLEARS & RECHECK
- **Input**: Previously deferred plan undergoes automated background recheck when rain probability drops to 10%.
- **Engine Decision**: `ALLOWED`.
- **Expected Outcome**: ActionPlan updates, single executable task becomes active, zero duplicate tasks created.

#### Scenario J — FAILURE & RECOVERY MODES
- **Input**: Weather API timeout, corrupted image file, or missing sensor payload.
- **Expected Outcome**: Safe fallback triggered. Informative user-facing error message displayed; system state fails closed with zero unsafe task dispatch.

