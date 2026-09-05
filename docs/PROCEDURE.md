# AgriBridge — Operational Procedures, Setup & Runbook
**Smart Horizon 2026 | Problem Statement: SH-AGR-001 / AGR-001**

---

## 1. Required Tools & Packages

### System Prerequisites
- **Operating System**: Windows 10/11, Ubuntu 20.04+, or macOS 12+
- **Python**: Version 3.10 to 3.14
- **Database**: MySQL 8.0+ (Active database supported, with automated SQLite fallback)
- **Web Browser**: Google Chrome, Microsoft Edge, Mozilla Firefox (Web Speech API supported)

### Core Dependencies
- **Backend Framework**: `FastAPI` (REST APIs, CORS middleware, static file mounting)
- **ASGI Server**: `uvicorn[standard]`
- **ORM & Database**: `SQLAlchemy`, `PyMySQL`
- **Machine Learning & Vision**: `TensorFlow`, `Pillow`, `NumPy`, `pandas`
- **Speech & Audio**: `gTTS` (Google Text-to-Speech), Web Speech API
- **Testing & Verification**: `pytest`, `httpx`
- **Reporting & Presentations**: `python-pptx`

---

## 2. Standard Installation & Environment Setup

```bash
# 1. Navigate to project root directory
cd "AgriBridge - 2"

# 2. Activate Python Virtual Environment
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Windows Command Prompt:
.\venv\Scripts\activate.bat
# On Linux/macOS:
source venv/bin/activate

# 3. Verify / Install Dependencies
pip install -r requirements.txt
```

---

## 3. Database Initialization & Demo Seeding

```bash
# Seed deterministic accounts for Farmer, Field Agent, Buyer, and Admin
python scripts/seed_demo_users.py
```
> **Note**: If MySQL is unavailable, AgriBridge's database layer (`backend/app/database/connection.py`) will automatically fall back to SQLite, ensuring 100% operational uptime during live demonstrations.

---

## 4. Application Startup Procedure

```bash
# Start backend API server from project root:
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```
- **Backend API Docs (Swagger)**: `http://127.0.0.1:8000/docs`
- **Database Status**: `http://127.0.0.1:8000/api/db/status`
- **System Health**: `http://127.0.0.1:8000/api/public/health`

---

## 5. Stakeholder Frontend Dashboards

Open the following URLs in your web browser:
1. **Farmer Dashboard**: `http://127.0.0.1:8000/frontend/pages/farmer-dashboard.html`
2. **Kisan Saathi Voice Companion**: `http://127.0.0.1:8000/frontend/pages/voice-assistant.html`
3. **Field Agent Portal**: `http://127.0.0.1:8000/frontend/pages/field-agent-dashboard.html`
4. **Buyer Marketplace**: `http://127.0.0.1:8000/frontend/pages/buyer-dashboard.html`
5. **Crop Listings**: `http://127.0.0.1:8000/frontend/pages/crop-listings.html`
6. **Login Screen**: `http://127.0.0.1:8000/frontend/pages/login.html`

---

## 6. Demonstration Credentials

| Role | Mobile Number | Password | Capabilities |
| :--- | :--- | :--- | :--- |
| **Farmer** | `9876500001` | `SecurePassword@123` | Crop Monitoring, Disease Diagnostics, Voice Advisory, Task Execution |
| **Field Agent** | `9876500002` | `SecurePassword@123` | Escalation Review Queue, Diagnosis Verification, Manual Overrides |
| **Buyer / FPO** | `9876500003` | `SecurePassword@123` | Harvest Listings, Mandi MSP Bands, Direct Bidding |
| **Administrator** | `9876500004` | `SecurePassword@123` | System Health, Audit Trail, Sensor Telemetry Oversight |

---

## 7. Automated Testing & Verification Procedure

```bash
# Execute entire 270-test automated test suite:
python -m pytest tests/unit/ tests/integration/

# Expected Output: 270 passed, 0 failed (100% Green in ~80s)
```

---

## 8. Troubleshooting & Recovery Runbook

1. **Port 8000 Already in Use**:
   - Run: `Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force` (PowerShell)
   - Or start on alternate port: `python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001`
2. **Database Connection Reset**:
   - Re-run `python scripts/seed_demo_users.py` to recreate table entries and refresh demo credentials.
3. **Microphone Permissions (Voice Assistant)**:
   - Ensure browser permissions allow microphone access for `127.0.0.1`.
