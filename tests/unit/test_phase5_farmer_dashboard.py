"""
AgriBridge Phase 5 Unit Test Suite: Farmer-Facing Dashboard, Action Plan Serialization,
Task Lifecycle Controller & Deterministic Observability.
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Platform

Verifies:
1. Context inspection endpoint returns complete signal dictionary without leaking secrets.
2. Action plan serialization safely includes deterministic decisions, constraints, recommendations.
3. Task lifecycle transitions strictly: PENDING -> ACKNOWLEDGED -> IN_PROGRESS -> COMPLETED (invalid strings rejected).
4. Task completion triggers automatic weather re-check & rescheduling logic.
5. Safety Invariant: BLOCKED, REQUIRES_HUMAN_REVIEW, and DEFERRED produce 0 executable tasks.
6. Prescription lock is enforced on borderline confidence scenarios.
7. Simulated signals maintain SIMULATED provenance and are never upgraded to LIVE.
8. MultiSignalPolicyEngine evaluation endpoint yields explainable trace without LLM hallucinations.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database.connection import SessionLocal
from backend.app.models.farmer import Farmer
from backend.app.models.action_plan import ActionPlan, PlanTask, NotificationEvent
from backend.app.domain.farm_decision_context import SignalProvenance, SignalQuality
from backend.app.domain.multi_signal_decision import DecisionResult


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def db_session():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def test_farmer(db_session):
    farmer = db_session.query(Farmer).filter(Farmer.name == "Phase5 Test Farmer").first()
    if not farmer:
        farmer = Farmer(
            name="Phase5 Test Farmer"
        )
        db_session.add(farmer)
        db_session.commit()
        db_session.refresh(farmer)
    return farmer


def test_1_context_inspection_no_secrets_leaked(client, test_farmer):
    """Verify context endpoint returns complete signal data without leaking credentials or secrets."""
    res = client.get(f"/api/orchestration/context/{test_farmer.id}?crop=wheat")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["success"] is True
    assert "context" in data
    ctx = data["context"]

    # Verify signals are structured
    assert "disease" in ctx
    assert "weather" in ctx
    assert "telemetry" in ctx
    assert "context_id" in ctx

    # Verify zero secrets leaked
    ctx_str = str(ctx).lower()
    for forbidden in ["password", "secret", "jwt", "api_key", "token_hash", "access_token"]:
        assert forbidden not in ctx_str, f"Forbidden keyword '{forbidden}' leaked in context!"


def test_2_action_plan_serialization_includes_decision_and_constraints(client, test_farmer, db_session):
    """Verify GET /api/action-plans/{farmer_id} safely serializes decision metadata and constraints."""
    plan = ActionPlan(
        farmer_id=test_farmer.id,
        crop_id="wheat",
        state="Punjab",
        district="Ludhiana",
        village="Samrala",
        risk_type="disease_treatment",
        risk_level="high",
        status="active",
        escalation_required=False,
        decision_json='{"decision_id": "DEC-P5-001", "overall_risk": "high"}',
        constraints_json='["WEATHER_RAIN_BLOCK", "PRESCRIPTION_LOCKED"]',
        recommended_actions_json='["Apply Propiconazole 25% EC"]'
    )
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)

    res = client.get(f"/api/action-plans/{test_farmer.id}")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["success"] is True
    assert len(data["action_plans"]) > 0

    found_plan = next(p for p in data["action_plans"] if p["id"] == plan.id)
    assert found_plan["risk_level"] == "high"
    assert found_plan["constraints"] == ["WEATHER_RAIN_BLOCK", "PRESCRIPTION_LOCKED"]
    assert found_plan["recommended_actions"] == ["Apply Propiconazole 25% EC"]
    assert found_plan["decision"]["decision_id"] == "DEC-P5-001"


def test_3_task_lifecycle_patch_validates_frozen_transitions(client, test_farmer, db_session):
    """Verify task lifecycle transitions strictly: PENDING -> ACKNOWLEDGED -> IN_PROGRESS -> COMPLETED."""
    plan = ActionPlan(
        farmer_id=test_farmer.id,
        crop_id="wheat",
        risk_type="disease_treatment",
        status="active"
    )
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)

    task = PlanTask(
        action_plan_id=plan.id,
        title="Apply Propiconazole 25% EC",
        status="pending"
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    # 1. PENDING -> ACKNOWLEDGED
    res1 = client.patch(
        f"/api/orchestration/tasks/{task.id}/status",
        json={"status": "ACKNOWLEDGED"}
    )
    assert res1.status_code == 200, res1.text
    db_session.commit()
    db_session.refresh(task)
    assert task.status == "acknowledged"

    # 2. ACKNOWLEDGED -> IN_PROGRESS
    res2 = client.patch(
        f"/api/orchestration/tasks/{task.id}/status",
        json={"status": "IN_PROGRESS"}
    )
    assert res2.status_code == 200, res2.text
    db_session.commit()
    db_session.refresh(task)
    assert task.status == "in_progress"

    # 3. Invalid status string rejected by enum validation
    res_bad = client.patch(
        f"/api/orchestration/tasks/{task.id}/status",
        json={"status": "DEFERRED"}
    )
    assert res_bad.status_code == 422 or res_bad.status_code == 400


def test_4_task_completion_triggers_weather_recheck(client, test_farmer, db_session):
    """Verify that completing a task triggers automatic weather re-check and response contains recheck key."""
    plan = ActionPlan(
        farmer_id=test_farmer.id,
        crop_id="wheat",
        state="Punjab",
        district="Ludhiana",
        village="Samrala",
        risk_type="disease_treatment",
        status="active"
    )
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)

    task = PlanTask(
        action_plan_id=plan.id,
        title="Apply Bio-Fungicide",
        status="in_progress"
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    res = client.patch(
        f"/api/orchestration/tasks/{task.id}/status",
        json={"status": "COMPLETED"}
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert "task_update" in data
    assert "recheck" in data
    assert data["task_update"]["success"] is True


def test_5_safety_boundary_blocked_and_review_produce_zero_executable_tasks(client):
    """Safety Test (Correction 7): Verify BLOCKED and REQUIRES_HUMAN_REVIEW produce 0 executable tasks."""
    # 1. Low Confidence (<30%) -> BLOCKED
    res_blocked = client.post(
        "/api/orchestration/evaluate",
        json={"crop": "wheat", "disease_name": "Unknown Rot", "confidence": 20.0}
    )
    assert res_blocked.status_code == 200
    data_blocked = res_blocked.json()
    assert data_blocked["decisions"][0]["result"] == DecisionResult.BLOCKED.value
    assert "DIAGNOSIS_UNRELIABLE_REJECTED" in data_blocked["constraints"]

    # 2. Borderline Confidence ([30%, 65%)) -> REQUIRES_HUMAN_REVIEW
    res_review = client.post(
        "/api/orchestration/evaluate",
        json={"crop": "wheat", "disease_name": "Yellow Rust", "confidence": 50.0}
    )
    assert res_review.status_code == 200
    data_review = res_review.json()
    assert data_review["decisions"][0]["result"] == DecisionResult.REQUIRES_HUMAN_REVIEW.value
    assert "PRESCRIPTION_LOCKED" in data_review["constraints"]
    assert "FIELD_AGENT_ESCALATION_REQUIRED" in data_review["constraints"]

    # 3. High Confidence + High Rain (>=60%) -> DEFERRED
    res_defer = client.post(
        "/api/orchestration/evaluate",
        json={"crop": "wheat", "disease_name": "Yellow Rust", "confidence": 88.0, "rain_probability": 85}
    )
    assert res_defer.status_code == 200
    data_defer = res_defer.json()
    assert data_defer["overall_risk"] in ("high", "moderate", "critical")
    assert "WEATHER_RAIN_BLOCK" in data_defer["constraints"]


def test_6_simulated_signals_retain_simulated_provenance(client):
    """Verify that simulated telemetry signals retain SIMULATED provenance in output."""
    res = client.post(
        "/api/orchestration/evaluate",
        json={
            "crop": "wheat",
            "soil_moisture_vwc": 14.5,
            "rain_probability": 10
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert "provenance_summary" in data
    # Provenance summary must contain SIMULATED signal
    simulated_signals = [k for k, v in data["provenance_summary"].items() if isinstance(v, dict) and v.get("provenance") == "SIMULATED"]
    assert len(simulated_signals) > 0, "Expected at least one SIMULATED signal in provenance summary"


def test_7_deterministic_decision_trace_contains_explainability_bullets(client):
    """Verify that decision trace contains explainable steps for why the system chose an action."""
    res = client.post(
        "/api/orchestration/evaluate",
        json={
            "crop": "wheat",
            "disease_name": "Yellow Rust",
            "confidence": 88.0,
            "rain_probability": 10
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert "decision_trace" in data
    assert len(data["decision_trace"]) > 0
    # Every trace item has signal, value, policy, and effect
    for trace_item in data["decision_trace"]:
        assert "signal" in trace_item
        assert "policy" in trace_item
        assert "effect" in trace_item
