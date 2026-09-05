# 🌾 AgriBridge — Smart Horizon 2026 Grand Finale

> **AI-Powered Farm Decision Engine & Verified Pre-Harvest Marketplace**  
> Connecting **Farm Intelligence**, **Virtual IoT Telemetry**, **Deep-Learning Diagnostics**, **Field Verification**, and **Direct Buyer Commitments**.

---

## 🌟 Executive Summary

**AgriBridge** is a full-stack agricultural operating system built to address the critical gap between farm-level risk management and market discovery in Indian agriculture.

Instead of isolated point solutions, AgriBridge delivers an end-to-end closed loop:
```
SENSE ➔ REASON ➔ PLAN ➔ ACT ➔ VERIFY ➔ CONNECT ➔ LEARN
```

---

## 🚀 Key Innovations & Grand Finale Features

### 1. ⚡ AI Farm Command Center (`farm-command-center.html`)
- **Farm Health Index (0–100)**: Dynamically evaluated based on sensor telemetry, microclimate anomalies, and crop phenology.
- **5 Modular Risk Engines**:
  - 💧 **Water Risk** (Evapotranspiration & root-zone hydration analysis)
  - 🦠 **Disease Risk** (Microclimate humidity spore model + leaf image CNN)
  - 🌦️ **Weather Risk** (15-day forecast & storm radar tracking)
  - 🧪 **Estimated Nutrient Risk** (Soil pH cation absorption rules)
  - 🛡️ **Overall Farm Risk** (Composite operational index)
- **Virtual IoT Telemetry Grid**:
  - Live streams for Soil Moisture, Temperature, Humidity, Rain Probability, Light, and Soil pH.
  - Clearly marked **`SIMULATION MODE`** with a hardware-ready abstraction layer for future ESP32/LoRaWAN sensor nodes.
- **Interactive Scenario Engine**:
  - `NORMAL`, `WATER STRESS`, `DISEASE RISK`, `HEAT STRESS`, `HEAVY RAIN`, `NUTRIENT RISK`.

### 2. 🧠 Multi-Agent Reasoning & Explainable Decision Layer
- 5 Specialized Autonomous Agents:
  1. 📡 **Farm Monitoring Agent**
  2. 💧 **Water Intelligence Agent**
  3. 🦠 **Crop Health / Disease Agent**
  4. 🧪 **Estimated Nutrient Risk Agent**
  5. 🌦️ **Weather Intelligence Agent**
- **Action Planning Agent (Conflict Resolver)**:
  - *Conflict Scenario*: Water Agent recommends 420 L irrigation; Weather Agent reports 91% storm cloudburst inbound.
  - *Outcome*: Automatically cancels irrigation $\rightarrow$ **saves 420 L of water** $\rightarrow$ records traceability event.
- **"Why This Decision?" Evidence Drawer**:
  - Transparent checklist of agricultural facts, confidence scores (e.g. `94%`), and decision IDs.

### 3. 🔄 Closed-Loop Action Verification
- Farmers mark actions completed $\rightarrow$ triggers a post-action simulated sensor sweep.
- Verifies recovery (e.g. *Soil moisture rose from 18% to 29%*) and updates Farm Health Index.

### 4. 📡 Offline Mode & Sync Engine
- Toggle between `ONLINE ●` and `OFFLINE ●`.
- Queues farmer field actions locally in `localStorage` when network connectivity drops.
- 1-Click `[Sync Now]` button replays and synchronizes queue upon reconnection.

### 5. 🛒 12-Crop Verified Pre-Harvest Marketplace (`buyer-dashboard.html`)
- Real pre-harvest forward contracts across 12 authentic crops with high-definition farm photography:
  - 🌾 *Golden Sharbati Wheat* (Raipur, CG)
  - 🍚 *Basmati 1121 Paddy Rice* (Bathinda, PB)
  - 🌼 *Pusa Bold Yellow Mustard* (Kota, RJ)
  - 🌱 *Organic Soybean JS 335* (Rajnandgaon, CG)
  - 🌽 *Hybrid Sweet Corn & Maize* (Raipur, CG)
  - ☁️ *Long-Staple BT Cotton* (Nagpur, MH)
  - 🎋 *High-Brix Sugarcane* (Karnal, HR)
  - 🥔 *Kufri Jyoti Potato* (Varanasi, UP)
  - 🍅 *Himsona Vine Tomato* (Bilaspur, CG)
  - 🧅 *Red Nasik Onion* (Nashik, MH)
  - 🌾 *Durum Malwa Gold Wheat* (Indore, MP)
  - 🌶️ *Guntur Sannam Red Chilli* (Guntur, AP)
- Attached Ground Truth Field Agent quality audit certificates (`AGB-CERT-2026`).

### 6. 👑 Operations Command Center (`admin-dashboard.html`)
- Passcode-guarded security barrier (`admin123`).
- Live AI health monitoring, real-time decision stream, security login telemetry, and RFC-4180 CSV export.

---

## 🌐 Quick Access Links (Port 3000)

| Experience / Role | Localhost URL | Network URL (Wi-Fi) |
| :--- | :--- | :--- |
| 🏠 **Landing Page** | `http://localhost:3000/frontend/pages/index.html` | `http://10.228.117.107:3000/frontend/pages/index.html` |
| ⚡ **AI Farm Command Center** | `http://localhost:3000/frontend/pages/farm-command-center.html` | `http://10.228.117.107:3000/frontend/pages/farm-command-center.html` |
| 🌾 **Farmer Dashboard** | `http://localhost:3000/frontend/pages/farmer-dashboard.html` | `http://10.228.117.107:3000/frontend/pages/farmer-dashboard.html` |
| 🛒 **Buyer Marketplace** | `http://localhost:3000/frontend/pages/buyer-dashboard.html` | `http://10.228.117.107:3000/frontend/pages/buyer-dashboard.html` |
| 📋 **Field Agent Map** | `http://localhost:3000/frontend/pages/field-agent-dashboard.html` | `http://10.228.117.107:3000/frontend/pages/field-agent-dashboard.html` |
| 👑 **Admin Portal** | `http://localhost:3000/frontend/pages/admin-dashboard.html` | `http://10.228.117.107:3000/frontend/pages/admin-dashboard.html` |

---

## 🧪 Quick Start & Running Instructions

1. Start Python HTTP server in project root:
   ```bash
   python -m http.server 3000
   ```
2. Open in browser: `http://localhost:3000/frontend/pages/index.html`
3. Refer to [`HACKATHON_DEMO.md`](./HACKATHON_DEMO.md) for the 22-step live presentation guide.

---

## 📝 Engineering Honesty & Prototype Limitations

- **Virtual IoT Telemetry**: Sensor values are generated by an in-browser deterministic simulation engine (`SIMULATION MODE`). Hardware socket abstractions are prepared for physical ESP32 / MQTT devices.
- **Estimated Nutrient Risk**: Evaluated using soil pH sensor levels and agronomic rules. We do not claim direct laboratory NPK measurement.
- **Decision Confidence Policy**: Thresholds (>85% High, 60–85% Medium, <60% Low) are implemented as prototype decision rules.
- **Offline Sync**: Leverages client-side `localStorage` data bus for hackathon demonstration.

