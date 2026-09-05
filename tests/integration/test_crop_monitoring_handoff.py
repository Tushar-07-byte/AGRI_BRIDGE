"""
AgriBridge AI/ML Handoff Package Zero-Regression Verification Suite
Tests all 16 registered crops, calendars, date-aware lifecycle calculations,
Open-Meteo weather context, dynamic calendar events, notification events,
Gemini recommendation generation, schema validation, and disease safety policies.
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# Add backend and ai_engine to sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = WORKSPACE_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(WORKSPACE_ROOT / "ai_engine"))

from app.crop_monitoring.crop_registry import (
    get_registered_crops,
    is_crop_supported,
    get_crop_metadata,
    get_scientific_calendar,
    get_management_calendar,
    SUPPORTED_CROPS_LIST,
)
from app.crop_monitoring.lifecycle_engine import calculate_crop_lifecycle
from app.crop_monitoring.weather_context import get_monitoring_weather_context, resolve_indian_coordinates
from app.crop_monitoring.calendar_engine import generate_calendar_events
from app.crop_monitoring.notification_engine import generate_farmer_notifications
from app.crop_monitoring.marketplace_context import get_marketplace_context
from app.crop_monitoring.safety_validator import validate_gemini_response, enforce_disease_safety_policy
from app.crop_monitoring.gemini_engine import generate_crop_recommendation, get_llm_api_key
from app.crop_monitoring.service import CropMonitoringService


def test_crop_registry():
    print("\n--- TEST 1: Crop Registry & 16 Indian Crops ---")
    crops = get_registered_crops()
    assert len(crops) >= 16, f"Expected at least 16 crops, found {len(crops)}"
    
    for crop in SUPPORTED_CROPS_LIST:
        assert is_crop_supported(crop), f"Crop {crop} should be supported"
        meta = get_crop_metadata(crop)
        assert meta.get("country") == "India", f"Crop {crop} metadata should indicate India"
        mgmt = get_management_calendar(crop)
        assert "stages" in mgmt, f"Management calendar for {crop} should contain stages"
        assert len(mgmt["stages"]) > 0, f"Management calendar for {crop} should have at least 1 stage"

    print(f"[PASSED]: All 16 registered crops validated ({', '.join(SUPPORTED_CROPS_LIST)})")


def test_crop_lifecycle():
    print("\n--- TEST 2: Date-Aware Crop Lifecycle & Dynamic Stages ---")
    
    # Test with planting date
    lifecycle_wheat = calculate_crop_lifecycle("wheat", planting_date="2026-09-01", reference_date="2026-09-25")
    assert lifecycle_wheat["days_after_planting"] == 24
    assert lifecycle_wheat["date_status"] == "available"
    assert "CRI" in lifecycle_wheat["current_stage"]
    assert lifecycle_wheat["next_stage"] is not None

    # Test with tomato Day 0
    lifecycle_tomato = calculate_crop_lifecycle("tomato", planting_date="2026-09-01", reference_date="2026-09-01")
    assert lifecycle_tomato["days_after_planting"] == 0
    assert "Transplanting" in lifecycle_tomato["current_stage"]

    # Test fallback without planting date
    lifecycle_no_date = calculate_crop_lifecycle("potato", current_stage="Vegetative")
    assert lifecycle_no_date["planting_date"] is None
    assert lifecycle_no_date["current_stage"] == "Vegetative"

    print("[PASSED]: Date-aware lifecycle and dynamic stage resolution verified.")


def test_weather_context():
    print("\n--- TEST 3: Open-Meteo Dynamic Location Weather & Risk Context ---")
    import asyncio
    lat, lon = resolve_indian_coordinates(state="Uttar Pradesh", district="Sultanpur")
    assert lat is not None and lon is not None

    weather_ctx = asyncio.run(get_monitoring_weather_context(
        state="Uttar Pradesh",
        district="Sultanpur",
        village="Dhanpatganj"
    ))
    assert "current_weather" in weather_ctx
    assert "forecast_7d" in weather_ctx
    assert "risks" in weather_ctx
    assert weather_ctx["decision"] in ["Keep", "Monitor", "Postpone"]
    assert "weather_summary" in weather_ctx

    print(f"[PASSED]: Open-Meteo context loaded. Decision: {weather_ctx['decision']}, Overall Risk: {weather_ctx['risks']['overall_risk']}")


def test_calendar_events():
    print("\n--- TEST 4: Dynamic Calendar Event Generation ---")
    
    events = generate_calendar_events(
        crop_id="wheat",
        planting_date="2026-09-01",
        farmer_id="FARMER_UP_001"
    )
    assert len(events) >= 5, f"Expected at least 5 events for wheat, got {len(events)}"
    first_event = events[0]
    assert first_event["event_id"].startswith("WHEAT_EVENT_")
    assert first_event["crop_id"] == "wheat"
    assert first_event["calendar_status"] == "scheduled"
    assert "activity" in first_event

    print(f"[PASSED]: Generated {len(events)} calendar events successfully.")


def test_farmer_notifications():
    print("\n--- TEST 5: Farmer Notification Event Generation ---")
    
    notifications = generate_farmer_notifications(
        crop_id="rice",
        planting_date="2026-09-01",
        current_stage="Transplanting",
        farmer_id="FARMER_WB_001"
    )
    assert len(notifications) >= 1
    assert any(n["type"] == "stage_management_reminder" for n in notifications)

    print(f"[PASSED]: Generated {len(notifications)} structured farmer notification events.")


def test_marketplace_context():
    print("\n--- TEST 6: Marketplace Context Integration ---")
    
    mp_ctx = get_marketplace_context("tomato")
    assert mp_ctx["marketplace_available"] is True
    assert "Marketplace" in mp_ctx["marketplace_guidance"]

    print("[PASSED]: Marketplace context successfully retrieved.")


def test_disease_safety_policy():
    print("\n--- TEST 7: Strict Disease Safety Policy Enforcement ---")
    
    unsafe_data = {
        "crop_protection_guidance": "I diagnose Early Blight on your plant.",
        "safety_information": ""
    }
    safe_data = enforce_disease_safety_policy(unsafe_data)
    assert "I diagnose" not in safe_data["crop_protection_guidance"]
    assert "inspection-only" in safe_data["crop_protection_guidance"].lower()
    assert "inspection-only" in safe_data["safety_information"].lower()

    print("[PASSED]: Disease safety policy strictly enforced (Inspection-Only).")


def test_schema_validation():
    print("\n--- TEST 8: Response Schema Validation Against gemini_response_schema.json ---")
    
    sample_response = {
        "current_stage": "Sowing",
        "stage_status": "Active (Day 0)",
        "next_stage": "CRI (Day 20-25)",
        "weather_summary": "Clear conditions at 28°C",
        "weather_risk": "low",
        "weather_decision": "Keep",
        "recommended_action": "Proceed with sowing",
        "irrigation_guidance": "Light irrigation after sowing",
        "fertilizer_guidance": "50kg DAP basal",
        "crop_protection_guidance": "Inspect seeds before planting",
        "monitoring_guidance": "Scout for uniform germination",
        "marketplace_guidance": "Marketplace available",
        "safety_information": "Follow registered label guidance",
        "important_note": "Scientific guidance from AgriBridge",
        "sources": ["AgriBridge Calendar"]
    }
    is_valid, validated, missing = validate_gemini_response(sample_response)
    assert is_valid, f"Expected valid response, missing: {missing}"
    assert len(missing) == 0

    print("[PASSED]: Structured response schema validated.")


def test_full_recommendation():
    print("\n--- TEST 9: Full Production Crop Recommendation Flow ---")
    import asyncio
    
    res = asyncio.run(CropMonitoringService.get_recommendation(
        state="Uttar Pradesh",
        district="Sultanpur",
        village="Dhanpatganj",
        crop_id="wheat",
        planting_date="2026-09-01",
        current_stage="Sowing"
    ))
    assert res["success"] is True
    rec = res["recommendation"]
    
    # Check all required fields from gemini_response_schema.json
    required_fields = [
        "current_stage", "stage_status", "next_stage", "weather_summary",
        "weather_risk", "weather_decision", "recommended_action",
        "irrigation_guidance", "fertilizer_guidance", "crop_protection_guidance",
        "monitoring_guidance", "marketplace_guidance", "safety_information",
        "important_note", "sources"
    ]
    for field in required_fields:
        assert field in rec, f"Missing required field {field} in recommendation"
        assert rec[field] is not None or field == "next_stage", f"Field {field} should not be None"

    print("[PASSED]: Full production recommendation generated and schema-compliant.")


def test_fastapi_endpoints():
    print("\n--- TEST 10: FastAPI Endpoints & App Integration ---")
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    
    # 1. Health check
    resp = client.get("/api/crop-monitoring/health")
    assert resp.status_code == 200
    assert resp.json()["supported_crops_count"] == 16

    # 2. Crops list
    resp = client.get("/api/crop-monitoring/crops")
    assert resp.status_code == 200
    assert resp.json()["count"] == 16

    # 3. Calendar details
    resp = client.get("/api/crop-monitoring/calendar/wheat")
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # 4. Lifecycle post
    resp = client.post("/api/crop-monitoring/lifecycle", json={
        "crop_id": "wheat",
        "planting_date": "2026-09-01",
        "reference_date": "2026-09-21"
    })
    assert resp.status_code == 200
    assert resp.json()["lifecycle"]["days_after_planting"] == 20

    # 5. Events post
    resp = client.post("/api/crop-monitoring/events", json={
        "crop_id": "rice",
        "planting_date": "2026-09-01"
    })
    assert resp.status_code == 200
    assert resp.json()["count"] > 0

    # 6. Notifications post
    resp = client.post("/api/crop-monitoring/notifications", json={
        "crop_id": "tomato",
        "planting_date": "2026-09-01",
        "current_stage": "Transplanting"
    })
    assert resp.status_code == 200
    assert resp.json()["count"] > 0

    # 7. Recommendation post
    resp = client.post("/api/crop-monitoring/recommend", json={
        "state": "Uttar Pradesh",
        "district": "Sultanpur",
        "village": "Dhanpatganj",
        "crop_id": "wheat",
        "planting_date": "2026-09-01",
        "current_stage": "Sowing"
    })
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # 8. Guidance package get
    resp = client.get("/api/crop-monitoring/guidance-package")
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert "package" in resp.json()

    # 9. Journey context get
    resp = client.get("/api/crop-monitoring/journey-context")
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert "journey_context" in resp.json()

    print("[PASSED]: All FastAPI Crop Monitoring endpoints respond with 200 OK.")


async def main():
    test_crop_registry()
    test_crop_lifecycle()
    await test_weather_context()
    test_calendar_events()
    test_farmer_notifications()
    test_marketplace_context()
    test_disease_safety_policy()
    test_schema_validation()
    await test_full_recommendation()
    test_fastapi_endpoints()
    print("\n============================================================")
    print("ALL 10 AI/ML HANDOFF VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("============================================================\n")


if __name__ == "__main__":
    asyncio.run(main())
