# 🏛️ AGRIBRIDGE SYSTEM ARCHITECTURE

## 1. High-Level Architecture Overview

AgriBridge is structured around a **Closed-Loop Agricultural Decision Engine** layered across six core tiers:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        1. SENSING & TELEMETRY                          │
│  Virtual IoT Nodes • Hardware-Ready Abstraction • Weather API • Vision │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Telemetry Stream
┌───────────────────────────────────▼────────────────────────────────────┐
│                    2. MULTI-AGENT REASONING LAYER                      │
│  • Farm Monitoring Agent       • Water Intelligence Agent              │
│  • Crop Health / Disease Agent • Estimated Nutrient Risk Agent         │
│  • Weather Intelligence Agent                                          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Agent Signal Tuple
┌───────────────────────────────────▼────────────────────────────────────┐
│              3. ACTION PLANNING & CONFLICT RESOLUTION                  │
│  • Rule & Heuristic Arbiter    • "Why This Decision?" Evidence Engine  │
│  • Priority Schedulers (P1/P2) • Confidence Escalation Policy          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Action Plan
┌───────────────────────────────────▼────────────────────────────────────┐
│             4. FARMER EXECUTION & CLOSED-LOOP VERIFICATION             │
│  • In-App Action Dispatch      • Offline Queue & Sync                  │
│  • Post-Action Sensor Sweep    • Recovery Detection (18% ➔ 29%)        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Verified Yield Data
┌───────────────────────────────────▼────────────────────────────────────┐
│              5. FIELD AGENT AUDIT & TRUST ASSURANCE                    │
│  • Geotagged GPS Verification  • 6-Point Physical Quality Audit        │
│  • Tamper-Evident Certificate Generation (AGB-CERT-2026)               │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Digital Certificate
┌───────────────────────────────────▼────────────────────────────────────┐
│               6. BUYER MARKETPLACE & ADMIN GOVERNANCE                  │
│  • Advance Pre-Harvest Contracts • 12 Verified Commodity Catalog       │
│  • Real-Time Operations Telemetry • Audit Trail & Security Center      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Multi-Agent Intelligence Layer

### A. Farm Monitoring Agent
- **Inputs**: Soil moisture, ambient temperature, relative humidity, light intensity, crop type, growth stage.
- **Output**: General physiological status, baseline anomalies, vegetative tillering health index.

### B. Water Intelligence Agent
- **Inputs**: Soil moisture, ambient temperature, humidity, root-zone depth, evapotranspiration estimate, recent irrigation events.
- **Output**: Water stress score (0–100), volumetric irrigation recommendation (Liters), timing schedule (e.g. 6:00 PM evening cycle).

### C. Crop Health / Disease Agent
- **Inputs**: CNN leaf image diagnostic inference, classification confidence (%), relative humidity, canopy wetness hours, temperature.
- **Output**: Disease risk index (0–100), severity rating, IPM organic treatment schedule (e.g. Bio-fungicide / Neem oil).

### D. Estimated Nutrient Risk Agent
- **Inputs**: Soil pH, crop stage, visible chlorosis symptoms.
- **Output**: Estimated nutrient bioavailability index (0–100), soil acidity/alkalinity lockup alert, soil amendment recommendation.
- *Strict Labeling*: Labeled as **Estimated Nutrient Risk** based on pH sensor data and crop rules (no physical NPK lab claims).

### E. Weather Intelligence Agent
- **Inputs**: 15-day forecast, hourly precipitation probability, wind velocity, cloud cover.
- **Output**: Weather risk index (0–100), rainfall arrival window, natural precipitation volume estimate.

### F. Action Planning Agent (Central Decision Layer)
- **Role**: Resolves conflicting inputs between individual agents.
- **Conflict Resolution Example**:
  - `Water Agent`: "Soil moisture is 18%. Recommend 420 L irrigation."
  - `Weather Agent`: "Rain probability surged to 91% (35mm storm inbound)."
  - `Action Planning Agent Decision`: **CANCEL IRRIGATION**. Natural rainfall fulfills crop water needs and prevents root rot while saving 420 L of water.

---

## 3. Hardware-Ready Virtual IoT Abstraction

The telemetry engine in `farm-command-center.js` uses a clean abstraction interface:

```javascript
const TelemetryAdapter = {
    // Current: Virtual IoT Simulation Node
    readSensors: async function() {
        return {
            soilMoisture: State.telemetry.soilMoisture,
            temperature: State.telemetry.temperature,
            humidity: State.telemetry.humidity,
            rainProb: State.telemetry.rainProb,
            lightIntensity: State.telemetry.lightIntensity,
            soilPh: State.telemetry.soilPh
        };
    },
    // Future hardware bridge: ESP32 / MQTT / LoRaWAN
    connectHardware: function(mqttBrokerUrl) {
        // Drop-in hardware socket connection
    }
};
```

---

## 4. Prototype Confidence Escalation Policy

| Confidence Score | Classification | System Policy |
| :---: | :---: | :--- |
| **> 85%** | **High Confidence** | Autonomous recommendation dispatched directly to Farmer Action Plan. |
| **60% – 85%** | **Medium Confidence** | Requires explicit Farmer Confirmation before scheduling. |
| **< 60%** | **Low Confidence** | Flagged for Field Agent / Agronomist physical review and sample verification. |

---

## 5. Security & Audit Logging Architecture

1. **Authentication Guard**: Role-based access control (`farmer`, `buyer`, `agent`, `admin`) with session token verification and passcode lock on Admin (`admin123`).
2. **Telemetry Traceability**: Every decision produces a persistent record containing `decision_id`, `timestamp`, `telemetry_snapshot`, `agent_outputs`, and `farmer_action_state`.
3. **Admin Sync**: Local events write to `localStorage.agribridge_ai_decisions` and `localStorage.agribridge_live_logins`, which are seamlessly streamed to the Admin Operations Center.

