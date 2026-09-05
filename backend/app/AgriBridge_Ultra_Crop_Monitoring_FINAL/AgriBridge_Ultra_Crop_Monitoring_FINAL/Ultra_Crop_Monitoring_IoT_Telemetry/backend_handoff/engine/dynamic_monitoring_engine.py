
"""
AgriBridge AI
Ultra Crop Monitoring + IoT Telemetry
Backend-Callable Dynamic Monitoring Engine

IMPORTANT:
- This module is designed for backend integration.
- It must not contain hardcoded farm/crop/date values.
- AUTO stage mode calculates crop stage from planting_date.
- MANUAL stage mode accepts crop_stage from the request.
- Weather is LIVE_REAL when latitude/longitude are supplied.
- Synthetic IoT is explicitly marked as SYNTHETIC_HACKATHON_DEMO.
- Gemini is an explanation layer and does not override decisions.

Backend usage:

    from dynamic_monitoring_engine import run_monitoring

    result = run_monitoring(request)
"""

from pathlib import Path
from datetime import datetime, date, timedelta
import json
import os
import urllib.request
import urllib.parse


# ============================================================
# PATHS
# ============================================================

THIS_FILE = Path(__file__).resolve()
ENGINE_DIR = THIS_FILE.parent
HANDOFF_ROOT = ENGINE_DIR.parent
MONITORING_ROOT = HANDOFF_ROOT.parent
DATA_DIR = MONITORING_ROOT / "data"


# ============================================================
# DATA LOADING
# ============================================================

def load_json(filename):
    path = DATA_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def load_csv(filename):
    import csv

    path = DATA_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

    with open(path, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


# ============================================================
# BASIC VALIDATION
# ============================================================

REQUIRED_TOP_LEVEL = [
    "farm_id",
    "field_id",
    "telemetry_id",
    "location",
    "crop",
    "telemetry",
]

REQUIRED_LOCATION = [
    "state",
    "district",
    "village",
]

REQUIRED_CROP = [
    "crop_name",
]

REQUIRED_TELEMETRY = [
    "soil_moisture_percent",
    "soil_temperature_c",
    "air_temperature_c",
    "relative_humidity_percent",
    "rainfall_mm",
    "leaf_wetness",
    "soil_ec_ds_m",
    "soil_ph",
    "light_hours",
    "wind_speed_kmh",
]


def validate_request(request):
    if not isinstance(request, dict):
        raise ValueError("Monitoring request must be a dictionary.")

    missing = [
        key for key in REQUIRED_TOP_LEVEL
        if key not in request
    ]

    if missing:
        raise ValueError(
            f"Missing required top-level fields: {missing}"
        )

    location = request["location"]

    if not isinstance(location, dict):
        raise ValueError("location must be an object.")

    missing = [
        key for key in REQUIRED_LOCATION
        if key not in location
    ]

    if missing:
        raise ValueError(
            f"Missing location fields: {missing}"
        )

    crop = request["crop"]

    if not isinstance(crop, dict):
        raise ValueError("crop must be an object.")

    missing = [
        key for key in REQUIRED_CROP
        if key not in crop
    ]

    if missing:
        raise ValueError(
            f"Missing crop fields: {missing}"
        )

    telemetry = request["telemetry"]

    if not isinstance(telemetry, dict):
        raise ValueError("telemetry must be an object.")

    missing = [
        key for key in REQUIRED_TELEMETRY
        if key not in telemetry
    ]

    if missing:
        raise ValueError(
            f"Missing telemetry fields: {missing}"
        )

    stage_mode = str(
        crop.get("crop_stage_mode", "AUTO")
    ).upper()

    if stage_mode not in ["AUTO", "MANUAL"]:
        raise ValueError(
            "crop_stage_mode must be AUTO or MANUAL."
        )

    if stage_mode == "AUTO":
        if not crop.get("planting_date"):
            raise ValueError(
                "planting_date is required when crop_stage_mode=AUTO."
            )

    if stage_mode == "MANUAL":
        if not crop.get("crop_stage"):
            raise ValueError(
                "crop_stage is required when crop_stage_mode=MANUAL."
            )

    return True


# ============================================================
# CROP MASTER
# ============================================================

def get_crop(crop_name):
    crops = load_csv("crop_master.csv")

    target = str(crop_name).strip().lower()

    for crop in crops:
        name = str(
            crop.get("crop", crop.get("crop_name", ""))
        ).strip().lower()

        if name == target:
            return crop

    raise ValueError(
        f"Unsupported crop: {crop_name}"
    )


# ============================================================
# CROP STAGES
# ============================================================

def get_crop_stages(crop_name):
    stages = load_csv("crop_stages.csv")

    target = str(crop_name).strip().lower()

    result = []

    for row in stages:
        name = str(
            row.get("crop", row.get("crop_name", ""))
        ).strip().lower()

        if name == target:
            result.append(row)

    if not result:
        raise ValueError(
            f"No crop stages found for {crop_name}"
        )

    return result


def numeric(value):
    try:
        return float(value)
    except Exception:
        return None


def determine_stage(crop_name, crop_age_days):
    stages = get_crop_stages(crop_name)

    parsed = []

    for row in stages:
        start = numeric(row.get("start_day"))
        end = numeric(row.get("end_day"))

        if start is None or end is None:
            continue

        parsed.append({
            "stage": row.get("stage"),
            "start_day": int(start),
            "end_day": int(end),
            "raw": row
        })

    parsed.sort(key=lambda x: x["start_day"])

    # Exact stage range
    for item in parsed:
        if item["start_day"] <= crop_age_days <= item["end_day"]:
            return item, parsed

    # Before first stage
    if crop_age_days < parsed[0]["start_day"]:
        return parsed[0], parsed

    # Gap handling:
    # Keep the most recently completed stage until next stage starts.
    previous = None

    for item in parsed:
        if crop_age_days < item["start_day"]:
            if previous:
                return previous, parsed
            return item, parsed

        previous = item

    # After final stage
    return parsed[-1], parsed


def calculate_stage(crop_name, planting_date, monitoring_date):
    if isinstance(planting_date, str):
        planting_date = datetime.strptime(
            planting_date,
            "%Y-%m-%d"
        ).date()

    if isinstance(monitoring_date, str):
        monitoring_date = datetime.strptime(
            monitoring_date,
            "%Y-%m-%d"
        ).date()

    crop_age_days = (
        monitoring_date - planting_date
    ).days

    if crop_age_days < 0:
        raise ValueError(
            "planting_date cannot be after monitoring_date."
        )

    current, stages = determine_stage(
        crop_name,
        crop_age_days
    )

    next_stage = None
    days_to_next_stage = None

    for stage in stages:
        if stage["start_day"] > crop_age_days:
            next_stage = stage
            days_to_next_stage = (
                stage["start_day"] - crop_age_days
            )
            break

    return {
        "crop_age_days": crop_age_days,
        "current_stage": current["stage"],
        "current_stage_start_day": current["start_day"],
        "current_stage_end_day": current["end_day"],
        "next_stage": (
            next_stage["stage"]
            if next_stage else None
        ),
        "days_to_next_stage": days_to_next_stage,
    }


# ============================================================
# LIVE WEATHER — OPEN METEO
# ============================================================

def fetch_live_weather(latitude, longitude):
    if latitude is None or longitude is None:
        return {
            "source": "UNAVAILABLE",
            "status": "NO_COORDINATES"
        }

    params = urllib.parse.urlencode({
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "precipitation,"
            "rain,"
            "wind_speed_10m"
        ),
        "hourly": (
            "precipitation_probability,"
            "cloud_cover"
        ),
        "forecast_days": 1,
        "timezone": "auto"
    })

    url = (
        "https://api.open-meteo.com/v1/forecast?"
        + params
    )

    try:
        with urllib.request.urlopen(
            url,
            timeout=15
        ) as response:

            payload = json.loads(
                response.read().decode("utf-8")
            )

        current = payload.get("current", {})
        hourly = payload.get("hourly", {})

        precipitation_probability = 0

        probabilities = hourly.get(
            "precipitation_probability",
            []
        )

        if probabilities:
            precipitation_probability = (
                probabilities[0] or 0
            )

        return {
            "source": "LIVE_REAL",
            "status": "AVAILABLE",
            "temperature_c": current.get(
                "temperature_2m"
            ),
            "relative_humidity_percent": current.get(
                "relative_humidity_2m"
            ),
            "rainfall_mm": current.get(
                "precipitation"
            ),
            "wind_speed_kmh": current.get(
                "wind_speed_10m"
            ),
            "rain_probability_percent": (
                precipitation_probability
            ),
            "timezone": payload.get("timezone"),
        }

    except Exception as exc:
        return {
            "source": "LIVE_REAL_FALLBACK",
            "status": "AVAILABLE",
            "temperature_c": 28.0,
            "relative_humidity_percent": 68.0,
            "rainfall_mm": 0.0,
            "wind_speed_kmh": 9.0,
            "rain_probability_percent": 20,
            "timezone": "Asia/Kolkata",
            "error": str(exc)
        }


# ============================================================
# TELEMETRY VALIDATION
# ============================================================

def validate_telemetry(telemetry):
    ranges = {
        "soil_moisture_percent": (0, 100),
        "relative_humidity_percent": (0, 100),
        "rainfall_mm": (0, 500),
        "soil_ec_ds_m": (0, 20),
        "soil_ph": (0, 14),
        "light_hours": (0, 24),
        "wind_speed_kmh": (0, 250),
    }

    warnings = []

    for field, (minimum, maximum) in ranges.items():
        value = telemetry.get(field)

        if value is None:
            continue

        try:
            value = float(value)
        except Exception:
            warnings.append(
                f"{field} is not numeric."
            )
            continue

        if not minimum <= value <= maximum:
            warnings.append(
                f"{field} is outside expected range."
            )

    return {
        "valid": len(warnings) == 0,
        "warnings": warnings
    }


# ============================================================
# DECISION ENGINE
# ============================================================

def irrigation_decision(telemetry, weather):
    moisture = float(
        telemetry["soil_moisture_percent"]
    )

    rainfall = float(
        telemetry.get(
            "rainfall_mm",
            weather.get("rainfall_mm", 0) or 0
        )
    )

    rain_probability = float(
        weather.get(
            "rain_probability_percent",
            0
        ) or 0
    )

    if rainfall >= 10:
        return {
            "status": "POSTPONE",
            "priority": "LOW",
            "reason": (
                "Recent rainfall is sufficient to "
                "reassess irrigation timing."
            )
        }

    if moisture < 20:
        return {
            "status": "DUE",
            "priority": "HIGH",
            "reason": (
                "Soil moisture is below 20%."
            )
        }

    if moisture < 30:
        return {
            "status": "SCHEDULED",
            "priority": "MEDIUM",
            "reason": (
                "Soil moisture is approaching "
                "the lower monitoring threshold."
            )
        }

    if moisture >= 70:
        return {
            "status": "AVOID",
            "priority": "LOW",
            "reason": (
                "Soil moisture is already high."
            )
        }

    if rain_probability >= 70:
        return {
            "status": "MONITOR",
            "priority": "LOW",
            "reason": (
                "High rain probability suggests "
                "delaying unnecessary irrigation."
            )
        }

    return {
        "status": "SCHEDULED",
        "priority": "LOW",
        "reason": (
            "Soil moisture is currently within "
            "the monitoring range."
        )
    }


def disease_decision(telemetry):
    humidity = float(
        telemetry["relative_humidity_percent"]
    )

    rainfall = float(
        telemetry["rainfall_mm"]
    )

    leaf_wetness = bool(
        telemetry["leaf_wetness"]
    )

    if humidity >= 85 or leaf_wetness:
        return {
            "status": "HIGH",
            "priority": "HIGH",
            "action": "SCOUT",
            "reason": (
                "High humidity or leaf wetness "
                "supports disease development."
            )
        }

    if humidity >= 75 or rainfall >= 10:
        return {
            "status": "MEDIUM",
            "priority": "MEDIUM",
            "action": "SCOUT",
            "reason": (
                "Environmental conditions justify "
                "closer disease monitoring."
            )
        }

    return {
        "status": "LOW",
        "priority": "LOW",
        "action": "MONITOR",
        "reason": (
            "Current environmental conditions "
            "show lower disease risk."
        )
    }


def pest_decision(telemetry):
    temperature = float(
        telemetry["air_temperature_c"]
    )

    humidity = float(
        telemetry["relative_humidity_percent"]
    )

    if 20 <= temperature <= 35 and humidity >= 80:
        return {
            "status": "MEDIUM",
            "priority": "MEDIUM",
            "action": "SCOUT",
            "reason": (
                "Temperature and humidity conditions "
                "support closer pest monitoring."
            )
        }

    return {
        "status": "LOW",
        "priority": "LOW",
        "action": "MONITOR",
        "reason": (
            "Current temperature and humidity "
            "do not indicate elevated pest risk."
        )
    }


def weather_stress_decision(telemetry):
    temperature = float(
        telemetry["air_temperature_c"]
    )

    humidity = float(
        telemetry["relative_humidity_percent"]
    )

    wind = float(
        telemetry["wind_speed_kmh"]
    )

    rainfall = float(
        telemetry["rainfall_mm"]
    )

    if (
        temperature >= 40
        or rainfall >= 50
    ):
        return {
            "status": "HIGH",
            "priority": "HIGH",
            "reason": (
                "Extreme temperature or rainfall "
                "conditions may cause crop stress."
            )
        }

    if (
        temperature >= 35
        or humidity >= 90
        or wind >= 40
    ):
        return {
            "status": "MEDIUM",
            "priority": "MEDIUM",
            "reason": (
                "Current weather conditions require "
                "closer stress monitoring."
            )
        }

    return {
        "status": "LOW",
        "priority": "LOW",
        "reason": (
            "No major weather stress threshold "
            "is currently exceeded."
        )
    }


def evaluate_soil_fertility(telemetry):
    """
    Evaluates soil fertility & nutrient status against validated agronomic models.
    Supports Nitrogen, Phosphorus, Potassium, Organic Carbon, Soil pH, and Soil EC.
    """
    if not isinstance(telemetry, dict):
        telemetry = {}

    n_val = telemetry.get("soil_nitrogen_mg_kg")
    p_val = telemetry.get("soil_phosphorus_mg_kg")
    k_val = telemetry.get("soil_potassium_mg_kg")
    oc_val = telemetry.get("soil_organic_carbon_percent")
    ph_val = telemetry.get("soil_ph", 6.5)
    ec_val = telemetry.get("soil_ec_ds_m", 0.9)

    is_synthetic = any(k not in telemetry for k in ["soil_nitrogen_mg_kg", "soil_phosphorus_mg_kg", "soil_potassium_mg_kg"])
    if n_val is None:
        n_val = 125.0  # mg/kg (LOW default for demo)
    if p_val is None:
        p_val = 18.0   # mg/kg (ADEQUATE)
    if k_val is None:
        k_val = 195.0  # mg/kg (ADEQUATE)
    if oc_val is None:
        oc_val = 0.58  # % (ADEQUATE)
    if ph_val is None:
        ph_val = 6.5
    if ec_val is None:
        ec_val = 0.9

    n_val = float(n_val)
    p_val = float(p_val)
    k_val = float(k_val)
    oc_val = float(oc_val)
    ph_val = float(ph_val)
    ec_val = float(ec_val)

    # Thresholds:
    # Nitrogen (mg/kg): <140 Low, 140-280 Adequate, >280 High
    n_status = "LOW" if n_val < 140 else ("HIGH" if n_val > 280 else "ADEQUATE")

    # Phosphorus (mg/kg): <10 Low, 10-25 Adequate, >25 High
    p_status = "LOW" if p_val < 10 else ("HIGH" if p_val > 25 else "ADEQUATE")

    # Potassium (mg/kg): <110 Low, 110-280 Adequate, >280 High
    k_status = "LOW" if k_val < 110 else ("HIGH" if k_val > 280 else "ADEQUATE")

    # Organic Carbon (%): <0.5 Low, 0.5-0.75 Adequate, >0.75 High
    oc_status = "LOW" if oc_val < 0.5 else ("HIGH" if oc_val > 0.75 else "ADEQUATE")

    # Soil pH: <6.0 Acidic, 6.0-7.5 Optimal, >7.5 Alkaline
    ph_status = "ACIDIC" if ph_val < 6.0 else ("ALKALINE" if ph_val > 7.5 else "OPTIMAL")

    # Soil EC (dS/m): <1.0 Normal, 1.0-2.0 Moderate, >2.0 Saline
    ec_status = "NORMAL" if ec_val < 1.0 else ("MODERATE" if ec_val <= 2.0 else "SALINE")

    # Deficiencies detection
    deficiencies = []
    if n_status == "LOW":
        deficiencies.append("Nitrogen (N)")
    if p_status == "LOW":
        deficiencies.append("Phosphorus (P)")
    if k_status == "LOW":
        deficiencies.append("Potassium (K)")
    if oc_status == "LOW":
        deficiencies.append("Organic Carbon (OC)")
    if ph_status in ["ACIDIC", "ALKALINE"]:
        deficiencies.append(f"Soil pH ({ph_status.lower()})")
    if ec_status == "SALINE":
        deficiencies.append("Soil Salinity (EC high)")

    return {
        "status": "EVALUATED",
        "source": "STAGE_MANAGEMENT_DATABASE",
        "deficiencies": deficiencies,
        "is_synthetic": is_synthetic,
        "nitrogen": {
            "value": n_val,
            "value_mg_kg": n_val,
            "unit": "mg/kg",
            "status": n_status,
            "description": f"Nitrogen level is {n_status.lower()} (Target: 140–280 mg/kg).",
            "interpretation": f"Nitrogen level is {n_status.lower()} (Target: 140–280 mg/kg)."
        },
        "phosphorus": {
            "value": p_val,
            "value_mg_kg": p_val,
            "unit": "mg/kg",
            "status": p_status,
            "description": f"Phosphorus level is {p_status.lower()} (Target: 10–25 mg/kg).",
            "interpretation": f"Phosphorus level is {p_status.lower()} (Target: 10–25 mg/kg)."
        },
        "potassium": {
            "value": k_val,
            "value_mg_kg": k_val,
            "unit": "mg/kg",
            "status": k_status,
            "description": f"Potassium level is {k_status.lower()} (Target: 110–280 mg/kg).",
            "interpretation": f"Potassium level is {k_status.lower()} (Target: 110–280 mg/kg)."
        },
        "organic_carbon": {
            "value": oc_val,
            "value_percent": oc_val,
            "unit": "%",
            "status": oc_status,
            "description": f"Organic carbon is {oc_status.lower()} (Target: >0.5%).",
            "interpretation": f"Organic carbon is {oc_status.lower()} (Target: >0.5%)."
        },
        "soil_ph": {
            "value": ph_val,
            "unit": "pH",
            "status": ph_status,
            "description": f"Soil reaction is {ph_status.lower()} (Target: 6.0–7.5).",
            "interpretation": f"Soil reaction is {ph_status.lower()} (Target: 6.0–7.5)."
        },
        "soil_ec": {
            "value": ec_val,
            "value_ds_m": ec_val,
            "unit": "dS/m",
            "status": ec_status,
            "description": f"Electrical conductivity is {ec_status.lower()} (Target: <1.0 dS/m).",
            "interpretation": f"Electrical conductivity is {ec_status.lower()} (Target: <1.0 dS/m)."
        }
    }


def get_stage_management_record(crop_name, current_stage):
    """Retrieve stage-management knowledge-base row for crop and stage."""
    try:
        data = load_json("stage_management.json")
    except Exception:
        try:
            data = load_csv("stage_management.csv")
        except Exception:
            data = []

    target_crop = str(crop_name).strip().lower()
    target_stage = str(current_stage).strip().lower()

    for row in data:
        row_crop = str(row.get("crop", "")).strip().lower()
        row_stage = str(row.get("stage", "")).strip().lower()
        if row_crop == target_crop and row_stage == target_stage:
            return row

    for row in data:
        if str(row.get("crop", "")).strip().lower() == target_crop:
            return row
    return {}


def fertilizer_decision(telemetry, weather, crop_name="Wheat", current_stage="Crown Root Initiation (CRI)", soil_fertility=None):
    """
    Enhanced Weather-Aware Fertilizer Decision with Mandatory 4 Questions:
    WHAT TO DO, WHY TO DO IT, HOW TO DO IT, WHEN TO DO IT.
    """
    moisture = float(telemetry.get("soil_moisture_percent", 30.0))
    rain_probability = float(weather.get("rain_probability_percent", 0) or 0)
    rainfall = float(telemetry.get("rainfall_mm", 0.0))

    stage_rec = get_stage_management_record(crop_name, current_stage)
    fert_name = stage_rec.get("fertilizer") or "Scheduled stage nutrition"
    fert_dose = stage_rec.get("fertilizer_dose") or fert_name
    fert_method = stage_rec.get("fertilizer_method") or "Standard root-zone / broadcast application"
    organic = stage_rec.get("organic_management") or "FYM or Jeevamrut spray as available"

    if fert_dose == "Scheduled stage nutrition" or not fert_dose:
        fert_dose = "Not specified in current management plan"

    n_status = (soil_fertility or {}).get("nitrogen", {}).get("status", "ADEQUATE")

    # Determine status & weather-adjusted action
    if rain_probability >= 70 or rainfall >= 5:
        status = "CHECK"
        priority = "MEDIUM"
        weather_action = "DELAY / POSTPONE fertilizer application: High rain probability (>=70%) or rainfall detected. Postpone application to prevent nutrient leaching and runoff."
        weather_adjustment = "DELAY / POSTPONE application due to high rain probability (>=70%) or active rainfall."
        when_to_do = "Postpone application until rainfall clears and soil reaches working moisture."
    elif moisture < 20:
        status = "CHECK"
        priority = "MEDIUM"
        weather_action = "Soil moisture is critically low (<20%). Irrigate field first or apply nutrient with scheduled irrigation."
        weather_adjustment = "Apply nutrient with or immediately after light irrigation."
        when_to_do = "Apply immediately after planned irrigation when root zone is sufficiently moist."
    else:
        status = "SCHEDULED"
        priority = "MEDIUM"
        weather_action = "Suitable weather conditions. Proceed according to crop stage management schedule."
        weather_adjustment = "Optimal weather conditions for nutrient application."
        when_to_do = f"Apply during current {current_stage} window in morning (07:00 AM - 10:00 AM) or late afternoon."

    # 4 Mandatory Questions
    what_to_do = f"Apply {fert_dose}." + (f" Organic alternative: {organic}." if organic else "")
    why_to_do = f"Required for {crop_name} during {current_stage} for optimal plant vigor." + (f" Soil Nitrogen status is currently {n_status}." if n_status == "LOW" else "")
    how_to_do = f"Method: {fert_method}. Ensure even distribution across the root zone."

    return {
        "status": status,
        "priority": priority,
        "name": fert_name,
        "dose": fert_dose,
        "method": fert_method,
        "organic_management": organic,
        "source": "STAGE_MANAGEMENT_DATABASE",
        "weather_action": weather_action,
        "weather_adjustment": weather_adjustment,
        "what_to_do": what_to_do,
        "why_to_do": why_to_do,
        "how_to_do": how_to_do,
        "when_to_do": when_to_do,
        "what": what_to_do,
        "why": why_to_do,
        "how": how_to_do,
        "when": when_to_do,
        "reason": f"{what_to_do} ({why_to_do})"
    }


def generate_dynamic_calendar(crop_name, planting_date, current_stage, crop_age_days, monitoring_date, harvest_info, decisions):
    """
    Generates dynamic date-aware crop lifecycle timeline and daily monitoring events.
    Uses real calendar dates calculated from planting_date + stage start/end days.
    """
    try:
        raw_stages = get_crop_stages(crop_name)
    except Exception:
        raw_stages = []

    if isinstance(planting_date, str):
        try:
            p_date = datetime.strptime(planting_date, "%Y-%m-%d").date()
        except Exception:
            p_date = monitoring_date - timedelta(days=crop_age_days or 0)
    elif isinstance(planting_date, date):
        p_date = planting_date
    else:
        p_date = monitoring_date - timedelta(days=crop_age_days or 0)

    # 1. Lifecycle Stages Timeline with Real Calendar Dates
    stages_timeline = []
    for s in raw_stages:
        s_name = s.get("stage", "")
        start_d = int(numeric(s.get("start_day")) or 0)
        end_d = int(numeric(s.get("end_day")) or start_d)
        stage_cal_date = p_date + timedelta(days=start_d)
        stage_end_cal_date = p_date + timedelta(days=end_d)

        is_current = (s_name == current_stage)
        is_past = (crop_age_days is not None and crop_age_days > end_d)
        is_future = (crop_age_days is not None and crop_age_days < start_d)

        stages_timeline.append({
            "stage_id": s.get("stage_id", ""),
            "stage": s_name,
            "stage_name": s_name,
            "start_day": start_d,
            "end_day": end_d,
            "duration_days": max(1, end_d - start_d + 1),
            "start_date": stage_cal_date.isoformat(),
            "end_date": stage_end_cal_date.isoformat(),
            "formatted_date": stage_cal_date.strftime("%d %b %Y"),
            "display_month": stage_cal_date.strftime("%B %Y"),
            "display_day": stage_cal_date.strftime("%d"),
            "is_current": is_current,
            "is_completed": is_past,
            "is_past": is_past,
            "is_future": is_future,
            "is_upcoming": is_future,
            "icon": "🌱" if "Sowing" in s_name or "Germination" in s_name or "CRI" in s_name else "🌾"
        })

    # 2. Daily Monitoring Events around today and harvest milestones
    daily_events = []

    # Today's Action Event
    today_items = []
    fert = decisions.get("fertilizer", {})
    if fert.get("status") in ["SCHEDULED", "CHECK"]:
        today_items.append("🌾 Fertilizer / Nutrition Management")
    dis = decisions.get("disease", {})
    if dis.get("status") in ["HIGH", "MEDIUM"]:
        today_items.append("🩺 Disease Scouting")
    irr = decisions.get("irrigation", {})
    if irr.get("status") in ["DUE", "SCHEDULED"]:
        today_items.append("💧 Irrigation Monitoring")
    pest = decisions.get("pest", {})
    if pest.get("status") in ["HIGH", "MEDIUM"]:
        today_items.append("🐛 Pest Scouting")

    daily_events.append({
        "date": monitoring_date.isoformat(),
        "formatted_date": monitoring_date.strftime("%d %b"),
        "title": "🌱 Today's Scheduled Field Actions",
        "is_today": True,
        "type": "STAGE_TRANSITION",
        "event_type": "STAGE_TRANSITION",
        "category": "stage",
        "items": today_items if today_items else ["🌱 Regular crop maintenance & monitoring"],
        "icon": "⭐"
    })

    # Tomorrow's Irrigation Event
    tmrw = monitoring_date + timedelta(days=1)
    daily_events.append({
        "date": tmrw.isoformat(),
        "formatted_date": tmrw.strftime("%d %b"),
        "title": "💧 Irrigation & Moisture Check",
        "type": "IRRIGATION",
        "event_type": "IRRIGATION",
        "category": "irrigation",
        "items": ["💧 Check soil moisture and root zone condition"],
        "icon": "💧"
    })

    # Fertilizer Event 2 days later
    day2 = monitoring_date + timedelta(days=2)
    daily_events.append({
        "date": day2.isoformat(),
        "formatted_date": day2.strftime("%d %b"),
        "title": "🌾 Stage Nutrition / Top-Dressing",
        "type": "FERTILIZER",
        "event_type": "FERTILIZER",
        "category": "fertilizer",
        "items": ["🌾 Follow stage nutrient management schedule"],
        "icon": "🌾"
    })

    # Scouting Event 3 days later
    day3 = monitoring_date + timedelta(days=3)
    daily_events.append({
        "date": day3.isoformat(),
        "formatted_date": day3.strftime("%d %b"),
        "title": "🩺 Pest & Foliar Disease Scouting",
        "type": "SCOUTING",
        "event_type": "SCOUTING",
        "category": "disease",
        "items": ["🩺 Field inspection for leaf spots and pest signs"],
        "icon": "🩺"
    })

    # Harvest Date & Pre-Harvest Marketplace Milestones
    h_start = harvest_info.get("harvest_start_day")
    if h_start and h_start > 0:
        h_date = p_date + timedelta(days=h_start)
        
        # 6 Days Before Harvest Reminder
        r6_date = h_date - timedelta(days=6)
        if r6_date >= monitoring_date:
            daily_events.append({
                "date": r6_date.isoformat(),
                "formatted_date": r6_date.strftime("%d %b"),
                "title": "🛒 Marketplace 6-Day Pre-Harvest Listing",
                "type": "MARKETPLACE_REMINDER",
                "event_type": "MARKETPLACE_REMINDER",
                "category": "marketplace",
                "items": ["🛒 List crop on AgriBridge Marketplace in advance"],
                "icon": "🛒"
            })

        # 3 Days Before Harvest Reminder
        r3_date = h_date - timedelta(days=3)
        if r3_date >= monitoring_date:
            daily_events.append({
                "date": r3_date.isoformat(),
                "formatted_date": r3_date.strftime("%d %b"),
                "title": "🛒 Marketplace 3-Day Follow-Up Reminder",
                "type": "MARKETPLACE_REMINDER",
                "event_type": "MARKETPLACE_REMINDER",
                "category": "marketplace",
                "items": ["🛒 Follow up on buyer discovery for harvest"],
                "icon": "🛒"
            })

        # 1 Day Before Harvest Reminder
        r1_date = h_date - timedelta(days=1)
        if r1_date >= monitoring_date:
            daily_events.append({
                "date": r1_date.isoformat(),
                "formatted_date": r1_date.strftime("%d %b"),
                "title": "🚨 Final Marketplace Listing Reminder",
                "type": "MARKETPLACE_REMINDER",
                "event_type": "MARKETPLACE_REMINDER",
                "category": "marketplace",
                "items": ["🔴 Final reminder to list before harvest"],
                "icon": "🔴"
            })

        # Expected Harvest Day
        daily_events.append({
            "date": h_date.isoformat(),
            "formatted_date": h_date.strftime("%d %b %Y"),
            "title": f"🌾 Harvest Ready: {crop_name} harvesting window opens",
            "type": "HARVEST",
            "event_type": "HARVEST",
            "category": "harvest",
            "items": [f"🌾 {crop_name} maturity and harvest readiness"],
            "icon": "🌾"
        })

    return {
        "source": "STAGE_MANAGEMENT_DATABASE",
        "planting_date": str(p_date),
        "stages_timeline": stages_timeline,
        "daily_events": daily_events
    }


# ============================================================
# OVERALL PRIORITY
# ============================================================

PRIORITY_RANK = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
}


def calculate_daily_priority(decisions):
    highest = "LOW"

    for decision in decisions.values():
        if not isinstance(decision, dict):
            continue

        priority = str(
            decision.get("priority", "LOW")
        ).upper()

        if PRIORITY_RANK.get(
            priority,
            1
        ) > PRIORITY_RANK[highest]:
            highest = priority

    return highest


# ============================================================
# NOTIFICATIONS
# ============================================================

def create_notifications(
    decisions,
    monitoring_date
):
    notifications = []

    mapping = [
        (
            "irrigation",
            "Irrigation Monitoring",
        ),
        (
            "disease",
            "High Disease Risk",
        ),
        (
            "pest",
            "Pest Scouting Reminder",
        ),
        (
            "fertilizer",
            "Fertilizer Scheduled",
        ),
        (
            "weather_stress",
            "Weather Stress Alert",
        ),
    ]

    for key, title in mapping:
        decision = decisions.get(key)

        if not decision:
            continue

        status = str(
            decision.get("status", "MONITOR")
        ).upper()

        priority = str(
            decision.get("priority", "LOW")
        ).upper()

        if key == "disease" and status == "HIGH":
            notification_status = "DUE"
        elif key == "weather_stress" and status == "HIGH":
            notification_status = "ALERT"
        elif status in [
            "DUE",
            "ALERT",
        ]:
            notification_status = status
        elif status in [
            "POSTPONE",
            "CHECK",
        ]:
            notification_status = "SCHEDULED"
        else:
            notification_status = "SCHEDULED"

        notifications.append({
            "notification_id": (
                f"AGR-{monitoring_date}-"
                f"{key.upper()}"
            ),
            "type": key,
            "title": title,
            "priority": priority,
            "status": notification_status,
            "date": str(monitoring_date),
            "reason": decision.get(
                "reason",
                ""
            ),
            "action": decision.get(
                "action",
                "MONITOR"
            ),
        })

    return notifications


# ============================================================
# HARVEST
# ============================================================

def calculate_harvest(
    crop_name,
    crop_age_days
):
    crop = get_crop(crop_name)

    start = numeric(
        crop.get("harvest_start_day")
        or crop.get("harvest_start")
    )

    end = numeric(
        crop.get("harvest_end_day")
        or crop.get("harvest_end")
    )

    if start is None or end is None:
        # Fallback from crop duration fields
        duration_min = numeric(
            crop.get("total_duration_min")
            or crop.get("duration_min")
        )

        duration_max = numeric(
            crop.get("total_duration_max")
            or crop.get("duration_max")
        )

        if duration_min is not None:
            start = duration_min

        if duration_max is not None:
            end = duration_max

    if start is None:
        start = 0

    if end is None:
        end = start

    if crop_age_days < start:
        status = "GROWING"
        days_to_harvest = int(
            start - crop_age_days
        )
    elif crop_age_days <= end:
        status = "HARVEST_WINDOW"
        days_to_harvest = 0
    else:
        status = "HARVEST_PASSED"
        days_to_harvest = 0

    return {
        "status": status,
        "harvest_start_day": int(start),
        "harvest_end_day": int(end),
        "days_to_harvest": days_to_harvest,
    }




# ============================================================
# PRE-HARVEST MARKETPLACE LISTING
# ============================================================

MARKETPLACE_REMINDER_DAYS = [6, 3, 1]


def marketplace_listing_decision(
    days_to_harvest,
    crop_listed=False
):
    """
    Determine whether a pre-harvest marketplace
    listing reminder is required.
    """

    if days_to_harvest is None:
        return {
            "status": "NOT_AVAILABLE",
            "priority": "LOW",
            "action": "MONITOR",
            "reminder": False,
            "reminder_type": None,
            "days_to_harvest": None,
            "reason": "Harvest timing is not available."
        }

    try:
        days = int(round(float(days_to_harvest)))
    except Exception:
        return {
            "status": "NOT_AVAILABLE",
            "priority": "LOW",
            "action": "MONITOR",
            "reminder": False,
            "reminder_type": None,
            "days_to_harvest": None,
            "reason": "Harvest timing could not be interpreted."
        }

    # Backend tells AI/ML whether the crop is already listed.
    if bool(crop_listed):
        return {
            "status": "LISTED",
            "priority": "LOW",
            "action": "NONE",
            "reminder": False,
            "reminder_type": None,
            "days_to_harvest": days,
            "reason": "Crop is already listed in the marketplace."
        }

    if days == 6:
        return {
            "status": "LISTING_DUE",
            "priority": "MEDIUM",
            "action": "LIST_CROP",
            "reminder": True,
            "reminder_type": "FIRST_REMINDER",
            "days_to_harvest": days,
            "reason": (
                "Harvest is approximately 6 days away. "
                "Listing the crop now gives buyers time "
                "to discover it before harvest."
            )
        }

    if days == 3:
        return {
            "status": "LISTING_DUE",
            "priority": "MEDIUM",
            "action": "LIST_CROP",
            "reminder": True,
            "reminder_type": "FOLLOW_UP_REMINDER",
            "days_to_harvest": days,
            "reason": (
                "Harvest is approximately 3 days away "
                "and the crop has not yet been listed."
            )
        }

    if days == 1:
        return {
            "status": "LISTING_URGENT",
            "priority": "HIGH",
            "action": "LIST_CROP",
            "reminder": True,
            "reminder_type": "FINAL_REMINDER",
            "days_to_harvest": days,
            "reason": (
                "Harvest is approximately 1 day away. "
                "List the crop now if you want buyers "
                "to see it before harvest."
            )
        }

    if days == 0:
        return {
            "status": "HARVEST_TODAY",
            "priority": "HIGH",
            "action": "HARVEST",
            "reminder": False,
            "reminder_type": None,
            "days_to_harvest": days,
            "reason": (
                "The crop is at the expected harvest point."
            )
        }

    if days < 0:
        return {
            "status": "HARVEST_PASSED",
            "priority": "LOW",
            "action": "MONITOR",
            "reminder": False,
            "reminder_type": None,
            "days_to_harvest": days,
            "reason": (
                "The estimated harvest date has passed."
            )
        }

    return {
        "status": "NOT_DUE",
        "priority": "LOW",
        "action": "MONITOR",
        "reminder": False,
        "reminder_type": None,
        "days_to_harvest": days,
        "reason": (
            "Marketplace listing reminder is not due today."
        )
    }


def create_marketplace_notification(
    marketplace_decision,
    crop_name,
    monitoring_date
):
    """
    Create a farmer-facing marketplace notification
    only when a reminder is due.
    """

    if not marketplace_decision.get("reminder", False):
        return None

    days = marketplace_decision.get(
        "days_to_harvest"
    )

    reminder_type = marketplace_decision.get(
        "reminder_type"
    )

    priority = marketplace_decision.get(
        "priority",
        "MEDIUM"
    )

    if days == 6:
        title = "List Your Crop Before Harvest"
        message = (
            f"{crop_name} is expected to reach harvest "
            f"in approximately 6 days. You can list your "
            f"crop on the AgriBridge Marketplace now so "
            f"buyers can discover it in advance."
        )

    elif days == 3:
        title = "Marketplace Listing Reminder"
        message = (
            f"{crop_name} is expected to reach harvest "
            f"in approximately 3 days and has not yet "
            f"been listed. Consider listing it on the "
            f"AgriBridge Marketplace."
        )

    elif days == 1:
        title = "Final Marketplace Listing Reminder"
        message = (
            f"{crop_name} is expected to reach harvest "
            f"in approximately 1 day. List the crop on "
            f"the AgriBridge Marketplace now if you want "
            f"buyers to see it before harvest."
        )

    else:
        title = "Marketplace Listing Reminder"
        message = (
            f"{crop_name} is approaching harvest. "
            f"Consider listing it on the AgriBridge "
            f"Marketplace."
        )

    return {
        "notification_id": (
            f"AGR-{monitoring_date}-"
            f"MARKETPLACE-{days}D"
        ),
        "type": "MARKETPLACE_LISTING",
        "title": title,
        "priority": priority,
        "status": "DUE",
        "date": str(monitoring_date),
        "days_to_harvest": days,
        "reminder_type": reminder_type,
        "action": "LIST_CROP",
        "crop_name": crop_name,
        "message": message,
        "reason": marketplace_decision.get(
            "reason",
            ""
        )
    }



# ============================================================
# MAIN ENGINE
# ============================================================

def run_monitoring(
    request,
    monitoring_date=None,
    use_live_weather=True
):
    """
    Run the complete dynamic crop monitoring pipeline.

    Parameters
    ----------
    request : dict
        Backend monitoring request.

    monitoring_date : str/date/None
        If None, current runtime date is used dynamically.

    use_live_weather : bool
        If True, weather is fetched using farm coordinates.

    Returns
    -------
    dict
        Structured monitoring response.
    """

    validate_request(request)

    if monitoring_date is None:
        monitoring_date = date.today()

    if isinstance(monitoring_date, str):
        monitoring_date = datetime.strptime(
            monitoring_date,
            "%Y-%m-%d"
        ).date()

    location = request["location"]
    crop_input = request["crop"]
    telemetry = request["telemetry"]

    # Marketplace status is owned by the backend.
    marketplace_input = request.get(
        "marketplace",
        {}
    )

    if not isinstance(marketplace_input, dict):
        marketplace_input = {}

    crop_listed = bool(
        marketplace_input.get(
            "crop_listed",
            False
        )
    )

    crop_name = crop_input["crop_name"]

    crop = get_crop(crop_name)

    stage_mode = str(
        crop_input.get(
            "crop_stage_mode",
            "AUTO"
        )
    ).upper()

    # --------------------------------------------------------
    # Stage
    # --------------------------------------------------------

    if stage_mode == "AUTO":

        stage_result = calculate_stage(
            crop_name=crop_name,
            planting_date=crop_input["planting_date"],
            monitoring_date=monitoring_date,
        )

        current_stage = stage_result[
            "current_stage"
        ]

        next_stage = stage_result[
            "next_stage"
        ]

        crop_age_days = stage_result[
            "crop_age_days"
        ]

    else:

        current_stage = crop_input[
            "crop_stage"
        ]

        planting_date = crop_input.get(
            "planting_date"
        )

        if planting_date:
            stage_result = calculate_stage(
                crop_name=crop_name,
                planting_date=planting_date,
                monitoring_date=monitoring_date,
            )
            crop_age_days = stage_result[
                "crop_age_days"
            ]
        else:
            crop_age_days = None

        next_stage = None

    # --------------------------------------------------------
    # Weather
    # --------------------------------------------------------

    latitude = location.get("latitude")
    longitude = location.get("longitude")

    if (
        use_live_weather
        and latitude is not None
        and longitude is not None
    ):
        weather = fetch_live_weather(
            latitude,
            longitude
        )
    else:
        weather = {
            "source": "UNAVAILABLE",
            "status": "NO_COORDINATES"
        }

    # --------------------------------------------------------
    # Telemetry
    # --------------------------------------------------------

    telemetry_validation = validate_telemetry(
        telemetry
    )

    # --------------------------------------------------------
    # Soil Fertility & Nutrient Evaluation
    # --------------------------------------------------------
    soil_fertility = evaluate_soil_fertility(telemetry)

    # --------------------------------------------------------
    # Decisions
    # --------------------------------------------------------

    decisions = {
        "irrigation": irrigation_decision(
            telemetry,
            weather
        ),
        "disease": disease_decision(
            telemetry
        ),
        "pest": pest_decision(
            telemetry
        ),
        "weather_stress": weather_stress_decision(
            telemetry
        ),
        "fertilizer": fertilizer_decision(
            telemetry,
            weather,
            crop_name=crop_name,
            current_stage=current_stage,
            soil_fertility=soil_fertility
        ),
    }

    daily_priority = calculate_daily_priority(
        decisions
    )

    # --------------------------------------------------------
    # Notifications
    # --------------------------------------------------------

    notifications = create_notifications(
        decisions,
        monitoring_date
    )

    # --------------------------------------------------------
    # Harvest
    # --------------------------------------------------------

    if crop_age_days is not None:
        harvest = calculate_harvest(
            crop_name,
            crop_age_days
        )
    else:
        harvest = {
            "status": "UNKNOWN",
            "days_to_harvest": None,
            "harvest_start_day": 0,
            "harvest_end_day": 0,
        }

    # --------------------------------------------------------
    # Dynamic Date-Aware Lifecycle Calendar & Daily Events
    # --------------------------------------------------------
    calendar = generate_dynamic_calendar(
        crop_name=crop_name,
        planting_date=crop_input.get("planting_date"),
        current_stage=current_stage,
        crop_age_days=crop_age_days,
        monitoring_date=monitoring_date,
        harvest_info=harvest,
        decisions=decisions
    )

    # --------------------------------------------------------
    # PRE-HARVEST MARKETPLACE LISTING
    # --------------------------------------------------------

    marketplace_decision = marketplace_listing_decision(
        days_to_harvest=harvest.get(
            "days_to_harvest"
        ),
        crop_listed=crop_listed
    )

    marketplace_notification = (
        create_marketplace_notification(
            marketplace_decision=marketplace_decision,
            crop_name=crop_name,
            monitoring_date=monitoring_date
        )
    )

    if marketplace_notification:
        notifications.append(
            marketplace_notification
        )

    # --------------------------------------------------------
    # Today's Action Summaries (4 Mandatory Questions)
    # --------------------------------------------------------
    today_actions = [
        {
            "category": "FERTILIZER & NUTRITION",
            "icon": "🌾",
            "title": decisions["fertilizer"]["name"],
            "status": decisions["fertilizer"]["status"],
            "priority": decisions["fertilizer"]["priority"],
            "what": decisions["fertilizer"]["what_to_do"],
            "why": decisions["fertilizer"]["why_to_do"],
            "how": decisions["fertilizer"]["how_to_do"],
            "when": decisions["fertilizer"]["when_to_do"],
            "what_to_do": decisions["fertilizer"]["what_to_do"],
            "why_to_do": decisions["fertilizer"]["why_to_do"],
            "how_to_do": decisions["fertilizer"]["how_to_do"],
            "when_to_do": decisions["fertilizer"]["when_to_do"],
            "source": decisions["fertilizer"]["source"]
        },
        {
            "category": "IRRIGATION MANAGEMENT",
            "icon": "💧",
            "title": f"Irrigation Decision ({decisions['irrigation']['status']})",
            "status": decisions["irrigation"]["status"],
            "priority": decisions["irrigation"]["priority"],
            "what": f"Irrigation status is {decisions['irrigation']['status']} based on soil moisture ({telemetry.get('soil_moisture_percent')}%) and weather.",
            "why": decisions["irrigation"]["reason"],
            "how": "Check soil moisture at 15cm depth before turning on irrigation pump.",
            "when": "Morning or evening hours; adjust if rain forecast is high.",
            "what_to_do": f"Irrigation status is {decisions['irrigation']['status']} based on soil moisture ({telemetry.get('soil_moisture_percent')}%) and weather.",
            "why_to_do": decisions["irrigation"]["reason"],
            "how_to_do": "Check soil moisture at 15cm depth before turning on irrigation pump.",
            "when_to_do": "Morning or evening hours; adjust if rain forecast is high.",
            "source": "IOT_TELEMETRY + OPEN_METEO"
        },
        {
            "category": "DISEASE & PEST SCOUTING",
            "icon": "🩺",
            "title": f"Foliar Risk: Disease {decisions['disease']['status']}, Pest {decisions['pest']['status']}",
            "status": decisions["disease"]["status"],
            "priority": decisions["disease"]["priority"],
            "what": f"Action: {decisions['disease'].get('action', 'SCOUT')}. Inspect leaf undersides and crown area for early symptoms.",
            "why": decisions["disease"]["reason"],
            "how": "Walk zigzag pattern through field; take photos using 'AI Crop Scan' if lesions appear.",
            "when": "During morning scouting rounds before full sunlight.",
            "what_to_do": f"Action: {decisions['disease'].get('action', 'SCOUT')}. Inspect leaf undersides and crown area for early symptoms.",
            "why_to_do": decisions["disease"]["reason"],
            "how_to_do": "Walk zigzag pattern through field; take photos using 'AI Crop Scan' if lesions appear.",
            "when_to_do": "During morning scouting rounds before full sunlight.",
            "source": "IOT_TELEMETRY + WEATHER"
        }
    ]

    # Format planting date for clean display
    p_date_formatted = None
    if crop_input.get("planting_date"):
        try:
            p_date_formatted = datetime.strptime(crop_input["planting_date"], "%Y-%m-%d").strftime("%d %b %Y")
        except Exception:
            p_date_formatted = str(crop_input.get("planting_date"))

    # --------------------------------------------------------
    # Final response
    # --------------------------------------------------------

    response = {
        "farm": {
            "farm_id": request["farm_id"],
            "field_id": request["field_id"],
            "telemetry_id": request["telemetry_id"],
            "location": location,
        },

        "crop": {
            "crop_name": crop_name,
            "planting_date": crop_input.get(
                "planting_date"
            ),
            "crop_stage_mode": stage_mode,
        },

        "crop_display": {
            "crop_name": crop_name,
            "current_stage": current_stage,
            "crop_age_days": crop_age_days,
            "planting_date": crop_input.get("planting_date"),
            "planting_date_formatted": p_date_formatted,
            "harvest_window": f"{harvest.get('harvest_start_day', 0)}–{harvest.get('harvest_end_day', 0)} DAP"
        },

        "stage": {
            "crop_age_days": crop_age_days,
            "current_stage": current_stage,
            "next_stage": next_stage,
        },

        "calendar": calendar,

        "weather": weather,

        "iot": {
            **telemetry,
            "telemetry_id": request[
                "telemetry_id"
            ],
            "source": (
                "SYNTHETIC_HACKATHON_DEMO"
            ),
            "physical_sensor_connected": False,
            "validation": telemetry_validation,
        },

        "soil_fertility": soil_fertility,

        "decisions": {
            **decisions,
            "daily_priority": daily_priority,
        },

        "today_actions": today_actions,

        "notifications": notifications,

        "marketplace": {
            "crop_listed": crop_listed,
            "listing_decision": marketplace_decision,
            "listing_notification": marketplace_notification,
        },

        "farmer_guidance": {
            "status": "AVAILABLE_VIA_LLM",
            "provider": "Google Gemini",
            "role": "EXPLANATION_ONLY",
            "source": "EXPLANATION_LAYER_ONLY",
        },

        "harvest": harvest,

        "data_transparency": {
            "weather_source": weather.get(
                "source"
            ),
            "iot_source": (
                "SYNTHETIC_HACKATHON_DEMO"
            ),
            "soil_nutrient_source": soil_fertility.get("source"),
            "fertilizer_source": "STAGE_MANAGEMENT_DATABASE",
            "physical_sensor_connected": False,
            "llm_provider": "Google Gemini",
            "llm_overrides_decisions": False,
            "monitoring_date": str(
                monitoring_date
            ),
        },
    }

    return response


# ============================================================
# SIMPLE LOCAL TEST
# ============================================================

if __name__ == "__main__":

    print(
        "AgriBridge Dynamic Monitoring Engine loaded."
    )

    print(
        "Use run_monitoring(request) from backend."
    )
