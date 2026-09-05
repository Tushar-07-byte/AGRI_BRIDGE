# AgriBridge — Autonomous Farm-to-Field Advisory and Action Orchestration Platform

**Smart Horizon 2026 Hackathon | Problem Statement: SH-AGR-001 / AGR-001 (Agriculture and Rural Development)**

---

## Executive Overview

**AgriBridge** is an end-to-end, multi-agent autonomous agricultural advisory and field orchestration platform designed to transform precision farming in India. 

Bridging the gap between raw data and verifiable field execution, AgriBridge integrates:
1. **IoT Sensor and Telemetry Layer**: Real-time soil moisture, temperature, NPK, and localized weather metrics.
2. **Computer Vision Disease Diagnosis**: Deep-learning image classification (Wheat, Rice, Tomato, Potato) paired with ICAR-approved remedies.
3. **Deterministic Multi-Signal Policy Engine**: The sole decision authority that fuses agronomic signals, weather forecasts, and crop growth stages before issuing consequential actions.
4. **4-State Task Lifecycle Orchestration**: Automated task tracking (PENDING -> ACKNOWLEDGED -> IN_PROGRESS -> COMPLETED) with weather-aware replanning and auto-rescheduling.
5. **Human-in-the-Loop Field Agent Escalation**: Automatic routing of borderline-confidence diagnoses (< 65%) to human agricultural officers.
6. **Mandi and Crop Bidding Marketplace**: Direct buyer-farmer trade linkage with live mandi price bands and transparent bidding.
7. **Kisan Saathi Multilingual Voice Companion**: Real-time voice assistant operating in **14 Indian languages + Hinglish** with strict zero-hallucination guardrails and interactive screen navigation.

---

## Quick Start Guide

### Prerequisites
- Python 3.10 - 3.14
- MySQL 8.0+ (or SQLite3 automatic fallback)
- Modern Web Browser (Chrome, Edge, Firefox)

### 1. Environment Setup & Seed Demo Data
```bash
# Clone repository
git clone https://github.com/Tushar-07-byte/AGRI_BRIDGE.git
cd "AgriBridge - 2"

# Activate virtual environment
.\venv\Scripts\Activate.ps1   # PowerShell
# or: .\venv\Scripts\activate.bat   # Windows CMD

# Install dependencies (if needed)
pip install -r requirements.txt

# Seed deterministic demo accounts
python scripts/seed_demo_users.py
```

### 2. Start Backend Server
```bash
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```
- **API Swagger Documentation**: `http://127.0.0.1:8000/docs`
- **Database Status**: `http://127.0.0.1:8000/api/db/status`

### 3. Open Frontend Dashboards
- **Farmer Dashboard**: `http://127.0.0.1:8000/frontend/pages/farmer-dashboard.html`
- **Kisan Saathi Voice**: `http://127.0.0.1:8000/frontend/pages/voice-assistant.html`
- **Field Agent Portal**: `http://127.0.0.1:8000/frontend/pages/field-agent-dashboard.html`
- **Buyer Marketplace**: `http://127.0.0.1:8000/frontend/pages/buyer-dashboard.html`
- **Crop Listings**: `http://127.0.0.1:8000/frontend/pages/crop-listings.html`
- **Login Screen**: `http://127.0.0.1:8000/frontend/pages/login.html`

### 🔑 Demo Credentials

| Role | Mobile Number | Password | Target Dashboard |
| :--- | :--- | :--- | :--- |
| **Farmer** | `9876500001` | `SecurePassword@123` | `farmer-dashboard.html` |
| **Field Agent** | `9876500002` | `SecurePassword@123` | `field-agent-dashboard.html` |
| **Buyer / FPO** | `9876500003` | `SecurePassword@123` | `buyer-dashboard.html` |
| **Admin** | `9876500004` | `SecurePassword@123` | `admin-dashboard.html` |

---

## Automated Testing

AgriBridge features a comprehensive 270-test test suite covering all unit and integration workflows:

```bash
# Run full test suite
python -m pytest tests/unit/ tests/integration/

# Result: 270 passed, 0 failed (100% Green)
```

---

## Judge Demo Scenarios (Scenarios A through J)

| Scenario | Feature Tested | Key Verifiable Outcome |
|---|---|---|
| **Scenario A** | Safe / Allowed Disease Action | High-confidence diagnosis + safe weather -> ALLOWED -> Exactly 1 executable PlanTask. |
| **Scenario B** | Rain / Deferred Rescheduling | Valid disease + unsafe rain forecast -> DEFERRED -> Zero unsafe tasks -> Auto-recheck. |
| **Scenario C** | High Wind / Deferred | Ambient wind > 20 km/h -> DEFERRED -> Spray drift risk alert issued. |
| **Scenario D** | Borderline / Human Escalation | Confidence < 65% -> REQUIRES_HUMAN_REVIEW -> Frozen tasks -> Ticket in Agent Portal. |
| **Scenario E** | Human Agent Verification | Officer reviews photo, verifies disease -> Context rebuilt -> Deterministic re-evaluation. |
| **Scenario F** | Verified + Unsafe Weather | Human verified but raining -> DEFERRED (Human verification does not bypass weather locks). |
| **Scenario G** | Blocked Invalid Agronomy | Extreme soil acidity / sensor failure -> BLOCKED -> Zero executable tasks. |
| **Scenario H** | Simulated Data Provenance | IoT and weather feeds display `[SIMULATED]` badges; never mislabeled as `[LIVE]`. |
| **Scenario I** | Weather Clears & Auto-Recheck | Background recheck upon weather improvement -> ALLOWED -> Single executable task. |
| **Scenario J** | Failure & Recovery Modes | Safe failure state upon API/network timeout with zero unsafe field actions. |

---

## Security and Privacy
- Zero hardcoded credentials or API keys committed in source code.
- Cryptographic password hashing using PBKDF2-SHA256.
- Stateless JWT role-based access tokens with expiration and route guards.
- Parameterized SQL queries preventing SQL injection vulnerabilities.

---

## License and Team
Smart Horizon 2026 — Team AgriBridge.

