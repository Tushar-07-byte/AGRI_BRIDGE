"""
Stress Test: Repeated Replanning Simulation (Prompt -2)
Tests:
1. 5 consecutive simulated rain surges on the same action plan.
2. Fresh plan vs. already-replanned plan.
3. Page refresh / trace endpoint integrity verification.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta

# Ensure UTF-8 stdout on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.models.action_plan import ActionPlan, PlanTask
from app.models.farmer import Farmer

client = TestClient(app)

def run_stress_test():
    print("\n======================================================================")
    print("STRESS TEST: 'SIMULATE RAIN SURGE' REPEATED REPLANNING (PROMPT -2)")
    print("======================================================================")

    db = SessionLocal()
    farmer = db.query(Farmer).first()
    if not farmer:
        farmer = Farmer(name="Balwinder Singh", location="Amritsar, Punjab")
        db.add(farmer)
        db.commit()
        db.refresh(farmer)

    # -------------------------------------------------------------------------
    # PART 1: Fresh Action Plan Creation
    # -------------------------------------------------------------------------
    fresh_plan = ActionPlan(
        farmer_id=farmer.id,
        risk_type="disease_treatment",
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(fresh_plan)
    db.flush()

    task_1 = PlanTask(
        action_plan_id=fresh_plan.id,
        title="Apply Dimethomorph + Mancozeb 75% WP",
        scheduled_for=datetime.utcnow() + timedelta(hours=3),
        status="pending",
        reasoning="Late Blight detected at 92% confidence. Dry weather forecast (10% rain risk). Immediate spray recommended.",
        completed_at=None
    )
    db.add(task_1)
    db.commit()
    db.refresh(fresh_plan)
    db.refresh(task_1)

    plan_id = fresh_plan.id
    print(f"\n[INIT] Created Fresh Action Plan #{plan_id} with Initial Task #{task_1.id} ('{task_1.title}')")

    # -------------------------------------------------------------------------
    # PART 2: Click 5 Times in a Row ("Simulate Rain Surge")
    # -------------------------------------------------------------------------
    print("\n----------------------------------------------------------------------")
    print("EXECUTING 5 CONSECUTIVE 'SIMULATE RAIN SURGE' CALLS ON PLAN #" + str(plan_id))
    print("----------------------------------------------------------------------")

    for click_num in range(1, 6):
        res = client.post(
            f"/api/action-plans/{plan_id}/recheck",
            json={
                "simulated_rain_probability": 85,
                "simulated_weather_condition": f"Rain surge simulation iteration #{click_num}",
                "recommended_window": f"Day +{click_num * 2} Window",
                "force_change": True
            }
        )
        assert res.status_code == 200, f"Click #{click_num} failed with {res.status_code}: {res.text}"
        data = res.json()
        print(f"\n>>> CLICK #{click_num}:")
        print(f"    HTTP Status        : {res.status_code}")
        print(f"    Change Detected    : {data.get('change_detected')}")
        print(f"    Change Type        : {data.get('change_type')}")
        print(f"    Superseded Task ID : {data.get('superseded_task_id')}")
        print(f"    New Task ID        : {data.get('new_task', {}).get('id')}")
        print(f"    New Task Title     : '{data.get('new_task', {}).get('title')}'")
        print(f"    New Task Reasoning : '{data.get('new_task', {}).get('reasoning')[:80]}...'")

    # -------------------------------------------------------------------------
    # PART 3: Verify Database State (Tasks and Statuses)
    # -------------------------------------------------------------------------
    db.close()
    verify_db = SessionLocal()
    all_tasks = (
        verify_db.query(PlanTask)
        .filter(PlanTask.action_plan_id == plan_id)
        .order_by(PlanTask.id.asc())
        .all()
    )

    print("\n----------------------------------------------------------------------")
    print(f"DATABASE VERIFICATION: TOTAL TASKS UNDER PLAN #{plan_id}: {len(all_tasks)} (Expect 6: 1 original + 5 replans)")
    print("----------------------------------------------------------------------")
    assert len(all_tasks) == 6, f"Expected 6 tasks, found {len(all_tasks)}"

    for idx, t in enumerate(all_tasks, 1):
        print(f"  [{idx}] Task #{t.id} | Status: [{t.status.upper():10}] | Title: '{t.title}'")
        if idx < 6:
            assert t.status == "superseded", f"Task #{t.id} should be superseded"
        else:
            assert t.status == "pending", f"Task #{t.id} should be active pending"

    # -------------------------------------------------------------------------
    # PART 4: Simulate Page Refresh (Calling Trace API)
    # -------------------------------------------------------------------------
    print("\n----------------------------------------------------------------------")
    print(f"SIMULATING PAGE REFRESH: GET /api/action-plans/{plan_id}/trace")
    print("----------------------------------------------------------------------")
    trace_res = client.get(f"/api/action-plans/{plan_id}/trace")
    assert trace_res.status_code == 200
    trace_data = trace_res.json()

    print(f"Trace Response Success : {trace_data['success']}")
    print(f"Total Tasks Recorded   : {trace_data['total_tasks_recorded']}")
    print(f"Trace Event Count      : {len(trace_data['trace'])}")

    print("\nFull Chronological Timeline Stream:")
    for evt in trace_data["trace"]:
        print(f"  Step {evt['step']}: [{evt['event_type']:22}] -> {evt.get('summary') or evt.get('task_title')}")

    assert trace_data["total_tasks_recorded"] == 6
    assert len(trace_data["trace"]) == 12  # 1 init + 5 * (1 superseded + 1 replan trigger) + 1 active task
    verify_db.close()

    print("\n======================================================================")
    print("STRESS TEST COMPLETED SUCCESSFULLY WITH 100% INTEGRITY!")
    print("======================================================================")

if __name__ == "__main__":
    run_stress_test()

