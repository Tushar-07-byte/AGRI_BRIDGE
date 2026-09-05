"""
AgriBridge Crop Registry & Scientific Calendar Repository
Authoritative registry for 16 supported Indian agricultural crops.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

KB_DIR = Path(__file__).resolve().parent / "knowledge_base"

# 16 Registered Crops Authoritative List
SUPPORTED_CROPS_LIST: List[str] = [
    "wheat", "rice", "apple", "blueberry", "cherry", "corn",
    "grape", "orange", "peach", "pepper", "potato", "raspberry",
    "soybean", "squash", "strawberry", "tomato"
]

def _load_json(filename: str) -> Dict[str, Any]:
    file_path = KB_DIR / filename
    if not file_path.exists():
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[AgriBridge Crop Registry] Warning loading {filename}: {e}")
        return {}

# In-memory cached registries
_CROP_REGISTRY: Dict[str, Any] = _load_json("crop_registry.json")
_SCIENTIFIC_CALENDARS: Dict[str, Any] = _load_json("scientific_crop_calendar.json").get("crop_calendars", {})
_ALL_SCIENTIFIC_REGISTRY: Dict[str, Any] = _load_json("all_crop_scientific_calendar_registry.json")
_MANAGEMENT_CALENDARS: Dict[str, Any] = _load_json("crop_management_calendar.json")
_MONITORING_ACTIVITIES: Dict[str, Any] = _load_json("monitoring_activities.json")
_CROP_KB: Dict[str, Any] = _load_json("crop_knowledge_base.json")


def get_registered_crops() -> Dict[str, Any]:
    """Returns the dictionary of all 16 registered crops."""
    if _CROP_REGISTRY:
        return _CROP_REGISTRY
    # Fallback to standard 16 crops dictionary
    return {
        crop: {
            "crop_id": crop,
            "crop_name": crop.capitalize(),
            "country": "India",
            "scientific_calendar": True,
            "management_calendar": True,
            "weather_aware": True,
            "monitoring_enabled": True
        }
        for crop in SUPPORTED_CROPS_LIST
    }


def is_crop_supported(crop_name_or_id: str) -> bool:
    """Check if crop is in the 16 registered Indian crops."""
    if not crop_name_or_id:
        return False
    norm = crop_name_or_id.strip().lower()
    return norm in SUPPORTED_CROPS_LIST or norm in _CROP_REGISTRY


def get_crop_metadata(crop_id: str) -> Dict[str, Any]:
    """Get metadata for a specific registered crop."""
    norm = crop_id.strip().lower()
    if norm in _CROP_REGISTRY:
        return _CROP_REGISTRY[norm]
    if is_crop_supported(norm):
        return {
            "crop_id": norm,
            "crop_name": norm.capitalize(),
            "country": "India",
            "scientific_calendar": True,
            "management_calendar": True,
            "weather_aware": True,
            "monitoring_enabled": True
        }
    return {}


def get_scientific_calendar(crop_id: str) -> Dict[str, Any]:
    """Get scientific crop calendar (stages, lifecycle) for a crop."""
    norm = crop_id.strip().lower()
    if norm in _SCIENTIFIC_CALENDARS:
        return _SCIENTIFIC_CALENDARS[norm]
    if norm in _ALL_SCIENTIFIC_REGISTRY:
        return _ALL_SCIENTIFIC_REGISTRY[norm]
    return {}


def get_management_calendar(crop_id: str) -> Dict[str, Any]:
    """Get management calendar (irrigation, fertilizer, protection) for a crop."""
    norm = crop_id.strip().lower()
    if norm in _MANAGEMENT_CALENDARS:
        return _MANAGEMENT_CALENDARS[norm]
    return {}


def get_monitoring_activities(crop_id: str) -> Dict[str, Any]:
    """Get specific monitoring activities for a crop."""
    norm = crop_id.strip().lower()
    if norm in _MONITORING_ACTIVITIES:
        return _MONITORING_ACTIVITIES[norm]
    return {}

