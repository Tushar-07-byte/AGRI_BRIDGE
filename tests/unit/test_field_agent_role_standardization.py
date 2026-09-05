"""
Test Suite: Field Agent Role Standardization & Authentication Flow
"""

import sys
import uuid
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.models.user import User

client = TestClient(app)

def run_field_agent_tests():
    print("\n======================================================================")
    print("TEST: FIELD AGENT ROLE STANDARDIZATION & AUTHENTICATION END-TO-END")
    print("======================================================================")

    db = SessionLocal()

    # Test 1: Register Field Agent with canonical 'field-agent'
    rand_phone1 = f"98765{str(uuid.uuid4().int)[:5]}"
    print(f"\n--- Test 1: Registration with canonical role='field-agent' (Mobile: {rand_phone1}) ---")
    reg_resp = client.post(
        "/api/auth/register",
        json={
            "name": "Priya Sharma (Field Agent)",
            "mobile": rand_phone1,
            "password": "Password@123",
            "confirm_password": "Password@123",
            "role": "field-agent"
        }
    )
    print(f"Status: {reg_resp.status_code}, Body: {reg_resp.json()}")
    assert reg_resp.status_code == 200
    assert reg_resp.json()["success"] is True

    # Login and verify role and routing
    login_resp = client.post(
        "/api/auth/login",
        json={
            "mobile": rand_phone1,
            "password": "Password@123"
        }
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    print(f"Login Response: User Role = '{login_data['user']['role']}', Redirect = '{login_data['redirect']}'")
    assert login_data["user"]["role"] == "field-agent"
    assert login_data["redirect"] == "/frontend/pages/field-agent-dashboard.html"

    # Test 2: Verify /api/auth/me returns canonical 'field-agent'
    me_resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {login_data['token']}"}
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    print(f"/api/auth/me Response: User Role = '{me_data['user']['role']}'")
    assert me_data["user"]["role"] == "field-agent"

    # Test 3: Register Field Agent with legacy alias 'professional' -> Auto-normalized to 'field-agent'
    rand_phone2 = f"98764{str(uuid.uuid4().int)[:5]}"
    print(f"\n--- Test 3: Registration with legacy alias role='professional' (Mobile: {rand_phone2}) ---")
    reg_pro = client.post(
        "/api/auth/register",
        json={
            "name": "Anil Verma (Professional)",
            "mobile": rand_phone2,
            "password": "Password@123",
            "confirm_password": "Password@123",
            "role": "professional"
        }
    )
    assert reg_pro.status_code == 200
    assert reg_pro.json()["success"] is True

    db.close()
    fresh_db = SessionLocal()
    pro_user = fresh_db.query(User).filter(User.mobile.like(f"%{rand_phone2}")).first()
    print(f"MySQL User Stored Role: '{pro_user.role}' (Normalized from 'professional')")
    assert pro_user.role == "field-agent"

    # Test 4: Register Field Agent with underscore alias 'field_agent' -> Auto-normalized to 'field-agent'
    rand_phone3 = f"98763{str(uuid.uuid4().int)[:5]}"
    print(f"\n--- Test 4: Registration with underscore alias role='field_agent' (Mobile: {rand_phone3}) ---")
    reg_under = client.post(
        "/api/auth/register",
        json={
            "name": "Sunita Patil (Field Agent)",
            "mobile": rand_phone3,
            "password": "Password@123",
            "confirm_password": "Password@123",
            "role": "field_agent"
        }
    )
    assert reg_under.status_code == 200
    assert reg_under.json()["success"] is True

    fresh_db.close()
    db4 = SessionLocal()
    under_user = db4.query(User).filter(User.mobile.like(f"%{rand_phone3}")).first()
    print(f"MySQL User Stored Role: '{under_user.role}' (Normalized from 'field_agent')")
    assert under_user.role == "field-agent"
    db4.close()

    # Test 5: Reject genuinely invalid role 'astronaut'
    print("\n--- Test 5: Rejection of Invalid Role 'astronaut' ---")
    reg_bad = client.post(
        "/api/auth/register",
        json={
            "name": "Test Alien",
            "mobile": "9876200001",
            "password": "Password@123",
            "confirm_password": "Password@123",
            "role": "astronaut"
        }
    )
    assert reg_bad.status_code == 200
    assert reg_bad.json()["success"] is False
    assert reg_bad.json()["code"] == "INVALID_ROLE"
    print(f"Correctly Rejected with: {reg_bad.json()['message']}")

    fresh_db.close()
    print("\n======================================================================")
    print("ALL FIELD AGENT ROLE STANDARDIZATION & AUTH TESTS PASSED!")
    print("======================================================================")

if __name__ == "__main__":
    run_field_agent_tests()
