"""
AgriBridge Open-Meteo Weather Context Adapter
Dynamic Indian location weather retrieval, 7-day forecast & agricultural risk assessment.
"""

from typing import Any, Dict, List, Optional, Tuple
from ..services.weather_service import get_current_weather, get_forecast
from ..data.india_districts import INDIA_DISTRICTS


def resolve_indian_coordinates(
    state: Optional[str] = None,
    district: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> Tuple[float, float]:
    """
    Resolves geographic coordinates for Indian farmer locations.
    Prioritizes direct lat/lon, then district centroid from master registry.
    Defaults to Central India (Nagpur 21.1458, 79.0882).
    """
    if latitude is not None and longitude is not None:
        try:
            lat = float(latitude)
            lon = float(longitude)
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return (lat, lon)
        except (ValueError, TypeError):
            pass

    if state and district:
        s_norm = state.strip().lower()
        d_norm = district.strip().lower()

        # Find matching state
        matched_state_key = None
        for k in INDIA_DISTRICTS.keys():
            if k.lower() == s_norm:
                matched_state_key = k
                break

        if matched_state_key:
            districts = INDIA_DISTRICTS[matched_state_key]
            for dist in districts:
                if dist["name"].lower() == d_norm or d_norm in dist["name"].lower():
                    return (dist["latitude"], dist["longitude"])

    # Fallback to general Indian coordinates
    return (21.1458, 79.0882)


async def get_monitoring_weather_context(
    state: Optional[str] = None,
    district: Optional[str] = None,
    village: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Fetches live Open-Meteo weather and compiles agricultural decision & risk context.
    """
    lat, lon = resolve_indian_coordinates(state, district, latitude, longitude)

    try:
        current = await get_current_weather(lat, lon)
    except Exception as e:
        print(f"[Weather Context] Current weather fetch error: {e}")
        current = {
            "temperature": 27.0,
            "humidity": 65,
            "precipitation": 0.0,
            "rainfall": 0.0,
            "wind_speed": 8.0,
            "weather_code": 0,
            "weather_condition": "Mainly Clear",
            "is_day": 1
        }

    try:
        forecast_15d = await get_forecast(lat, lon)
        # Take 7 days for the monitoring forecast
        forecast_7d = forecast_15d[:7] if forecast_15d else []
    except Exception as e:
        print(f"[Weather Context] Forecast fetch error: {e}")
        forecast_7d = []

    # Calculate Agricultural Weather Risks
    temp = current.get("temperature", 25.0) or 25.0
    humidity = current.get("humidity", 60) or 60
    wind_speed = current.get("wind_speed", 8.0) or 8.0
    rainfall_now = current.get("rainfall", 0.0) or current.get("precipitation", 0.0) or 0.0

    total_7d_rain = sum(float(day.get("rainfall", 0.0) or 0.0) for day in forecast_7d)
    rain_days_count = sum(1 for day in forecast_7d if float(day.get("rainfall", 0.0) or 0.0) > 2.0 or int(day.get("rain_probability", 0) or 0) > 50)
    max_7d_temp = max([float(day.get("temperature_max", 30) or 30) for day in forecast_7d] or [temp])
    min_7d_temp = min([float(day.get("temperature_min", 18) or 18) for day in forecast_7d] or [temp])

    # Risk Categories (Standardized for Indian Agricultural Seasons)
    rain_risk = "high" if (total_7d_rain > 150.0 or rainfall_now > 50.0) else ("moderate" if (total_7d_rain > 5.0 or rain_days_count >= 1 or rainfall_now > 0.0) else "low")
    humidity_risk = "high" if humidity > 96 else ("moderate" if humidity > 60 else "low")
    wind_risk = "high" if wind_speed > 45.0 else ("moderate" if wind_speed > 15.0 else "low")
    heat_risk = "high" if (temp > 44.0 or max_7d_temp > 44.0) else "low"
    cold_risk = "high" if (temp < 4.0 or min_7d_temp < 3.0) else "low"

    # Overall Weather Risk Score
    if rain_risk == "high" or heat_risk == "high" or wind_risk == "high" or cold_risk == "high":
        overall_risk = "high"
    elif rain_risk == "moderate" or humidity_risk in ["moderate", "high"] or wind_risk == "moderate":
        overall_risk = "moderate"
    else:
        overall_risk = "low"

    # Weather Decision for Farming Actions
    decision_reasons = []
    if rain_risk == "high":
        decision = "Postpone"
        decision_reasons.append(f"Significant precipitation expected ({total_7d_rain:.1f} mm across forecast). Postpone pesticide sprays and irrigation.")
    elif wind_risk == "high":
        decision = "Postpone"
        decision_reasons.append(f"High wind speed ({wind_speed:.1f} km/h) creates spray drift hazard.")
    elif rain_risk == "moderate" or humidity_risk == "high":
        decision = "Monitor"
        if humidity_risk == "high":
            decision_reasons.append(f"High humidity ({humidity}%) creates favorable microclimate for foliar fungal pathogens. Increase field scouting.")
        if rain_risk == "moderate":
            decision_reasons.append(f"Scattered light rain expected ({total_7d_rain:.1f} mm). Monitor weather before applying foliar nutrients.")
    else:
        decision = "Keep"
        decision_reasons.append("Current weather and 7-day forecast are clear and favorable for scheduled crop operations.")

    location_str = ", ".join(filter(None, [village, district, state, "India"])) or "India"

    # Build human-readable weather summary string
    weather_summary = (
        f"Current weather in {location_str} is {current.get('weather_condition', 'Clear')} at {temp:.1f}°C "
        f"with {humidity}% humidity, wind speed of {wind_speed:.1f} km/h, and {rainfall_now:.1f} mm precipitation. "
        f"The 7-day forecast indicates {total_7d_rain:.1f} mm total rainfall with {rain_days_count} rain-active days."
    )

    risk_explanation = (
        f"Overall weather risk is {overall_risk.capitalize()}. "
        + ("High humidity elevates disease pressure. " if humidity_risk == 'high' else "")
        + (f"Precipitation of {total_7d_rain:.1f} mm expected over next 7 days. " if total_7d_rain > 0 else "Dry conditions prevailing. ")
    )

    decision_explanation = (
        f"{decision} ({decision_reasons[0] if decision_reasons else 'Conditions suitable for scheduled management'})."
    )

    return {
        "location": {
            "state": state,
            "district": district,
            "village": village,
            "latitude": lat,
            "longitude": lon
        },
        "current_weather": current,
        "forecast_7d": forecast_7d,
        "risks": {
            "overall_risk": overall_risk,
            "rain_risk": rain_risk,
            "humidity_risk": humidity_risk,
            "wind_risk": wind_risk,
            "heat_risk": heat_risk,
            "cold_risk": cold_risk
        },
        "decision": decision,
        "decision_reasons": decision_reasons,
        "weather_summary": weather_summary,
        "weather_risk_summary": risk_explanation,
        "weather_decision_summary": decision_explanation
    }

