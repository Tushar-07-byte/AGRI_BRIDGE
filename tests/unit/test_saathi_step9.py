"""
AgriBridge Saathi Voice Assistant Step 9 Proactive UI Guidance & User Assistance Test Suite
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Validates:
1. Proactive Step Prompting (File uploaded on Disease Detection):
   - ui_context={'file_uploaded': True} -> 'Ji, ab aap Analyze button par click kar sakte hain.'
2. Proactive Inactivity Assistance:
   - ui_context={'proactive_help': True} -> 'Ji, agar aapko aage badhne mein dikkat ho rahi hai...'
3. Error Explanation & Actionable Guidance:
   - 'Photo upload nahi ho rahi.' -> 'Photo upload nahi hui. Ek baar dobara photo select karke try karein.'
   - 'Page atak gaya hai.' -> 'Koi baat nahi ji, ek baar page ko refresh karke dobara button dabayein...'
4. Multilingual Proactive Assistance (Punjabi & Hindi).
5. Strict Scope Guard (Pure Platform Help Guide).
"""

import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_proactive_guidance_file_uploaded():
    """Verify Saathi proactively prompts the farmer to click Analyze when an image is uploaded."""
    r = client.post("/api/voice/saathi", json={
        "text": "Ab kya karna hai?",
        "current_page": "upload-crop",
        "ui_context": {"file_uploaded": True}
    })
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    res = data["response_text"].lower()
    assert "analyze" in res or "click" in res


def test_proactive_assistance_stuck_state():
    """Verify Saathi offers gentle proactive assistance when the farmer is stuck or idle."""
    r = client.post("/api/voice/saathi", json={
        "ui_context": {"proactive_help": True},
        "current_page": "farmer-dashboard"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    res = data["response_text"].lower()
    assert "dikkat" in res or "pooch" in res or "trouble" in res or "forward" in res


def test_error_guidance_photo_upload_failure():
    """Verify Saathi gives actionable advice when the farmer faces a photo upload failure."""
    r = client.post("/api/voice/saathi", json={
        "text": "Photo upload nahi ho rahi.",
        "current_page": "upload-crop"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    res = data["response_text"].lower()
    assert "photo" in res or "dobara" in res or "select" in res or "try" in res


def test_trouble_guidance_page_stuck():
    """Verify Saathi gives calming advice when the screen is frozen or stuck."""
    r = client.post("/api/voice/saathi", json={
        "text": "Page atak gaya hai.",
        "current_page": "crop-monitoring"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    res = data["response_text"].lower()
    assert "refresh" in res or "dobara" in res or "button" in res


def test_multilingual_proactive_assistance_punjabi():
    """Verify proactive advice in Punjabi."""
    r = client.post("/api/voice/saathi", json={
        "language": "pa",
        "ui_context": {"proactive_help": True}
    })
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["language"] == "pa"
    assert "ਦਿੱਕਤ" in data["response_text"] or "ਪੁੱਛ" in data["response_text"]


def test_strict_scope_boundaries_step9():
    """Verify Saathi never gives raw pesticide recipes during error handling."""
    r = client.post("/api/voice/saathi", json={
        "text": "Page atak gaya hai, davai ka naam bata do."
    })
    assert r.status_code == 200
    res = r.json()["response_text"]
    assert "carbendazim" not in res.lower()
    assert "hexaconazole" not in res.lower()
    assert "₹" not in res


if __name__ == "__main__":
    print("Running Saathi Step 9 Proactive UI Guidance & User Assistance Unit Test Suite...")
    test_proactive_guidance_file_uploaded()
    print("  [PASSED] Proactive Guidance: File Uploaded -> Prompt Analyze")
    test_proactive_assistance_stuck_state()
    print("  [PASSED] Proactive Assistance: Inactivity / Stuck State")
    test_error_guidance_photo_upload_failure()
    print("  [PASSED] Error Guidance: 'Photo upload nahi ho rahi.'")
    test_trouble_guidance_page_stuck()
    print("  [PASSED] Trouble Guidance: 'Page atak gaya hai.'")
    test_multilingual_proactive_assistance_punjabi()
    print("  [PASSED] Multilingual Proactive Assistance (Punjabi)")
    test_strict_scope_boundaries_step9()
    print("  [PASSED] Strict Step 9 Scope Boundaries (Platform Guidance Only)")
    print("\nALL SAATHI STEP 9 TESTS PASSED SUCCESSFULLY (100% SUCCESS)!")

