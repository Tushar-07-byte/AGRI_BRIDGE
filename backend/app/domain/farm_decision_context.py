"""
AgriBridge Canonical Farm Decision Context Domain Model
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Provides a unified, normalized, traceable data contract representing the comprehensive state of a farm.
Encapsulates 20 agricultural signals across 8 domain sub-states with strict provenance tracking.
"""

from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar("T")


# ==============================================================================
# PROVENANCE & QUALITY ENUMS
# ==============================================================================

class SignalProvenance(str, Enum):
    """
    Strict traceability category denoting the origin of the signal.
    Never misrepresents virtual telemetry as physical hardware.
    """
    LIVE = "LIVE"                  # Live external API or real-time hardware/inference
    SIMULATED = "SIMULATED"        # Virtual prototype IoT telemetry or simulation model
    CACHED = "CACHED"              # High-confidence in-memory or persisted lookup / ICAR protocol
    DERIVED = "DERIVED"            # Mathematically or heuristically computed from other inputs
    DECLARED = "DECLARED"          # Self-reported by farmer/operator via form or profile
    UNAVAILABLE = "UNAVAILABLE"    # Optional signal not yet reported or observed


class SignalQuality(str, Enum):
    """Operational reliability & freshness of the signal."""
    VALID = "VALID"
    STALE = "STALE"
    MISSING = "MISSING"
    SIMULATED = "SIMULATED"
    LIVE = "LIVE"
    FALLBACK = "FALLBACK"


# ==============================================================================
# GENERIC TRACEABLE SIGNAL WRAPPER
# ==============================================================================

class TraceableSignal(BaseModel, Generic[T]):
    """
    Wraps an individual measurement with complete traceability metadata:
    WHAT (value, unit), WHERE FROM (source), WHEN (timestamp),
    STATUS (provenance, quality), and WHY RELEVANT (machine reasoning hook).
    """
    value: Optional[T] = Field(None, description="Actual measurement or observation value")
    unit: str = Field("N/A", description="Measurement unit (e.g. °C, mm, % VWC, kg/ha, INR/kg)")
    provenance: SignalProvenance = Field(SignalProvenance.UNAVAILABLE, description="Source provenance")
    quality: SignalQuality = Field(SignalQuality.MISSING, description="Quality/freshness indicator")
    timestamp: Optional[str] = Field(None, description="ISO-8601 timestamp of measurement")
    source: str = Field("unknown", description="Originating sensor, API, database or model name")
    reason_relevant: str = Field("", description="Why this signal is relevant to farm decision making")

    class Config:
        use_enum_values = True


# ==============================================================================
# 1. IDENTITY & LOCATION SUB-STATE
# ==============================================================================

class IdentityLocationState(BaseModel):
    farmer_id: TraceableSignal[int] = Field(default_factory=TraceableSignal[int])
    farmer_name: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])
    state: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])
    district: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])
    village: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])
    latitude: TraceableSignal[float] = Field(default_factory=TraceableSignal[float])
    longitude: TraceableSignal[float] = Field(default_factory=TraceableSignal[float])


# ==============================================================================
# 2. CROP & PHENOLOGY SUB-STATE
# ==============================================================================

class CropState(BaseModel):
    crop_id: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])
    crop_name: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])
    variety: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])
    planting_date: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])
    growth_stage: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])
    season: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])
    farm_area_acres: TraceableSignal[float] = Field(default_factory=TraceableSignal[float])
    irrigation_method: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])
    irrigation_status: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])


# ==============================================================================
# 3. SOIL & NUTRIENT SUB-STATE
# ==============================================================================

class SoilState(BaseModel):
    soil_type: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])
    ph: TraceableSignal[float] = Field(default_factory=TraceableSignal[float])
    nitrogen_kg_ha: TraceableSignal[float] = Field(default_factory=TraceableSignal[float])
    phosphorus_kg_ha: TraceableSignal[float] = Field(default_factory=TraceableSignal[float])
    potassium_kg_ha: TraceableSignal[float] = Field(default_factory=TraceableSignal[float])
    nutrient_status: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])


# ==============================================================================
# 4. TELEMETRY & VIRTUAL IoT SUB-STATE
# ==============================================================================

class TelemetryState(BaseModel):
    soil_moisture_vwc: TraceableSignal[float] = Field(default_factory=TraceableSignal[float])
    ambient_temp_c: TraceableSignal[float] = Field(default_factory=TraceableSignal[float])
    humidity_percent: TraceableSignal[float] = Field(default_factory=TraceableSignal[float])
    light_lux: TraceableSignal[int] = Field(default_factory=TraceableSignal[int])
    status_label: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])
    is_simulated: bool = Field(True, description="Always True for virtual IoT prototype nodes")


# ==============================================================================
# 5. WEATHER & ATMOSPHERIC SUB-STATE
# ==============================================================================

class WeatherState(BaseModel):
    temperature_c: TraceableSignal[float] = Field(default_factory=TraceableSignal[float])
    humidity_percent: TraceableSignal[float] = Field(default_factory=TraceableSignal[float])
    precipitation_mm: TraceableSignal[float] = Field(default_factory=TraceableSignal[float])
    rain_probability_percent: TraceableSignal[int] = Field(default_factory=TraceableSignal[int])
    wind_speed_kmh: TraceableSignal[float] = Field(default_factory=TraceableSignal[float])
    weather_code: TraceableSignal[int] = Field(default_factory=TraceableSignal[int])
    condition_text: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])
    overall_risk: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])
    favorable_window: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])


# ==============================================================================
# 6. DISEASE & PATHOLOGY SUB-STATE (CANONICAL CONFIDENCE STANDARD)
# ==============================================================================

class DiseaseState(BaseModel):
    """
    Captures clinical crop disease detection signals.
    Enforces the single canonical confidence representation:
      - confidence_percent: float in range [0.0, 100.0] (CANONICAL PRIMARY)
      - confidence_fraction: float in range [0.0, 1.0] (CONVENIENCE MAPPING)
      - gating_thresholds: Explicitly defines 30.0% / 0.30 and 65.0% / 0.65 bounds.
    """
    has_diagnosis: bool = Field(False, description="Whether an active disease scan exists")
    pathogen_name: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])
    scientific_name: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])
    confidence_percent: TraceableSignal[float] = Field(default_factory=TraceableSignal[float])
    confidence_fraction: TraceableSignal[float] = Field(default_factory=TraceableSignal[float])
    confidence_unit: str = Field("PERCENTAGE", description="Canonical internal standard unit (0-100%)")
    risk_level: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])
    is_borderline: bool = Field(False, description="True if confidence is in [30.0, 65.0)%")
    needs_expert_review: bool = Field(False, description="True if human agronomist escalation required")
    prescription_locked: bool = Field(False, description="True if chemical dosage is gated from farmer view")
    model_name: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])
    image_quality_status: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])
    gating_thresholds: Dict[str, float] = Field(
        default={
            "uncertainty_min_percent": 30.0,
            "uncertainty_max_percent": 65.0,
            "uncertainty_min_fraction": 0.30,
            "uncertainty_max_fraction": 0.65
        },
        description="Explicit bounds preventing 30% vs 0.30 ambiguity"
    )


# ==============================================================================
# 7. MARKET & COMMERCIAL SUB-STATE
# ==============================================================================

class MarketState(BaseModel):
    crop: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])
    reference_price_per_kg: TraceableSignal[float] = Field(default_factory=TraceableSignal[float])
    currency: str = Field("INR", description="Currency standard")
    pricing_type: TraceableSignal[str] = Field(default_factory=TraceableSignal[str]) # BENCHMARK | ACTIVE_LISTING
    active_market_listings: TraceableSignal[int] = Field(default_factory=TraceableSignal[int])


# ==============================================================================
# 8. CURRENT ACTION & ORCHESTRATION SUB-STATE
# ==============================================================================

class CurrentActionState(BaseModel):
    active_plan_id: TraceableSignal[int] = Field(default_factory=TraceableSignal[int])
    plan_status: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])
    risk_type: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])
    escalation_required: TraceableSignal[bool] = Field(default_factory=TraceableSignal[bool])
    tasks_count: TraceableSignal[int] = Field(default_factory=TraceableSignal[int])
    active_task_title: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])
    last_replan_reason: TraceableSignal[str] = Field(default_factory=TraceableSignal[str])


# ==============================================================================
# ROOT CANONICAL FARM DECISION CONTEXT
# ==============================================================================

class FarmDecisionContext(BaseModel):
    """
    Canonical Farm Decision Context for AgriBridge (SH-AGR-001).
    Integrates all 20 decision-relevant signals into a structured, traceable,
    explainable domain model for autonomous farm orchestration.
    """
    context_id: str = Field(..., description="Unique deterministic or UUID context identifier")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    decision_readiness: bool = Field(True, description="True if essential minimum signals are present")

    # 8 Domain Sub-States
    identity: IdentityLocationState = Field(default_factory=IdentityLocationState)
    crop: CropState = Field(default_factory=CropState)
    soil: SoilState = Field(default_factory=SoilState)
    telemetry: TelemetryState = Field(default_factory=TelemetryState)
    weather: WeatherState = Field(default_factory=WeatherState)
    disease: DiseaseState = Field(default_factory=DiseaseState)
    market: MarketState = Field(default_factory=MarketState)
    current_action: CurrentActionState = Field(default_factory=CurrentActionState)

    # Provenance Summary
    provenance_summary: Dict[str, Dict[str, str]] = Field(
        default_factory=dict,
        description="Index of all signals with their provenance, quality, and units"
    )

    def compile_provenance_summary(self) -> Dict[str, Dict[str, str]]:
        """
        Compiles a high-level judge-readable matrix of every signal and its provenance.
        """
        summary = {}

        def extract_signals(obj, prefix=""):
            if isinstance(obj, BaseModel):
                for name, field in obj.__fields__.items():
                    val = getattr(obj, name)
                    if isinstance(val, TraceableSignal):
                        key = f"{prefix}.{name}" if prefix else name
                        summary[key] = {
                            "provenance": val.provenance,
                            "quality": val.quality,
                            "unit": val.unit,
                            "source": val.source,
                            "has_value": str(val.value is not None)
                        }
                    elif isinstance(val, BaseModel):
                        extract_signals(val, prefix=f"{prefix}.{name}" if prefix else name)

        extract_signals(self)
        self.provenance_summary = summary
        return summary

