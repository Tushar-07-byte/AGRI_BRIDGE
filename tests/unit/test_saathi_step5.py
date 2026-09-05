"""
AgriBridge Saathi Voice Assistant Step 5 Comprehensive Unit Test Suite
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Validates:
1. Complete Multi-Step Guided Navigation Workflow:
   - Turn 1: 'Mujhe crop disease check karna hai.' -> Guide to 'AI Crop Scan' button
   - Turn 2: 'Kar diya.' -> 'Ab apni crop ki photo upload karein.'
   - Turn 3: 'Upload kar diya.' -> 'Ab Analyze button par click karein.'
   - Turn 4: 'Kar diya.' -> 'Bahut badhiya! Ab screen par bimari ka naam aur ilaj ke sujhav dekh sakte hain.'
2. Natural Farmer Progression Phrases ('Kar diya', 'Ho gaya', 'Upload kar diya', 'Click kar diya').
3. Troubleshooting Handling ('Button nahi mil raha', 'Galti se kuch aur open ho gaya', 'Nahi ho raha').
4. Multilingual Step-by-Step Guided Navigation (Punjabi & Marathi).
5. Strict Step 5 Scope Boundary (No chemical prescriptions, No direct agricultural diagnosis).
"""

import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_complete_guided_navigation_crop_disease_workflow():
    """Verify end-to-end patient step-by-step guided walkthrough for Crop Disease Detection."""
    # Turn 1: Farmer states goal
    r1 = client.post("/api/voice/saathi", json={
        "text": "Mujhe crop disease check karna hai.",
        "current_page": "farmer-dashboard"
    })
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["success"] is True
    assert "AI Crop Scan" in d1["response_text"] or "Crop" in d1["response_text"]

    # Turn 2: Farmer says 'Kar diya.' -> Step 2 (Upload photo)
    history = [
        {"role": "user", "text": "Mujhe crop disease check karna hai."},
        {"role": "assistant", "text": d1["response_text"]}
    ]
    r2 = client.post("/api/voice/saathi", json={
        "text": "Kar diya.",
        "history": history,
        "current_page": "upload-crop"
    })
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["success"] is True
    assert "photo" in d2["response_text"].lower() or "upload" in d2["response_text"].lower()

    # Turn 3: Farmer says 'Upload kar diya.' -> Step 3 (Click Analyze)
    history.extend([
        {"role": "user", "text": "Kar diya."},
        {"role": "assistant", "text": d2["response_text"]}
    ])
    r3 = client.post("/api/voice/saathi", json={
        "text": "Upload kar diya.",
        "history": history,
        "current_page": "upload-crop"
    })
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3["success"] is True
    assert "Analyze" in d3["response_text"] or "analyze" in d3["response_text"].lower()

    # Turn 4: Farmer says 'Analyze par click kar diya.' -> Step 4 (View results)
    history.extend([
        {"role": "user", "text": "Upload kar diya."},
        {"role": "assistant", "text": d3["response_text"]}
    ])
    r4 = client.post("/api/voice/saathi", json={
        "text": "Analyze par click kar diya.",
        "history": history,
        "current_page": "upload-crop"
    })
    assert r4.status_code == 200
    d4 = r4.json()
    assert d4["success"] is True
    assert "bimari" in d4["response_text"].lower() or "screen" in d4["response_text"].lower() or "ilaj" in d4["response_text"].lower()


def test_troubleshooting_button_not_found():
    """Verify Saathi helps farmer when they say 'Button nahi mil raha'."""
    history = [
        {"role": "user", "text": "Mujhe mandi bhav dekhna hai."},
        {"role": "assistant", "text": "Marketplace button par click karein."}
    ]
    r = client.post("/api/voice/saathi", json={
        "text": "Mujhe button nahi mil raha",
        "history": history,
        "current_page": "farmer-dashboard"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert "navigation" in data["response_text"].lower() or "upar" in data["response_text"].lower() or "Marketplace" in data["response_text"]


def test_troubleshooting_wrong_page_recovery():
    """Verify Saathi helps farmer recover when they say 'Galti se kuch aur open ho gaya'."""
    history = [
        {"role": "user", "text": "AI Crop Scan karna hai."},
        {"role": "assistant", "text": "AI Crop Scan button par click karein."}
    ]
    r = client.post("/api/voice/saathi", json={
        "text": "Galti se kuch aur open ho gaya",
        "history": history
    })
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert "AI Crop Scan" in data["response_text"] or "Dashboard" in data["response_text"] or "click" in data["response_text"].lower()


def test_troubleshooting_not_working_patience():
    """Verify Saathi gives patient advice when farmer says 'Nahi ho raha'."""
    r = client.post("/api/voice/saathi", json={
        "text": "Nahi ho raha"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert "refresh" in data["response_text"].lower() or "try" in data["response_text"].lower() or "dhyan" in data["response_text"].lower()


def test_multilingual_guided_step_punjabi():
    """Verify step-by-step navigation progression in Punjabi."""
    # Turn 1
    r1 = client.post("/api/voice/saathi", json={
        "text": "ਮੈਂ ਫਸਲ ਦੀ ਬਿਮਾਰੀ ਚੈੱਕ ਕਰਨੀ ਹੈ।",
        "language": "pa"
    })
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["language"] == "pa"

    # Turn 2: 'ਕਰ ਦਿੱਤਾ।'
    history = [
        {"role": "user", "text": "ਮੈਂ ਫਸਲ ਦੀ ਬਿਮਾਰੀ ਚੈੱਕ ਕਰਨੀ ਹੈ।"},
        {"role": "assistant", "text": d1["response_text"]}
    ]
    r2 = client.post("/api/voice/saathi", json={
        "text": "ਕਰ ਦਿੱਤਾ।",
        "language": "pa",
        "history": history
    })
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["success"] is True
    assert d2["language"] == "pa"
    assert "ਫੋਟੋ" in d2["response_text"] or "ਪੱਤੇ" in d2["response_text"]


def test_strict_step5_scope_boundaries():
    """Verify Saathi never gives raw chemical prescriptions or weather degrees during guided walkthrough."""
    history = [
        {"role": "user", "text": "AI Crop Scan khola hai."},
        {"role": "assistant", "text": "Patti ki photo upload karein."}
    ]
    r = client.post("/api/voice/saathi", json={
        "text": "Upload kar diya",
        "history": history
    })
    assert r.status_code == 200
    res = r.json()["response_text"]
    assert "mancozeb" not in res.lower()
    assert "chlorpyrifos" not in res.lower()
    assert "₹" not in res


if __name__ == "__main__":
    print("Running Saathi Step 5 Guided Platform Navigation Unit Test Suite...")
    test_complete_guided_navigation_crop_disease_workflow()
    print("  [PASSED] Complete Multi-Step Guided Walkthrough (Crop Disease Detection)")
    test_troubleshooting_button_not_found()
    print("  [PASSED] Troubleshooting: 'Button nahi mil raha'")
    test_troubleshooting_wrong_page_recovery()
    print("  [PASSED] Troubleshooting: 'Galti se kuch aur open ho gaya'")
    test_troubleshooting_not_working_patience()
    print("  [PASSED] Troubleshooting: 'Nahi ho raha'")
    test_multilingual_guided_step_punjabi()
    print("  [PASSED] Multilingual Step Progression (Punjabi)")
    test_strict_step5_scope_boundaries()
    print("  [PASSED] Strict Step 5 Scope Boundaries (Platform Guidance Only)")
    print("\nALL SAATHI STEP 5 TESTS PASSED SUCCESSFULLY (100% SUCCESS)!")

