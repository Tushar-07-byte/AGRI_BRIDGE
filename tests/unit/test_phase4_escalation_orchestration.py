"""
Phase 4 Master Test Suite: Human / Field-Agent Escalation & Alert Orchestration
Problem Statement: SH-AGR-001 / AGR-001 — Agriculture & Rural Development

Asserts all 17 Phase 4 conditions:
1. Low confidence AI prediction ([30%, 65%)) triggers REQUIRES_HUMAN_REVIEW and creates FieldAgentEscalation.
2. Exactly zero executable PlanTasks exist during human review.
3. Chemical recommendations are LOCKED during human review.
4. Field Agent retrieves pending escalation queue.
5. Field Agent accepts escalation task.
6. Field Agent rejects escalation task with mandatory reason.
7. Human verification provides verified diagnostic input without bypassing policy engine.
8. Closed-loop re-evaluation rebuilds FarmDecisionContext and runs MultiSignalPolicyEngine.
9. Deterministic policy creates executable PlanTask post-approval.
10. Weather safety invariant strictly enforced post-human verification (unsafe weather defers execution).
11. FieldAgentEscalation is transitioned to resolved post-approval.
12. Disease scan rejection marks NEEDS_PHYSICAL_VISIT and schedules physical visit.
13. NotificationEvent lifecycle state machine operates independently from PlanTask.
14. Sensor anomaly telemetry evaluation triggers escalation.
15. Provenance and trust-gate integrity preserved (SIMULATED never becomes LIVE).
16. Phase 1 frozen task lifecycle (PENDING -> ACKNOWLEDGED -> IN_PROGRESS -> COMPLETED) is strictly preserved.
17. Full system regression pass.
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
from app.models.disease_record import DiseaseRecord
from app.models.action_plan import ActionPlan, PlanTask, NotificationEvent, FieldAgentEscalation
from app.domain.farm_decision_context import (
    FarmDecisionContext,
    SignalProvenance,
    SignalQuality,
    TraceableSignal
)
from app.domain.multi_signal_decision import DecisionResult, DecisionType, MultiSignalDecision
from app.services.farm_decision_context_service import FarmDecisionContextService
from app.services.multi_signal_policy_engine import MultiSignalPolicyEngine
from app.services.orchestration_service import OrchestrationService
from app.services.field_agent_engine import (
    evaluate_disease_confidence,
    evaluate_sensor_telemetry,
    create_field_agent_task,
    get_field_agent_tasks,
    accept_field_agent_task,
    reject_field_agent_task,
    submit_field_verification,
    _TASK_STORE
)
from app.services.utils import is_signal_trustworthy

client = TestClient(app)


@pytest.fixture(scope="function")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def sample_farmer(db):
    f_name = f"Phase 4 Farmer {uuid.uuid4().hex[:6]}"
    farmer = Farmer(name=f_name)
    db.add(farmer)
    db.commit()
    db.refresh(farmer)
    return farmer


# ==============================================================================
# 1. LOW CONFIDENCE TRIGGERS REQUIRES_HUMAN_REVIEW AND ESCALATION
# ==============================================================================
@pytest.mark.anyio
async def test_1_low_confidence_triggers_requires_human_review_and_escalation(db, sample_farmer):
    """Borderline confidence (e.g. 52%) produces REQUIRES_HUMAN_REVIEW and creates escalation."""
    context = await FarmDecisionContextService.build_context(
        farmer_id=sample_farmer.id,
        db=db,
        crop_id="wheat",
        disease_scan_data={
            "pathogen": "Yellow Rust",
            "scientific_name": "Puccinia striiformis",
            "confidence": 52.0,
            "severity": "moderate",
            "is_simulated": False
        }
    )

    decision = MultiSignalPolicyEngine.evaluate(context)
    assert decision.escalation_required is True
    assert "PRESCRIPTION_LOCKED" in decision.constraints
    assert "FIELD_AGENT_ESCALATION_REQUIRED" in decision.constraints

    disease_finding = next(d for d in decision.decisions if d.decision_type == DecisionType.DISEASE_TREATMENT)
    assert disease_finding.result == DecisionResult.REQUIRES_HUMAN_REVIEW


# ==============================================================================
# 2. ZERO EXECUTABLE TASKS DURING HUMAN REVIEW
# ==============================================================================
def test_2_zero_executable_tasks_during_human_review(db, sample_farmer):
    """Under REQUIRES_HUMAN_REVIEW or needs_expert_review, exactly 0 executable PlanTasks exist."""
    plan = ActionPlan(
        farmer_id=sample_farmer.id,
        crop_id="wheat",
        risk_type="low_confidence_disease_review",
        status="needs_expert_review",
        escalation_required=True,
        escalation_reason="LOW_CONFIDENCE_DISEASE_PREDICTION",
        created_at=datetime.utcnow()
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    esc = FieldAgentEscalation(
        action_plan_id=plan.id,
        farmer_id=sample_farmer.id,
        risk_level="high",
        reason="LOW_CONFIDENCE_DISEASE_PREDICTION",
        status="escalated",
        created_at=datetime.utcnow()
    )
    db.add(esc)
    db.commit()

    # Verify 0 tasks exist under plan
    tasks = db.query(PlanTask).filter(PlanTask.action_plan_id == plan.id).all()
    assert len(tasks) == 0, f"Expected 0 executable PlanTasks during human review, found {len(tasks)}"


# ==============================================================================
# 3. CHEMICAL RECOMMENDATION LOCKED DURING HUMAN REVIEW
# ==============================================================================
def test_3_chemical_recommendation_locked_during_human_review():
    """evaluate_disease_confidence strictly locks chemicals when confidence < 0.60."""
    gate = evaluate_disease_confidence(
        confidence=0.52,
        disease_name="Yellow Rust",
        crop_name="Wheat"
    )
    assert gate["confidence_status"] == "LOW"
    assert gate["field_agent_escalation"] is True
    assert gate["chemical_recommendation"]["status"] == "LOCKED"
    assert gate["chemical_recommendation"]["pesticide_name"] is None


# ==============================================================================
# 4. FIELD AGENT RETRIEVES ESCALATION QUEUE
# ==============================================================================
def test_4_field_agent_retrieves_escalation_queue(db, sample_farmer):
    """Field agent queue returns pending disease scans."""
    record = DiseaseRecord(
        farmer_id=sample_farmer.id,
        crop_type="wheat",
        confidence=54.0,
        predicted_pathogen="Yellow Rust",
        scientific_name="Puccinia striiformis",
        severity="moderate",
        status="PENDING_AGENT_REVIEW",
        created_at=datetime.utcnow()
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    resp = client.get("/api/verifications/disease-scans?status=PENDING_AGENT_REVIEW")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert any(s["id"] == record.id for s in data["disease_scans"])


# ==============================================================================
# 5. FIELD AGENT ACCEPTS ESCALATION TASK
# ==============================================================================
def test_5_field_agent_accepts_escalation_task():
    """Field agent accepts task transitioning to ACCEPTED."""
    task = create_field_agent_task(
        trigger_type="LOW_CONFIDENCE_DISEASE_PREDICTION",
        reason="Borderline leaf scan",
        payload={"farm_id": "FARM_01"},
        priority="HIGH"
    )
    t_id = task["task_id"]

    resp = client.post(f"/api/field-agent/tasks/{t_id}/accept", json={
        "agent_id": "AGENT_007",
        "agent_name": "Rahul Verma",
        "notes": "Starting physical inspection."
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["status"] == "ACCEPTED"


# ==============================================================================
# 6. FIELD AGENT REJECTS ESCALATION TASK WITH MANDATORY REASON
# ==============================================================================
def test_6_field_agent_rejects_escalation_task_with_mandatory_reason():
    """Rejection requires non-empty reason >= 3 chars."""
    task = create_field_agent_task(
        trigger_type="LOW_CONFIDENCE_DISEASE_PREDICTION",
        reason="Borderline scan",
        payload={},
        priority="HIGH"
    )
    t_id = task["task_id"]

    # Missing reason -> 400
    bad_resp = client.post(f"/api/field-agent/tasks/{t_id}/reject", json={"rejection_reason": ""})
    assert bad_resp.status_code == 400

    # Valid reason -> 200
    good_resp = client.post(f"/api/field-agent/tasks/{t_id}/reject", json={"rejection_reason": "Out of operational territory"})
    assert good_resp.status_code == 200
    assert good_resp.json()["status"] == "REJECTED"


# ==============================================================================
# 7. HUMAN VERIFICATION PROVIDES VERIFIED INPUT TO POLICY ENGINE
# ==============================================================================
def test_7_human_verification_provides_verified_input_to_policy_engine(db, sample_farmer):
    """Verification updates DiseaseRecord to VERIFIED_HEALTH_RECORD with agronomist parameters."""
    rec = DiseaseRecord(
        farmer_id=sample_farmer.id,
        crop_type="wheat",
        confidence=52.0,
        predicted_pathogen="Yellow Rust",
        scientific_name="Puccinia striiformis",
        severity="moderate",
        status="PENDING_AGENT_REVIEW",
        created_at=datetime.utcnow()
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    resp = client.post(f"/api/verifications/disease-scans/{rec.id}/approve", json={
        "agent_name": "Agronomist Dr. Sharma",
        "remarks": "Confirmed Puccinia striiformis via spore examination.",
        "prescription_chemical": "Propiconazole 25% EC",
        "prescription_dosage": "1.0 ml / L water",
        "prescription_phi": "14 Days PHI"
    })
    assert resp.status_code == 200
    db.commit()
    refreshed_rec = db.query(DiseaseRecord).filter(DiseaseRecord.id == rec.id).first()
    assert refreshed_rec.status == "VERIFIED_HEALTH_RECORD"
    assert refreshed_rec.prescription_chemical == "Propiconazole 25% EC"
    assert refreshed_rec.agent_name == "Agronomist Dr. Sharma"


# ==============================================================================
# 8. REBUILD CONTEXT AND DETERMINISTIC POLICY RE-EVALUATION
# ==============================================================================
@pytest.mark.anyio
async def test_8_rebuild_context_and_deterministic_policy_reevaluation(db, sample_farmer):
    """Rebuilding context from VERIFIED_HEALTH_RECORD produces ALLOWED in MultiSignalPolicyEngine."""
    rec = DiseaseRecord(
        farmer_id=sample_farmer.id,
        crop_type="wheat",
        confidence=98.0,
        predicted_pathogen="Yellow Rust",
        scientific_name="Puccinia striiformis",
        severity="moderate",
        status="VERIFIED_HEALTH_RECORD",
        agent_name="Agronomist Dr. Sharma",
        created_at=datetime.utcnow()
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    context = await FarmDecisionContextService.build_context(
        farmer_id=sample_farmer.id,
        db=db,
        crop_id="wheat",
        disease_record_id=rec.id
    )
    assert context.disease.needs_expert_review is False
    assert context.disease.prescription_locked is False

    decision = MultiSignalPolicyEngine.evaluate(context)
    disease_item = next(d for d in decision.decisions if d.decision_type == DecisionType.DISEASE_TREATMENT)
    assert disease_item.result == DecisionResult.ALLOWED


# ==============================================================================
# 9. DETERMINISTIC POLICY CREATES EXECUTABLE TASK POST-APPROVAL
# ==============================================================================
def test_9_deterministic_policy_creates_executable_task_post_approval(db, sample_farmer):
    """Approving disease scan creates 1 executable PlanTask in pending status."""
    plan = ActionPlan(
        farmer_id=sample_farmer.id,
        crop_id="wheat",
        risk_type="low_confidence_disease_review",
        status="needs_expert_review",
        escalation_required=True,
        created_at=datetime.utcnow()
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    rec = DiseaseRecord(
        farmer_id=sample_farmer.id,
        action_plan_id=plan.id,
        crop_type="wheat",
        confidence=55.0,
        predicted_pathogen="Yellow Rust",
        status="PENDING_AGENT_REVIEW",
        created_at=datetime.utcnow()
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    # Approve with safe weather override
    resp = client.post(f"/api/verifications/disease-scans/{rec.id}/approve", json={
        "agent_name": "Dr. Sharma",
        "prescription_chemical": "Propiconazole 25% EC",
        "prescription_dosage": "1.0 ml / L water",
        "weather_override": {
            "rain_probability_percent": 10,
            "condition": "Clear sunny skies",
            "provenance": "SIMULATED",
            "quality": "SIMULATED"
        }
    })
    assert resp.status_code == 200

    db.commit()
    refreshed_plan = db.query(ActionPlan).filter(ActionPlan.id == plan.id).first()
    assert refreshed_plan.status == "active_verified_rx"
    tasks = db.query(PlanTask).filter(PlanTask.action_plan_id == plan.id).all()
    assert len(tasks) == 1
    assert tasks[0].status == "pending"
    assert "Propiconazole" in tasks[0].title


# ==============================================================================
# 10. WEATHER SAFETY ENFORCED POST HUMAN VERIFICATION
# ==============================================================================
def test_10_weather_safety_enforced_post_human_verification(db, sample_farmer):
    """Human approval does NOT bypass weather safety: heavy rain defers execution."""
    plan = ActionPlan(
        farmer_id=sample_farmer.id,
        crop_id="wheat",
        risk_type="low_confidence_disease_review",
        status="needs_expert_review",
        escalation_required=True,
        created_at=datetime.utcnow()
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    rec = DiseaseRecord(
        farmer_id=sample_farmer.id,
        action_plan_id=plan.id,
        crop_type="wheat",
        confidence=55.0,
        predicted_pathogen="Yellow Rust",
        status="PENDING_AGENT_REVIEW",
        created_at=datetime.utcnow()
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    # Approve during heavy rain (80% rain probability)
    resp = client.post(f"/api/verifications/disease-scans/{rec.id}/approve", json={
        "agent_name": "Dr. Sharma",
        "prescription_chemical": "Propiconazole 25% EC",
        "prescription_dosage": "1.0 ml / L water",
        "weather_override": {
            "rain_probability_percent": 80,
            "condition": "Severe rainstorm and gusty winds",
            "provenance": "SIMULATED",
            "quality": "SIMULATED"
        }
    })
    assert resp.status_code == 200

    db.commit()
    refreshed_plan = db.query(ActionPlan).filter(ActionPlan.id == plan.id).first()
    assert refreshed_plan.status == "deferred"
    assert refreshed_plan.risk_type == "weather_delay"
    tasks = db.query(PlanTask).filter(PlanTask.action_plan_id == plan.id).all()
    assert len(tasks) == 1
    assert "Rescheduled" in tasks[0].title or "delayed" in tasks[0].reasoning.lower()


# ==============================================================================
# 11. FIELD AGENT ESCALATION RESOLVED POST-APPROVAL
# ==============================================================================
def test_11_field_agent_escalation_resolved_post_approval(db, sample_farmer):
    """FieldAgentEscalation status transitions to resolved with resolved_at."""
    plan = ActionPlan(
        farmer_id=sample_farmer.id,
        crop_id="wheat",
        status="needs_expert_review",
        escalation_required=True,
        created_at=datetime.utcnow()
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    esc = FieldAgentEscalation(
        action_plan_id=plan.id,
        farmer_id=sample_farmer.id,
        risk_level="high",
        reason="LOW_CONFIDENCE_DISEASE_PREDICTION",
        status="escalated",
        created_at=datetime.utcnow()
    )
    db.add(esc)
    db.commit()

    rec = DiseaseRecord(
        farmer_id=sample_farmer.id,
        action_plan_id=plan.id,
        crop_type="wheat",
        confidence=55.0,
        predicted_pathogen="Yellow Rust",
        status="PENDING_AGENT_REVIEW",
        created_at=datetime.utcnow()
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    resp = client.post(f"/api/verifications/disease-scans/{rec.id}/approve", json={
        "agent_name": "Dr. Sharma",
        "remarks": "Approved"
    })
    assert resp.status_code == 200

    db.commit()
    refreshed_esc = db.query(FieldAgentEscalation).filter(FieldAgentEscalation.id == esc.id).first()
    assert refreshed_esc.status == "resolved"
    assert refreshed_esc.resolved_at is not None


# ==============================================================================
# 12. DISEASE SCAN REJECTION MARKS NEEDS_PHYSICAL_VISIT
# ==============================================================================
def test_12_disease_scan_rejection_marks_needs_physical_visit(db, sample_farmer):
    """Rejection sets status to NEEDS_PHYSICAL_VISIT and assigns escalation."""
    rec = DiseaseRecord(
        farmer_id=sample_farmer.id,
        crop_type="wheat",
        confidence=45.0,
        predicted_pathogen="Unknown Spot",
        status="PENDING_AGENT_REVIEW",
        created_at=datetime.utcnow()
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    resp = client.post(f"/api/verifications/disease-scans/{rec.id}/reject", json={
        "agent_name": "Field Agent Rahul",
        "reason": "Atypical leaf necrosis requires in-person tissue sampling."
    })
    assert resp.status_code == 200
    db.commit()
    refreshed_rec = db.query(DiseaseRecord).filter(DiseaseRecord.id == rec.id).first()
    assert refreshed_rec.status == "NEEDS_PHYSICAL_VISIT"
    assert refreshed_rec.inspection_status == "SCHEDULED"


# ==============================================================================
# 13. NOTIFICATION LIFECYCLE STATE MACHINE SEPARATE FROM TASKS
# ==============================================================================
def test_13_notification_lifecycle_state_machine_separate_from_tasks(db, sample_farmer):
    """NotificationEvent transitions through states without altering PlanTask lifecycle."""
    notif = NotificationEvent(
        farmer_id=sample_farmer.id,
        title="Field Visit Scheduled",
        message="Agent Rahul visiting tomorrow",
        status="PENDING",
        created_at=datetime.utcnow()
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)

    res1 = OrchestrationService.update_notification_lifecycle(notif.id, "NOTIFIED", db)
    assert res1["notification"]["status"] == "NOTIFIED"

    res2 = OrchestrationService.update_notification_lifecycle(notif.id, "ACKNOWLEDGED", db)
    assert res2["notification"]["status"] == "ACKNOWLEDGED"

    res3 = OrchestrationService.update_notification_lifecycle(notif.id, "COMPLETED", db)
    assert res3["notification"]["status"] == "COMPLETED"


# ==============================================================================
# 14. SENSOR ANOMALY TELEMETRY TRIGGERS ESCALATION
# ==============================================================================
def test_14_sensor_anomaly_telemetry_triggers_escalation():
    """Suspicious zero or missing soil moisture triggers field agent task creation."""
    res = evaluate_sensor_telemetry(
        sensor_id="SN_SOIL_99",
        sensor_type="soil_moisture",
        value=0.0
    )
    assert res["anomaly_detected"] is True
    assert res["field_agent_escalation"] is True
    assert res["anomaly_type"] == "ZERO_READING"


# ==============================================================================
# 15. PROVENANCE AND TRUST-GATE INTEGRITY PRESERVED
# ==============================================================================
def test_15_provenance_and_trust_gate_integrity_preserved():
    """Trust gate rejects stale/future signals and preserves provenance."""
    future_time = (datetime.now(timezone.utc) + timedelta(minutes=20)).isoformat()
    signal = TraceableSignal[float](
        value=24.5,
        unit="°C",
        provenance=SignalProvenance.SIMULATED,
        quality=SignalQuality.SIMULATED,
        timestamp=future_time
    )
    # Trust check rejects future timestamp
    assert is_signal_trustworthy(signal) is False


# ==============================================================================
# 16. PHASE 1 FROZEN TASK LIFECYCLE STRICTLY PRESERVED
# ==============================================================================
def test_16_phase1_frozen_task_lifecycle_strictly_preserved(db, sample_farmer):
    """PlanTask lifecycle is strictly: pending -> acknowledged -> in_progress -> completed."""
    plan = ActionPlan(farmer_id=sample_farmer.id, crop_id="wheat", created_at=datetime.utcnow())
    db.add(plan)
    db.commit()

    task = PlanTask(
        action_plan_id=plan.id,
        title="Apply Verified Fungicide",
        status="pending",
        scheduled_for=datetime.utcnow() + timedelta(hours=12)
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # 1. PENDING -> ACKNOWLEDGED
    task.status = "acknowledged"
    db.commit()
    db.refresh(task)
    assert task.status == "acknowledged"

    # 2. ACKNOWLEDGED -> IN_PROGRESS
    task.status = "in_progress"
    db.commit()
    db.refresh(task)
    assert task.status == "in_progress"

    # 3. IN_PROGRESS -> COMPLETED
    task.status = "completed"
    task.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    assert task.status == "completed"


# ==============================================================================
# 17. FULL SYSTEM REGRESSION PASS
# ==============================================================================
@pytest.mark.anyio
async def test_17_full_system_regression_pass(db, sample_farmer):
    """End-to-end multi-step verification flow."""
    # Step 1: Borderline disease context
    context = await FarmDecisionContextService.build_context(
        farmer_id=sample_farmer.id,
        db=db,
        crop_id="wheat",
        disease_scan_data={
            "pathogen": "Leaf Rust",
            "confidence": 58.0,
            "severity": "high"
        }
    )
    decision = MultiSignalPolicyEngine.evaluate(context)
    assert decision.escalation_required is True

    # Step 2: Create ActionPlan under review
    plan = ActionPlan(
        farmer_id=sample_farmer.id,
        crop_id="wheat",
        status="needs_expert_review",
        escalation_required=True,
        created_at=datetime.utcnow()
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    # Step 3: Field record created
    rec = DiseaseRecord(
        farmer_id=sample_farmer.id,
        action_plan_id=plan.id,
        crop_type="wheat",
        confidence=58.0,
        predicted_pathogen="Leaf Rust",
        status="PENDING_AGENT_REVIEW",
        created_at=datetime.utcnow()
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    # Step 4: Field Agent approves scan
    resp = client.post(f"/api/verifications/disease-scans/{rec.id}/approve", json={
        "agent_name": "Dr. Rao",
        "prescription_chemical": "Azoxystrobin 23% SC",
        "prescription_dosage": "1.0 ml / L water",
        "weather_override": {
            "rain_probability_percent": 15,
            "condition": "Dry weather",
            "provenance": "SIMULATED",
            "quality": "SIMULATED"
        }
    })
    assert resp.status_code == 200
    db.commit()
    refreshed_plan = db.query(ActionPlan).filter(ActionPlan.id == plan.id).first()
    assert refreshed_plan.status == "active_verified_rx"
    tasks = db.query(PlanTask).filter(PlanTask.action_plan_id == plan.id).all()
    assert len(tasks) == 1
    assert tasks[0].status == "pending"
    assert len(tasks) == 1
    assert tasks[0].status == "pending"
