from datetime import datetime, date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..models.listing import Listing
from ..models.farmer import Farmer
from ..models.verification import Verification


router = APIRouter(
    prefix="/api/listings",
    tags=["Listings"]
)


# =========================================
# GET ALL LISTINGS (Farmer & Field Agent View)
# =========================================

@router.get("/")
def get_listings(db: Session = Depends(get_db)):
    """
    Returns all crop listings regardless of verification status.
    Used by farmers (to see their crops) and field agents (to see pending items).
    """
    listings = db.query(Listing).all()

    return {
        "success": True,
        "count": len(listings),
        "listings": [
            {
                "id": listing.id,
                "farmer_id": listing.farmer_id,
                "crop_type": listing.crop_type,
                "photo_path": listing.photo_path,
                "health_status": listing.health_status,
                "confidence": float(listing.confidence)
                if listing.confidence is not None else None,
                "harvest_date": listing.harvest_date,
                "quantity_est": float(listing.quantity_est)
                if listing.quantity_est is not None else None,
                "status": listing.status
            }
            for listing in listings
        ]
    }


# =========================================
# GET BUYER MARKETPLACE (Strictly Verified Only)
# =========================================

@router.get("/marketplace")
def get_marketplace_listings(db: Session = Depends(get_db)):
    """
    Buyer-facing listings endpoint: ONLY returns listings where the linked
    verification record has status == 'verified'.
    """
    results = (
        db.query(Listing, Verification)
        .join(Verification, Listing.id == Verification.listing_id)
        .filter(Verification.status == "verified", Listing.status == "available")
        .order_by(Listing.id.desc())
        .all()
    )

    return {
        "success": True,
        "count": len(results),
        "listings": [
            {
                "id": listing.id,
                "farmer_id": listing.farmer_id,
                "crop_type": listing.crop_type,
                "photo_path": listing.photo_path,
                "health_status": listing.health_status,
                "confidence": float(listing.confidence)
                if listing.confidence is not None else None,
                "harvest_date": listing.harvest_date,
                "quantity_est": float(listing.quantity_est)
                if listing.quantity_est is not None else None,
                "status": listing.status,
                "verification_status": verification.status,
                "agent_name": verification.agent_name,
                "verified_at": verification.verified_at.isoformat()
                if verification.verified_at else None
            }
            for listing, verification in results
        ]
    }


# =========================================
# CREATE LISTING
# =========================================

@router.post("/")
def create_listing(
    listing_data: dict,
    db: Session = Depends(get_db)
):

    farmer_id = listing_data.get("farmer_id")

    if not farmer_id:
        raise HTTPException(
            status_code=400,
            detail="farmer_id is required"
        )

    farmer = db.query(Farmer).filter(
        Farmer.id == farmer_id
    ).first()

    if not farmer:
        raise HTTPException(
            status_code=404,
            detail="Farmer not found"
        )

    # -------------------------------------------------------------------------
    # CONFIDENCE VALIDATION & NORMALIZATION (DECIMAL(5,4) SAFE)
    # Accepts fraction (0.0 - 1.0) or percentage (0.0% - 100.0%)
    # -------------------------------------------------------------------------
    raw_confidence = listing_data.get("confidence")
    normalized_confidence = None

    if raw_confidence is not None:
        try:
            val = float(raw_confidence)
            # If provided as percentage (1.0 < val <= 100.0), normalize to fraction
            if 1.0 < val <= 100.0:
                val = val / 100.0
            elif val < 0.0 or val > 100.0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid confidence value: {raw_confidence}. Must be between 0.0 and 1.0 (or 0% - 100%)."
                )
            normalized_confidence = round(val, 4)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid confidence format: {raw_confidence}. Must be a valid numeric value."
            )

    # Check for identical duplicate submission
    crop_type_input = listing_data.get("crop_type")
    harvest_date_input = listing_data.get("harvest_date")
    quantity_input = listing_data.get("quantity_est")

    existing_duplicate = db.query(Listing).filter(
        Listing.farmer_id == farmer_id,
        Listing.crop_type == crop_type_input,
        Listing.harvest_date == harvest_date_input,
        Listing.quantity_est == quantity_input,
        Listing.status == "pending"
    ).first()

    if existing_duplicate:
        return {
            "success": True,
            "message": "This listing already exists and is pending verification.",
            "listing": {
                "id": existing_duplicate.id,
                "farmer_id": existing_duplicate.farmer_id,
                "crop_type": existing_duplicate.crop_type,
                "photo_path": existing_duplicate.photo_path,
                "health_status": existing_duplicate.health_status,
                "confidence": float(existing_duplicate.confidence) if existing_duplicate.confidence is not None else None,
                "harvest_date": existing_duplicate.harvest_date,
                "quantity_est": float(existing_duplicate.quantity_est) if existing_duplicate.quantity_est is not None else None,
                "status": existing_duplicate.status
            }
        }

    raw_health = listing_data.get("health_status")
    if isinstance(raw_health, dict):
        health_str = raw_health.get("name") or raw_health.get("disease") or "Diseased"
    else:
        health_str = str(raw_health) if raw_health else "Healthy"

    listing = Listing(
        farmer_id=farmer_id,
        crop_type=crop_type_input,
        photo_path=listing_data.get("photo_path"),
        health_status=health_str[:100],
        confidence=normalized_confidence,
        harvest_date=harvest_date_input,
        quantity_est=quantity_input,
        # A crop is not available to buyers until a field agent verifies it.
        status="pending"
    )

    db.add(listing)
    db.flush()

    # Create verification record with status 'pending'
    existing_verification = db.query(Verification).filter(
        Verification.listing_id == listing.id
    ).first()

    if not existing_verification:
        verification = Verification(
            listing_id=listing.id,
            agent_name="Agent Rahul",
            status="pending",
            remarks="Crop submitted for field verification.",
            created_at=datetime.utcnow()
        )
        db.add(verification)

    try:
        db.commit()
        db.refresh(listing)
    except Exception:
        db.rollback()
        raise

    return {
        "success": True,
        "message": "Listing created successfully",
        "listing": {
            "id": listing.id,
            "farmer_id": listing.farmer_id,
            "crop_type": listing.crop_type,
            "photo_path": listing.photo_path,
            "health_status": listing.health_status,
            "confidence": float(listing.confidence)
            if listing.confidence is not None else None,
            "harvest_date": listing.harvest_date,
            "quantity_est": float(listing.quantity_est)
            if listing.quantity_est is not None else None,
            "status": listing.status
        }
    }
