"""
Verification of Authentication & Session Management Fixes
"""

import time
import base64
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_auth_me_endpoints():
    print("\n--- 1. Testing /api/auth/me with Valid Token ---")
    login_resp = client.post("/api/auth/login", json={"mobile": "9999990001", "password": "Password@123"})
    assert login_resp.status_code == 200
    token = login_resp.json()["token"]

    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["success"] is True
    print(f"[PASSED] Valid Token User: {me_resp.json()['user']['name']}")

    print("\n--- 2. Testing /api/auth/me with Invalid Token ---")
    bad_resp = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.value"})
    assert bad_resp.status_code == 401
    print(f"[PASSED] Invalid Token correctly returns 401: {bad_resp.json()}")

    print("\n--- 3. Testing /api/auth/me with No Token ---")
    no_resp = client.get("/api/auth/me")
    assert no_resp.status_code == 401
    print(f"[PASSED] Missing Token correctly returns 401: {no_resp.json()}")

    print("\n--- 4. Testing HTML Landing Page Accessibility ---")
    index_resp = client.get("/frontend/pages/index.html")
    assert index_resp.status_code == 200
    assert "Login" in index_resp.text
    assert "Get Started" in index_resp.text
    print("[PASSED] index.html is accessible and contains public auth action links.")

if __name__ == "__main__":
    test_auth_me_endpoints()
    print("\nALL VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
