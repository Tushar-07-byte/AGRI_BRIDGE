"""
AgriBridge Saathi Voice Assistant Step 16 Layer 2: Action Plan & Execution Guidance Test Suite
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Validates:
1. Start Action Plan Guidance:
   - 'Ab mujhe kya karna hai?' -> Explains Step 1 ('Irrigate 420 L').
2. One-Step-At-A-Time Step Progression:
   - 'Kar diya.' -> Advances to Step 2 ('Check soil moisture afterward').
   - 'Ho gaya.' -> Advances to Step 3 ('Record completion').
   - 'Kar liya.' (final step) -> Completes action plan with congratulations.
3. Troubleshooting & Failure Handling:
   - 'Nahi hua.' -> Offers troubleshooting assistance for active step.
4. Step-Specific Inquiries:
   - 'Kaise karu?' -> Method for active step.
   - 'Kyun?' -> Reason for active step.
5. Multilingual Action Plan Progression (pa, hi, hinglish).
"""

import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_action_plan_step_by_step_progression_sequence():
    """Verify complete one-step-at-a-time guided execution sequence through a multi-step action plan."""
    guidance = {
        "crop": "Tomato",
        "action_plan": {
            "steps": [
                {
                    "step_number": 1,
                    "action": "Irrigate 420 L",
                    "quantity": "420 L",
                    "timing": "6 PM",
                    "status": "pending"
                },
                {
                    "step_number": 2,
                    "action": "Check soil moisture afterward",
                    "status": "pending"
                },
                {
                    "step_number": 3,
                    "action": "Record completion in AgriBridge",
                    "status": "pending"
                }
            ]
        }
    }

    # Step 1: Initial Prompt
    r1 = client.post("/api/voice/saathi", json={
        "text": "Ab mujhe kya karna hai?",
        "guidance_context": guidance
    })
    assert r1.status_code == 200
    res1 = r1.json()["response_text"]
    assert "Step 1" in res1
    assert "Irrigate 420 L" in res1

    # Step 2: Farmer completed step 1 -> 'Kar diya.'
    history = [
        {"role": "user", "content": "Ab mujhe kya karna hai?"},
        {"role": "assistant", "content": res1}
    ]
    r2 = client.post("/api/voice/saathi", json={
        "text": "Kar diya.",
        "guidance_context": guidance,
        "history": history
    })
    assert r2.status_code == 200
    res2 = r2.json()["response_text"]
    assert "Step 2" in res2
    assert "Check soil moisture" in res2

    # Step 3: Farmer completed step 2 -> 'Ho gaya.'
    history.extend([
        {"role": "user", "content": "Kar diya."},
        {"role": "assistant", "content": res2}
    ])
    # Now simulate context where step 1 was marked complete
    guidance_step2 = dict(guidance)
    guidance_step2["action_plan"]["steps"][0]["status"] = "completed"
    guidance_step2["action_plan"]["steps"][1]["status"] = "pending"

    r3 = client.post("/api/voice/saathi", json={
        "text": "Ho gaya.",
        "guidance_context": guidance_step2,
        "history": history
    })
    assert r3.status_code == 200
    res3 = r3.json()["response_text"]
    assert "Step 3" in res3
    assert "Record completion" in res3

    # Step 4: Final Step completed -> 'Kar liya.'
    history.extend([
        {"role": "user", "content": "Ho gaya."},
        {"role": "assistant", "content": res3}
    ])
    guidance_final = dict(guidance)
    for s in guidance_final["action_plan"]["steps"]:
        s["status"] = "completed"

    r4 = client.post("/api/voice/saathi", json={
        "text": "Kar liya.",
        "guidance_context": guidance_final,
        "history": history
    })
    assert r4.status_code == 200
    res4 = r4.json()["response_text"]
    assert "Badhaai" in res4 or "complete" in res4.lower() or "सफलतापूर्वक" in res4


def test_troubleshooting_failed_step():
    """Verify 'Nahi hua.' offers helpful troubleshooting without hallucinating or breaking safety."""
    guidance = {
        "crop": "Wheat",
        "action_plan": {
            "steps": [
                {
                    "step_number": 1,
                    "action": "Calibrate Spray Nozzle",
                    "status": "in_progress"
                }
            ]
        }
    }
    r = client.post("/api/voice/saathi", json={
        "text": "Nahi hua.",
        "guidance_context": guidance
    })
    assert r.status_code == 200
    data = r.json()
    assert data["layer"] == "GUIDANCE_HELP"
    res = data["response_text"].lower()
    assert "dikkat" in res or "pareshani" in res or "madad" in res or "no worries" in res


def test_step_specific_how_and_why_inquiries():
    """Verify 'Kaise karu?' and 'Kyun?' explain method and reason for active step."""
    guidance = {
        "crop": "Cotton",
        "action_plan": {
            "steps": [
                {
                    "step_number": 1,
                    "action": "Set Pheromone Traps",
                    "method": "Hang at canopy height facing windward direction",
                    "reason": "Monitors pink bollworm moth population",
                    "status": "pending"
                }
            ]
        }
    }

    # How
    r_how = client.post("/api/voice/saathi", json={
        "text": "Kaise karna hai?",
        "guidance_context": guidance
    })
    assert r_how.status_code == 200
    res_how = r_how.json()["response_text"]
    assert "canopy height" in res_how or "Hang" in res_how

    # Why
    r_why = client.post("/api/voice/saathi", json={
        "text": "Kyun karna hai?",
        "guidance_context": guidance
    })
    assert r_why.status_code == 200
    res_why = r_why.json()["response_text"]
    assert "bollworm" in res_why.lower()


def test_multilingual_action_plan_progression_punjabi():
    """Verify action plan guidance in Punjabi."""
    guidance = {
        "crop": "Wheat",
        "action_plan": {
            "steps": [
                {
                    "step_number": 1,
                    "action": "ਪਹਿਲੀ ਸਿੰਚਾਈ (First Irrigation)",
                    "timing": "6 PM",
                    "status": "pending"
                },
                {
                    "step_number": 2,
                    "action": "ਨਮੀ ਚੈੱਕ ਕਰੋ (Check Moisture)",
                    "status": "pending"
                }
            ]
        }
    }
    r = client.post("/api/voice/saathi", json={
        "text": "ਕਰ ਦਿੱਤਾ (Kar ditta)",
        "language": "pa",
        "guidance_context": guidance
    })
    assert r.status_code == 200
    data = r.json()
    assert data["layer"] == "GUIDANCE_HELP"
    assert data["language"] == "pa"


if __name__ == "__main__":
    print("Running Saathi Step 16 Layer 2: Action Plan & Execution Guidance Unit Test Suite...")
    test_action_plan_step_by_step_progression_sequence()
    print("  [PASSED] One-Step-At-A-Time Step Progression Sequence (Step 1 -> 2 -> 3 -> Completed)")
    test_troubleshooting_failed_step()
    print("  [PASSED] Troubleshooting Failed Step ('Nahi hua.')")
    test_step_specific_how_and_why_inquiries()
    print("  [PASSED] Step-Specific How & Why Inquiries ('Kaise karu?', 'Kyun?')")
    test_multilingual_action_plan_progression_punjabi()
    print("  [PASSED] Multilingual Action Plan Progression (Punjabi)")
    print("\nALL SAATHI STEP 16 TESTS PASSED SUCCESSFULLY (100% SUCCESS)!")
