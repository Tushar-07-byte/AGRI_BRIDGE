"""
Test Suite: Autonomous Replanning & Agent Trace Verification
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.models.action_plan import ActionPlan, PlanTask
from app.models.farmer import Farmer

client = TestClient(app)

def run_replanning_test():
    print("\n======================================================================")
    print("TEST: AUTONOMOUS REPLANNING & AGENT TRACE VERIFICATION")
    print("======================================================================")

    db = SessionLocal()
    farmer = db.query(Farmer).first()
    if not farmer:
        farmer = Farmer(name="Kavita Devi")
        db.add(farmer)
        db.commit()
        db.refresh(farmer)

    # 1. Create Initial Action Plan with LOW RAIN RISK (Favorable immediate spray)
    initial_plan = ActionPlan(
        farmer_id=farmer.id,
        listing_id=None,
        risk_type="disease_treatment",
        status="active",
        created_at=datetime.utcnow() - timedelta(hours=2),
        updated_at=datetime.utcnow() - timedelta(hours=2)
    )
    db.add(initial_plan)
    db.flush()

    initial_task = PlanTask(
        action_plan_id=initial_plan.id,
        title="Apply Mancozeb 75% WP @ 2.5g/L",
        scheduled_for=datetime.utcnow() + timedelta(hours=4),
        status="pending",
        reasoning="Early Blight detected at 91% confidence. Forecast indicates clear dry weather (12% rain risk) — immediate foliar spray recommended for maximum adhesion.",
        completed_at=None
    )
    db.add(initial_task)
    db.commit()
    db.refresh(initial_plan)
    db.refresh(initial_task)

    plan_id = initial_plan.id
    old_task_id = initial_task.id
    print(f"Step 1: Created Initial Action Plan #{plan_id} with Initial Task #{old_task_id}")
    print(f"  Initial Task Status:    {initial_task.status}")
    print(f"  Initial Task Reasoning: {initial_task.reasoning}")

    # 2. Trigger Recheck with SIMULATED HIGH RAIN FORECAST (85% Rain Surge)
    print("\nStep 2: Triggering POST /api/action-plans/{id}/recheck with high rain forecast (85%)...")
    recheck_payload = {
        "simulated_rain_probability": 85,
        "simulated_rainfall_mm": 18.5,
        "simulated_weather_condition": "Heavy convective thunderstorm expected",
        "recommended_window": "2026-09-08 (Sunny & Dry Window)"
    }

    recheck_resp = client.post(
        f"/api/action-plans/{plan_id}/recheck",
        json=recheck_payload
    )

    assert recheck_resp.status_code == 200, f"Recheck failed: {recheck_resp.text}"
    recheck_data = recheck_resp.json()
    print("Recheck API Response:")
    print(json.dumps(recheck_data, indent=2))

    assert recheck_data["change_detected"] is True
    assert recheck_data["superseded_task_id"] == old_task_id
    new_task_id = recheck_data["new_task"]["id"]

    # 3. Query MySQL Database to verify old task is superseded (NOT deleted) and new task exists
    db.close()
    fresh_db = SessionLocal()
    tasks_in_db = fresh_db.query(PlanTask).filter(PlanTask.action_plan_id == plan_id).order_by(PlanTask.id.asc()).all()

    print("\nStep 3: Database Verification (Both tasks preserved side-by-side):")
    print(f"Total Tasks under Plan #{plan_id}: {len(tasks_in_db)}")
    for t in tasks_in_db:
        print(f"  Task #{t.id} | Status: [{t.status.upper()}] | Title: '{t.title}'")
        print(f"    Reasoning: \"{t.reasoning}\"\n")

    assert len(tasks_in_db) == 2
    assert tasks_in_db[0].status == "superseded"
    assert tasks_in_db[1].status == "pending"

    # 4. Test GET /api/action-plans/{id}/trace
    print("\nStep 4: Testing GET /api/action-plans/{id}/trace (Agent Trace)...")
    trace_resp = client.get(f"/api/action-plans/{plan_id}/trace")
    assert trace_resp.status_code == 200
    trace_data = trace_resp.json()

    print("======================================================================")
    print(f"AGENT TRACE OUTPUT FOR ACTION PLAN #{plan_id}:")
    print("======================================================================")
    print(json.dumps(trace_data, indent=2))

    assert trace_data["success"] is True
    assert len(trace_data["trace"]) >= 3
    print("\n======================================================================")
    print("ALL REPLANNING & AGENT TRACE TESTS PASSED PERFECTLY!")
    print("======================================================================")
    fresh_db.close()

if __name__ == "__main__":
    run_replanning_test()
