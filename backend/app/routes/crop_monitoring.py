"""
AgriBridge Crop Monitoring & AI/ML Handoff Route
Exposes the All-India Crop Lifecycle, Open-Meteo Weather Context, Dynamic Calendar & Gemini Recommendation API.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..crop_monitoring.service import CropMonitoringService

router = APIRouter(
    prefix="/api/crop-monitoring",
    tags=["Crop Monitoring & AI/ML"]
)


# ============================================================
# REQUEST MODELS
# ============================================================

class LifecycleRequest(BaseModel):
    crop_id: str = Field(..., description="Crop identifier (e.g. wheat, rice, tomato)")
    planting_date: Optional[str] = Field(None, description="Planting / sowing date in YYYY-MM-DD")
    current_stage: Optional[str] = Field(None, description="Optional current growth stage")
    reference_date: Optional[str] = Field(None, description="Optional reference date (default: today)")


class WeatherContextRequest(BaseModel):
    state: Optional[str] = Field(None, description="Indian state name")
    district: Optional[str] = Field(None, description="Indian district name")
    village: Optional[str] = Field(None, description="Village name")
    latitude: Optional[float] = Field(None, description="Geographic latitude")
    longitude: Optional[float] = Field(None, description="Geographic longitude")


class CalendarEventsRequest(BaseModel):
    crop_id: str = Field(..., description="Crop identifier")
    planting_date: Optional[str] = Field(None, description="Planting date (YYYY-MM-DD)")
    farmer_id: Optional[str] = Field(None, description="Farmer identifier")
    state: Optional[str] = Field(None, description="State for weather context")
    district: Optional[str] = Field(None, description="District for weather context")


class FarmerNotificationsRequest(BaseModel):
    crop_id: str = Field(..., description="Crop identifier")
    planting_date: Optional[str] = Field(None, description="Planting date (YYYY-MM-DD)")
    current_stage: Optional[str] = Field(None, description="Current growth stage")
    farmer_id: Optional[str] = Field(None, description="Farmer identifier")
    state: Optional[str] = Field(None, description="State for weather context")
    district: Optional[str] = Field(None, description="District for weather context")


class MonitoringRecommendationRequest(BaseModel):
    state: str = Field(..., description="Indian state name")
    district: str = Field(..., description="Indian district name")
    village: Optional[str] = Field(None, description="Indian village name")
    crop_id: str = Field(..., description="One of 16 registered crops (e.g. wheat, tomato, rice)")
    planting_date: Optional[str] = Field(None, description="Planting date in YYYY-MM-DD")
    current_stage: Optional[str] = Field(None, description="Current stage (e.g. Sowing, CRI, Flowering)")
    latitude: Optional[float] = Field(None, description="Optional geographic latitude")
    longitude: Optional[float] = Field(None, description="Optional geographic longitude")
    farmer_id: Optional[str] = Field(None, description="Optional farmer identifier")


# ============================================================
# API ENDPOINTS
# ============================================================

@router.get("/health")
def monitoring_health():
    """Health check endpoint for the Crop Monitoring subsystem."""
    return {
        "success": True,
        "service": "AgriBridge AI/ML Crop Monitoring",
        "supported_crops_count": 16,
        "country": "India",
        "weather_provider": "Open-Meteo",
        "gemini_model": "gemini-3.6-flash",
        "disease_safety": "inspection_only"
    }


@router.get("/crops")
def list_supported_crops():
    """Returns all 16 registered Indian crops."""
    return CropMonitoringService.list_crops()


@router.get("/active-crops")
def get_active_crops_endpoint(farmer_id: Optional[str] = "FARMER_001"):
    """Returns active crops currently being grown by the farmer."""
    from ..routes.monitoring_v1 import get_active_crops_endpoint as v1_active
    return v1_active(farmer_id)


@router.post("/analyze")
async def analyze_crop_monitoring_endpoint(request: Request):
    """
    Direct Crop Monitoring Analyze Endpoint:
    Invokes the Ultra Crop Monitoring dynamic engine.
    """
    from ..routes.monitoring_v1 import analyze_crop_monitoring, MonitoringAnalyzeRequest
    try:
        body = await request.json()
    except Exception:
        body = {}
    req_obj = MonitoringAnalyzeRequest(**body)
    return await analyze_crop_monitoring(req_obj)


@router.get("/stages/{crop_name}")
def get_crop_stages_endpoint(crop_name: str):
    """Returns only the human-readable valid stage names for the specified crop."""
    from ..routes.monitoring_v1 import get_crop_stages_endpoint as v1_stages
    return v1_stages(crop_name)


@router.get("/calendar/{crop_id}")
def get_crop_calendar(crop_id: str):
    """Returns scientific and management calendars for a registered crop."""
    res = CropMonitoringService.get_crop_details(crop_id)
    if not res.get("success"):
        raise HTTPException(status_code=404, detail=res.get("error"))
    return res


@router.post("/lifecycle")
def calculate_lifecycle(payload: LifecycleRequest):
    """Calculates date-aware crop lifecycle position, DAP, current stage, and next stage."""
    return CropMonitoringService.compute_lifecycle(
        crop_id=payload.crop_id,
        planting_date=payload.planting_date,
        current_stage=payload.current_stage,
        reference_date=payload.reference_date
    )


@router.post("/weather-context")
async def get_weather_context(payload: WeatherContextRequest):
    """Retrieves Open-Meteo current weather and 7-day agricultural risk decision context."""
    return await CropMonitoringService.get_weather(
        state=payload.state,
        district=payload.district,
        village=payload.village,
        latitude=payload.latitude,
        longitude=payload.longitude
    )


@router.post("/events")
async def get_calendar_events(payload: CalendarEventsRequest):
    """Generates dynamic date-aware calendar events across the entire crop journey."""
    return await CropMonitoringService.get_events(
        crop_id=payload.crop_id,
        planting_date=payload.planting_date,
        farmer_id=payload.farmer_id,
        state=payload.state,
        district=payload.district
    )


@router.post("/notifications")
async def get_farmer_notifications(payload: FarmerNotificationsRequest):
    """Generates structured notification reminders for irrigation, fertilizer, and protection."""
    return await CropMonitoringService.get_notifications(
        crop_id=payload.crop_id,
        planting_date=payload.planting_date,
        current_stage=payload.current_stage,
        farmer_id=payload.farmer_id,
        state=payload.state,
        district=payload.district
    )


@router.post("/recommend")
async def get_crop_recommendation(
    payload: MonitoringRecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    Generates structured, validated Gemini crop monitoring recommendation based on
    farmer location, crop, lifecycle, live Open-Meteo weather, and management calendars.
    """
    return await CropMonitoringService.get_recommendation(
        state=payload.state,
        district=payload.district,
        village=payload.village,
        crop_id=payload.crop_id,
        planting_date=payload.planting_date,
        current_stage=payload.current_stage,
        latitude=payload.latitude,
        longitude=payload.longitude,
        farmer_id=payload.farmer_id,
        db_session=db
    )


@router.post("/orchestrate")
async def orchestrate_crop_monitoring(
    payload: MonitoringRecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    Unified Orchestration Endpoint:
    Combines AI/ML Lifecycle, Live Weather, Gemini Recommendation, Dynamic Calendars,
    Farmer Notifications, Escalation Evaluation, and Database Persistence into a single call.
    """
    from ..services.orchestration_service import OrchestrationService
    return await OrchestrationService.orchestrate_farm_plan(
        state=payload.state,
        district=payload.district,
        village=payload.village,
        crop_id=payload.crop_id,
        planting_date=payload.planting_date,
        current_stage=payload.current_stage,
        latitude=payload.latitude,
        longitude=payload.longitude,
        farmer_id=int(payload.farmer_id) if payload.farmer_id and payload.farmer_id.isdigit() else None,
        db=db
    )


@router.get("/guidance-package")
def get_farmer_guidance_package():
    """Returns the precomputed complete farmer guidance package."""
    return CropMonitoringService.get_guidance_package()


@router.get("/journey-context")
def get_all_india_journey_context():
    """Returns the multi-crop monitoring engine spec and full crop journey context."""
    return CropMonitoringService.get_journey_context()


