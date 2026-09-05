import json
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import get_db
from app.models.listing import Listing
from app.models.verification import Verification
from app.models.farmer import Farmer

client = TestClient(app)
db = next(get_db())

# Ensure a farmer exists
farmer = db.query(Farmer).first()
if not farmer:
    farmer = Farmer(name='Orchestration Test Farmer', contact='9876500001', location='Raipur', farm_size=5.0)
    db.add(farmer)
    db.commit()
    db.refresh(farmer)

print(f"Using Farmer ID: {farmer.id}")

# 1. Create a Listing via API
payload = {
    "farmer_id": farmer.id,
    "crop_type": "Wheat HD-2967",
    "photo_path": "uploads/test_wheat.jpg",
    "health_status": "Healthy",
    "confidence": 0.8850,
    "harvest_date": "2026-10-15",
    "quantity_est": 2500.0
}

resp = client.post("/api/listings/", json=payload)
print("CREATE LISTING HTTP RESPONSE:", resp.status_code, resp.json())

# Query the database directly with fresh session
from app.database.connection import SessionLocal
db_fresh = SessionLocal()
created_listing_id = resp.json()["listing"]["id"]
db_listing = db_fresh.query(Listing).filter(Listing.id == created_listing_id).first()
db_verification = db_fresh.query(Verification).filter(Verification.listing_id == created_listing_id).first()

print("\n--- ACTUAL DATABASE RECORDS ---")
print(f"LISTING: id={db_listing.id}, farmer_id={db_listing.farmer_id}, crop={db_listing.crop_type}, status={db_listing.status}, quantity={db_listing.quantity_est}, confidence={db_listing.confidence}")
if db_verification:
    print(f"VERIFICATION: id={db_verification.id}, listing_id={db_verification.listing_id}, agent={db_verification.agent_name}, status={db_verification.status}, remarks=\"{db_verification.remarks}\", created_at={db_verification.created_at}")
else:
    print("VERIFICATION: NOT FOUND!")
