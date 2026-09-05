from datetime import datetime
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..models.farmer import Farmer
from ..models.disease_record import DiseaseRecord
from ..models.action_plan import ActionPlan, NotificationEvent, FieldAgentEscalation
from ..models.listing import Listing
from ..models.order import Order
from ..models.buyer import Buyer
from ..models.verification import Verification


router = APIRouter(
    prefix="/api/farmers",
    tags=["Farmers"]
)



def format_relative_time(dt: datetime) -> str:
    if not dt:
        return "Recently"
    now = datetime.utcnow()
    diff = now - dt
    seconds = int(diff.total_seconds())
    if seconds < 0:
        return "Just now"
    if seconds < 120:
        return "Just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} mins ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hours ago"
    days = hours // 24
    if days == 1:
        return "Yesterday"
    if days < 30:
        return f"{days} days ago"
    return dt.strftime("%b %d, %Y")


@router.get("/")
def get_farmers(db: Session = Depends(get_db)):
    farmers = db.query(Farmer).all()

    return {
        "success": True,
        "count": len(farmers),
        "farmers": [
            {
                "id": farmer.id,
                "name": farmer.name
            }
            for farmer in farmers
        ]
    }


# ==============================================================================
# REAL-TIME FARMER ACTIVITY FEED
# ==============================================================================

@router.get("/activity")
@router.get("/{farmer_id}/activity")
def get_farmer_activity_feed(
    farmer_id: int = None,
    limit: int = 8,
    db: Session = Depends(get_db)
):
    events = []

    # 1. Real Disease Records (Leaf scans & Agronomist verifications)
    try:
        disease_q = db.query(DiseaseRecord)
        if farmer_id:
            disease_q = disease_q.filter(DiseaseRecord.farmer_id == farmer_id)
        recent_scans = disease_q.order_by(DiseaseRecord.created_at.desc()).limit(5).all()

        for s in recent_scans:
            conf_pct = int(s.confidence * 100) if s.confidence else 92
            event_time = s.verified_at or s.created_at or datetime.utcnow()
            if s.status == "VERIFIED_HEALTH_RECORD":
                title = "ICAR Regimen Verified"
                desc = f"{s.predicted_pathogen or s.crop_type} verified by Field Agent {s.agent_name or 'Rahul'}. Prescription issued."
                icon = "✅"
                bg = "bg-green"
            elif s.status == "NEEDS_PHYSICAL_VISIT":
                title = "On-Site Physical Audit Assigned"
                desc = f"{s.predicted_pathogen or s.crop_type} scan assigned to Agri-Student Field Agent for physical inspection."
                icon = "📍"
                bg = "bg-gold"
            else:
                title = "Crop Diagnosis Recorded"
                desc = f"Leaf scan for {s.crop_type}: {s.predicted_pathogen} ({conf_pct}% confidence) • Pending Agent Review"
                icon = "🌱"
                bg = "bg-green"

            events.append({
                "timestamp": event_time,
                "time": format_relative_time(event_time),
                "icon": icon,
                "bg": bg,
                "title": title,
                "desc": desc
            })
    except Exception as e:
        print("Error fetching disease records for activity:", e)

    # 2. Real Action Plans & Weather Spray Window Advisories
    try:
        plan_q = db.query(ActionPlan)
        if farmer_id:
            plan_q = plan_q.filter(ActionPlan.farmer_id == farmer_id)
        recent_plans = plan_q.order_by(ActionPlan.created_at.desc()).limit(5).all()

        for p in recent_plans:
            risk = p.risk_type.replace("_", " ").title() if p.risk_type else "Treatment"
            status_disp = p.status.replace("_", " ").title() if p.status else "Active"
            p_time = p.updated_at or p.created_at or datetime.utcnow()
            events.append({
                "timestamp": p_time,
                "time": format_relative_time(p_time),
                "icon": "🌦️",
                "bg": "bg-gold",
                "title": "Spray Window & Action Plan",
                "desc": f"Plan #{p.id}: {risk} evaluated for {p.district or 'Farm District'}. Status: {status_disp}."
            })
    except Exception as e:
        print("Error fetching action plans for activity:", e)

    # 3. Real Buyer Purchase Orders
    try:
        order_q = db.query(Order, Listing, Buyer).join(Listing, Order.listing_id == Listing.id).outerjoin(Buyer, Order.buyer_id == Buyer.id)
        if farmer_id:
            order_q = order_q.filter(Listing.farmer_id == farmer_id)
        recent_orders = order_q.order_by(Order.id.desc()).limit(5).all()

        for o, l, b in recent_orders:
            buyer_name = b.name if b else f"Wholesale Buyer #{o.buyer_id}"
            o_time = o.committed_at or datetime.utcnow()
            events.append({
                "timestamp": o_time,
                "time": format_relative_time(o_time),
                "icon": "🤝",
                "bg": "bg-blue",
                "title": "Buyer Purchase Agreement",
                "desc": f"Purchase commitment registered by {buyer_name} for Lot #{l.id} ({l.crop_type})."
            })
    except Exception as e:
        print("Error fetching orders for activity:", e)

    # 4. Real Verified Marketplace Listings
    try:
        verif_q = db.query(Verification, Listing).join(Listing, Verification.listing_id == Listing.id)
        if farmer_id:
            verif_q = verif_q.filter(Listing.farmer_id == farmer_id)
        recent_verifs = verif_q.order_by(Verification.id.desc()).limit(5).all()

        for v, l in recent_verifs:
            v_time = v.verified_at or v.created_at or datetime.utcnow()
            events.append({
                "timestamp": v_time,
                "time": format_relative_time(v_time),
                "icon": "📋",
                "bg": "bg-green",
                "title": f"Marketplace Listing {v.status.title()}",
                "desc": f"Lot #{l.id} ({l.crop_type}) inspected by {v.agent_name or 'Field Agent'}: {v.remarks or 'Quality criteria verified'}."
            })
    except Exception as e:
        print("Error fetching verifications for activity:", e)

    # Sort descending by timestamp
    events.sort(key=lambda x: x["timestamp"] or datetime.min, reverse=True)

    # Trim to limit
    events = events[:limit]

    # Convert timestamps to ISO string
    for e in events:
        if isinstance(e["timestamp"], datetime):
            e["timestamp"] = e["timestamp"].isoformat()

    # Onboarding milestones for fresh account
    if len(events) == 0:
        events = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "time": "Just now",
                "icon": "🌱",
                "bg": "bg-green",
                "title": "Farm Profile Setup Complete",
                "desc": "Your AgriBridge account is active. Upload a leaf scan to initiate AI diagnosis."
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "time": "Live",
                "icon": "🌦️",
                "bg": "bg-gold",
                "title": "Agro-Weather Active",
                "desc": "15-day live weather tracking is enabled for your regional farm coordinates."
            }
        ]

    return {
        "success": True,
        "count": len(events),
        "activities": events
    }


# ==============================================================================
# FARMER NOTIFICATION DASHBOARD & CENTER
# ==============================================================================

@router.get("/notifications")
@router.get("/{farmer_id}/notifications")
def get_farmer_notifications(
    farmer_id: Optional[int] = None,
    filter_type: Optional[str] = Query(None, description="Filter by type: ALL, TREATMENTS, INSPECTIONS, WEATHER, ORDERS"),
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Returns all notifications for the farmer notification dashboard.
    Enriched with deep links, action metadata, and live inspection statuses.
    """
    q = db.query(NotificationEvent)
    if farmer_id:
        q = q.filter((NotificationEvent.farmer_id == farmer_id) | (NotificationEvent.farmer_id == None))

    # Order newest first
    all_notifs = q.order_by(NotificationEvent.id.desc()).limit(limit * 2).all()

    formatted = []
    unread_count = 0

    for n in all_notifs:
        n_type = getattr(n, "notification_type", None) or "SYSTEM"
        
        # Determine category / type filter matching
        if filter_type and filter_type.upper() != "ALL":
            ft = filter_type.upper()
            if ft == "TREATMENTS" and n_type not in ["TREATMENT_APPROVED", "TREATMENT"]:
                continue
            elif ft == "INSPECTIONS" and n_type not in ["INSPECTION_DISPATCHED", "INSPECTION", "NEEDS_PHYSICAL_VISIT"]:
                continue
            elif ft == "WEATHER" and n_type not in ["WEATHER_ALERT", "WEATHER"]:
                continue
            elif ft == "ORDERS" and n_type not in ["ORDER", "BUYER_ORDER", "LISTING_VERIFIED", "LISTING_REJECTED"]:
                continue

        is_unread = (n.status not in ["READ", "ACKNOWLEDGED", "COMPLETED"])
        if is_unread:
            unread_count += 1

        meta = {}
        if getattr(n, "meta_data", None):
            try:
                meta = json.loads(n.meta_data)
            except Exception:
                meta = {}

        # Enrich with live DiseaseRecord status if linked
        related_rec_id = getattr(n, "related_id", None)
        disease_scan = None
        if related_rec_id:
            try:
                d_rec = db.query(DiseaseRecord).filter(DiseaseRecord.id == related_rec_id).first()
                if d_rec:
                    disease_scan = {
                        "id": d_rec.id,
                        "crop_type": d_rec.crop_type,
                        "predicted_pathogen": d_rec.predicted_pathogen,
                        "status": d_rec.status,
                        "inspection_status": getattr(d_rec, "inspection_status", None),
                        "inspection_date": d_rec.inspection_date.isoformat() if getattr(d_rec, "inspection_date", None) else None,
                        "farmer_notes": getattr(d_rec, "farmer_notes", None),
                        "chemical": d_rec.prescription_chemical,
                        "dosage": d_rec.prescription_dosage,
                        "phi": d_rec.prescription_phi,
                        "agent_name": d_rec.agent_name,
                        "image_url": d_rec.image_url
                    }
                    if d_rec.inspection_status:
                        meta["inspection_status"] = d_rec.inspection_status
                    if d_rec.inspection_date:
                        meta["inspection_date"] = d_rec.inspection_date.isoformat()
                        meta["scheduled_date_formatted"] = d_rec.inspection_date.strftime("%d %b %Y at 10:00 AM")
            except Exception as e:
                print("Error loading linked disease record:", e)

        created_dt = n.created_at or datetime.utcnow()

        formatted.append({
            "id": n.id,
            "notification_id": n.notification_id,
            "action_plan_id": n.action_plan_id,
            "title": n.title,
            "message": n.message,
            "notification_type": n_type,
            "related_id": related_rec_id,
            "action_url": getattr(n, "action_url", None) or (f"/frontend/pages/ai-result.html?record_id={related_rec_id}" if n_type == "TREATMENT_APPROVED" else None),
            "meta_data": meta,
            "disease_scan": disease_scan,
            "status": n.status,
            "is_unread": is_unread,
            "priority": n.priority,
            "created_at": created_dt.isoformat(),
            "time_ago": format_relative_time(created_dt)
        })

    return {
        "success": True,
        "unread_count": unread_count,
        "total_count": len(formatted),
        "notifications": formatted[:limit]
    }


@router.post("/notifications/{notif_id}/read")
def mark_notification_read(
    notif_id: int,
    db: Session = Depends(get_db)
):
    notif = db.query(NotificationEvent).filter(NotificationEvent.id == notif_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.status = "READ"
    notif.acknowledged_at = datetime.utcnow()
    db.commit()
    return {"success": True, "message": "Notification marked as read"}


@router.post("/notifications/read-all")
def mark_all_notifications_read(
    farmer_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    q = db.query(NotificationEvent)
    if farmer_id:
        q = q.filter(NotificationEvent.farmer_id == farmer_id)
    q.filter(NotificationEvent.status != "READ").update({"status": "READ", "acknowledged_at": datetime.utcnow()})
    db.commit()
    return {"success": True, "message": "All notifications marked as read"}