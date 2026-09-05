# AgriBridge Field Agent Logic & Decision Gates

## 1. Disease Confidence Gate
The disease confidence gate evaluates AI model inference scores against a configurable threshold (default: `0.60` defined in `disease_confidence_config.json`):

```python
if confidence < threshold:
    # LOW CONFIDENCE GATE
    confidence_status = "LOW"
    chemical_recommendation.status = "LOCKED"
    chemical_recommendation.reason = "LOW_DISEASE_CONFIDENCE"
    field_agent_escalation = True
    trigger_reason = "LOW_CONFIDENCE_DISEASE_PREDICTION"
else:
    # ACCEPTABLE CONFIDENCE GATE
    confidence_status = "ACCEPTABLE"
    field_agent_escalation = False
    if verified_kb_treatment_exists:
        chemical_recommendation.status = "AVAILABLE"
    else:
        chemical_recommendation.status = "UNAVAILABLE"
```

### Safety Constraints:
- **No Chemical Hallucination**: When `chemical_recommendation.status == "LOCKED"`, chemical names, dosage, and schedules are withheld.
- **Gemini Safety Rule**: LLMs cannot bypass the confidence gate or invent treatments.

---

## 2. Sensor Anomaly Detection Gate
Evaluates raw IoT telemetry using physical plausibility criteria (defined in `sensor_anomaly_config.json`):

1. **Physical Boundary Check**: Values outside `[valid_min, valid_max]` trigger `SENSOR_VALUE_OUT_OF_RANGE`.
2. **Zero-Value Nuanced Evaluation**:
   - `soil_moisture == 0%`: Flags `UNUSUAL_SENSOR_READING` (likely disconnected probe or dry sensor in irrigated field).
   - `leaf_wetness == 0`: Allowed under dry daylight conditions (not flagged).
   - `relative_humidity == 0%`: Flags `UNUSUAL_SENSOR_READING` (impossible atmospheric reading).
3. **Rapid Rate of Change**: Sudden drops exceeding hourly maximums trigger `SENSOR_DATA_ANOMALY`.
4. **Missing Telemetry**: Lost heartbeats trigger `SENSOR_DATA_MISSING`.

---

## 3. Human Decision Acceptance/Rejection
- **ACCEPT**: Moves task to `ACCEPTED`, assigns field agent, and enables field report submission.
- **REJECT**: Requires mandatory `rejection_reason` (min length: 5 chars), transitions status to `REJECTED`, and preserves full audit history.

