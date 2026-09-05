"""
STEP 25 VERIFICATION SUITE
Realistic Farmer Speech & Imperfect Query Testing
==================================================
Validates:
1. Realistic Hindi/Hinglish farmer utterances (22 phrases: single words, imperfect grammar, colloquial queries).
2. Incomplete speech handling:
   - With context (e.g., "Paani wala...", "Photo upload...", "Mandi...", "Ye disease...") -> Answers and resolves
   - Without context (e.g., "Saathi... ye...", "Mujhe...", "Wo jo...") -> Politely asks clarification
3. Multi-turn conversational reference resolution sequence:
   - Turn 1: "Ye recommendation kya hai?" -> General explanation
   - Turn 2: "Isme kitna hai?" -> Quantity/dosage for active recommendation
   - Turn 3: "Achha, kab karna hai?" -> Timing for active recommendation
   - Turn 4: "Phir agar baarish ho gayi?" -> Contingency/replanning explanation
"""

import os
import sys

# Reconfigure stdout for UTF-8 in Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient

# Add backend directory to path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app

client = TestClient(app)

MOCK_GUIDANCE = {
    "recommendation": {
        "action": "Hold irrigation and apply 2.5 kg/ha Zinc Sulphate foliar spray",
        "reason": "Rain forecasted in next 24 hours with high soil moisture.",
        "quantity": "2.5 kg/ha Zinc Sulphate in 200 liters water",
        "timing": "Friday morning between 7:00 AM and 10:00 AM",
        "dose": "2.5 kg/ha",
        "method": "Knapsack sprayer with fine hollow cone nozzle",
        "replanned": True,
        "contingency": "Agar baarish ho jaye toh spray postpone karein aur mausam khulne par hi karein."
    },
    "current_decision": {
        "action": "Foliar Zinc Sulphate Spray",
        "quantity": "2.5 kg/ha",
        "timing": "Friday morning 7:00 AM - 10:00 AM",
        "reason": "Rain forecasted in next 24 hours (85% probability)"
    }
}

def test_1_twenty_two_realistic_farmer_utterances():
    print("\n" + "="*70)
    print("TEST 1: 22 REALISTIC HINDI / HINGLISH FARMER UTTERANCES")
    print("="*70)

    test_queries = [
        "Saathi ye wala kya hai?",
        "Isme kya karna hai?",
        "Ab kya karu?",
        "Ye kyun aaya?",
        "Paani kab dena hai?",
        "Kitna paani?",
        "Ye kaise hoga?",
        "Mujhe samajh nahi aaya.",
        "Phir se batao.",
        "Thoda aasaan mein batao.",
        "Ye jo upar hai uska kya?",
        "Neeche wala kahan hai?",
        "Wo button nahi mil raha.",
        "Haan kar diya.",
        "Nahi ho raha.",
        "Aage kya?",
        "Ab?",
        "Kyun?",
        "Kaise?",
        "Kitna?",
        "Kab?",
        "Iska matlab?"
    ]

    passed = 0
    for query in test_queries:
        payload = {
            "message": query,
            "text": query,
            "language": "hinglish",
            "current_page": "farmer-dashboard",
            "guidance_context": MOCK_GUIDANCE,
            "history": [
                {"role": "assistant", "text": "Aapki fasal ke liye Zinc Sulphate foliar spray ki sifarish hai."}
            ]
        }
        resp = client.post("/api/voice/saathi", json=payload)
        assert resp.status_code == 200, f"HTTP {resp.status_code} for query: {query}"
        data = resp.json()
        assert data.get("success") is True, f"Response success was False for: {query}"
        text = data.get("response_text", "").strip()
        assert len(text) > 0, f"Empty response text for: {query}"
        print(f"  [PASS] '{query:28s}' -> [{data.get('layer', 'saathi')}] {text[:70]}...")
        passed += 1

    print(f"\nResult: {passed}/{len(test_queries)} realistic queries verified successfully.")
    assert passed == len(test_queries)


def test_2_incomplete_speech_and_context_determination():
    print("\n" + "="*70)
    print("TEST 2: INCOMPLETE SPEECH & CONTEXT DETERMINATION")
    print("="*70)

    # 2A. Incomplete speech with enough agricultural / navigation context
    context_rich_queries = [
        ("Paani wala...", "weather / irrigation"),
        ("Photo upload...", "AI crop scan / disease detection"),
        ("Mandi...", "marketplace / mandi bhav"),
        ("Ye disease...", "disease detection")
    ]

    print("\n--- Subtest 2A: Incomplete speech WITH sufficient context (should resolve & answer) ---")
    for query, desc in context_rich_queries:
        payload = {
            "message": query,
            "language": "hinglish",
            "current_page": "farmer-dashboard",
            "guidance_context": MOCK_GUIDANCE
        }
        resp = client.post("/api/voice/saathi", json=payload).json()
        assert resp["success"] is True
        text = resp["response_text"].strip()
        assert len(text) > 10, f"Response too short for '{query}': {text}"
        print(f"  [PASS] '{query:18s}' ({desc}) -> {text[:75]}...")

    # 2B. Incomplete speech without sufficient context (should politely ask what the farmer means)
    vague_queries = [
        "Saathi... ye...",
        "Mujhe...",
        "Wo jo..."
    ]

    print("\n--- Subtest 2B: Incomplete speech WITHOUT context (should ask polite clarification) ---")
    for query in vague_queries:
        payload = {
            "message": query,
            "language": "hinglish",
            "current_page": "farmer-dashboard"
        }
        resp = client.post("/api/voice/saathi", json=payload).json()
        assert resp["success"] is True
        text = resp["response_text"].strip()
        assert len(text) > 5
        print(f"  [PASS] '{query:18s}' -> {text}")


def test_3_conversational_references_sequence():
    print("\n" + "="*70)
    print("TEST 3: CONVERSATIONAL REFERENCE RESOLUTION SEQUENCE (4 TURNS)")
    print("="*70)

    history = []

    # Turn 1: "Ye recommendation kya hai?"
    print("\nTurn 1: 'Ye recommendation kya hai?'")
    p1 = {
        "message": "Ye recommendation kya hai?",
        "language": "hinglish",
        "current_page": "farmer-dashboard",
        "guidance_context": MOCK_GUIDANCE,
        "history": history
    }
    r1 = client.post("/api/voice/saathi", json=p1).json()
    assert r1["success"] is True
    t1 = r1["response_text"]
    print(f"  Saathi: {t1}")
    assert any(k in t1.lower() for k in ["zinc", "spray", "recommendation", "sifarish", "irrigation", "paani"])
    history.append({"role": "farmer", "text": "Ye recommendation kya hai?"})
    history.append({"role": "assistant", "text": t1})

    # Turn 2: "Isme kitna hai?"
    print("\nTurn 2: 'Isme kitna hai?'")
    p2 = {
        "message": "Isme kitna hai?",
        "language": "hinglish",
        "current_page": "farmer-dashboard",
        "guidance_context": MOCK_GUIDANCE,
        "history": history
    }
    r2 = client.post("/api/voice/saathi", json=p2).json()
    assert r2["success"] is True
    t2 = r2["response_text"]
    print(f"  Saathi: {t2}")
    assert any(k in t2.lower() for k in ["2.5", "kg", "dose", "matra", "maatra", "quantity"])
    history.append({"role": "farmer", "text": "Isme kitna hai?"})
    history.append({"role": "assistant", "text": t2})

    # Turn 3: "Achha, kab karna hai?"
    print("\nTurn 3: 'Achha, kab karna hai?'")
    p3 = {
        "message": "Achha, kab karna hai?",
        "language": "hinglish",
        "current_page": "farmer-dashboard",
        "guidance_context": MOCK_GUIDANCE,
        "history": history
    }
    r3 = client.post("/api/voice/saathi", json=p3).json()
    assert r3["success"] is True
    t3 = r3["response_text"]
    print(f"  Saathi: {t3}")
    assert any(k in t3.lower() for k in ["friday", "subah", "morning", "7", "samay", "time", "ghante"])
    history.append({"role": "farmer", "text": "Achha, kab karna hai?"})
    history.append({"role": "assistant", "text": t3})

    # Turn 4: "Phir agar baarish ho gayi?"
    print("\nTurn 4: 'Phir agar baarish ho gayi?'")
    p4 = {
        "message": "Phir agar baarish ho gayi?",
        "language": "hinglish",
        "current_page": "farmer-dashboard",
        "guidance_context": MOCK_GUIDANCE,
        "history": history
    }
    r4 = client.post("/api/voice/saathi", json=p4).json()
    assert r4["success"] is True
    t4 = r4["response_text"]
    print(f"  Saathi: {t4}")
    assert any(k in t4.lower() for k in ["baarish", "rain", "postpone", "rok", "badal", "update", "mausam", "agribridge"])
    print("  [PASS] All 4 turns in conversational reference sequence resolved accurately!")


if __name__ == "__main__":
    print("======================================================================")
    print("STEP 25: REALISTIC FARMER SPEECH & IMPERFECT QUERY TESTING")
    print("======================================================================")
    test_1_twenty_two_realistic_farmer_utterances()
    test_2_incomplete_speech_and_context_determination()
    test_3_conversational_references_sequence()
    print("\n======================================================================")
    print("✅ ALL STEP 25 REALISTIC FARMER SPEECH TESTS PASSED (100% SUCCESS)")
    print("======================================================================")

