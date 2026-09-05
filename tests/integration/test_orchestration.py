import json
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

@pytest.fixture(scope="function")
def db_session():
    # Obtain a DB session from the app's dependency
    from backend.app.database.connection import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_orchestration_with_demo_overrides(db_session):
    import uuid
    from backend.app.models.farmer import Farmer
    farmer = Farmer(name=f"Demo Test Farmer {uuid.uuid4().hex[:6]}")
    db_session.add(farmer)
    db_session.commit()
    db_session.refresh(farmer)

    payload = {
        "state": "Punjab",
        "district": "Ludhiana",
        "village": "Samrala",
        "crop_id": "wheat",
        "planting_date": "2023-11-01",
        "current_stage": "Tillering",
        "latitude": 30.9,
        "longitude": 75.9,
        "farmer_id": farmer.id,
        "soil_moisture_vwc": 20.0,
        "rain_probability": 40,
    }
    response = client.post("/api/orchestration/plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    # Verify response contains expected sections
    assert data.get("action_plan") is not None
    assert data.get("tasks") is not None
    # Verify demo overrides are reflected in the decision context
    telemetry = data.get("decision_context", {}).get("telemetry", {})
    assert telemetry.get("soil_moisture_vwc", {}).get("value") == 20.0
    weather = data.get("decision_context", {}).get("weather", {})
    assert weather.get("rain_probability_percent", {}).get("value") == 40
    # Ensure escalation flag aligns with policy (should be False for this demo scenario)
    assert data.get("escalation_required") is False
    # Verify persistence in the test DB
    db_session.commit()
    from backend.app.models.action_plan import ActionPlan, PlanTask
    plan = db_session.query(ActionPlan).filter(ActionPlan.id == data["action_plan"]["id"]).first()
    assert plan is not None
    task = db_session.query(PlanTask).filter(PlanTask.action_plan_id == plan.id).first()
    assert task is not None

