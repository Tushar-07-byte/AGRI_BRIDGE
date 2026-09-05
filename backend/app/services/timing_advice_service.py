"""
AgriBridge Shared Timing Advice Service

Unified single source of truth for weather-aware disease treatment and spray timing.
Combines:
  1. Indian district coordinate resolution (app.data.india_districts)
  2. 15-day Open-Meteo dynamic weather forecasting (app.services.weather_service)
  3. 48-hour precipitation probability gate (>= 60% rain warning vs favorable window)

Called by:
  - Disease Prediction Pipeline: POST /api/ai/predict
  - Farmer Dashboard Live Advisory Banner: GET /api/weather/timing-alert
"""

from typing import Any, Dict, Optional, Tuple
from ..services.weather_service import get_forecast
from ..data.india_districts import INDIA_DISTRICTS, find_district, get_districts


def resolve_farm_coordinates(
    farm_info: Optional[Dict[str, Any]] = None,
    region_str: Optional[str] = None
) -> Tuple[float, float, str]:
    """
    Extracts latitude, longitude and human-readable location name from a farm profile
    dictionary or raw region string.
    """
    farm_info = farm_info or {}
    region = region_str or farm_info.get("region") or farm_info.get("location") or ""
    state_input = farm_info.get("state", "")
    district_input = farm_info.get("district", "")

    # 1. State and district explicitly provided
    if state_input and district_input:
        match = find_district(state_input, district_input)
        if match:
            return match["latitude"], match["longitude"], f"{match['name']}, {state_input}"

    # 2. Parse region string (e.g. "Ludhiana, Punjab" or "Guntur, Andhra Pradesh")
    if region:
        clean_parts = [p.strip() for p in region.replace("/", ",").replace("-", ",").split(",") if p.strip()]
        if len(clean_parts) >= 2:
            p1, p2 = clean_parts[0], clean_parts[1]
            match = find_district(p2, p1) or find_district(p1, p2)
            if match:
                loc_state = p2 if find_district(p2, p1) else p1
                return match["latitude"], match["longitude"], f"{match['name']}, {loc_state}"

        query = clean_parts[0].lower() if clean_parts else ""
        if query:
            # Check state match
            for state_name, dist_list in INDIA_DISTRICTS.items():
                if state_name.lower() == query and dist_list:
                    d0 = dist_list[0]
                    return d0["latitude"], d0["longitude"], f"{d0['name']}, {state_name}"
            # Check district match across all states
            for state_name, dist_list in INDIA_DISTRICTS.items():
                for d in dist_list:
                    if d["name"].lower() == query:
                        return d["latitude"], d["longitude"], f"{d['name']}, {state_name}"

    # Default fallback: central India coordinates
    return 21.1458, 79.0882, region or "Central India"


async def calculate_timing_advice(
    farm_info: Optional[Dict[str, Any]] = None,
    region_str: Optional[str] = None,
    crop_name: Optional[str] = None,
    disease_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Unified evaluation of weather forecast against crop treatment requirements.

    Returns structured timing_advice object:
      - status: 'delayed' | 'favorable'
      - rain_risk: bool
      - rain_probability: int
      - when: str (e.g. 'tomorrow')
      - recommended_window: str (e.g. 'Thursday (2026-09-04)')
      - summary: Short plain-language text for dashboard alert banner
      - advice: Detailed explanatory paragraph for AI result view
    """
    lat, lon, location_name = resolve_farm_coordinates(farm_info, region_str)

    try:
        forecast = await get_forecast(lat, lon)
    except Exception:
        forecast = []

    crop_display = f"your {crop_name.lower()} crop" if crop_name else "your crop"

    # If forecast is unavailable
    if not forecast or len(forecast) == 0:
        return {
            "status": "favorable",
            "rain_risk": False,
            "rain_probability": 0,
            "rainfall_est_mm": 0.0,
            "when": "upcoming days",
            "recommended_window": "Next 48 hours (calm morning hours)",
            "summary": f"Weather conditions are currently favorable — no significant rain expected for {crop_display}.",
            "advice": "Conditions are favorable — no significant rain expected in the next 48 hours.",
            "location": location_name,
            "crop": crop_name,
            "coordinates": {"latitude": lat, "longitude": lon}
        }

    # Evaluate next 48 hours (Day 0 and Day 1)
    next_48h = forecast[:2]
    high_rain_day = None
    max_rain_prob = 0
    max_rainfall = 0.0

    for idx, day in enumerate(next_48h):
        prob = int(day.get("rain_probability") or 0)
        rain_mm = float(day.get("rainfall") or 0.0)
        if prob > max_rain_prob:
            max_rain_prob = prob
        if rain_mm > max_rainfall:
            max_rainfall = rain_mm

        if prob >= 60 or rain_mm >= 5.0:
            if not high_rain_day:
                high_rain_day = {
                    "day_index": idx,
                    "date": day.get("date", "upcoming day"),
                    "rain_prob": prob,
                    "rainfall": rain_mm,
                    "condition": day.get("weather_condition", "Rain")
                }

    # CASE 1: High Rain Chance (>= 60% probability or heavy rain) -> DELAY SPRAYING
    if max_rain_prob >= 60 or (high_rain_day is not None):
        when_str = "today" if high_rain_day and high_rain_day["day_index"] == 0 else "tomorrow"
        date_str = high_rain_day.get("date", "") if high_rain_day else next_48h[0].get("date", "")
        when_display = f"{when_str} ({date_str})" if date_str else when_str

        # Find next dry window in forecast (days 2 to 14)
        recommended_window = "after the 48-hour rain system passes"
        short_dry_day = "later this week"
        for day in forecast[2:]:
            day_prob = int(day.get("rain_probability") or 0)
            day_rain = float(day.get("rainfall") or 0.0)
            if day_prob < 30 and day_rain < 1.0:
                recommended_window = f"{day.get('date')} ({day.get('weather_condition', 'Clear')})"
                short_dry_day = day.get('date')
                break

        summary_text = f"⚠ Rain expected {when_str} ({max_rain_prob}% chance) — delay spraying {crop_display} until {short_dry_day}."
        advice_text = (
            f"Delay spraying — {max_rain_prob}% chance of rain expected {when_display}. "
            f"Rain will wash off treatment before it takes effect. "
            f"Recommended window: {recommended_window}."
        )

        return {
            "status": "delayed",
            "rain_risk": True,
            "rain_probability": max_rain_prob,
            "rainfall_est_mm": max_rainfall,
            "when": when_str,
            "rain_expected_period": when_display,
            "recommended_window": recommended_window,
            "short_dry_day": short_dry_day,
            "summary": summary_text,
            "advice": advice_text,
            "location": location_name,
            "crop": crop_name,
            "coordinates": {"latitude": lat, "longitude": lon}
        }

    # CASE 2: Favorable Weather -> SAFE TO SPRAY
    summary_text = f"✓ Conditions are currently favorable — no significant rain expected in the next 48 hours for {crop_display}."
    advice_text = (
        f"Conditions are favorable — no significant rain expected in the next 48 hours (rain chance: {max_rain_prob}%)."
    )

    return {
        "status": "favorable",
        "rain_risk": False,
        "rain_probability": max_rain_prob,
        "rainfall_est_mm": max_rainfall,
        "when": "next 48 hours",
        "recommended_window": "Next 48 hours (optimal early morning or late afternoon hours)",
        "summary": summary_text,
        "advice": advice_text,
        "location": location_name,
        "crop": crop_name,
        "coordinates": {"latitude": lat, "longitude": lon}
    }

