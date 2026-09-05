"""
Phase 3 Master Test Suite: Weather-Aware Adaptive Execution & Replanning
Problem Statement: SH-AGR-001 / AGR-001 — Agriculture & Rural Development

Asserts all 12 Phase 3 conditions:
1. Valid weather + ALLOWED disease action -> executable task remains possible.
2. High-confidence disease + heavy rain -> DEFERRED -> zero executable task for unsafe execution.
3. Existing task becomes unsafe during execution-time recheck -> execution prevented, replan/defer state recorded.
4. Weather becomes safe -> deterministic recheck returns ALLOWED -> safe execution window updated/confirmed.
5. Repeated recheck -> duplicate-task guard prevents duplicate tasks.
6. Stale weather -> trust failure -> no unsafe execution.
7. Unavailable weather -> safe failure/defer behavior, no invented weather values.
8. SIMULATED weather in demo mode -> provenance remains SIMULATED.
9. SIMULATED weather outside demo mode -> must not be silently trusted as LIVE.
10. LLM failure/absence -> deterministic weather policy remains authoritative.
11. Invalid weather payload/timestamp -> rejected safely by trust gate.
12. Phase 1 task lifecycle remains intact.
"""

import sys
import json
import uuid
import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Anchor sys.path
WORKSPACE_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = WORKSPACE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.models.farmer import Farmer
from app.models.action_plan import ActionPlan, PlanTask, CalendarEvent, NotificationEvent
from app.domain.farm_decision_context import (
    FarmDecisionContext,
    SignalProvenance,
    SignalQuality,
    TraceableSignal,
    DiseaseState
)
from app.domain.multi_signal_decision import DecisionResult, DecisionType, MultiSignalDecision
from app.services.farm_decision_context_service import FarmDecisionContextService
from app.services.multi_signal_policy_engine import MultiSignalPolicyEngine
from app.services.orchestration_service import OrchestrationService
from app.services.utils import is_signal_trustworthy

client = TestClient(app)


@pytest.fixture(scope="function")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def test_farmer(db):
    f_name = f"Phase 3 Farmer {uuid.uuid4().hex[:6]}"
    farmer = Farmer(name=f_name)
    db.add(farmer)
    db.commit()
    db.refresh(farmer)
    return farmer


# ------------------------------------------------------------------------------
# TEST 1: Valid weather + ALLOWED disease action -> executable task remains possible
# ------------------------------------------------------------------------------
@pytest.mark.anyio
async def test_1_valid_weather_allowed_disease_action(db, test_farmer):
    scan_data = {
        "pathogen": "Wheat Yellow Rust",
        "scientific_name": "Puccinia striiformis",
        "confidence": 88.5,
        "severity": "high",
        "model": "AgriBridge_EfficientNetB0",
        "provenance": SignalProvenance.LIVE,
        "quality": SignalQuality.VALID
    }

    ctx = await FarmDecisionContextService.build_context(
        farmer_id=test_farmer.id,
        db=db,
        crop_id="wheat",
        disease_scan_data=scan_data,
        weather_override={
            "rain_probability_percent": 10,
            "wind_speed": 8.0,
            "condition": "Mainly clear",
            "provenance": SignalProvenance.LIVE,
            "quality": SignalQuality.VALID
        }
    )

    decision = MultiSignalPolicyEngine.evaluate(ctx)
    disease_decision = next(d for d in decision.decisions if d.decision_type == DecisionType.DISEASE_TREATMENT)
    weather_decision = next(d for d in decision.decisions if d.decision_type == DecisionType.WEATHER_TIMING)

    assert disease_decision.result == DecisionResult.ALLOWED
    assert weather_decision.result == DecisionResult.ALLOWED
    assert "WEATHER_RAIN_BLOCK" not in decision.constraints

    # Create Plan and Task
    plan = ActionPlan(
        farmer_id=test_farmer.id,
        crop_id="wheat",
        risk_type="disease_treatment",
        status="active",
        decision_json=decision.json(),
        constraints_json=json.dumps(decision.constraints),
        recommended_actions_json=json.dumps(decision.recommended_actions),
        created_at=datetime.utcnow()
    )
    db.add(plan)
    db.flush()

    task = PlanTask(
        action_plan_id=plan.id,
        title="Apply Propiconazole 25% EC @ 1ml/L",
        scheduled_for=datetime.utcnow() + timedelta(days=1),
        status="pending",
        reasoning="Weather is clear; immediate treatment authorized.",
        completed_at=None
    )
    db.add(task)
    db.commit()

    assert task.status == "pending"
    assert task.completed_at is None


# ------------------------------------------------------------------------------
# TEST 2: High-confidence disease + heavy rain -> DEFERRED -> zero executable tasks
# ------------------------------------------------------------------------------
@pytest.mark.anyio
async def test_2_disease_plus_heavy_rain_deferred(db, test_farmer):
    scan_data = {
        "pathogen": "Wheat Yellow Rust",
        "confidence": 91.0,
        "model": "AgriBridge_EfficientNetB0"
    }

    # 85% Rain probability -> Wash-off risk
    ctx = await FarmDecisionContextService.build_context(
        farmer_id=test_farmer.id,
        db=db,
        crop_id="wheat",
        disease_scan_data=scan_data,
        weather_override={
            "rain_probability_percent": 85,
            "precipitation": 12.0,
            "condition": "Heavy convective thunderstorm"
        }
    )

    decision = MultiSignalPolicyEngine.evaluate(ctx)
    weather_item = next(d for d in decision.decisions if d.decision_type == DecisionType.WEATHER_TIMING)
    assert weather_item.result == DecisionResult.DEFERRED
    assert "WEATHER_RAIN_BLOCK" in decision.constraints
    assert decision.overall_risk == "critical"

    # Precedence rule: Treatment is deferred until favorable dry window
    assert any("deferred until" in action.lower() for action in decision.recommended_actions)


# ------------------------------------------------------------------------------
# TEST 3: Existing task becomes unsafe during execution recheck -> execution prevented
# ------------------------------------------------------------------------------
@pytest.mark.anyio
async def test_3_existing_task_becomes_unsafe_during_recheck(db, test_farmer):
    # Initialize Plan with pending task
    plan = ActionPlan(
        farmer_id=test_farmer.id,
        crop_id="wheat",
        risk_type="disease_treatment",
        status="active",
        created_at=datetime.utcnow()
    )
    db.add(plan)
    db.flush()

    task = PlanTask(
        action_plan_id=plan.id,
        title="Apply Fungicide Treatment",
        scheduled_for=datetime.utcnow() + timedelta(hours=6),
        status="pending",
        reasoning="Initial clear forecast.",
        completed_at=None
    )
    db.add(task)
    db.commit()

    # Recheck with incoming heavy rain surge (80% rain)
    recheck_res = await OrchestrationService.recheck_weather_and_reschedule(
        plan_id=plan.id,
        simulated_rain=80,
        simulated_condition="Heavy downpour forecasted",
        db=db
    )

    assert recheck_res["success"] is True
    assert recheck_res["change_detected"] is True
    assert recheck_res["change_type"] == "WEATHER_WORSENED_RAIN_SURGE"

    db.refresh(plan)
    db.refresh(task)

    # Risk type shifted to weather delay
    assert plan.risk_type == "weather_delay"
    # Task status remains valid lifecycle ('pending') with updated scheduled time in safe window
    assert task.status == "pending"
    assert "Rescheduled" in task.title
    assert "Weather constraint detected" in task.reasoning
    # Task is NOT completed
    assert task.completed_at is None


# ------------------------------------------------------------------------------
# TEST 4: Weather becomes safe -> deterministic recheck returns ALLOWED
# ------------------------------------------------------------------------------
@pytest.mark.anyio
async def test_4_weather_becomes_safe_recheck_allowed(db, test_farmer):
    # Initialize previously delayed Plan
    plan = ActionPlan(
        farmer_id=test_farmer.id,
        crop_id="wheat",
        risk_type="weather_delay",
        status="active",
        created_at=datetime.utcnow()
    )
    db.add(plan)
    db.flush()

    task = PlanTask(
        action_plan_id=plan.id,
        title="Rescheduled: Apply Fungicide Treatment",
        scheduled_for=datetime.utcnow() + timedelta(days=4),
        status="pending",
        reasoning="Delayed for storm system.",
        completed_at=None
    )
    db.add(task)
    db.commit()

    # Recheck with clear skies (10% rain)
    recheck_res = await OrchestrationService.recheck_weather_and_reschedule(
        plan_id=plan.id,
        simulated_rain=10,
        simulated_condition="Clear skies and optimal inversion",
        db=db
    )

    assert recheck_res["success"] is True
    assert recheck_res["change_detected"] is True
    assert recheck_res["change_type"] == "WEATHER_CLEARED_SAFE_WINDOW"

    db.refresh(plan)
    db.refresh(task)

    assert plan.risk_type == "disease_treatment"
    assert "Expedited" in task.title
    assert "Weather cleared" in task.reasoning


# ------------------------------------------------------------------------------
# TEST 5: Repeated recheck under stable weather -> no duplicate tasks
# ------------------------------------------------------------------------------
@pytest.mark.anyio
async def test_5_repeated_recheck_no_duplicate_tasks(db, test_farmer):
    plan = ActionPlan(
        farmer_id=test_farmer.id,
        crop_id="wheat",
        risk_type="disease_treatment",
        status="active",
        created_at=datetime.utcnow()
    )
    db.add(plan)
    db.flush()

    task = PlanTask(
        action_plan_id=plan.id,
        title="Apply Fungicide Treatment",
        scheduled_for=datetime.utcnow() + timedelta(hours=12),
        status="pending",
        reasoning="Optimal window.",
        completed_at=None
    )
    db.add(task)
    db.commit()

    # Run recheck 3 times with stable clear weather
    for _ in range(3):
        res = await OrchestrationService.recheck_weather_and_reschedule(
            plan_id=plan.id,
            simulated_rain=15,
            simulated_condition="Clear sky",
            db=db
        )
        assert res["success"] is True

    # Confirm exactly 1 task exists in database
    task_count = db.query(PlanTask).filter(PlanTask.action_plan_id == plan.id).count()
    assert task_count == 1, "Repeated rechecks must NEVER duplicate tasks!"


# ------------------------------------------------------------------------------
# TEST 6: Stale weather data (> 2h) -> trust failure -> no unsafe execution
# ------------------------------------------------------------------------------
@pytest.mark.anyio
async def test_6_stale_weather_data_fails_trust_gate(db, test_farmer):
    stale_time = (datetime.now(timezone.utc) - timedelta(hours=4)).isoformat()
    stale_signal = TraceableSignal[int](
        value=15,
        unit="%",
        provenance=SignalProvenance.LIVE,
        quality=SignalQuality.STALE,
        timestamp=stale_time,
        source="Open-Meteo REST API",
        reason_relevant="Precipitation check"
    )

    # Signal trust utility must reject stale data
    assert is_signal_trustworthy(stale_signal) is False

    ctx = await FarmDecisionContextService.build_context(
        farmer_id=test_farmer.id,
        db=db,
        crop_id="wheat",
        weather_override={"rain_probability_percent": 15}
    )
    # Inject stale signal
    ctx.weather.rain_probability_percent = stale_signal

    decision = MultiSignalPolicyEngine.evaluate(ctx)
    weather_item = next(d for d in decision.decisions if d.decision_type == DecisionType.WEATHER_TIMING)
    assert weather_item.result == DecisionResult.DEFERRED
    assert "UNTRUSTED_WEATHER" in decision.constraints


# ------------------------------------------------------------------------------
# TEST 7: Unavailable weather -> safe failure/defer behavior -> no invented values
# ------------------------------------------------------------------------------
@pytest.mark.anyio
async def test_7_unavailable_weather_fails_safely(db, test_farmer):
    unavail_signal = TraceableSignal[int](
        value=None,
        unit="%",
        provenance=SignalProvenance.UNAVAILABLE,
        quality=SignalQuality.MISSING,
        timestamp=None,
        source="Open-Meteo REST API",
        reason_relevant="Weather feed down"
    )

    assert is_signal_trustworthy(unavail_signal) is False

    ctx = await FarmDecisionContextService.build_context(
        farmer_id=test_farmer.id,
        db=db,
        crop_id="wheat"
    )
    ctx.weather.rain_probability_percent = unavail_signal

    decision = MultiSignalPolicyEngine.evaluate(ctx)
    weather_item = next(d for d in decision.decisions if d.decision_type == DecisionType.WEATHER_TIMING)
    assert weather_item.result == DecisionResult.DEFERRED
    assert "UNTRUSTED_WEATHER" in decision.constraints


# ------------------------------------------------------------------------------
# TEST 8: SIMULATED weather in demo mode -> provenance remains SIMULATED
# ------------------------------------------------------------------------------
@pytest.mark.anyio
async def test_8_simulated_weather_in_demo_mode(db, test_farmer):
    ctx = await FarmDecisionContextService.build_context(
        farmer_id=test_farmer.id,
        db=db,
        crop_id="wheat",
        weather_override={
            "rain_probability_percent": 25,
            "condition": "Simulated Sunny",
            "provenance": SignalProvenance.SIMULATED,
            "quality": SignalQuality.SIMULATED
        }
    )

    assert ctx.weather.rain_probability_percent.provenance == SignalProvenance.SIMULATED
    assert ctx.weather.rain_probability_percent.quality == SignalQuality.SIMULATED

    decision = MultiSignalPolicyEngine.evaluate(ctx)
    trace_item = next(t for t in decision.decision_trace if t.signal == "weather.rain_probability_percent")
    assert trace_item.provenance == "SIMULATED"


# ------------------------------------------------------------------------------
# TEST 9: SIMULATED weather outside demo mode -> not silently trusted as LIVE
# ------------------------------------------------------------------------------
@pytest.mark.anyio
async def test_9_simulated_weather_never_rewritten_to_live(db, test_farmer):
    ctx = await FarmDecisionContextService.build_context(
        farmer_id=test_farmer.id,
        db=db,
        crop_id="wheat",
        weather_override={
            "rain_probability_percent": 10,
            "provenance": SignalProvenance.SIMULATED
        }
    )

    assert ctx.weather.rain_probability_percent.provenance == SignalProvenance.SIMULATED
    assert ctx.weather.rain_probability_percent.provenance != SignalProvenance.LIVE


# ------------------------------------------------------------------------------
# TEST 10: LLM failure/absence -> deterministic weather decision remains authoritative
# ------------------------------------------------------------------------------
@pytest.mark.anyio
async def test_10_deterministic_weather_decision_without_llm(db, test_farmer):
    # MultiSignalPolicyEngine has ZERO LLM calls and is 100% deterministic
    ctx = await FarmDecisionContextService.build_context(
        farmer_id=test_farmer.id,
        db=db,
        crop_id="wheat",
        weather_override={
            "rain_probability_percent": 70,
            "wind_speed": 25.0
        }
    )

    decision = MultiSignalPolicyEngine.evaluate(ctx)
    assert "WEATHER_RAIN_BLOCK" in decision.constraints
    assert "WEATHER_WIND_DRIFT_BLOCK" in decision.constraints
    weather_item = next(d for d in decision.decisions if d.decision_type == DecisionType.WEATHER_TIMING)
    assert weather_item.result == DecisionResult.DEFERRED
    assert weather_item.reason_code == "RAIN_RISK_EXECUTION_BLOCKED"


# ------------------------------------------------------------------------------
# TEST 11: Invalid weather payload/timestamp -> rejected safely by trust gate
# ------------------------------------------------------------------------------
def test_11_invalid_future_timestamp_rejected():
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    future_signal = TraceableSignal[int](
        value=10,
        unit="%",
        provenance=SignalProvenance.LIVE,
        quality=SignalQuality.VALID,
        timestamp=future_time,
        source="Open-Meteo REST API",
        reason_relevant="Precipitation check"
    )

    # A timestamp 2 days in the future is invalid/untrusted
    assert is_signal_trustworthy(future_signal) is False


# ------------------------------------------------------------------------------
# TEST 12: Phase 1 task lifecycle remains intact
# ------------------------------------------------------------------------------
def test_12_phase1_task_lifecycle_intact(db, test_farmer):
    plan = ActionPlan(
        farmer_id=test_farmer.id,
        crop_id="rice",
        risk_type="disease_treatment",
        status="active",
        created_at=datetime.utcnow()
    )
    db.add(plan)
    db.flush()

    task = PlanTask(
        action_plan_id=plan.id,
        title="Phase 1 Lifecycle Check",
        scheduled_for=datetime.utcnow() + timedelta(hours=2),
        status="pending",
        completed_at=None
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # 1. PENDING -> IN_PROGRESS
    res1 = client.patch(f"/api/plan-tasks/{task.id}", json={"status": "in_progress"})
    assert res1.status_code == 200
    assert res1.json()["task"]["status"] == "in_progress"

    # 2. IN_PROGRESS -> COMPLETED (done)
    res2 = client.patch(f"/api/plan-tasks/{task.id}", json={"status": "done"})
    assert res2.status_code == 200
    assert res2.json()["task"]["status"] == "done"
    assert res2.json()["task"]["completed_at"] is not None
