"""
AgriBridge Gemini Agricultural Advisory Service

Sends weather + crop + growth stage context to Gemini LLM
and generates a structured, actionable agricultural advisory.
Includes an expert rule-based agricultural fallback engine
when GEMINI_API_KEY is not configured or network is unreachable.
"""

import os
import httpx
from typing import Any, Dict, List


def get_gemini_api_key() -> str:
    return os.getenv("GEMINI_API_KEY", "").strip()


# ============================================
# BUILD AGRICULTURAL CONTEXT
# ============================================

def build_weather_advice_context(
    current_weather: Dict[str, Any],
    forecast: List[Dict[str, Any]],
) -> str:
    """Convert weather data into a readable context string."""
    lines = []

    lines.append("CURRENT WEATHER:")
    lines.append(f"  Temperature: {current_weather.get('temperature', 'N/A')} °C")
    lines.append(f"  Humidity: {current_weather.get('humidity', 'N/A')}%")
    lines.append(f"  Rainfall: {current_weather.get('rainfall', 0)} mm")
    lines.append(f"  Wind Speed: {current_weather.get('wind_speed', 'N/A')} km/h")
    lines.append(f"  Condition: {current_weather.get('weather_condition', 'Clear')}")

    lines.append("")
    lines.append("15-DAY FORECAST:")
    for day in forecast:
        lines.append(
            f"  {day.get('date', '')}: "
            f"{day.get('temperature_min', '?')}°C to "
            f"{day.get('temperature_max', '?')}°C, "
            f"Rain: {day.get('rainfall', 0)}mm "
            f"({day.get('rain_probability', 0)}% chance), "
            f"{day.get('weather_condition', 'Clear')}"
        )

    return "\n".join(lines)


# ============================================
# EXPERT RULE-BASED FALLBACK ADVISORY
# ============================================

def generate_fallback_advisory(
    state: str,
    district: str,
    crop: str,
    growth_stage: str,
    current_weather: Dict[str, Any],
    forecast: List[Dict[str, Any]],
) -> str:
    """Generate structured agricultural advisory from weather metrics."""
    temp = current_weather.get("temperature", 25.0) or 25.0
    humidity = current_weather.get("humidity", 60) or 60
    wind_speed = current_weather.get("wind_speed", 5.0) or 5.0
    rainfall = current_weather.get("rainfall", 0.0) or 0.0

    total_forecast_rain = sum(
        float(day.get("rainfall", 0) or 0) for day in forecast
    )
    rainy_days = [
        day.get("date") for day in forecast
        if float(day.get("rainfall", 0) or 0) > 2.0 or int(day.get("rain_probability", 0) or 0) > 50
    ]
    spray_days = [
        day.get("date") for day in forecast[:7]
        if float(day.get("rainfall", 0) or 0) < 0.5 and int(day.get("rain_probability", 0) or 0) < 25
    ]
    max_forecast_temp = max(
        [float(day.get("temperature_max", 30) or 30) for day in forecast] or [30.0]
    )
    min_forecast_temp = min(
        [float(day.get("temperature_min", 18) or 18) for day in forecast] or [18.0]
    )

    crop_title = crop.capitalize()
    stage_title = growth_stage.capitalize()

    # 1. Irrigation Advice
    if total_forecast_rain > 15.0 or rainfall > 5.0:
        irrigation = (
            f"Precipitation expected in the forecast ({total_forecast_rain:.1f} mm total). "
            f"Postpone planned irrigation to conserve water and prevent soil saturation around {crop_title} root zones."
        )
    elif humidity < 45 or temp > 32:
        irrigation = (
            f"High evaporation demand detected ({temp:.1f}°C, {humidity}% humidity). "
            f"Maintain light and frequent irrigation during morning or evening hours to support the {stage_title} stage."
        )
    else:
        irrigation = (
            f"Moderate moisture levels. Provide regular maintenance irrigation according to {crop_title} soil moisture status."
        )

    # 2. Rain Precautions
    if rainy_days:
        rain_precaution = (
            f"Rain expected on {len(rainy_days)} day(s) in the 15-day window ({', '.join(rainy_days[:3])}). "
            f"Ensure open drainage paths and protect newly harvested or sensitive field produce."
        )
    else:
        rain_precaution = (
            f"Dry weather trend expected over the forecast period with minimal rainfall probability. "
            f"Plan standard intercultural operations without rain disruption."
        )

    # 3. Temperature Advice
    if max_forecast_temp >= 35.0:
        temp_advice = (
            f"Peak temperatures reaching {max_forecast_temp:.1f}°C may cause heat stress during {stage_title}. "
            f"Ensure adequate soil mulching and morning irrigation to buffer root-zone temperatures."
        )
    elif min_forecast_temp <= 12.0:
        temp_advice = (
            f"Night-time temperatures dropping to {min_forecast_temp:.1f}°C. "
            f"Monitor young {crop_title} plants for cold sensitivity and maintain light soil moisture."
        )
    else:
        temp_advice = (
            f"Forecast temperatures ({min_forecast_temp:.1f}°C to {max_forecast_temp:.1f}°C) are favourable "
            f"for {crop_title} development in {district}, {state}."
        )

    # 4. Humidity and Disease Risk
    if humidity >= 70 or total_forecast_rain > 10.0:
        disease_risk = (
            f"Elevated humidity ({humidity}%) and moisture increase the risk of fungal and bacterial foliar diseases. "
            f"Scout lower leaves for early spots or lesions and apply recommended bio-fungicide preventatively."
        )
    else:
        disease_risk = (
            f"Moderate humidity ({humidity}%). Low immediate disease pressure, but regular field scouting is recommended."
        )

    # 5. Spraying Timing
    if spray_days:
        spray_advice = (
            f"Favourable spraying windows (calm wind, low rain probability) identified on: {', '.join(spray_days[:3])}. "
            f"Complete bio-fertilizer or nutrient foliar sprays during early morning hours."
        )
    else:
        spray_advice = (
            f"Current wind ({wind_speed:.1f} km/h) or weather conditions suggest checking immediate field conditions before spraying."
        )

    # 6. Drainage
    if total_forecast_rain > 20.0:
        drainage = "High total precipitation expected. Clear field drainage channels and prevent standing water in crop furrows."
    else:
        drainage = "Standard drainage management is sufficient. Ensure soil has proper aeration."

    # 7. Field Monitoring
    field_monitoring = (
        f"For {crop_title} at the {stage_title} stage, inspect crop canopy twice weekly. "
        f"Check for nutrient deficiency symptoms and pest presence on new growth."
    )

    # 8. General Recommendation
    general_rec = (
        f"Focus on balanced moisture management and timely canopy protection for {crop_title} "
        f"across {district}, {state} over the next 15 days."
    )

    advisory_text = (
        f"1. **Irrigation Advice** - {irrigation}\n\n"
        f"2. **Rain Precautions** - {rain_precaution}\n\n"
        f"3. **Temperature Advice** - {temp_advice}\n\n"
        f"4. **Humidity and Disease Risk** - {disease_risk}\n\n"
        f"5. **Spraying Timing** - {spray_advice}\n\n"
        f"6. **Drainage** - {drainage}\n\n"
        f"7. **Field Monitoring** - {field_monitoring}\n\n"
        f"8. **General Recommendation** - {general_rec}"
    )

    return advisory_text


# ============================================
# GEMINI ADVISORY
# ============================================

async def get_gemini_advisory(
    state: str,
    district: str,
    crop: str,
    growth_stage: str,
    current_weather: Dict[str, Any],
    forecast: List[Dict[str, Any]],
) -> str:
    """
    Generate agricultural advisory using Gemini LLM if API key is provided,
    otherwise smoothly utilize the expert agricultural rule-based engine.
    """
    api_key = get_gemini_api_key()

    if not api_key:
        return generate_fallback_advisory(
            state, district, crop, growth_stage, current_weather, forecast
        )

    weather_text = build_weather_advice_context(
        current_weather, forecast
    )

    prompt = (
        "You are an expert agricultural advisor for Indian farmers. "
        "Provide practical, actionable advice based on the following real-time data.\n\n"
        f"FARMER LOCATION: {state}, {district}\n"
        f"CROP: {crop}\n"
        f"GROWTH STAGE: {growth_stage}\n\n"
        f"{weather_text}\n\n"
        "Provide advice organized strictly in the following 8 numbered sections:\n\n"
        "1. **Irrigation Advice** - When and how much to irrigate based on current and forecast rainfall.\n"
        "2. **Rain Precautions** - Any rain expected and what the farmer should prepare for.\n"
        "3. **Temperature Advice** - Any heat stress or cold risk based on forecast temperatures.\n"
        "4. **Humidity and Disease Risk** - Humidity-related disease risk for this crop at this growth stage.\n"
        "5. **Spraying Timing** - Best days in the forecast for spraying (low wind, no rain).\n"
        "6. **Drainage** - Advice on field drainage and flood prevention.\n"
        "7. **Field Monitoring** - What specific symptoms to watch for in the next 15 days.\n"
        "8. **General Recommendation** - Overall 15-day action plan for the farmer.\n\n"
        "Rules:\n"
        "- Use simple, clear language suitable for farmers.\n"
        "- Do NOT recommend specific chemical brand names (only general categories like fungicide, bio-pesticide, urea, etc.).\n"
        "- Base ALL weather claims strictly on the provided weather data. Do not invent weather numbers."
    )

    try:
        api_url = (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models/gemini-1.5-flash:generateContent"
            f"?key={api_key}"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                api_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

        candidates = data.get("candidates", [])
        if candidates:
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if parts:
                text = parts[0].get("text", "")
                if text and len(text.strip()) > 50:
                    return text.strip()

        return generate_fallback_advisory(
            state, district, crop, growth_stage, current_weather, forecast
        )

    except Exception:
        return generate_fallback_advisory(
            state, district, crop, growth_stage, current_weather, forecast
        )
