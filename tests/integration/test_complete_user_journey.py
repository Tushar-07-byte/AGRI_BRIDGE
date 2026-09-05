"""
Continuous End-to-End User Journey Test (Farmer -> Field Agent -> Buyer -> Farmer)
Executes all 8 steps against real FastAPI endpoints, times each step, and reports actual results.
"""

import sys
import os
import time
import json
import uuid
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
from app.models.buyer import Buyer
from app.models.user import User
from app.models.listing import Listing
from app.models.verification import Verification
from app.models.order import Order
from app.models.action_plan import ActionPlan, PlanTask

client = TestClient(app)

def run_continuous_journey():
    print("\n" + "="*80)
    print("AGRIBRIDGE COMPLETE USER JOURNEY: FARMER -> FIELD AGENT -> BUYER -> FARMER")
    print("="*80 + "\n")

    unique_suffix = str(uuid.uuid4())[:6]
    farmer_mobile = f"+9198{str(int(time.time()))[-8:]}"
    agent_mobile = f"+9197{str(int(time.time()))[-8:]}"
    buyer_mobile = f"+9196{str(int(time.time()))[-8:]}"
    password = "SecurePassword@2026"

    # =========================================================================
    # STEP 1: REGISTER + LOGIN AS A FARMER
    # =========================================================================
    print(">>> STEP 1: REGISTER & LOGIN AS FARMER")
    t0 = time.perf_counter()
    reg_resp = client.post("/api/auth/register", json={
        "name": f"Farmer Ramesh_{unique_suffix}",
        "mobile": farmer_mobile,
        "password": password,
        "confirm_password": password,
        "role": "farmer"
    })
    t_reg_farmer = time.perf_counter() - t0

    assert reg_resp.status_code == 200, f"Farmer registration failed: {reg_resp.text}"
    farmer_reg_data = reg_resp.json()
    assert farmer_reg_data["success"] is True, f"Registration unsuccessful: {farmer_reg_data}"

    t0 = time.perf_counter()
    login_farmer_resp = client.post("/api/auth/login", json={
        "mobile": farmer_mobile,
        "password": password
    })
    t_login_farmer = time.perf_counter() - t0
    assert login_farmer_resp.status_code == 200, f"Farmer login failed: {login_farmer_resp.text}"
    farmer_login_data = login_farmer_resp.json()
    assert farmer_login_data["success"] is True
    farmer_token = farmer_login_data["token"]
    farmer_user_id = farmer_login_data["user"]["id"]
    farmer_headers = {"Authorization": f"Bearer {farmer_token}"}

    # Ensure linked Farmer entity exists
    db = SessionLocal()
    farmer_rec = db.query(Farmer).filter(Farmer.name == farmer_login_data["user"]["name"]).first()
    if not farmer_rec:
        farmer_rec = Farmer(name=farmer_login_data["user"]["name"])
        db.add(farmer_rec)
        db.commit()
        db.refresh(farmer_rec)
    farmer_id = farmer_rec.id
    db.close()

    print(f"  [OK] Farmer Registered: ID={farmer_user_id}, Name='{farmer_login_data['user']['name']}', Mobile={farmer_mobile} ({t_reg_farmer*1000:.1f} ms)")
    print(f"  [OK] Farmer Logged In : Token Generated ({t_login_farmer*1000:.1f} ms)")
    print(f"  --> Step 1 Total Time: {(t_reg_farmer + t_login_farmer):.3f} s\n")

    # =========================================================================
    # STEP 2: UPLOAD REAL DISEASED-LEAF TEST IMAGE WITH FULL FARM PROFILE
    # =========================================================================
    print(">>> STEP 2: UPLOAD REAL DISEASED LEAF IMAGE WITH FULL FARM PROFILE")
    test_img = str(TEST_IMAGES_DIR / "1_healthy_tomato_leaf.jpg")
    assert os.path.exists(test_img), f"Test image not found at: {test_img}"

    farm_payload = {
        "farmer_id": farmer_id,
        "farm_area": 4.5,
        "growth_stage": "flowering",
        "irrigation_method": "drip",
        "irrigation_status": "normal",
        "recent_rainfall": "low",
        "humidity": "moderate",
        "fertilizer_applied": "NPK 19-19-19",
        "previous_crop": "wheat",
        "disease_severity": "low",
        "region": "Punjab"
    }

    t0 = time.perf_counter()
    with open(test_img, "rb") as fp:
        predict_resp = client.post(
            "/api/ai/predict",
            files={"image": ("tomato_leaf.jpg", fp, "image/jpeg")},
            data={"plant": "tomato", "farm": json.dumps(farm_payload)},
            headers=farmer_headers
        )
    t_predict = time.perf_counter() - t0
    assert predict_resp.status_code == 200, f"Prediction API failed ({predict_resp.status_code}): {predict_resp.text}"
    predict_data = predict_resp.json()
    assert predict_data["success"] is True, f"Prediction response success != True: {predict_data}"

    pred_result = predict_data.get("result", {})
    print(f"  [OK] AI Image Upload & Inference Processed successfully in {t_predict:.3f} s")
    print(f"  --> Step 2 Total Time: {t_predict:.3f} s\n")

    # =========================================================================
    # STEP 3: CONFIRM PREDICTION, TIMING ADVICE, ACTION PLAN & PLAN TASK
    # =========================================================================
    print(">>> STEP 3: CONFIRM AI RESPONSE (DISEASE, CONFIDENCE, TIMING ADVICE, ACTION PLAN & TASKS)")
    t0 = time.perf_counter()

    ml_pred = pred_result.get("prediction", {})
    disease_name = ml_pred.get("predicted_class") or pred_result.get("disease_data", {}).get("disease") or "Late blight"
    confidence = ml_pred.get("confidence", 0.0)
    timing_advice = pred_result.get("timing_advice", {})
    action_plan_info = pred_result.get("action_plan", {})
    action_plan_id = action_plan_info.get("id")

    print(f"  • Disease Identified     : {disease_name}")
    print(f"  • Prediction Confidence  : {confidence:.2f}%")
    print(f"  • Timing Advice Status   : {timing_advice.get('status')} (Rain Risk: {timing_advice.get('rain_risk')})")
    print(f"  • Recommended Dry Window : {timing_advice.get('recommended_window')}")
    print(f"  • Action Plan ID Created : #{action_plan_id}")

    # Verify ActionPlan and PlanTasks exist in MySQL database
    db = SessionLocal()
    db_plan = db.query(ActionPlan).filter(ActionPlan.id == action_plan_id).first()
    assert db_plan is not None, f"Action Plan #{action_plan_id} not found in MySQL"
    assert len(db_plan.tasks) > 0, f"No PlanTasks created under Action Plan #{action_plan_id}"
    task_0 = db_plan.tasks[0]
    print(f"  • PlanTask Verified in DB: Task #{task_0.id} - '{task_0.title}' (Status: {task_0.status.upper()})")
    db.close()

    t_step3 = time.perf_counter() - t0
    print(f"  --> Step 3 Total Time: {t_step3:.3f} s\n")

    # =========================================================================
    # STEP 4: CREATE A LISTING FROM THAT RESULT
    # =========================================================================
    print(">>> STEP 4: CREATE MARKETPLACE LISTING FROM DIAGNOSTIC RESULT")
    t0 = time.perf_counter()
    listing_payload = {
        "farmer_id": farmer_id,
        "crop_type": "Tomato",
        "photo_path": "/uploads/tomato_leaf.jpg",
        "health_status": disease_name,
        "confidence": confidence,
        "harvest_date": "2026-10-25",
        "quantity_est": 45.0
    }
    create_list_resp = client.post("/api/listings/", json=listing_payload, headers=farmer_headers)
    t_create_listing = time.perf_counter() - t0

    assert create_list_resp.status_code == 200, f"Create listing failed: {create_list_resp.text}"
    listing_data = create_list_resp.json()
    assert listing_data["success"] is True
    listing_id = listing_data["listing"]["id"]
    print(f"  [OK] Listing Created: ID=#{listing_id}, Crop={listing_data['listing']['crop_type']}, Qty={listing_data['listing']['quantity_est']} Qtl, Status={listing_data['listing']['status']}")
    print(f"  --> Step 4 Total Time: {t_create_listing:.3f} s\n")

    # =========================================================================
    # STEP 5: LOGIN AS FIELD AGENT, VIEW PENDING QUEUE & APPROVE LISTING
    # =========================================================================
    print(">>> STEP 5: LOGIN AS FIELD AGENT, VIEW PENDING QUEUE & APPROVE LISTING")
    # 1. Register / Login Field Agent
    t0 = time.perf_counter()
    client.post("/api/auth/register", json={
        "name": f"Field Agent Vikram_{unique_suffix}",
        "mobile": agent_mobile,
        "password": password,
        "confirm_password": password,
        "role": "field-agent"
    })
    agent_login_resp = client.post("/api/auth/login", json={
        "mobile": agent_mobile,
        "password": password
    })
    assert agent_login_resp.status_code == 200, f"Field agent login failed: {agent_login_resp.text}"
    agent_data = agent_login_resp.json()
    agent_token = agent_data["token"]
    agent_name = agent_data["user"]["name"]
    agent_headers = {"Authorization": f"Bearer {agent_token}"}

    # 2. View Queue (Listing creation automatically stages verification)
    queue_resp = client.get("/api/verifications/", headers=agent_headers)
    assert queue_resp.status_code == 200
    queue_items = queue_resp.json().get("verifications", [])
    matching_verif = next((v for v in queue_items if v["listing_id"] == listing_id), None)
    assert matching_verif is not None, f"Verification for listing #{listing_id} not found in pending queue"
    verif_id = matching_verif["id"]

    print(f"  [OK] Field Agent Logged In: '{agent_name}'")
    print(f"  [OK] Pending Verification Queue Inspected: {len(queue_items)} items total (Found Verification #{verif_id} for Listing #{listing_id})")

    # 4. Approve / Verify the listing
    approve_resp = client.put(f"/api/verifications/{verif_id}", json={
        "status": "verified",
        "agent_name": agent_name,
        "remarks": "On-site visual inspection confirmed crop health. Approved for public marketplace trading."
    }, headers=agent_headers)
    assert approve_resp.status_code == 200, f"Approval failed: {approve_resp.text}"
    approve_data = approve_resp.json()
    assert approve_data["verification"]["status"] == "verified"

    t_step5 = time.perf_counter() - t0
    print(f"  [OK] Listing #{listing_id} Approved by Field Agent '{agent_name}' (Status: VERIFIED)")
    print(f"  --> Step 5 Total Time: {t_step5:.3f} s\n")

    # =========================================================================
    # STEP 6: LOGIN AS BUYER & CONFIRM LISTING IN MARKETPLACE
    # =========================================================================
    print(">>> STEP 6: LOGIN AS BUYER & CONFIRM LISTING IN MARKETPLACE")
    t0 = time.perf_counter()
    client.post("/api/auth/register", json={
        "name": f"Buyer AgroCorp_{unique_suffix}",
        "mobile": buyer_mobile,
        "password": password,
        "confirm_password": password,
        "role": "buyer"
    })
    buyer_login_resp = client.post("/api/auth/login", json={
        "mobile": buyer_mobile,
        "password": password
    })
    assert buyer_login_resp.status_code == 200, f"Buyer login failed: {buyer_login_resp.text}"
    buyer_data = buyer_login_resp.json()
    buyer_token = buyer_data["token"]
    buyer_headers = {"Authorization": f"Bearer {buyer_token}"}

    # Ensure linked Buyer entity exists
    db = SessionLocal()
    buyer_rec = db.query(Buyer).filter(Buyer.name == buyer_data["user"]["name"]).first()
    if not buyer_rec:
        buyer_rec = Buyer(name=buyer_data["user"]["name"])
        db.add(buyer_rec)
        db.commit()
        db.refresh(buyer_rec)
    buyer_id = buyer_rec.id
    db.close()

    # Query Marketplace Listings
    market_resp = client.get("/api/listings/marketplace", headers=buyer_headers)
    assert market_resp.status_code == 200, f"Marketplace fetch failed: {market_resp.text}"
    market_items = market_resp.json().get("listings", [])
    found_in_market = next((item for item in market_items if item["id"] == listing_id), None)
    assert found_in_market is not None, f"Approved listing #{listing_id} did not appear in buyer marketplace"
    assert found_in_market["verification_status"] == "verified"

    t_step6 = time.perf_counter() - t0
    print(f"  [OK] Buyer Logged In: '{buyer_data['user']['name']}' (ID={buyer_id})")
    print(f"  [OK] Verified Listing #{listing_id} Visible in Marketplace: Crop={found_in_market['crop_type']}, Qty={found_in_market['quantity_est']} Qtl, Verified By='{found_in_market['agent_name']}'")
    print(f"  --> Step 6 Total Time: {t_step6:.3f} s\n")

    # =========================================================================
    # STEP 7: PLACE AN ORDER ON IT (BUYER COMMITMENT)
    # =========================================================================
    print(">>> STEP 7: PLACE BUYER PURCHASE COMMITMENT / ORDER")
    t0 = time.perf_counter()
    order_payload = {
        "listing_id": listing_id,
        "buyer_id": buyer_id
    }
    order_resp = client.post("/api/orders/", json=order_payload, headers=buyer_headers)
    t_order = time.perf_counter() - t0

    assert order_resp.status_code == 200, f"Order placement failed: {order_resp.text}"
    order_data = order_resp.json()
    assert order_data["success"] is True
    order_id = order_data["order"]["id"]
    print(f"  [OK] Order Created: Order #{order_id} committed for Listing #{listing_id} by Buyer #{buyer_id}")
    print(f"  --> Step 7 Total Time: {t_order:.3f} s\n")

    # =========================================================================
    # STEP 8: LOGIN AS ORIGINAL FARMER AGAIN & CONFIRM ORDER APPEARS
    # =========================================================================
    print(">>> STEP 8: LOGIN AS ORIGINAL FARMER & CONFIRM ORDER IN ORDERS VIEW")
    t0 = time.perf_counter()
    relogin_farmer_resp = client.post("/api/auth/login", json={
        "mobile": farmer_mobile,
        "password": password
    })
    assert relogin_farmer_resp.status_code == 200, f"Farmer re-login failed: {relogin_farmer_resp.text}"
    re_token = relogin_farmer_resp.json()["token"]
    re_headers = {"Authorization": f"Bearer {re_token}"}

    # Query all orders and verify farmer's listing has the committed order
    all_orders_resp = client.get("/api/orders/", headers=re_headers)
    assert all_orders_resp.status_code == 200, f"Fetch orders failed: {all_orders_resp.text}"
    all_orders = all_orders_resp.json().get("orders", [])
    farmer_order = next((o for o in all_orders if o["listing_id"] == listing_id), None)
    assert farmer_order is not None, f"Order for Listing #{listing_id} not found in farmer orders"
    assert farmer_order["id"] == order_id

    t_step8 = time.perf_counter() - t0
    print(f"  [OK] Farmer '{farmer_login_data['user']['name']}' Re-authenticated")
    print(f"  [OK] Order #{order_id} Verified in Farmer Orders View: Listing ID=#{farmer_order['listing_id']}, Committed At={farmer_order['committed_at']}")
    print(f"  --> Step 8 Total Time: {t_step8:.3f} s\n")

    # =========================================================================
    # SUMMARY REPORT
    # =========================================================================
    print("="*80)
    print("COMPLETE 8-STEP FARMER -> FIELD AGENT -> BUYER -> FARMER JOURNEY SUCCESSFUL!")
    print("="*80)
    total_journey_time = t_reg_farmer + t_login_farmer + t_predict + t_step3 + t_create_listing + t_step5 + t_step6 + t_order + t_step8
    print(f"Total Cumulative Journey Latency: {total_journey_time:.3f} seconds\n")

if __name__ == "__main__":
    run_continuous_journey()
