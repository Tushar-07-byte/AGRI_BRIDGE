from datetime import datetime, timedelta
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..models.verification import Verification
from ..models.listing import Listing
from ..models.disease_record import DiseaseRecord
from ..models.action_plan import ActionPlan, PlanTask, NotificationEvent, FieldAgentEscalation


router = APIRouter(
    prefix="/api/verifications",
    tags=["Verifications"]
)


# ==============================================================================
# 1. DISEASE DETECTION VERIFICATION CONTROLLER (Human-in-the-Loop Plant Health)
#    Strictly decoupled from Marketplace. No listings created or updated.
# ==============================================================================

@router.get("/disease-scans/queue")
@router.get("/disease-scans")
def get_disease_scans(
    status: Optional[str] = Query(None, description="Filter by status, e.g. PENDING_AGENT_REVIEW, VERIFIED_HEALTH_RECORD, NEEDS_PHYSICAL_VISIT"),
    farmer_id: Optional[int] = Query(None, description="Filter by farmer_id"),
    db: Session = Depends(get_db)
):
    """
    Returns disease detection diagnostic records for Field Agent review.
    """
    query = db.query(DiseaseRecord)

    if status:
        query = query.filter(DiseaseRecord.status == status)
    if farmer_id:
        query = query.filter(DiseaseRecord.farmer_id == farmer_id)

    records = query.order_by(DiseaseRecord.id.desc()).all()

    return {
        "success": True,
        "count": len(records),
        "disease_scans": [
            {
                "id": r.id,
                "farmer_id": r.farmer_id,
                "crop_type": r.crop_type,
                "image_url": r.image_url,
                "confidence": r.confidence,
                "predicted_pathogen": r.predicted_pathogen,
                "scientific_name": r.scientific_name,
                "severity": r.severity,
                "status": r.status,
                "prescription_chemical": r.prescription_chemical,
                "prescription_dosage": r.prescription_dosage,
                "prescription_phi": r.prescription_phi,
                "prescription_organic": r.prescription_organic,
                "farm_area": r.farm_area,
                "growth_stage": r.growth_stage,
                "geolocation": r.geolocation,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "agent_name": r.agent_name,
                "agent_remarks": r.agent_remarks,
                "inspection_status": getattr(r, "inspection_status", None),
                "inspection_date": r.inspection_date.isoformat() if getattr(r, "inspection_date", None) else None,
                "farmer_notes": getattr(r, "farmer_notes", None),
                "action_plan_id": r.action_plan_id,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "verified_at": r.verified_at.isoformat() if r.verified_at else None
            }
            for r in records
        ]
    }


@router.get("/disease-scans/{record_id}")
def get_disease_scan_detail(
    record_id: int,
    db: Session = Depends(get_db)
):
    record = db.query(DiseaseRecord).filter(DiseaseRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Disease record not found")

    return {
        "success": True,
        "disease_scan": {
            "id": record.id,
            "farmer_id": record.farmer_id,
            "crop_type": record.crop_type,
            "image_url": record.image_url,
            "confidence": record.confidence,
            "predicted_pathogen": record.predicted_pathogen,
            "scientific_name": record.scientific_name,
            "severity": record.severity,
            "status": record.status,
            "prescription_chemical": record.prescription_chemical,
            "prescription_dosage": record.prescription_dosage,
            "prescription_phi": record.prescription_phi,
            "prescription_organic": record.prescription_organic,
            "farm_area": record.farm_area,
            "growth_stage": record.growth_stage,
            "geolocation": record.geolocation,
            "latitude": record.latitude,
            "longitude": record.longitude,
            "agent_name": record.agent_name,
            "agent_remarks": record.agent_remarks,
            "inspection_status": getattr(record, "inspection_status", None),
            "inspection_date": record.inspection_date.isoformat() if getattr(record, "inspection_date", None) else None,
            "farmer_notes": getattr(record, "farmer_notes", None),
            "action_plan_id": record.action_plan_id,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "verified_at": record.verified_at.isoformat() if record.verified_at else None
        }
    }


@router.post("/disease-scans/{record_id}/approve")
async def approve_disease_scan(
    record_id: int,
    payload: dict = {},
    db: Session = Depends(get_db)
):
    """
    Field Agent Action: APPROVE (status = APPROVED / VERIFIED_HEALTH_RECORD)
    1. Update disease record status to: VERIFIED_HEALTH_RECORD.
    2. Push notification to farmer with ICAR-compliant agronomic prescription and direct link to treatment output.
    3. Update farm active health log in the Crop Lifecycle Engine / ActionPlan.
    2. Rebuild canonical FarmDecisionContext with verified inputs.
    3. Evaluate via deterministic MultiSignalPolicyEngine (sole decision authority).
    4. If ALLOWED and weather safe -> create verified executable PlanTask & resolve escalation.
    5. If weather unsafe -> enforce weather timing deferral (DEFERRED).
    6. Push ICAR-compliant prescription notification to farmer.
    CRITICAL: Strictly zero marketplace interaction. No listing is created or published.
    """
    from ..services.farm_decision_context_service import FarmDecisionContextService
    from ..services.multi_signal_policy_engine import MultiSignalPolicyEngine
    from ..domain.multi_signal_decision import DecisionResult, DecisionType
    from ..services.field_agent_engine import _TASK_STORE

    record = db.query(DiseaseRecord).filter(DiseaseRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Disease record not found")

    agent_name = payload.get("agent_name", "Field Agent Rahul (Agri-Student)")
    remarks = payload.get("remarks", "Diagnosis verified by Field Agent. ICAR treatment prescription authorized.")

    # 1. Update disease record status
    record.status = "VERIFIED_HEALTH_RECORD"
    record.agent_name = agent_name
    record.agent_remarks = remarks
    record.verified_at = datetime.utcnow()

    # Allow custom prescription overrides from agronomist if supplied
    if payload.get("prescription_chemical"):
        record.prescription_chemical = payload["prescription_chemical"]
    if payload.get("prescription_dosage"):
        record.prescription_dosage = payload["prescription_dosage"]
    if payload.get("prescription_phi"):
        record.prescription_phi = payload["prescription_phi"]

    # 2. Push ICAR-compliant prescription notification to farmer
    chemical_name = record.prescription_chemical or "Mancozeb 75% WP"
    exact_dosage = record.prescription_dosage or "2.0 g / L water"
    phi_warning = record.prescription_phi or "7-10 Days Pre-Harvest Interval (PHI)"
    organic_opt = record.prescription_organic or "Cold-pressed Neem Oil @ 5ml/L"

    # 2. Push ICAR-compliant prescription notification to farmer
    notif_title = f"ICAR Prescription Verified: {record.crop_type.title()} — {record.predicted_pathogen}"
    notif_msg = (
        f"Your crop scan has been verified by {agent_name}. "
        f"Approved Agronomic Prescription: Apply {chemical_name} at {exact_dosage}. "
        f"Safety Warning: Strictly observe {phi_warning}. "
        f"Organic Alternative: {organic_opt}."
    )

    action_url = f"/frontend/pages/ai-result.html?record_id={record.id}"
    meta_payload = json.dumps({
        "type": "TREATMENT_APPROVED",
        "record_id": record.id,
        "crop_type": record.crop_type,
        "predicted_pathogen": record.predicted_pathogen,
        "chemical_name": chemical_name,
        "exact_dosage": exact_dosage,
        "pre_harvest_interval": phi_warning,
        "organic_alternative": organic_opt,
        "agent_name": agent_name,
        "action_url": action_url
    })

    farmer_notification = NotificationEvent(
        action_plan_id=record.action_plan_id,
        farmer_id=record.farmer_id,
        notification_id=f"NOTIF-RX-{record.id}",
        title=notif_title,
        message=notif_msg,
        notification_type="TREATMENT_APPROVED",
        related_id=record.id,
        action_url=action_url,
        meta_data=meta_payload,
        channel="sms_voice_app",
        priority="high",
        status="NOTIFIED",
        scheduled_at=datetime.utcnow(),
        delivered_at=datetime.utcnow()
    )
    db.add(farmer_notification)

    # 3. Update farm's active health log in Crop Lifecycle Engine / ActionPlan
    # 3. Closed-Loop Deterministic Policy Re-evaluation
    action_plan = None
    if record.action_plan_id:
        action_plan = db.query(ActionPlan).filter(ActionPlan.id == record.action_plan_id).first()

    weather_override_param = payload.get("weather_override")

    context = await FarmDecisionContextService.build_context(
        farmer_id=record.farmer_id,
        db=db,
        crop_id=record.crop_type,
        disease_record_id=record.id,
        weather_override=weather_override_param
    )

    # MultiSignalPolicyEngine is the SOLE deterministic decision authority
    decision = MultiSignalPolicyEngine.evaluate(context)

    is_weather_blocked = (
        "WEATHER_RAIN_BLOCK" in decision.constraints
        or "WEATHER_WIND_DRIFT_BLOCK" in decision.constraints
        or any(d.decision_type == DecisionType.WEATHER_TIMING and d.result == DecisionResult.DEFERRED for d in decision.decisions)
    )

    if action_plan:
        action_plan.decision_json = decision.json() if hasattr(decision, "json") else json.dumps(decision.dict() if hasattr(decision, "dict") else decision.__dict__)
        action_plan.constraints_json = json.dumps(decision.constraints)
        action_plan.recommended_actions_json = json.dumps(decision.recommended_actions)
        action_plan.escalation_required = False
        action_plan.updated_at = datetime.utcnow()

        if is_weather_blocked:
            action_plan.status = "deferred"
            action_plan.risk_type = "weather_delay"
            fav_win = (context.weather.favorable_window.value if context.weather and context.weather.favorable_window else None) or "Next dry window in 48-72h"

            # Reschedule or add deferred task
            existing_task = db.query(PlanTask).filter(PlanTask.action_plan_id == action_plan.id, PlanTask.status == "pending").first()
            if existing_task:
                existing_task.title = f"Rescheduled: Apply Verified Rx: {chemical_name} @ {exact_dosage}"
                existing_task.execution_window = fav_win
                existing_task.scheduled_for = datetime.utcnow() + timedelta(days=3)
                existing_task.reasoning = f"Field Agent Verified: {remarks}. Delayed due to weather constraints to prevent chemical wash-off."
            else:
                deferred_task = PlanTask(
                    action_plan_id=action_plan.id,
                    title=f"Rescheduled: Apply Verified Rx: {chemical_name} @ {exact_dosage}",
                    description=f"WHAT: Apply {chemical_name} at {exact_dosage}\nWHEN: {fav_win}\nWHERE: Field\nWHY: Verified ICAR Rx delayed for safe weather window.",
                    location=f"{action_plan.village or 'Farm'}, {action_plan.district or 'District'}",
                    execution_window=fav_win,
                    scheduled_for=datetime.utcnow() + timedelta(days=3),
                    status="pending",
                    reasoning=f"Field Agent Verified: {remarks}. Delayed due to weather constraints.",
                    completed_at=None
                )
                db.add(deferred_task)
        else:
            action_plan.status = "active_verified_rx"
            action_plan.risk_type = "verified_disease_treatment"
            action_plan.updated_at = datetime.utcnow()
            # Update associated plan tasks to reflect verified dosage
            for t in action_plan.tasks:
                if t.status == "pending":
                    t.title = f"Apply Verified Rx: {chemical_name} @ {exact_dosage}"
                    t.reasoning = f"Field Agent Verified: {remarks} (PHI: {phi_warning})"
            fav_win = (context.weather.favorable_window.value if context.weather and context.weather.favorable_window else None) or "Tomorrow Morning (6:00 AM - 9:00 AM)"

            # Resolve any associated FieldAgentEscalation
            pending_esc = db.query(FieldAgentEscalation).filter(
                FieldAgentEscalation.action_plan_id == action_plan.id,
                FieldAgentEscalation.status == "escalated"
            ).first()
            if pending_esc:
                pending_esc.status = "resolved"
            # If no active task exists (because under REQUIRES_HUMAN_REVIEW 0 tasks were created), create 1 executable PlanTask
            existing_task = db.query(PlanTask).filter(PlanTask.action_plan_id == action_plan.id, PlanTask.status == "pending").first()
            if existing_task:
                existing_task.title = f"Apply Verified Rx: {chemical_name} @ {exact_dosage}"
                existing_task.reasoning = f"Field Agent Verified: {remarks} (PHI: {phi_warning})"
                existing_task.execution_window = fav_win
            else:
                exec_task = PlanTask(
                    action_plan_id=action_plan.id,
                    title=f"Apply Verified Rx: {chemical_name} @ {exact_dosage}",
                    description=f"WHAT: Apply {chemical_name} at {exact_dosage}\nWHEN: {fav_win}\nWHERE: Field\nWHY: Verified ICAR Rx for {record.predicted_pathogen}. Observe {phi_warning}.",
                    location=f"{action_plan.village or 'Farm'}, {action_plan.district or 'District'}",
                    execution_window=fav_win,
                    scheduled_for=datetime.utcnow() + timedelta(hours=18),
                    status="pending",
                    reasoning=f"Field Agent Verified: {remarks} (PHI: {phi_warning})",
                    completed_at=None
                )
                db.add(exec_task)

        # Resolve any associated FieldAgentEscalation
        pending_esc = db.query(FieldAgentEscalation).filter(
            FieldAgentEscalation.action_plan_id == action_plan.id,
            FieldAgentEscalation.status.in_(["escalated", "assigned"])
        ).first()
        if pending_esc:
            pending_esc.status = "resolved"
            pending_esc.resolved_at = datetime.utcnow()

        # Synchronize in-memory task store
        for t_id, t_obj in _TASK_STORE.items():
            if t_obj.get("signal_details", {}).get("action_plan_id") == action_plan.id or t_obj.get("farmer_id") == str(record.farmer_id):
                t_obj["status"] = "VERIFIED"
                t_obj["chemical_recommendation_status"] = "AVAILABLE"
                t_obj["updated_at"] = datetime.utcnow().isoformat()

    db.commit()
    db.refresh(record)

    return {
        "success": True,
        "message": "Disease diagnosis verified and ICAR prescription issued.",
        "message": "Disease diagnosis verified and ICAR prescription evaluated via deterministic policy.",
        "status": record.status,
        "disease_record_id": record.id,
        "action_url": action_url,
        "prescription": {
            "chemical_name": chemical_name,
            "exact_dosage": exact_dosage,
            "pre_harvest_interval": phi_warning,
            "organic_alternative": organic_opt,
            "source": "ICAR-IIHR Agronomy Standard"
        },
        "deterministic_decision": decision.dict() if hasattr(decision, "dict") else decision.__dict__,
        "notification": {
            "title": notif_title,
            "message": notif_msg,
            "action_url": action_url,
            "status": "NOTIFIED"
        }
    }


@router.post("/disease-scans/{record_id}/reject")
def reject_disease_scan(
    record_id: int,
    payload: dict = {},
    db: Session = Depends(get_db)
):
    """
    Field Agent Action: REJECT (status = REJECTED / NEEDS_PHYSICAL_VISIT)
    1. Update disease record status to: NEEDS_PHYSICAL_VISIT / PENDING_FIELD_DISPATCH.
    2. Set inspection_status = SCHEDULED with default inspection date (Tomorrow).
    3. Move farmer's case into Field Agent's 'Pending Field Visits' section for an on-site audit.
    4. Push notification to farmer with interactive actions: Confirm, Reject, or Reschedule.
    CRITICAL: Strictly zero marketplace interaction.
    """
    record = db.query(DiseaseRecord).filter(DiseaseRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Disease record not found")

    agent_name = payload.get("agent_name", "Field Agent Rahul (Agri-Student)")
    reason = payload.get("reason", payload.get("remarks", "Complex symptom presentation requires in-person leaf inspection."))

    # Scheduled inspection date: defaults to tomorrow 10:00 AM local
    now = datetime.utcnow()
    scheduled_inspection_date = now + timedelta(days=1)
    scheduled_date_str = scheduled_inspection_date.strftime("%d %b %Y at 10:00 AM")

    # 1. Update disease record status to NEEDS_PHYSICAL_VISIT and set inspection schedule
    record.status = "NEEDS_PHYSICAL_VISIT"
    record.agent_name = agent_name
    record.agent_remarks = f"Rejected for auto-prescription: {reason}"
    record.inspection_status = "SCHEDULED"
    record.inspection_date = scheduled_inspection_date
    record.verified_at = now

    # 2. Move into Field Agent Pending Field Visits Queue (via FieldAgentEscalation)
    if record.action_plan_id:
        escalation = db.query(FieldAgentEscalation).filter(
            FieldAgentEscalation.action_plan_id == record.action_plan_id
        ).first()

        if not escalation:
            escalation = FieldAgentEscalation(
                action_plan_id=record.action_plan_id,
                farmer_id=record.farmer_id,
                risk_level="high",
                reason=f"On-site physical audit required: {reason}",
                status="assigned",
                created_at=now
            )
            db.add(escalation)
        else:
            escalation.status = "assigned"
            escalation.reason = f"On-site physical audit required: {reason}"

    # 3. Push notification to farmer with reschedule/reject options
    notif_title = f"🚨 On-Site Field Inspection Dispatched: {record.crop_type.title()}"
    notif_msg = (
        f"Field Agent {agent_name} rejected the automated diagnosis ({reason}) "
        f"and is scheduled to visit your farm on {scheduled_date_str} for physical inspection. "
        f"If you do not want an inspection on this date, you can reject the inspection or schedule for later."
    )

    action_url = "/frontend/pages/farmer-dashboard.html#notification-center"
    meta_payload = json.dumps({
        "type": "INSPECTION_DISPATCHED",
        "record_id": record.id,
        "crop_type": record.crop_type,
        "predicted_pathogen": record.predicted_pathogen,
        "agent_name": agent_name,
        "reason": reason,
        "inspection_status": "SCHEDULED",
        "inspection_date": scheduled_inspection_date.isoformat(),
        "scheduled_date_formatted": scheduled_date_str,
        "action_url": action_url
    })

    farmer_notification = NotificationEvent(
        action_plan_id=record.action_plan_id,
        farmer_id=record.farmer_id,
        notification_id=f"NOTIF-VISIT-{record.id}",
        title=notif_title,
        message=notif_msg,
        notification_type="INSPECTION_DISPATCHED",
        related_id=record.id,
        action_url=action_url,
        meta_data=meta_payload,
        channel="sms_voice_app",
        priority="high",
        status="NOTIFIED",
        scheduled_at=now,
        delivered_at=now
    )
    db.add(farmer_notification)

    db.commit()
    db.refresh(record)

    return {
        "success": True,
        "message": "On-site physical visit dispatched. Case moved to Pending Field Visits.",
        "status": record.status,
        "disease_record_id": record.id,
        "dispatch_status": "PENDING_FIELD_DISPATCH",
        "inspection_status": record.inspection_status,
        "inspection_date": record.inspection_date.isoformat() if record.inspection_date else None,
        "notification": {
            "title": notif_title,
            "message": notif_msg,
            "action_url": action_url,
            "status": "NOTIFIED"
        }
    }


@router.post("/disease-scans/{record_id}/inspection-response")
def farmer_inspection_response(
    record_id: int,
    payload: dict,
    db: Session = Depends(get_db)
):
    """
    Farmer Action on Field Inspection:
    - action: "CONFIRM" (Farmer accepts scheduled visit date)
    - action: "REJECT" (Farmer declines / rejects the in-person field inspection)
    - action: "RESCHEDULE" (Farmer picks a new convenient inspection date/time)
    """
    record = db.query(DiseaseRecord).filter(DiseaseRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Disease record not found")

    action = str(payload.get("action", "")).upper()
    notes = payload.get("notes", "")
    reschedule_date_str = payload.get("reschedule_date")

    now = datetime.utcnow()

    if action == "CONFIRM":
        record.inspection_status = "CONFIRMED"
        record.farmer_notes = notes or "Confirmed by farmer."
        msg = f"Inspection confirmed for {record.inspection_date.strftime('%d %b %Y') if record.inspection_date else 'scheduled date'}."
        
        # Acknowledge notification
        notif = NotificationEvent(
            action_plan_id=record.action_plan_id,
            farmer_id=record.farmer_id,
            notification_id=f"NOTIF-RESP-{record.id}-{int(now.timestamp())}",
            title="Inspection Confirmed",
            message=f"You confirmed the field inspection visit for {record.crop_type.title()}.",
            notification_type="SYSTEM",
            related_id=record.id,
            channel="sms_voice_app",
            priority="medium",
            status="NOTIFIED",
            scheduled_at=now,
            delivered_at=now
        )
        db.add(notif)

    elif action == "REJECT":
        record.inspection_status = "REJECTED"
        record.farmer_notes = notes or "Farmer declined in-person field inspection."
        msg = "Field inspection has been cancelled as per your request."

        # Update escalation status
        if record.action_plan_id:
            esc = db.query(FieldAgentEscalation).filter(
                FieldAgentEscalation.action_plan_id == record.action_plan_id
            ).first()
            if esc:
                esc.status = "declined_by_farmer"
                esc.reason += " [Farmer declined inspection]"

        notif = NotificationEvent(
            action_plan_id=record.action_plan_id,
            farmer_id=record.farmer_id,
            notification_id=f"NOTIF-RESP-{record.id}-{int(now.timestamp())}",
            title="Inspection Declined",
            message=f"You declined the physical inspection for {record.crop_type.title()}.",
            notification_type="SYSTEM",
            related_id=record.id,
            channel="sms_voice_app",
            priority="medium",
            status="NOTIFIED",
            scheduled_at=now,
            delivered_at=now
        )
        db.add(notif)

    elif action == "RESCHEDULE":
        if not reschedule_date_str:
            raise HTTPException(status_code=400, detail="reschedule_date is required when action is RESCHEDULE")
        
        try:
            # Handle YYYY-MM-DD or ISO string
            if "T" in reschedule_date_str:
                new_dt = datetime.fromisoformat(reschedule_date_str.replace("Z", "+00:00"))
            else:
                new_dt = datetime.strptime(reschedule_date_str[:10], "%Y-%m-%d")
        except Exception:
            new_dt = now + timedelta(days=3)

        record.inspection_status = "RESCHEDULED"
        record.inspection_date = new_dt
        record.farmer_notes = notes or f"Rescheduled by farmer to {new_dt.strftime('%d %b %Y')}."
        formatted_date = new_dt.strftime("%d %b %Y")
        msg = f"Field inspection successfully rescheduled to {formatted_date}."

        notif = NotificationEvent(
            action_plan_id=record.action_plan_id,
            farmer_id=record.farmer_id,
            notification_id=f"NOTIF-RESP-{record.id}-{int(now.timestamp())}",
            title="Inspection Rescheduled",
            message=f"Field inspection for {record.crop_type.title()} rescheduled to {formatted_date}.",
            notification_type="SYSTEM",
            related_id=record.id,
            channel="sms_voice_app",
            priority="medium",
            status="NOTIFIED",
            scheduled_at=now,
            delivered_at=now
        )
        db.add(notif)

    else:
        raise HTTPException(status_code=400, detail="Invalid action. Must be CONFIRM, REJECT, or RESCHEDULE.")

    db.commit()
    db.refresh(record)

    return {
        "success": True,
        "message": msg,
        "action": action,
        "disease_record_id": record.id,
        "inspection_status": record.inspection_status,
        "inspection_date": record.inspection_date.isoformat() if record.inspection_date else None,
        "farmer_notes": record.farmer_notes
    }



@router.put("/disease-scans/{record_id}")
def update_disease_scan_status(
    record_id: int,
    payload: dict,
    db: Session = Depends(get_db)
):
    """
    Unified endpoint for disease scan verification decisions.
    Accepts status: APPROVED / VERIFIED / REJECTED.
    """
    decision = str(payload.get("status", "")).upper()
    if decision in ["APPROVED", "VERIFIED", "VERIFIED_HEALTH_RECORD"]:
        return approve_disease_scan(record_id, payload, db)
    elif decision in ["REJECTED", "NEEDS_PHYSICAL_VISIT", "PENDING_FIELD_DISPATCH"]:
        return reject_disease_scan(record_id, payload, db)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid decision status: {decision}. Expected APPROVED or REJECTED."
        )


# ==============================================================================
# 2. HARVEST LISTING VERIFICATIONS (Strictly for Pre-Harvest Marketplace)
# ==============================================================================

@router.get("/")
def get_verifications(
    db: Session = Depends(get_db)
):
    verifications = db.query(Verification).all()

    return {
        "success": True,
        "count": len(verifications),
        "verifications": [
            {
                "id": verification.id,
                "listing_id": verification.listing_id,
                "agent_name": verification.agent_name,
                "status": verification.status,
                "remarks": verification.remarks,
                "verified_at": verification.verified_at,
                "created_at": verification.created_at
            }
            for verification in verifications
        ]
    }


@router.post("/")
def create_verification(
    verification_data: dict,
    db: Session = Depends(get_db)
):
    listing_id = verification_data.get("listing_id")

    if not listing_id:
        raise HTTPException(
            status_code=400,
            detail="listing_id is required"
        )

    listing = db.query(Listing).filter(
        Listing.id == listing_id
    ).first()

    if not listing:
        raise HTTPException(
            status_code=404,
            detail="Listing not found"
        )

    existing = db.query(Verification).filter(
        Verification.listing_id == listing_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Verification already exists for this listing"
        )

    verification = Verification(
        listing_id=listing_id,
        agent_name="Agent Rahul",
        status="pending",
        remarks="Crop submitted for field verification.",
        created_at=datetime.utcnow()
    )

    db.add(verification)
    db.commit()
    db.refresh(verification)

    return {
        "success": True,
        "verification_id": verification.id,
        "status": verification.status
    }


@router.get("/{verification_id}")
def get_verification(
    verification_id: int,
    db: Session = Depends(get_db)
):
    verification = db.query(Verification).filter(
        Verification.id == verification_id
    ).first()

    if not verification:
        raise HTTPException(
            status_code=404,
            detail="Verification not found"
        )

    return {
        "success": True,
        "verification": {
            "id": verification.id,
            "listing_id": verification.listing_id,
            "agent_name": verification.agent_name,
            "status": verification.status,
            "remarks": verification.remarks,
            "verified_at": verification.verified_at,
            "created_at": verification.created_at
        }
    }


@router.put("/{verification_id}")
def update_verification(
    verification_id: int,
    verification_data: dict,
    db: Session = Depends(get_db)
):
    verification = db.query(Verification).filter(
        Verification.id == verification_id
    ).first()

    if not verification:
        raise HTTPException(
            status_code=404,
            detail="Verification not found"
        )

    new_status = verification_data.get("status")

    if not new_status:
        raise HTTPException(
            status_code=400,
            detail="status is required"
        )

    new_status = new_status.lower()

    if new_status not in ["verified", "rejected"]:
        raise HTTPException(
            status_code=400,
            detail="status must be verified or rejected"
        )

    agent_name = verification_data.get("agent_name", "Agent Rahul")
    remarks = verification_data.get("remarks")

    verification.status = new_status
    verification.agent_name = agent_name
    verification.remarks = remarks
    verification.verified_at = datetime.utcnow()

    # Pre-Harvest Engine contract trigger: Only genuine harvest listings become available
    listing = db.query(Listing).filter(
        Listing.id == verification.listing_id
    ).first()

    if listing:
        if new_status == "verified":
            listing.status = "available"
            notif_title = f"Marketplace Listing Verified: {listing.crop_type.title()}"
            notif_msg = f"Your harvest listing #{listing.id} ({listing.crop_type}) has been verified by {agent_name} and is now live on the marketplace."
            action_url = "/frontend/pages/crop-listings.html"
            notif_type = "LISTING_VERIFIED"
        else:
            listing.status = "rejected"
            notif_title = f"Marketplace Listing Update: {listing.crop_type.title()}"
            notif_msg = f"Your harvest listing #{listing.id} ({listing.crop_type}) was reviewed by {agent_name}: {remarks or 'Listing criteria not met'}."
            action_url = "/frontend/pages/crop-listings.html"
            notif_type = "LISTING_REJECTED"

        farmer_notification = NotificationEvent(
            farmer_id=listing.farmer_id,
            notification_id=f"NOTIF-LISTING-{listing.id}-{int(datetime.utcnow().timestamp())}",
            title=notif_title,
            message=notif_msg,
            notification_type=notif_type,
            related_id=listing.id,
            action_url=action_url,
            meta_data=json.dumps({
                "type": notif_type,
                "listing_id": listing.id,
                "crop_type": listing.crop_type,
                "agent_name": agent_name,
                "remarks": remarks,
                "status": new_status,
                "action_url": action_url
            }),
            channel="sms_voice_app",
            priority="high" if new_status == "verified" else "medium",
            status="NOTIFIED",
            scheduled_at=datetime.utcnow(),
            delivered_at=datetime.utcnow()
        )
        db.add(farmer_notification)

    db.commit()
    db.refresh(verification)

    return {
        "success": True,
        "message": f"Verification updated to {new_status}",
        "verification_id": verification.id,
        "status": verification.status,
        "verification": {
            "id": verification.id,
            "listing_id": verification.listing_id,
            "agent_name": verification.agent_name,
            "status": verification.status,
            "remarks": verification.remarks,
            "verified_at": verification.verified_at.isoformat() if verification.verified_at else None,
            "created_at": verification.created_at.isoformat() if verification.created_at else None
        }
    }
