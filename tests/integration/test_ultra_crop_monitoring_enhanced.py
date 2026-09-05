# tests/integration/test_ultra_crop_monitoring_enhanced.py
"""
Integration test suite for Ultra Crop Monitoring Enhanced Features:
1. Active Crops Endpoint with Human-Readable Stage Names
2. Dynamic Date-Aware Lifecycle & Event Calendar
3. Soil Fertility & Nutrient Status Engine (N, P, K, OC, pH, EC)
4. Mandatory 4-Question Action Format (WHAT, WHY, HOW, WHEN)
5. Weather-Aware Application & Rain Postponement
6. Pre-Harvest Marketplace 6d/3d/1d Reminders & Suppression
7. Source Transparency Tags
"""

import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_active_crops_endpoint():
    """Verify GET /api/v1/monitoring/active-crops returns active crops with human-readable stages."""
    response = client.get("/api/v1/monitoring/active-crops")
    assert response.status_code == 200
    data = response.json()
    assert "active_crops" in data
    assert len(data["active_crops"]) >= 1
    
    crop = data["active_crops"][0]
    assert "crop_name" in crop
    assert "human_stage_name" in crop
    assert "days_after_planting" in crop
    assert "planting_date" in crop
    assert "field_id" in crop
    
    # Ensure no internal day ranges in human_stage_name
    stage_name = crop["human_stage_name"]
    assert "days" not in stage_name.lower()


def test_soil_fertility_evaluation_low_n_and_oc():
    """Verify Soil Fertility engine correctly assesses Low N, Low OC, and Optimal pH/EC."""
    payload = {
        "farm_id": "FARM_TEST_01",
        "field_id": "FIELD_TEST_01",
        "crop": {
            "crop_name": "Wheat",
            "planting_date": (date.today() - timedelta(days=25)).isoformat(),
            "crop_stage_mode": "AUTO"
        },
        "telemetry": {
            "soil_nitrogen_mg_kg": 95.0,        # < 140 -> LOW
            "soil_phosphorus_mg_kg": 18.0,      # 10-25 -> ADEQUATE
            "soil_potassium_mg_kg": 200.0,      # 110-280 -> ADEQUATE
            "soil_organic_carbon_percent": 0.35,# < 0.50 -> LOW
            "soil_ph": 6.8,                     # 6.0-7.5 -> OPTIMAL
            "soil_ec_ds_m": 0.85                # < 1.0 -> NORMAL
        }
    }
    
    response = client.post("/api/v1/monitoring/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    fertility = data.get("soil_fertility", {})
    assert fertility.get("status") == "EVALUATED"
    assert fertility["nitrogen"]["status"] == "LOW"
    assert fertility["phosphorus"]["status"] == "ADEQUATE"
    assert fertility["potassium"]["status"] == "ADEQUATE"
    assert fertility["organic_carbon"]["status"] == "LOW"
    assert fertility["soil_ph"]["status"] == "OPTIMAL"
    assert fertility["soil_ec"]["status"] == "NORMAL"
    assert "Nitrogen (N)" in fertility["deficiencies"]
    assert "Organic Carbon (OC)" in fertility["deficiencies"]
    assert fertility.get("source") == "STAGE_MANAGEMENT_DATABASE"


def test_fertilizer_mandatory_4_question_format():
    """Verify fertilizer decision answers WHAT, WHY, HOW, and WHEN."""
    payload = {
        "farm_id": "FARM_TEST_02",
        "field_id": "FIELD_TEST_02",
        "crop": {
            "crop_name": "Wheat",
            "planting_date": (date.today() - timedelta(days=22)).isoformat(),
            "crop_stage_mode": "AUTO"
        },
        "telemetry": {
            "soil_nitrogen_mg_kg": 100.0,
            "soil_moisture_percent": 28.0
        }
    }
    
    response = client.post("/api/v1/monitoring/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    fert_dec = data.get("decisions", {}).get("fertilizer", {})
    assert "what" in fert_dec and len(fert_dec["what"]) > 10
    assert "why" in fert_dec and len(fert_dec["why"]) > 10
    assert "how" in fert_dec and len(fert_dec["how"]) > 10
    assert "when" in fert_dec and len(fert_dec["when"]) > 10
    assert fert_dec.get("source") == "STAGE_MANAGEMENT_DATABASE"
    
    # Check today_actions array
    today_actions = data.get("today_actions", [])
    assert len(today_actions) >= 1
    for act in today_actions:
        assert "what" in act
        assert "why" in act
        assert "how" in act
        assert "when" in act


def test_dynamic_date_aware_calendar():
    """Verify calendar generates stages timeline with real dates and daily action events."""
    planting_date = date.today() - timedelta(days=30)
    payload = {
        "farm_id": "FARM_TEST_03",
        "field_id": "FIELD_TEST_03",
        "crop": {
            "crop_name": "Wheat",
            "planting_date": planting_date.isoformat(),
            "crop_stage_mode": "AUTO"
        }
    }
    
    response = client.post("/api/v1/monitoring/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    cal = data.get("calendar", {})
    assert cal.get("source") == "STAGE_MANAGEMENT_DATABASE"
    assert cal.get("planting_date") == planting_date.isoformat()
    
    timeline = cal.get("stages_timeline", [])
    assert len(timeline) >= 3
    for st in timeline:
        assert "stage_name" in st
        assert "start_date" in st
        assert "end_date" in st
        assert "duration_days" in st
        # Ensure start_date is before end_date
        assert st["start_date"] <= st["end_date"]
    
    daily_events = cal.get("daily_events", [])
    assert len(daily_events) >= 3
    event_types = [e.get("event_type") for e in daily_events]
    assert "STAGE_TRANSITION" in event_types or "IRRIGATION" in event_types or "FERTILIZER" in event_types or "HARVEST" in event_types


def test_pre_harvest_marketplace_6d_3d_1d_schedule():
    """Verify pre-harvest marketplace reminders trigger at 6d, 3d, 1d and are suppressed when listed."""
    # Wheat harvest is typically ~120 days.
    # 1. Test 6-day reminder (age = 114)
    pdate_6d = (date.today() - timedelta(days=114)).isoformat()
    resp_6d = client.post("/api/v1/monitoring/analyze", json={
        "crop": { "crop_name": "Wheat", "planting_date": pdate_6d },
        "marketplace": { "crop_listed": False }
    })
    assert resp_6d.status_code == 200
    data_6d = resp_6d.json()
    mkt_6d = data_6d.get("marketplace", {}).get("listing_decision", {})
    assert mkt_6d.get("reminder") is True
    assert mkt_6d.get("reminder_type") == "FIRST_REMINDER"
    assert mkt_6d.get("days_to_harvest") == 6
    
    # 2. Test 3-day reminder (age = 117)
    pdate_3d = (date.today() - timedelta(days=117)).isoformat()
    resp_3d = client.post("/api/v1/monitoring/analyze", json={
        "crop": { "crop_name": "Wheat", "planting_date": pdate_3d },
        "marketplace": { "crop_listed": False }
    })
    assert resp_3d.status_code == 200
    mkt_3d = resp_3d.json().get("marketplace", {}).get("listing_decision", {})
    assert mkt_3d.get("reminder") is True
    assert mkt_3d.get("reminder_type") == "FOLLOW_UP_REMINDER"
    assert mkt_3d.get("days_to_harvest") == 3
    
    # 3. Test 1-day reminder (age = 119)
    pdate_1d = (date.today() - timedelta(days=119)).isoformat()
    resp_1d = client.post("/api/v1/monitoring/analyze", json={
        "crop": { "crop_name": "Wheat", "planting_date": pdate_1d },
        "marketplace": { "crop_listed": False }
    })
    assert resp_1d.status_code == 200
    mkt_1d = resp_1d.json().get("marketplace", {}).get("listing_decision", {})
    assert mkt_1d.get("reminder") is True
    assert mkt_1d.get("reminder_type") == "FINAL_REMINDER"
    assert mkt_1d.get("days_to_harvest") == 1
    
    # 4. Test suppression when crop_listed is True
    resp_suppressed = client.post("/api/v1/monitoring/analyze", json={
        "crop": { "crop_name": "Wheat", "planting_date": pdate_6d },
        "marketplace": { "crop_listed": True }
    })
    assert resp_suppressed.status_code == 200
    mkt_suppressed = resp_suppressed.json().get("marketplace", {})
    assert mkt_suppressed.get("crop_listed") is True
    assert mkt_suppressed.get("listing_decision", {}).get("reminder") is False


def test_weather_aware_rain_delay():
    """Verify rain probability >= 70% or rainfall >= 5mm causes weather postponement for fertilizer."""
    payload = {
        "crop": { "crop_name": "Wheat", "planting_date": (date.today() - timedelta(days=25)).isoformat() },
        "telemetry": {
            "rainfall_mm": 15.0  # heavy rain
        }
    }
    response = client.post("/api/v1/monitoring/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    fert_dec = data.get("decisions", {}).get("fertilizer", {})
    assert "DELAY" in fert_dec.get("weather_adjustment", "") or "rain" in fert_dec.get("weather_adjustment", "").lower()

