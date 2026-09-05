"""
AgriBridge Phase 2 Deterministic Demo Scenario Fixture
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Provides a deterministic multi-signal benchmark representing Farmer Balwinder Singh (Wheat Farm, Ludhiana, Punjab).
Explicitly marks each signal's provenance (LIVE, SIMULATED, DECLARED, DERIVED, CACHED).
"""

from app.domain.farm_decision_context import (
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

def get_deterministic_demo_scenario() -> FarmDecisionContext:
    """
    Returns the golden benchmark FarmDecisionContext for judge defense.
    Scenario:
      Farmer: Balwinder Singh (Farmer #101)
      Location: Ludhiana, Punjab (30.9010° N, 75.8573° E)
      Crop: Wheat (HD-2967), Tillering Stage, 4.5 Acres
      Soil: Alluvial Sandy Loam, pH 6.8, N: 110 kg/ha, P: 22 kg/ha, K: 140 kg/ha
      Virtual Telemetry: 24.0% VWC, 29.0°C, 62.0% RH, 62,000 Lux (SIMULATED)
      Weather: 28.5°C, 58% RH, 10% Rain Prob, 12 km/h Wind, Favorable Window (LIVE Open-Meteo)
      Disease: Wheat Yellow Rust (Puccinia striiformis), 51.69% Confidence (LIVE EfficientNet - BORDERLINE)
      Market: Wheat Benchmark ₹27.50 / kg (DECLARED / BENCHMARK)
      Current Action: Plan #801, Needs Expert Review, Escalation Dispatched (LIVE DB)
    """
    iso_now = "2026-09-03T12:00:00Z"

    identity = IdentityLocationState(
        farmer_id=TraceableSignal[int](
            value=101,
            unit="ID",
            provenance=SignalProvenance.LIVE,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="agribridge_database.farmers",
            reason_relevant="Primary key identifying farm operator"
        ),
        farmer_name=TraceableSignal[str](
            value="Balwinder Singh",
            unit="text",
            provenance=SignalProvenance.DECLARED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="user_profile",
            reason_relevant="Personalized communication and field dispatch"
        ),
        state=TraceableSignal[str](
            value="Punjab",
            unit="text",
            provenance=SignalProvenance.DECLARED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="farmer_profile",
            reason_relevant="State-level agro-climatic zone classification"
        ),
        district=TraceableSignal[str](
            value="Ludhiana",
            unit="text",
            provenance=SignalProvenance.DECLARED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="farmer_profile",
            reason_relevant="District coordinate anchoring for hyper-local weather"
        ),
        village=TraceableSignal[str](
            value="Samrala",
            unit="text",
            provenance=SignalProvenance.DECLARED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="farmer_profile",
            reason_relevant="Micro-location for field agent routing"
        ),
        latitude=TraceableSignal[float](
            value=30.9010,
            unit="degrees_north",
            provenance=SignalProvenance.CACHED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="india_districts_registry",
            reason_relevant="Geographic coordinate for Open-Meteo satellite feed"
        ),
        longitude=TraceableSignal[float](
            value=75.8573,
            unit="degrees_east",
            provenance=SignalProvenance.CACHED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="india_districts_registry",
            reason_relevant="Geographic coordinate for Open-Meteo satellite feed"
        )
    )

    crop = CropState(
        crop_id=TraceableSignal[str](
            value="wheat",
            unit="slug",
            provenance=SignalProvenance.DECLARED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="field_registry",
            reason_relevant="Target crop for ICAR disease models and nutrition schedules"
        ),
        crop_name=TraceableSignal[str](
            value="Wheat",
            unit="text",
            provenance=SignalProvenance.DECLARED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="field_registry",
            reason_relevant="Human-readable crop name for farmer advisory"
        ),
        variety=TraceableSignal[str](
            value="HD-2967 (Certified ICAR Seed)",
            unit="text",
            provenance=SignalProvenance.DECLARED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="farmer_declaration",
            reason_relevant="Specific varietal resistance and duration to maturity"
        ),
        planting_date=TraceableSignal[str](
            value="2026-11-05",
            unit="YYYY-MM-DD",
            provenance=SignalProvenance.DECLARED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="farmer_declaration",
            reason_relevant="Baseline for calculating Days After Sowing (DAS)"
        ),
        growth_stage=TraceableSignal[str](
            value="Tillering",
            unit="phenology_stage",
            provenance=SignalProvenance.DECLARED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="farmer_declaration",
            reason_relevant="Determines vulnerability window to specific fungal strains"
        ),
        season=TraceableSignal[str](
            value="Rabi",
            unit="season_name",
            provenance=SignalProvenance.DECLARED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="calendar_engine",
            reason_relevant="Cropping season alignment"
        ),
        farm_area_acres=TraceableSignal[float](
            value=4.5,
            unit="acres",
            provenance=SignalProvenance.DECLARED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="farmer_profile",
            reason_relevant="Used to scale spray volume and water allocation"
        ),
        irrigation_method=TraceableSignal[str](
            value="drip",
            unit="method_enum",
            provenance=SignalProvenance.DECLARED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="farm_profile",
            reason_relevant="Determines application efficiency and leaf wetness duration"
        ),
        irrigation_status=TraceableSignal[str](
            value="normal",
            unit="status_enum",
            provenance=SignalProvenance.DECLARED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="farm_profile",
            reason_relevant="Current field saturation baseline"
        )
    )

    soil = SoilState(
        soil_type=TraceableSignal[str](
            value="Alluvial Sandy Loam",
            unit="soil_taxonomy",
            provenance=SignalProvenance.DECLARED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="soil_survey_report",
            reason_relevant="Determines cation exchange capacity and water holding capacity"
        ),
        ph=TraceableSignal[float](
            value=6.8,
            unit="pH",
            provenance=SignalProvenance.DECLARED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="soil_health_card",
            reason_relevant="Optimal micronutrient uptake bracket (6.5 - 7.5)"
        ),
        nitrogen_kg_ha=TraceableSignal[float](
            value=110.0,
            unit="kg/ha",
            provenance=SignalProvenance.DECLARED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="soil_testing_laboratory",
            reason_relevant="Baseline soil nitrogen fertility"
        ),
        phosphorus_kg_ha=TraceableSignal[float](
            value=22.0,
            unit="kg/ha",
            provenance=SignalProvenance.DECLARED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="soil_testing_laboratory",
            reason_relevant="Available phosphorus for root tillering"
        ),
        potassium_kg_ha=TraceableSignal[float](
            value=140.0,
            unit="kg/ha",
            provenance=SignalProvenance.DECLARED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="soil_testing_laboratory",
            reason_relevant="Available potassium for disease resistance and cell wall rigidity"
        ),
        nutrient_status=TraceableSignal[str](
            value="Laboratory Verified Balanced Stand",
            unit="category",
            provenance=SignalProvenance.DERIVED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="soil_evaluation_engine",
            reason_relevant="Categorical nutritional rating"
        )
    )

    telemetry = TelemetryState(
        soil_moisture_vwc=TraceableSignal[float](
            value=24.0,
            unit="% VWC",
            provenance=SignalProvenance.SIMULATED,
            quality=SignalQuality.SIMULATED,
            timestamp=iso_now,
            source="Virtual IoT Node #SIM-NODE-01",
            reason_relevant="Root zone volumetric water content triggers irrigation/re-planning"
        ),
        ambient_temp_c=TraceableSignal[float](
            value=29.0,
            unit="°C",
            provenance=SignalProvenance.SIMULATED,
            quality=SignalQuality.SIMULATED,
            timestamp=iso_now,
            source="Virtual IoT Node #SIM-NODE-01",
            reason_relevant="Microclimate sensor telemetry for localized crop stress"
        ),
        humidity_percent=TraceableSignal[float](
            value=62.0,
            unit="%",
            provenance=SignalProvenance.SIMULATED,
            quality=SignalQuality.SIMULATED,
            timestamp=iso_now,
            source="Virtual IoT Node #SIM-NODE-01",
            reason_relevant="Canopy level relative humidity"
        ),
        light_lux=TraceableSignal[int](
            value=62000,
            unit="lux",
            provenance=SignalProvenance.SIMULATED,
            quality=SignalQuality.SIMULATED,
            timestamp=iso_now,
            source="Virtual IoT Node #SIM-NODE-01",
            reason_relevant="Photosynthetically active radiation indicator"
        ),
        status_label=TraceableSignal[str](
            value="Optimal",
            unit="status_label",
            provenance=SignalProvenance.DERIVED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="telemetry_analyzer",
            reason_relevant="Categorical rating of soil hydration"
        ),
        is_simulated=True
    )

    weather = WeatherState(
        temperature_c=TraceableSignal[float](
            value=28.5,
            unit="°C",
            provenance=SignalProvenance.LIVE,
            quality=SignalQuality.LIVE,
            timestamp=iso_now,
            source="Open-Meteo REST API",
            reason_relevant="Ambient air temperature for chemical evaporation rate"
        ),
        humidity_percent=TraceableSignal[float](
            value=58.0,
            unit="%",
            provenance=SignalProvenance.LIVE,
            quality=SignalQuality.LIVE,
            timestamp=iso_now,
            source="Open-Meteo REST API",
            reason_relevant="Canopy humidity risk factor"
        ),
        precipitation_mm=TraceableSignal[float](
            value=0.0,
            unit="mm",
            provenance=SignalProvenance.LIVE,
            quality=SignalQuality.LIVE,
            timestamp=iso_now,
            source="Open-Meteo REST API",
            reason_relevant="Current precipitation volume"
        ),
        rain_probability_percent=TraceableSignal[int](
            value=10,
            unit="%",
            provenance=SignalProvenance.LIVE,
            quality=SignalQuality.LIVE,
            timestamp=iso_now,
            source="Open-Meteo REST API",
            reason_relevant="Low rain risk ensures optimal spray absorption"
        ),
        wind_speed_kmh=TraceableSignal[float](
            value=12.0,
            unit="km/h",
            provenance=SignalProvenance.LIVE,
            quality=SignalQuality.LIVE,
            timestamp=iso_now,
            source="Open-Meteo REST API",
            reason_relevant="Wind speed under 20 km/h satisfies spray drift threshold"
        ),
        weather_code=TraceableSignal[int](
            value=1,
            unit="wmo_code",
            provenance=SignalProvenance.LIVE,
            quality=SignalQuality.LIVE,
            timestamp=iso_now,
            source="Open-Meteo REST API",
            reason_relevant="Mainly clear conditions"
        ),
        condition_text=TraceableSignal[str](
            value="Mainly clear",
            unit="text",
            provenance=SignalProvenance.LIVE,
            quality=SignalQuality.LIVE,
            timestamp=iso_now,
            source="Open-Meteo REST API",
            reason_relevant="Human-readable synopsis"
        ),
        overall_risk=TraceableSignal[str](
            value="low",
            unit="risk_level",
            provenance=SignalProvenance.DERIVED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="agribridge_weather_engine",
            reason_relevant="Synthesized atmospheric risk category"
        ),
        favorable_window=TraceableSignal[str](
            value="Clear 48-hour spray window available. Favorable atmospheric inversion.",
            unit="text",
            provenance=SignalProvenance.DERIVED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="timing_advice_engine",
            reason_relevant="Actionable execution advice"
        )
    )

    disease = DiseaseState(
        has_diagnosis=True,
        pathogen_name=TraceableSignal[str](
            value="Wheat Yellow Rust",
            unit="text",
            provenance=SignalProvenance.LIVE,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="AgriBridge_EfficientNetB0_Wheat",
            reason_relevant="Primary biological threat requiring treatment"
        ),
        scientific_name=TraceableSignal[str](
            value="Puccinia striiformis f. sp. tritici",
            unit="latin_binomial",
            provenance=SignalProvenance.CACHED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="icar_plant_pathology_registry",
            reason_relevant="ICAR active ingredient reference baseline"
        ),
        confidence_percent=TraceableSignal[float](
            value=51.69,
            unit="PERCENTAGE",
            provenance=SignalProvenance.LIVE,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="AgriBridge_EfficientNetB0_Wheat",
            reason_relevant="Borderline confidence score in [30.0, 65.0)% requiring HITL escalation"
        ),
        confidence_fraction=TraceableSignal[float](
            value=0.5169,
            unit="DECIMAL_FRACTION",
            provenance=SignalProvenance.DERIVED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="agribridge_normalizer",
            reason_relevant="Decimal fraction representation [0.0 - 1.0]"
        ),
        confidence_unit="PERCENTAGE",
        risk_level=TraceableSignal[str](
            value="moderate",
            unit="risk_level",
            provenance=SignalProvenance.DERIVED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="pathology_risk_classifier",
            reason_relevant="Severity level"
        ),
        is_borderline=True,
        needs_expert_review=True,
        prescription_locked=True,
        model_name=TraceableSignal[str](
            value="EfficientNetB0_Wheat_Stage2",
            unit="identifier",
            provenance=SignalProvenance.CACHED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="ai_engine_manifest",
            reason_relevant="Deep learning model"
        ),
        image_quality_status=TraceableSignal[str](
            value="VALID_LEAF",
            unit="status_enum",
            provenance=SignalProvenance.LIVE,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="leaf_hsv_quality_filter",
            reason_relevant="Image quality verification"
        )
    )

    market = MarketState(
        crop=TraceableSignal[str](
            value="Wheat",
            unit="commodity_name",
            provenance=SignalProvenance.DECLARED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="mandi_commodity_registry",
            reason_relevant="Wholesale trade benchmark mapping"
        ),
        reference_price_per_kg=TraceableSignal[float](
            value=27.50,
            unit="INR/kg",
            provenance=SignalProvenance.DECLARED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="AgriBridge Mandi Price Registry",
            reason_relevant="Official benchmark procurement rate"
        ),
        currency="INR",
        pricing_type=TraceableSignal[str](
            value="BENCHMARK",
            unit="pricing_type_enum",
            provenance=SignalProvenance.DERIVED,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="marketplace_engine",
            reason_relevant="Differentiates static benchmark rates from active farmer lots"
        ),
        active_market_listings=TraceableSignal[int](
            value=4,
            unit="count",
            provenance=SignalProvenance.LIVE,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="agribridge_database.listings",
            reason_relevant="Active market lots available"
        )
    )

    action = CurrentActionState(
        active_plan_id=TraceableSignal[int](
            value=801,
            unit="ID",
            provenance=SignalProvenance.LIVE,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="agribridge_database.action_plans",
            reason_relevant="Active plan tracking"
        ),
        plan_status=TraceableSignal[str](
            value="needs_expert_review",
            unit="status_enum",
            provenance=SignalProvenance.LIVE,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="action_plan_lifecycle_engine",
            reason_relevant="Lifecycle state"
        ),
        risk_type=TraceableSignal[str](
            value="disease_treatment",
            unit="risk_type_enum",
            provenance=SignalProvenance.LIVE,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="action_plan_orchestrator",
            reason_relevant="Threat category"
        ),
        escalation_required=TraceableSignal[bool](
            value=True,
            unit="boolean",
            provenance=SignalProvenance.LIVE,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="escalation_policy_engine",
            reason_relevant="HITL agronomist review trigger"
        ),
        tasks_count=TraceableSignal[int](
            value=1,
            unit="count",
            provenance=SignalProvenance.LIVE,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="plan_tasks_table",
            reason_relevant="Total tasks"
        ),
        active_task_title=TraceableSignal[str](
            value="Awaiting Field Agent Verification (Tebuconazole 25.9% EC)",
            unit="text",
            provenance=SignalProvenance.LIVE,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="plan_tasks_table",
            reason_relevant="Prescription locked pending HITL authorization"
        ),
        last_replan_reason=TraceableSignal[str](
            value="Inspection uncertainty: Confidence in 30-65% range requires on-site expert review.",
            unit="text",
            provenance=SignalProvenance.LIVE,
            quality=SignalQuality.VALID,
            timestamp=iso_now,
            source="action_plan_audit_trail",
            reason_relevant="Audit trail"
        )
    )

    ctx = FarmDecisionContext(
        context_id="ctx_demo_balwinder_wheat_001",
        created_at=iso_now,
        decision_readiness=True,
        identity=identity,
        crop=crop,
        soil=soil,
        telemetry=telemetry,
        weather=weather,
        disease=disease,
        market=market,
        current_action=action
    )
    ctx.compile_provenance_summary()
    return ctx

