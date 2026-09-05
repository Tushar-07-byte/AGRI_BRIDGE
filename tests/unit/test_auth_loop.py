import os
import sys

# Set UTF-8 encoding for stdout
sys.stdout.reconfigure(encoding='utf-8')

from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.models.user import User

client = TestClient(app)
db = SessionLocal()

print("=== 1. DEMO LOGINS FOR ALL 3 ROLES ===")
for role in ["farmer", "buyer", "field-agent"]:
    res = client.post("/api/auth/demo-login", json={"role": role})
    assert res.status_code == 200
    data = res.json()
    assert data.get("success") is True
    print(f"Role: {role} -> User: {data['user']['name']}, Redirect: {data['redirect']}")
    
    # Test /api/auth/me
    token = data["token"]
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["user"]["role"] == role
    print(f"  [OK] /api/auth/me verified role: {me_res.json()['user']['role']}")
    
    # Test logout
    logout_res = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_res.status_code == 200
    print("  [OK] /api/auth/logout: 200 OK")

print("\n=== 2. PASSWORD REGISTRATION & LOGIN FOR ALL 3 ROLES ===")
for idx, role in enumerate(["farmer", "buyer", "field-agent"], start=20):
    mobile = f"+9198000000{idx}"
    password = "SecurePassword123!"
    name = f"Test {role.capitalize()} {idx}"
    
    existing = db.query(User).filter(User.mobile == mobile).first()
    if existing:
        db.delete(existing)
        db.commit()
        
    reg_res = client.post("/api/auth/register", json={
        "name": name,
        "mobile": mobile,
        "password": password,
        "confirm_password": password,
        "role": role
    })
    assert reg_res.status_code == 200
    assert reg_res.json().get("success") is True
    print(f"Registered {name} as {role}")
    
    login_res = client.post("/api/auth/login", json={"mobile": mobile, "password": password})
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data.get("success") is True
    assert login_data["user"]["role"] == role
    print(f"  [OK] Logged in {name} -> Redirect: {login_data['redirect']}")

db.close()
print("\n=== ALL AUTHENTICATION LOGIN/LOGOUT LOOPS PASSED 100% ===")
