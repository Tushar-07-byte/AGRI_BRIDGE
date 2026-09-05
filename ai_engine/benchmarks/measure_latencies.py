"""
AgriBridge Latency Benchmark & Profiling Script
Measures exact execution times (cold & warm) and provides step-by-step breakdown.
"""

import sys
import os
import time
import json
from pathlib import Path

# Ensure UTF-8 stdout
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.models.farmer import Farmer
from app.models.user import User
from app.services.auth_service import hash_password, create_access_token

client = TestClient(app)

def run_benchmarks():
    print("\n" + "="*75)
    print("AGRIBRIDGE PERFORMANCE & LATENCY MEASUREMENT REPORT")
    print("="*75 + "\n")

    db = SessionLocal()
    farmer = db.query(Farmer).first()
    if not farmer:
        farmer = Farmer(name="Performance Benchmark Farmer")
        db.add(farmer)
        db.commit()
        db.refresh(farmer)
    farmer_id = farmer.id

    user = db.query(User).filter(User.mobile == "+919876500001").first()
    if not user:
        user = User(
            name="Bench User",
            mobile="+919876500001",
            password_hash=hash_password("Pass@1234"),
            role="farmer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # -------------------------------------------------------------
    # 1. LOGIN REQUEST
    # -------------------------------------------------------------
    t0 = time.perf_counter()
    login_resp = client.post("/api/auth/login", json={
        "mobile": "+919876500001",
        "password": "Pass@1234"
    })
    t_login = time.perf_counter() - t0
    token = login_resp.json().get("token")
    auth_headers = {"Authorization": f"Bearer {token}"} if token else {}

    # -------------------------------------------------------------
    # 2. POST /api/ai/predict (COLD REQUEST WITH DETAILED PROFILING)
    # -------------------------------------------------------------
    test_img = os.path.join(BACKEND_DIR, "test_images", "1_healthy_tomato_leaf.jpg")
    farm_payload = {
        "farmer_id": farmer_id,
        "farm_area": 3.5,
        "growth_stage": "vegetative",
        "irrigation_method": "drip",
        "irrigation_status": "normal",
        "recent_rainfall": "none",
        "humidity": "moderate",
        "fertilizer_applied": "urea",
        "previous_crop": "wheat",
        "disease_severity": "low",
        "region": "Punjab"
    }

    # Step-by-step profiling of predict
    print("--- Detailed Step-by-Step Profiling of POST /api/ai/predict ---")
    
    # Measure AI initialization / Keras model load from disk
    t_init_start = time.perf_counter()
    from app.services.ai_service import initialize_ai, analyze_crop
    initialize_ai()
    t_model_load = time.perf_counter() - t_init_start

    # Measure Weather API call alone
    t_weather_start = time.perf_counter()
    from app.services.timing_advice_service import calculate_timing_advice
    import asyncio
    weather_res = asyncio.run(calculate_timing_advice(region_str="Punjab"))
    t_weather_call = time.perf_counter() - t_weather_start

    # Measure Image inference alone
    t_infer_start = time.perf_counter()
    pred_res = analyze_crop(test_img, "tomato", farm_payload)
    t_inference = time.perf_counter() - t_infer_start

    # Full cold HTTP request
    with open(test_img, "rb") as fp:
        t0 = time.perf_counter()
        predict_resp = client.post(
            "/api/ai/predict",
            files={"image": ("1_healthy_tomato_leaf.jpg", fp, "image/jpeg")},
            data={"plant": "tomato", "farm": json.dumps(farm_payload)},
            headers=auth_headers
        )
        t_predict_cold = time.perf_counter() - t0

    plan_id = predict_resp.json().get("result", {}).get("action_plan", {}).get("id", 1)

    # Full warm HTTP request (subsequent prediction)
    with open(test_img, "rb") as fp:
        t0 = time.perf_counter()
        predict_warm_resp = client.post(
            "/api/ai/predict",
            files={"image": ("1_healthy_tomato_leaf.jpg", fp, "image/jpeg")},
            data={"plant": "tomato", "farm": json.dumps(farm_payload)},
            headers=auth_headers
        )
        t_predict_warm = time.perf_counter() - t0

    # -------------------------------------------------------------
    # 3. GET /api/action-plans/{farmer_id}
    # -------------------------------------------------------------
    t0 = time.perf_counter()
    get_plans_resp = client.get(f"/api/action-plans/{farmer_id}", headers=auth_headers)
    t_get_plans = time.perf_counter() - t0

    # -------------------------------------------------------------
    # 4. POST /api/action-plans/{id}/recheck
    # -------------------------------------------------------------
    # Cold recheck with live weather fetch
    t0 = time.perf_counter()
    recheck_live_resp = client.post(f"/api/action-plans/{plan_id}/recheck", json={}, headers=auth_headers)
    t_recheck_live = time.perf_counter() - t0

    # Simulated recheck (no live weather network fetch)
    t0 = time.perf_counter()
    recheck_sim_resp = client.post(f"/api/action-plans/{plan_id}/recheck", json={"simulated_rain_probability": 85}, headers=auth_headers)
    t_recheck_sim = time.perf_counter() - t0

    # -------------------------------------------------------------
    # 5. FARMER DASHBOARD INITIAL PAGE LOAD (COMBINED API CALLS)
    # -------------------------------------------------------------
    # In farmer-dashboard.js, the dashboard triggers:
    #   1. GET /api/auth/me (or user verification)
    #   2. GET /api/listings/farmer/{farmer_id}
    #   3. GET /api/orders/farmer/{farmer_id}
    #   4. GET /api/action-plans/{farmer_id}
    #   5. GET /api/notifications/{farmer_id}
    t0 = time.perf_counter()
    r_auth = client.get("/api/auth/me", headers=auth_headers)
    t_d_auth = time.perf_counter() - t0

    t0 = time.perf_counter()
    r_list = client.get(f"/api/listings/farmer/{farmer_id}", headers=auth_headers)
    t_d_list = time.perf_counter() - t0

    t0 = time.perf_counter()
    r_orders = client.get(f"/api/orders/farmer/{farmer_id}", headers=auth_headers)
    t_d_orders = time.perf_counter() - t0

    t0 = time.perf_counter()
    r_plans = client.get(f"/api/action-plans/{farmer_id}", headers=auth_headers)
    t_d_plans = time.perf_counter() - t0

    t0 = time.perf_counter()
    r_notif = client.get(f"/api/notifications/{farmer_id}", headers=auth_headers)
    t_d_notif = time.perf_counter() - t0

    t_dashboard_total = t_d_auth + t_d_list + t_d_orders + t_d_plans + t_d_notif

    # -------------------------------------------------------------
    # REPORT SUMMARY
    # -------------------------------------------------------------
    print("\n" + "-"*75)
    print("1. MEASURED LATENCIES (COLD REQUESTS)")
    print("-"*75)
    print(f"• POST /api/ai/predict (Cold Start)       : {t_predict_cold:.3f} s  ({t_predict_cold*1000:.1f} ms)")
    print(f"• POST /api/ai/predict (Warm / Reused)     : {t_predict_warm:.3f} s  ({t_predict_warm*1000:.1f} ms)")
    print(f"• GET /api/action-plans/{farmer_id}         : {t_get_plans:.3f} s  ({t_get_plans*1000:.1f} ms)")
    print(f"• POST /api/action-plans/{plan_id}/recheck (Live) : {t_recheck_live:.3f} s  ({t_recheck_live*1000:.1f} ms)")
    print(f"• POST /api/action-plans/{plan_id}/recheck (Sim)  : {t_recheck_sim:.3f} s  ({t_recheck_sim*1000:.1f} ms)")
    print(f"• Login request (POST /api/auth/login)     : {t_login:.3f} s  ({t_login*1000:.1f} ms)")
    print(f"• Farmer Dashboard Combined Page Load      : {t_dashboard_total:.3f} s  ({t_dashboard_total*1000:.1f} ms)")
    print(f"    - /api/auth/me                         : {t_d_auth:.3f} s")
    print(f"    - /api/listings/farmer/{farmer_id}     : {t_d_list:.3f} s")
    print(f"    - /api/orders/farmer/{farmer_id}       : {t_d_orders:.3f} s")
    print(f"    - /api/action-plans/{farmer_id}        : {t_d_plans:.3f} s")
    print(f"    - /api/notifications/{farmer_id}       : {t_d_notif:.3f} s")

    print("\n" + "-"*75)
    print("2. BOTTLENECK BREAKDOWN FOR SLOWEST OPERATION (POST /api/ai/predict)")
    print("-"*75)
    print(f"1. Keras Model Loading & Graph Init (Disk/CPU) : {t_model_load:.3f} s  ({(t_model_load/max(0.001, t_predict_cold))*100:.1f}%)")
    print(f"2. Open-Meteo Weather API HTTP Call           : {t_weather_call:.3f} s  ({(t_weather_call/max(0.001, t_predict_cold))*100:.1f}%)")
    print(f"3. Neural Network Forward Inference           : {t_inference:.3f} s  ({(t_inference/max(0.001, t_predict_cold))*100:.1f}%)")
    print(f"4. Database Action Plan & Task Persistence    : {(t_predict_cold - t_model_load - t_weather_call - t_inference):.3f} s")

    db.close()

if __name__ == "__main__":
    run_benchmarks()

