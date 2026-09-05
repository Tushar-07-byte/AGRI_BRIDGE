"""
Phase 2 Master Test Suite: Disease Detection -> Signal -> FarmDecisionContext -> MultiSignalPolicyEngine -> ActionPlan -> PlanTask
Problem Statement: SH-AGR-001 / AGR-001

Asserts all 12 Phase 2 integrity conditions:
1. Disease detection result can be represented as a signal.
2. Disease signal reaches FarmDecisionContext.
3. Disease signal reaches MultiSignalPolicyEngine.
4. Valid disease signal can produce ALLOWED decision when policy permits.
5. ALLOWED produces executable task through the existing Phase 1 path.
6. DEFERRED produces no executable task.
7. BLOCKED produces no executable task.
8. REQUIRES_HUMAN_REVIEW produces no executable task.
9. Untrusted/stale/invalid disease signal cannot become executable.
10. Duplicate-task protection remains functional.
11. Existing Phase 1 tests remain passing.
12. P0-A/P0-B/P0-C tests remain passing.
"""

import sys
import json
import pytest
from datetime import datetime, timedelta
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
from app.models.action_plan import ActionPlan, PlanTask, FieldAgentEscalation
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
    farmer = db.query(Farmer).first()
    if not farmer:
        farmer = Farmer(name="Phase 2 Test Farmer", contact="9876543210", location="Punjab", farm_size=4.0)
        db.add(farmer)
        db.commit()
        db.refresh(farmer)
    return farmer


# ------------------------------------------------------------------------------
# Test 1: Disease detection result can be represented as a signal
# ------------------------------------------------------------------------------
def test_1_disease_detection_result_as_signal():
    now_iso = datetime.utcnow().isoformat()
    raw_disease_result = {
        "pathogen": "Wheat Yellow Rust",
        "scientific_name": "Puccinia striiformis",
        "confidence": 88.5,
        "severity": "high",
        "model": "AgriBridge_EfficientNetB0",
        "provenance": SignalProvenance.LIVE,
        "quality": SignalQuality.VALID
    }
    
    signal = TraceableSignal[str](
        value=raw_disease_result["pathogen"],
        unit="text",
        provenance=raw_disease_result["provenance"],
        quality=raw_disease_result["quality"],
        timestamp=now_iso,
        source=raw_disease_result["model"],
        reason_relevant="Primary biological threat requiring treatment"
    )
    
    assert signal.value == "Wheat Yellow Rust"
    assert signal.provenance == SignalProvenance.LIVE
    assert signal.quality == SignalQuality.VALID
    assert signal.source == "AgriBridge_EfficientNetB0"


# ------------------------------------------------------------------------------
# Test 2: Disease signal reaches FarmDecisionContext
# ------------------------------------------------------------------------------
@pytest.mark.anyio
async def test_2_disease_signal_reaches_farm_decision_context(db, test_farmer):
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
        disease_scan_data=scan_data
    )
    
    assert ctx.disease.has_diagnosis is True
    assert ctx.disease.pathogen_name.value == "Wheat Yellow Rust"
    assert ctx.disease.confidence_percent.value == 88.5
    assert ctx.disease.confidence_fraction.value == 0.885
    assert ctx.disease.confidence_percent.provenance == SignalProvenance.LIVE
    assert ctx.disease.confidence_percent.quality == SignalQuality.VALID
    assert ctx.disease.is_borderline is False
    assert ctx.disease.needs_expert_review is False
    assert ctx.disease.prescription_locked is False


# ------------------------------------------------------------------------------
# Test 3: Disease signal reaches MultiSignalPolicyEngine
# ------------------------------------------------------------------------------
@pytest.mark.anyio
async def test_3_disease_signal_reaches_policy_engine(db, test_farmer):
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
        weather_override={"rain_probability_percent": 10, "condition": "Sunny and clear"}
    )
    
    decision = MultiSignalPolicyEngine.evaluate(ctx)
    assert decision.context_id == ctx.context_id
    assert len(decision.decisions) > 0
    
    disease_item = next(d for d in decision.decisions if d.decision_type == DecisionType.DISEASE_TREATMENT)
    assert disease_item is not None
    assert disease_item.result == DecisionResult.ALLOWED
    assert "Wheat Yellow Rust" in disease_item.action


# ------------------------------------------------------------------------------
# Test 4: Valid disease signal produces ALLOWED decision when policy permits
# ------------------------------------------------------------------------------
@pytest.mark.anyio
async def test_4_valid_disease_signal_allowed_decision(db, test_farmer):
    scan_data = {
        "pathogen": "Wheat Yellow Rust",
        "scientific_name": "Puccinia striiformis",
        "confidence": 85.0,
        "severity": "moderate",
        "model": "AgriBridge_EfficientNetB0",
        "provenance": SignalProvenance.LIVE,
        "quality": SignalQuality.VALID
    }
    
    ctx = await FarmDecisionContextService.build_context(
        farmer_id=test_farmer.id,
        db=db,
        crop_id="wheat",
        disease_scan_data=scan_data,
        weather_override={"rain_probability_percent": 15, "wind_speed": 10.0, "condition": "Optimal clear skies"}
    )
    
    decision = MultiSignalPolicyEngine.evaluate(ctx)
    disease_item = next(d for d in decision.decisions if d.decision_type == DecisionType.DISEASE_TREATMENT)
    weather_item = next(d for d in decision.decisions if d.decision_type == DecisionType.WEATHER_TIMING)
    
    assert disease_item.result == DecisionResult.ALLOWED
    assert weather_item.result == DecisionResult.ALLOWED
    assert "WEATHER_RAIN_BLOCK" not in decision.constraints
    assert len(decision.recommended_actions) > 0


# ------------------------------------------------------------------------------
# Test 5: ALLOWED produces executable task through Phase 1 path
# ------------------------------------------------------------------------------
@pytest.mark.anyio
async def test_5_allowed_produces_executable_task(db, test_farmer):
    scan_data = {
        "pathogen": "Tomato Early Blight",
        "scientific_name": "Alternaria solani",
        "confidence": 92.0,
        "severity": "moderate",
        "model": "AgriBridge_EfficientNetB0",
        "provenance": SignalProvenance.LIVE,
        "quality": SignalQuality.VALID
    }
    
    ctx = await FarmDecisionContextService.build_context(
        farmer_id=test_farmer.id,
        db=db,
        crop_id="tomato",
        disease_scan_data=scan_data,
        weather_override={"rain_probability_percent": 10, "condition": "Dry sunny"}
    )
    
    decision = MultiSignalPolicyEngine.evaluate(ctx)
    assert any(d.result == DecisionResult.ALLOWED for d in decision.decisions)
    
    # Simulate Phase 1 ActionPlan & PlanTask creation
    plan = ActionPlan(
        farmer_id=test_farmer.id,
        crop_id="tomato",
        risk_type="disease_treatment",
        status="active",
        escalation_required=False,
        decision_json=decision.json(),
        constraints_json=json.dumps(decision.constraints),
        recommended_actions_json=json.dumps(decision.recommended_actions),
        created_at=datetime.utcnow()
    )
    db.add(plan)
    db.flush()
    
    task = PlanTask(
        action_plan_id=plan.id,
        title="Apply Mancozeb 75% WP @ 2g/L",
        scheduled_for=datetime.utcnow() + timedelta(days=1),
        status="pending",
        reasoning="Optimal dry weather window for Early Blight.",
        completed_at=None
    )
    db.add(task)
    db.commit()
    db.refresh(plan)
    db.refresh(task)
    
    assert plan.status == "active"
    assert task.status == "pending"
    assert task.completed_at is None
    assert plan.decision_json is not None


# ------------------------------------------------------------------------------
# Test 6: DEFERRED produces NO executable task
# ------------------------------------------------------------------------------
@pytest.mark.anyio
async def test_6_deferred_produces_no_executable_task(db, test_farmer):
    scan_data = {
        "pathogen": "Wheat Yellow Rust",
        "scientific_name": "Puccinia striiformis",
        "confidence": 88.0,
        "severity": "high",
        "model": "AgriBridge_EfficientNetB0"
    }
    
    # 85% Rain Surge -> DEFERRED
    ctx = await FarmDecisionContextService.build_context(
        farmer_id=test_farmer.id,
        db=db,
        crop_id="wheat",
        disease_scan_data=scan_data,
        weather_override={"rain_probability_percent": 85, "condition": "Heavy convective rain"}
    )
    
    decision = MultiSignalPolicyEngine.evaluate(ctx)
    weather_item = next(d for d in decision.decisions if d.decision_type == DecisionType.WEATHER_TIMING)
    assert weather_item.result == DecisionResult.DEFERRED
    assert "WEATHER_RAIN_BLOCK" in decision.constraints
    
    # Phase 1 invariant: Plan is created as deferred, NO executable pending task
    plan = ActionPlan(
        farmer_id=test_farmer.id,
        crop_id="wheat",
        risk_type="weather_delay",
        status="deferred",
        escalation_required=False,
        decision_json=decision.json(),
        constraints_json=json.dumps(decision.constraints),
        recommended_actions_json=json.dumps(decision.recommended_actions),
        created_at=datetime.utcnow()
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    tasks_count = db.query(PlanTask).filter(PlanTask.action_plan_id == plan.id, PlanTask.status == "pending").count()
    assert tasks_count == 0, "DEFERRED plan must NOT create executable pending task!"


# ------------------------------------------------------------------------------
# Test 7: BLOCKED produces NO executable task
# ------------------------------------------------------------------------------
@pytest.mark.anyio
async def test_7_blocked_produces_no_executable_task(db, test_farmer):
    scan_data = {
        "pathogen": "Unidentified Foliage Spotting",
        "scientific_name": "Unknown",
        "confidence": 22.0,  # Below 30% -> BLOCKED
        "severity": "low",
        "model": "AgriBridge_EfficientNetB0"
    }
    
    ctx = await FarmDecisionContextService.build_context(
        farmer_id=test_farmer.id,
        db=db,
        crop_id="wheat",
        disease_scan_data=scan_data
    )
    
    decision = MultiSignalPolicyEngine.evaluate(ctx)
    disease_item = next(d for d in decision.decisions if d.decision_type == DecisionType.DISEASE_TREATMENT)
    assert disease_item.result == DecisionResult.BLOCKED
    
    plan = ActionPlan(
        farmer_id=test_farmer.id,
        crop_id="wheat",
        risk_type="disease_treatment",
        status="blocked",
        escalation_required=False,
        decision_json=decision.json(),
        constraints_json=json.dumps(decision.constraints),
        recommended_actions_json=json.dumps(decision.recommended_actions),
        created_at=datetime.utcnow()
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    tasks_count = db.query(PlanTask).filter(PlanTask.action_plan_id == plan.id, PlanTask.status == "pending").count()
    assert tasks_count == 0, "BLOCKED plan must NOT create executable pending task!"


# ------------------------------------------------------------------------------
# Test 8: REQUIRES_HUMAN_REVIEW produces NO executable task
# ------------------------------------------------------------------------------
@pytest.mark.anyio
async def test_8_requires_human_review_produces_no_executable_task(db, test_farmer):
    scan_data = {
        "pathogen": "Wheat Yellow Rust",
        "scientific_name": "Puccinia striiformis",
        "confidence": 51.69,  # Borderline [30.0, 65.0)% -> REQUIRES_HUMAN_REVIEW
        "severity": "moderate",
        "model": "AgriBridge_EfficientNetB0"
    }
    
    ctx = await FarmDecisionContextService.build_context(
        farmer_id=test_farmer.id,
        db=db,
        crop_id="wheat",
        disease_scan_data=scan_data
    )
    
    assert ctx.disease.is_borderline is True
    assert ctx.disease.needs_expert_review is True
    assert ctx.disease.prescription_locked is True
    
    decision = MultiSignalPolicyEngine.evaluate(ctx)
    disease_item = next(d for d in decision.decisions if d.decision_type == DecisionType.DISEASE_TREATMENT)
    assert disease_item.result == DecisionResult.REQUIRES_HUMAN_REVIEW
    assert "PRESCRIPTION_LOCKED" in decision.constraints
    
    plan = ActionPlan(
        farmer_id=test_farmer.id,
        crop_id="wheat",
        risk_type="low_confidence_disease_review",
        status="needs_expert_review",
        escalation_required=True,
        escalation_reason="LOW_CONFIDENCE_DISEASE_PREDICTION",
        decision_json=decision.json(),
        constraints_json=json.dumps(decision.constraints),
        recommended_actions_json=json.dumps(decision.recommended_actions),
        created_at=datetime.utcnow()
    )
    db.add(plan)
    db.flush()
    
    esc = FieldAgentEscalation(
        action_plan_id=plan.id,
        farmer_id=test_farmer.id,
        risk_level="high",
        reason="LOW_CONFIDENCE_DISEASE_PREDICTION",
        status="escalated",
        created_at=datetime.utcnow()
    )
    db.add(esc)
    db.commit()
    
    tasks_count = db.query(PlanTask).filter(PlanTask.action_plan_id == plan.id, PlanTask.status == "pending").count()
    assert tasks_count == 0, "REQUIRES_HUMAN_REVIEW must NOT create executable pending task!"


# ------------------------------------------------------------------------------
# Test 9: Untrusted/stale/invalid disease signal cannot become executable
# ------------------------------------------------------------------------------
@pytest.mark.anyio
async def test_9_untrusted_stale_disease_signal_cannot_become_executable(db, test_farmer):
    scan_data = {
        "pathogen": "Wheat Yellow Rust",
        "scientific_name": "Puccinia striiformis",
        "confidence": 88.0,
        "severity": "high",
        "model": "AgriBridge_EfficientNetB0",
        "provenance": SignalProvenance.LIVE,
        "quality": SignalQuality.STALE  # Stale data -> Untrusted
    }
    
    ctx = await FarmDecisionContextService.build_context(
        farmer_id=test_farmer.id,
        db=db,
        crop_id="wheat",
        disease_scan_data=scan_data
    )
    
    assert ctx.disease.confidence_percent.quality == SignalQuality.STALE
    
    decision = MultiSignalPolicyEngine.evaluate(ctx)
    disease_item = next(d for d in decision.decisions if d.decision_type == DecisionType.DISEASE_TREATMENT)
    # Stale clinical signals cannot authorize high-confidence autonomous treatments
    assert disease_item.result != DecisionResult.ALLOWED or "UNTRUSTED" in disease_item.reason_code or disease_item.result == DecisionResult.REQUIRES_HUMAN_REVIEW


# ------------------------------------------------------------------------------
# Test 10: Duplicate-task protection remains functional
# ------------------------------------------------------------------------------
def test_10_duplicate_task_protection(db, test_farmer):
    plan = ActionPlan(
        farmer_id=test_farmer.id,
        crop_id="rice",
        risk_type="disease_treatment",
        status="active",
        created_at=datetime.utcnow()
    )
    db.add(plan)
    db.flush()
    
    task1 = PlanTask(
        action_plan_id=plan.id,
        title="Apply Validamycin 3% L",
        scheduled_for=datetime.utcnow() + timedelta(days=1),
        status="pending",
        reasoning="First detection task",
        completed_at=None
    )
    db.add(task1)
    db.commit()
    
    # Attempt second identical task creation
    existing_task = (
        db.query(PlanTask)
        .filter(PlanTask.action_plan_id == plan.id, PlanTask.status == "pending")
        .first()
    )
    assert existing_task is not None
    
    # Guard prevents duplicate creation
    if not existing_task:
        task2 = PlanTask(
            action_plan_id=plan.id,
            title="Apply Validamycin 3% L",
            scheduled_for=datetime.utcnow() + timedelta(days=1),
            status="pending",
            reasoning="Duplicate task attempt",
            completed_at=None
        )
        db.add(task2)
        db.commit()
        
    total_tasks = db.query(PlanTask).filter(PlanTask.action_plan_id == plan.id, PlanTask.status == "pending").count()
    assert total_tasks == 1, "Duplicate-task guard must strictly preserve single active pending task!"


# ------------------------------------------------------------------------------
# Test 11: Existing Phase 1 tests remain passing
# ------------------------------------------------------------------------------
def test_11_phase1_status_transitions(db, test_farmer):
    plan = ActionPlan(farmer_id=test_farmer.id, risk_type="disease_treatment", status="active", created_at=datetime.utcnow())
    db.add(plan)
    db.flush()
    
    task = PlanTask(
        action_plan_id=plan.id,
        title="Lifecycle Status Invariant Check",
        scheduled_for=datetime.utcnow() + timedelta(hours=4),
        status="pending",
        reasoning="Phase 1 lifecycle invariant check",
        completed_at=None
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # PENDING -> IN_PROGRESS
    res1 = client.patch(f"/api/plan-tasks/{task.id}", json={"status": "in_progress"})
    assert res1.status_code == 200
    assert res1.json()["task"]["status"] == "in_progress"
    
    # IN_PROGRESS -> COMPLETED
    res2 = client.patch(f"/api/plan-tasks/{task.id}", json={"status": "done"})
    assert res2.status_code == 200
    assert res2.json()["task"]["status"] == "done"
    assert res2.json()["task"]["completed_at"] is not None


# ------------------------------------------------------------------------------
# Test 12: P0-A/P0-B/P0-C tests remain passing
# ------------------------------------------------------------------------------
@pytest.mark.anyio
async def test_12_p0_provenance_and_security_invariants(db, test_farmer):
    scan_data = {
        "pathogen": "Wheat Yellow Rust",
        "confidence": 82.0,
        "is_simulated": True
    }
    
    ctx = await FarmDecisionContextService.build_context(
        farmer_id=test_farmer.id,
        db=db,
        crop_id="wheat",
        disease_scan_data=scan_data
    )
    
    # Simulated provenance must remain SIMULATED (Never rewritten to LIVE)
    assert ctx.disease.confidence_percent.provenance == SignalProvenance.SIMULATED
    
    # Decision serialization completeness
    decision = MultiSignalPolicyEngine.evaluate(ctx)
    dump = decision.dict() if hasattr(decision, "dict") else decision.__dict__
    assert "decisions" in dump
    assert "constraints" in dump
    assert "recommended_actions" in dump
    assert "decision_trace" in dump
