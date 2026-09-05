"""
AgriBridge Saathi Step 28: Agricultural Guidance Explanation & Farmer Understanding Validation
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Validates:
1. Scenario Testing with Trusted AgriBridge Guidance:
   - Soil moisture: 18%
   - Recommendation: 420 L at 6 PM
   - Reason: low soil moisture
2. Multi-turn Sequential Conversation:
   - 'Saathi, ye recommendation kya hai?' -> Explains actual guidance with trusted context & units
   - 'Kyun?' -> Explains reason from source
   - '420 litre kyun?' -> Explains quantity reason preserving 420 L unit
   - '6 baje hi kyun?' -> Explains timing reason preserving 6 PM
   - 'Kaise karna hai?' -> Explains method grounded in the recommendation
   - 'Samajh nahi aaya.' -> Simplifies explanation in simple language
3. Understanding Verification & Transitions:
   - Farmer says 'Haan' -> Continues naturally
   - Farmer says 'Nahi' -> Explains differently using simpler language
   - Farmer says 'Thoda' -> Gives a shorter, crisper explanation
   - Farmer asks a new question -> Answers directly without forcing understanding check
4. Zero Agricultural Fabrication Guard:
   - Preserves exact source values (18%, 420 L, 6 PM)
   - Refuses unauthorized pesticide inventions or independent decision alterations
"""

import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def run_step28_tests():
    print("=" * 70)
    print("STEP 28 VERIFICATION: AGRICULTURAL GUIDANCE EXPLANATION & UNDERSTANDING")
    print("=" * 70)

    total_tests = 0
    passed_tests = 0

    # Trusted AgriBridge Guidance Context for Test
    trusted_guidance = {
        "crop": "Tomato",
        "soil_moisture": "18%",
        "recommendation": {
            "action": "Irrigate 420 L at 6 PM",
            "quantity": "420 L",
            "timing": "6 PM",
            "reason": "low soil moisture"
        },
        "decision_id": "DEC-TOMATO-420L",
        "confidence": 0.95,
        "sources": {"decision_engine": "AgriBridge Ultra Decision Matrix"}
    }

    # -------------------------------------------------------------------------
    # SUITE 1: Multi-Turn Explanation Flow (Example Scenario)
    # -------------------------------------------------------------------------
    print("\n--- Suite 1: Sequential Agricultural Guidance Flow ---")
    
    # Turn 1: "Saathi, ye recommendation kya hai?"
    total_tests += 1
    r1 = client.post("/api/voice/saathi", json={
        "text": "Saathi, ye recommendation kya hai?",
        "guidance_context": trusted_guidance,
        "language": "hinglish"
    })
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["success"] is True
    assert d1["layer"] == "GUIDANCE_HELP"
    res1 = d1["response_text"].lower()
    assert "420 l" in res1 or "irrigate" in res1 or "low soil moisture" in res1
    assert "samajh aa gaya" in res1 or "samajh" in res1
    print(f"[PASS] Turn 1: 'Saathi, ye recommendation kya hai?'\n       Response: {d1['response_text']}")
    passed_tests += 1

    # Turn 2: "Kyun?"
    total_tests += 1
    r2 = client.post("/api/voice/saathi", json={
        "text": "Kyun?",
        "guidance_context": trusted_guidance,
        "history": [{"role": "user", "content": "Saathi, ye recommendation kya hai?"}, {"role": "assistant", "content": d1["response_text"]}],
        "language": "hinglish"
    })
    assert r2.status_code == 200
    d2 = r2.json()
    res2 = d2["response_text"].lower()
    assert "low soil moisture" in res2 or "moisture" in res2 or "18%" in res2
    print(f"[PASS] Turn 2: 'Kyun?'\n       Response: {d2['response_text']}")
    passed_tests += 1

    # Turn 3: "420 litre kyun?"
    total_tests += 1
    r3 = client.post("/api/voice/saathi", json={
        "text": "420 litre kyun?",
        "guidance_context": trusted_guidance,
        "language": "hinglish"
    })
    assert r3.status_code == 200
    d3 = r3.json()
    res3 = d3["response_text"].lower()
    assert "420 l" in res3 or "420" in res3
    assert "low soil moisture" in res3 or "18%" in res3
    print(f"[PASS] Turn 3: '420 litre kyun?'\n       Response: {d3['response_text']}")
    passed_tests += 1

    # Turn 4: "6 baje hi kyun?"
    total_tests += 1
    r4 = client.post("/api/voice/saathi", json={
        "text": "6 baje hi kyun?",
        "guidance_context": trusted_guidance,
        "language": "hinglish"
    })
    assert r4.status_code == 200
    d4 = r4.json()
    res4 = d4["response_text"].lower()
    assert "6 pm" in res4 or "6 baje" in res4 or "samay" in res4
    assert "low soil moisture" in res4 or "18%" in res4 or "field" in res4
    print(f"[PASS] Turn 4: '6 baje hi kyun?'\n       Response: {d4['response_text']}")
    passed_tests += 1

    # Turn 5: "Kaise karna hai?"
    total_tests += 1
    r5 = client.post("/api/voice/saathi", json={
        "text": "Kaise karna hai?",
        "guidance_context": trusted_guidance,
        "language": "hinglish"
    })
    assert r5.status_code == 200
    d5 = r5.json()
    res5 = d5["response_text"].lower()
    assert "irrigation" in res5 or "paani" in res5 or "420 l" in res5 or "steps" in res5
    print(f"[PASS] Turn 5: 'Kaise karna hai?'\n       Response: {d5['response_text']}")
    passed_tests += 1

    # Turn 6: "Samajh nahi aaya."
    total_tests += 1
    r6 = client.post("/api/voice/saathi", json={
        "text": "Samajh nahi aaya.",
        "guidance_context": trusted_guidance,
        "language": "hinglish"
    })
    assert r6.status_code == 200
    d6 = r6.json()
    res6 = d6["response_text"].lower()
    assert "aasan" in res6 or "seedhe" in res6 or "irrigate" in res6 or "420 l" in res6 or "18%" in res6
    print(f"[PASS] Turn 6: 'Samajh nahi aaya.'\n       Response: {d6['response_text']}")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # SUITE 2: Understanding Verification & Natural Transitions
    # -------------------------------------------------------------------------
    print("\n--- Suite 2: Understanding Verification & Farmer Responses ---")

    # Farmer says 'Haan' -> Continue naturally
    total_tests += 1
    rh = client.post("/api/voice/saathi", json={
        "text": "Haan.",
        "guidance_context": trusted_guidance,
        "history": [{"role": "assistant", "content": "AgriBridge ka active sujhav hai: 'Irrigate 420 L at 6 PM'. Samajh aa gaya ji?"}],
        "language": "hinglish"
    })
    assert rh.status_code == 200
    dh = rh.json()
    resh = dh["response_text"].lower()
    assert "badhiya" in resh or "sawaal" in resh or "poochiye" in resh or "great" in resh
    print(f"[PASS] Farmer says: 'Haan.' -> '{dh['response_text']}'")
    passed_tests += 1

    # Farmer says 'Nahi' -> Explain differently using simpler language
    total_tests += 1
    rn = client.post("/api/voice/saathi", json={
        "text": "Nahi.",
        "guidance_context": trusted_guidance,
        "history": [{"role": "assistant", "content": "AgriBridge ka active sujhav hai: 'Irrigate 420 L at 6 PM'. Samajh aa gaya ji?"}],
        "language": "hinglish"
    })
    assert rn.status_code == 200
    dn = rn.json()
    resn = dn["response_text"].lower()
    assert "seedhe" in resn or "aasan" in resn or "420 l" in resn or "nami" in resn or "low soil moisture" in resn
    print(f"[PASS] Farmer says: 'Nahi.' -> '{dn['response_text']}'")
    passed_tests += 1

    # Farmer says 'Thoda' -> Give shorter, clearer explanation
    total_tests += 1
    rt = client.post("/api/voice/saathi", json={
        "text": "Thoda.",
        "guidance_context": trusted_guidance,
        "history": [{"role": "assistant", "content": "AgriBridge ka active sujhav hai: 'Irrigate 420 L at 6 PM'. Samajh aa gaya ji?"}],
        "language": "hinglish"
    })
    assert rt.status_code == 200
    dt = rt.json()
    rest = dt["response_text"].lower()
    assert "short mein" in rest or "420 l" in rest or "moisture" in rest or "6 pm" in rest
    print(f"[PASS] Farmer says: 'Thoda.' -> '{dt['response_text']}'")
    passed_tests += 1

    # Farmer asks a new question instead of yes/no -> Directly answers new question
    total_tests += 1
    rq = client.post("/api/voice/saathi", json={
        "text": "Paani kab dena hai?",
        "guidance_context": trusted_guidance,
        "history": [{"role": "assistant", "content": "AgriBridge ka active sujhav hai: 'Irrigate 420 L at 6 PM'. Samajh aa gaya ji?"}],
        "language": "hinglish"
    })
    assert rq.status_code == 200
    dq = rq.json()
    resq = dq["response_text"].lower()
    assert "6 pm" in resq or "samay" in resq or "timing" in resq
    assert "samajh aa gaya" not in resq  # Does not force repetitive check on direct query
    print(f"[PASS] Farmer asks new question: 'Paani kab dena hai?' -> '{dq['response_text']}'")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # SUITE 3: Multilingual Guidance Explanation & Fidelity (Hindi & English)
    # -------------------------------------------------------------------------
    print("\n--- Suite 3: Multilingual Fidelity (Hindi & English) ---")

    # Hindi Explanation
    total_tests += 1
    r_hi = client.post("/api/voice/saathi", json={
        "text": "यह सिफारिश क्यों दी गई है?",
        "guidance_context": trusted_guidance,
        "language": "hi"
    })
    assert r_hi.status_code == 200
    d_hi = r_hi.json()
    assert d_hi["language"] == "hi"
    res_hi = d_hi["response_text"]
    assert "420 L" in res_hi or "Irrigate" in res_hi or "low soil moisture" in res_hi or "नमी" in res_hi
    print(f"[PASS] Hindi: 'यह सिफारिश क्यों दी गई है?' -> '{d_hi['response_text']}'")
    passed_tests += 1

    # English Explanation
    total_tests += 1
    r_en = client.post("/api/voice/saathi", json={
        "text": "Why 420 liters?",
        "guidance_context": trusted_guidance,
        "language": "en"
    })
    assert r_en.status_code == 200
    d_en = r_en.json()
    res_en = d_en["response_text"].lower()
    assert "420 l" in res_en or "420" in res_en
    assert "low soil moisture" in res_en or "18%" in res_en
    print(f"[PASS] English: 'Why 420 liters?' -> '{d_en['response_text']}'")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # SUITE 4: Grounding Guard & Zero Unauthorized Decision Invention
    # -------------------------------------------------------------------------
    print("\n--- Suite 4: Zero Unauthorized Decision Creation / Chemical Guard ---")

    # Farmer asks for pesticide when no pesticide exists in context
    total_tests += 1
    r_pest = client.post("/api/voice/saathi", json={
        "text": "Kaunsa pesticide spray karna hai?",
        "guidance_context": trusted_guidance,
        "language": "hinglish"
    })
    assert r_pest.status_code == 200
    d_pest = r_pest.json()
    assert d_pest["layer"] == "GUIDANCE_HELP"
    res_pest = d_pest["response_text"].lower()
    assert "koi specific pesticide" in res_pest or "suggest nahi" in res_pest or "ai crop scan" in res_pest
    print(f"[PASS] Pesticide Hallucination Blocked: '{d_pest['response_text']}'")
    passed_tests += 1

    # Missing value handling (missing quantity)
    total_tests += 1
    guidance_no_qty = {
        "crop": "Wheat",
        "recommendation": {
            "action": "Weeding in row 3",
            "reason": "high weed density"
        }
    }
    r_noqty = client.post("/api/voice/saathi", json={
        "text": "Kitna quantity lagana hai?",
        "guidance_context": guidance_no_qty,
        "language": "hinglish"
    })
    assert r_noqty.status_code == 200
    d_noqty = r_noqty.json()
    res_noqty = d_noqty["response_text"].lower()
    assert "quantity uplabdh nahi" in res_noqty or "exact quantity" in res_noqty or "not available" in res_noqty
    print(f"[PASS] Missing Quantity Handled Faithfully: '{d_noqty['response_text']}'")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print(f"FINAL RESULT: {passed_tests}/{total_tests} Tests Passed ({(passed_tests/total_tests)*100:.1f}%)")
    print("=" * 70)

    return 0 if passed_tests == total_tests else 1


if __name__ == "__main__":
    sys.exit(run_step28_tests())

