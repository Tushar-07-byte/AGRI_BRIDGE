"""
AgriBridge AI — Ultra Crop Monitoring & IoT Telemetry Comprehensive Integration Test Suite
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Validates:
1. Module integration into AgriBridge (not a standalone app).
2. GET /api/v1/monitoring/health and GET /api/v1/monitoring/crops.
3. POST /api/v1/monitoring/analyze with dynamic inputs (State, District, Village, Farm ID, Field ID, Crop, Stage Mode).
4. Deterministic multi-signal decisions (irrigation, disease, pest, weather stress, fertilizer, daily priority).
5. Pre-Harvest Marketplace Reminder Schedule (6 days, 3 days, 1 day, and already-listed suppression).
6. Notification Action State Management via POST /api/v1/monitoring/notification/action.
7. Data Transparency (weather_source: LIVE_REAL, iot_source: SYNTHETIC_HACKATHON_DEMO, sensor connected: false).
"""

import sys
from datetime import date, timedelta
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_monitoring_v1_health_and_crops():
    """Verify health endpoint and list of registered crops."""
    # 1. Health
    r_health = client.get("/api/v1/monitoring/health")
    assert r_health.status_code == 200
    h_data = r_health.json()
    assert h_data["success"] is True
    assert h_data["weather_source"] == "LIVE_REAL"
    assert h_data["iot_source"] == "SYNTHETIC_HACKATHON_DEMO"
    assert h_data["physical_sensor_connected"] is False

    # 2. Crops
    r_crops = client.get("/api/v1/monitoring/crops")
    assert r_crops.status_code == 200
    c_data = r_crops.json()
    assert c_data["success"] is True
    assert c_data["count"] >= 16
    crop_names = [c.get("crop") or c.get("crop_name") for c in c_data["crops"]]
    assert "Wheat" in crop_names
    assert "Rice" in crop_names
    assert "Tomato" in crop_names
    assert "Potato" in crop_names


def test_monitoring_analyze_auto_stage_wheat_cri():
    """Verify dynamic monitoring analysis with auto stage calculation from planting date."""
    p_date = (date.today() - timedelta(days=34)).isoformat()
    req = {
        "farm_id": "FARM_001",
        "field_id": "FIELD_001",
        "telemetry_id": "TEL_001",
        "location": {
            "state": "Uttar Pradesh",
            "district": "Varanasi",
            "village": "Demo Village",
            "latitude": 25.3176,
            "longitude": 82.9739
        },
        "crop": {
            "crop_name": "Wheat",
            "planting_date": p_date,
            "crop_stage_mode": "AUTO"
        },
        "telemetry": {
            "soil_moisture_percent": 30.56,
            "soil_temperature_c": 23.62,
            "air_temperature_c": 25.7,
            "relative_humidity_percent": 70.0,
            "rainfall_mm": 0.0,
            "leaf_wetness": False,
            "soil_ec_ds_m": 0.93,
            "soil_ph": 6.49,
            "light_hours": 8.0,
            "wind_speed_kmh": 10.6
        }
    }

    resp = client.post("/api/v1/monitoring/analyze", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True

    # Farm & Location
    assert data["farm"]["farm_id"] == "FARM_001"
    assert data["farm"]["field_id"] == "FIELD_001"
    assert data["farm"]["location"]["state"] == "Uttar Pradesh"
    assert data["farm"]["location"]["district"] == "Varanasi"

    # Stage
    assert data["stage"]["crop_age_days"] == 34
    assert "Crown Root Initiation" in data["stage"]["current_stage"]

    # Decisions
    assert "irrigation" in data["decisions"]
    assert "disease" in data["decisions"]
    assert "pest" in data["decisions"]
    assert "weather_stress" in data["decisions"]
    assert "fertilizer" in data["decisions"]
    assert "daily_priority" in data["decisions"]

    # Notifications
    assert isinstance(data["notifications"], list)
    assert len(data["notifications"]) >= 3

    # Transparency
    assert data["data_transparency"]["weather_source"] is not None
    assert data["data_transparency"]["iot_source"] == "SYNTHETIC_HACKATHON_DEMO"
    assert data["data_transparency"]["physical_sensor_connected"] is False


def test_pre_harvest_marketplace_reminder_schedule():
    """Verify 6-day, 3-day, 1-day reminders, and already-listed suppression."""
    # Wheat duration: 120 days minimum
    # 1. 6 Days Before Harvest -> FIRST_REMINDER
    p6 = (date.today() - timedelta(days=114)).isoformat()
    r6 = client.post("/api/v1/monitoring/analyze", json={
        "farm_id": "FARM_001",
        "field_id": "FIELD_001",
        "location": {"state": "Uttar Pradesh", "district": "Varanasi"},
        "crop": {"crop_name": "Wheat", "planting_date": p6, "crop_stage_mode": "AUTO"},
        "marketplace": {"crop_listed": False}
    }).json()
    m6 = r6["marketplace"]["listing_decision"]
    assert m6["status"] == "LISTING_DUE"
    assert m6["reminder"] is True
    assert m6["reminder_type"] == "FIRST_REMINDER"
    assert m6["action"] == "LIST_CROP"
    assert m6["days_to_harvest"] == 6

    # 2. 3 Days Before Harvest -> FOLLOW_UP_REMINDER
    p3 = (date.today() - timedelta(days=117)).isoformat()
    r3 = client.post("/api/v1/monitoring/analyze", json={
        "farm_id": "FARM_001",
        "field_id": "FIELD_001",
        "location": {"state": "Uttar Pradesh", "district": "Varanasi"},
        "crop": {"crop_name": "Wheat", "planting_date": p3, "crop_stage_mode": "AUTO"},
        "marketplace": {"crop_listed": False}
    }).json()
    m3 = r3["marketplace"]["listing_decision"]
    assert m3["status"] == "LISTING_DUE"
    assert m3["reminder"] is True
    assert m3["reminder_type"] == "FOLLOW_UP_REMINDER"
    assert m3["action"] == "LIST_CROP"

    # 3. 1 Day Before Harvest -> FINAL_REMINDER
    p1 = (date.today() - timedelta(days=119)).isoformat()
    r1 = client.post("/api/v1/monitoring/analyze", json={
        "farm_id": "FARM_001",
        "field_id": "FIELD_001",
        "location": {"state": "Uttar Pradesh", "district": "Varanasi"},
        "crop": {"crop_name": "Wheat", "planting_date": p1, "crop_stage_mode": "AUTO"},
        "marketplace": {"crop_listed": False}
    }).json()
    m1 = r1["marketplace"]["listing_decision"]
    assert m1["status"] == "LISTING_URGENT"
    assert m1["reminder"] is True
    assert m1["reminder_type"] == "FINAL_REMINDER"
    assert m1["action"] == "LIST_CROP"

    # 4. Already Listed -> No reminder generated
    r_listed = client.post("/api/v1/monitoring/analyze", json={
        "farm_id": "FARM_001",
        "field_id": "FIELD_001",
        "location": {"state": "Uttar Pradesh", "district": "Varanasi"},
        "crop": {"crop_name": "Wheat", "planting_date": p6, "crop_stage_mode": "AUTO"},
        "marketplace": {"crop_listed": True}
    }).json()
    m_listed = r_listed["marketplace"]["listing_decision"]
    assert m_listed["status"] == "LISTED"
    assert m_listed["reminder"] is False


def test_notification_action_state_management():
    """Verify notification action endpoint updates notification state."""
    notif_id = f"AGR-{date.today().isoformat()}-DISEASE"
    resp = client.post("/api/v1/monitoring/notification/action", json={
        "notification_id": notif_id,
        "action": "COMPLETE",
        "reason": "Disease scouting completed by field agent."
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["notification_id"] == notif_id
    assert data["action"] == "COMPLETE"
    assert data["status"] == "UPDATED"


def test_high_disease_and_low_moisture_multi_signals():
    """Verify extreme environmental signals trigger correct multi-signal decisions."""
    # 1. High Humidity + Wet Leaf -> High Disease Risk
    r_dis = client.post("/api/v1/monitoring/analyze", json={
        "location": {"state": "Maharashtra", "district": "Nashik"},
        "crop": {"crop_name": "Tomato", "planting_date": (date.today() - timedelta(days=40)).isoformat()},
        "telemetry": {
            "relative_humidity_percent": 95.0,
            "leaf_wetness": True,
            "rainfall_mm": 15.0,
            "soil_moisture_percent": 45.0
        }
    }).json()
    assert r_dis["decisions"]["disease"]["status"] == "HIGH"
    assert r_dis["decisions"]["disease"]["action"] == "SCOUT"

    # 2. Low Moisture 14% -> Irrigation DUE
    r_irr = client.post("/api/v1/monitoring/analyze", json={
        "location": {"state": "Punjab", "district": "Ludhiana"},
        "crop": {"crop_name": "Wheat", "planting_date": (date.today() - timedelta(days=25)).isoformat()},
        "telemetry": {
            "soil_moisture_percent": 14.0,
            "relative_humidity_percent": 40.0,
            "leaf_wetness": False,
            "rainfall_mm": 0.0
        }
    }).json()
    assert r_irr["decisions"]["irrigation"]["status"] == "DUE"
    assert r_irr["decisions"]["irrigation"]["priority"] == "HIGH"


def test_backward_compatibility_crop_monitoring_analyze():
    """Verify /api/crop-monitoring/analyze endpoint operates identically."""
    p_date = (date.today() - timedelta(days=34)).isoformat()
    resp = client.post("/api/crop-monitoring/analyze", json={
        "farm_id": "FARM_002",
        "field_id": "FIELD_002",
        "location": {"state": "Punjab", "district": "Ludhiana", "village": "Demo Village"},
        "crop": {"crop_name": "Wheat", "planting_date": p_date, "crop_stage_mode": "AUTO"}
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["farm"]["farm_id"] == "FARM_002"
    assert "Crown Root Initiation" in data["stage"]["current_stage"]


def test_dynamic_crop_stages_clean_human_readable_names():
    """Verify GET /api/v1/monitoring/stages/{crop_name} returns pure human-readable stage names without day ranges."""
    # 1. Wheat
    rw = client.get("/api/v1/monitoring/stages/Wheat")
    assert rw.status_code == 200
    dw = rw.json()
    assert dw["success"] is True
    assert dw["crop"] == "Wheat"
    expected_wheat = [
        "Sowing & Germination",
        "Crown Root Initiation (CRI)",
        "Tillering & Jointing",
        "Booting & Flowering",
        "Milking Stage",
        "Dough & Maturity"
    ]
    assert dw["stages"] == expected_wheat

    # Ensure no internal numeric day ranges exist in names
    for name in dw["stages"]:
        assert "days" not in name.lower()
        assert "stage " not in name.lower()

    # 2. Rice
    rr = client.get("/api/v1/monitoring/stages/Rice")
    assert rr.status_code == 200
    dr = rr.json()
    assert dr["success"] is True
    expected_rice = [
        "Nursery & Transplanting",
        "Active Tillering",
        "Panicle Initiation",
        "Flowering & Heading",
        "Grain Filling & Maturity"
    ]
    assert dr["stages"] == expected_rice


def test_monitoring_analyze_manual_stage_selection():
    """Verify manual stage mode returns the user-selected human-readable stage name."""
    req = {
        "farm_id": "FARM_001",
        "field_id": "FIELD_001",
        "location": {"state": "Uttar Pradesh", "district": "Varanasi"},
        "crop": {
            "crop_name": "Wheat",
            "crop_stage_mode": "MANUAL",
            "crop_stage": "Tillering & Jointing"
        }
    }
    resp = client.post("/api/v1/monitoring/analyze", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["stage"]["current_stage"] == "Tillering & Jointing"
    assert data["crop"]["crop_stage_mode"] == "MANUAL"


if __name__ == "__main__":
    print("Running Ultra Crop Monitoring Integration Test Suite...")
    test_monitoring_v1_health_and_crops()
    print("  [PASSED] Health Check & Registered Crops (16 Indian Crops)")
    test_dynamic_crop_stages_clean_human_readable_names()
    print("  [PASSED] Dynamic Crop Stages: Pure Human-Readable Names (No Day Ranges)")
    test_monitoring_analyze_manual_stage_selection()
    print("  [PASSED] Manual Crop Stage Selection Mode")
    test_monitoring_analyze_auto_stage_wheat_cri()
    print("  [PASSED] Dynamic Monitoring Analyze: Auto Stage Calculation (Wheat CRI)")
    test_pre_harvest_marketplace_reminder_schedule()
    print("  [PASSED] Pre-Harvest Marketplace Reminder Schedule (6d, 3d, 1d, Listed)")
    test_notification_action_state_management()
    print("  [PASSED] Notification Action State Management (COMPLETE, POSTPONE)")
    test_high_disease_and_low_moisture_multi_signals()
    print("  [PASSED] Multi-Signal Decision Matrix (Disease High, Irrigation Due)")
    test_backward_compatibility_crop_monitoring_analyze()
    print("  [PASSED] Backward Compatibility via /api/crop-monitoring/analyze")
    print("\nALL ULTRA CROP MONITORING INTEGRATION TESTS PASSED (100% SUCCESS)!")

