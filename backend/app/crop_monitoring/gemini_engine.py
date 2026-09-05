"""
AgriBridge Gemini Crop Monitoring & Recommendation Engine
Connects to Google Gemini (gemini-3.6-flash / 1.5-flash) with structured schema validation
and deterministic rule-based agricultural fallback.
"""

import os
import json
import httpx
from typing import Any, Dict, Optional

from .crop_registry import get_management_calendar, get_scientific_calendar
from .lifecycle_engine import calculate_crop_lifecycle
from .weather_context import get_monitoring_weather_context
from .marketplace_context import get_marketplace_context
from .safety_validator import validate_gemini_response, enforce_disease_safety_policy


def get_llm_api_key() -> str:
    """
    Retrieves API key securely from server environment.
    Prioritizes AGRIBRIDGE_LLM_API_KEY, falls back to GEMINI_API_KEY.
    """
    key = os.getenv("AGRIBRIDGE_LLM_API_KEY", "").strip()
    if not key:
        key = os.getenv("GEMINI_API_KEY", "").strip()
    return key


def _build_prompt_context(
    state: str,
    district: str,
    village: str,
    crop_id: str,
    planting_date: Optional[str],
    current_stage: Optional[str],
    lifecycle: Dict[str, Any],
    weather: Dict[str, Any],
    marketplace: Dict[str, Any],
) -> str:
    """Constructs complete prompt context for Gemini."""
    mgmt = get_management_calendar(crop_id)
    scientific = get_scientific_calendar(crop_id)

    curr_weather = weather.get("current_weather", {})
    forecast_7d = weather.get("forecast_7d", [])
    risks = weather.get("risks", {})

    context = {
        "system": {
            "name": "AgriBridge All India Crop Monitoring System",
            "country": "India"
        },
        "farmer_location": {
            "country": "India",
            "state": state,
            "district": district,
            "village": village
        },
        "crop": {
            "crop_id": crop_id,
            "crop_name": mgmt.get("crop_name", crop_id.capitalize())
        },
        "lifecycle_context": {
            "planting_date": planting_date,
            "days_after_planting": lifecycle.get("days_after_planting"),
            "current_stage": lifecycle.get("current_stage"),
            "stage_status": lifecycle.get("stage_status"),
            "next_stage": lifecycle.get("next_stage"),
            "current_activity_schedule": lifecycle.get("current_activity")
        },
        "weather_context": {
            "current": curr_weather,
            "7_day_forecast": forecast_7d,
            "weather_risks": risks,
            "weather_decision": weather.get("decision"),
            "weather_reasons": weather.get("decision_reasons")
        },
        "management_calendar": mgmt,
        "marketplace_context": marketplace
    }

    instructions = (
        "You are the AgriBridge Agricultural Monitoring Assistant for Indian farmers.\n"
        "Generate a structured, safe, scientific agronomic recommendation based on the supplied context.\n\n"
        "CRITICAL DISEASE SAFETY RULES:\n"
        "1. DO NOT diagnose, confirm, or predict any disease.\n"
        "2. Disease handling is INSPECTION-ONLY.\n"
        "3. Instruct the farmer that if abnormal leaf spots or symptoms appear, they should take a clear photo and use the separate AgriBridge Disease Detection feature.\n"
        "4. Follow standard registered pesticide and fertilizer labels.\n\n"
        "RESPONSE FORMAT:\n"
        "You MUST respond with valid JSON matching this exact schema:\n"
        "{\n"
        '  "current_stage": "string",\n'
        '  "stage_status": "string",\n'
        '  "next_stage": "string or null",\n'
        '  "weather_summary": "string",\n'
        '  "weather_risk": "low | moderate | high",\n'
        '  "weather_decision": "string",\n'
        '  "recommended_action": "string",\n'
        '  "irrigation_guidance": "string",\n'
        '  "fertilizer_guidance": "string",\n'
        '  "crop_protection_guidance": "string",\n'
        '  "monitoring_guidance": "string",\n'
        '  "marketplace_guidance": "string",\n'
        '  "safety_information": "string",\n'
        '  "important_note": "string",\n'
        '  "sources": ["string"]\n'
        "}"
    )

    return f"{instructions}\n\nCONTEXT:\n{json.dumps(context, indent=2, ensure_ascii=False)}"


def generate_rule_based_fallback_recommendation(
    crop_id: str,
    lifecycle: Dict[str, Any],
    weather: Dict[str, Any],
    marketplace: Dict[str, Any],
    state: str,
    district: str,
) -> Dict[str, Any]:
    """
    Expert rule-based fallback generating exact schema-compliant response
    when Gemini API key is not configured or network fails.
    """
    crop_norm = crop_id.strip().lower() if crop_id else "wheat"
    mgmt = get_management_calendar(crop_norm)
    crop_name = mgmt.get("crop_name", crop_norm.capitalize())

    stage = lifecycle.get("current_stage", "Active Growth")
    act = lifecycle.get("current_activity", {})
    weather_decision = weather.get("decision", "Keep")
    risks = weather.get("risks", {})
    overall_risk = risks.get("overall_risk", "low")

    irrigation = act.get("irrigation", "Maintain standard soil moisture")
    fertilizer = act.get("fertilizer", "Apply balanced nutrients as per schedule")
    protection = act.get("crop_protection", "Routine leaf visual scouting")

    if weather_decision == "Postpone":
        action_summary = (
            f"Postpone planned heavy irrigation and spraying due to weather risk ({weather.get('weather_risk_summary', '')}). "
            f"Resume {stage} activities once field conditions dry out."
        )
    elif weather_decision == "Monitor":
        action_summary = (
            f"Proceed cautiously with {stage} operations. Monitor canopy for moisture and humidity stress. "
            f"Apply scheduled: {fertilizer}."
        )
    else:
        action_summary = (
            f"Conditions favorable. Carry out {stage} activities on schedule: "
            f"Irrigation: {irrigation}; Fertilizer: {fertilizer}."
        )

    irrigation_guidance = (
        f"Provide {irrigation} for {crop_name} at {stage} stage. "
        + ("Delay if active rain occurs." if overall_risk in ("moderate", "high") else "Ensure uniform distribution.")
    )

    fertilizer_guidance = (
        f"Apply {fertilizer} according to the {crop_name} management calendar for the {stage} stage."
    )

    crop_protection_guidance = (
        f"Management calendar reference for {stage}: {protection}. "
        f"Note: Disease handling is inspection-only. Inspect leaves regularly for spots or lesions. "
        f"If abnormal symptoms appear, photograph the leaf and submit to AgriBridge AI Disease Scan."
    )

    monitoring_guidance = (
        f"Scout field for crop vigor, soil moisture at root zone, and monitor weather for sudden rain or wind shifts."
    )

    safety_info = (
        "Disease handling is inspection-only. No disease diagnosis or model inference is performed by LLM. "
        "Always follow registered product labels, maintain 7-10 days pre-harvest intervals (PHI), and wear protective gloves and mask."
    )

    note = (
        f"Advisory compiled from AgriBridge Scientific Calendar Registry and live Open-Meteo weather intelligence for {district}, {state}."
    )

    return {
        "current_stage": stage,
        "stage_status": lifecycle.get("stage_status", "Active"),
        "next_stage": lifecycle.get("next_stage"),
        "weather_summary": weather.get("weather_summary", "Weather data analyzed."),
        "weather_risk": f"Overall weather risk is {overall_risk.capitalize()}.",
        "weather_decision": f"{weather_decision} ({weather.get('weather_decision_summary', 'Weather conditions reviewed')})",
        "recommended_action": action_summary,
        "irrigation_guidance": irrigation_guidance,
        "fertilizer_guidance": fertilizer_guidance,
        "crop_protection_guidance": crop_protection_guidance,
        "monitoring_guidance": monitoring_guidance,
        "marketplace_guidance": marketplace.get("marketplace_guidance", "AgriBridge Marketplace is available for price monitoring."),
        "safety_information": safety_info,
        "important_note": note,
        "sources": [
            f"AgriBridge {crop_name} Management Calendar",
            "Open-Meteo Live Weather Service",
            "ICAR / Indian Agronomy Standards"
        ]
    }


async def generate_crop_recommendation(
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
    """
    Main entry point for generating complete AI/ML crop monitoring recommendation.
    """
    v_clean = village.strip() if village else ""
    s_clean = state.strip() if state else "Uttar Pradesh"
    d_clean = district.strip() if district else "Sultanpur"
    crop_norm = crop_id.strip().lower() if crop_id else "wheat"

    # 1. Compute Date-Aware Lifecycle
    lifecycle = calculate_crop_lifecycle(crop_norm, planting_date, current_stage)

    # 2. Get Open-Meteo Weather Context
    weather = await get_monitoring_weather_context(
        state=s_clean,
        district=d_clean,
        village=v_clean,
        latitude=latitude,
        longitude=longitude
    )

    # 3. Get Marketplace Context
    marketplace = get_marketplace_context(crop_norm, db_session=db_session)

    # 4. Check for Gemini API key
    api_key = get_llm_api_key()
    if not api_key:
        print("[Gemini Engine] AGRIBRIDGE_LLM_API_KEY not configured. Generating rule-based agricultural fallback.")
        fallback_res = generate_rule_based_fallback_recommendation(
            crop_id=crop_norm,
            lifecycle=lifecycle,
            weather=weather,
            marketplace=marketplace,
            state=s_clean,
            district=d_clean
        )
        _, validated, _ = validate_gemini_response(fallback_res)
        return validated

    # 5. Call Gemini LLM
    prompt = _build_prompt_context(
        state=s_clean,
        district=d_clean,
        village=v_clean,
        crop_id=crop_norm,
        planting_date=planting_date,
        current_stage=current_stage,
        lifecycle=lifecycle,
        weather=weather,
        marketplace=marketplace
    )

    # Try calling Gemini
    model_candidates = ["gemini-2.0-flash", "gemini-1.5-flash"]
    for model_name in model_candidates:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        # Parse JSON
                        parsed = json.loads(raw_text)
                        is_valid, validated, missing = validate_gemini_response(parsed)
                        if is_valid:
                            return validated
        except Exception as e:
            print(f"[Gemini Engine] Call to {model_name} failed: {e}")

    # If Gemini calls failed or returned invalid response, use rule-based fallback
    print("[Gemini Engine] Falling back to robust rule-based agricultural advisory.")
    fallback_res = generate_rule_based_fallback_recommendation(
        crop_id=crop_norm,
        lifecycle=lifecycle,
        weather=weather,
        marketplace=marketplace,
        state=s_clean,
        district=d_clean
    )
    _, validated, _ = validate_gemini_response(fallback_res)
    return validated

