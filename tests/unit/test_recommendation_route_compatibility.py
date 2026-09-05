"""
Crop Recommendation Route Compatibility Master Test
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Proves that:
1. Both /recommend-crop and /api/recommend-crop are fully accessible.
2. Both endpoints return equivalent crop recommendations for identical valid inputs.
3. Both endpoints share identical validation behavior and HTTP 400 error codes.
4. Dropdown routes (/recommend-crop/states vs /api/recommend-crop/states) return identical data.
"""

import sys
from pathlib import Path

# Ensure UTF-8 stdout
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

WORKSPACE_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = WORKSPACE_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_recommendation_dual_route_compatibility():
    print("\n" + "=" * 80)
    print("RUNNING CROP RECOMMENDATION DUAL-ROUTE COMPATIBILITY TEST")
    print("=" * 80)

    # 1. Test Dropdown routes compatibility
    print("\n--- TEST 1: Dropdown States Route Equivalence ---")
    resp_legacy_states = client.get("/recommend-crop/states")
    resp_canon_states = client.get("/api/recommend-crop/states")

    assert resp_legacy_states.status_code == 200, f"Legacy failed: {resp_legacy_states.status_code}"
    assert resp_canon_states.status_code == 200, f"Canonical failed: {resp_canon_states.status_code}"
    assert resp_legacy_states.json() == resp_canon_states.json(), "States list differs between routes"
    print(f"  ✓ States match across both routes: {resp_canon_states.json()['states']}")

    # 2. Test Recommendation POST equivalence with valid payload
    print("\n--- TEST 2: Valid Recommendation Payload Equivalence ---")
    valid_payload = {
        "state": "Punjab",
        "district": "Ludhiana",
        "season": "Kharif",
        "soil_type": "Central Alluvial Loam Soil",
        "ph": 6.8
    }

    resp_legacy = client.post("/recommend-crop", json=valid_payload)
    resp_canonical = client.post("/api/recommend-crop", json=valid_payload)

    assert resp_legacy.status_code == 200, f"Legacy route failed: {resp_legacy.status_code} - {resp_legacy.text}"
    assert resp_canonical.status_code == 200, f"Canonical route failed: {resp_canonical.status_code} - {resp_canonical.text}"

    data_legacy = resp_legacy.json()
    data_canon = resp_canonical.json()

    print(f"  Legacy Route Result    (/recommend-crop)     : {data_legacy}")
    print(f"  Canonical Route Result (/api/recommend-crop) : {data_canon}")

    assert data_legacy == data_canon, (
        f"Mismatch between /recommend-crop and /api/recommend-crop!\nLegacy: {data_legacy}\nCanon: {data_canon}"
    )
    assert data_canon.get("status") == "success"
    assert "recommended_crops" in data_canon
    print(f"  ✓ Equivalence verified! Recommended crops: {data_canon['recommended_crops']}")

    # 3. Test Invalid Input Behavior Equivalence
    print("\n--- TEST 3: Validation Error Equivalence (Missing State) ---")
    invalid_payload = {
        "state": "",
        "district": "Ludhiana",
        "season": "Kharif",
        "soil_type": "Alluvial"
    }

    err_legacy = client.post("/recommend-crop", json=invalid_payload)
    err_canon = client.post("/api/recommend-crop", json=invalid_payload)

    assert err_legacy.status_code in [400, 422]
    assert err_canon.status_code == err_legacy.status_code
    assert err_legacy.json() == err_canon.json()
    print(f"  ✓ Both routes return HTTP {err_canon.status_code} with identical error detail: {err_canon.json()}")

    print("\n" + "=" * 80)
    print("ALL DUAL-ROUTE RECOMMENDATION COMPATIBILITY ASSERTIONS PASSED!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    test_recommendation_dual_route_compatibility()
