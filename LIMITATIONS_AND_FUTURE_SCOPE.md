# AgriBridge — Limitations & Future Scope
**Smart Horizon 2026**

---

## Current System Limitations
1. **Vision Pathology Scope**: Deep learning models currently cover 4 major staple/cash crops (Wheat, Rice, Tomato, Potato). Other crops utilize ICAR botanical heuristics.
2. **IoT Connectivity in Remote Fields**: Field sensor ingestion currently relies on HTTP REST telemetry; offline mesh networking (LoRaWAN) is in simulated mode.
3. **Edge Deployment**: AI inference runs on the backend server rather than on low-power microcontrollers at the field edge.

---

## Future Roadmap & Scaling Scope
1. **LoRaWAN & Satellite Ingestion**: Direct integration with ISRO Bhuvan and Sentinel-2 multispectral NDVI imagery for field-wide canopy health monitoring.
2. **Autonomous Drone & Valve Actuation**: Direct MQTT protocol integration with automated solar irrigation pumps and drone sprayers based on AgriBridge action plans.
3. **Expanded Crop Models**: Scaling from 4 to 25 commercial Indian crops using transfer learning.
4. **On-Device Edge AI**: Quantized INT8 TensorFlow Lite models running directly on Android mobile devices for zero-connectivity diagnosis.
