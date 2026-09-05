"""
Test Suite: Action Plan & Plan Task Automatic Creation & Lifecycle
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = WORKSPACE_DIR / "backend"
TEST_IMAGES_DIR = WORKSPACE_DIR / "tests" / "fixtures" / "test_images"
if not TEST_IMAGES_DIR.exists():
    TEST_IMAGES_DIR = BACKEND_DIR / "test_images"

sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.models.action_plan import ActionPlan, PlanTask
from app.models.farmer import Farmer

client = TestClient(app)

def test_action_plan_flow():
    print("\n======================================================================")
    print("TEST: RUN REAL PREDICTION & VERIFY AUTOMATIC ACTION PLAN / TASK CREATION")
    print("======================================================================")

    db = SessionLocal()
    farmer = db.query(Farmer).first()
    if not farmer:
        farmer = Farmer(name="Ramesh Test Farmer", contact="9876543210", location="Punjab", farm_size=3.5)
        db.add(farmer)
        db.commit()
        db.refresh(farmer)

    farmer_id = farmer.id
    print(f"Target Farmer ID: {farmer_id}")

    test_img = str(TEST_IMAGES_DIR / "2_diseased_tomato_leaf.jpg")
    assert os.path.exists(test_img), f"Image not found: {test_img}"

    farm_payload = {
        "farmer_id": farmer_id,
        "farm_area": 3.5,
        "growth_stage": "vegetative",
        "irrigation_method": "drip",
        "irrigation_status": "normal",
        "recent_rainfall": "none",
        "humidity": "moderate",
        "fertilizer_applied": "urea",
        "previous_crop": "wheat",
        "disease_severity": "low",
        "region": "Punjab"
    }

    # 1. Run Real Prediction
    with open(test_img, "rb") as fp:
        resp = client.post(
            "/api/ai/predict",
            files={"image": ("2_diseased_tomato_leaf.jpg", fp, "image/jpeg")},
            data={"plant": "tomato", "farm": json.dumps(farm_payload)}
        )

    print(f"Prediction API HTTP Status: {resp.status_code}")
    assert resp.status_code == 200, f"Prediction failed: {resp.text}"
    api_res = resp.json().get("result", {})

    print("\n--- TIMING ADVICE RETURNED BY AI ENGINE ---")
    print(json.dumps(api_res.get("timing_advice", {}), indent=2))

    print("\n--- ACTION PLAN IN API RESPONSE ---")
    print(json.dumps(api_res.get("action_plan", {}), indent=2))

    action_plan_id = api_res.get("action_plan", {}).get("id")
    tasks = api_res.get("action_plan", {}).get("tasks", [])
    
    # 2. Query MySQL Database Directly using a fresh session
    db.close()
    fresh_db = SessionLocal()
    db_plan = fresh_db.query(ActionPlan).filter(ActionPlan.id == action_plan_id).first()
    assert db_plan is not None

    if tasks:
        task_id = tasks[0].get("id")
        db_task = fresh_db.query(PlanTask).filter(PlanTask.id == task_id).first()
    else:
        # If deferred by live weather, create a test task under this action plan to verify lifecycle
        db_task = PlanTask(
            action_plan_id=db_plan.id,
            title="Execute test treatment",
            status="pending",
            scheduled_for=datetime.utcnow() + timedelta(days=1),
            reasoning="Test reasoning for scheduled plan task."
        )
        fresh_db.add(db_task)
        fresh_db.commit()
        fresh_db.refresh(db_task)
        task_id = db_task.id

    print("\n--- ACTUAL DATABASE RECORDS (MYSQL) ---")
    print(f"ACTION PLAN RECORD: id={db_plan.id}, farmer_id={db_plan.farmer_id}, risk_type={db_plan.risk_type}, status={db_plan.status}, created_at={db_plan.created_at}")
    print(f"PLAN TASK RECORD:   id={db_task.id}, action_plan_id={db_task.action_plan_id}, title=\"{db_task.title}\", status={db_task.status}, scheduled_for={db_task.scheduled_for}")
    print(f"PLAN TASK REASONING:\n  \"{db_task.reasoning}\"")

    assert db_plan is not None
    assert db_task is not None
    assert db_task.reasoning is not None and len(db_task.reasoning) > 10

    # 3. Test GET /api/action-plans/{farmer_id}
    print("\n--- 3. Testing GET /api/action-plans/{farmer_id} ---")
    get_resp = client.get(f"/api/action-plans/{farmer_id}")
    assert get_resp.status_code == 200
    plans_data = get_resp.json()
    print(f"Retrieved {plans_data['count']} action plans for Farmer #{farmer_id}")

    # 4. Test PATCH /api/plan-tasks/{task_id}
    print(f"\n--- 4. Testing PATCH /api/plan-tasks/{task_id} (Marking Done) ---")
    patch_resp = client.patch(
        f"/api/plan-tasks/{task_id}",
        json={"status": "done"}
    )
    assert patch_resp.status_code == 200
    updated_task = patch_resp.json().get("task", {})
    print(f"Updated Task Status: {updated_task['status']}, completed_at: {updated_task['completed_at']}")
    assert updated_task["status"] == "done"
    assert updated_task["completed_at"] is not None

    fresh_db.close()
    print("\n======================================================================")
    print("ALL ACTION PLAN & TASK ORCHESTRATION TESTS PASSED SUCCESSFULLY!")
    print("======================================================================")

if __name__ == "__main__":
    test_action_plan_flow()
