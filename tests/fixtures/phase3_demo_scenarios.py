"""
AgriBridge Phase 3 Deterministic Demo Scenarios
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Provides 4 fully deterministic FarmDecisionContext fixtures demonstrating:
1. SCENARIO 1 — Borderline Clinical Disease (51.69% -> Expert Review, Prescription Locked)
2. SCENARIO 2 — High-Confidence Disease + Unfavorable Weather (88.5% disease + 85% rain -> Spray Deferred)
3. SCENARIO 3 — Missing Laboratory NPK (Disease/weather active, NPK insufficient_data, zero fabricated fertilizer)
4. SCENARIO 4 — Simulated Telemetry (Soil moisture 32.5% VWC -> Irrigation recommended, provenance=SIMULATED)
"""

from datetime import datetime
from app.domain.farm_decision_context import (
    CropState,
    CurrentActionState,
    DiseaseState,
    FarmDecisionContext,
    IdentityLocationState,
    MarketState,
    SignalProvenance,
    SignalQuality,
    SoilState,
    TelemetryState,
    TraceableSignal,
    WeatherState,
)


def create_scenario_1_borderline_disease() -> FarmDecisionContext:
    """
    Scenario 1: Borderline Clinical Disease
    Farmer: Balwinder Singh (Wheat, Ludhiana, Punjab)
    Disease: Yellow Rust detected with 51.69% confidence (Borderline [30%, 65%))
    Weather: Favorable (15% rain, 9.5 km/h wind)
    Telemetry: 48.0% VWC (Optimal)
    NPK: 110 kg/ha N (Balanced)
    """
    now = datetime.utcnow().isoformat()
    return FarmDecisionContext(
        context_id="SCENARIO-01-BORDERLINE-DISEASE",
        created_at=now,
        decision_readiness=True,
        identity=IdentityLocationState(
            farmer_id=TraceableSignal[int](value=1, unit="id", provenance=SignalProvenance.DECLARED, quality=SignalQuality.VALID, source="farmer_profile"),
            farmer_name=TraceableSignal[str](value="Balwinder Singh", unit="text", provenance=SignalProvenance.DECLARED, quality=SignalQuality.VALID, source="farmer_profile"),
            state=TraceableSignal[str](value="Punjab", unit="text", provenance=SignalProvenance.DECLARED, quality=SignalQuality.VALID, source="farmer_profile"),
            district=TraceableSignal[str](value="Ludhiana", unit="text", provenance=SignalProvenance.DECLARED, quality=SignalQuality.VALID, source="farmer_profile"),
            village=TraceableSignal[str](value="Samrala", unit="text", provenance=SignalProvenance.DECLARED, quality=SignalQuality.VALID, source="farmer_profile"),
            latitude=TraceableSignal[float](value=30.9010, unit="degrees", provenance=SignalProvenance.CACHED, quality=SignalQuality.VALID, source="india_districts"),
            longitude=TraceableSignal[float](value=75.8573, unit="degrees", provenance=SignalProvenance.CACHED, quality=SignalQuality.VALID, source="india_districts"),
        ),
        crop=CropState(
            crop_id=TraceableSignal[str](value="wheat", unit="slug", provenance=SignalProvenance.DECLARED, quality=SignalQuality.VALID, source="field_registry"),
            crop_name=TraceableSignal[str](value="Wheat", unit="text", provenance=SignalProvenance.DECLARED, quality=SignalQuality.VALID, source="field_registry"),
            variety=TraceableSignal[str](value="HD-2967", unit="text", provenance=SignalProvenance.DECLARED, quality=SignalQuality.VALID, source="farmer_profile"),
            planting_date=TraceableSignal[str](value="2026-11-05", unit="YYYY-MM-DD", provenance=SignalProvenance.DECLARED, quality=SignalQuality.VALID, source="farmer_profile"),
            growth_stage=TraceableSignal[str](value="Tillering", unit="phenology_stage", provenance=SignalProvenance.DECLARED, quality=SignalQuality.VALID, source="farmer_profile"),
            season=TraceableSignal[str](value="Rabi", unit="season_name", provenance=SignalProvenance.DECLARED, quality=SignalQuality.VALID, source="calendar_engine"),
            farm_area_acres=TraceableSignal[float](value=4.5, unit="acres", provenance=SignalProvenance.DECLARED, quality=SignalQuality.VALID, source="farmer_profile"),
            irrigation_method=TraceableSignal[str](value="drip", unit="method_enum", provenance=SignalProvenance.DECLARED, quality=SignalQuality.VALID, source="farmer_profile"),
            irrigation_status=TraceableSignal[str](value="normal", unit="status_enum", provenance=SignalProvenance.DECLARED, quality=SignalQuality.VALID, source="farmer_profile"),
        ),
        soil=SoilState(
            soil_type=TraceableSignal[str](value="Alluvial Sandy Loam", unit="taxonomy", provenance=SignalProvenance.DECLARED, quality=SignalQuality.VALID, source="soil_survey"),
            ph=TraceableSignal[float](value=6.8, unit="pH", provenance=SignalProvenance.DECLARED, quality=SignalQuality.VALID, source="soil_health_card"),
            nitrogen_kg_ha=TraceableSignal[float](value=110.0, unit="kg/ha", provenance=SignalProvenance.DECLARED, quality=SignalQuality.VALID, source="soil_testing_lab"),
            phosphorus_kg_ha=TraceableSignal[float](value=22.0, unit="kg/ha", provenance=SignalProvenance.DECLARED, quality=SignalQuality.VALID, source="soil_testing_lab"),
            potassium_kg_ha=TraceableSignal[float](value=140.0, unit="kg/ha", provenance=SignalProvenance.DECLARED, quality=SignalQuality.VALID, source="soil_testing_lab"),
            nutrient_status=TraceableSignal[str](value="Laboratory Tested", unit="status", provenance=SignalProvenance.DERIVED, quality=SignalQuality.VALID, source="soil_analyzer"),
        ),
        telemetry=TelemetryState(
            soil_moisture_vwc=TraceableSignal[float](value=48.0, unit="% VWC", provenance=SignalProvenance.SIMULATED, quality=SignalQuality.SIMULATED, source="Virtual IoT Node #SIM-NODE-01"),
            ambient_temp_c=TraceableSignal[float](value=22.0, unit="°C", provenance=SignalProvenance.SIMULATED, quality=SignalQuality.SIMULATED, source="Virtual IoT Node #SIM-NODE-01"),
            humidity_percent=TraceableSignal[float](value=65.0, unit="%", provenance=SignalProvenance.SIMULATED, quality=SignalQuality.SIMULATED, source="Virtual IoT Node #SIM-NODE-01"),
            light_lux=TraceableSignal[int](value=52000, unit="lux", provenance=SignalProvenance.SIMULATED, quality=SignalQuality.SIMULATED, source="Virtual IoT Node #SIM-NODE-01"),
            status_label=TraceableSignal[str](value="Optimal", unit="status", provenance=SignalProvenance.DERIVED, quality=SignalQuality.VALID, source="telemetry_analyzer"),
            is_simulated=True,
        ),
        weather=WeatherState(
            temperature_c=TraceableSignal[float](value=23.5, unit="°C", provenance=SignalProvenance.LIVE, quality=SignalQuality.VALID, source="Open-Meteo REST API"),
            humidity_percent=TraceableSignal[float](value=58.0, unit="%", provenance=SignalProvenance.LIVE, quality=SignalQuality.VALID, source="Open-Meteo REST API"),
            precipitation_mm=TraceableSignal[float](value=0.0, unit="mm", provenance=SignalProvenance.LIVE, quality=SignalQuality.VALID, source="Open-Meteo REST API"),
            rain_probability_percent=TraceableSignal[int](value=15, unit="%", provenance=SignalProvenance.LIVE, quality=SignalQuality.VALID, source="Open-Meteo REST API"),
            wind_speed_kmh=TraceableSignal[float](value=9.5, unit="km/h", provenance=SignalProvenance.LIVE, quality=SignalQuality.VALID, source="Open-Meteo REST API"),
            weather_code=TraceableSignal[int](value=1, unit="wmo", provenance=SignalProvenance.LIVE, quality=SignalQuality.VALID, source="Open-Meteo REST API"),
            condition_text=TraceableSignal[str](value="Mainly Clear", unit="text", provenance=SignalProvenance.LIVE, quality=SignalQuality.VALID, source="Open-Meteo REST API"),
            overall_risk=TraceableSignal[str](value="low", unit="risk", provenance=SignalProvenance.DERIVED, quality=SignalQuality.VALID, source="weather_engine"),
            favorable_window=TraceableSignal[str](value="Next 48 hours (calm morning hours)", unit="text", provenance=SignalProvenance.DERIVED, quality=SignalQuality.VALID, source="timing_advice_engine"),
        ),
        disease=DiseaseState(
            has_diagnosis=True,
            pathogen_name=TraceableSignal[str](value="Wheat Yellow Rust (Puccinia striiformis)", unit="text", provenance=SignalProvenance.LIVE, quality=SignalQuality.VALID, source="EfficientNet-B0"),
            scientific_name=TraceableSignal[str](value="Puccinia striiformis", unit="latin", provenance=SignalProvenance.CACHED, quality=SignalQuality.VALID, source="icar_registry"),
            confidence_percent=TraceableSignal[float](value=51.69, unit="PERCENTAGE", provenance=SignalProvenance.LIVE, quality=SignalQuality.VALID, source="EfficientNet-B0"),
            confidence_fraction=TraceableSignal[float](value=0.5169, unit="DECIMAL_FRACTION", provenance=SignalProvenance.DERIVED, quality=SignalQuality.VALID, source="normalizer"),
            confidence_unit="PERCENTAGE",
            risk_level=TraceableSignal[str](value="high", unit="risk", provenance=SignalProvenance.DERIVED, quality=SignalQuality.VALID, source="pathology_classifier"),
            is_borderline=True,
            needs_expert_review=True,
            prescription_locked=True,
            model_name=TraceableSignal[str](value="EfficientNet-B0-AgriV2", unit="identifier", provenance=SignalProvenance.CACHED, quality=SignalQuality.VALID, source="ai_manifest"),
            image_quality_status=TraceableSignal[str](value="GOOD", unit="status", provenance=SignalProvenance.LIVE, quality=SignalQuality.VALID, source="hsv_filter"),
        ),
        market=MarketState(
            crop=TraceableSignal[str](value="Wheat", unit="text", provenance=SignalProvenance.DECLARED, quality=SignalQuality.VALID, source="mandi_registry"),
            reference_price_per_kg=TraceableSignal[float](value=24.50, unit="INR/kg", provenance=SignalProvenance.DECLARED, quality=SignalQuality.VALID, source="mandi_registry"),
            currency="INR",
            pricing_type=TraceableSignal[str](value="BENCHMARK", unit="type", provenance=SignalProvenance.DERIVED, quality=SignalQuality.VALID, source="marketplace_engine"),
            active_market_listings=TraceableSignal[int](value=3, unit="count", provenance=SignalProvenance.LIVE, quality=SignalQuality.VALID, source="agribridge_db"),
        ),
        current_action=CurrentActionState()
    )


def create_scenario_2_disease_plus_bad_weather() -> FarmDecisionContext:
    """
    Scenario 2: High-Confidence Disease + Unfavorable Weather
    Farmer: Balwinder Singh (Wheat, Ludhiana, Punjab)
    Disease: High confidence Yellow Rust (88.50%)
    Weather: Heavy rain alert (85% rain prob, 18.5 mm rain, 24.0 km/h wind)
    Telemetry: 52.0% VWC
    NPK: 110 kg/ha N
    """
    ctx = create_scenario_1_borderline_disease()
    ctx.context_id = "SCENARIO-02-DISEASE-AND-BAD-WEATHER"
    # Disease: High Confidence (Not Borderline)
    ctx.disease.confidence_percent.value = 88.50
    ctx.disease.confidence_fraction.value = 0.8850
    ctx.disease.is_borderline = False
    ctx.disease.needs_expert_review = False
    ctx.disease.prescription_locked = False

    # Weather: Unfavorable Rain & Wind
    ctx.weather.rain_probability_percent.value = 85
    ctx.weather.precipitation_mm.value = 18.5
    ctx.weather.wind_speed_kmh.value = 24.0
    ctx.weather.condition_text.value = "Moderate to Heavy Rain Showers"
    ctx.weather.overall_risk.value = "high"
    ctx.weather.favorable_window.value = "Friday (2026-09-08) after rain system clears"
    return ctx


def create_scenario_3_missing_npk() -> FarmDecisionContext:
    """
    Scenario 3: Missing Laboratory NPK Data
    Farmer: Balwinder Singh (Wheat, Ludhiana, Punjab)
    Disease: High confidence Yellow Rust (85.0%)
    Weather: Favorable (10% rain, 8 km/h wind)
    Telemetry: 44.0% VWC (Optimal)
    NPK: Completely UNAVAILABLE (value=None, provenance=UNAVAILABLE)
    """
    ctx = create_scenario_1_borderline_disease()
    ctx.context_id = "SCENARIO-03-MISSING-NPK"
    ctx.disease.confidence_percent.value = 85.00
    ctx.disease.confidence_fraction.value = 0.8500
    ctx.disease.is_borderline = False
    ctx.disease.needs_expert_review = False
    ctx.disease.prescription_locked = False

    # NPK Missing
    ctx.soil.nitrogen_kg_ha.value = None
    ctx.soil.nitrogen_kg_ha.provenance = SignalProvenance.UNAVAILABLE
    ctx.soil.nitrogen_kg_ha.quality = SignalQuality.MISSING
    ctx.soil.nitrogen_kg_ha.source = "none"

    ctx.soil.phosphorus_kg_ha.value = None
    ctx.soil.phosphorus_kg_ha.provenance = SignalProvenance.UNAVAILABLE
    ctx.soil.phosphorus_kg_ha.quality = SignalQuality.MISSING
    ctx.soil.phosphorus_kg_ha.source = "none"

    ctx.soil.potassium_kg_ha.value = None
    ctx.soil.potassium_kg_ha.provenance = SignalProvenance.UNAVAILABLE
    ctx.soil.potassium_kg_ha.quality = SignalQuality.MISSING
    ctx.soil.potassium_kg_ha.source = "none"

    ctx.soil.nutrient_status.value = "Insufficient Lab Data"
    return ctx


def create_scenario_4_simulated_telemetry() -> FarmDecisionContext:
    """
    Scenario 4: Simulated Telemetry with Low Soil Moisture
    Farmer: Balwinder Singh (Wheat, Ludhiana, Punjab)
    Disease: None (Routine Scouting)
    Weather: Favorable (10% rain, 7 km/h wind)
    Telemetry: 32.5% VWC (< 40% threshold -> Deficit), provenance=SIMULATED
    NPK: Standard Baseline
    """
    ctx = create_scenario_1_borderline_disease()
    ctx.context_id = "SCENARIO-04-SIMULATED-TELEMETRY"
    ctx.disease.has_diagnosis = False

    # Telemetry indicates soil deficit
    ctx.telemetry.soil_moisture_vwc.value = 32.5
    ctx.telemetry.soil_moisture_vwc.provenance = SignalProvenance.SIMULATED
    ctx.telemetry.soil_moisture_vwc.quality = SignalQuality.SIMULATED
    ctx.telemetry.status_label.value = "Low"
    ctx.telemetry.is_simulated = True
    return ctx
