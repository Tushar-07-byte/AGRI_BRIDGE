"""
AgriBridge AI — Ultra Crop Monitoring + IoT Telemetry API (v1)
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

API Endpoints:
- POST /api/v1/monitoring/analyze
- POST /api/v1/monitoring/notification/action
- GET  /api/v1/monitoring/crops
- GET  /api/v1/monitoring/health
"""

import os
import sys
import json
import httpx
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import date, datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

# Ensure the Ultra Crop Monitoring engine directory is in sys.path
ENGINE_DIR = Path(__file__).resolve().parent.parent / "AgriBridge_Ultra_Crop_Monitoring_FINAL" / "AgriBridge_Ultra_Crop_Monitoring_FINAL" / "Ultra_Crop_Monitoring_IoT_Telemetry" / "backend_handoff" / "engine"
if str(ENGINE_DIR) not in sys.path and ENGINE_DIR.exists():
    sys.path.insert(0, str(ENGINE_DIR))

try:
    from dynamic_monitoring_engine import run_monitoring, load_json
except ImportError:
    # Fallback import if directory structure is direct
    from ..AgriBridge_Ultra_Crop_Monitoring_FINAL.AgriBridge_Ultra_Crop_Monitoring_FINAL.Ultra_Crop_Monitoring_IoT_Telemetry.backend_handoff.engine.dynamic_monitoring_engine import run_monitoring, load_json

router = APIRouter(
    prefix="/api/v1/monitoring",
    tags=["Ultra Crop Monitoring (v1)"]
)


# ============================================================
# PYDANTIC SCHEMAS
# ============================================================

class LocationModel(BaseModel):
    state: Optional[str] = Field("Uttar Pradesh", description="Indian state name (e.g. Uttar Pradesh, Maharashtra)")
    district: Optional[str] = Field("Varanasi", description="Indian district name (e.g. Varanasi, Nashik)")
    village: Optional[str] = Field("Demo Village", description="Village or tehsil name")
    latitude: Optional[float] = Field(None, description="Geographic latitude for live Open-Meteo weather")
    longitude: Optional[float] = Field(None, description="Geographic longitude for live Open-Meteo weather")


class CropInputModel(BaseModel):
    crop_name: str = Field(..., description="Registered crop name (e.g. Wheat, Rice, Tomato, Potato, Corn, Soybean)")
    planting_date: Optional[str] = Field(None, description="Planting / sowing date in YYYY-MM-DD")
    crop_stage_mode: Optional[str] = Field("AUTO", description="'AUTO' (calculated from date) or 'MANUAL'")
    crop_stage: Optional[str] = Field(None, description="Manual stage name if mode is MANUAL")


class MarketplaceInputModel(BaseModel):
    crop_listed: Optional[bool] = Field(False, description="Whether the crop has already been listed in AgriBridge Marketplace")


class TelemetryInputModel(BaseModel):
    soil_moisture_percent: Optional[float] = Field(30.0, description="Soil moisture percentage (0-100%)")
    soil_temperature_c: Optional[float] = Field(23.0, description="Soil temperature in Celsius")
    air_temperature_c: Optional[float] = Field(25.0, description="Air temperature in Celsius")
    relative_humidity_percent: Optional[float] = Field(70.0, description="Relative humidity percentage (0-100%)")
    rainfall_mm: Optional[float] = Field(0.0, description="Recent rainfall in mm")
    leaf_wetness: Optional[bool] = Field(False, description="Leaf wetness sensor boolean flag")
    soil_ec_ds_m: Optional[float] = Field(0.9, description="Soil Electrical Conductivity (dS/m)")
    soil_ph: Optional[float] = Field(6.5, description="Soil pH level (4.0-9.0)")
    soil_nitrogen_mg_kg: Optional[float] = Field(None, description="Soil Nitrogen (mg/kg)")
    soil_phosphorus_mg_kg: Optional[float] = Field(None, description="Soil Phosphorus (mg/kg)")
    soil_potassium_mg_kg: Optional[float] = Field(None, description="Soil Potassium (mg/kg)")
    soil_organic_carbon_percent: Optional[float] = Field(None, description="Soil Organic Carbon (%)")
    light_hours: Optional[float] = Field(8.0, description="Daily sunlight hours")
    wind_speed_kmh: Optional[float] = Field(10.0, description="Wind speed in km/h")


class MonitoringAnalyzeRequest(BaseModel):
    farm_id: Optional[str] = Field("FARM_001", description="Unique farm identifier")
    field_id: Optional[str] = Field("FIELD_001", description="Unique field identifier")
    telemetry_id: Optional[str] = Field("TEL_001", description="Telemetry session identifier")
    location: Optional[LocationModel] = Field(default_factory=lambda: LocationModel(state="Uttar Pradesh", district="Varanasi"))
    crop: CropInputModel
    marketplace: Optional[MarketplaceInputModel] = None
    telemetry: Optional[TelemetryInputModel] = None


class NotificationActionRequest(BaseModel):
    notification_id: str = Field(..., description="Notification identifier to act upon")
    action: str = Field(..., description="Action: 'COMPLETE', 'POSTPONE', 'RESCHEDULE', 'CANCEL'")
    reason: Optional[str] = Field(None, description="Farmer notes or reason for action")
    new_date: Optional[str] = Field(None, description="New date if action is RESCHEDULE (YYYY-MM-DD)")


# In-memory notification state store for demo & persistence
NOTIFICATION_ACTION_STORE: Dict[str, Dict[str, Any]] = {}


# ============================================================
# LLM EXPLANATION HELPER (Gemini Explanation Layer)
# ============================================================

async def enrich_with_gemini_guidance(monitoring_result: Dict[str, Any]) -> str:
    """
    Calls Google Gemini for natural-language farmer explanation if API key is present.
    Gemini serves strictly as an explanation layer and does NOT override deterministic decisions.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        crop_name = monitoring_result.get("crop", {}).get("crop_name", "Crop")
        stage = monitoring_result.get("stage", {}).get("current_stage", "Current stage")
        irr = monitoring_result.get("decisions", {}).get("irrigation", {}).get("status", "SCHEDULED")
        dis = monitoring_result.get("decisions", {}).get("disease", {}).get("status", "LOW")
        return (
            f"Your {crop_name} is currently in the {stage} stage. "
            f"Irrigation is {irr} based on current soil moisture levels. "
            f"Disease risk is evaluated as {dis}. Follow scheduled field scouting activities."
        )

    try:
        crop_info = monitoring_result.get("crop", {})
        stage_info = monitoring_result.get("stage", {})
        weather_info = monitoring_result.get("weather", {})
        decisions_info = monitoring_result.get("decisions", {})

        prompt = (
            f"You are AgriBridge AI, an expert agronomist advisor speaking to an Indian farmer.\n"
            f"CROP: {crop_info.get('crop_name')} (Age: {stage_info.get('crop_age_days')} days)\n"
            f"STAGE: {stage_info.get('current_stage')}\n"
            f"WEATHER: Temp {weather_info.get('temperature_c')}°C, Humidity {weather_info.get('relative_humidity_percent')}%, Rain {weather_info.get('rainfall_mm')}mm\n"
            f"DECISIONS: Irrigation={decisions_info.get('irrigation', {}).get('status')}, Disease Risk={decisions_info.get('disease', {}).get('status')}, Pest Risk={decisions_info.get('pest', {}).get('status')}\n"
            f"Provide a warm, concise 2-3 sentence agricultural advisory summarizing key actions for today. Do not give chemical dosages."
        )

        api_url = (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models/gemini-1.5-flash:generateContent"
            f"?key={api_key}"
        )
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(api_url, json=payload, headers={"Content-Type": "application/json"})
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
    except Exception:
        pass

    crop_name = monitoring_result.get("crop", {}).get("crop_name", "Crop")
    stage = monitoring_result.get("stage", {}).get("current_stage", "Current stage")
    return f"Your {crop_name} is progressing well in {stage} stage. Continue following recommended irrigation and scouting routines."


# ============================================================
# API ENDPOINTS
# ============================================================

@router.get("/health")
def monitoring_health():
    """Health check endpoint for the Ultra Crop Monitoring subsystem."""
    return {
        "success": True,
        "service": "AgriBridge Ultra Crop Monitoring + IoT Telemetry",
        "version": "1.0",
        "weather_source": "LIVE_REAL",
        "iot_source": "SYNTHETIC_HACKATHON_DEMO",
        "physical_sensor_connected": False,
        "llm_provider": "Google Gemini",
        "llm_role": "Explanation layer only"
    }


@router.get("/crops")
def list_supported_crops():
    """Returns all registered crops supported by the Ultra Crop Monitoring engine."""
    try:
        crops = load_json("crop_master.json")
        return {
            "success": True,
            "count": len(crops),
            "crops": crops
        }
    except Exception:
        # Fallback list
        fallback = [
            {"crop": "Wheat", "total_duration_min": 120, "total_duration_max": 140},
            {"crop": "Rice", "total_duration_min": 130, "total_duration_max": 160},
            {"crop": "Corn", "total_duration_min": 90, "total_duration_max": 140},
            {"crop": "Potato", "total_duration_min": 100, "total_duration_max": 130},
            {"crop": "Soybean", "total_duration_min": 120, "total_duration_max": 150},
            {"crop": "Tomato", "total_duration_min": 120, "total_duration_max": 160},
            {"crop": "Pepper", "total_duration_min": 120, "total_duration_max": 150},
            {"crop": "Squash", "total_duration_min": 90, "total_duration_max": 120},
            {"crop": "Strawberry", "total_duration_min": 60, "total_duration_max": 90},
            {"crop": "Raspberry", "total_duration_min": 90, "total_duration_max": 120},
            {"crop": "Grape", "total_duration_min": 140, "total_duration_max": 170},
            {"crop": "Apple", "total_duration_min": 160, "total_duration_max": 180},
            {"crop": "Peach", "total_duration_min": 120, "total_duration_max": 150},
            {"crop": "Cherry", "total_duration_min": 80, "total_duration_max": 90},
            {"crop": "Blueberry", "total_duration_min": 100, "total_duration_max": 130},
            {"crop": "Orange", "total_duration_min": 300, "total_duration_max": 360}
        ]
        return {
            "success": True,
            "count": len(fallback),
            "crops": fallback
        }


@router.get("/stages/{crop_name}")
def get_crop_stages_endpoint(crop_name: str):
    """
    Returns only the human-readable valid stage names for the specified crop.
    Internal day ranges and numeric bounds are never exposed to the frontend.
    """
    try:
        from dynamic_monitoring_engine import get_crop_stages
        raw_stages = get_crop_stages(crop_name)
        stage_names = []
        for s in raw_stages:
            name = s.get("stage")
            if name and name not in stage_names:
                stage_names.append(name)
        return {
            "success": True,
            "crop": crop_name,
            "stages": stage_names
        }
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Crop '{crop_name}' stages not found: {str(e)}"
        )


@router.get("/active-crops")
def get_active_crops_endpoint(farmer_id: Optional[str] = "FARMER_001"):
    """
    Returns active crops and fields currently being grown by the farmer with clean human-readable stage names.
    """
    today_dt = date.today()
    return {
        "success": True,
        "farmer_id": farmer_id,
        "active_crops": [
            {
                "crop_name": "Wheat",
                "field_id": "FIELD_WHT_001",
                "field_name": "North Field - Plot A",
                "planting_date": (today_dt - timedelta(days=22)).isoformat(),
                "formatted_planting_date": (today_dt - timedelta(days=22)).strftime("%d %b %Y"),
                "planting_date_formatted": (today_dt - timedelta(days=22)).strftime("%d %b %Y"),
                "days_after_planting": 22,
                "crop_age_days": 22,
                "current_stage": "Crown Root Initiation (CRI)",
                "human_stage_name": "Crown Root Initiation (CRI)",
                "status": "HEALTHY",
                "area_acres": 2.5
            },
            {
                "crop_name": "Rice",
                "field_id": "FIELD_RICE_001",
                "field_name": "East Basin - Plot B",
                "planting_date": (today_dt - timedelta(days=35)).isoformat(),
                "formatted_planting_date": (today_dt - timedelta(days=35)).strftime("%d %b %Y"),
                "planting_date_formatted": (today_dt - timedelta(days=35)).strftime("%d %b %Y"),
                "days_after_planting": 35,
                "crop_age_days": 35,
                "current_stage": "Active Tillering",
                "human_stage_name": "Active Tillering",
                "status": "NEEDS_ATTENTION",
                "area_acres": 3.0
            }
        ]
    }


@router.post("/analyze")
async def analyze_crop_monitoring(request: MonitoringAnalyzeRequest):
    """
    Official Ultra Crop Monitoring Decision Pipeline:
    Processes farm location, crop, planting date/stage, Open-Meteo live weather, and IoT telemetry.
    Generates multi-signal decisions, pre-harvest marketplace reminders, and structured notifications.
    """
    # Auto-resolve latitude and longitude for Indian district if not provided
    req_loc = request.location if request.location else LocationModel(state="Uttar Pradesh", district="Varanasi")
    lat = req_loc.latitude
    lon = req_loc.longitude

    if lat is None or lon is None:
        from ..data.india_districts import find_district
        matched = find_district(req_loc.state or "Uttar Pradesh", req_loc.district or "Varanasi")
        if matched:
            lat = matched.get("latitude")
            lon = matched.get("longitude")
        else:
            lat = 25.3176
            lon = 82.9739

    # Build raw dictionary request for the dynamic engine
    engine_req = {
        "farm_id": request.farm_id or "FARM_001",
        "field_id": request.field_id or "FIELD_001",
        "telemetry_id": request.telemetry_id or "TEL_001",
        "location": {
            "state": req_loc.state or "Uttar Pradesh",
            "district": req_loc.district or "Varanasi",
            "village": req_loc.village or "Demo Village",
            "latitude": lat,
            "longitude": lon,
        },
        "crop": {
            "crop_name": request.crop.crop_name,
            "planting_date": request.crop.planting_date,
            "crop_stage_mode": request.crop.crop_stage_mode or "AUTO",
            "crop_stage": request.crop.crop_stage,
        },
        "marketplace": {
            "crop_listed": request.marketplace.crop_listed if request.marketplace else False,
        },
        "telemetry": request.telemetry.dict() if request.telemetry else {
            "soil_moisture_percent": 30.0,
            "soil_temperature_c": 23.0,
            "air_temperature_c": 25.0,
            "relative_humidity_percent": 70.0,
            "rainfall_mm": 0.0,
            "leaf_wetness": False,
            "soil_ec_ds_m": 0.9,
            "soil_ph": 6.5,
            "light_hours": 8.0,
            "wind_speed_kmh": 10.0,
        }
    }

    try:
        monitoring_result = run_monitoring(engine_req)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Monitoring engine execution error: {str(e)}"
        )

    # Enrich with LLM guidance
    guidance_text = await enrich_with_gemini_guidance(monitoring_result)
    monitoring_result["farmer_guidance"]["advisory_text"] = guidance_text
    monitoring_result["farmer_guidance"]["summary"] = guidance_text

    # Apply any stored notification actions
    for notif in monitoring_result.get("notifications", []):
        nid = notif.get("notification_id")
        if nid in NOTIFICATION_ACTION_STORE:
            action_data = NOTIFICATION_ACTION_STORE[nid]
            notif["action_status"] = action_data.get("action")
            notif["action_reason"] = action_data.get("reason")
            notif["action_date"] = action_data.get("action_date")

    return {
        "success": True,
        **monitoring_result
    }


@router.post("/notification/action")
def handle_notification_action(payload: NotificationActionRequest):
    """
    Updates the state of a specific notification (e.g. marking as COMPLETE, POSTPONE, or RESCHEDULE).
    """
    valid_actions = ["COMPLETE", "POSTPONE", "RESCHEDULE", "CANCEL"]
    action_upper = payload.action.strip().upper()
    if action_upper not in valid_actions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action '{payload.action}'. Must be one of {valid_actions}"
        )

    NOTIFICATION_ACTION_STORE[payload.notification_id] = {
        "notification_id": payload.notification_id,
        "action": action_upper,
        "reason": payload.reason,
        "new_date": payload.new_date,
        "action_date": date.today().isoformat()
    }

    return {
        "success": True,
        "notification_id": payload.notification_id,
        "action": action_upper,
        "status": "UPDATED",
        "message": f"Notification '{payload.notification_id}' successfully updated to {action_upper}.",
        "updated_at": datetime.utcnow().isoformat()
    }

