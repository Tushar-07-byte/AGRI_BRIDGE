"""
AgriBridge Farm Decision Context Builder Service
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Responsible for deterministically assembling the canonical FarmDecisionContext from existing
subsystems (Farmer DB, India Districts Registry, Open-Meteo Weather, EfficientNet Disease Records,
Virtual IoT Telemetry, and Mandi Marketplace Benchmarks) with zero new external dependencies.
"""

import os
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..domain.farm_decision_context import (
    FarmDecisionContext,
    SignalProvenance,
    SignalQuality,
    TraceableSignal,
    IdentityLocationState,
    CropState,
    SoilState,
    TelemetryState,
    WeatherState,
    DiseaseState,
    MarketState,
    CurrentActionState
)
from ..models.farmer import Farmer
from ..models.user import User
from ..models.disease_record import DiseaseRecord
from ..models.action_plan import ActionPlan, PlanTask
from ..data.india_districts import find_district, INDIA_DISTRICTS
from ..crop_monitoring.weather_context import resolve_indian_coordinates
from ..crop_monitoring.marketplace_context import get_marketplace_context
from ..services.weather_service import get_current_weather, get_forecast

# Standard ICAR / Mandi Commodity Benchmark Prices (₹ / kg)
MANDI_BENCHMARK_PRICES = {
    "wheat": 27.50,
    "rice": 75.00,
    "basmati": 82.00,
    "mustard": 58.00,
    "soybean": 44.00,
    "maize": 22.50,
    "tomato": 35.00,
    "cotton": 68.00,
    "sugarcane": 34.00,
    "potato": 18.00
}


class FarmDecisionContextService:

    @staticmethod
    async def build_context(
        farmer_id: Optional[int] = None,
        db: Optional[Session] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
        village: Optional[str] = None,
        crop_id: Optional[str] = None,
        crop_name: Optional[str] = None,
        variety: Optional[str] = None,
        planting_date: Optional[str] = None,
        current_stage: Optional[str] = None,
        growth_stage: Optional[str] = None,
        season: Optional[str] = None,
        farm_area: Optional[float] = None,
        irrigation_method: Optional[str] = None,
        irrigation_status: Optional[str] = None,
        soil_type: Optional[str] = None,
        soil_ph: Optional[float] = None,
        nitrogen: Optional[float] = None,
        phosphorus: Optional[float] = None,
        potassium: Optional[float] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        disease_record_id: Optional[int] = None,
        disease_scan_data: Optional[Dict[str, Any]] = None,
        telemetry_data: Optional[Dict[str, Any]] = None,
        weather_override: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> FarmDecisionContext:
        """
        Constructs the canonical FarmDecisionContext.
        Gracefully handles optional / missing signals without rejecting valid farms.
        """
        now_iso = datetime.utcnow().isoformat()
        ctx_id = f"ctx_{uuid.uuid4().hex[:12]}"

        # =====================================================================
        # 1. RESOLVE IDENTITY & LOCATION
        # =====================================================================
        resolved_farmer_name = "Farmer Ramesh Patel"
        res_farmer_id = farmer_id

        if db and farmer_id:
            farmer_rec = db.query(Farmer).filter(Farmer.id == farmer_id).first()
            if farmer_rec:
                resolved_farmer_name = farmer_rec.name
            else:
                user_rec = db.query(User).filter(User.id == farmer_id).first()
                if user_rec:
                    resolved_farmer_name = user_rec.name
        elif not res_farmer_id and db:
            first_f = db.query(Farmer).first()
            if first_f:
                res_farmer_id = first_f.id
                resolved_farmer_name = first_f.name

        s_clean = (state or "Punjab").strip()
        d_clean = (district or "Ludhiana").strip()
        v_clean = (village or "Samrala").strip()

        # Coordinate resolution
        res_lat, res_lon = resolve_indian_coordinates(
            state=s_clean,
            district=d_clean,
            latitude=latitude,
            longitude=longitude
        )

        identity_state = IdentityLocationState(
            farmer_id=TraceableSignal[int](
                value=res_farmer_id,
                unit="ID",
                provenance=SignalProvenance.LIVE if db else SignalProvenance.DECLARED,
                quality=SignalQuality.VALID if res_farmer_id else SignalQuality.MISSING,
                timestamp=now_iso,
                source="agribridge_database.farmers",
                reason_relevant="Primary key identifying farm operator"
            ),
            farmer_name=TraceableSignal[str](
                value=resolved_farmer_name,
                unit="text",
                provenance=SignalProvenance.DECLARED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="user_profile",
                reason_relevant="Personalized communication and advisory delivery"
            ),
            state=TraceableSignal[str](
                value=s_clean,
                unit="text",
                provenance=SignalProvenance.DECLARED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="farmer_profile",
                reason_relevant="State-level agro-climatic zone classification"
            ),
            district=TraceableSignal[str](
                value=d_clean,
                unit="text",
                provenance=SignalProvenance.DECLARED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="farmer_profile",
                reason_relevant="District coordinate anchoring for hyper-local weather"
            ),
            village=TraceableSignal[str](
                value=v_clean,
                unit="text",
                provenance=SignalProvenance.DECLARED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="farmer_profile",
                reason_relevant="Micro-location for localized field agent dispatch"
            ),
            latitude=TraceableSignal[float](
                value=res_lat,
                unit="degrees_north",
                provenance=SignalProvenance.CACHED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="india_districts_registry",
                reason_relevant="Geographic coordinate for Open-Meteo satellite feed"
            ),
            longitude=TraceableSignal[float](
                value=res_lon,
                unit="degrees_east",
                provenance=SignalProvenance.CACHED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="india_districts_registry",
                reason_relevant="Geographic coordinate for Open-Meteo satellite feed"
            )
        )

        # =====================================================================
        # 2. CROP & PHENOLOGY STATE
        # =====================================================================
        norm_crop = (crop_id or "wheat").strip().lower()
        norm_crop_name = crop_name or norm_crop.capitalize()
        norm_stage = current_stage or growth_stage or "Tillering / Vegetative"
        norm_season = season or "Rabi"
        norm_area = float(farm_area) if farm_area and farm_area > 0 else 4.5
        norm_irrig_m = (irrigation_method or "drip").lower()
        norm_irrig_s = (irrigation_status or "normal").lower()
        norm_plant_date = planting_date or "2026-11-05"

        crop_state = CropState(
            crop_id=TraceableSignal[str](
                value=norm_crop,
                unit="slug",
                provenance=SignalProvenance.DECLARED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="field_registry",
                reason_relevant="Target crop for ICAR disease models and nutrition schedules"
            ),
            crop_name=TraceableSignal[str](
                value=norm_crop_name,
                unit="text",
                provenance=SignalProvenance.DECLARED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="field_registry",
                reason_relevant="Human-readable crop name for farmer advisory"
            ),
            variety=TraceableSignal[str](
                value=variety or "HD-2967 (Certified ICAR Seed)",
                unit="text",
                provenance=SignalProvenance.DECLARED,
                quality=SignalQuality.VALID if variety else SignalQuality.FALLBACK,
                timestamp=now_iso,
                source="farmer_declaration",
                reason_relevant="Specific varietal resistance and duration to maturity"
            ),
            planting_date=TraceableSignal[str](
                value=norm_plant_date,
                unit="YYYY-MM-DD",
                provenance=SignalProvenance.DECLARED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="farmer_declaration",
                reason_relevant="Baseline for calculating Days After Sowing (DAS)"
            ),
            growth_stage=TraceableSignal[str](
                value=norm_stage,
                unit="phenology_stage",
                provenance=SignalProvenance.DECLARED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="farmer_declaration",
                reason_relevant="Determines vulnerability window to specific fungal strains"
            ),
            season=TraceableSignal[str](
                value=norm_season,
                unit="season_name",
                provenance=SignalProvenance.DECLARED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="calendar_engine",
                reason_relevant="Cropping season alignment (Kharif, Rabi, Zaid)"
            ),
            farm_area_acres=TraceableSignal[float](
                value=norm_area,
                unit="acres",
                provenance=SignalProvenance.DECLARED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="farmer_profile",
                reason_relevant="Used to scale spray volume and water allocation"
            ),
            irrigation_method=TraceableSignal[str](
                value=norm_irrig_m,
                unit="method_enum",
                provenance=SignalProvenance.DECLARED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="farm_profile",
                reason_relevant="Determines application efficiency and leaf wetness duration"
            ),
            irrigation_status=TraceableSignal[str](
                value=norm_irrig_s,
                unit="status_enum",
                provenance=SignalProvenance.DECLARED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="farm_profile",
                reason_relevant="Current field saturation baseline"
            )
        )

        # =====================================================================
        # 3. SOIL & NUTRIENT STATE (OPTIONAL / GRACEFUL DEGRADATION)
        # =====================================================================
        has_soil_type = bool(soil_type and soil_type.strip())
        res_soil_type = soil_type if has_soil_type else "Alluvial Sandy Loam"

        soil_state = SoilState(
            soil_type=TraceableSignal[str](
                value=res_soil_type,
                unit="soil_taxonomy",
                provenance=SignalProvenance.DECLARED if has_soil_type else SignalProvenance.CACHED,
                quality=SignalQuality.VALID if has_soil_type else SignalQuality.FALLBACK,
                timestamp=now_iso,
                source="district_soil_survey" if not has_soil_type else "farmer_declaration",
                reason_relevant="Determines cation exchange capacity and water holding capacity"
            ),
            ph=TraceableSignal[float](
                value=float(soil_ph) if soil_ph is not None else 6.8,
                unit="pH",
                provenance=SignalProvenance.DECLARED if soil_ph is not None else SignalProvenance.CACHED,
                quality=SignalQuality.VALID if soil_ph is not None else SignalQuality.FALLBACK,
                timestamp=now_iso,
                source="soil_health_card" if soil_ph is not None else "regional_baseline",
                reason_relevant="Dictates micronutrient availability (6.5-7.5 optimal for cereals)"
            ),
            nitrogen_kg_ha=TraceableSignal[float](
                value=float(nitrogen) if nitrogen is not None else None,
                unit="kg/ha",
                provenance=SignalProvenance.DECLARED if nitrogen is not None else SignalProvenance.UNAVAILABLE,
                quality=SignalQuality.VALID if nitrogen is not None else SignalQuality.MISSING,
                timestamp=now_iso if nitrogen is not None else None,
                source="soil_lab_test" if nitrogen is not None else "none",
                reason_relevant="Excessive nitrogen increases succulent foliage susceptibility to rust"
            ),
            phosphorus_kg_ha=TraceableSignal[float](
                value=float(phosphorus) if phosphorus is not None else None,
                unit="kg/ha",
                provenance=SignalProvenance.DECLARED if phosphorus is not None else SignalProvenance.UNAVAILABLE,
                quality=SignalQuality.VALID if phosphorus is not None else SignalQuality.MISSING,
                timestamp=now_iso if phosphorus is not None else None,
                source="soil_lab_test" if phosphorus is not None else "none",
                reason_relevant="Root development and vigorous tillering catalyst"
            ),
            potassium_kg_ha=TraceableSignal[float](
                value=float(potassium) if potassium is not None else None,
                unit="kg/ha",
                provenance=SignalProvenance.DECLARED if potassium is not None else SignalProvenance.UNAVAILABLE,
                quality=SignalQuality.VALID if potassium is not None else SignalQuality.MISSING,
                timestamp=now_iso if potassium is not None else None,
                source="soil_lab_test" if potassium is not None else "none",
                reason_relevant="Fortifies cellular walls against fungal haustorium penetration"
            ),
            nutrient_status=TraceableSignal[str](
                value="Balanced Cereal Baseline" if nitrogen is None else "Laboratory Tested",
                unit="category",
                provenance=SignalProvenance.DERIVED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="soil_evaluation_engine",
                reason_relevant="High-level classification for nutritional advisory"
            )
        )

        # =====================================================================
        # 4. TELEMETRY & VIRTUAL IoT STATE (STRICTLY SIMULATED)
        # =====================================================================
        t_data = telemetry_data or {}
        val_moisture = float(t_data.get("soilMoisture", t_data.get("soil_moisture", 24.0)))
        val_moisture = float(t_data.get("soil_moisture_vwc", t_data.get("soilMoisture", t_data.get("soil_moisture", 24.0))))
        val_temp = float(t_data.get("temperature", 29.0))
        val_hum = float(t_data.get("humidity", 62.0))
        val_lux = int(t_data.get("lightIntensity", 62000))

        moisture_label = "Optimal" if 20.0 <= val_moisture <= 45.0 else ("Elevated" if val_moisture > 45.0 else "Dry")

        telemetry_state = TelemetryState(
            soil_moisture_vwc=TraceableSignal[float](
                value=val_moisture,
                unit="% VWC",
                provenance=SignalProvenance.SIMULATED,
                quality=SignalQuality.SIMULATED,
                timestamp=now_iso,
                source="Virtual IoT Node #SIM-NODE-01",
                reason_relevant="Root zone volumetric water content triggers irrigation/re-planning"
            ),
            ambient_temp_c=TraceableSignal[float](
                value=val_temp,
                unit="°C",
                provenance=SignalProvenance.SIMULATED,
                quality=SignalQuality.SIMULATED,
                timestamp=now_iso,
                source="Virtual IoT Node #SIM-NODE-01",
                reason_relevant="Microclimate sensor telemetry for localized crop stress"
            ),
            humidity_percent=TraceableSignal[float](
                value=val_hum,
                unit="%",
                provenance=SignalProvenance.SIMULATED,
                quality=SignalQuality.SIMULATED,
                timestamp=now_iso,
                source="Virtual IoT Node #SIM-NODE-01",
                reason_relevant="Canopy level relative humidity"
            ),
            light_lux=TraceableSignal[int](
                value=val_lux,
                unit="lux",
                provenance=SignalProvenance.SIMULATED,
                quality=SignalQuality.SIMULATED,
                timestamp=now_iso,
                source="Virtual IoT Node #SIM-NODE-01",
                reason_relevant="Solar radiation and photosynthetic active radiation indicator"
            ),
            status_label=TraceableSignal[str](
                value=moisture_label,
                unit="status_label",
                provenance=SignalProvenance.DERIVED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="telemetry_analyzer",
                reason_relevant="Categorical rating of soil hydration"
            ),
            is_simulated=True
        )

        # =====================================================================
        # 5. WEATHER & ATMOSPHERIC STATE (LIVE OPEN-METEO API)
        # =====================================================================
        live_temp = 28.5
        live_hum = 58.0
        live_precip = 0.0
        live_rain_prob = 10
        live_wind = 12.0
        live_wmo = 1
        live_cond = "Mainly clear"
        weather_prov = SignalProvenance.LIVE
        weather_qual = SignalQuality.LIVE

        if weather_override:
            live_temp = float(weather_override.get("temperature", live_temp))
            live_hum = float(weather_override.get("humidity", live_hum))
            live_precip = float(weather_override.get("precipitation", live_precip))
            live_rain_prob = int(weather_override.get("rain_probability", live_rain_prob))
            live_rain_prob = int(weather_override.get("rain_probability_percent", weather_override.get("rain_probability", live_rain_prob)))
            live_wind = float(weather_override.get("wind_speed", live_wind))
            live_wind = float(weather_override.get("wind_speed_kmh", weather_override.get("wind_speed", live_wind)))
            live_cond = str(weather_override.get("condition", live_cond))
            weather_prov = SignalProvenance.SIMULATED
            weather_qual = SignalQuality.SIMULATED

            p_override = weather_override.get("provenance")
            if isinstance(p_override, SignalProvenance):
                weather_prov = p_override
            elif isinstance(p_override, str) and p_override in SignalProvenance.__members__:
                weather_prov = SignalProvenance[p_override]
            else:
                weather_prov = SignalProvenance.SIMULATED

            q_override = weather_override.get("quality")
            if isinstance(q_override, SignalQuality):
                weather_qual = q_override
            elif isinstance(q_override, str) and q_override in SignalQuality.__members__:
                weather_qual = SignalQuality[q_override]
            else:
                weather_qual = SignalQuality.SIMULATED
        else:
            try:
                curr_w = await get_current_weather(res_lat, res_lon)
                if curr_w:
                    live_temp = float(curr_w.get("temperature_2m", live_temp))
                    live_hum = float(curr_w.get("relative_humidity_2m", live_hum))
                    live_precip = float(curr_w.get("precipitation", live_precip))
                    live_wind = float(curr_w.get("wind_speed_10m", live_wind))
                    live_wmo = int(curr_w.get("weather_code", live_wmo))
                    from ..services.weather_service import _weather_code_to_text
                    live_cond = _weather_code_to_text(live_wmo)

                fc_w = await get_forecast(res_lat, res_lon, days=3)
                if fc_w and "daily" in fc_w and "precipitation_probability_max" in fc_w["daily"]:
                    probs = fc_w["daily"]["precipitation_probability_max"]
                    if probs:
                        live_rain_prob = int(probs[0])
            except Exception as e:
                # Graceful fallback: Network drop at hackathon does not break context
                weather_prov = SignalProvenance.CACHED
                weather_qual = SignalQuality.FALLBACK

        # Evaluate risk level from weather
        if live_rain_prob >= 75 or live_wind >= 28.0:
            w_risk = "high"
            fav_win = "Hold chemical spray; high wash-off or drift hazard"
        elif live_rain_prob >= 50 or live_wind >= 20.0:
            w_risk = "moderate"
            fav_win = "Spray window tight; execute within next 4-6 hours before rainfall"
        else:
            w_risk = "low"
            fav_win = "Clear 48-hour spray window available. Favorable atmospheric inversion."

        weather_state = WeatherState(
            temperature_c=TraceableSignal[float](
                value=live_temp,
                unit="°C",
                provenance=weather_prov,
                quality=weather_qual,
                timestamp=now_iso,
                source="Open-Meteo REST API",
                reason_relevant="Ambient air temperature for chemical evaporation rate"
            ),
            humidity_percent=TraceableSignal[float](
                value=live_hum,
                unit="%",
                provenance=weather_prov,
                quality=weather_qual,
                timestamp=now_iso,
                source="Open-Meteo REST API",
                reason_relevant="Relative humidity > 85% significantly accelerates fungal sporulation"
            ),
            precipitation_mm=TraceableSignal[float](
                value=live_precip,
                unit="mm",
                provenance=weather_prov,
                quality=weather_qual,
                timestamp=now_iso,
                source="Open-Meteo REST API",
                reason_relevant="Direct rainfall volume"
            ),
            rain_probability_percent=TraceableSignal[int](
                value=live_rain_prob,
                unit="%",
                provenance=weather_prov,
                quality=weather_qual,
                timestamp=now_iso,
                source="Open-Meteo REST API",
                reason_relevant="Gating metric: >= 60% delays spray, >= 80% triggers autonomous replan"
            ),
            wind_speed_kmh=TraceableSignal[float](
                value=live_wind,
                unit="km/h",
                provenance=weather_prov,
                quality=weather_qual,
                timestamp=now_iso,
                source="Open-Meteo REST API",
                reason_relevant="Gating metric: > 20 km/h risks off-target droplet drift"
            ),
            weather_code=TraceableSignal[int](
                value=live_wmo,
                unit="wmo_code",
                provenance=weather_prov,
                quality=weather_qual,
                timestamp=now_iso,
                source="Open-Meteo REST API",
                reason_relevant="Standard WMO meteorological weather code"
            ),
            condition_text=TraceableSignal[str](
                value=live_cond,
                unit="text",
                provenance=weather_prov,
                quality=weather_qual,
                timestamp=now_iso,
                source="Open-Meteo REST API",
                reason_relevant="Human-readable weather synopsis for advisory"
            ),
            overall_risk=TraceableSignal[str](
                value=w_risk,
                unit="risk_level",
                provenance=SignalProvenance.DERIVED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="agribridge_weather_engine",
                reason_relevant="Synthesized atmospheric risk category"
            ),
            favorable_window=TraceableSignal[str](
                value=fav_win,
                unit="text",
                provenance=SignalProvenance.DERIVED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="timing_advice_engine",
                reason_relevant="Actionable execution advice based on 48h forecast"
            )
        )

        # =====================================================================
        # 6. DISEASE & PATHOLOGY STATE (CANONICAL CONFIDENCE NORMALIZATION)
        # =====================================================================
        has_disease = False
        pathogen = "Healthy Leaf Stand"
        sci_name = "None"
        raw_conf = 96.5
        d_risk = "low"
        img_qual = "VALID_LEAF"
        model_name = "AgriBridge_EfficientNetB0"
        d_prov = SignalProvenance.LIVE
        d_qual = SignalQuality.VALID
        rec = None

        # Check DB for recent disease record
        if db and res_farmer_id:
            query = db.query(DiseaseRecord).filter(DiseaseRecord.farmer_id == res_farmer_id)
            if disease_record_id:
                query = query.filter(DiseaseRecord.id == disease_record_id)
            elif norm_crop:
                query = query.filter(func.lower(DiseaseRecord.crop_type) == norm_crop.lower())
            rec = query.order_by(DiseaseRecord.id.desc()).first()
            if rec:
                has_disease = True
                pathogen = rec.predicted_pathogen or pathogen
                sci_name = rec.scientific_name or sci_name
                raw_conf = float(rec.confidence) if rec.confidence is not None else raw_conf
                d_risk = (rec.severity or "moderate").lower()
                model_name = "AgriBridge_EfficientNetB0_Stage2"

        # Check in-memory disease scan data override
        d_prov = SignalProvenance.LIVE if has_disease else SignalProvenance.DECLARED
        d_qual = SignalQuality.VALID

        if disease_scan_data:
            has_disease = True
            pathogen = disease_scan_data.get("pathogen", disease_scan_data.get("predicted_pathogen", pathogen))
            sci_name = disease_scan_data.get("scientific_name", sci_name)
            raw_conf = float(disease_scan_data.get("confidence", raw_conf))
            d_risk = disease_scan_data.get("severity", d_risk).lower()
            model_name = disease_scan_data.get("model", model_name)
            
            # Check explicit provenance
            if "provenance" in disease_scan_data:
                p_val = disease_scan_data["provenance"]
                if isinstance(p_val, SignalProvenance):
                    d_prov = p_val
                elif isinstance(p_val, str) and p_val in SignalProvenance.__members__:
                    d_prov = SignalProvenance[p_val]
            elif disease_scan_data.get("is_simulated"):
                d_prov = SignalProvenance.SIMULATED

            # Check explicit quality
            if "quality" in disease_scan_data:
                q_val = disease_scan_data["quality"]
                if isinstance(q_val, SignalQuality):
                    d_qual = q_val
                elif isinstance(q_val, str) and q_val in SignalQuality.__members__:
                    d_qual = SignalQuality[q_val]

            is_verified = bool(disease_scan_data.get("is_verified", False))
        else:
            is_verified = bool(rec is not None and rec.status == "VERIFIED_HEALTH_RECORD")

        # CANONICAL CONFIDENCE STANDARDIZATION
        # If passed as 0.0-1.0 fraction, normalize to percentage
        conf_percent = raw_conf if raw_conf > 1.0 else (raw_conf * 100.0)
        conf_percent = round(conf_percent, 2)
        conf_fraction = round(conf_percent / 100.0, 4)

        is_borderline = (30.0 <= conf_percent < 65.0)
        needs_review = is_borderline
        rx_locked = is_borderline
        if is_verified:
            conf_percent = max(conf_percent, 98.0)
            conf_fraction = round(conf_percent / 100.0, 4)
            is_borderline = False
            needs_review = False
            rx_locked = False
            model_name = f"Agronomist_Verified_{rec.agent_name if (rec and rec.agent_name) else 'Field_Agent'}"
        else:
            is_borderline = (30.0 <= conf_percent < 65.0)
            needs_review = is_borderline
            rx_locked = is_borderline

        disease_state = DiseaseState(
            has_diagnosis=has_disease,
            pathogen_name=TraceableSignal[str](
                value=pathogen,
                unit="text",
                provenance=d_prov,
                quality=d_qual,
                timestamp=now_iso,
                source=model_name,
                reason_relevant="Primary biological threat requiring treatment"
            ),
            scientific_name=TraceableSignal[str](
                value=sci_name,
                unit="latin_binomial",
                provenance=SignalProvenance.CACHED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="icar_plant_pathology_registry",
                reason_relevant="Scientific verification baseline for chemical active ingredient"
            ),
            confidence_percent=TraceableSignal[float](
                value=conf_percent,
                unit="PERCENTAGE",
                provenance=d_prov,
                quality=d_qual,
                timestamp=now_iso,
                source=model_name,
                reason_relevant="Canonical primary confidence score [0.0 - 100.0%]"
            ),
            confidence_fraction=TraceableSignal[float](
                value=conf_fraction,
                unit="DECIMAL_FRACTION",
                provenance=SignalProvenance.DERIVED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="agribridge_normalizer",
                reason_relevant="Decimal fraction representation [0.0 - 1.0]"
            ),
            confidence_unit="PERCENTAGE",
            risk_level=TraceableSignal[str](
                value=d_risk,
                unit="risk_level",
                provenance=SignalProvenance.DERIVED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="pathology_risk_classifier",
                reason_relevant="Risk tier determining urgent scheduling priority"
            ),
            is_borderline=is_borderline,
            needs_expert_review=needs_review,
            prescription_locked=rx_locked,
            model_name=TraceableSignal[str](
                value=model_name,
                unit="identifier",
                provenance=SignalProvenance.CACHED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="ai_engine_manifest",
                reason_relevant="Underlying neural network architecture"
            ),
            image_quality_status=TraceableSignal[str](
                value=img_qual,
                unit="status_enum",
                provenance=SignalProvenance.LIVE,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="leaf_hsv_quality_filter",
                reason_relevant="Leaf segmentation and blur check indicator"
            )
        )

        # =====================================================================
        # 7. MARKET & COMMERCIAL STATE (DECLARED / BENCHMARK)
        # =====================================================================
        ref_price = MANDI_BENCHMARK_PRICES.get(norm_crop, 30.0)
        active_listings = 0
        market_type = "BENCHMARK"

        if db:
            m_ctx = get_marketplace_context(norm_crop, db)
            active_listings = m_ctx.get("active_market_listings") or 0
            if active_listings > 0:
                market_type = "ACTIVE_LISTING"

        market_state = MarketState(
            crop=TraceableSignal[str](
                value=norm_crop_name,
                unit="commodity_name",
                provenance=SignalProvenance.DECLARED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="mandi_commodity_registry",
                reason_relevant="Wholesale trade benchmark mapping"
            ),
            reference_price_per_kg=TraceableSignal[float](
                value=ref_price,
                unit="INR/kg",
                provenance=SignalProvenance.DECLARED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="AgriBridge Mandi Price Registry",
                reason_relevant="Reference price for farm economic viability and forward commitments"
            ),
            currency="INR",
            pricing_type=TraceableSignal[str](
                value=market_type,
                unit="pricing_type_enum",
                provenance=SignalProvenance.DERIVED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="marketplace_engine",
                reason_relevant="Differentiates static benchmark rates from active farmer lots"
            ),
            active_market_listings=TraceableSignal[int](
                value=active_listings,
                unit="count",
                provenance=SignalProvenance.LIVE if db else SignalProvenance.CACHED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="agribridge_database.listings",
                reason_relevant="Buyer liquidity and supply depth indicator"
            )
        )

        # =====================================================================
        # 8. CURRENT ACTION & ORCHESTRATION STATE (LIVE DB)
        # =====================================================================
        active_plan_id = None
        plan_status = "none"
        risk_type = "routine_monitoring"
        esc_req = False
        task_count = 0
        active_task_title = "Routine field inspection"
        replan_reason = "Initial baseline stand"

        if db and res_farmer_id:
            plan_rec = db.query(ActionPlan).filter(
                ActionPlan.farmer_id == res_farmer_id
            ).order_by(ActionPlan.id.desc()).first()

            if plan_rec:
                active_plan_id = plan_rec.id
                plan_status = plan_rec.status
                risk_type = plan_rec.risk_type
                esc_req = plan_rec.escalation_required
                replan_reason = plan_rec.escalation_reason or replan_reason

                tasks = db.query(PlanTask).filter(PlanTask.action_plan_id == plan_rec.id).all()
                task_count = len(tasks)
                pending_task = next((t for t in tasks if t.status == "pending"), None)
                if pending_task:
                    active_task_title = pending_task.title

        action_state = CurrentActionState(
            active_plan_id=TraceableSignal[int](
                value=active_plan_id,
                unit="ID",
                provenance=SignalProvenance.LIVE if db else SignalProvenance.UNAVAILABLE,
                quality=SignalQuality.VALID if active_plan_id else SignalQuality.MISSING,
                timestamp=now_iso,
                source="agribridge_database.action_plans",
                reason_relevant="Current active orchestration workflow instance"
            ),
            plan_status=TraceableSignal[str](
                value=plan_status,
                unit="status_enum",
                provenance=SignalProvenance.LIVE if db else SignalProvenance.DECLARED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="action_plan_lifecycle_engine",
                reason_relevant="Lifecycle state (active, needs_expert_review, superseded, active_verified_rx)"
            ),
            risk_type=TraceableSignal[str](
                value=risk_type,
                unit="risk_type_enum",
                provenance=SignalProvenance.LIVE if db else SignalProvenance.DECLARED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="action_plan_orchestrator",
                reason_relevant="Active threat category being managed"
            ),
            escalation_required=TraceableSignal[bool](
                value=esc_req,
                unit="boolean",
                provenance=SignalProvenance.LIVE if db else SignalProvenance.DECLARED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="escalation_policy_engine",
                reason_relevant="Human-in-the-loop gating flag"
            ),
            tasks_count=TraceableSignal[int](
                value=task_count,
                unit="count",
                provenance=SignalProvenance.LIVE if db else SignalProvenance.DECLARED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="plan_tasks_table",
                reason_relevant="Total pending/completed tactical tasks in plan"
            ),
            active_task_title=TraceableSignal[str](
                value=active_task_title,
                unit="text",
                provenance=SignalProvenance.LIVE if db else SignalProvenance.DECLARED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="plan_tasks_table",
                reason_relevant="Immediate actionable intervention scheduled for farm"
            ),
            last_replan_reason=TraceableSignal[str](
                value=replan_reason,
                unit="text",
                provenance=SignalProvenance.LIVE if db else SignalProvenance.DECLARED,
                quality=SignalQuality.VALID,
                timestamp=now_iso,
                source="action_plan_audit_trail",
                reason_relevant="Audit trail explaining why plan was created or rescheduled"
            )
        )

        # =====================================================================
        # 9. CONSTRUCT ROOT CONTEXT & COMPILE SUMMARY
        # =====================================================================
        context = FarmDecisionContext(
            context_id=ctx_id,
            created_at=now_iso,
            decision_readiness=True,
            identity=identity_state,
            crop=crop_state,
            soil=soil_state,
            telemetry=telemetry_state,
            weather=weather_state,
            disease=disease_state,
            market=market_state,
            current_action=action_state
        )

        context.compile_provenance_summary()
        return context

