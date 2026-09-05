"""
AgriBridge Phase 3 Multi-Signal Policy Engine Unit Test Suite
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Comprehensive verification of the 20 Phase 3 evaluation requirements:
1. Complete context evaluation.
2. Borderline disease handling (51.69% -> expert review, prescription locked).
3. High-confidence disease (88.5% -> actionable treatment).
4. Out-of-domain disease (22% -> rejected).
5. Disease + bad weather conflict (action required, execution deferred to dry window).
6. Disease + safe weather (immediate execution authorized).
7. Missing weather values (graceful fallback to safe defaults).
8. Missing NPK data (insufficient_data, zero fabricated fertilizer).
9. Available NPK (excessive nitrogen > 120 kg/ha rust alert).
10. Simulated telemetry (irrigation recommended, provenance=SIMULATED).
11. Missing telemetry (insufficient_data, maintains schedule).
12. Benchmark market data (provenance=DECLARED/BENCHMARK, advisory only).
13. Missing market data (graceful fallback).
14. Conflicting multi-signal resolution (5-tier precedence hierarchy).
15. Human-review precedence preservation.
16. Prescription lock cannot be bypassed by other signals.
17. Strict provenance preservation across all signals.
18. Decision trace auditability and explainability.
19. Existing OrchestrationService backward compatibility.
20. POST /api/orchestration/evaluate endpoint verification.
"""

import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient
from app.main import app
from app.domain.farm_decision_context import (
    FarmDecisionContext,
    SignalProvenance,
    SignalQuality,
)
from app.domain.multi_signal_decision import DecisionResult, DecisionType
from app.services.multi_signal_policy_engine import MultiSignalPolicyEngine
from tests.fixtures.phase3_demo_scenarios import (
    create_scenario_1_borderline_disease,
    create_scenario_2_disease_plus_bad_weather,
    create_scenario_3_missing_npk,
    create_scenario_4_simulated_telemetry,
)

client = TestClient(app)


# ------------------------------------------------------------------------------
# 1. Complete Context Evaluation
# ------------------------------------------------------------------------------
def test_complete_context_evaluation():
    ctx = create_scenario_1_borderline_disease()
    decision = MultiSignalPolicyEngine.evaluate(ctx)
    assert decision.decision_id.startswith("DEC-")
    assert decision.context_id == ctx.context_id
    assert decision.signals_considered >= 8
    assert len(decision.decisions) == 5  # Disease, Weather, Telemetry, Nutrient, Market
    assert len(decision.decision_trace) >= 8
    assert len(decision.provenance_summary) > 0


# ------------------------------------------------------------------------------
# 2. Borderline Disease (30% <= conf < 65%)
# ------------------------------------------------------------------------------
def test_borderline_disease_handling():
    ctx = create_scenario_1_borderline_disease()
    assert ctx.disease.confidence_percent.value == 51.69
    decision = MultiSignalPolicyEngine.evaluate(ctx)
    assert decision.escalation_required is True
    assert "PRESCRIPTION_LOCKED" in decision.constraints
    assert "FIELD_AGENT_ESCALATION_REQUIRED" in decision.constraints
    assert decision.priority == "urgent"
    d_item = next(d for d in decision.decisions if d.decision_type == DecisionType.DISEASE_TREATMENT)
    assert d_item.result == DecisionResult.REQUIRES_HUMAN_REVIEW
    assert d_item.reason_code == "BORDERLINE_CONFIDENCE_GATE"


# ------------------------------------------------------------------------------
# 3. High-Confidence Disease (conf >= 65%)
# ------------------------------------------------------------------------------
def test_high_confidence_disease_actionable():
    ctx = create_scenario_1_borderline_disease()
    ctx.disease.confidence_percent.value = 88.5
    ctx.disease.is_borderline = False
    ctx.disease.needs_expert_review = False
    ctx.disease.prescription_locked = False
    decision = MultiSignalPolicyEngine.evaluate(ctx)
    d_item = next(d for d in decision.decisions if d.decision_type == DecisionType.DISEASE_TREATMENT)
    assert d_item.result == DecisionResult.ALLOWED
    assert d_item.reason_code == "CONFIDENT_DIAGNOSIS_ACTIONABLE"
    assert "PRESCRIPTION_LOCKED" not in decision.constraints


# ------------------------------------------------------------------------------
# 4. Out-of-Domain Low Confidence (< 30%)
# ------------------------------------------------------------------------------
def test_out_of_domain_disease_rejected():
    ctx = create_scenario_1_borderline_disease()
    ctx.disease.confidence_percent.value = 22.4
    decision = MultiSignalPolicyEngine.evaluate(ctx)
    d_item = next(d for d in decision.decisions if d.decision_type == DecisionType.DISEASE_TREATMENT)
    assert d_item.result == DecisionResult.BLOCKED
    assert d_item.reason_code == "OUT_OF_DOMAIN_CONFIDENCE"
    assert "DIAGNOSIS_UNRELIABLE_REJECTED" in decision.constraints


# ------------------------------------------------------------------------------
# 5. Disease + Bad Weather Conflict
# ------------------------------------------------------------------------------
def test_disease_plus_bad_weather_deferred():
    ctx = create_scenario_2_disease_plus_bad_weather()
    decision = MultiSignalPolicyEngine.evaluate(ctx)
    assert decision.overall_risk == "critical"
    assert "WEATHER_RAIN_BLOCK" in decision.constraints
    w_item = next(d for d in decision.decisions if d.decision_type == DecisionType.WEATHER_TIMING)
    assert w_item.result == DecisionResult.DEFERRED
    assert w_item.reason_code == "RAIN_RISK_EXECUTION_BLOCKED"
    # Action must be deferred, not prescribed for immediate execution
    assert any("deferred until" in action.lower() for action in decision.recommended_actions)


# ------------------------------------------------------------------------------
# 6. Disease + Safe Weather
# ------------------------------------------------------------------------------
def test_disease_plus_safe_weather_authorized():
    ctx = create_scenario_2_disease_plus_bad_weather()
    ctx.weather.rain_probability_percent.value = 10
    ctx.weather.precipitation_mm.value = 0.0
    ctx.weather.wind_speed_kmh.value = 8.0
    decision = MultiSignalPolicyEngine.evaluate(ctx)
    assert "WEATHER_RAIN_BLOCK" not in decision.constraints
    assert any("prepare icar standard" in action.lower() for action in decision.recommended_actions)


# ------------------------------------------------------------------------------
# 7. Missing Weather Values (Safe Fallback)
# ------------------------------------------------------------------------------
def test_missing_weather_values_safe_fallback():
    ctx = create_scenario_1_borderline_disease()
    ctx.weather.rain_probability_percent.value = None
    ctx.weather.precipitation_mm.value = None
    ctx.weather.wind_speed_kmh.value = None
    decision = MultiSignalPolicyEngine.evaluate(ctx)
    assert decision.decision_id is not None
    # Defaults should not falsely block weather
    assert "WEATHER_RAIN_BLOCK" not in decision.constraints


# ------------------------------------------------------------------------------
# 8. Missing NPK Data (Zero Fabricated Fertilizer)
# ------------------------------------------------------------------------------
def test_missing_npk_no_fabricated_fertilizer():
    ctx = create_scenario_3_missing_npk()
    decision = MultiSignalPolicyEngine.evaluate(ctx)
    n_item = next(d for d in decision.decisions if d.decision_type == DecisionType.NUTRIENT_MANAGEMENT)
    assert n_item.result == DecisionResult.INSUFFICIENT_DATA
    assert n_item.reason_code == "MISSING_NPK_DATA"
    assert "unavailable" in n_item.action.lower()
    # Confirm zero chemical fertilizer dosages fabricated
    for rec in decision.recommended_actions:
        assert "kg/ha urea" not in rec.lower()
        assert "dap" not in rec.lower()


# ------------------------------------------------------------------------------
# 9. Available NPK (Excessive Nitrogen Rust Risk)
# ------------------------------------------------------------------------------
def test_available_npk_excessive_nitrogen_alert():
    ctx = create_scenario_1_borderline_disease()
    ctx.soil.nitrogen_kg_ha.value = 145.0  # > 120 kg/ha
    decision = MultiSignalPolicyEngine.evaluate(ctx)
    n_item = next(d for d in decision.decisions if d.decision_type == DecisionType.NUTRIENT_MANAGEMENT)
    assert n_item.result == DecisionResult.REQUIRES_HUMAN_REVIEW
    assert n_item.reason_code == "EXCESSIVE_NITROGEN_RUST_RISK"
    assert "EXCESSIVE_NITROGEN_ALERT" in decision.constraints


# ------------------------------------------------------------------------------
# 10. Simulated Telemetry (Low Moisture -> Irrigation)
# ------------------------------------------------------------------------------
def test_simulated_telemetry_irrigation_recommendation():
    ctx = create_scenario_4_simulated_telemetry()
    decision = MultiSignalPolicyEngine.evaluate(ctx)
    t_item = next(d for d in decision.decisions if d.decision_type == DecisionType.IRRIGATION)
    assert t_item.result == DecisionResult.ALLOWED
    assert t_item.reason_code == "LOW_SOIL_MOISTURE_IRRIGATION_NEEDED"
    assert any("irrigation" in action.lower() for action in decision.recommended_actions)
    # Provenance strictly remains SIMULATED
    vwc_trace = next(t for t in decision.decision_trace if t.signal == "telemetry.soil_moisture_vwc")
    assert vwc_trace.provenance == "SIMULATED"


# ------------------------------------------------------------------------------
# 11. Missing Telemetry (Insufficient Data)
# ------------------------------------------------------------------------------
def test_missing_telemetry_insufficient_data():
    ctx = create_scenario_4_simulated_telemetry()
    ctx.telemetry.soil_moisture_vwc.value = None
    decision = MultiSignalPolicyEngine.evaluate(ctx)
    t_item = next(d for d in decision.decisions if d.decision_type == DecisionType.IRRIGATION)
    assert t_item.result == DecisionResult.INSUFFICIENT_DATA
    assert t_item.reason_code == "TELEMETRY_UNAVAILABLE"


# ------------------------------------------------------------------------------
# 12. Benchmark Market Data (Provenance Preserved)
# ------------------------------------------------------------------------------
def test_benchmark_market_data_advisory_only():
    ctx = create_scenario_1_borderline_disease()
    ctx.market.pricing_type.value = "BENCHMARK"
    decision = MultiSignalPolicyEngine.evaluate(ctx)
    m_item = next(d for d in decision.decisions if d.decision_type == DecisionType.MARKET_DISPATCH)
    assert m_item.result == DecisionResult.ALLOWED
    assert "BENCHMARK" in m_item.reason_code or "MARKET_LISTING" in m_item.reason_code
    m_trace = next(t for t in decision.decision_trace if t.signal == "market.reference_price_per_kg")
    assert m_trace.provenance in ["DECLARED", "BENCHMARK"]


# ------------------------------------------------------------------------------
# 13. Missing Market Data (Graceful Fallback)
# ------------------------------------------------------------------------------
def test_missing_market_data_graceful():
    ctx = create_scenario_1_borderline_disease()
    ctx.market.reference_price_per_kg.value = None
    decision = MultiSignalPolicyEngine.evaluate(ctx)
    assert decision.decision_id is not None


# ------------------------------------------------------------------------------
# 14. Conflicting Multi-Signal Resolution
# ------------------------------------------------------------------------------
def test_conflicting_multi_signal_resolution():
    # Low soil moisture (<40%) BUT heavy rain (85% prob)
    ctx = create_scenario_4_simulated_telemetry()
    ctx.weather.rain_probability_percent.value = 85
    ctx.weather.precipitation_mm.value = 12.0
    decision = MultiSignalPolicyEngine.evaluate(ctx)
    t_item = next(d for d in decision.decisions if d.decision_type == DecisionType.IRRIGATION)
    # Irrigation must be deferred for incoming rain
    assert t_item.result == DecisionResult.DEFERRED
    assert t_item.reason_code == "DEFER_IRRIGATION_FOR_INCOMING_RAIN"


# ------------------------------------------------------------------------------
# 15. Human-Review Precedence
# ------------------------------------------------------------------------------
def test_human_review_precedence():
    ctx = create_scenario_1_borderline_disease()
    # Even if market is active and weather is perfect, human review MUST take precedence
    decision = MultiSignalPolicyEngine.evaluate(ctx)
    assert decision.priority == "urgent"
    assert decision.escalation_required is True


# ------------------------------------------------------------------------------
# 16. Prescription Lock Preservation
# ------------------------------------------------------------------------------
def test_prescription_lock_cannot_be_bypassed():
    ctx = create_scenario_1_borderline_disease()
    # Add great weather, rich NPK, high market price
    ctx.weather.rain_probability_percent.value = 0
    ctx.weather.wind_speed_kmh.value = 5.0
    ctx.soil.nitrogen_kg_ha.value = 100.0
    ctx.market.reference_price_per_kg.value = 50.0
    decision = MultiSignalPolicyEngine.evaluate(ctx)
    assert "PRESCRIPTION_LOCKED" in decision.constraints
    assert any("prescription" in b.lower() for b in decision.blocked_actions)


# ------------------------------------------------------------------------------
# 17. Strict Provenance Preservation
# ------------------------------------------------------------------------------
def test_provenance_preservation():
    ctx = create_scenario_4_simulated_telemetry()
    decision = MultiSignalPolicyEngine.evaluate(ctx)
    for t in decision.decision_trace:
        assert t.provenance in ["LIVE", "SIMULATED", "DECLARED", "CACHED", "DERIVED", "UNAVAILABLE"]
    # Telemetry must NEVER be claimed as LIVE
    tel_traces = [t for t in decision.decision_trace if "telemetry" in t.signal]
    for tt in tel_traces:
        assert tt.provenance == "SIMULATED"


# ------------------------------------------------------------------------------
# 18. Decision Trace Auditability
# ------------------------------------------------------------------------------
def test_decision_trace_auditability():
    ctx = create_scenario_2_disease_plus_bad_weather()
    decision = MultiSignalPolicyEngine.evaluate(ctx)
    for t in decision.decision_trace:
        assert t.signal is not None
        assert t.policy is not None
        assert t.condition is not None
        assert t.effect is not None


# ------------------------------------------------------------------------------
# 19. Existing OrchestrationService Compatibility
# ------------------------------------------------------------------------------
def test_orchestration_service_integration():
    from app.services.orchestration_service import OrchestrationService
    ctx = create_scenario_1_borderline_disease()
    # Call orchestrate_farm_plan directly with decision_context
    import asyncio
    res = asyncio.run(OrchestrationService.orchestrate_farm_plan(
        state="Punjab",
        district="Ludhiana",
        village="Samrala",
        crop_id="wheat",
        planting_date="2026-11-05",
        current_stage="Tillering",
        farmer_id=1,
        decision_context=ctx
    ))
    assert res["success"] is True
    assert "multi_signal_decision" in res
    assert res["multi_signal_decision"] is not None
    assert res["multi_signal_decision"]["escalation_required"] is True


# ------------------------------------------------------------------------------
# 20. POST /api/orchestration/evaluate Endpoint Verification
# ------------------------------------------------------------------------------
def test_evaluate_inspection_endpoint():
    resp = client.post("/api/orchestration/evaluate", json={
        "state": "Punjab",
        "district": "Ludhiana",
        "crop": "wheat",
        "disease_name": "Yellow Rust",
        "confidence": 51.69,
        "soil_moisture_vwc": 35.0,
        "rain_probability": 15
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["escalation_required"] is True
    assert "PRESCRIPTION_LOCKED" in data["constraints"]
    assert len(data["decision_trace"]) > 0
    assert "provenance_summary" in data


if __name__ == "__main__":
    print("Running Phase 3 Multi-Signal Policy Engine Unit Tests...")
    test_complete_context_evaluation()
    print("  [PASSED] 1. Complete Context Evaluation")
    test_borderline_disease_handling()
    print("  [PASSED] 2. Borderline Disease Handling (51.69% -> Lock Rx)")
    test_high_confidence_disease_actionable()
    print("  [PASSED] 3. High-Confidence Disease Actionable (88.5%)")
    test_out_of_domain_disease_rejected()
    print("  [PASSED] 4. Out-of-Domain Disease Rejected (<30%)")
    test_disease_plus_bad_weather_deferred()
    print("  [PASSED] 5. Disease + Bad Weather Conflict (Deferred)")
    test_disease_plus_safe_weather_authorized()
    print("  [PASSED] 6. Disease + Safe Weather Authorized")
    test_missing_weather_values_safe_fallback()
    print("  [PASSED] 7. Missing Weather Values Safe Fallback")
    test_missing_npk_no_fabricated_fertilizer()
    print("  [PASSED] 8. Missing NPK Data (Zero Fabricated Fertilizer)")
    test_available_npk_excessive_nitrogen_alert()
    print("  [PASSED] 9. Available NPK (Excessive Nitrogen Rust Alert)")
    test_simulated_telemetry_irrigation_recommendation()
    print("  [PASSED] 10. Simulated Telemetry (Provenance=SIMULATED)")
    test_missing_telemetry_insufficient_data()
    print("  [PASSED] 11. Missing Telemetry Insufficient Data")
    test_benchmark_market_data_advisory_only()
    print("  [PASSED] 12. Benchmark Market Data Advisory Only")
    test_missing_market_data_graceful()
    print("  [PASSED] 13. Missing Market Data Graceful Fallback")
    test_conflicting_multi_signal_resolution()
    print("  [PASSED] 14. Conflicting Multi-Signal Resolution")
    test_human_review_precedence()
    print("  [PASSED] 15. Human-Review Precedence")
    test_prescription_lock_cannot_be_bypassed()
    print("  [PASSED] 16. Prescription Lock Cannot Be Bypassed")
    test_provenance_preservation()
    print("  [PASSED] 17. Strict Provenance Preservation")
    test_decision_trace_auditability()
    print("  [PASSED] 18. Decision Trace Auditability")
    test_orchestration_service_integration()
    print("  [PASSED] 19. Existing OrchestrationService Compatibility")
    test_evaluate_inspection_endpoint()
    print("  [PASSED] 20. POST /api/orchestration/evaluate Endpoint Verification")
    print("\nALL 20 PHASE 3 UNIT TESTS PASSED SUCCESSFULLY!")
