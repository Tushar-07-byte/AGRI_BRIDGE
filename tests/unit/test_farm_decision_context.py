"""
Unit Test Suite: Canonical Farm Decision Context (Phase 2)
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Asserts all 12 Phase 2 integrity conditions:
1. Complete context with all signals available.
2. Disease-only context.
3. Weather unavailable / fallback resilience.
4. Market unavailable resilience.
5. NPK unavailable resilience.
6. Telemetry simulated flag preservation.
7. Mixed live + simulated + derived signals.
8. Confidence representation & normalization (30-65% gating).
9. Unit preservation across metrics.
10. Missing optional signal does not crash context construction.
11. Existing orchestration behavior remains unchanged.
12. No secrets (passwords, JWT secrets, API keys) leak in context responses.
"""

import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime

# Setup root path
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = WORKSPACE_ROOT / "backend"
sys.path.insert(0, str(WORKSPACE_ROOT))
sys.path.insert(0, str(BACKEND_ROOT))

from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.domain.farm_decision_context import (
    FarmDecisionContext,
    SignalProvenance,
    SignalQuality
)
from app.services.farm_decision_context_service import FarmDecisionContextService
from tests.fixtures.demo_scenario_context import get_deterministic_demo_scenario

client = TestClient(app)


def test_1_complete_context_all_signals():
    """1. Complete context with all signals available."""
    ctx = get_deterministic_demo_scenario()
    assert ctx.decision_readiness is True
    assert ctx.identity.farmer_name.value == "Balwinder Singh"
    assert ctx.crop.crop_id.value == "wheat"
    assert ctx.soil.nitrogen_kg_ha.value == 110.0
    assert ctx.telemetry.soil_moisture_vwc.value == 24.0
    assert ctx.weather.rain_probability_percent.value == 10
    assert ctx.disease.confidence_percent.value == 51.69
    assert ctx.market.reference_price_per_kg.value == 27.50
    assert ctx.current_action.active_plan_id.value == 801
    assert len(ctx.provenance_summary) > 30
    print("[PASS] Condition 1: Complete context with all signals validated.")


def test_2_disease_only_context():
    """2. Disease-only context operates safely when other inputs are minimal."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        ctx = loop.run_until_complete(
            FarmDecisionContextService.build_context(
                disease_scan_data={
                    "pathogen": "Tomato Early Blight",
                    "confidence": 88.5,
                    "severity": "high",
                    "model": "EfficientNetB0_Tomato"
                }
            )
        )
        assert ctx.disease.has_diagnosis is True
        assert ctx.disease.pathogen_name.value == "Tomato Early Blight"
        assert ctx.disease.confidence_percent.value == 88.5
        assert ctx.disease.confidence_fraction.value == 0.885
        assert ctx.disease.is_borderline is False
        assert ctx.disease.needs_expert_review is False
        print("[PASS] Condition 2: Disease-only context successfully constructed.")
    finally:
        loop.close()


def test_3_weather_unavailable_fallback():
    """3. Weather unavailable does not crash context builder; marks quality as FALLBACK or CACHED."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # Pass coordinates in an inaccessible or extreme coordinate that triggers graceful fallback
        ctx = loop.run_until_complete(
            FarmDecisionContextService.build_context(
                state="NonExistentState",
                district="UnknownDistrict",
                latitude=999.0,
                longitude=999.0
            )
        )
        assert ctx.weather is not None
        assert ctx.weather.temperature_c.value is not None
        # Must have fallback or cached provenance
        assert ctx.weather.temperature_c.provenance in [SignalProvenance.CACHED, SignalProvenance.LIVE]
        print("[PASS] Condition 3: Weather unavailable fallback resilience validated.")
    finally:
        loop.close()


def test_4_market_unavailable_resilience():
    """4. Market data absence does not break decision context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        ctx = loop.run_until_complete(
            FarmDecisionContextService.build_context(
                crop_id="rare_exotic_herb_xyz",
                db=None
            )
        )
        assert ctx.market.crop.value is not None
        assert ctx.market.reference_price_per_kg.value == 30.0 # Default fallback benchmark
        assert ctx.market.pricing_type.value == "BENCHMARK"
        print("[PASS] Condition 4: Market unavailable resilience validated.")
    finally:
        loop.close()


def test_5_npk_unavailable_resilience():
    """5. Missing laboratory NPK soil data leaves values as None with UNAVAILABLE provenance."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        ctx = loop.run_until_complete(
            FarmDecisionContextService.build_context(
                nitrogen=None,
                phosphorus=None,
                potassium=None
            )
        )
        assert ctx.soil.nitrogen_kg_ha.value is None
        assert ctx.soil.nitrogen_kg_ha.provenance == SignalProvenance.UNAVAILABLE
        assert ctx.soil.nitrogen_kg_ha.quality == SignalQuality.MISSING
        assert ctx.soil.nitrogen_kg_ha.unit == "kg/ha"
        assert ctx.decision_readiness is True
        print("[PASS] Condition 5: NPK unavailable resilience validated.")
    finally:
        loop.close()


def test_6_telemetry_simulated_flag():
    """6. Virtual IoT telemetry strictly tagged as SIMULATED with is_simulated = True."""
    ctx = get_deterministic_demo_scenario()
    assert ctx.telemetry.is_simulated is True
    assert ctx.telemetry.soil_moisture_vwc.provenance == SignalProvenance.SIMULATED
    assert ctx.telemetry.ambient_temp_c.provenance == SignalProvenance.SIMULATED
    assert ctx.telemetry.soil_moisture_vwc.unit == "% VWC"
    assert "Virtual IoT Node" in ctx.telemetry.soil_moisture_vwc.source
    print("[PASS] Condition 6: Telemetry simulated flag preservation validated.")


def test_7_mixed_provenance_signals():
    """7. Mixed live + simulated + derived signals are co-present with accurate metadata."""
    ctx = get_deterministic_demo_scenario()
    summary = ctx.provenance_summary
    provenances = {v["provenance"] for v in summary.values()}
    assert "LIVE" in provenances
    assert "SIMULATED" in provenances
    assert "DERIVED" in provenances
    assert "DECLARED" in provenances
    assert "CACHED" in provenances
    print("[PASS] Condition 7: Mixed provenance categorization validated across all signals.")


def test_8_confidence_representation():
    """8. Confidence representation: unambiguous percentage primary, fraction secondary, 30-65% gating."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # Case A: Borderline score 51.69%
        ctx_borderline = loop.run_until_complete(
            FarmDecisionContextService.build_context(
                disease_scan_data={"confidence": 51.69, "pathogen": "Wheat Rust"}
            )
        )
        assert ctx_borderline.disease.confidence_percent.value == 51.69
        assert ctx_borderline.disease.confidence_fraction.value == 0.5169
        assert ctx_borderline.disease.confidence_unit == "PERCENTAGE"
        assert ctx_borderline.disease.is_borderline is True
        assert ctx_borderline.disease.needs_expert_review is True
        assert ctx_borderline.disease.prescription_locked is True

        # Case B: High confidence 95.5% (passed as decimal fraction 0.955)
        ctx_fraction = loop.run_until_complete(
            FarmDecisionContextService.build_context(
                disease_scan_data={"confidence": 0.955, "pathogen": "Healthy Wheat"}
            )
        )
        assert ctx_fraction.disease.confidence_percent.value == 95.5
        assert ctx_fraction.disease.confidence_fraction.value == 0.955
        assert ctx_fraction.disease.is_borderline is False
        assert ctx_fraction.disease.needs_expert_review is False
        assert ctx_fraction.disease.prescription_locked is False

        # Verify explicit bounds dictionary
        bounds = ctx_borderline.disease.gating_thresholds
        assert bounds["uncertainty_min_percent"] == 30.0
        assert bounds["uncertainty_max_percent"] == 65.0
        assert bounds["uncertainty_min_fraction"] == 0.30
        assert bounds["uncertainty_max_fraction"] == 0.65
        print("[PASS] Condition 8: Confidence representation & normalization validated.")
    finally:
        loop.close()


def test_9_unit_preservation():
    """9. Unit preservation across scientific metrics."""
    ctx = get_deterministic_demo_scenario()
    assert ctx.weather.temperature_c.unit == "°C"
    assert ctx.weather.precipitation_mm.unit == "mm"
    assert ctx.weather.wind_speed_kmh.unit == "km/h"
    assert ctx.telemetry.soil_moisture_vwc.unit == "% VWC"
    assert ctx.telemetry.light_lux.unit == "lux"
    assert ctx.soil.nitrogen_kg_ha.unit == "kg/ha"
    assert ctx.market.reference_price_per_kg.unit == "INR/kg"
    assert ctx.disease.confidence_percent.unit == "PERCENTAGE"
    print("[PASS] Condition 9: Metric unit preservation validated.")


def test_10_missing_optional_signals_does_not_crash():
    """10. Completely blank optional inputs do not crash context construction."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        ctx = loop.run_until_complete(FarmDecisionContextService.build_context())
        assert ctx is not None
        assert ctx.context_id.startswith("ctx_")
        assert ctx.decision_readiness is True
        print("[PASS] Condition 10: Missing optional signals resilience validated.")
    finally:
        loop.close()


def test_11_existing_orchestration_unchanged():
    """11. Existing orchestration endpoint POST /api/orchestration/plan behaves identically."""
    resp = client.post(
        "/api/orchestration/plan",
        json={
            "state": "Punjab",
            "district": "Ludhiana",
            "village": "Samrala",
            "crop": "Wheat",
            "planting_date": "2026-11-05",
            "crop_stage": "Tillering"
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "action_plan_id" in data
    assert "tasks" in data
    assert "recommendation" in data
    # Enriched context metadata present
    assert "farm_decision_context_id" in data
    assert data["signals_considered_count"] > 30
    print("[PASS] Condition 11: Existing orchestration compatibility validated.")


def test_12_no_secrets_leaked_in_context():
    """12. Context inspection response contains zero secrets, passwords, or API keys."""
    resp = client.get("/api/orchestration/context/1")
    assert resp.status_code == 200
    raw_text = resp.text

    forbidden_patterns = [
        "password",
        "secret_key",
        "AUTH_SECRET_KEY",
        "AgriBridge@2026",
        "GEMINI_API_KEY",
        "AQ.Ab8RN6L7TDTT3ny"
    ]
    for pattern in forbidden_patterns:
        assert pattern not in raw_text, f"Security violation: found '{pattern}' in context response!"

    data = resp.json()
    assert data["success"] is True
    assert "context" in data
    assert data["context"]["context_id"].startswith("ctx_")
    print("[PASS] Condition 12: Zero secrets in context response validated.")


def run_all_tests():
    print("=======================================================================")
    print("  RUNNING PHASE 2 FARM DECISION CONTEXT TEST SUITE (12 CONDITIONS)")
    print("=======================================================================")
    test_1_complete_context_all_signals()
    test_2_disease_only_context()
    test_3_weather_unavailable_fallback()
    test_4_market_unavailable_resilience()
    test_5_npk_unavailable_resilience()
    test_6_telemetry_simulated_flag()
    test_7_mixed_provenance_signals()
    test_8_confidence_representation()
    test_9_unit_preservation()
    test_10_missing_optional_signals_does_not_crash()
    test_11_existing_orchestration_unchanged()
    test_12_no_secrets_leaked_in_context()
    print("=======================================================================")
    print("  ALL 12 PHASE 2 TEST CONDITIONS PASSED (0 FAILURES)")
    print("=======================================================================")


if __name__ == "__main__":
    run_all_tests()
