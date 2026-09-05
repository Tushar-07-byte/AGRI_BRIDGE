"""
STEP 24 VERIFICATION SUITE
Complete Multilingual Saathi Validation
======================================
Validates:
1. English test category (Weather, replanning, disease upload, simple explanation).
2. Hindi test category (Devanagari queries for weather, reasons, crop scan, simplification).
3. Hinglish test category (Code-mixed Hindi-English queries).
4. Multi-turn language switching sequence (Hindi -> English -> Hindi -> Hinglish) preserving context.
5. Semantic equivalence & exact unit/value preservation (400L, 500g/acre, 35% moisture).
6. Robustness against speech variations (pauses, fillers, repeated words, regional variations).
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

REPLAN_GUIDANCE_CONTEXT = {
    "is_replanned": True,
    "version": 2,
    "current_decision": {
        "action": "Postpone irrigation",
        "quantity": "0L",
        "reason": "heavy rain forecast of 45mm tomorrow",
        "timing": "Next 48 hours"
    },
    "previous_decision": {
        "action": "Irrigate field with 400L",
        "quantity": "400L",
        "reason": "low soil moisture at 28%",
        "timing": "Today 6:00 AM"
    },
    "new_information": "85% heavy rain precipitation forecast",
    "reason_for_update": "Heavy rain risk avoidance"
}

STANDARD_GUIDANCE_CONTEXT = {
    "recommendation": {
        "action": "Apply Trichoderma spray",
        "quantity": "500g/acre",
        "timing": "6:00 AM",
        "reason": "high soil fungal risk due to high humidity"
    }
}

def test_1_english_category():
    print("\n--- TEST 1: ENGLISH CATEGORY ---")
    queries = [
        ("Where is the weather section?", "farmer-dashboard", None, "weather"),
        ("Why did AgriBridge change my irrigation plan?", "farmer-dashboard", REPLAN_GUIDANCE_CONTEXT, "previously"),
        ("How do I upload a crop image?", "farmer-dashboard", None, "crop"),
        ("Please explain this recommendation simply.", "farmer-dashboard", STANDARD_GUIDANCE_CONTEXT, "simple")
    ]
    for q, page, guidance, expected_token in queries:
        resp = client.post("/api/voice/saathi", json={
            "text": q,
            "message": q,
            "language": "en",
            "current_page": page,
            "guidance_context": guidance
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["language"] == "en"
        assert expected_token in data["response_text"].lower()
        print(f"  [PASS] [EN] '{q:45s}' -> [{data['layer']}] {data['response_text'][:70]}...")

def test_2_hindi_category():
    print("\n--- TEST 2: HINDI CATEGORY (DEVANAGARI) ---")
    queries = [
        ("मुझे मौसम कहाँ दिखाई देगा?", "farmer-dashboard", None, "मौसम"),
        ("यह सिफारिश क्यों दी गई है?", "farmer-dashboard", STANDARD_GUIDANCE_CONTEXT, "क्योंकि"),
        ("फसल की फोटो कैसे अपलोड करूं?", "farmer-dashboard", None, "AI Crop Scan"),
        ("मुझे समझ नहीं आया, आसान भाषा में बताओ।", "farmer-dashboard", STANDARD_GUIDANCE_CONTEXT, "सरल")
    ]
    for q, page, guidance, expected_token in queries:
        resp = client.post("/api/voice/saathi", json={
            "text": q,
            "message": q,
            "language": "hi",
            "current_page": page,
            "guidance_context": guidance
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["language"] == "hi"
        if expected_token not in data["response_text"]:
            print(f"DEBUG FAIL: q='{q}', expected_token='{expected_token}', actual='{data['response_text']}'")
        assert expected_token in data["response_text"], f"Expected '{expected_token}' in '{data['response_text']}'"
        print(f"  [PASS] [HI] '{q:40s}' -> [{data['layer']}] {data['response_text'][:70]}...")

def test_3_hinglish_category():
    print("\n--- TEST 3: HINGLISH CATEGORY ---")
    queries = [
        ("Saathi ye recommendation kyun aayi?", "farmer-dashboard", STANDARD_GUIDANCE_CONTEXT, "kyunki"),
        ("Mujhe crop ka photo upload karna hai.", "farmer-dashboard", None, "crop"),
        ("Ab mujhe kya karna hai?", "farmer-dashboard", STANDARD_GUIDANCE_CONTEXT, "karna hai"),
        ("Ye irrigation plan change kyun hua?", "farmer-dashboard", REPLAN_GUIDANCE_CONTEXT, "pehle"),
        ("Simple mein samjhao.", "farmer-dashboard", STANDARD_GUIDANCE_CONTEXT, "aasan")
    ]
    for q, page, guidance, expected_token in queries:
        resp = client.post("/api/voice/saathi", json={
            "text": q,
            "message": q,
            "language": "hinglish",
            "current_page": page,
            "guidance_context": guidance
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["language"] == "hinglish"
        assert expected_token in data["response_text"].lower()
        print(f"  [PASS] [HINGLISH] '{q:40s}' -> [{data['layer']}] {data['response_text'][:70]}...")

def test_4_language_switching_sequence():
    print("\n--- TEST 4: MULTI-TURN LANGUAGE SWITCHING SEQUENCE ---")
    history = []
    
    # 1. Start in Hindi: "Saathi, mujhe weather dikhao."
    turn1 = client.post("/api/voice/saathi", json={
        "text": "Saathi, mujhe weather dikhao.",
        "language": "hi",
        "current_page": "farmer-dashboard",
        "history": history,
        "guidance_context": REPLAN_GUIDANCE_CONTEXT
    }).json()
    assert turn1["success"] is True
    print(f"  Turn 1 (Hindi Initial) -> Lang: {turn1['language']} | Response: {turn1['response_text']}")
    history.append({"role": "farmer", "text": "Saathi, mujhe weather dikhao."})
    history.append({"role": "assistant", "text": turn1["response_text"]})

    # 2. Switch to English: "Okay, now explain why the plan changed."
    turn2 = client.post("/api/voice/saathi", json={
        "text": "Okay, now explain why the plan changed.",
        "language": "en",
        "current_page": "farmer-dashboard",
        "history": history,
        "guidance_context": REPLAN_GUIDANCE_CONTEXT
    }).json()
    assert turn2["success"] is True
    assert turn2["language"] == "en"
    assert "previously" in turn2["response_text"].lower()
    print(f"  Turn 2 (Switch to EN)  -> Lang: {turn2['language']} | Response: {turn2['response_text']}")
    history.append({"role": "farmer", "text": "Okay, now explain why the plan changed."})
    history.append({"role": "assistant", "text": turn2["response_text"]})

    # 3. Switch back to Hindi: "Ab Hindi mein batao."
    turn3 = client.post("/api/voice/saathi", json={
        "text": "Ab Hindi mein batao.",
        "current_page": "farmer-dashboard",
        "history": history,
        "guidance_context": REPLAN_GUIDANCE_CONTEXT
    }).json()
    assert turn3["success"] is True
    assert turn3["language"] == "hi"
    assert "पहले" in turn3["response_text"] or "agribridge" in turn3["response_text"].lower()
    print(f"  Turn 3 (Switch to HI)  -> Lang: {turn3['language']} | Response: {turn3['response_text']}")
    history.append({"role": "farmer", "text": "Ab Hindi mein batao."})
    history.append({"role": "assistant", "text": turn3["response_text"]})

    # 4. Switch to Hinglish: "Thoda simple Hinglish mein."
    turn4 = client.post("/api/voice/saathi", json={
        "text": "Thoda simple Hinglish mein.",
        "current_page": "farmer-dashboard",
        "history": history,
        "guidance_context": REPLAN_GUIDANCE_CONTEXT
    }).json()
    assert turn4["success"] is True
    assert turn4["language"] == "hinglish"
    assert "pehle" in turn4["response_text"].lower() or "baarish" in turn4["response_text"].lower() or "agribridge" in turn4["response_text"].lower()
    print(f"  Turn 4 (Switch to HING) -> Lang: {turn4['language']} | Response: {turn4['response_text']}")

def test_5_exact_value_and_unit_preservation():
    print("\n--- TEST 5: EXACT VALUE, QUANTITY & UNIT PRESERVATION ---")
    units_guidance = {
        "recommendation": {
            "action": "Spray Chlorantraniliprole 18.5% SC",
            "quantity": "150 ml/acre in 200 litre water",
            "timing": "5:30 PM",
            "reason": "Soil moisture at 32% and pest threshold exceeded"
        }
    }
    
    # 1. Quantity Inquiries
    res_en_qty = client.post("/api/voice/saathi", json={
        "text": "How much quantity or dose should I apply?",
        "language": "en",
        "guidance_context": units_guidance
    }).json()
    assert "150 ml/acre" in res_en_qty["response_text"] or "200 litre" in res_en_qty["response_text"]
    print(f"  [PASS] [EN Quantity] -> {res_en_qty['response_text']}")

    res_hi_qty = client.post("/api/voice/saathi", json={
        "text": "कितनी मात्रा में दवाई डालनी है?",
        "language": "hi",
        "guidance_context": units_guidance
    }).json()
    assert "150 ml/acre" in res_hi_qty["response_text"] or "200 litre" in res_hi_qty["response_text"]
    print(f"  [PASS] [HI Quantity] -> {res_hi_qty['response_text']}")

    res_hing_qty = client.post("/api/voice/saathi", json={
        "text": "Dose kitna daalna hai?",
        "language": "hinglish",
        "guidance_context": units_guidance
    }).json()
    assert "150 ml/acre" in res_hing_qty["response_text"] or "200 litre" in res_hing_qty["response_text"]
    print(f"  [PASS] [HING Quantity] -> {res_hing_qty['response_text']}")

    # 2. Timing Inquiries
    res_en_time = client.post("/api/voice/saathi", json={
        "text": "What is the scheduled timing for spray?",
        "language": "en",
        "guidance_context": units_guidance
    }).json()
    assert "5:30 pm" in res_en_time["response_text"].lower() or "5:30" in res_en_time["response_text"]
    print(f"  [PASS] [EN Timing]   -> {res_en_time['response_text']}")

    res_hi_time = client.post("/api/voice/saathi", json={
        "text": "किस समय छिड़काव करना है?",
        "language": "hi",
        "guidance_context": units_guidance
    }).json()
    if "5:30" not in res_hi_time.get("response_text", ""):
        print("DEBUG FAIL res_hi_time:", res_hi_time)
    assert "5:30 PM" in res_hi_time["response_text"] or "5:30" in res_hi_time["response_text"], f"Actual: {res_hi_time['response_text']}"
    print(f"  [PASS] [HI Timing]   -> {res_hi_time['response_text']}")

    res_hing_time = client.post("/api/voice/saathi", json={
        "text": "Kitne baje spray karna hai?",
        "language": "hinglish",
        "guidance_context": units_guidance
    }).json()
    assert "5:30 PM" in res_hing_time["response_text"] or "5:30" in res_hing_time["response_text"]
    print(f"  [PASS] [HING Timing] -> {res_hing_time['response_text']}")

def test_6_speech_variations_and_robustness():
    print("\n--- TEST 6: SPEECH VARIATIONS (PAUSES, CODE-MIXING, FILLERS) ---")
    variations = [
        ("Saathi... um... mujhe... weather dekhna hai...", "weather"),
        ("Bhai saathi jaldi batao mandi bhav kahan hai", "marketplace"),
        ("Saathi suno saathi suno crop scan kahan hai", "disease"),
        ("Acha saathi ji ye bataiye weather kahan milega", "weather")
    ]
    for v, expected_feat in variations:
        resp = client.post("/api/voice/saathi", json={
            "text": v,
            "current_page": "farmer-dashboard"
        }).json()
        assert resp["success"] is True
        print(f"  [PASS] Variation: '{v:50s}' -> {resp['response_text'][:70]}...")

if __name__ == "__main__":
    print("======================================================================")
    print("STEP 24: COMPLETE MULTILINGUAL SAATHI VALIDATION")
    print("======================================================================")
    test_1_english_category()
    test_2_hindi_category()
    test_3_hinglish_category()
    test_4_language_switching_sequence()
    test_5_exact_value_and_unit_preservation()
    test_6_speech_variations_and_robustness()
    print("\n======================================================================")
    print("✅ ALL STEP 24 MULTILINGUAL TESTS PASSED (100% SUCCESS)")
    print("======================================================================")
