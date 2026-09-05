"""
AgriBridge Borderline Confidence & Human Escalation Master Integration Test
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Verifies:
1. Input with confidence in [30.0, 65.0) triggers uncertainty policy.
2. Autonomous treatment/action is NOT activated (ActionPlan status is 'needs_expert_review').
3. Action plan is explicitly flagged for expert review (escalation_required == True).
4. FieldAgentEscalation record is persisted in the database with status 'escalated'.
5. Field-agent escalation queue (GET /api/action-plans/escalations/queue) retrieves the item.
6. DiseaseRecord prescription remains locked with status 'PENDING_AGENT_REVIEW'.
7. Appropriate farmer-facing status and feedback is returned.
8. Field Agent verification (POST /api/verifications/disease-scans/{id}/approve) unlocks the prescription
   and transitions the action plan and escalation to resolved/active.
"""

import sys
import os
import json
import time
from pathlib import Path

# Ensure UTF-8 stdout on Windows
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
from app.models.disease_record import DiseaseRecord

client = TestClient(app)


def test_borderline_confidence_escalation_lifecycle():
    print("\n" + "=" * 80)
    print("RUNNING BORDERLINE CONFIDENCE & HUMAN ESCALATION INTEGRATION TEST")
    print("=" * 80)

    # Step 1: Ensure test farmer exists in DB
    db = SessionLocal()
    farmer = db.query(Farmer).first()
    if not farmer:
        farmer = Farmer(name="Borderline Test Farmer", location="Samrala, Ludhiana")
        db.add(farmer)
        db.commit()
        db.refresh(farmer)
    farmer_id = farmer.id
    db.close()

    farm_payload = {
        "farmer_id": farmer_id,
        "farm_area": 3.5,
        "growth_stage": "flowering",
        "irrigation_method": "drip",
        "irrigation_status": "normal",
        "recent_rainfall": "none",
        "humidity": "moderate",
        "fertilizer_applied": "urea",
        "previous_crop": "wheat",
        "disease_severity": "moderate",
        "region": "Punjab"
    }

    # Step 2: Upload borderline confidence image (1_healthy_tomato_leaf yields ~51.7% confidence)
    border_img_path = TEST_IMAGES_DIR / "1_healthy_tomato_leaf.jpg"
    assert border_img_path.exists(), f"Missing benchmark test image: {border_img_path}"

    print("\n--- STEP 1: Image Submission with Borderline Confidence [30.0, 65.0) ---")
    with open(str(border_img_path), "rb") as fp:
        resp = client.post(
            "/api/ai/predict",
            files={"image": ("1_healthy_tomato_leaf.jpg", fp, "image/jpeg")},
            data={"plant": "tomato", "farm": json.dumps(farm_payload)}
        )

    assert resp.status_code == 200, f"AI predict failed: {resp.status_code} - {resp.text}"
    body = resp.json()
    assert body.get("success") is True, f"Prediction did not succeed: {body}"

    result = body["result"]
    prediction = result.get("prediction", {})
    confidence = float(prediction.get("confidence", 0.0))
    action_plan_data = result.get("action_plan", {})
    plan_id = action_plan_data.get("id")

    print(f"  AI Predicted Pathogen : {prediction.get('predicted_pathogen')}")
    print(f"  Confidence Score      : {confidence:.2f}%")
    print(f"  Action Plan ID        : #{plan_id}")

    # Assertion 1: Confidence is within borderline range
    assert 30.0 <= confidence < 65.0, (
        f"Expected confidence in [30.0, 65.0), but got {confidence}"
    )
    print("  ✓ ASSERTION 1 PASSED: Confidence is within [30.0, 65.0) range.")

    # Assertion 2: Autonomous intervention NOT activated; status is 'needs_expert_review'
    plan_status = action_plan_data.get("status")
    assert plan_status == "needs_expert_review", (
        f"Autonomous treatment must NOT be active! Expected 'needs_expert_review', got '{plan_status}'"
    )
    print("  ✓ ASSERTION 2 PASSED: Autonomous intervention NOT activated (status: 'needs_expert_review').")

    # Step 3: Verify ActionPlan and FieldAgentEscalation in Database
    print("\n--- STEP 2: Database State Verification ---")
    db = SessionLocal()
    db_plan = db.query(ActionPlan).filter(ActionPlan.id == plan_id).first()
    assert db_plan is not None, f"ActionPlan #{plan_id} not found in database"
    assert db_plan.status == "needs_expert_review", f"DB status is {db_plan.status}"
    assert db_plan.escalation_required is True, "escalation_required must be True"
    assert db_plan.escalation_reason is not None and len(db_plan.escalation_reason) > 0, "Missing escalation reason"
    print(f"  ActionPlan in DB      : status='{db_plan.status}', escalation_required={db_plan.escalation_required}")
    print(f"  Escalation Reason     : '{db_plan.escalation_reason}'")
    print("  ✓ ASSERTION 3 PASSED: Action plan marked for expert review with descriptive reason.")

    # Assertion 4: Escalation record created in FieldAgentEscalation table
    db_esc = db.query(FieldAgentEscalation).filter(
        FieldAgentEscalation.action_plan_id == plan_id
    ).first()
    assert db_esc is not None, f"No FieldAgentEscalation record found for ActionPlan #{plan_id}"
    assert db_esc.status == "escalated", f"Expected escalation status 'escalated', got '{db_esc.status}'"
    print(f"  FieldAgentEscalation  : ID=#{db_esc.id}, status='{db_esc.status}', risk_level='{db_esc.risk_level}'")
    print("  ✓ ASSERTION 4 PASSED: Escalation record created with status 'escalated'.")

    # Assertion 5: DiseaseRecord created with status PENDING_AGENT_REVIEW (prescription masked)
    db_record = db.query(DiseaseRecord).filter(
        DiseaseRecord.action_plan_id == plan_id
    ).first()
    assert db_record is not None, f"No DiseaseRecord found linked to ActionPlan #{plan_id}"
    assert db_record.status == "PENDING_AGENT_REVIEW", (
        f"Expected DiseaseRecord status 'PENDING_AGENT_REVIEW', got '{db_record.status}'"
    )
    disease_record_id = db_record.id
    print(f"  DiseaseRecord in DB   : ID=#{disease_record_id}, status='{db_record.status}'")
    print("  ✓ ASSERTION 5 PASSED: Clinical disease record created with status 'PENDING_AGENT_REVIEW'.")
    db.close()

    # Step 4: Verify Field-Agent Escalation Queue retrieval via API
    print("\n--- STEP 3: Field-Agent Escalation Queue API Verification ---")
    queue_resp = client.get("/api/action-plans/escalations/queue")
    assert queue_resp.status_code == 200, f"Failed to query escalation queue: {queue_resp.status_code}"
    queue_data = queue_resp.json()
    escalation_list = queue_data.get("escalations", [])
    matching_item = next((item for item in escalation_list if item.get("id") == plan_id), None)
    assert matching_item is not None, (
        f"ActionPlan #{plan_id} not returned in /api/action-plans/escalations/queue"
    )
    print(f"  Queue Search Result   : Found plan #{matching_item['id']} (status: {matching_item['status']})")
    print("  ✓ ASSERTION 6 PASSED: Field-agent queue retrieves the escalated plan.")

    # Step 5: Verify Pending Disease Scans verification queue
    scans_resp = client.get("/api/verifications/disease-scans/queue?status=PENDING_AGENT_REVIEW")
    assert scans_resp.status_code == 200
    pending_scans = scans_resp.json().get("disease_scans", [])
    scan_item = next((s for s in pending_scans if s.get("id") == disease_record_id), None)
    assert scan_item is not None, f"DiseaseRecord #{disease_record_id} not in pending disease-scans queue"
    print(f"  Pending Scan Queue    : Found record #{scan_item['id']} (pathogen: {scan_item.get('predicted_pathogen')})")
    print("  ✓ ASSERTION 7 PASSED: Field-agent disease verification queue contains pending scan.")

    # Step 6: Simulate Field Agent HITL Review & Approval
    print("\n--- STEP 4: Field Agent Review & Approval Lifecycle ---")
    approve_resp = client.post(
        f"/api/verifications/disease-scans/{disease_record_id}/approve",
        json={"agent_name": "Senior Agronomist Dr. Patil", "remarks": "Diagnosis confirmed on-site; early blight treated."}
    )
    assert approve_resp.status_code == 200, f"Approval failed: {approve_resp.status_code} - {approve_resp.text}"
    approve_body = approve_resp.json()
    assert approve_body.get("success") is True, f"Approval response returned false: {approve_body}"

    # Step 7: Post-Approval Database Verification
    db = SessionLocal()
    db_record_after = db.query(DiseaseRecord).filter(DiseaseRecord.id == disease_record_id).first()
    assert db_record_after.status == "VERIFIED_HEALTH_RECORD", (
        f"Expected VERIFIED_HEALTH_RECORD after approval, got '{db_record_after.status}'"
    )
    assert db_record_after.agent_name == "Senior Agronomist Dr. Patil"
    print(f"  DiseaseRecord Post-Approval: status='{db_record_after.status}', agent='{db_record_after.agent_name}'")

    db_plan_after = db.query(ActionPlan).filter(ActionPlan.id == plan_id).first()
    assert db_plan_after.status in ["active", "active_verified_rx"], (
        f"Expected ActionPlan status 'active' or 'active_verified_rx' after human approval, got '{db_plan_after.status}'"
    )
    assert db_plan_after.risk_type == "verified_disease_treatment", (
        f"Expected risk_type 'verified_disease_treatment', got '{db_plan_after.risk_type}'"
    )
    print(f"  ActionPlan Post-Approval   : status='{db_plan_after.status}', risk_type='{db_plan_after.risk_type}'")

    db_esc_after = db.query(FieldAgentEscalation).filter(
        FieldAgentEscalation.action_plan_id == plan_id
    ).first()
    assert db_esc_after.status in ["resolved", "approved"], (
        f"Expected escalation status 'resolved' or 'approved', got '{db_esc_after.status}'"
    )
    print(f"  Escalation Post-Approval   : status='{db_esc_after.status}'")
    db.close()

    print("  ✓ ASSERTION 8 PASSED: Human approval transitions record to VERIFIED_HEALTH_RECORD and activates ActionPlan.")
    print("\n" + "=" * 80)
    print("ALL 8 BORDERLINE ESCALATION INTEGRATION ASSERTIONS PASSED SUCCESSFULLY!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    test_borderline_confidence_escalation_lifecycle()
