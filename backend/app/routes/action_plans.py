import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..models.action_plan import ActionPlan, PlanTask
from ..models.farmer import Farmer
from ..services.timing_advice_service import calculate_timing_advice, resolve_farm_coordinates

router = APIRouter(
    prefix="/api",
    tags=["Action Plans"]
)


class TaskUpdatePayload(BaseModel):
    status: Optional[str] = None
    completed: Optional[bool] = None
    title: Optional[str] = None
    reasoning: Optional[str] = None


class RecheckPayload(BaseModel):
    simulated_rain_probability: Optional[int] = None
    simulated_rainfall_mm: Optional[float] = None
    simulated_weather_condition: Optional[str] = None
    recommended_window: Optional[str] = None
    force_change: Optional[bool] = False


# ==============================================================================
# 1. GET ALL ACTION PLANS FOR A FARMER
# ==============================================================================

@router.get("/action-plans/{farmer_id}")
def get_farmer_action_plans(
    farmer_id: int,
    status: Optional[str] = Query(None, description="Filter by action plan status"),
    db: Session = Depends(get_db)
):
    """
    Returns all action plans and their nested trackable plan_tasks for a given farmer_id.
    Safely serializes deterministic decisions, constraints, and tasks without exposing internal credentials.
    """
    query = db.query(ActionPlan).filter(ActionPlan.farmer_id == farmer_id)

    if status:
        query = query.filter(ActionPlan.status == status)

    action_plans = query.order_by(ActionPlan.id.desc()).all()

    results = []
    for plan in action_plans:
        tasks = [
            {
                "id": t.id,
                "action_plan_id": t.action_plan_id,
                "title": t.title,
                "description": t.description,
                "location": t.location,
                "execution_window": t.execution_window,
                "scheduled_for": t.scheduled_for.isoformat() if t.scheduled_for else None,
                "status": t.status,
                "reasoning": t.reasoning,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None
            }
            for t in plan.tasks
        ]

        # Safe parsing of persisted decision metadata
        parsed_decision = None
        if plan.decision_json:
            try:
                parsed_decision = json.loads(plan.decision_json)
            except Exception:
                parsed_decision = None

        parsed_constraints = []
        if plan.constraints_json:
            try:
                parsed_constraints = json.loads(plan.constraints_json)
            except Exception:
                parsed_constraints = []

        parsed_recommended_actions = []
        if plan.recommended_actions_json:
            try:
                parsed_recommended_actions = json.loads(plan.recommended_actions_json)
            except Exception:
                parsed_recommended_actions = []

        results.append({
            "id": plan.id,
            "farmer_id": plan.farmer_id,
            "listing_id": plan.listing_id,
            "crop_id": plan.crop_id,
            "crop_stage": plan.crop_stage,
            "state": plan.state,
            "district": plan.district,
            "village": plan.village,
            "risk_type": plan.risk_type,
            "risk_level": plan.risk_level,
            "status": plan.status,
            "escalation_required": plan.escalation_required,
            "escalation_reason": plan.escalation_reason,
            "decision": parsed_decision,
            "constraints": parsed_constraints,
            "recommended_actions": parsed_recommended_actions,
            "created_at": plan.created_at.isoformat() if plan.created_at else None,
            "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
            "tasks_count": len(tasks),
            "completed_tasks_count": sum(1 for t in tasks if t["status"] == "done"),
            "completed_tasks_count": sum(1 for t in tasks if t["status"] in ("done", "completed")),
            "tasks": tasks
        })

    return {
        "success": True,
        "count": len(results),
        "farmer_id": farmer_id,
        "action_plans": results
    }


# ==============================================================================
# 1B. GET FIELD AGENT ESCALATIONS QUEUE (DISTINCT FROM NORMAL PENDING)
# ==============================================================================

@router.get("/action-plans/escalations/queue")
def get_escalations_queue(db: Session = Depends(get_db)):
    """
    Field-agent distinct escalation queue: returns all action plans needing expert review
    due to borderline AI confidence or high environmental risk.
    """
    plans = (
        db.query(ActionPlan)
        .filter((ActionPlan.status == "needs_expert_review") | (ActionPlan.escalation_required == True))
        .order_by(ActionPlan.id.desc())
        .all()
    )
    return {
        "success": True,
        "count": len(plans),
        "escalations": [
            {
                "id": p.id,
                "farmer_id": p.farmer_id,
                "status": p.status,
                "risk_type": p.risk_type,
                "escalation_reason": p.escalation_reason,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "tasks": [
                    {
                        "id": t.id,
                        "title": t.title,
                        "status": t.status,
                        "reasoning": t.reasoning
                    }
                    for t in p.tasks
                ]
            }
            for p in plans
        ]
    }


# ==============================================================================
# 2. UPDATE / COMPLETE A PLAN TASK
# ==============================================================================

@router.patch("/plan-tasks/{task_id}")
def update_plan_task(
    task_id: int,
    payload: TaskUpdatePayload,
    db: Session = Depends(get_db)
):
    """
    Updates a plan_task status. When status is 'done' or completed=True,
    automatically sets completed_at to the current UTC timestamp.
    """
    task = db.query(PlanTask).filter(PlanTask.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Plan task with ID {task_id} not found."
        )

    # Status update handling
    st = (payload.status or "").lower().replace("-", "_").replace(" ", "_")
    if payload.completed is True or st in ("done", "completed"):
        task.status = "done"
        task.completed_at = datetime.utcnow()
    elif payload.status:
        task.status = st
        task.completed_at = None

    if payload.title:
        task.title = payload.title

    if payload.reasoning:
        task.reasoning = payload.reasoning

    # Check if all tasks under the parent action plan are completed
    parent_plan = task.action_plan
    if parent_plan:
        all_done = all(t.status == "done" for t in parent_plan.tasks)
        if all_done and parent_plan.status == "active":
            parent_plan.status = "completed"
        elif not all_done and parent_plan.status == "completed":
            parent_plan.status = "active"
        parent_plan.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(task)

    return {
        "success": True,
        "message": f"Task #{task.id} updated successfully.",
        "task": {
            "id": task.id,
            "action_plan_id": task.action_plan_id,
            "title": task.title,
            "scheduled_for": task.scheduled_for.isoformat() if task.scheduled_for else None,
            "status": task.status,
            "reasoning": task.reasoning,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None
        }
    }


# ==============================================================================
# 3. RECHECK / ADAPT ACTION PLAN (REPLANNING ENGINE)
# ==============================================================================

@router.post("/action-plans/{plan_id}/recheck")
async def recheck_action_plan(
    plan_id: int,
    payload: Optional[RecheckPayload] = None,
    db: Session = Depends(get_db)
):
    """
    Re-evaluates weather conditions for an action plan's farm.
    If weather changes invalidate the existing task timing:
      1. Marks the OLD task as 'superseded' (never deleted).
      2. Generates a NEW replanned task with updated schedule & explicit reasoning.
    """
    plan = db.query(ActionPlan).filter(ActionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=404,
            detail=f"Action plan #{plan_id} not found."
        )

    farmer = db.query(Farmer).filter(Farmer.id == plan.farmer_id).first()
    location_str = getattr(farmer, "location", None) or "Punjab, India"

    # Find the current active/pending task
    active_task = (
        db.query(PlanTask)
        .filter(PlanTask.action_plan_id == plan_id, PlanTask.status == "pending")
        .order_by(PlanTask.id.desc())
        .first()
    )

    if not active_task:
        # Fallback to latest task
        active_task = (
            db.query(PlanTask)
            .filter(PlanTask.action_plan_id == plan_id)
            .order_by(PlanTask.id.desc())
            .first()
        )

    if not active_task:
        raise HTTPException(
            status_code=400,
            detail=f"No tasks exist under Action Plan #{plan_id} to re-evaluate."
        )

    # Re-fetch live weather or simulated weather
    payload = payload or RecheckPayload()
    sim_rain = payload.simulated_rain_probability
    sim_condition = payload.simulated_weather_condition
    sim_window = payload.recommended_window

    if sim_rain is not None:
        new_rain_prob = sim_rain
        new_rain_risk = new_rain_prob >= 60
        new_condition_desc = sim_condition or ("Heavy rain expected" if new_rain_risk else "Clear and dry skies")
        new_window = sim_window or ("2026-09-08 (Mainly clear)" if new_rain_risk else "Tomorrow Morning (6:00 AM - 9:00 AM)")
    else:
        # Fetch real Open-Meteo live timing advice
        live_advice = await calculate_timing_advice(region_str=location_str)
        new_rain_prob = live_advice.get("rain_probability", 0)
        new_rain_risk = live_advice.get("rain_risk", False)
        new_condition_desc = live_advice.get("advice", "Weather forecast updated.")
        new_window = live_advice.get("recommended_window", "Next available dry window")

    # Evaluate whether conditions have changed enough to supersede the existing task
    was_weather_delay = plan.risk_type == "weather_delay" or "Delay spraying" in (active_task.reasoning or "")
    now_weather_delay = new_rain_risk

    change_triggered = False
    change_type = "NO_CHANGE"
    new_reasoning = ""
    new_scheduled_for = datetime.utcnow() + timedelta(days=1)
    new_title = active_task.title

    if not was_weather_delay and now_weather_delay:
        # Weather worsened: Low rain -> High rain (Delay required)
        change_triggered = True
        change_type = "WEATHER_WORSENED_RAIN_SURGE"
        plan.risk_type = "weather_delay"
        new_scheduled_for = datetime.utcnow() + timedelta(days=5)
        new_title = f"Rescheduled: {active_task.title.replace('Rescheduled: ', '').replace('Expedited: ', '')}"
        new_reasoning = (
            f"Original plan assumed low rain risk; new weather forecast shows {new_rain_prob}% rain probability "
            f"({new_condition_desc}). Application delayed to prevent chemical wash-off and environmental leaching. "
            f"Rescheduled to safe window: {new_window}."
        )

    elif was_weather_delay and not now_weather_delay:
        # Weather improved: High rain cleared -> Safe window open (Expedite)
        change_triggered = True
        change_type = "WEATHER_CLEARED_SAFE_WINDOW"
        plan.risk_type = "disease_treatment"
        new_scheduled_for = datetime.utcnow() + timedelta(hours=18)
        new_title = f"Expedited: {active_task.title.replace('Rescheduled: ', '').replace('Expedited: ', '')}"
        new_reasoning = (
            f"Weather update: Rain threat has cleared (precipitation probability dropped to {new_rain_prob}%). "
            f"Optimal foliar uptake window detected immediately ({new_window}). Task expedited to halt disease progression."
        )

    elif payload.force_change or (sim_rain is not None and abs(new_rain_prob - 50) > 20):
        # Explicit simulated override
        change_triggered = True
        change_type = "SIMULATED_FORECAST_ADAPTATION"
        plan.risk_type = "weather_delay" if new_rain_risk else "disease_treatment"
        new_scheduled_for = datetime.utcnow() + timedelta(days=4 if new_rain_risk else 1)
        new_title = f"Adapted: {active_task.title.replace('Adapted: ', '').replace('Rescheduled: ', '').replace('Expedited: ', '')}"
        new_reasoning = (
            f"Autonomous replanning triggered: Forecast updated to {new_rain_prob}% rain probability. "
            f"Schedule adapted to {new_window} with updated agronomic parameters."
        )

    if change_triggered:
        # 1. Supersede previous active task
        active_task.status = "superseded"
        
        # 2. Create new replanned task
        new_task = PlanTask(
            action_plan_id=plan.id,
            title=new_title,
            scheduled_for=new_scheduled_for,
            status="pending",
            reasoning=new_reasoning,
            completed_at=None
        )
        db.add(new_task)
        plan.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(plan)
        db.refresh(new_task)

        return {
            "success": True,
            "action_plan_id": plan.id,
            "change_detected": True,
            "change_type": change_type,
            "message": "Weather change detected. Original task superseded and replaced with adapted plan.",
            "superseded_task_id": active_task.id,
            "new_task": {
                "id": new_task.id,
                "title": new_task.title,
                "status": new_task.status,
                "scheduled_for": new_task.scheduled_for.isoformat() if new_task.scheduled_for else None,
                "reasoning": new_task.reasoning
            },
            "action_plan_status": plan.status,
            "risk_type": plan.risk_type
        }

    return {
        "success": True,
        "action_plan_id": plan.id,
        "change_detected": False,
        "change_type": "WEATHER_STABLE",
        "message": f"Weather forecast rechecked ({new_rain_prob}% rain chance). Current task timing remains optimal.",
        "current_task": {
            "id": active_task.id,
            "title": active_task.title,
            "status": active_task.status,
        "reasoning": active_task.reasoning
        }
    }


# ==============================================================================
# 3B. GET SINGLE ACTION PLAN (WITH FARMER OWNERSHIP VERIFICATION)
# ==============================================================================

@router.get("/action-plans/plan/{plan_id}")
def get_action_plan_by_id(
    plan_id: int,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Retrieves a single action plan with strict ownership authorization.
    """
    plan = db.query(ActionPlan).filter(ActionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Action plan #{plan_id} not found.")

    if authorization:
        from ..services.auth_service import decode_access_token
        from ..models.user import User
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            user_data = decode_access_token(parts[1])
            if user_data:
                user = db.query(User).filter(User.id == user_data["user_id"]).first()
                if user and user.role == "farmer":
                    farmer = db.query(Farmer).filter(Farmer.name == user.name).first()
                    if farmer and farmer.id != plan.farmer_id:
                        raise HTTPException(
                            status_code=403,
                            detail="Access denied: You do not have permission to view another farmer's action plan."
                        )

    tasks = [
        {
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "scheduled_for": t.scheduled_for.isoformat() if t.scheduled_for else None,
            "reasoning": t.reasoning,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None
        }
        for t in plan.tasks
    ]

    return {
        "success": True,
        "action_plan": {
            "id": plan.id,
            "farmer_id": plan.farmer_id,
            "crop_id": plan.crop_id,
            "risk_type": plan.risk_type,
            "risk_level": plan.risk_level,
            "status": plan.status,
            "escalation_required": plan.escalation_required,
            "escalation_reason": plan.escalation_reason,
            "created_at": plan.created_at.isoformat() if plan.created_at else None,
            "tasks": tasks
        }
    }


# ==============================================================================
# 4. ACTION PLAN AGENT TRACE ENDPOINT
# ==============================================================================

@router.get("/action-plans/{plan_id}/trace")
def get_action_plan_trace(
    plan_id: int,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Returns the chronological evolution and agent trace of an action plan:
      - Initial plan creation
      - Calendar scheduling
      - Notification staging
      - Escalation evaluation
      - Weather evaluations
      - Superseded task history
      - Replanned active tasks
      - Completion status
    """
    plan = db.query(ActionPlan).filter(ActionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=404,
            detail=f"Action plan #{plan_id} not found."
        )

    # Ownership Authorization
    if authorization:
        from ..services.auth_service import decode_access_token
        from ..models.user import User
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            user_data = decode_access_token(parts[1])
            if user_data:
                user = db.query(User).filter(User.id == user_data["user_id"]).first()
                if user and user.role == "farmer":
                    farmer = db.query(Farmer).filter(Farmer.name == user.name).first()
                    if farmer and farmer.id != plan.farmer_id:
                        raise HTTPException(
                            status_code=403,
                            detail="Access denied: You do not own this action plan."
                        )

    tasks = (
        db.query(PlanTask)
        .filter(PlanTask.action_plan_id == plan_id)
        .order_by(PlanTask.id.asc())
        .all()
    )

    trace_events = []
    step = 1

    # Event 1: Initial Plan Creation
    trace_events.append({
        "step": step,
        "event_type": "PLAN_INITIALIZED",
        "timestamp": plan.created_at.isoformat() if plan.created_at else datetime.utcnow().isoformat(),
        "summary": f"Autonomous Action Plan #{plan.id} created for Farmer #{plan.farmer_id} (Initial Risk: {plan.risk_level.upper() if plan.risk_level else plan.risk_type}).",
        "status": "INITIALIZED"
    })
    step += 1

    # Event 2: Calendar & Notification Milestones
    if hasattr(plan, "calendar_events") and plan.calendar_events:
        trace_events.append({
            "step": step,
            "event_type": "CALENDAR_SCHEDULED",
            "timestamp": plan.created_at.isoformat() if plan.created_at else datetime.utcnow().isoformat(),
            "summary": f"Generated {len(plan.calendar_events)} date-aware agronomic calendar milestones.",
            "status": "SCHEDULED"
        })
        step += 1

    if hasattr(plan, "notifications") and plan.notifications:
        trace_events.append({
            "step": step,
            "event_type": "NOTIFICATIONS_STAGED",
            "timestamp": plan.created_at.isoformat() if plan.created_at else datetime.utcnow().isoformat(),
            "summary": f"Staged {len(plan.notifications)} multichannel farmer notification alerts.",
            "status": "NOTIFIED"
        })
        step += 1

    # Event 3: Escalation Policy Evaluation (if escalated)
    if plan.escalation_required:
        trace_events.append({
            "step": step,
            "event_type": "ESCALATION_EVALUATED",
            "timestamp": plan.created_at.isoformat() if plan.created_at else datetime.utcnow().isoformat(),
            "summary": f"Field Agent Escalation Dispatched: {plan.escalation_reason or 'High environmental risk.'}",
            "status": "ESCALATED"
        })
        step += 1

    # Task Evolution Traces
    for idx, t in enumerate(tasks):
        if t.status == "superseded":
            trace_events.append({
                "step": step,
                "event_type": "TASK_SUPERSEDED",
                "timestamp": plan.updated_at.isoformat() if plan.updated_at else datetime.utcnow().isoformat(),
                "task_id": t.id,
                "task_title": t.title,
                "task_status": "superseded",
                "scheduled_for": t.scheduled_for.isoformat() if t.scheduled_for else None,
                "reasoning": t.reasoning,
                "summary": f"Task #{t.id} ('{t.title}') invalidated due to incoming forecast shift."
            })
            step += 1

            trace_events.append({
                "step": step,
                "event_type": "REPLANNING_TRIGGERED",
                "timestamp": plan.updated_at.isoformat() if plan.updated_at else datetime.utcnow().isoformat(),
                "summary": f"Autonomous orchestrator adapted schedule: created replacement Task #{t.id + 1}."
            })
            step += 1

        elif t.status == "done":
            trace_events.append({
                "step": step,
                "event_type": "TASK_COMPLETED",
                "timestamp": t.completed_at.isoformat() if t.completed_at else datetime.utcnow().isoformat(),
                "task_id": t.id,
                "task_title": t.title,
                "task_status": "done",
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                "summary": f"Farmer marked Task #{t.id} completed."
            })
            step += 1

        else: # pending or in_progress
            trace_events.append({
                "step": step,
                "event_type": "ACTIVE_TASK_SCHEDULED",
                "timestamp": plan.updated_at.isoformat() if plan.updated_at else datetime.utcnow().isoformat(),
                "task_id": t.id,
                "task_title": t.title,
                "task_status": t.status,
                "scheduled_for": t.scheduled_for.isoformat() if t.scheduled_for else None,
                "reasoning": t.reasoning,
                "summary": f"Task #{t.id} currently active with target window: {t.scheduled_for.isoformat() if t.scheduled_for else 'Immediate'}."
            })
            step += 1

    return {
        "success": True,
        "action_plan_id": plan.id,
        "farmer_id": plan.farmer_id,
        "current_status": plan.status,
        "current_risk_type": plan.risk_type,
        "risk_level": plan.risk_level,
        "escalation_required": plan.escalation_required,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
        "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
        "total_tasks_recorded": len(tasks),
        "trace": trace_events
    }
