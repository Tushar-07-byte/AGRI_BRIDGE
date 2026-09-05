"""
AI Prediction Non-Happy-Path Outcome Test Suite
Tests:
1. Blurry image rejection with clear message (HTTP 400).
2. Non-leaf image rejection with clear message (HTTP 400).
3. Borderline confidence (30-65%) -> ActionPlan status "needs_expert_review" & field agent escalation queue.
4. High confidence image -> ActionPlan status "active".
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

WORKSPACE_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = WORKSPACE_DIR / "backend"
TEST_IMAGES_DIR = WORKSPACE_DIR / "tests" / "fixtures" / "test_images"
if not TEST_IMAGES_DIR.exists():
    TEST_IMAGES_DIR = BACKEND_DIR / "test_images"

sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.models.farmer import Farmer
from app.models.action_plan import ActionPlan, FieldAgentEscalation

client = TestClient(app)

def run_non_happy_path_tests():
    print("\n" + "="*80)
    print("AI PREDICTION NON-HAPPY-PATH & EDGE-CASE TEST SUITE")
    print("="*80 + "\n")

    db = SessionLocal()
    farmer = db.query(Farmer).first()
    if not farmer:
        farmer = Farmer(name="Edge Case Farmer")
        db.add(farmer)
        db.commit()
        db.refresh(farmer)
    farmer_id = farmer.id
    db.close()

    farm_payload = {
        "farmer_id": farmer_id,
        "farm_area": 3.0,
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

    results = []

    # =========================================================================
    # CASE 1: BLURRY TEST IMAGE
    # =========================================================================
    print(">>> CASE 1: BLURRY / LOW-QUALITY TEST IMAGE (3_blurry_leaf.jpg)")
    blurry_img = str(TEST_IMAGES_DIR / "3_blurry_leaf.jpg")
    assert os.path.exists(blurry_img), f"Image not found: {blurry_img}"

    t0 = time.perf_counter()
    with open(blurry_img, "rb") as fp:
        resp1 = client.post(
            "/api/ai/predict",
            files={"image": ("3_blurry_leaf.jpg", fp, "image/jpeg")},
            data={"plant": "tomato", "farm": json.dumps(farm_payload)}
        )
    t1 = time.perf_counter() - t0

    print(f"  HTTP Status Code : {resp1.status_code} (Expected 400)")
    print(f"  Response Body    : {resp1.json()}")
    print(f"  Execution Time   : {t1*1000:.2f} ms ({t1:.4f} s)")

    assert resp1.status_code == 400, f"Expected 400, got {resp1.status_code}"
    detail1 = resp1.json().get("detail", "")
    assert "blurry" in detail1.lower() or "quality" in detail1.lower(), f"Unexpected error message: {detail1}"
    print("  [PASSED]: Blurry image rejected cleanly with user-friendly guidance.\n")
    results.append(("Blurry Image Rejection", resp1.status_code, detail1, t1))

    # =========================================================================
    # CASE 2: NON-LEAF TEST IMAGE
    # =========================================================================
    print(">>> CASE 2: NON-LEAF OBJECT TEST IMAGE (4_non_leaf_object.jpg)")
    non_leaf_img = str(TEST_IMAGES_DIR / "4_non_leaf_object.jpg")
    assert os.path.exists(non_leaf_img), f"Image not found: {non_leaf_img}"

    t0 = time.perf_counter()
    with open(non_leaf_img, "rb") as fp:
        resp2 = client.post(
            "/api/ai/predict",
            files={"image": ("4_non_leaf_object.jpg", fp, "image/jpeg")},
            data={"plant": "tomato", "farm": json.dumps(farm_payload)}
        )
    t2 = time.perf_counter() - t0

    print(f"  HTTP Status Code : {resp2.status_code} (Expected 400)")
    print(f"  Response Body    : {resp2.json()}")
    print(f"  Execution Time   : {t2*1000:.2f} ms ({t2:.4f} s)")

    assert resp2.status_code == 400, f"Expected 400, got {resp2.status_code}"
    detail2 = resp2.json().get("detail", "")
    assert "leaf" in detail2.lower() or "plant tissue" in detail2.lower(), f"Unexpected error message: {detail2}"
    print("  [PASSED]: Non-leaf image rejected cleanly with user-friendly guidance.\n")
    results.append(("Non-Leaf Image Rejection", resp2.status_code, detail2, t2))

    # =========================================================================
    # CASE 3: BORDERLINE CONFIDENCE IMAGE (30% - 65% RANGE)
    # =========================================================================
    print(">>> CASE 3: BORDERLINE CONFIDENCE (30-65% RANGE) -> NEEDS EXPERT REVIEW")
    # 1_healthy_tomato_leaf yields 51.69% confidence for tomato model (borderline)
    border_img = str(TEST_IMAGES_DIR / "1_healthy_tomato_leaf.jpg")

    t0 = time.perf_counter()
    with open(border_img, "rb") as fp:
        resp3 = client.post(
            "/api/ai/predict",
            files={"image": ("1_healthy_tomato_leaf.jpg", fp, "image/jpeg")},
            data={"plant": "tomato", "farm": json.dumps(farm_payload)}
        )
    t3 = time.perf_counter() - t0

    assert resp3.status_code == 200, f"Expected 200, got {resp3.status_code}: {resp3.text}"
    data3 = resp3.json()["result"]
    conf3 = data3["prediction"]["confidence"]
    plan3 = data3["action_plan"]
    plan3_id = plan3["id"]
    plan3_status = plan3["status"]

    print(f"  Prediction Confidence    : {conf3:.2f}% (Within 30-65% Borderline Range)")
    print(f"  Action Plan ID Created   : #{plan3_id}")
    print(f"  Action Plan Status       : '{plan3_status}' (Expected 'needs_expert_review')")
    print(f"  Execution Time           : {t3*1000:.2f} ms ({t3:.4f} s)")

    assert 30.0 <= conf3 < 65.0, f"Confidence {conf3} not in borderline range"
    assert plan3_status == "needs_expert_review", f"Expected 'needs_expert_review', got '{plan3_status}'"

    # Check distinct escalation queue for field agent
    t_q_start = time.perf_counter()
    esc_resp = client.get("/api/action-plans/escalations/queue")
    t_q = time.perf_counter() - t_q_start
    assert esc_resp.status_code == 200
    esc_items = esc_resp.json().get("escalations", [])
    matching_esc = next((e for e in esc_items if e["id"] == plan3_id), None)
    assert matching_esc is not None, f"Action Plan #{plan3_id} missing from Field Agent Escalation Queue"
    print(f"  Field Agent Escalation   : Verified in Distinct Escalation Queue (#{matching_esc['id']}, Status: {matching_esc['status']})")
    print("  [PASSED]: Borderline confidence correctly routed to 'needs_expert_review' & escalation queue.\n")
    results.append(("Borderline Confidence (needs_expert_review)", resp3.status_code, f"Confidence {conf3:.1f}% -> {plan3_status}", t3))

    # =========================================================================
    # CASE 4: HIGH-CONFIDENCE IMAGE (>= 65%)
    # =========================================================================
    print(">>> CASE 4: HIGH-CONFIDENCE IMAGE (>= 65%) -> ACTIVE ACTION PLAN")
    # 2_diseased_tomato_leaf.jpg yields 92.26% confidence on tomato model
    high_img = str(TEST_IMAGES_DIR / "2_diseased_tomato_leaf.jpg")

    t0 = time.perf_counter()
    with open(high_img, "rb") as fp:
        resp4 = client.post(
            "/api/ai/predict",
            files={"image": ("2_diseased_tomato_leaf.jpg", fp, "image/jpeg")},
            data={"plant": "tomato", "farm": json.dumps(farm_payload)}
        )
    t4 = time.perf_counter() - t0

    assert resp4.status_code == 200, f"Expected 200, got {resp4.status_code}: {resp4.text}"
    data4 = resp4.json()["result"]
    conf4 = data4["prediction"]["confidence"]
    plan4 = data4["action_plan"]
    plan4_id = plan4["id"]
    plan4_status = plan4["status"]

    print(f"  Prediction Confidence    : {conf4:.2f}% (High Confidence >= 65%)")
    print(f"  Action Plan ID Created   : #{plan4_id}")
    print(f"  Action Plan Status       : '{plan4_status}' (Expected 'active')")
    print(f"  Execution Time           : {t4*1000:.2f} ms ({t4:.4f} s)")

    assert conf4 >= 65.0, f"Confidence {conf4} is not >= 65.0"
    assert plan4_status == "active", f"Expected 'active', got '{plan4_status}'"
    print("  [PASSED]: High confidence image formulated into normal 'active' action plan.\n")
    results.append(("High Confidence (active)", resp4.status_code, f"Confidence {conf4:.1f}% -> {plan4_status}", t4))

    # =========================================================================
    # SUMMARY TABLE
    # =========================================================================
    print("="*80)
    print("AI NON-HAPPY-PATH TEST EXECUTION MATRIX")
    print("="*80)
    print(f"{'Case Description':<45}{'HTTP':<8}{'Latency':<15}{'Result'}")
    print("-"*80)
    for desc, code, detail, lat in results:
        print(f"{desc:<45}{code:<8}{lat*1000:>6.2f} ms       [PASSED]")
    print("="*80 + "\n")

if __name__ == "__main__":
    run_non_happy_path_tests()
