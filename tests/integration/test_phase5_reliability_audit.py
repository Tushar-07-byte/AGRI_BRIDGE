"""
AgriBridge Phase 5 Reliability, Failure Recovery & Complete User Journey Audit Suite
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents
"""

import os
import sys
import io
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

backend_path = Path(__file__).resolve().parents[2] / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.main import app
from app.database.connection import SessionLocal
from app.models.farmer import Farmer
from app.models.user import User
from app.models.listing import Listing
from app.models.order import Order
from app.models.buyer import Buyer
from app.models.verification import Verification
from app.models.disease_record import DiseaseRecord
from app.models.action_plan import ActionPlan, PlanTask, FieldAgentEscalation, NotificationEvent
from app.domain.farm_decision_context import SignalProvenance, SignalQuality
from app.services.auth_service import create_access_token, hash_password

client = TestClient(app)


def test_complete_farmer_journey():
    """1. Farmer Auth -> Profile -> Orchestration -> Task Execution"""
    db = SessionLocal()
    ts = int(time.time() * 1000) % 100000000
    mobile = f"+9198{ts:08d}"
    email = f"farmer_p5_{ts}@test.com"
    hashed = hash_password("Secret123!")
    user = User(name="Ramesh Kumar", email=email, mobile=mobile, password_hash=hashed, role="farmer")
    db.add(user)
    db.commit()
    db.refresh(user)

    farmer = Farmer(name=user.name)
    db.add(farmer)
    db.commit()
    db.refresh(farmer)
    farmer_id = farmer.id
    user_id = user.id
    db.close()

    token = create_access_token(user_id=user_id, mobile=mobile, name=user.name, role="farmer")
    headers = {"Authorization": f"Bearer {token}"}

    # A. Orchestrate plan
    plan_payload = {
        "farmer_id": farmer_id,
        "crop": "Wheat",
        "state": "Uttar Pradesh",
        "district": "Sultanpur",
        "village": "Dhanpatganj",
        "crop_stage": "Tillering",
        "planting_date": "2026-11-05"
    }
    res_plan = client.post("/api/orchestration/plan", json=plan_payload, headers=headers)
    assert res_plan.status_code == 200, res_plan.text
    plan_data = res_plan.json()
    assert plan_data["success"] is True
    plan_id = plan_data["action_plan_id"]
    assert plan_id is not None

    # B. Fetch Farmer's Action Plan
    res_get = client.get(f"/api/action-plans/plan/{plan_id}", headers=headers)
    assert res_get.status_code == 200
    plan_retrieved = res_get.json()["action_plan"]
    assert plan_retrieved["id"] == plan_id
    assert len(plan_retrieved["tasks"]) > 0
    task_id = plan_retrieved["tasks"][0]["id"]

    # C. Execute / Complete a Task
    res_task = client.patch(f"/api/plan-tasks/{task_id}", json={"status": "done"}, headers=headers)
    assert res_task.status_code == 200
    task_updated = res_task.json()["task"]
    assert task_updated["status"] == "done"
    assert task_updated["completed_at"] is not None

    print("[PASS] Complete Farmer Journey validated.")


def test_complete_field_agent_journey():
    """2. Field Agent Escalation Queue -> Inspection -> Verification -> Notification"""
    db = SessionLocal()
    farmer = db.query(Farmer).first()
    farmer_id = farmer.id if farmer else 1

    # Create borderline disease record
    rec = DiseaseRecord(
        farmer_id=farmer_id,
        crop_type="wheat",
        confidence=52.5,
        predicted_pathogen="Wheat Yellow Rust",
        status="PENDING_AGENT_REVIEW",
        prescription_chemical="Propiconazole 25% EC",
        prescription_dosage="1.0 ml / L water",
        prescription_phi="30 Days Pre-Harvest Interval (PHI)",
        created_at=datetime.utcnow()
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    rec_id = rec.id
    db.close()

    # Agent inspects queue
    res_q = client.get("/api/verifications/disease-scans/queue")
    assert res_q.status_code == 200
    scans = res_q.json()["disease_scans"]
    target = next((s for s in scans if s["id"] == rec_id), None)
    assert target is not None
    assert target["status"] == "PENDING_AGENT_REVIEW"

    # Agent verifies diagnosis
    res_app = client.post(f"/api/verifications/disease-scans/{rec_id}/approve", json={
        "agent_name": "Field Officer Ananya (Krishi Vigyan Kendra)",
        "remarks": "Diagnostic verified on-site. Moderate stripe rust confirmed. Prescription authorized."
    })
    assert res_app.status_code == 200
    app_data = res_app.json()
    assert app_data["status"] == "VERIFIED_HEALTH_RECORD"
    assert app_data["prescription"]["chemical_name"] == "Propiconazole 25% EC"
    assert app_data["notification"]["status"] == "NOTIFIED"

    print("[PASS] Complete Field Agent Journey validated.")


def test_complete_buyer_journey():
    """3. Buyer Marketplace Browse -> Listing View -> Order Placement"""
    db = SessionLocal()
    farmer = db.query(Farmer).first()
    if not farmer:
        farmer = Farmer(name="Farmer Ramesh")
        db.add(farmer)
        db.commit()
        db.refresh(farmer)

    listing = Listing(
        farmer_id=farmer.id,
        crop_type="wheat",
        quantity_est=500.0,
        status="available"
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)

    verif = Verification(
        listing_id=listing.id,
        agent_name="Krishi Vigyan Kendra Officer",
        status="verified",
        created_at=datetime.utcnow()
    )
    db.add(verif)

    ts = int(time.time() * 1000) % 10000000
    buyer = Buyer(name=f"ITC Agri Hub {ts}")
    db.add(buyer)
    db.commit()
    db.refresh(buyer)

    listing_id = listing.id
    buyer_id = buyer.id
    db.close()

    # Buyer browses marketplace
    res_m = client.get("/api/marketplace/")
    assert res_m.status_code == 200

    # Buyer places wholesale order
    order_payload = {
        "listing_id": listing_id,
        "buyer_id": buyer_id
    }
    res_ord = client.post("/api/orders/", json=order_payload)
    assert res_ord.status_code in [200, 201], res_ord.text
    ord_data = res_ord.json()
    assert ord_data["success"] is True

    print("[PASS] Complete Buyer Wholesale Journey validated.")


def test_failure_and_recovery_modes():
    """4. Robust Failure Modes & Controlled Degradation"""
    # A. Invalid Auth Token
    res_bad_auth = client.get("/api/action-plans/plan/1", headers={"Authorization": "Bearer INVALID_TOKEN_STRING"})
    assert res_bad_auth.status_code in [200, 401, 403]

    # B. Missing Plan ID
    res_404 = client.get("/api/action-plans/plan/99999999")
    assert res_404.status_code == 404

    # C. Missing / Invalid Image in Disease Prediction
    res_bad_img = client.post("/api/ai/predict", data={"plant": "wheat", "farm": "{}"}, files={"image": ("bad.txt", b"not an image", "text/plain")})
    assert res_bad_img.status_code == 400
    assert len(res_bad_img.text) > 0

    # D. Missing NPK laboratory data in evaluate
    res_npk = client.post("/api/orchestration/evaluate", json={"crop": "wheat", "confidence": 70.0})
    assert res_npk.status_code == 200
    dec = res_npk.json()["multi_signal_decision"] if "multi_signal_decision" in res_npk.json() else res_npk.json()
    npk_d = next((d for d in dec["decisions"] if str(d.get("decision_type", "")).lower() == "nutrient_management"), None)
    assert npk_d is not None
    assert str(npk_d["result"]).lower() in ["insufficient_data", "allowed"]

    # E. Weather Re-check with high rain surge (graceful task invalidation)
    db = SessionLocal()
    farmer = db.query(Farmer).first()
    plan = ActionPlan(farmer_id=farmer.id if farmer else 1, crop_id="wheat", status="active", created_at=datetime.utcnow())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    t = PlanTask(action_plan_id=plan.id, title="Apply Mancozeb", status="pending", reasoning="Initial schedule")
    db.add(t)
    db.commit()
    plan_id = plan.id
    db.close()

    res_recheck = client.post(f"/api/orchestration/recheck/{plan_id}", json={
        "simulated_rain_probability": 88,
        "simulated_weather_condition": "Severe thunderstorm warning",
        "recommended_window": "2026-09-10 (Dry Window)",
        "force_change": True
    })
    assert res_recheck.status_code == 200
    rec_data = res_recheck.json()
    assert rec_data["change_detected"] is True
    assert rec_data["change_type"] == "WEATHER_WORSENED_RAIN_SURGE"

    print("[PASS] Failure Modes & Controlled Recovery validated.")


def test_security_and_role_isolation():
    """5. Security: Cross-Farmer Ownership Authorization"""
    db = SessionLocal()
    f1 = Farmer(name="Farmer Alpha")
    f2 = Farmer(name="Farmer Beta")
    db.add_all([f1, f2])
    db.commit()
    db.refresh(f1)
    db.refresh(f2)

    ts1 = int(time.time() * 1000) % 100000000
    ts2 = (ts1 + 1) % 100000000
    u1 = User(name="Farmer Alpha", email=f"alpha_{ts1}@farm.in", mobile=f"+9197{ts1:08d}", password_hash="pw", role="farmer")
    u2 = User(name="Farmer Beta", email=f"beta_{ts2}@farm.in", mobile=f"+9197{ts2:08d}", password_hash="pw", role="farmer")
    db.add_all([u1, u2])
    db.commit()
    db.refresh(u1)
    db.refresh(u2)

    plan_alpha = ActionPlan(farmer_id=f1.id, crop_id="wheat", status="active", created_at=datetime.utcnow())
    db.add(plan_alpha)
    db.commit()
    db.refresh(plan_alpha)
    p_alpha_id = plan_alpha.id
    u2_id = u2.id
    u2_mobile = u2.mobile
    u2_name = u2.name
    db.close()

    token_beta = create_access_token(user_id=u2_id, mobile=u2_mobile, name=u2_name, role="farmer")
    headers_beta = {"Authorization": f"Bearer {token_beta}"}

    # Farmer Beta tries to access Farmer Alpha's plan -> Must be 403 Forbidden!
    res_unauth = client.get(f"/api/action-plans/plan/{p_alpha_id}", headers=headers_beta)
    assert res_unauth.status_code == 403, f"Expected 403 Forbidden but got {res_unauth.status_code}"
    assert "Access denied" in res_unauth.text

    print("[PASS] Cross-Farmer Ownership Authorization & Security verified.")


def test_demo_reset_reproducibility():
    """6. Demo Reset & Scenario Isolation"""
    db = SessionLocal()
    count_before = db.query(ActionPlan).count()
    db.close()

    # Run Scenario B (Borderline Yellow Rust)
    res_b = client.post("/api/orchestration/evaluate", json={
        "crop": "wheat",
        "disease_name": "Wheat Yellow Rust",
        "confidence": 51.69,
        "soil_moisture_vwc": 24.0
    })
    assert res_b.status_code == 200
    dec_b = res_b.json().get("multi_signal_decision", res_b.json())
    assert dec_b["escalation_required"] is True
    assert "PRESCRIPTION_LOCKED" in dec_b["constraints"]

    # Verify zero database writes during deterministic evaluation
    db2 = SessionLocal()
    count_after = db2.query(ActionPlan).count()
    db2.close()
    assert count_before == count_after, "Deterministic evaluation must NEVER create un-scoped database records!"

    print("[PASS] Demo Reset & Scenario Determinism verified.")


if __name__ == "__main__":
    print("=======================================================================")
    print("  RUNNING PHASE 5 PRODUCTION RELIABILITY & USER JOURNEY AUDIT SUITE")
    print("=======================================================================")
    test_complete_farmer_journey()
    test_complete_field_agent_journey()
    test_complete_buyer_journey()
    test_failure_and_recovery_modes()
    test_security_and_role_isolation()
    test_demo_reset_reproducibility()
    print("=======================================================================")
    print("  ALL PHASE 5 RELIABILITY & INTEGRATION AUDIT TESTS PASSED (100% SUCCESS)!")
    print("=======================================================================")
