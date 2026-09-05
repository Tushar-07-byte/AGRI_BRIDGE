"""
AgriBridge Master Orchestration API Router
Connects Frontend, Backend Persistence, AI/ML Intelligence, Notification Delivery,
Weather Re-check, and Escalation Routing.
"""

from typing import Any, Dict, List, Optional
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

class NotificationStatus(str, Enum):
    PENDING = "PENDING"
    NOTIFIED = "NOTIFIED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
    ESCALATED = "ESCALATED"

from ..database.connection import get_db
from ..models.user import User
from ..models.action_plan import ActionPlan, NotificationEvent, CalendarEvent, FieldAgentEscalation
from ..models.action_plan import ActionPlan, PlanTask, NotificationEvent, CalendarEvent, FieldAgentEscalation
from ..services.auth_service import get_current_user, decode_access_token
from ..services.orchestration_service import OrchestrationService

router = APIRouter(
    prefix="/api",
    tags=["Master Orchestration"]
)


class OrchestrateRequest(BaseModel):
    state: str = Field(..., description="Indian state name")
    district: str = Field(..., description="Indian district name")
    village: Optional[str] = Field("Dhanpatganj", description="Indian village name")
    crop: Optional[str] = Field(None, description="Crop name (e.g. Rice, Wheat, Tomato)")
    crop_id: Optional[str] = Field(None, description="Crop identifier (e.g. rice, wheat, tomato)")
    planting_date: Optional[str] = Field(None, description="Planting date in YYYY-MM-DD")
    crop_stage: Optional[str] = Field(None, description="Crop stage (e.g. Flowering, Tillering)")
    current_stage: Optional[str] = Field(None, description="Current stage alias")
    latitude: Optional[float] = Field(None, description="Geographic latitude")
    longitude: Optional[float] = Field(None, description="Geographic longitude")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Geographic latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Geographic longitude")
    farmer_id: Optional[int] = Field(None, description="Optional farmer identifier")
    # Demo overrides – not part of the core data model but enable deterministic demo scenarios
    soil_moisture_vwc: Optional[float] = Field(None, description="Demo override: soil moisture VWC %")
    rain_probability: Optional[int] = Field(None, description="Demo override: rain probability %")
    soil_moisture_vwc: Optional[float] = Field(None, ge=0, le=100, description="Demo override: soil moisture VWC %")
    rain_probability: Optional[int] = Field(None, ge=0, le=100, description="Demo override: rain probability %")


class NotificationStatusUpdate(BaseModel):
    status: str = Field(..., description="Target lifecycle state (PENDING, NOTIFIED, ACKNOWLEDGED, IN_PROGRESS, COMPLETED, SKIPPED, ESCALATED)")
    status: NotificationStatus = Field(..., description="Target lifecycle state (PENDING, NOTIFIED, ACKNOWLEDGED, IN_PROGRESS, COMPLETED, SKIPPED, ESCALATED)")


class RecheckRequest(BaseModel):
    simulated_rain_probability: Optional[int] = None
    simulated_weather_condition: Optional[str] = None
    recommended_window: Optional[str] = None
    force_change: Optional[bool] = False


class EvaluateRequest(BaseModel):
    farmer_id: Optional[int] = Field(None, description="Farmer identifier")
    crop: Optional[str] = Field("wheat", description="Crop name")
    state: Optional[str] = Field("Punjab", description="State")
    district: Optional[str] = Field("Ludhiana", description="District")
    village: Optional[str] = Field("Samrala", description="Village")
    planting_date: Optional[str] = Field(None, description="Planting date YYYY-MM-DD")
    current_stage: Optional[str] = Field(None, description="Growth stage")
    disease_name: Optional[str] = Field(None, description="Optional active disease name")
    confidence: Optional[float] = Field(None, description="Disease confidence score (0-100%)")
    confidence: Optional[float] = Field(None, ge=0, le=100, description="Disease confidence score (0-100%)")
    nitrogen: Optional[float] = Field(None, description="Soil nitrogen kg/ha")
    soil_moisture_vwc: Optional[float] = Field(None, description="Soil moisture % VWC")
    rain_probability: Optional[int] = Field(None, description="Rain probability %")
    wind_speed: Optional[float] = Field(None, description="Wind speed km/h")
    soil_moisture_vwc: Optional[float] = Field(None, ge=0, le=100, description="Soil moisture % VWC")
    rain_probability: Optional[int] = Field(None, ge=0, le=100, description="Rain probability %")
    wind_speed: Optional[float] = Field(None, ge=0, description="Wind speed km/h")



# ============================================================
# ORCHESTRATION ENDPOINTS
# ============================================================

@router.post("/orchestration/plan")
async def orchestrate_plan(
    payload: OrchestrateRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Unified Orchestration Endpoint:
    Receives farmer context, invokes AI/ML intelligence, applies strict escalation policy,
    and persists ActionPlan, Tasks, CalendarEvents, and Notifications in MySQL.
    """
    current_user = None
    if authorization:
        try:
            parts = authorization.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                user_payload = decode_access_token(parts[1])
                if user_payload and "user_id" in user_payload:
                    current_user = db.query(User).filter(User.id == user_payload["user_id"]).first()
        except Exception:
            current_user = None

    crop_key = payload.crop_id or payload.crop or "rice"
    stage_key = payload.crop_stage or payload.current_stage or "Flowering"

    result = await OrchestrationService.orchestrate_farm_plan(
        state=payload.state,
        district=payload.district,
        village=payload.village,
        crop_id=crop_key,
        planting_date=payload.planting_date,
        current_stage=stage_key,
        latitude=payload.latitude,
        longitude=payload.longitude,
        farmer_id=payload.farmer_id,
        current_user=current_user,
        db=db,
        soil_moisture_vwc=payload.soil_moisture_vwc,
        rain_probability=payload.rain_probability,
    )
    return result


@router.get("/orchestration/context/{farmer_id}")
async def get_farmer_decision_context(
    farmer_id: int,
    crop: Optional[str] = None,
    state: Optional[str] = None,
    district: Optional[str] = None,
    village: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Read-only Farm Decision Context Inspection Endpoint.
    Exposes the canonical 20-signal FarmDecisionContext domain model in a judge-readable
    JSON structure with complete provenance, confidence standard, and quality ratings.
    Strictly zero passwords, API keys, or JWT secrets exposed.
    """
    from ..services.farm_decision_context_service import FarmDecisionContextService
    context = await FarmDecisionContextService.build_context(
        farmer_id=farmer_id,
        db=db,
        crop_id=crop,
        state=state,
        district=district,
        village=village
    )
    return {
        "success": True,
        "context": context.dict()
    }


@router.post("/orchestration/evaluate")
async def evaluate_multi_signal_policy(
    payload: Optional[EvaluateRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Phase 3 Multi-Signal Policy Evaluation Inspection Endpoint.
    Consumes farm signals, applies the deterministic MultiSignalPolicyEngine,
    and returns structured decision findings, constraints, and audit trace.
    Purely deterministic evaluation; performs zero writes and zero external network calls.
    """
    payload = payload or EvaluateRequest()
    from ..services.farm_decision_context_service import FarmDecisionContextService
    from ..services.multi_signal_policy_engine import MultiSignalPolicyEngine
    from ..domain.farm_decision_context import SignalProvenance, SignalQuality

    # 1. Build or retrieve canonical FarmDecisionContext
    context = await FarmDecisionContextService.build_context(
        farmer_id=payload.farmer_id or 1,
        db=db,
        crop_id=payload.crop or "wheat",
        state=payload.state or "Punjab",
        district=payload.district or "Ludhiana",
        village=payload.village or "Samrala",
        planting_date=payload.planting_date,
        current_stage=payload.current_stage or "Tillering",
        nitrogen=payload.nitrogen
    )

    # 2. Apply optional overrides for demo scenario simulation
    if payload.disease_name or payload.confidence is not None:
        context.disease.has_diagnosis = True
        if payload.disease_name:
            context.disease.pathogen_name.value = payload.disease_name
        if payload.confidence is not None:
            context.disease.confidence_percent.value = payload.confidence
            context.disease.confidence_fraction.value = round(payload.confidence / 100.0, 4)
            is_borderline = (payload.confidence >= 30.0 and payload.confidence < 65.0)
            context.disease.is_borderline = is_borderline
            context.disease.needs_expert_review = is_borderline
            context.disease.prescription_locked = is_borderline

    if payload.soil_moisture_vwc is not None:
        context.telemetry.soil_moisture_vwc.value = payload.soil_moisture_vwc
        context.telemetry.soil_moisture_vwc.provenance = SignalProvenance.SIMULATED
        context.telemetry.soil_moisture_vwc.quality = SignalQuality.SIMULATED

    if payload.rain_probability is not None:
        context.weather.rain_probability_percent.value = payload.rain_probability

    if payload.wind_speed is not None:
        context.weather.wind_speed_kmh.value = payload.wind_speed

    # 3. Deterministic Policy Evaluation
    decision = MultiSignalPolicyEngine.evaluate(context)

    return {
        "success": True,
        "context_id": context.context_id,
        "decision_id": decision.decision_id,
        "overall_risk": decision.overall_risk,
        "priority": decision.priority,
        "escalation_required": decision.escalation_required,
        "escalation_reason": decision.escalation_reason,
        "constraints": decision.constraints,
        "blocked_actions": decision.blocked_actions,
        "recommended_actions": decision.recommended_actions,
        "signals_considered": decision.signals_considered,
        "decisions": [d.dict() for d in decision.decisions],
        "decision_trace": [t.dict() for t in decision.decision_trace],
        "provenance_summary": decision.provenance_summary,
        "generated_at": decision.generated_at
    }


@router.post("/orchestration/recheck/{plan_id}")
async def orchestrate_recheck(
    plan_id: int,
    payload: Optional[RecheckRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Weather Re-check & Autonomous Rescheduling Endpoint.
    """
    payload = payload or RecheckRequest()
    result = await OrchestrationService.recheck_weather_and_reschedule(
        plan_id=plan_id,
        simulated_rain=payload.simulated_rain_probability,
        simulated_condition=payload.simulated_weather_condition,
        recommended_window=payload.recommended_window,
        force_change=payload.force_change,
        db=db
    )
    return result

@router.patch("/orchestration/tasks/{task_id}/status")
async def update_task_status_endpoint(
    task_id: int,
    payload: NotificationStatusUpdate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Update PlanTask lifecycle status.

    Validates transition using OrchestrationService.update_task_status.
    If the new status is COMPLETED, triggers a weather re‑check and possible rescheduling.
    Returns combined result.
    """
    # Update task status
    update_result = OrchestrationService.update_task_status(task_id, payload.status.value, db)
    if not update_result.get("success"):
        raise HTTPException(status_code=400, detail=update_result.get("error"))

    response = {"task_update": update_result}

    # If task completed, perform re‑check
    if payload.status == NotificationStatus.COMPLETED:
        # Retrieve the task to get its action_plan_id
        task = db.query(PlanTask).filter(PlanTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail=f"PlanTask #{task_id} not found for recheck.")
        recheck_result = await OrchestrationService.recheck_weather_and_reschedule(
            plan_id=task.action_plan_id,
            db=db
        )
        response["recheck"] = recheck_result

    return response


# ============================================================
# NOTIFICATION LIFECYCLE MANAGEMENT
# ============================================================

@router.patch("/notifications/{notification_id}/status")
def update_notification_status(
    notification_id: int,
    payload: NotificationStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Updates notification status through:
    PENDING -> NOTIFIED -> ACKNOWLEDGED -> IN_PROGRESS -> COMPLETED (or SKIPPED / ESCALATED)
    """
    res = OrchestrationService.update_notification_lifecycle(
        notification_id=notification_id,
        status=payload.status,
        db=db
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res


@router.get("/notifications/{farmer_id}")
def get_farmer_notifications(
    farmer_id: int,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieves all notification records for a farmer.
    """
    q = db.query(NotificationEvent).filter(NotificationEvent.farmer_id == farmer_id)
    if status_filter:
        q = q.filter(NotificationEvent.status == status_filter.upper())
    items = q.order_by(NotificationEvent.id.desc()).all()

    return {
        "success": True,
        "count": len(items),
        "farmer_id": farmer_id,
        "notifications": [
            {
                "id": n.id,
                "notification_id": n.notification_id,
                "action_plan_id": n.action_plan_id,
                "title": n.title,
                "message": n.message,
                "channel": n.channel,
                "priority": n.priority,
                "status": n.status,
                "scheduled_at": n.scheduled_at.isoformat() if n.scheduled_at else None,
                "delivered_at": n.delivered_at.isoformat() if n.delivered_at else None,
                "acknowledged_at": n.acknowledged_at.isoformat() if n.acknowledged_at else None,
                "completed_at": n.completed_at.isoformat() if n.completed_at else None,
            }
            for n in items
        ]
    }

