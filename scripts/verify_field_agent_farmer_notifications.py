#!/usr/bin/env python3
"""
Verification Script: Field Agent -> Farmer Notification Dashboard End-to-End Flow
Tests:
1. Field Agent Approves Disease Diagnosis -> ICAR Prescription Notification created and delivered to Farmer Dashboard.
2. Field Agent Dispatches On-Site Visit -> Inspection Dispatched Notification created with actions (Confirm/Reject/Reschedule).
3. Field Agent Verifies Pre-Harvest Marketplace Listing -> Listing Verified Notification created and delivered.
4. Farmer Notification Dashboard endpoints (/api/farmers/notifications and /api/farmers/{farmer_id}/notifications) with tab filtering.
5. Read-state management (/api/farmers/notifications/{id}/read and /read-all).
"""

import os
import sys
from datetime import datetime

# Reconfigure stdout for UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient

# Add backend directory to path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
from app.database.connection import SessionLocal
from app.models.farmer import Farmer
from app.models.disease_record import DiseaseRecord
from app.models.listing import Listing
from app.models.verification import Verification
from app.models.action_plan import NotificationEvent

client = TestClient(app)

def run_tests():
    db = SessionLocal()
    total_tests = 0
    passed_tests = 0

    print("======================================================================")
    print("VERIFICATION: FIELD AGENT -> FARMER NOTIFICATION DASHBOARD FLOW")
    print("======================================================================\n")

    # Ensure a test farmer exists
    farmer = db.query(Farmer).first()
    if not farmer:
        farmer = Farmer(name="Test Farmer Ramesh")
        db.add(farmer)
        db.commit()
        db.refresh(farmer)
    farmer_id = farmer.id

    try:
        # ---------------------------------------------------------------------
        # TEST 1: Field Agent Approves Disease Scan -> ICAR Rx Notification
        # ---------------------------------------------------------------------
        print("--- Test 1: Field Agent Approves Disease Scan ---")
        total_tests += 1
        
        disease_record = DiseaseRecord(
            farmer_id=farmer_id,
            crop_type="tomato",
            predicted_pathogen="Tomato Early Blight",
            confidence=0.92,
            severity="moderate",
            status="PENDING_AGENT_REVIEW",
            prescription_chemical="Mancozeb 75% WP",
            prescription_dosage="2.0 g / L water",
            prescription_phi="7-10 Days PHI",
            prescription_organic="Neem Oil @ 5ml/L",
            created_at=datetime.utcnow()
        )
        db.add(disease_record)
        db.commit()
        db.refresh(disease_record)

        # Field agent approves
        approve_payload = {
            "agent_name": "Field Agent Rahul",
            "remarks": "Foliage lesions verified as early blight. Approved ICAR prescription."
        }
        res = client.post(f"/api/verifications/disease-scans/{disease_record.id}/approve", json=approve_payload)
        assert res.status_code == 200, f"Approve failed with status {res.status_code}"
        approve_data = res.json()
        assert approve_data["success"] is True

        # Check farmer notification dashboard endpoint
        notif_res = client.get(f"/api/farmers/{farmer_id}/notifications?filter_type=TREATMENTS")
        assert notif_res.status_code == 200, f"Get notifs failed with {notif_res.status_code}"
        notif_data = notif_res.json()
        notifs = notif_data.get("notifications", [])
        
        rx_notif = next((n for n in notifs if n["notification_type"] == "TREATMENT_APPROVED" and n["related_id"] == disease_record.id), None)
        assert rx_notif is not None, "Treatment approval notification was NOT found in farmer notifications!"
        assert "Mancozeb 75% WP" in rx_notif["message"] or rx_notif["meta_data"].get("chemical_name") == "Mancozeb 75% WP"
        print(f"[PASS] Treatment notification received: '{rx_notif['title']}'")
        passed_tests += 1

        # ---------------------------------------------------------------------
        # TEST 2: Field Agent Rejects Disease Scan -> On-Site Visit Dispatched
        # ---------------------------------------------------------------------
        print("\n--- Test 2: Field Agent Rejects Disease Scan (Dispatch On-Site Visit) ---")
        total_tests += 1

        disease_record_2 = DiseaseRecord(
            farmer_id=farmer_id,
            crop_type="wheat",
            predicted_pathogen="Wheat Rust",
            confidence=0.55,
            severity="high",
            status="PENDING_AGENT_REVIEW",
            created_at=datetime.utcnow()
        )
        db.add(disease_record_2)
        db.commit()
        db.refresh(disease_record_2)

        reject_payload = {
            "agent_name": "Field Agent Vikram",
            "reason": "Borderline AI confidence. Physical stem rust audit required."
        }
        res2 = client.post(f"/api/verifications/disease-scans/{disease_record_2.id}/reject", json=reject_payload)
        assert res2.status_code == 200, f"Reject failed with status {res2.status_code}"
        
        # Check farmer notification dashboard endpoint for INSPECTIONS
        notif_res2 = client.get(f"/api/farmers/{farmer_id}/notifications?filter_type=INSPECTIONS")
        assert notif_res2.status_code == 200
        notif_data2 = notif_res2.json()
        notifs2 = notif_data2.get("notifications", [])
        
        insp_notif = next((n for n in notifs2 if n["notification_type"] == "INSPECTION_DISPATCHED" and n["related_id"] == disease_record_2.id), None)
        assert insp_notif is not None, "Inspection dispatched notification was NOT found in farmer notifications!"
        print(f"[PASS] Inspection notification received: '{insp_notif['title']}'")
        passed_tests += 1

        # ---------------------------------------------------------------------
        # TEST 3: Field Agent Verifies Pre-Harvest Marketplace Listing
        # ---------------------------------------------------------------------
        print("\n--- Test 3: Field Agent Verifies Marketplace Listing ---")
        total_tests += 1

        listing = Listing(
            farmer_id=farmer_id,
            crop_type="Wheat (Sharbati)",
            quantity_est=2000.0,
            status="pending"
        )
        db.add(listing)
        db.commit()
        db.refresh(listing)

        verification = Verification(
            listing_id=listing.id,
            agent_name="Field Agent Rahul",
            status="pending",
            remarks="Pending physical lot inspection."
        )
        db.add(verification)
        db.commit()
        db.refresh(verification)

        # Field agent updates verification to verified
        verif_payload = {
            "status": "verified",
            "agent_name": "Field Agent Rahul",
            "remarks": "Grade A grain quality certified on-site."
        }
        verif_res = client.put(f"/api/verifications/{verification.id}", json=verif_payload)
        assert verif_res.status_code == 200, f"Verification update failed: {verif_res.status_code}"

        # Check farmer notification dashboard endpoint for ORDERS/LISTINGS
        notif_res3 = client.get(f"/api/farmers/{farmer_id}/notifications?filter_type=ORDERS")
        assert notif_res3.status_code == 200
        notif_data3 = notif_res3.json()
        notifs3 = notif_data3.get("notifications", [])

        listing_notif = next((n for n in notifs3 if n["notification_type"] == "LISTING_VERIFIED" and n["related_id"] == listing.id), None)
        assert listing_notif is not None, "Listing verification notification was NOT found in farmer notifications!"
        print(f"[PASS] Listing verification notification received: '{listing_notif['title']}'")
        passed_tests += 1

        # ---------------------------------------------------------------------
        # TEST 4: Global Notification Fetching & Tab Counters
        # ---------------------------------------------------------------------
        print("\n--- Test 4: Global Notification Fetching & Unread Counts ---")
        total_tests += 1

        all_notif_res = client.get(f"/api/farmers/notifications")
        assert all_notif_res.status_code == 200
        all_data = all_notif_res.json()
        assert all_data["success"] is True
        assert all_data["total_count"] >= 3
        assert all_data["unread_count"] >= 1
        print(f"[PASS] Total notifications in dashboard: {all_data['total_count']}, Unread: {all_data['unread_count']}")
        passed_tests += 1

        # ---------------------------------------------------------------------
        # TEST 5: Mark Notifications as Read
        # ---------------------------------------------------------------------
        print("\n--- Test 5: Mark Notification Read ---")
        total_tests += 1

        if rx_notif:
            read_res = client.post(f"/api/farmers/notifications/{rx_notif['id']}/read")
            assert read_res.status_code == 200
            assert read_res.json()["success"] is True
            print(f"[PASS] Notification #{rx_notif['id']} successfully marked as READ.")

        read_all_res = client.post(f"/api/farmers/notifications/read-all?farmer_id={farmer_id}")
        assert read_all_res.status_code == 200
        assert read_all_res.json()["success"] is True
        print("[PASS] All notifications marked as READ.")
        passed_tests += 1

    finally:
        db.close()

    print("\n======================================================================")
    print(f"FINAL RESULT: {passed_tests}/{total_tests} Tests Passed ({passed_tests/total_tests*100:.1f}%)")
    print("======================================================================")

    if passed_tests == total_tests:
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(run_tests())
