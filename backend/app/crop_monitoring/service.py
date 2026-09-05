"""
AgriBridge Crop Monitoring Unified Service
High-level service orchestrating knowledge base, lifecycle engine,
Open-Meteo weather intelligence, dynamic calendar, notifications & Gemini recommendations.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).resolve().parent / "data"

def _load_data_json(filename: str) -> Dict[str, Any]:
    file_path = DATA_DIR / filename
    if not file_path.exists():
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {}

from .crop_registry import (
    get_registered_crops,
    is_crop_supported,
    get_crop_metadata,
    get_scientific_calendar,
    get_management_calendar,
    get_monitoring_activities,
    SUPPORTED_CROPS_LIST,
)
from .lifecycle_engine import calculate_crop_lifecycle
from .weather_context import get_monitoring_weather_context
from .calendar_engine import generate_calendar_events
from .notification_engine import generate_farmer_notifications
from .marketplace_context import get_marketplace_context
from .gemini_engine import generate_crop_recommendation


class CropMonitoringService:

    @staticmethod
    def list_crops() -> Dict[str, Any]:
        """Returns all 16 registered crops in the AgriBridge system."""
        return {
            "success": True,
            "count": len(SUPPORTED_CROPS_LIST),
            "country": "India",
            "crops": get_registered_crops()
        }

    @staticmethod
    def get_crop_details(crop_id: str) -> Dict[str, Any]:
        """Returns scientific and management calendar for a registered crop."""
        norm = crop_id.strip().lower()
        if not is_crop_supported(norm):
            return {
                "success": False,
                "error": f"Crop '{crop_id}' is not one of the 16 registered AgriBridge crops."
            }

        return {
            "success": True,
            "crop_id": norm,
            "metadata": get_crop_metadata(norm),
            "management_calendar": get_management_calendar(norm),
            "scientific_calendar": get_scientific_calendar(norm),
            "monitoring_activities": get_monitoring_activities(norm)
        }

    @staticmethod
    def compute_lifecycle(
        crop_id: str,
        planting_date: Optional[str] = None,
        current_stage: Optional[str] = None,
        reference_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Calculates date-aware crop lifecycle position and current stage."""
        norm = crop_id.strip().lower()
        res = calculate_crop_lifecycle(norm, planting_date, current_stage, reference_date)
        return {
            "success": True,
            "lifecycle": res
        }

    @staticmethod
    async def get_weather(
        state: Optional[str] = None,
        district: Optional[str] = None,
        village: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Retrieves Open-Meteo weather context with agricultural decision risks."""
        res = await get_monitoring_weather_context(state, district, village, latitude, longitude)
        return {
            "success": True,
            "weather_context": res
        }

    @staticmethod
    async def get_events(
        crop_id: str,
        planting_date: Optional[str] = None,
        farmer_id: Optional[str] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generates dynamic date-aware calendar events."""
        norm = crop_id.strip().lower()
        weather = None
        if state or district:
            weather = await get_monitoring_weather_context(state, district)

        events = generate_calendar_events(norm, planting_date, farmer_id, weather)
        return {
            "success": True,
            "crop_id": norm,
            "count": len(events),
            "events": events
        }

    @staticmethod
    async def get_notifications(
        crop_id: str,
        planting_date: Optional[str] = None,
        current_stage: Optional[str] = None,
        farmer_id: Optional[str] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generates structured farmer notification reminders."""
        norm = crop_id.strip().lower()
        weather = None
        if state or district:
            weather = await get_monitoring_weather_context(state, district)

        notifications = generate_farmer_notifications(
            crop_id=norm,
            planting_date=planting_date,
            current_stage=current_stage,
            farmer_id=farmer_id,
            weather_context=weather
        )
        return {
            "success": True,
            "crop_id": norm,
            "count": len(notifications),
            "notifications": notifications
        }

    @staticmethod
    async def get_recommendation(
        state: str,
        district: str,
        village: Optional[str] = None,
        crop_id: str = "wheat",
        planting_date: Optional[str] = None,
        current_stage: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        farmer_id: Optional[str] = None,
        db_session=None,
    ) -> Dict[str, Any]:
        """Full production Gemini recommendation generation with Open-Meteo & calendar context."""
        rec = await generate_crop_recommendation(
            state=state,
            district=district,
            village=village,
            crop_id=crop_id,
            planting_date=planting_date,
            current_stage=current_stage,
            latitude=latitude,
            longitude=longitude,
            farmer_id=farmer_id,
            db_session=db_session
        )
        return {
            "success": True,
            "recommendation": rec
        }

    @staticmethod
    def get_guidance_package() -> Dict[str, Any]:
        """Returns the precomputed complete production farmer guidance package."""
        pkg = _load_data_json("complete_farmer_guidance_package.json")
        if not pkg:
            pkg = _load_data_json("final_farmer_guidance.json")
        return {
            "success": True,
            "package": pkg
        }

    @staticmethod
    def get_journey_context() -> Dict[str, Any]:
        """Returns the All-India crop journey context and multi-crop monitoring engine specification."""
        journey = _load_data_json("final_all_india_crop_journey_context.json")
        engine = _load_data_json("multi_crop_monitoring_engine.json")
        profile = _load_data_json("active_farmer_crop_profile.json")
        return {
            "success": True,
            "engine": engine,
            "profile": profile,
            "journey_context": journey
        }

