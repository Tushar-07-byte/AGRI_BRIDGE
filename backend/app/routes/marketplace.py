from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..models.farmer import Farmer
from ..models.listing import Listing
from ..models.order import Order
from ..models.buyer import Buyer


router = APIRouter(
    prefix="/api/marketplace",
    tags=["Marketplace"]
)


@router.get("/")
def get_marketplace(db: Session = Depends(get_db)):

    results = (
        db.query(
            Farmer.id.label("farmer_id"),
            Farmer.name.label("farmer_name"),

            Listing.id.label("listing_id"),
            Listing.crop_type,
            Listing.health_status,
            Listing.confidence,
            Listing.harvest_date,
            Listing.quantity_est,
            Listing.status,

            Order.id.label("order_id"),
            Order.buyer_id,
            Order.committed_at,

            Buyer.name.label("buyer_name")
        )
        .join(Listing, Farmer.id == Listing.farmer_id)
        .join(Order, Listing.id == Order.listing_id)
        .join(Buyer, Order.buyer_id == Buyer.id)
        .order_by(Farmer.id)
        .all()
    )

    return {
        "success": True,
        "count": len(results),
        "marketplace": [
            {
                "farmer": {
                    "id": row.farmer_id,
                    "name": row.farmer_name
                },
                "listing": {
                    "id": row.listing_id,
                    "crop_type": row.crop_type,
                    "health_status": row.health_status,
                    "confidence": float(row.confidence)
                    if row.confidence is not None else None,
                    "harvest_date": row.harvest_date,
                    "quantity_est": float(row.quantity_est)
                    if row.quantity_est is not None else None,
                    "status": row.status
                },
                "order": {
                    "id": row.order_id,
                    "buyer_id": row.buyer_id,
                    "buyer_name": row.buyer_name,
                    "committed_at": row.committed_at
                }
            }
            for row in results
        ]
    }


# =============================================================================
# TWO-PHASE MARKETPLACE GUIDANCE ENDPOINTS
# =============================================================================

@router.get("/guidance/{crop_id}")
def get_marketplace_guidance(crop_id: str, db: Session = Depends(get_db)):
    """
    Returns complete two-phase marketplace context for a crop:
    1. Pre-Harvest Marketplace
    2. Post-Harvest Cleaned Crop
    """
    from ..crop_monitoring.marketplace_context import get_marketplace_context
    context = get_marketplace_context(crop_id=crop_id, db_session=db)
    return {
        "success": True,
        "data": context
    }


@router.get("/pre-harvest/{crop_id}")
def get_pre_harvest_guidance(crop_id: str, db: Session = Depends(get_db)):
    """
    Returns Pre-Harvest Marketplace guidance only.
    """
    from ..crop_monitoring.marketplace_context import get_marketplace_context
    context = get_marketplace_context(crop_id=crop_id, db_session=db)
    return {
        "success": True,
        "data": context.get("pre_harvest_marketplace", {})
    }


@router.get("/post-harvest/{crop_id}")
def get_post_harvest_guidance(crop_id: str, db: Session = Depends(get_db)):
    """
    Returns Post-Harvest Cleaned Crop guidance only.
    """
    from ..crop_monitoring.marketplace_context import get_marketplace_context
    context = get_marketplace_context(crop_id=crop_id, db_session=db)
    return {
        "success": True,
        "data": context.get("post_harvest_cleaned_crop", {})
    }


@router.post("/quality-assessment")
def perform_crop_quality_assessment(payload: dict):
    """
    Assesses physical quality parameters for harvested and cleaned crop.
    Strictly separates target grade vs achieved grade and calculates potential premium pricing.
    """
    from ..services.marketplace_quality_service import assess_crop_quality
    
    crop_name = payload.get("crop_name", "wheat")
    target_grade = payload.get("target_grade", "Grade A")
    moisture_pct = float(payload.get("moisture_pct", 12.0))
    foreign_matter_pct = float(payload.get("foreign_matter_pct", 1.0))
    defects_pct = float(payload.get("defects_pct", 2.0))
    uniformity_pct = float(payload.get("uniformity_pct", 90.0))
    custom_base_price = float(payload.get("base_price", 0.0)) if payload.get("base_price") else None
    
    assessment = assess_crop_quality(
        crop_name=crop_name,
        target_grade=target_grade,
        moisture_pct=moisture_pct,
        foreign_matter_pct=foreign_matter_pct,
        defects_pct=defects_pct,
        uniformity_pct=uniformity_pct,
        custom_base_price=custom_base_price
    )
    
    return {
        "success": True,
        "data": assessment
    }
