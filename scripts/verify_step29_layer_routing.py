"""
AgriBridge Saathi Step 29: Complete Layer 1 / Layer 2 Routing Validation Test Suite
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Validates:
1. Layer 1 Platform Navigation Questions -> PLATFORM_HELP
   - "Mandi bhav ka button kahan hai?"
   - "Crop photo kaise upload karu?"
   - "Weather section kahan hai?"
   - "Is page se dashboard kaise jaunga?"
   - "Ye button kya karta hai?"
   - "Mujhe disease section kahan milega?"

2. Layer 2 Agricultural Explanation Questions -> GUIDANCE_HELP
   - "Ye recommendation kyun di?"
   - "420 litre kyun?"
   - "Irrigation kab karna hai?"
   - "Ye disease result ka matlab kya hai?"
   - "Plan change kyun hua?"
   - "Pehle kuch aur bola tha, ab kuch aur kyun?"
   - "Ab mujhe kya karna hai?"

3. Mixed Conversation Workflow:
   - Turn 1: "Saathi, weather kahan hai?" -> Layer 1 (PLATFORM_HELP)
   - Turn 2: "Ab yahan jo weather hai uska matlab kya hai?" -> Layer 2 (GUIDANCE_HELP)
   - Turn 3: "Ab mujhe kya karna hai?" -> Layer 2 (GUIDANCE_HELP)
   - Turn 4: "Dashboard kaise jaunga?" -> Layer 1 (PLATFORM_HELP)

4. Context Preservation & Safety:
   - Context transitions between Layer 1 and Layer 2 smoothly.
   - If Layer 2 guidance is unavailable: says guidance is currently unavailable without hallucinating.
"""

import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def run_step29_tests():
    print("=" * 70)
    print("STEP 29 VERIFICATION: COMPLETE LAYER 1 / LAYER 2 ROUTING VALIDATION")
    print("=" * 70)

    total_tests = 0
    passed_tests = 0

    trusted_guidance = {
        "crop": "Tomato",
        "soil_moisture": "18%",
        "recommendation": {
            "action": "Irrigate 420 L at 6 PM",
            "quantity": "420 L",
            "timing": "6 PM",
            "reason": "low soil moisture"
        },
        "weather": {
            "forecast": "Clear skies, no rain expected for next 48 hours",
            "spray_safe": True
        },
        "disease_result": {
            "disease_name": "Tomato Early Blight",
            "confidence": 0.92,
            "treatment": "Apply Mancozeb 75% WP @ 2g/L"
        },
        "is_replanned": True,
        "previous_decision": {
            "action": "Spray Fungicide",
            "quantity": "250 ml",
            "reason": "Early spot detection"
        },
        "current_decision": {
            "action": "Irrigate 420 L at 6 PM",
            "quantity": "420 L",
            "reason": "low soil moisture"
        },
        "decision_id": "DEC-ROUTING-990",
        "confidence": 0.95
    }

    # -------------------------------------------------------------------------
    # SUITE 1: Layer 1 Test Questions (PLATFORM_HELP)
    # -------------------------------------------------------------------------
    print("\n--- Suite 1: Layer 1 Questions (Expected: PLATFORM_HELP) ---")

    layer1_queries = [
        "Mandi bhav ka button kahan hai?",
        "Crop photo kaise upload karu?",
        "Weather section kahan hai?",
        "Is page se dashboard kaise jaunga?",
        "Ye button kya karta hai?",
        "Mujhe disease section kahan milega?"
    ]

    for q in layer1_queries:
        total_tests += 1
        r = client.post("/api/voice/saathi", json={
            "text": q,
            "current_page": "farmer-dashboard",
            "language": "hinglish"
        })
        assert r.status_code == 200
        d = r.json()
        assert d["layer"] == "PLATFORM_HELP", f"Expected PLATFORM_HELP for '{q}', got {d['layer']}"
        print(f"[PASS] '{q}' -> Layer: {d['layer']} | Response: {d['response_text'][:80]}...")
        passed_tests += 1

    # -------------------------------------------------------------------------
    # SUITE 2: Layer 2 Test Questions (GUIDANCE_HELP)
    # -------------------------------------------------------------------------
    print("\n--- Suite 2: Layer 2 Questions (Expected: GUIDANCE_HELP) ---")

    layer2_queries = [
        ("Ye recommendation kyun di?", "low soil moisture"),
        ("420 litre kyun?", "420"),
        ("Irrigation kab karna hai?", "6 pm"),
        ("Ye disease result ka matlab kya hai?", "tomato early blight"),
        ("Plan change kyun hua?", "pehle"),
        ("Pehle kuch aur bola tha, ab kuch aur kyun?", "pehle"),
        ("Ab mujhe kya karna hai?", "irrigate 420 l")
    ]

    for q, expected_snippet in layer2_queries:
        total_tests += 1
        r = client.post("/api/voice/saathi", json={
            "text": q,
            "guidance_context": trusted_guidance,
            "current_page": "farmer-dashboard",
            "language": "hinglish"
        })
        assert r.status_code == 200
        d = r.json()
        assert d["layer"] == "GUIDANCE_HELP", f"Expected GUIDANCE_HELP for '{q}', got {d['layer']}"
        res_lower = d["response_text"].lower()
        assert expected_snippet.lower() in res_lower, f"Expected '{expected_snippet}' in '{d['response_text']}'"
        print(f"[PASS] '{q}' -> Layer: {d['layer']} | Response: {d['response_text'][:80]}...")
        passed_tests += 1

    # -------------------------------------------------------------------------
    # SUITE 3: Mixed Conversation Workflow (Layer 1 <-> Layer 2 Transitions)
    # -------------------------------------------------------------------------
    print("\n--- Suite 3: Mixed Multi-Turn Conversation Flow ---")

    history = []

    # Turn 1: "Saathi, weather kahan hai?" -> Layer 1
    total_tests += 1
    t1 = client.post("/api/voice/saathi", json={
        "text": "Saathi, weather kahan hai?",
        "current_page": "farmer-dashboard",
        "language": "hinglish"
    })
    assert t1.status_code == 200
    d1 = t1.json()
    assert d1["layer"] == "PLATFORM_HELP"
    history.append({"role": "user", "content": "Saathi, weather kahan hai?"})
    history.append({"role": "assistant", "content": d1["response_text"]})
    print(f"[PASS] Turn 1: 'Saathi, weather kahan hai?' -> Layer: {d1['layer']}")
    passed_tests += 1

    # Turn 2: "Ab yahan jo weather hai uska matlab kya hai?" -> Layer 2
    total_tests += 1
    t2 = client.post("/api/voice/saathi", json={
        "text": "Ab yahan jo weather hai uska matlab kya hai?",
        "current_page": "weather-dashboard",
        "guidance_context": trusted_guidance,
        "history": history,
        "language": "hinglish"
    })
    assert t2.status_code == 200
    d2 = t2.json()
    assert d2["layer"] == "GUIDANCE_HELP"
    history.append({"role": "user", "content": "Ab yahan jo weather hai uska matlab kya hai?"})
    history.append({"role": "assistant", "content": d2["response_text"]})
    print(f"[PASS] Turn 2: 'Ab yahan jo weather hai uska matlab kya hai?' -> Layer: {d2['layer']}")
    passed_tests += 1

    # Turn 3: "Ab mujhe kya karna hai?" -> Layer 2
    total_tests += 1
    t3 = client.post("/api/voice/saathi", json={
        "text": "Ab mujhe kya karna hai?",
        "current_page": "weather-dashboard",
        "guidance_context": trusted_guidance,
        "history": history,
        "language": "hinglish"
    })
    assert t3.status_code == 200
    d3 = t3.json()
    assert d3["layer"] == "GUIDANCE_HELP"
    history.append({"role": "user", "content": "Ab mujhe kya karna hai?"})
    history.append({"role": "assistant", "content": d3["response_text"]})
    print(f"[PASS] Turn 3: 'Ab mujhe kya karna hai?' -> Layer: {d3['layer']}")
    passed_tests += 1

    # Turn 4: "Dashboard kaise jaunga?" -> Layer 1
    total_tests += 1
    t4 = client.post("/api/voice/saathi", json={
        "text": "Dashboard kaise jaunga?",
        "current_page": "weather-dashboard",
        "history": history,
        "language": "hinglish"
    })
    assert t4.status_code == 200
    d4 = t4.json()
    assert d4["layer"] == "PLATFORM_HELP"
    print(f"[PASS] Turn 4: 'Dashboard kaise jaunga?' -> Layer: {d4['layer']}")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # SUITE 4: Safety Guard (Unavailable Layer 2 Guidance)
    # -------------------------------------------------------------------------
    print("\n--- Suite 4: Safety Guard (Unavailable Layer 2 Guidance) ---")

    total_tests += 1
    r_unavail = client.post("/api/voice/saathi", json={
        "text": "Ye recommendation kyun di?",
        "guidance_context": None,  # No guidance available
        "language": "hinglish"
    })
    assert r_unavail.status_code == 200
    d_unavail = r_unavail.json()
    assert d_unavail["layer"] == "GUIDANCE_HELP"
    res_unavail = d_unavail["response_text"].lower()
    assert "uplabdh nahi" in res_unavail or "currently unavailable" in res_unavail
    print(f"[PASS] Unavailable Guidance Guard: '{d_unavail['response_text']}'")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print(f"FINAL RESULT: {passed_tests}/{total_tests} Tests Passed ({(passed_tests/total_tests)*100:.1f}%)")
    print("=" * 70)

    return 0 if passed_tests == total_tests else 1


if __name__ == "__main__":
    sys.exit(run_step29_tests())

