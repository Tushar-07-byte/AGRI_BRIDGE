"""
Test Suite: Confidence Standardization & DECIMAL(5,4) Boundary Safety
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.models.listing import Listing
from app.models.farmer import Farmer

client = TestClient(app)

def run_confidence_tests():
    print("\n======================================================================")
    print("TEST: CONFIDENCE STANDARDIZATION & DECIMAL(5,4) BOUNDARY SAFETY")
    print("======================================================================")

    db = SessionLocal()
    farmer = db.query(Farmer).first()
    if not farmer:
        farmer = Farmer(name="Balwinder Singh")
        db.add(farmer)
        db.commit()
        db.refresh(farmer)

    farmer_id = farmer.id

    # Test 1: Submitting confidence in percentage format (88.5)
    print("\n--- Test 1: Submitting Percentage Format (confidence = 88.5) ---")
    resp_pct = client.post(
        "/api/listings/",
        json={
            "farmer_id": farmer_id,
            "crop_type": "Wheat",
            "photo_path": "uploads/wheat_sample.jpg",
            "health_status": "Healthy",
            "confidence": 88.5,
            "harvest_date": "2026-09-30",
            "quantity_est": 1500.0
        }
    )
    print(f"Status: {resp_pct.status_code}")
    assert resp_pct.status_code == 200, f"Failed percentage submission: {resp_pct.text}"
    listing_pct = resp_pct.json()["listing"]
    print(f"Returned Confidence: {listing_pct['confidence']} (Normalized from 88.5)")
    assert listing_pct["confidence"] == 0.885

    # Verify directly in MySQL with fresh session
    db.close()
    fresh_db = SessionLocal()
    db_item = fresh_db.query(Listing).filter(Listing.id == listing_pct["id"]).first()
    print(f"MySQL Stored DECIMAL(5,4): {db_item.confidence}")
    assert float(db_item.confidence) == 0.8850

    # Test 2: Submitting confidence in fraction format (0.9234)
    print("\n--- Test 2: Submitting Fraction Format (confidence = 0.9234) ---")
    resp_frac = client.post(
        "/api/listings/",
        json={
            "farmer_id": farmer_id,
            "crop_type": "Tomato",
            "photo_path": "uploads/tomato_sample.jpg",
            "health_status": "Early Blight",
            "confidence": 0.9234,
            "harvest_date": "2026-09-25",
            "quantity_est": 800.0
        }
    )
    print(f"Status: {resp_frac.status_code}")
    assert resp_frac.status_code == 200
    listing_frac = resp_frac.json()["listing"]
    print(f"Returned Confidence: {listing_frac['confidence']}")
    assert listing_frac["confidence"] == 0.9234

    # Test 3: Submitting Out-of-Bounds High Value (150.0) -> Expect HTTP 400
    print("\n--- Test 3: Submitting Out-of-Range High Value (confidence = 150.0) ---")
    resp_high = client.post(
        "/api/listings/",
        json={
            "farmer_id": farmer_id,
            "crop_type": "Rice",
            "confidence": 150.0
        }
    )
    print(f"Status: {resp_high.status_code}, Body: {resp_high.json()}")
    assert resp_high.status_code == 400
    assert "Invalid confidence value" in resp_high.json()["detail"]

    # Test 4: Submitting Negative Value (-5.0) -> Expect HTTP 400
    print("\n--- Test 4: Submitting Negative Value (confidence = -5.0) ---")
    resp_neg = client.post(
        "/api/listings/",
        json={
            "farmer_id": farmer_id,
            "crop_type": "Rice",
            "confidence": -5.0
        }
    )
    print(f"Status: {resp_neg.status_code}, Body: {resp_neg.json()}")
    assert resp_neg.status_code == 400
    assert "Invalid confidence value" in resp_neg.json()["detail"]

    # Test 5: Submitting Non-numeric String -> Expect HTTP 400
    print("\n--- Test 5: Submitting Non-numeric String (confidence = 'high') ---")
    resp_str = client.post(
        "/api/listings/",
        json={
            "farmer_id": farmer_id,
            "crop_type": "Rice",
            "confidence": "high"
        }
    )
    print(f"Status: {resp_str.status_code}, Body: {resp_str.json()}")
    assert resp_str.status_code == 400
    assert "Invalid confidence format" in resp_str.json()["detail"]

    db.close()
    print("\n======================================================================")
    print("ALL CONFIDENCE STANDARDIZATION & SAFETY NET TESTS PASSED!")
    print("======================================================================")

if __name__ == "__main__":
    run_confidence_tests()
