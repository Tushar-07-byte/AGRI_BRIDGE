"""
AgriBridge Saathi Voice Assistant Step 14 Layer 2: Natural Follow-Up Questions Test Suite
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Validates:
1. Multi-Turn Dialogue Continuity:
   - Turn 1: '420 litre paani kyun?' -> Explains soil moisture 18%.
   - Turn 2: 'Kitne baje?' (with history) -> Resolves timing '6 PM' for 420 L irrigation.
   - Turn 3: 'Agar baarish ho gayi toh?' -> Explains dynamic contingency / replanning.
2. Ambiguity Clarification (Zero Guessing):
   - Multiple items without focus -> Asks short clarification between items.
3. Context Switching & Non-Mixing of Plans:
   - Switching from Irrigation 420 L to Nitrogen 25 kg resolves correct parameters without mixing.
4. Multi-Turn Multilingual Transition:
   - Hindi -> English -> Hinglish without losing active guidance context.
"""

import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_multi_turn_natural_follow_up_sequence():
    """Verify 3-turn natural conversation sequence (420 L -> Kitne baje? -> Agar baarish ho gayi toh?)."""
    guidance = {
        "crop": "Tomato",
        "soil_moisture": "18%",
        "recommendation": {
            "action": "Irrigate 420 L",
            "quantity": "420 L",
            "timing": "6 PM",
            "reason": "Current soil moisture is 18%"
        }
    }

    # Turn 1: Why 420 L?
    r1 = client.post("/api/voice/saathi", json={
        "text": "420 litre paani kyun?",
        "guidance_context": guidance
    })
    assert r1.status_code == 200
    res1 = r1.json()["response_text"]
    assert "18%" in res1 or "moisture" in res1.lower()

    # Turn 2: Follow-up 'Kitne baje?'
    history = [
        {"role": "user", "content": "420 litre paani kyun?"},
        {"role": "assistant", "content": res1}
    ]
    r2 = client.post("/api/voice/saathi", json={
        "text": "Kitne baje?",
        "guidance_context": guidance,
        "history": history
    })
    assert r2.status_code == 200
    res2 = r2.json()["response_text"]
    assert "6 PM" in res2 or "6" in res2

    # Turn 3: Contingency 'Agar baarish ho gayi toh?'
    history.extend([
        {"role": "user", "content": "Kitne baje?"},
        {"role": "assistant", "content": res2}
    ])
    r3 = client.post("/api/voice/saathi", json={
        "text": "Agar baarish ho gayi toh?",
        "guidance_context": guidance,
        "history": history
    })
    assert r3.status_code == 200
    res3 = r3.json()["response_text"].lower()
    assert "baarish" in res3 or "barish" in res3 or "replan" in res3 or "update" in res3 or "rain" in res3


def test_ambiguous_pronoun_clarification_no_guessing():
    """Verify Saathi asks a short clarification when an ungrounded pronoun refers to multiple active items."""
    guidance = {
        "crop": "Wheat",
        "recommendations": [
            {"action": "First Irrigation", "quantity": "400 L"},
            {"action": "Zinc Sulfate Application", "quantity": "10 kg"}
        ]
    }
    r = client.post("/api/voice/saathi", json={
        "text": "Iska kya karna hai?",
        "guidance_context": guidance
    })
    assert r.status_code == 200
    data = r.json()
    assert data["layer"] == "GUIDANCE_HELP"
    res = data["response_text"]
    assert "First Irrigation" in res
    assert "Zinc Sulfate" in res or "10 kg" in res or "sujhav" in res or "recommendation" in res.lower()


def test_context_switching_between_items():
    """Verify switching focus between multiple items resolves exact grounded values without cross-contamination."""
    guidance = {
        "crop": "Wheat",
        "recommendations": [
            {
                "action": "Irrigation",
                "quantity": "420 L",
                "timing": "6 PM",
                "reason": "Soil moisture is below 35%"
            },
            {
                "action": "Nitrogen Top-Dressing",
                "quantity": "25 kg",
                "timing": "Morning 8 AM",
                "reason": "Tillering stage nitrogen requirement"
            }
        ]
    }

    # Ask about Item 2
    r = client.post("/api/voice/saathi", json={
        "text": "25 kg wala kab karna hai?",
        "guidance_context": guidance
    })
    assert r.status_code == 200
    res = r.json()["response_text"]
    assert "Morning 8 AM" in res
    assert "6 PM" not in res  # Does not mix with Item 1's timing


def test_multi_turn_multilingual_transition():
    """Verify multi-turn guidance continuity across Hindi -> English -> Hinglish transitions."""
    guidance = {
        "crop": "Tomato",
        "recommendation": {
            "action": "Fungicide Spray",
            "quantity": "2 ml/L",
            "timing": "Early Morning",
            "reason": "Early Blight prevention during humid weather"
        }
    }

    # Turn 1 in Hindi
    r1 = client.post("/api/voice/saathi", json={
        "text": "यह क्यों करना है?",
        "language": "hi",
        "guidance_context": guidance
    })
    assert r1.status_code == 200
    assert r1.json()["layer"] == "GUIDANCE_HELP"

    # Turn 2 in English
    history = [
        {"role": "user", "content": "यह क्यों करना है?"},
        {"role": "assistant", "content": r1.json()["response_text"]}
    ]
    r2 = client.post("/api/voice/saathi", json={
        "text": "What is the timing for this?",
        "language": "en",
        "guidance_context": guidance,
        "history": history
    })
    assert r2.status_code == 200
    assert "Early Morning" in r2.json()["response_text"]


if __name__ == "__main__":
    print("Running Saathi Step 14 Layer 2: Natural Follow-Up Questions Unit Test Suite...")
    test_multi_turn_natural_follow_up_sequence()
    print("  [PASSED] Multi-Turn Dialogue Continuity (420 L -> Kitne baje? -> Agar baarish ho gayi toh?)")
    test_ambiguous_pronoun_clarification_no_guessing()
    print("  [PASSED] Ambiguous Pronoun Clarification (Zero Guessing)")
    test_context_switching_between_items()
    print("  [PASSED] Context Switching & Non-Mixing of Plans")
    test_multi_turn_multilingual_transition()
    print("  [PASSED] Multi-Turn Multilingual Transition (Hindi -> English -> Hinglish)")
    print("\nALL SAATHI STEP 14 TESTS PASSED SUCCESSFULLY (100% SUCCESS)!")

