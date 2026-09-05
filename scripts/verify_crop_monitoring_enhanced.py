# scripts/verify_crop_monitoring_enhanced.py
"""
Automated Verification for AgriBridge AI Final Crop Monitoring Enhancement:
1. Active Crops Endpoint & Human-Readable Stages
2. Dynamic Date-Aware Lifecycle & Event Calendar
3. Soil Fertility & Nutrient Status Engine
4. Mandatory 4-Question Action Format
5. Pre-Harvest Marketplace 6d/3d/1d Schedule & Suppression
6. Weather-Aware Rain Postponement
7. Source Transparency Tagging
"""

import sys
import os
from datetime import date, timedelta

# Add workspace and backend to path
workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(workspace_dir, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_tests():
    passed = 0
    failed = 0

    def test(name, fn):
        nonlocal passed, failed
        try:
            fn()
            print(f"  [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("================================================================")
    print("AGRIBRIDGE AI — FINAL CROP MONITORING ENHANCEMENT VERIFICATION")
    print("================================================================")

    # 1. Active Crops Endpoint
    def test_active_crops():
        res = client.get("/api/v1/monitoring/active-crops")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        assert "active_crops" in data, "Missing 'active_crops'"
        crops = data["active_crops"]
        assert len(crops) >= 1, "Expected at least 1 active crop"
        for c in crops:
            assert "crop_name" in c and c["crop_name"]
            assert "human_stage_name" in c and c["human_stage_name"]
            assert "days_after_planting" in c
            assert "planting_date" in c
            assert "field_id" in c
            # Clean human name check: no day ranges like '20-25 days'
            assert "days" not in c["human_stage_name"].lower()
    test("1. Active Crops in Farmer Dashboard & Clean Human Stage Names", test_active_crops)

    # 2. Dynamic Date-Aware Lifecycle & Event Calendar
    def test_dynamic_calendar():
        pdate = (date.today() - timedelta(days=43)).isoformat()
        res = client.post("/api/v1/monitoring/analyze", json={
            "crop": { "crop_name": "Wheat", "planting_date": pdate, "crop_stage_mode": "AUTO" }
        })
        assert res.status_code == 200
        data = res.json()
        cal = data.get("calendar", {})
        assert cal.get("source") == "STAGE_MANAGEMENT_DATABASE"
        assert cal.get("planting_date") == pdate
        assert len(cal.get("stages_timeline", [])) >= 3
        for st in cal["stages_timeline"]:
            assert "stage_name" in st
            assert "start_date" in st and "end_date" in st
            assert st["start_date"] <= st["end_date"]
        
        events = cal.get("daily_events", [])
        assert len(events) >= 3
        types = [e["event_type"] for e in events]
        assert "STAGE_TRANSITION" in types or "IRRIGATION" in types or "FERTILIZER" in types
    test("2. Dynamic Date-Aware Lifecycle & Event Calendar", test_dynamic_calendar)

    # 3. Soil Fertility & Nutrient Engine
    def test_soil_fertility():
        res = client.post("/api/v1/monitoring/analyze", json={
            "crop": { "crop_name": "Wheat", "planting_date": (date.today() - timedelta(days=30)).isoformat() },
            "telemetry": {
                "soil_nitrogen_mg_kg": 95.0,        # < 140 -> LOW
                "soil_phosphorus_mg_kg": 18.0,      # 10-25 -> ADEQUATE
                "soil_potassium_mg_kg": 200.0,      # 110-280 -> ADEQUATE
                "soil_organic_carbon_percent": 0.35,# < 0.50 -> LOW
                "soil_ph": 6.8,                     # 6.0-7.5 -> OPTIMAL
                "soil_ec_ds_m": 0.85                # < 1.0 -> NORMAL
            }
        })
        assert res.status_code == 200
        data = res.json()
        fert = data.get("soil_fertility", {})
        assert fert.get("status") == "EVALUATED"
        assert fert["nitrogen"]["status"] == "LOW"
        assert fert["phosphorus"]["status"] == "ADEQUATE"
        assert fert["potassium"]["status"] == "ADEQUATE"
        assert fert["organic_carbon"]["status"] == "LOW"
        assert fert["soil_ph"]["status"] == "OPTIMAL"
        assert fert["soil_ec"]["status"] == "NORMAL"
        assert "Nitrogen (N)" in fert["deficiencies"]
        assert "Organic Carbon (OC)" in fert["deficiencies"]
        assert fert.get("source") == "STAGE_MANAGEMENT_DATABASE"
    test("3. Soil Fertility & Nutrient Status Engine (NPK, OC, pH, EC)", test_soil_fertility)

    # 4. Mandatory 4-Question Format
    def test_mandatory_4q():
        res = client.post("/api/v1/monitoring/analyze", json={
            "crop": { "crop_name": "Wheat", "planting_date": (date.today() - timedelta(days=22)).isoformat() }
        })
        assert res.status_code == 200
        data = res.json()
        fert_dec = data.get("decisions", {}).get("fertilizer", {})
        assert "what" in fert_dec and len(fert_dec["what"]) > 10, "Missing WHAT in fertilizer"
        assert "why" in fert_dec and len(fert_dec["why"]) > 10, "Missing WHY in fertilizer"
        assert "how" in fert_dec and len(fert_dec["how"]) > 10, "Missing HOW in fertilizer"
        assert "when" in fert_dec and len(fert_dec["when"]) > 10, "Missing WHEN in fertilizer"
        
        today_actions = data.get("today_actions", [])
        assert len(today_actions) >= 1
        for act in today_actions:
            assert "what" in act and "why" in act and "how" in act and "when" in act
    test("4. Mandatory 4-Question Action Format (WHAT, WHY, HOW, WHEN)", test_mandatory_4q)

    # 5. Pre-Harvest Marketplace 6d, 3d, 1d Reminders
    def test_marketplace_schedule():
        # 6 days
        p6d = (date.today() - timedelta(days=114)).isoformat()
        r6d = client.post("/api/v1/monitoring/analyze", json={
            "crop": { "crop_name": "Wheat", "planting_date": p6d },
            "marketplace": { "crop_listed": False }
        }).json()
        assert r6d["marketplace"]["listing_decision"]["reminder"] is True
        assert r6d["marketplace"]["listing_decision"]["reminder_type"] == "FIRST_REMINDER"

        # 3 days
        p3d = (date.today() - timedelta(days=117)).isoformat()
        r3d = client.post("/api/v1/monitoring/analyze", json={
            "crop": { "crop_name": "Wheat", "planting_date": p3d },
            "marketplace": { "crop_listed": False }
        }).json()
        assert r3d["marketplace"]["listing_decision"]["reminder"] is True
        assert r3d["marketplace"]["listing_decision"]["reminder_type"] == "FOLLOW_UP_REMINDER"

        # 1 day
        p1d = (date.today() - timedelta(days=119)).isoformat()
        r1d = client.post("/api/v1/monitoring/analyze", json={
            "crop": { "crop_name": "Wheat", "planting_date": p1d },
            "marketplace": { "crop_listed": False }
        }).json()
        assert r1d["marketplace"]["listing_decision"]["reminder"] is True
        assert r1d["marketplace"]["listing_decision"]["reminder_type"] == "FINAL_REMINDER"

        # Suppressed when crop_listed is True
        r_sup = client.post("/api/v1/monitoring/analyze", json={
            "crop": { "crop_name": "Wheat", "planting_date": p6d },
            "marketplace": { "crop_listed": True }
        }).json()
        assert r_sup["marketplace"]["crop_listed"] is True
        assert r_sup["marketplace"]["listing_decision"]["reminder"] is False
    test("5. Pre-Harvest Marketplace 6d/3d/1d Schedule & Suppression", test_marketplace_schedule)

    # 6. Weather-Aware Rain Postponement
    def test_weather_aware_rain():
        res = client.post("/api/v1/monitoring/analyze", json={
            "crop": { "crop_name": "Wheat", "planting_date": (date.today() - timedelta(days=22)).isoformat() },
            "telemetry": { "rainfall_mm": 18.0 }
        })
        assert res.status_code == 200
        data = res.json()
        fert_dec = data["decisions"]["fertilizer"]
        assert "DELAY" in fert_dec.get("weather_adjustment", "") or "rain" in fert_dec.get("weather_adjustment", "").lower()
    test("6. Weather-Aware Rain Postponement for Nutrient Application", test_weather_aware_rain)

    # 7. Source Transparency Tagging
    def test_source_transparency():
        res = client.post("/api/v1/monitoring/analyze", json={
            "crop": { "crop_name": "Wheat", "planting_date": (date.today() - timedelta(days=25)).isoformat() }
        })
        assert res.status_code == 200
        data = res.json()
        assert data["weather"]["source"] == "LIVE_REAL"
        assert data["iot"]["source"] == "SYNTHETIC_HACKATHON_DEMO"
        assert data["soil_fertility"]["source"] == "STAGE_MANAGEMENT_DATABASE"
        assert data["calendar"]["source"] == "STAGE_MANAGEMENT_DATABASE"
        assert data["farmer_guidance"]["source"] == "EXPLANATION_LAYER_ONLY"
    test("7. Source Transparency Tagging (LIVE_REAL, SYNTHETIC, DATABASE, GEMINI)", test_source_transparency)

    print("================================================================")
    print(f"VERIFICATION RESULTS: {passed} PASSED, {failed} FAILED")
    print("================================================================")
    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
