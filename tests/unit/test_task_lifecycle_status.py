"""
Lifecycle Status Stress Test (Prompt -1b)
Demonstrates:
  Pending -> In Progress -> Completed
using PATCH /api/plan-tasks/{id} and verifying database & trace state.
"""

import sys
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

def test_task_lifecycle():
    print("\n======================================================================")
    print("TASK LIFECYCLE CONTROLLER TEST: PENDING -> IN PROGRESS -> COMPLETED")
    print("======================================================================")

    db = SessionLocal()
    farmer = db.query(Farmer).first()
    if not farmer:
        farmer = Farmer(name="Demo Farmer", location="Amritsar, Punjab")
        db.add(farmer)
        db.commit()
        db.refresh(farmer)

    plan = ActionPlan(
        farmer_id=farmer.id,
        risk_type="disease_treatment",
        status="active"
    )
    db.add(plan)
    db.flush()

    task = PlanTask(
        action_plan_id=plan.id,
        title="Apply Propiconazole 25% EC",
        scheduled_for=datetime.utcnow() + timedelta(hours=6),
        status="pending",
        reasoning="Yellow Rust risk detected at 88% confidence.",
        completed_at=None
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    db.refresh(plan)

    task_id = task.id
    plan_id = plan.id
    print(f"\n[STEP 0: INITIAL STATE] Task #{task_id} initialized with status: '{task.status}'")
    assert task.status == "pending"
    assert task.completed_at is None

    # -------------------------------------------------------------------------
    # Transition 1: Pending -> In Progress
    # -------------------------------------------------------------------------
    print("\n[STEP 1: TRANSITION -> IN PROGRESS]")
    res1 = client.patch(f"/api/plan-tasks/{task_id}", json={"status": "in_progress"})
    assert res1.status_code == 200, res1.text
    data1 = res1.json()
    print(f"  PATCH Response Success : {data1['success']}")
    print(f"  Task Status in DB      : '{data1['task']['status']}'")
    assert data1["task"]["status"] == "in_progress"

    # Verify Trace Output
    trace1 = client.get(f"/api/action-plans/{plan_id}/trace").json()
    latest_event = trace1["trace"][-1]
    print(f"  Trace Event Type       : {latest_event['event_type']} (Task Status: {latest_event['task_status']})")
    assert latest_event["task_status"] == "in_progress"

    # -------------------------------------------------------------------------
    # Transition 2: In Progress -> Completed
    # -------------------------------------------------------------------------
    print("\n[STEP 2: TRANSITION -> COMPLETED / DONE]")
    res2 = client.patch(f"/api/plan-tasks/{task_id}", json={"status": "done"})
    assert res2.status_code == 200, res2.text
    data2 = res2.json()
    print(f"  PATCH Response Success : {data2['success']}")
    print(f"  Task Status in DB      : '{data2['task']['status']}'")
    print(f"  Completed At Timestamp : {data2['task']['completed_at']}")
    assert data2["task"]["status"] == "done"
    assert data2["task"]["completed_at"] is not None

    # Verify Trace Output
    trace2 = client.get(f"/api/action-plans/{plan_id}/trace").json()
    latest_event2 = trace2["trace"][-1]
    print(f"  Trace Event Type       : {latest_event2['event_type']} (Task Status: {latest_event2['task_status']})")
    assert latest_event2["event_type"] == "TASK_COMPLETED"
    assert latest_event2["task_status"] == "done"

    # -------------------------------------------------------------------------
    # Transition 3: Completed -> Back to Pending
    # -------------------------------------------------------------------------
    print("\n[STEP 3: TRANSITION BACK -> PENDING]")
    res3 = client.patch(f"/api/plan-tasks/{task_id}", json={"status": "pending"})
    assert res3.status_code == 200, res3.text
    data3 = res3.json()
    print(f"  PATCH Response Success : {data3['success']}")
    print(f"  Task Status in DB      : '{data3['task']['status']}'")
    print(f"  Completed At Reset     : {data3['task']['completed_at']}")
    assert data3["task"]["status"] == "pending"
    assert data3["task"]["completed_at"] is None

    db.close()
    print("\n======================================================================")
    print("ALL TASK LIFECYCLE TRANSITIONS VERIFIED END-TO-END IN DATABASE & UI TRACE!")
    print("======================================================================")

if __name__ == "__main__":
    test_task_lifecycle()

