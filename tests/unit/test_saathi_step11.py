"""
AgriBridge Saathi Voice Assistant Step 11 Layer 2: Guidance Context Foundation Test Suite
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Validates:
1. Layer Classification:
   - 'Mandi Bhav button kahan hai?' -> Layer 1 (PLATFORM_HELP)
   - 'Ye recommendation kyu di gayi?' with context -> Layer 2 (GUIDANCE_HELP)
2. Conflict Resolution (Latest Active Decision Priority):
   - Old plan: 420 L irrigation at 6 PM.
   - New plan: Irrigation cancelled because heavy rain probability is 91%.
   - Saathi identifies cancellation as active decision.
3. Reason & Timing Explanation from Trusted Context.
4. Missing Field Detection (Zero Guessing / Hallucinating).
5. Source Engine Tracking.
"""

import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_layer_classification_platform_vs_guidance():
    """Verify Layer 1 (PLATFORM_HELP) vs Layer 2 (GUIDANCE_HELP) routing."""
    # Layer 1
    r1 = client.post("/api/voice/saathi", json={
        "text": "Mandi Bhav wala button kahan hai?"
    })
    assert r1.status_code == 200
    assert r1.json()["layer"] == "PLATFORM_HELP"

    # Layer 2
    guidance = {
        "crop": "Wheat",
        "crop_stage": "Crown Root Initiation (CRI)",
        "recommendation": {
            "action": "Light Irrigation",
            "reason": "Soil moisture is below 35% during critical CRI stage.",
            "quantity": "350 L",
            "timing": "Morning 7 AM"
        }
    }
    r2 = client.post("/api/voice/saathi", json={
        "text": "Ye irrigation kyu recommend ki gayi?",
        "guidance_context": guidance
    })
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["layer"] == "GUIDANCE_HELP"
    assert "CRI" in d2["response_text"] or "moisture" in d2["response_text"] or "35%" in d2["response_text"]


def test_replan_conflict_resolution_active_decision_priority():
    """Verify Saathi identifies the new active cancellation decision over the old plan."""
    guidance = {
        "crop": "Wheat",
        "previous_decision": {
            "action": "Irrigation",
            "quantity": "420 L",
            "timing": "6 PM"
        },
        "current_decision": {
            "action": "Irrigation Cancelled",
            "reason": "Heavy rain probability is 91% in the next 12 hours.",
            "timing": "Hold until weather clears"
        },
        "replan_status": {
            "is_replanned": True,
            "replan_reason": "Severe rainfall forecast"
        },
        "sources": {
            "weather": "Open-Meteo",
            "decision_engine": "AgriBridge Ultra Decision Matrix"
        }
    }
    r = client.post("/api/voice/saathi", json={
        "text": "Pehle 420 L tha, ab plan kyu cancel hua?",
        "guidance_context": guidance
    })
    assert r.status_code == 200
    data = r.json()
    assert data["layer"] == "GUIDANCE_HELP"
    res = data["response_text"]
    assert "Irrigation Cancelled" in res or "cancel" in res.lower()
    assert "91%" in res or "rain" in res.lower() or "barish" in res.lower()


def test_missing_attribute_handling_no_guessing():
    """Verify Saathi explicitly reports when quantity or timing is missing in trusted context."""
    guidance = {
        "crop": "Rice",
        "recommendation": {
            "action": "Weeding and Drainage",
            "reason": "Excess water logging in active tillering stage."
        }
    }
    r = client.post("/api/voice/saathi", json={
        "text": "Is recommendation mein kitna quantity daalna hai?",
        "guidance_context": guidance
    })
    assert r.status_code == 200
    data = r.json()
    res = data["response_text"].lower()
    assert "uplabdh nahi" in res or "not specified" in res or "action plan" in res


def test_source_engine_tracking():
    """Verify Saathi returns source tracking metadata in the guidance response."""
    guidance = {
        "crop": "Mustard",
        "recommendation": {
            "action": "Monitor Aphid Infestation",
            "reason": "High humidity and moderate temperature favorable for aphids."
        },
        "sources": {
            "weather": "Open-Meteo Realtime",
            "pest_model": "AgriBridge Multi-Signal Pest Pipeline"
        }
    }
    r = client.post("/api/voice/saathi", json={
        "text": "Aphid alert kyu aaya?",
        "guidance_context": guidance
    })
    assert r.status_code == 200
    data = r.json()
    assert data["layer"] == "GUIDANCE_HELP"
    assert "guidance_context" in data
    assert data["guidance_context"]["sources"]["weather"] == "Open-Meteo Realtime"


if __name__ == "__main__":
    print("Running Saathi Step 11 Layer 2: Guidance Context Foundation Unit Test Suite...")
    test_layer_classification_platform_vs_guidance()
    print("  [PASSED] Layer Classification (PLATFORM_HELP vs GUIDANCE_HELP)")
    test_replan_conflict_resolution_active_decision_priority()
    print("  [PASSED] Conflict Resolution (New Cancellation Priority over Old 420 L Plan)")
    test_missing_attribute_handling_no_guessing()
    print("  [PASSED] Missing Attribute Detection (Zero Guessing / Hallucinating)")
    test_source_engine_tracking()
    print("  [PASSED] Trusted Source Engine Tracking")
    print("\nALL SAATHI STEP 11 TESTS PASSED SUCCESSFULLY (100% SUCCESS)!")

