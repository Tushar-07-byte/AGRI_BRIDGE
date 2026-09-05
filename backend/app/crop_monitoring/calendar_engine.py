"""
AgriBridge Dynamic Calendar Engine
Generates date-aware agricultural activity calendar events derived from crop schedule & weather context.
"""

import datetime
from typing import Any, Dict, List, Optional
from .crop_registry import get_management_calendar
from .lifecycle_engine import _parse_day_range


def generate_calendar_events(
    crop_id: str,
    planting_date: Optional[str] = None,
    farmer_id: Optional[str] = None,
    weather_context: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Generates structured, date-aware calendar events across the entire crop journey.
    """
    crop_norm = crop_id.strip().lower() if crop_id else "wheat"
    mgmt_calendar = get_management_calendar(crop_norm)
    stages = mgmt_calendar.get("stages", [])

    p_date = datetime.date.today()
    if planting_date and planting_date.strip():
        try:
            p_date = datetime.date.fromisoformat(planting_date.strip())
        except Exception:
            p_date = datetime.date.today()

    weather_decision = (weather_context or {}).get("decision", "Keep")
    weather_reasons = (weather_context or {}).get("decision_reasons", ["Activity is scheduled as per scientific calendar"])

    events = []
    for idx, st in enumerate(stages, start=1):
        s_min, s_max = _parse_day_range(st.get("day_range", "Day 0"))
        
        # Calculate target calendar date for this stage
        stage_date = p_date + datetime.timedelta(days=s_min)
        event_id = f"{crop_norm.upper()}_EVENT_{idx:03d}"

        # Weather sensitivity evaluation: sprays and heavy irrigation are weather-sensitive
        is_weather_sensitive = bool(
            st.get("crop_protection") and "none" not in st.get("crop_protection", "").lower()
            or (st.get("irrigation") and "paani" in st.get("irrigation", "").lower())
        )

        event = {
            "event_id": event_id,
            "farmer_id": farmer_id or "FARMER_DEFAULT",
            "country": "India",
            "crop_id": crop_norm,
            "crop_name": mgmt_calendar.get("crop_name", crop_norm.capitalize()),
            "crop_stage": st.get("stage", "Stage"),
            "activity": {
                "irrigation": st.get("irrigation", "Regular"),
                "fertilizer": st.get("fertilizer", "Standard"),
                "crop_protection": st.get("crop_protection", "Inspection only")
            },
            "original_schedule": {
                "start_day": s_min,
                "end_day": s_max,
                "recommended_date": str(stage_date)
            },
            "date": str(stage_date),
            "weather": {
                "decision": weather_decision if is_weather_sensitive else "Keep",
                "reasons": weather_reasons if is_weather_sensitive else ["Activity is not heavily weather-dependent"]
            },
            "dynamic_update": {
                "required": False,
                "previous_date": str(stage_date),
                "new_date": "",
                "updated": False
            },
            "calendar_status": "scheduled",
            "farmer_action_completed": False,
            "notification_sent": False,
            "source": "AgriBridge Scientific Calendar Engine",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        events.append(event)

    return events

