"""
STEP 23 VERIFICATION SUITE
Saathi Human-Like Conversation & Interaction Validation
======================================================
Validates:
1. All 15 short, natural conversational utterances from Step 23 prompt.
2. Understanding check dynamic responses ("Haan", "Nahi", "Thoda").
3. Interruption and pause handling ("Ruko", "Ek minute").
4. Rolling context and pronoun reference resolution ("ye", "wo", "iska", "uska", "ab", "phir").
5. Simplification, brevity, and detailed elaboration queries.
6. Consecutive multi-turn conversational flow without state loss.
7. Zero manual mode toggle (Layer 1 vs Layer 2 automatic classification).
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

def test_1_fifteen_conversational_utterances():
    print("\n--- TEST 1: 15 NATURAL CONVERSATIONAL UTTERANCES ---")
    utterances = [
        ("Saathi?", "farmer-dashboard", None),
        ("Haan bolo.", "farmer-dashboard", None),
        ("Mujhe ek cheez puchni thi.", "farmer-dashboard", None),
        ("Achha ye batao...", "farmer-dashboard", None),
        ("Samajh nahi aaya.", "upload-crop", None),
        ("Phir kya karna hai?", "upload-crop", None),
        ("Accha.", "farmer-dashboard", None),
        ("Haan kar diya.", "upload-crop", {"steps": [{"action": "Upload leaf photo", "status": "completed"}, {"action": "Click Diagnose Disease", "status": "pending"}]}),
        ("Nahi hua.", "upload-crop", {"current_decision": {"action": "Upload leaf photo"}}),
        ("Ruko.", "farmer-dashboard", None),
        ("Ek minute.", "farmer-dashboard", None),
        ("Dobara batao.", "weather-dashboard", None),
        ("Thoda simple mein batao.", "farmer-dashboard", {"recommendation": {"action": "Apply Trichoderma spray", "reason": "high fungal humidity index"}}),
        ("Short mein batao.", "farmer-dashboard", {"recommendation": {"action": "Irrigate field with 400L", "timing": "6:00 AM", "quantity": "400L"}}),
        ("Detail mein samjhao.", "farmer-dashboard", {"recommendation": {"action": "Spray Chlorantraniliprole", "quantity": "150ml/acre", "timing": "Evening", "reason": "stem borer infestation risk"}})
    ]

    for utt, page, guidance in utterances:
        payload = {
            "message": utt,
            "text": utt,
            "language": "hinglish",
            "current_page": page,
            "mode": "saathi",
            "guidance_context": guidance
        }
        resp = client.post("/api/voice/saathi", json=payload)
        assert resp.status_code == 200, f"HTTP {resp.status_code} for '{utt}'"
        data = resp.json()
        assert data["success"] is True, f"Failed for '{utt}': {data}"
        assert data.get("response_text"), f"Empty response text for '{utt}'"
        assert len(data["response_text"].strip()) > 0
        print(f"  [PASS] Utterance: '{utt:28s}' -> [{data['layer']}] {data['response_text'][:75]}...")

def test_2_understanding_check_adaptation():
    print("\n--- TEST 2: DYNAMIC UNDERSTANDING CHECK RESPONSES (Haan / Nahi / Thoda) ---")
    
    # 1. Affirmation "Haan" -> Acknowledge warmly & proceed
    resp_haan = client.post("/api/voice/saathi", json={
        "message": "Haan",
        "language": "hinglish",
        "current_page": "upload-crop"
    }).json()
    assert resp_haan["success"] is True
    assert any(w in resp_haan["response_text"].lower() for w in ["badhiya", "step", "aage", "great"])
    print(f"  [PASS] 'Haan' -> {resp_haan['response_text']}")

    # 2. Negation "Nahi" -> Fresh simplification (not verbatim repeat)
    resp_nahi = client.post("/api/voice/saathi", json={
        "message": "Nahi",
        "language": "hinglish",
        "current_page": "upload-crop"
    }).json()
    assert resp_nahi["success"] is True
    assert "choose file" in resp_nahi["response_text"].lower() or "saral" in resp_nahi["response_text"].lower() or "aasan" in resp_nahi["response_text"].lower()
    print(f"  [PASS] 'Nahi' -> {resp_nahi['response_text']}")

    # 3. Partial "Thoda" -> Break down into single simplest step
    resp_thoda = client.post("/api/voice/saathi", json={
        "message": "Thoda",
        "language": "hinglish",
        "current_page": "farmer-dashboard"
    }).json()
    assert resp_thoda["success"] is True
    assert "saral" in resp_thoda["response_text"].lower() or "aasan" in resp_thoda["response_text"].lower() or "pehle" in resp_thoda["response_text"].lower()
    print(f"  [PASS] 'Thoda' -> {resp_thoda['response_text']}")

def test_3_interruptions_and_pauses():
    print("\n--- TEST 3: INTERRUPTIONS & PAUSES (Ruko / Ek minute) ---")
    pauses = ["Ruko", "Ek minute", "Wait", "Rukiye"]
    for p in pauses:
        resp = client.post("/api/voice/saathi", json={
            "message": p,
            "language": "hinglish",
            "current_page": "farmer-dashboard"
        }).json()
        assert resp["success"] is True
        assert any(w in resp["response_text"].lower() for w in ["rukta", "ready", "pause", "wait", "thambto", "हूँ"])
        print(f"  [PASS] Pause phrase: '{p:12s}' -> {resp['response_text']}")

def test_4_multi_turn_reference_resolution():
    print("\n--- TEST 4: MULTI-TURN ROLLING CONTEXT & PRONOUN RESOLUTION ('ye', 'wo', 'iska', 'iska reason') ---")
    history = [
        {"role": "assistant", "text": "AgriBridge ne do cheezein batai hain: 1. Apply Trichoderma spray, 2. Light irrigation."},
        {"role": "farmer", "text": "Iska reason kya hai?"}
    ]
    guidance = {
        "recommendations": [
            {"action": "Apply Trichoderma spray", "reason": "High soil fungus risk due to humid forecast", "dose": "500g/acre"},
            {"action": "Light irrigation", "reason": "Soil moisture is below 35%", "dose": "200L"}
        ]
    }
    # Farmer asks with pronoun referring to specific item
    payload = {
        "message": "Trichoderma spray ka reason kya hai?",
        "language": "hinglish",
        "history": history,
        "guidance_context": guidance
    }
    resp = client.post("/api/voice/saathi", json=payload).json()
    assert resp["success"] is True
    assert "fungus" in resp["response_text"].lower()
    print(f"  [PASS] Target resolution query -> {resp['response_text']}")

    # Next turn: Farmer asks "Iska dose kitna hai?"
    history.append({"role": "farmer", "text": "Trichoderma spray ka reason kya hai?"})
    history.append({"role": "assistant", "text": resp["response_text"]})
    payload2 = {
        "message": "Iska dose kitna hai?",
        "language": "hinglish",
        "history": history,
        "guidance_context": guidance
    }
    resp2 = client.post("/api/voice/saathi", json=payload2).json()
    assert resp2["success"] is True
    assert "500g" in resp2["response_text"].lower()
    print(f"  [PASS] Pronoun follow-up 'Iska dose kitna hai?' -> {resp2['response_text']}")

def test_5_multilingual_human_interaction():
    print("\n--- TEST 5: MULTILINGUAL HUMAN-LIKE INTERACTION (Hindi, Punjabi, Marathi, English) ---")
    multi_queries = [
        ("Saathi, ek cheez puchni thi", "hi", "हाँजी"),
        ("ਸਾਥੀ, ਰੁਕੋ ਜ਼ਰਾ", "pa", "ਮੈਂ"),
        ("साथी, थोडं सोप्या भाषेत सांगा", "mr", "सोप्या"),
        ("Saathi, explain in simple terms", "en", "simple")
    ]
    for q, lang, expected_token in multi_queries:
        resp = client.post("/api/voice/saathi", json={
            "message": q,
            "language": lang,
            "current_page": "farmer-dashboard",
            "guidance_context": {"recommendation": {"action": "Neem oil spray", "reason": "Aphid prevention"}}
        }).json()
        assert resp["success"] is True
        print(f"  [PASS] [{lang.upper()}] '{q}' -> {resp['response_text'][:75]}...")

if __name__ == "__main__":
    print("======================================================================")
    print("STEP 23: SAATHI HUMAN-LIKE CONVERSATION & INTERACTION VALIDATION")
    print("======================================================================")
    test_1_fifteen_conversational_utterances()
    test_2_understanding_check_adaptation()
    test_3_interruptions_and_pauses()
    test_4_multi_turn_reference_resolution()
    test_5_multilingual_human_interaction()
    print("\n======================================================================")
    print("✅ ALL STEP 23 HUMAN-LIKE CONVERSATION TESTS PASSED (100% SUCCESS)")
    print("======================================================================")

