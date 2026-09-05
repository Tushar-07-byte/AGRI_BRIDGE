# AgriBridge Field Agent Backend Handoff & API Specification

## 1. REST Endpoints

### 1.1 List Field Agent Tasks
- **URL**: `GET /api/field-agent/tasks`
- **Query Params**: `status` (optional: `PENDING`, `ACCEPTED`, `IN_PROGRESS`, `FIELD_VISIT`, `REPORT_SUBMITTED`, `VERIFIED`, `REJECTED`, `ALL`)
- **Response**:
  ```json
  {
    "success": true,
    "count": 2,
    "tasks": [ ... ]
  }
  ```

### 1.2 Accept Task
- **URL**: `POST /api/field-agent/tasks/{task_id}/accept`
- **Payload**:
  ```json
  {
    "agent_id": "AGENT_007",
    "agent_name": "Rahul Verma",
    "notes": "Will inspect plot A at 2 PM"
  }
  ```

### 1.3 Reject Task
- **URL**: `POST /api/field-agent/tasks/{task_id}/reject`
- **Payload**:
  ```json
  {
    "agent_id": "AGENT_007",
    "rejection_reason": "Out of operational sector boundary"
  }
  ```

### 1.4 Submit Field Verification Report
- **URL**: `POST /api/field-agent/tasks/{task_id}/verify`
- **Payload**:
  ```json
  {
    "agent_id": "AGENT_007",
    "field_observation": "Spotted orange pustules on lower leaves",
    "disease_observed": "YES",
    "pathogen_identified": "Wheat Leaf Rust",
    "verification_result": "VERIFIED_DISEASE",
    "notes": "Early localized infection, verified ICAR treatment unlocked"
  }
  ```

### 1.5 Evaluate IoT Telemetry Anomaly
- **URL**: `POST /api/field-agent/evaluate-telemetry`
- **Payload**:
  ```json
  {
    "sensor_id": "SN_SOIL_04",
    "sensor_type": "soil_moisture",
    "value": 0.0,
    "crop": "Wheat",
    "farm_id": "FARM_01"
  }
  ```

### 1.6 Tracked Farmer Notifications
- **URL**: `GET /api/notifications/farmer/{farmer_id}/tracked`
- **Response**:
  ```json
  {
    "success": true,
    "notifications": [
      {
        "notification_id": "NTF_001",
        "title": "Disease Scan Alert",
        "delivery_status": "DELIVERED",
        "created_at": "...",
        "delivered_at": "..."
      }
    ]
  }
  ```

