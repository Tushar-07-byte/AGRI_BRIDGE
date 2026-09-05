"""
AgriBridge Weather Routes

Provides:
  GET  /api/weather/states
  GET  /api/weather/districts/{state}
  GET  /api/weather/current
  GET  /api/weather/forecast
  POST /api/weather/advisory
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.listing import Listing
from app.data.india_districts import (
    get_all_states,
    get_districts,
    find_district,
)
from app.services.weather_service import (
    get_current_weather,
    get_forecast,
)
from app.services.gemini_service import get_gemini_advisory
from app.services.timing_advice_service import calculate_timing_advice


# ============================================
# ROUTER
# ============================================

router = APIRouter(
    prefix="/api/weather",
    tags=["Weather"],
)


# ============================================
# VALID CROPS (matches SUPPORTED_PLANTS from ai.py)
# ============================================

VALID_CROPS = {
    "apple", "blueberry", "cherry", "corn", "grape",
    "orange", "peach", "pepper", "potato", "raspberry",
    "rice", "soybean", "squash", "strawberry", "tomato",
    "wheat",
}

VALID_GROWTH_STAGES = {
    "seedling", "vegetative", "flowering",
    "fruiting", "maturity",
}


# ============================================
# GET /api/weather/states
# ============================================

@router.get("/states")
def get_states():
    """Return all 36 Indian States/UTs."""
    return {
        "success": True,
        "states": get_all_states(),
    }


# ============================================
# GET /api/weather/districts/{state}
# ============================================

@router.get("/districts")
@router.get("/districts/{state}")
def get_state_districts(state: Optional[str] = None):
    """Return districts with coordinates for a given state (supports path or query param)."""
    if not state:
        return {
            "success": False,
            "error": "State parameter is required.",
            "districts": []
        }

    districts = get_districts(state)

    if not districts:
        return {
            "success": False,
            "error": f"State '{state}' not found.",
            "districts": []
        }

    return {
        "success": True,
        "state": state,
        "districts": [
            {
                "name": d["name"],
                "latitude": d["latitude"],
                "longitude": d["longitude"],
            }
            for d in districts
        ],
    }


# ============================================
# GET /api/weather/current
# ============================================

@router.get("/current")
async def get_current(
    state: str = "",
    district: str = "",
):
    """Fetch current weather for a district."""

    if not state or not district:
        raise HTTPException(
            status_code=400,
            detail="Both 'state' and 'district' are required.",
        )

    district_data = find_district(state, district)
    if not district_data:
        return {
            "success": False,
            "error": (
                f"District '{district}' not found "
                f"in state '{state}'."
            ),
        }

    try:
        weather = await get_current_weather(
            district_data["latitude"],
            district_data["longitude"],
        )
    except Exception:
        return {
            "success": False,
            "error": (
                "Weather service is temporarily unavailable. "
                "Please try again later."
            ),
        }

    return {
        "success": True,
        "location": {
            "state": state,
            "district": district,
            "latitude": district_data["latitude"],
            "longitude": district_data["longitude"],
        },
        "current_weather": weather,
    }


# ============================================
# GET /api/weather/forecast
# ============================================

@router.get("/forecast")
async def get_forecast_api(
    state: str = "",
    district: str = "",
):
    """Fetch 15-day forecast for a district."""

    if not state or not district:
        raise HTTPException(
            status_code=400,
            detail="Both 'state' and 'district' are required.",
        )

    district_data = find_district(state, district)
    if not district_data:
        return {
            "success": False,
            "error": (
                f"District '{district}' not found "
                f"in state '{state}'."
            ),
        }

    try:
        forecast = await get_forecast(
            district_data["latitude"],
            district_data["longitude"],
        )
    except Exception:
        return {
            "success": False,
            "error": (
                "Weather forecast service is temporarily "
                "unavailable. Please try again later."
            ),
        }

    return {
        "success": True,
        "location": {
            "state": state,
            "district": district,
            "latitude": district_data["latitude"],
            "longitude": district_data["longitude"],
        },
        "forecast": forecast,
    }


# ============================================
# REQUEST MODEL FOR ADVISORY
# ============================================

class AdvisoryRequest(BaseModel):
    state: str = Field(
        ..., description="Indian state or UT", min_length=1
    )
    district: str = Field(
        ..., description="District name", min_length=1
    )
    crop: str = Field(
        ..., description="Crop name", min_length=1
    )
    growth_stage: str = Field(
        ..., description="Growth stage", min_length=1
    )


# ============================================
# POST /api/weather/advisory
# ============================================

@router.post("/advisory")
async def get_advisory(request: AdvisoryRequest):
    """
    Full weather advisory endpoint.
    Validates → fetches weather → builds context → calls Gemini.
    """

    # -------------------------------------------
    # Validate state
    # -------------------------------------------

    districts = get_districts(request.state)
    if not districts:
        return {
            "success": False,
            "error": (
                f"State '{request.state}' not found. "
                "Please select a valid Indian state or UT."
            ),
        }

    # -------------------------------------------
    # Validate district
    # -------------------------------------------

    district_data = find_district(
        request.state, request.district
    )
    if not district_data:
        return {
            "success": False,
            "error": (
                f"District '{request.district}' not found "
                f"in {request.state}."
            ),
        }

    # -------------------------------------------
    # Validate crop
    # -------------------------------------------

    crop_lower = request.crop.strip().lower()
    if crop_lower not in VALID_CROPS:
        return {
            "success": False,
            "error": (
                f"Crop '{request.crop}' is not supported. "
                f"Valid crops: {', '.join(sorted(VALID_CROPS))}"
            ),
        }

    # -------------------------------------------
    # Validate growth stage
    # -------------------------------------------

    stage_lower = request.growth_stage.strip().lower()
    if stage_lower not in VALID_GROWTH_STAGES:
        return {
            "success": False,
            "error": (
                f"Growth stage '{request.growth_stage}' is "
                f"not valid. Valid stages: "
                f"{', '.join(sorted(VALID_GROWTH_STAGES))}"
            ),
        }

    # -------------------------------------------
    # Fetch weather
    # -------------------------------------------

    try:
        current_weather = await get_current_weather(
            district_data["latitude"],
            district_data["longitude"],
        )
        forecast = await get_forecast(
            district_data["latitude"],
            district_data["longitude"],
        )
    except Exception:
        return {
            "success": False,
            "error": (
                "Weather service is temporarily unavailable. "
                "Please try again later."
            ),
        }

    # -------------------------------------------
    # Get Gemini advisory
    # -------------------------------------------

    agricultural_advisory = await get_gemini_advisory(
        state=request.state,
        district=request.district,
        crop=request.crop.strip(),
        growth_stage=request.growth_stage.strip(),
        current_weather=current_weather,
        forecast=forecast,
    )

    # -------------------------------------------
    # Return consistent response
    # -------------------------------------------

    return {
        "success": True,
        "status": "success",
        "location": {
            "state": request.state,
            "district": request.district,
            "latitude": district_data["latitude"],
            "longitude": district_data["longitude"],
        },
        "crop": request.crop.strip(),
        "growth_stage": request.growth_stage.strip(),
        "current_weather": current_weather,
        "forecast": forecast,
        "forecast_15_days": forecast,
        "agricultural_advisory": agricultural_advisory,
        "ai_advisory": {
            "provider": "Gemini",
            "advisory": agricultural_advisory,
        },
    }


# ============================================
# GET /api/weather/timing-alert
# ============================================

@router.get("/timing-alert")
async def get_spray_timing_alert(
    region: Optional[str] = None,
    crop: Optional[str] = None,
    farmer_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Farmer Dashboard Live Spray Timing & Rain Alert.
    Reuses the shared timing_advice_service to calculate rain probability
    and spray timing advice for the farmer's region and crop.
    """
    crop_name = crop
    farm_info = {}

    # If farmer_id provided and crop not specified, check most recent listing for this farmer
    if farmer_id and not crop_name:
        latest_listing = (
            db.query(Listing)
            .filter(Listing.farmer_id == farmer_id)
            .order_by(Listing.id.desc())
            .first()
        )
        if latest_listing:
            crop_name = latest_listing.crop_type

    if region:
        farm_info["region"] = region

    alert_data = await calculate_timing_advice(
        farm_info=farm_info,
        region_str=region,
        crop_name=crop_name
    )

    return {
        "success": True,
        "alert": alert_data
    }
