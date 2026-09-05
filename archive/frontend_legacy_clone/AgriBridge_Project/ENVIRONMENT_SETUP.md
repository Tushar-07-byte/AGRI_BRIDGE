# ⚙️ AGRIBRIDGE ENVIRONMENT & SETUP GUIDE

## Prerequisites
- **Python 3.8+** (for HTTP server / optional FastAPI backend gateway)
- **Modern Web Browser** (Google Chrome, Microsoft Edge, Firefox, or Safari)
- **Local Network / Wi-Fi** (for multi-device teammate access)

---

## 1. Quick Start (Standalone Mode)

No complex builds or NPM installs required. AgriBridge runs out-of-the-box with standard web technologies.

1. Open PowerShell or Terminal in the project root directory:
   ```powershell
   cd "c:\Users\HP\Desktop\Agribridge ferontend"
   ```

2. Start the local server on port 3000:
   ```bash
   python -m http.server 3000
   ```

3. Open your browser and navigate to:
   👉 **`http://localhost:3000/frontend/pages/index.html`**

---

## 2. Multi-Device / Teammate Access over Wi-Fi

If you are on the same Wi-Fi / Hotspot network, teammates can access portals from their phone or laptop using your machine's local IP:

- **Homepage**: `http://10.228.117.107:3000/frontend/pages/index.html`
- **AI Farm Command Center**: `http://10.228.117.107:3000/frontend/pages/farm-command-center.html`
- **Buyer Marketplace**: `http://10.228.117.107:3000/frontend/pages/buyer-dashboard.html`
- **Field Agent Map**: `http://10.228.117.107:3000/frontend/pages/field-agent-dashboard.html`
- **Admin Control Center**: `http://10.228.117.107:3000/frontend/pages/admin-dashboard.html` *(Passcode: `admin123`)*

---

## 3. Demo Credentials Reference

| Role | Email / ID | Password | Portal Entry Link |
| :--- | :--- | :--- | :--- |
| 🌾 **Farmer** | `ramesh@agrifarm.in` | `farm123` | `/frontend/pages/farm-command-center.html` |
| 🛒 **Buyer** | `procurement@freshbazaar.in` | `buyer123` | `/frontend/pages/buyer-dashboard.html` |
| 📋 **Field Agent** | `amit.sharma@agribridge.org` | `agent123` | `/frontend/pages/field-agent-dashboard.html` |
| 👑 **Admin** | `ops@agribridge.org` | `admin123` | `/frontend/pages/admin-dashboard.html` |

---

## 4. Optional Backend Gateway Integration

If running the optional FastAPI backend for live database and CNN model inference:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
The frontend automatically detects whether the backend gateway on port 8000 is online and gracefully falls back to the in-memory/localStorage data bus when in standalone demo mode.

