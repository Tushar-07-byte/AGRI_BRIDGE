"""
================================================================================
TEST SUITE: Disease Detection Verification Flow & Marketplace Leak Prevention
================================================================================
Verifies:
1. Disease Scan Submission:
   - Sets diagnostic status to PENDING_AGENT_REVIEW.
   - Masks/locks chemical dosage from farmer UI until verified.
   - Routes payload to Field Agent queue with zero Marketplace insertion.
2. Field Agent REJECT Action:
   - Status updates to NEEDS_PHYSICAL_VISIT / PENDING_FIELD_DISPATCH.
   - Moves to Pending Field Visits section.
   - Pushes on-site dispatch notification to farmer.
3. Field Agent APPROVE Action:
   - Status updates to VERIFIED_HEALTH_RECORD.
   - Pushes ICAR-compliant prescription (chemical name, dosage, PHI) notification.
   - Updates farm active health log.
   - Strictly ZERO Marketplace leakage.
================================================================================
"""

import sys
from pathlib import Path

# Setup paths
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = WORKSPACE_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import get_db, Base, engine
from app.models.farmer import Farmer
from app.models.listing import Listing
from app.models.verification import Verification
from app.models.disease_record import DiseaseRecord
from app.models.action_plan import ActionPlan, PlanTask, NotificationEvent, FieldAgentEscalation


def run_tests():
    print("\n" + "=" * 75)
    print("  TEST SUITE: DISEASE VERIFICATION FLOW & MARKETPLACE LEAK PREVENTION")
    print("=" * 75)

    client = TestClient(app)
    db = next(get_db())

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    # 1. Setup test farmer
    farmer = db.query(Farmer).filter(Farmer.name == "Ramesh Test Farmer").first()
    if not farmer:
        farmer = Farmer(
            name="Ramesh Test Farmer"
        )
        db.add(farmer)
        db.commit()
        db.refresh(farmer)

    farmer_id = farmer.id

    # Count initial marketplace listings
    initial_market_resp = client.get("/api/listings/marketplace")
    assert initial_market_resp.status_code == 200
    initial_market_count = initial_market_resp.json().get("count", 0)

    # Count initial listings in DB
    initial_listing_count = db.query(Listing).count()

    print(f"\n[SETUP] Farmer ID: {farmer_id}")
    print(f"[SETUP] Initial DB Listings: {initial_listing_count}")
    print(f"[SETUP] Initial Verified Marketplace Listings: {initial_market_count}")

    # =========================================================================
    # TEST 1: Farmer Disease Scan Submission Logic
    # =========================================================================
    print("\n--- TEST 1: Disease Submission Logic (Farmer Side) ---")

    test_image_path = WORKEND_IMG = WORKSPACE_ROOT / "backend" / "test_images" / "2_diseased_tomato_leaf.jpg"
    if not test_image_path.exists():
        test_image_path = WORKSPACE_ROOT / "tests" / "fixtures" / "test_images" / "2_diseased_tomato_leaf.jpg"

    farm_payload = {
        "farmer_id": farmer_id,
        "farm_area": 3.5,
        "growth_stage": "flowering",
        "irrigation_method": "drip",
        "irrigation_status": "normal",
        "recent_rainfall": "low",
        "humidity": "moderate",
        "fertilizer_applied": "NPK 19:19:19",
        "previous_crop": "Mustard",
        "disease_severity": "moderate",
        "region": "Raipur, Chhattisgarh"
    }

    import json
    with open(test_image_path, "rb") as img_file:
        files = {"image": ("tomato_leaf.jpg", img_file, "image/jpeg")}
        data = {
            "plant": "tomato",
            "farm": json.dumps(farm_payload)
        }
        predict_resp = client.post("/api/ai/predict", data=data, files=files)

    assert predict_resp.status_code == 200, f"Predict failed: {predict_resp.text}"
    pred_data = predict_resp.json()
    assert pred_data.get("success") is True

    result_obj = pred_data.get("result", {})
    assert "disease_record" in result_obj, "disease_record missing from predict response"

    record_meta = result_obj["disease_record"]
    disease_record_id = record_meta["id"]

    # Verify status is PENDING_AGENT_REVIEW
    assert record_meta["status"] == "PENDING_AGENT_REVIEW", f"Expected PENDING_AGENT_REVIEW, got {record_meta['status']}"
    assert record_meta["locked_prescription"] is True, "Prescription must be locked until verified"
    assert "PENDING_AGENT_REVIEW" in record_meta["notice"]

    # Verify database persistence (commit/close test transaction to see client's committed data)
    db.commit()
    db_record = db.query(DiseaseRecord).filter(DiseaseRecord.id == disease_record_id).first()
    assert db_record is not None, f"DiseaseRecord #{disease_record_id} not found in DB"
    assert db_record.status == "PENDING_AGENT_REVIEW"
    assert db_record.farmer_id == farmer_id
    assert db_record.crop_type == "tomato"

    # CRITICAL: Verify NO new Listing was created in the database
    new_listing_count = db.query(Listing).count()
    assert new_listing_count == initial_listing_count, (
        f"CRITICAL BUG: A Listing was created during disease scan! "
        f"Initial: {initial_listing_count}, Current: {new_listing_count}"
    )

    # CRITICAL: Verify Marketplace still has initial count
    market_resp = client.get("/api/listings/marketplace")
    assert market_resp.json().get("count", 0) == initial_market_count

    print(f"[PASSED] Disease scan created DiseaseRecord #{disease_record_id} with status PENDING_AGENT_REVIEW.")
    print("[PASSED] Prescription locked. ZERO Listing entries created in database.")
    print(f"[PASSED] Buyer Marketplace strictly isolated (count unchanged: {initial_market_count}).")

    # =========================================================================
    # TEST 2: Field Agent Queue Retrieval
    # =========================================================================
    print("\n--- TEST 2: Field Agent Queue Retrieval ---")

    queue_resp = client.get("/api/verifications/disease-scans?status=PENDING_AGENT_REVIEW")
    assert queue_resp.status_code == 200
    queue_data = queue_resp.json()
    assert queue_data.get("success") is True

    found = any(s["id"] == disease_record_id for s in queue_data.get("disease_scans", []))
    assert found, f"Record #{disease_record_id} not found in PENDING_AGENT_REVIEW queue"

    print(f"[PASSED] Record #{disease_record_id} successfully listed in Field Agent pending review queue.")

    # =========================================================================
    # TEST 3: Field Agent Action REJECT (status = REJECTED)
    # =========================================================================
    print("\n--- TEST 3: Field Agent Action REJECT (Dispatch Field Visit) ---")

    # Create a second scan specifically to test REJECT
    reject_record = DiseaseRecord(
        farmer_id=farmer_id,
        crop_type="potato",
        image_url="uploads/test_potato.jpg",
        confidence=62.5,
        predicted_pathogen="Late Blight (Phytophthora infestans)",
        scientific_name="Phytophthora infestans",
        severity="high",
        status="PENDING_AGENT_REVIEW",
        prescription_chemical="Cymoxanil 8% + Mancozeb 64% WP",
        prescription_dosage="2.5 g / L water",
        prescription_phi="7-10 Days PHI",
        farm_area=2.0,
        geolocation="Raipur, Chhattisgarh",
        created_at=db_record.created_at
    )
    db.add(reject_record)
    db.commit()
    db.refresh(reject_record)

    reject_resp = client.post(
        f"/api/verifications/disease-scans/{reject_record.id}/reject",
        json={"agent_name": "Field Agent Rahul", "reason": "Ambiguous chlorotic margins require physical on-site audit."}
    )
    assert reject_resp.status_code == 200
    reject_data = reject_resp.json()
    assert reject_data.get("success") is True
    assert reject_data.get("status") == "NEEDS_PHYSICAL_VISIT"

    # Verify notification pushed to farmer
    notif = reject_data.get("notification", {})
    assert "Your disease scan requires on-site verification. An Agri-Student Agent has been assigned to visit your field." in notif.get("message", "")

    # Verify in DB
    db.commit()
    db.refresh(reject_record)
    assert reject_record.status == "NEEDS_PHYSICAL_VISIT"

    # Verify retrieved in Pending Field Visits queue
    visits_resp = client.get("/api/verifications/disease-scans?status=NEEDS_PHYSICAL_VISIT")
    visits_found = any(s["id"] == reject_record.id for s in visits_resp.json().get("disease_scans", []))
    assert visits_found, "Rejected record not found in NEEDS_PHYSICAL_VISIT queue"

    # Verify still ZERO listings created
    assert db.query(Listing).count() == initial_listing_count
    assert client.get("/api/listings/marketplace").json().get("count", 0) == initial_market_count

    print(f"[PASSED] Reject handler transitioned #{reject_record.id} to NEEDS_PHYSICAL_VISIT.")
    print("[PASSED] Farmer notification generated: 'An Agri-Student Agent has been assigned to visit your field.'")
    print("[PASSED] Case moved into Pending Field Visits queue.")
    print("[PASSED] ZERO listings created or modified.")

    # =========================================================================
    # TEST 4: Field Agent Action APPROVE (status = APPROVED)
    # =========================================================================
    print("\n--- TEST 4: Field Agent Action APPROVE (Issue ICAR Prescription) ---")

    approve_resp = client.post(
        f"/api/verifications/disease-scans/{disease_record_id}/approve",
        json={
            "agent_name": "Field Agent Rahul (Agri-Student)",
            "remarks": "Early blight target-board concentric lesions confirmed. Authorized ICAR Mancozeb regimen."
        }
    )
    assert approve_resp.status_code == 200
    appr_data = approve_resp.json()
    assert appr_data.get("success") is True
    assert appr_data.get("status") == "VERIFIED_HEALTH_RECORD"

    # Check ICAR prescription details in response
    rx = appr_data.get("prescription", {})
    assert "chemical_name" in rx and rx["chemical_name"]
    assert "exact_dosage" in rx and rx["exact_dosage"]
    assert "pre_harvest_interval" in rx and rx["pre_harvest_interval"]

    # Check farmer notification
    appr_notif = appr_data.get("notification", {})
    assert "ICAR Prescription" in appr_notif.get("title", "")
    assert rx["chemical_name"] in appr_notif.get("message", "")

    # Verify DB update
    db.commit()
    db.refresh(db_record)
    assert db_record.status == "VERIFIED_HEALTH_RECORD"
    assert db_record.verified_at is not None

    # CRITICAL: Verify ZERO Marketplace Leakage after approval
    post_approve_listings = db.query(Listing).count()
    assert post_approve_listings == initial_listing_count, (
        f"CRITICAL MARKETPLACE LEAK: Approving disease scan created a Listing! "
        f"Expected: {initial_listing_count}, Found: {post_approve_listings}"
    )

    post_approve_market = client.get("/api/listings/marketplace").json().get("count", 0)
    assert post_approve_market == initial_market_count, (
        f"CRITICAL MARKETPLACE LEAK: Marketplace count increased after disease approval! "
        f"Expected: {initial_market_count}, Found: {post_approve_market}"
    )

    print(f"[PASSED] Approve handler transitioned #{disease_record_id} to VERIFIED_HEALTH_RECORD.")
    print(f"[PASSED] ICAR Agronomic Prescription: {rx['chemical_name']} @ {rx['exact_dosage']} ({rx['pre_harvest_interval']}).")
    print("[PASSED] Farmer notification delivered with ICAR safety warnings.")
    print(f"[PASSED] ZERO Marketplace leakage: Marketplace listings count remains strictly {initial_market_count}.")

    # =========================================================================
    # TEST 5: Legitimate Pre-Harvest Listing Verification (Sanity Check)
    # =========================================================================
    print("\n--- TEST 5: Legitimate Pre-Harvest Forward Contract Verification ---")

    # Explicit farmer harvest listing for future sale
    legit_listing = Listing(
        farmer_id=farmer_id,
        crop_type="wheat",
        photo_path="uploads/legit_wheat.jpg",
        health_status="Healthy",
        confidence=0.96,
        harvest_date="2026-09-20",
        quantity_est=5000.0,
        status="pending"
    )
    db.add(legit_listing)
    db.commit()
    db.refresh(legit_listing)

    legit_verif = Verification(
        listing_id=legit_listing.id,
        agent_name="Agent Rahul",
        status="pending",
        remarks="Farmer pre-harvest declaration submitted for harvest lot."
    )
    db.add(legit_verif)
    db.commit()
    db.refresh(legit_verif)

    # Verify harvest listing
    verify_resp = client.put(
        f"/api/verifications/{legit_verif.id}",
        json={"status": "verified", "agent_name": "Agent Rahul", "remarks": "Grade A Wheat verified for forward contracts."}
    )
    assert verify_resp.status_code == 200

    db.commit()
    db.refresh(legit_listing)
    assert legit_listing.status == "available"

    # Now marketplace should have exactly initial_market_count + 1
    new_market_count = client.get("/api/listings/marketplace").json().get("count", 0)
    assert new_market_count == initial_market_count + 1

    print("[PASSED] Legitimate pre-harvest listing verified and published to Marketplace.")
    print(f"[PASSED] Marketplace now contains {new_market_count} verified commercial lots.")

    # Cleanup test additions safely honoring foreign keys
    try:
        db.delete(legit_verif)
        db.commit()
        db.delete(legit_listing)
        db.commit()
        db.delete(reject_record)
        db.delete(db_record)
        db.commit()
    except Exception as cleanup_err:
        db.rollback()
        print(f"[NOTE] Cleanup handled: {cleanup_err}")

    print("\n" + "=" * 75)
    print("  ALL 5 DISEASE VERIFICATION & MARKETPLACE LEAK TESTS PASSED!")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    run_tests()
