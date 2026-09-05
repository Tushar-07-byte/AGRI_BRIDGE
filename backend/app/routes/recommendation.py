"""
AgriBridge Recommendation Engine Route

Provides POST /recommend-crop endpoint that calls the
recommendation_engine module to suggest crops based on
state, district, season, soil type, and optional pH.
"""

import sys
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional


# ============================================
# RECOMMENDATION ENGINE PATH
# ============================================

_backend_dir = Path(__file__).resolve().parents[2]
_workspace_dir = Path(__file__).resolve().parents[3]

RECOMMENDATION_ENGINE_DIR = (
    _workspace_dir / "ai_engine" / "recommendation"
    if (_workspace_dir / "ai_engine" / "recommendation").exists()
    else _backend_dir / "Recommendation_Engine"
)

sys.path.insert(0, str(RECOMMENDATION_ENGINE_DIR))


# ============================================
# IMPORT ENGINE FUNCTION
# ============================================

from recommendation_engine import (
    agribridge_crop_recommendation
)


# ============================================
# ROUTER
# ============================================

router = APIRouter(
    tags=["Recommendation"]
)


# ============================================
# REQUEST MODEL
# ============================================

class CropRecommendationRequest(BaseModel):

    state: str = Field(
        ...,
        description="Farmer's state",
        min_length=1
    )

    district: str = Field(
        ...,
        description="Farmer's district",
        min_length=1
    )

    season: str = Field(
        ...,  # required field
        description="Agricultural season",
        min_length=1
    )

    soil_type: str = Field(
        ...,  # required field
        description="Selected soil type",
        min_length=1
    )

    ph: Optional[float] = Field(
        default=None,
        description="Optional soil pH (0-14)"
    )


# ============================================
# VALIDATE PH RANGE
# ============================================

def validate_ph(ph_value):

    if ph_value is None:
        return None

    try:
        ph_float = float(ph_value)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=400,
            detail="Invalid soil pH value."
        )

    if ph_float < 0 or ph_float > 14:
        raise HTTPException(
            status_code=400,
            detail="Soil pH must be between 0 and 14."
        )

    return ph_float


# ============================================
# DROPDOWN DATA - Loaded once at startup
# ============================================

_dropdown_data = None


def _load_dropdown_data():
    global _dropdown_data
    if _dropdown_data is not None:
        return _dropdown_data

    # Build lookup structures from the loaded recommendation_index
    from recommendation_engine import recommendation_index

    states = {}
    for key, record in recommendation_index.items():
        state = record["State"]
        district = record["District"]
        season = record["Season"]
        soil_type = record["Soil_Type"]

        if state not in states:
            states[state] = {}
        if district not in states[state]:
            states[state][district] = {}
        if season not in states[state][district]:
            states[state][district][season] = soil_type

    _dropdown_data = states
    return _dropdown_data


# ============================================
# DROPDOWN ENDPOINTS
# ============================================

@router.get("/recommend-crop/states")
@router.get("/api/recommend-crop/states")
def get_states():
    data = _load_dropdown_data()
    return {"states": sorted(data.keys())}


@router.get("/recommend-crop/districts/{state}")
@router.get("/api/recommend-crop/districts/{state}")
def get_districts(state: str):
    data = _load_dropdown_data()
    state_key = state.strip()
    if state_key not in data:
        return {"districts": []}
    return {"districts": sorted(data[state_key].keys())}


@router.get("/recommend-crop/seasons/{state}/{district}")
@router.get("/api/recommend-crop/seasons/{state}/{district}")
def get_seasons(state: str, district: str):
    data = _load_dropdown_data()
    state_key = state.strip()
    district_key = district.strip()
    if state_key not in data:
        return {"seasons": []}
    if district_key not in data[state_key]:
        return {"seasons": []}
    return {"seasons": sorted(data[state_key][district_key].keys())}


@router.get("/recommend-crop/soil-type/{state}/{district}/{season}")
@router.get("/api/recommend-crop/soil-type/{state}/{district}/{season}")
def get_soil_type(state: str, district: str, season: str):
    data = _load_dropdown_data()
    state_key = state.strip()
    district_key = district.strip()
    season_key = season.strip()
    if (
        state_key in data
        and district_key in data[state_key]
        and season_key in data[state_key][district_key]
    ):
        return {"soil_type": data[state_key][district_key][season_key]}
    return {"soil_type": None}


# ============================================
# CROP RECOMMENDATION ENDPOINT
# ============================================

@router.post("/recommend-crop")
@router.post("/api/recommend-crop")
def recommend_crop(
    request: CropRecommendationRequest
):

    # ----------------------------------------
    # Validate required fields
    # ----------------------------------------

    if not request.state or not request.state.strip():
        raise HTTPException(
            status_code=400,
            detail="State is required."
        )

    if not request.district or not request.district.strip():
        raise HTTPException(
            status_code=400,
            detail="District is required."
        )

    if not request.season or not request.season.strip():
        raise HTTPException(
            status_code=400,
            detail="Season is required."
        )

    if not request.soil_type or not request.soil_type.strip():
        raise HTTPException(
            status_code=400,
            detail="Soil type is required."
        )

    # ----------------------------------------
    # Validate pH
    # ----------------------------------------

    validated_ph = validate_ph(request.ph)

    # ----------------------------------------
    # Call recommendation engine
    # ----------------------------------------

    result = agribridge_crop_recommendation(
        state=request.state,
        district=request.district,
        season=request.season,
        soil_type=request.soil_type,
        ph=validated_ph
    )

    # ----------------------------------------
    # Handle engine errors
    # ----------------------------------------

    if result["status"] == "error":

        raise HTTPException(
            status_code=404,
            detail=result["message"]
        )

    # ----------------------------------------
    # Return successful result
    # ----------------------------------------

    return result
