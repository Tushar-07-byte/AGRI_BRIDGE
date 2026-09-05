"""
AgriBridge Field Agent & Tracked Notification Routes
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any

from ..services.field_agent_engine import (
    get_field_agent_tasks,
    get_task_by_id,
    accept_field_agent_task,
    reject_field_agent_task,
    submit_field_verification,
    evaluate_sensor_telemetry,
    create_field_agent_task
)
from ..services.notification_delivery_service import (
    get_farmer_notifications,
    mark_notification_read,
    create_notification,
    retry_failed_notification
)

router = APIRouter(
    prefix="/api/field-agent",
    tags=["Field Agent"]
)


@router.get("/tasks")
def list_tasks(status: Optional[str] = Query(None, description="Filter by status (PENDING, ACCEPTED, REJECTED, etc.)")):
    """Lists field agent tasks with optional status filter."""
    tasks = get_field_agent_tasks(status=status)
    return {
        "success": True,
        "count": len(tasks),
        "tasks": tasks
    }


@router.get("/tasks/{task_id}")
def get_task(task_id: str):
    """Retrieves a specific field agent task by ID."""
    task = get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return {
        "success": True,
        "task": task
    }


@router.post("/tasks/{task_id}/accept")
def accept_task(task_id: str, payload: Dict[str, Any] = {}):
    """Field agent accepts an escalation task."""
    try:
        res = accept_field_agent_task(
            task_id=task_id,
            agent_id=payload.get("agent_id", "AGENT_007"),
            agent_name=payload.get("agent_name", "Rahul Verma"),
            notes=payload.get("notes", "")
        )
        return res
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.post("/tasks/{task_id}/reject")
def reject_task(task_id: str, payload: Dict[str, Any]):
    """Field agent rejects an escalation task. Requires mandatory rejection reason."""
    reason = payload.get("rejection_reason")
    if not reason or len(reason.strip()) < 3:
        raise HTTPException(status_code=400, detail="Rejection reason is mandatory.")

    try:
        res = reject_field_agent_task(
            task_id=task_id,
            rejection_reason=reason,
            agent_id=payload.get("agent_id", "AGENT_007"),
            agent_name=payload.get("agent_name", "Rahul Verma")
        )
        return res
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.post("/tasks/{task_id}/verify")
def submit_verification(task_id: str, payload: Dict[str, Any]):
    """Submits field visit report and formal verification result."""
    obs = payload.get("field_observation", "")
    disease_obs = payload.get("disease_observed", "UNCERTAIN")
    res_val = payload.get("verification_result", "INCONCLUSIVE")

    try:
        res = submit_field_verification(
            task_id=task_id,
            field_observation=obs,
            disease_observed=disease_obs,
            verification_result=res_val,
            pathogen_identified=payload.get("pathogen_identified"),
            notes=payload.get("notes", ""),
            agent_id=payload.get("agent_id", "AGENT_007"),
            evidence_photos=payload.get("evidence_photos")
        )
        return res
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.post("/evaluate-telemetry")
def evaluate_telemetry(payload: Dict[str, Any]):
    """Evaluates sensor telemetry for anomalies, missing data, or zero-value issues."""
    sensor_id = payload.get("sensor_id", "SN_01")
    sensor_type = payload.get("sensor_type", "soil_moisture")
    value = payload.get("value")
    crop = payload.get("crop", "Wheat")
    farm_id = payload.get("farm_id", "FARM_01")
    prev_val = payload.get("previous_value")

    eval_res = evaluate_sensor_telemetry(
        sensor_id=sensor_id,
        sensor_type=sensor_type,
        value=value,
        crop_name=crop,
        farm_id=farm_id,
        previous_value=prev_val
    )

    # Auto-escalate if anomaly detected
    if eval_res.get("anomaly_detected") and eval_res.get("field_agent_escalation"):
        task = create_field_agent_task(
            trigger_type=eval_res["escalation_reason"],
            reason=eval_res["interpretation"],
            payload=eval_res,
            priority=eval_res.get("priority", "HIGH"),
            farmer_id=payload.get("farmer_id", "FARMER_101"),
            crop=crop,
            location=payload.get("location", "Sector 4, Raipur Zone")
        )
        eval_res["generated_task_id"] = task["task_id"]

    return {
        "success": True,
        "data": eval_res
    }


# ==============================================================================
# NOTIFICATION TRACKING ROUTES
# ==============================================================================

notification_router = APIRouter(
    prefix="/api/notifications",
    tags=["Notifications"]
)


@notification_router.get("/farmer/{farmer_id}/tracked")
def get_tracked_notifications(farmer_id: str):
    """Returns farmer notifications with true delivery lifecycle status."""
    notifs = get_farmer_notifications(farmer_id=farmer_id)
    return {
        "success": True,
        "count": len(notifs),
        "notifications": notifs
    }


@notification_router.post("/{notification_id}/mark-read")
def mark_read(notification_id: str):
    """Transitions notification status to READ upon farmer viewing."""
    try:
        return {
            "success": True,
            "data": mark_notification_read(notification_id)
        }
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))

