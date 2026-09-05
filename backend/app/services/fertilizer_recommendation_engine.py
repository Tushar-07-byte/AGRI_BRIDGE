# fertilizer_recommendation_engine.py
"""
Fertilizer Recommendation Engine
Provides a structured fertilizer recommendation based on existing recommendation data,
farmer info, and weather context.
"""
from typing import Dict, Any


def evaluate_fertilizer_recommendation(
    recommendation: Dict[str, Any],
    farm_info: Dict[str, Any],
    weather_context: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Generate a structured fertilizer recommendation.

    The function evaluates simple safety gates:
      * Postpone if high rain probability (>60%) or strong wind (>15 km/h).
      * Require verification if soil moisture > 80%.
    Otherwise it returns an AVAILABLE recommendation using the most recent
    fertilizer advice from the recommendation DB.

    Returns a dict matching the required schema:
        {
            "status": str,
            "crop": str,
            "stage": str,
            "fertilizer": str,
            "dose": str,
            "method": str,
            "timing": str,
            "why": str,
            "weather_check": str,
            "soil_check": str,
            "organic_management": str,
            "source": str,
            "verified": bool,
        }
    """
    # Basic context extraction with safe defaults
    crop = farm_info.get("crop", recommendation.get("crop", ""))
    stage = farm_info.get("growth_stage", recommendation.get("growth_stage", ""))
    fertilizer = farm_info.get("fertilizer_applied", "")
    # Placeholder values – in a real system these would be looked up from
    # a stage‑specific knowledge base.
    dose = "Standard dose as per soil test"
    method = "Broadcast"
    timing = "At planting"
    why = "Based on crop nutrient requirements and recent soil test"
    source = recommendation.get("fertilizer_advice", "")

    # Safety checks
    status = "AVAILABLE"
    weather_check = "OK"
    soil_check = "OK"
    organic_management = "Not required"
    if weather_context:
        rain_prob = weather_context.get("rain_probability", 0)
        wind = weather_context.get("wind_speed", 0)
        if rain_prob > 60 or wind > 15:
            status = "POSTPONED"
            weather_check = f"Rain probability {rain_prob}% or wind {wind} km/h too high"
    soil_moisture = farm_info.get("soil_moisture_percent", 0)
    if isinstance(soil_moisture, (int, float)) and soil_moisture > 80:
        status = "REQUIRES_VERIFICATION"
        soil_check = f"Soil moisture {soil_moisture}% high"

    verified = status == "AVAILABLE"

    return {
        "status": status,
        "crop": crop,
        "stage": stage,
        "fertilizer": fertilizer,
        "dose": dose,
        "method": method,
        "timing": timing,
        "why": why,
        "weather_check": weather_check,
        "soil_check": soil_check,
        "organic_management": organic_management,
        "source": source,
        "verified": verified,
    }


