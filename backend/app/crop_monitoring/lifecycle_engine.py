"""
AgriBridge Crop Lifecycle & Dynamic Stage Engine
Date-aware crop timeline calculator and lifecycle stage resolver.
"""

import re
import datetime
from typing import Any, Dict, List, Optional, Tuple

from .crop_registry import (
    get_management_calendar,
    get_scientific_calendar,
    is_crop_supported,
)


def _parse_day_range(day_range_str: str) -> Tuple[int, int]:
    """Parse strings like 'Day 0', 'Day 20-25', 'Day 80-85' into (start_day, end_day)."""
    if not day_range_str:
        return (0, 0)
    
    # Match numbers in string
    nums = [int(n) for n in re.findall(r"\d+", day_range_str)]
    if not nums:
        return (0, 0)
    if len(nums) == 1:
        return (nums[0], nums[0])
    return (nums[0], nums[1])


def calculate_crop_lifecycle(
    crop_id: str,
    planting_date: Optional[str] = None,
    current_stage: Optional[str] = None,
    reference_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Computes date-aware crop lifecycle position, days after planting,
    current stage, next stage, and scheduled activities.
    """
    crop_id_norm = crop_id.strip().lower() if crop_id else "unknown"
    mgmt_calendar = get_management_calendar(crop_id_norm)
    stages: List[Dict[str, Any]] = mgmt_calendar.get("stages", [])

    today = datetime.date.today()
    ref_date = today
    if reference_date:
        try:
            ref_date = datetime.date.fromisoformat(reference_date.strip())
        except Exception:
            ref_date = today

    # 1. If Planting Date is provided
    if planting_date and planting_date.strip():
        try:
            p_date = datetime.date.fromisoformat(planting_date.strip())
            dap = (ref_date - p_date).days
            if dap < 0:
                # Sowing scheduled in future
                return {
                    "crop_id": crop_id_norm,
                    "crop_name": mgmt_calendar.get("crop_name", crop_id.capitalize()),
                    "planting_date": str(p_date),
                    "reference_date": str(ref_date),
                    "days_after_planting": dap,
                    "date_status": "future_scheduled",
                    "current_stage": "Pre-Sowing / Field Preparation",
                    "stage_status": f"Scheduled in future (Sowing date: {p_date})",
                    "next_stage": stages[0].get("stage") if stages else "Sowing",
                    "current_activity": {
                        "irrigation": "Pre-sowing field preparation",
                        "fertilizer": "Soil testing and basal organic manure",
                        "crop_protection": "Seed treatment"
                    },
                    "all_stages": stages
                }

            # Find matching stage based on DAP
            matched_stage = None
            next_stage_name = None
            matched_index = -1

            for idx, st in enumerate(stages):
                s_min, s_max = _parse_day_range(st.get("day_range", ""))
                
                # Check next stage threshold if we're between stages
                next_min = 9999
                if idx + 1 < len(stages):
                    next_min, _ = _parse_day_range(stages[idx + 1].get("day_range", ""))

                if s_min <= dap < next_min:
                    matched_stage = st
                    matched_index = idx
                    if idx + 1 < len(stages):
                        next_st = stages[idx + 1]
                        next_stage_name = f"{next_st.get('stage')} ({next_st.get('day_range', '')}, as per management calendar)"
                    break

            if matched_stage is None and stages:
                # If DAP exceeds all listed stages -> Maturity / Harvest
                last_st = stages[-1]
                matched_stage = last_st
                matched_index = len(stages) - 1
                next_stage_name = "Maturity / Harvest / Post-Harvest Marketing"

            resolved_stage_name = matched_stage.get("stage", current_stage or "Active Growth") if matched_stage else (current_stage or "Active Growth")
            
            return {
                "crop_id": crop_id_norm,
                "crop_name": mgmt_calendar.get("crop_name", crop_id.capitalize()),
                "planting_date": str(p_date),
                "reference_date": str(ref_date),
                "days_after_planting": dap,
                "date_status": "available",
                "current_stage": resolved_stage_name,
                "stage_status": f"Active (Planting date: {p_date}, Days After Planting: {dap})",
                "next_stage": next_stage_name,
                "current_activity": {
                    "irrigation": matched_stage.get("irrigation", "Regular as per soil moisture") if matched_stage else "Regular",
                    "fertilizer": matched_stage.get("fertilizer", "As per schedule") if matched_stage else "Standard",
                    "crop_protection": matched_stage.get("crop_protection", "Inspect for pest/disease symptoms") if matched_stage else "Inspection only"
                },
                "stage_number": matched_index + 1 if matched_index >= 0 else None,
                "total_stages": len(stages),
                "all_stages": stages
            }

        except Exception as e:
            print(f"[Lifecycle Engine] Date parse error for {planting_date}: {e}")

    # 2. Fallback when planting_date is unavailable
    resolved_stage = current_stage.strip() if current_stage and current_stage.strip() else "Unspecified"
    next_stage_fallback = None

    if stages and resolved_stage != "Unspecified":
        for idx, st in enumerate(stages):
            if st.get("stage", "").lower() == resolved_stage.lower():
                if idx + 1 < len(stages):
                    next_st = stages[idx + 1]
                    next_stage_fallback = f"{next_st.get('stage')} ({next_st.get('day_range', '')}, as per management calendar)"
                break

    return {
        "crop_id": crop_id_norm,
        "crop_name": mgmt_calendar.get("crop_name", crop_id.capitalize()),
        "planting_date": None,
        "reference_date": str(ref_date),
        "days_after_planting": None,
        "date_status": "unavailable",
        "current_stage": resolved_stage,
        "stage_status": f"Stage: {resolved_stage} (Planting date not specified)",
        "next_stage": next_stage_fallback,
        "current_activity": {
            "irrigation": "Provide standard stage-specific irrigation",
            "fertilizer": "Maintain balanced nutrient supply",
            "crop_protection": "Routine leaf canopy visual inspection"
        },
        "all_stages": stages
    }

