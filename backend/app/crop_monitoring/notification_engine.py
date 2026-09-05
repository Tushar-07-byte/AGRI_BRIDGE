"""
AgriBridge Farmer Notification Event Generator
Generates structured notification reminders for irrigation, fertilizer, crop protection, and stage transitions.
"""

import datetime
from typing import Any, Dict, List, Optional
from .crop_registry import get_management_calendar
from .lifecycle_engine import calculate_crop_lifecycle


def generate_farmer_notifications(
    crop_id: str,
    planting_date: Optional[str] = None,
    current_stage: Optional[str] = None,
    farmer_id: Optional[str] = None,
    weather_context: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Generates structured, actionable notification events for farmers.
    """
    crop_norm = crop_id.strip().lower() if crop_id else "wheat"
    mgmt_calendar = get_management_calendar(crop_norm)
    crop_name = mgmt_calendar.get("crop_name", crop_norm.capitalize())

    lifecycle = calculate_crop_lifecycle(crop_norm, planting_date, current_stage)
    weather = weather_context or {}
    weather_decision = weather.get("decision", "Keep")

    notifications = []
    stages = mgmt_calendar.get("stages", [])

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    today_str = str(datetime.date.today())

    # 1. Current Active Stage Notification
    active_stage = lifecycle.get("current_stage", "Active Growth")
    act = lifecycle.get("current_activity", {})

    irrigation_text = act.get("irrigation", "Regular irrigation")
    fertilizer_text = act.get("fertilizer", "Balanced fertilization")
    protection_text = act.get("crop_protection", "Leaf scouting")

    primary_msg = (
        f"For your {crop_name} ({active_stage}): "
        f"Irrigation: {irrigation_text}. "
        f"Nutrients: {fertilizer_text}. "
        f"Scouting: {protection_text}. "
        f"Weather Advice: {weather_decision}."
    )

    notifications.append({
        "notification_id": f"NOTIFY_{crop_norm.upper()}_CURRENT",
        "farmer_id": farmer_id or "FARMER_DEFAULT",
        "date": today_str,
        "crop": crop_name,
        "stage": active_stage,
        "type": "stage_management_reminder",
        "title": f"🌱 {crop_name} {active_stage} Management Advisory",
        "message": primary_msg,
        "weather_decision": weather_decision,
        "calendar_status": "scheduled",
        "next_stage": lifecycle.get("next_stage"),
        "status": "pending",
        "created_at": now_iso
    })

    # 2. Weather Alert Notification (if risk is moderate or high)
    overall_risk = weather.get("risks", {}).get("overall_risk", "low")
    if overall_risk in ("moderate", "high"):
        notifications.append({
            "notification_id": f"NOTIFY_{crop_norm.upper()}_WEATHER",
            "farmer_id": farmer_id or "FARMER_DEFAULT",
            "date": today_str,
            "crop": crop_name,
            "stage": active_stage,
            "type": "weather_risk_alert",
            "title": f"🌦️ Weather Advisory for {crop_name} ({overall_risk.capitalize()} Risk)",
            "message": (
                f"{weather.get('weather_risk_summary', '')} "
                f"Recommendation: {weather.get('weather_decision_summary', '')}"
            ).strip(),
            "weather_decision": weather_decision,
            "calendar_status": "active_alert",
            "next_stage": lifecycle.get("next_stage"),
            "status": "pending",
            "created_at": now_iso
        })

    # 3. Scheduled Milestone Notifications (if planting date is available)
    if planting_date:
        try:
            p_date = datetime.date.fromisoformat(planting_date.strip())
            for idx, st in enumerate(stages, start=1):
                from .lifecycle_engine import _parse_day_range
                s_min, _ = _parse_day_range(st.get("day_range", ""))
                stage_date = p_date + datetime.timedelta(days=s_min)
                
                # Only include upcoming/future stages
                if stage_date >= datetime.date.today():
                    notifications.append({
                        "notification_id": f"NOTIFY_{crop_norm.upper()}_{idx:03d}",
                        "farmer_id": farmer_id or "FARMER_DEFAULT",
                        "date": str(stage_date),
                        "crop": crop_name,
                        "stage": st.get("stage"),
                        "type": "scheduled_activity_reminder",
                        "title": f"🗓️ Scheduled {crop_name} Activity: {st.get('stage')}",
                        "message": (
                            f"Scheduled activity on {stage_date} for {crop_name} ({st.get('stage')}): "
                            f"Irrigation: {st.get('irrigation')}, "
                            f"Fertilizer: {st.get('fertilizer')}, "
                            f"Protection: {st.get('crop_protection')}."
                        ),
                        "weather_decision": "Keep",
                        "calendar_status": "scheduled",
                        "next_stage": None,
                        "status": "pending",
                        "created_at": now_iso
                    })
        except Exception:
            pass

    return notifications

