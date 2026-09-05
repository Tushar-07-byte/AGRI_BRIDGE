"""
AgriBridge AI/ML Crop Monitoring Package
Comprehensive All-India Crop Lifecycle, Open-Meteo Weather,
Dynamic Calendar & Gemini Recommendation System.
"""

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
from .safety_validator import validate_gemini_response, enforce_disease_safety_policy

__all__ = [
    "get_registered_crops",
    "is_crop_supported",
    "get_crop_metadata",
    "get_scientific_calendar",
    "get_management_calendar",
    "get_monitoring_activities",
    "SUPPORTED_CROPS_LIST",
    "calculate_crop_lifecycle",
    "get_monitoring_weather_context",
    "generate_calendar_events",
    "generate_farmer_notifications",
    "get_marketplace_context",
    "generate_crop_recommendation",
    "validate_gemini_response",
    "enforce_disease_safety_policy",
]

