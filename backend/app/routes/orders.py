from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..models.order import Order
from ..models.listing import Listing
from ..models.buyer import Buyer
from ..models.user import User
from ..models.verification import Verification


router = APIRouter(
    prefix="/api/orders",
    tags=["Orders"]
)


# =========================================
# HELPER: BENCHMARK RATES
# =========================================

def get_crop_benchmark_price(crop_type: str) -> str:
    rate_map = {
        "wheat": "₹2,520 / Quintal",
        "sharbati wheat": "₹2,520 / Quintal",
        "tomato": "₹1,850 / Quintal",
        "potato": "₹1,420 / Quintal",
        "rice": "₹2,380 / Quintal",
        "cotton": "₹6,620 / Quintal",
        "maize": "₹2,090 / Quintal"
    }
    return rate_map.get((crop_type or "").lower(), "₹2,450 / Quintal")


# =========================================
# GET ALL ORDERS (with optional farmer/buyer filter)
# =========================================

@router.get("/")
def get_orders(
    farmer_id: int = None,
    buyer_id: int = None,
    db: Session = Depends(get_db)
):
    query = (
        db.query(Order, Listing, Buyer)
        .outerjoin(Listing, Order.listing_id == Listing.id)
        .outerjoin(Buyer, Order.buyer_id == Buyer.id)
    )

    if farmer_id:
        query = query.filter(Listing.farmer_id == farmer_id)
    if buyer_id:
        query = query.filter(Order.buyer_id == buyer_id)

    results = query.order_by(Order.id.desc()).all()

    orders_list = []
    for order, listing, buyer in results:
        crop_type = listing.crop_type if listing else "Agricultural Crop"
        qty = float(listing.quantity_est) if (listing and listing.quantity_est) else 50.0

        orders_list.append({
            "id": order.id,
            "listing_id": order.listing_id,
            "buyer_id": order.buyer_id,
            "buyer_name": buyer.name if buyer else f"AgroCorp Procurement #{order.buyer_id}",
            "farmer_id": listing.farmer_id if listing else None,
            "crop_type": crop_type,
            "quantity": qty,
            "harvest_date": str(listing.harvest_date) if (listing and listing.harvest_date) else "Expected: Next Month",
            "health_status": listing.health_status if listing else "Grade A Stand",
            "photo_path": listing.photo_path if listing else None,
            "price": get_crop_benchmark_price(crop_type),
            "committed_at": order.committed_at.isoformat() if order.committed_at else None,
            "status": "Buyer Committed"
        })

    return {
        "success": True,
        "count": len(orders_list),
        "orders": orders_list
    }


# =========================================
# GET ORDERS FOR SPECIFIC FARMER
# =========================================

@router.get("/farmer/{farmer_id}")
def get_farmer_orders(
    farmer_id: int,
    db: Session = Depends(get_db)
):
    return get_orders(farmer_id=farmer_id, db=db)


# =========================================
# GET ORDER DETAIL BY ID
# =========================================

@router.get("/{order_id}")
def get_order_detail(
    order_id: int,
    db: Session = Depends(get_db)
):
    result = (
        db.query(Order, Listing, Buyer)
        .outerjoin(Listing, Order.listing_id == Listing.id)
        .outerjoin(Buyer, Order.buyer_id == Buyer.id)
        .filter(Order.id == order_id)
        .first()
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Order {order_id} not found"
        )

    order, listing, buyer = result
    crop_type = listing.crop_type if listing else "Agricultural Crop"
    qty = float(listing.quantity_est) if (listing and listing.quantity_est) else 50.0

    return {
        "success": True,
        "order": {
            "id": order.id,
            "listing_id": order.listing_id,
            "buyer_id": order.buyer_id,
            "buyer_name": buyer.name if buyer else f"AgroCorp Procurement #{order.buyer_id}",
            "farmer_id": listing.farmer_id if listing else None,
            "crop_type": crop_type,
            "quantity": qty,
            "harvest_date": str(listing.harvest_date) if (listing and listing.harvest_date) else "Expected: Next Month",
            "health_status": listing.health_status if listing else "Grade A Stand",
            "photo_path": listing.photo_path if listing else None,
            "price": get_crop_benchmark_price(crop_type),
            "committed_at": order.committed_at.isoformat() if order.committed_at else None,
            "status": "Buyer Committed"
        }
    }


# =========================================
# CREATE ORDER (Commit to Buy)
# =========================================

@router.post("/")
def create_order(
    order_data: dict,
    db: Session = Depends(get_db)
):
    listing_id = order_data.get("listing_id")
    buyer_id = order_data.get("buyer_id")

    # =====================================
    # VALIDATE INPUT
    # =====================================

    if not listing_id or not buyer_id:
        raise HTTPException(
            status_code=400,
            detail="listing_id and buyer_id are both required"
        )

    # =====================================
    # CHECK LISTING EXISTS
    # =====================================

    listing = db.query(Listing).filter(
        Listing.id == listing_id
    ).first()

    if not listing:
        raise HTTPException(
            status_code=404,
            detail=f"Listing {listing_id} not found"
        )

    # =====================================
    # CHECK BUYER EXISTS
    # =====================================

    buyer = db.query(Buyer).filter(
        Buyer.id == buyer_id
    ).first()

    if not buyer:
        # Check if buyer registered in User model
        user = db.query(User).filter(User.id == buyer_id).first()
        if user:
            buyer = Buyer(name=user.name)
            db.add(buyer)
            db.flush()
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Buyer {buyer_id} not found"
            )

    # =====================================
    # CHECK LISTING IS VERIFIED
    # =====================================

    verification = db.query(Verification).filter(
        Verification.listing_id == listing_id
    ).order_by(Verification.id.desc()).first()

    if not verification:
        raise HTTPException(
            status_code=400,
            detail="Order rejected: This listing has not been submitted for field verification."
        )

    if verification.status != "verified":
        raise HTTPException(
            status_code=400,
            detail=f"Order rejected: Listing {listing_id} is currently '{verification.status}'. Only field-agent verified crops can be purchased."
        )

    # =====================================
    # CHECK DUPLICATE COMMITMENT
    # =====================================

    existing_order = db.query(Order).filter(
        Order.listing_id == listing_id,
        Order.buyer_id == buyer_id
    ).first()

    if existing_order:
        raise HTTPException(
            status_code=409,
            detail="You have already committed to buy this listing"
        )

    # =====================================
    # CREATE ORDER
    # =====================================

    order = Order(
        listing_id=listing_id,
        buyer_id=buyer_id
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return {
        "success": True,
        "message": "Purchase committed successfully.",
        "order": {
            "id": order.id,
            "listing_id": order.listing_id,
            "buyer_id": order.buyer_id,
            "committed_at": str(order.committed_at)
        }
    }