"""
STEP 22 VERIFICATION SUITE
Saathi Wake-Up & Activation Validation
======================================
Validates:
1. English wake-up and activation phrases.
2. Hindi wake-up and activation phrases (Devanagari & Latin).
3. Hinglish wake-up and activation phrases.
4. Natural variations and imperfect pronunciations ("sathi", "saathi ji", "hey sathi", etc.).
5. Activation across all farmer-accessible pages.
6. Automatic Layer 1 vs Layer 2 mode detection (No manual mode selection forced).
7. Consecutive multi-turn conversational interaction without page reload.
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

def test_1_english_activation_phrases():
    print("\n--- TEST 1: ENGLISH WAKE-UP & ACTIVATION PHRASES ---")
    phrases = [
        "Saathi",
        "Hey Saathi",
        "Saathi, can you help me?",
        "Saathi, where should I go?",
        "Saathi, I need help."
    ]
    for p in phrases:
        payload = {
            "message": p,
            "text": p,
            "language": "en",
            "current_page": "farmer-dashboard",
            "mode": "saathi"
        }
        resp = client.post("/api/voice/saathi", json=payload)
        assert resp.status_code == 200, f"HTTP {resp.status_code} for '{p}'"
        data = resp.json()
        assert data["success"] is True, f"Failed for '{p}': {data}"
        assert data.get("response_text"), f"No response text for '{p}'"
        print(f"  [PASS] Phrase: '{p:30s}' -> Layer: {data['layer']} | Response: {data['response_text'][:70]}...")

def test_2_hindi_activation_phrases():
    print("\n--- TEST 2: HINDI WAKE-UP & ACTIVATION PHRASES ---")
    phrases = [
        ("साथी", "hi"),
        ("साथी मेरी मदद करो", "hi"),
        ("साथी, मुझे मदद चाहिए", "hi"),
        ("साथी, ये कैसे करना है?", "hi"),
        ("Saathi meri madad karo", "hi"),
        ("Saathi, mujhe help chahiye", "hi"),
        ("Saathi, ye kaise karna hai?", "hi")
    ]
    for p, lang in phrases:
        payload = {
            "message": p,
            "text": p,
            "language": lang,
            "current_page": "farmer-dashboard",
            "mode": "saathi"
        }
        resp = client.post("/api/voice/saathi", json=payload)
        assert resp.status_code == 200, f"HTTP {resp.status_code} for '{p}'"
        data = resp.json()
        assert data["success"] is True, f"Failed for '{p}': {data}"
        assert data.get("response_text"), f"No response text for '{p}'"
        print(f"  [PASS] Phrase: '{p:30s}' -> Layer: {data['layer']} | Response: {data['response_text'][:70]}...")

def test_3_hinglish_activation_phrases():
    print("\n--- TEST 3: HINGLISH WAKE-UP & ACTIVATION PHRASES ---")
    phrases = [
        "Saathi ye kaise karna hai?",
        "Saathi mujhe yahan kya karna hai?",
        "Saathi, ye button kahan hai?",
        "Saathi mandi bhav kahan hai?"
    ]
    for p in phrases:
        payload = {
            "message": p,
            "text": p,
            "language": "hinglish",
            "current_page": "farmer-dashboard",
            "mode": "saathi"
        }
        resp = client.post("/api/voice/saathi", json=payload)
        assert resp.status_code == 200, f"HTTP {resp.status_code} for '{p}'"
        data = resp.json()
        assert data["success"] is True, f"Failed for '{p}': {data}"
        assert data.get("response_text"), f"No response text for '{p}'"
        print(f"  [PASS] Phrase: '{p:35s}' -> Layer: {data['layer']} | Response: {data['response_text'][:70]}...")

def test_4_natural_variations_and_pronunciations():
    print("\n--- TEST 4: NATURAL VARIATIONS & IMPERFECT PRONUNCIATIONS ---")
    variations = [
        "sathi",
        "saathi ji",
        "hey sathi",
        "sathi suno",
        "saathi bhai",
        "sathi meri madad karo",
        "hey sathi mujhe batao",
        "sathi ji ye kaise karein"
    ]
    for p in variations:
        payload = {
            "message": p,
            "text": p,
            "language": "hinglish",
            "current_page": "farmer-dashboard",
            "mode": "saathi"
        }
        resp = client.post("/api/voice/saathi", json=payload)
        assert resp.status_code == 200, f"HTTP {resp.status_code} for '{p}'"
        data = resp.json()
        assert data["success"] is True, f"Failed for '{p}': {data}"
        assert data.get("response_text"), f"No response text for '{p}'"
        print(f"  [PASS] Variation: '{p:28s}' -> Layer: {data['layer']} | Response: {data['response_text'][:70]}...")

def test_5_activation_across_farmer_pages():
    print("\n--- TEST 5: ACTIVATION ACROSS ALL 18 FARMER-ACCESSIBLE PAGES ---")
    pages = [
        "index", "login", "signup", "farmer-dashboard", "farmer-profile",
        "farmer-details", "upload-crop", "ai-result", "crop-monitoring",
        "crop-recommendation", "crop-listings", "weather-dashboard", "orders",
        "order-confirmation", "action-plan-trace", "farm-command-center",
        "verification-status", "voice-assistant"
    ]
    for pg in pages:
        payload = {
            "message": "Saathi, where should I go?",
            "text": "Saathi, where should I go?",
            "language": "en",
            "current_page": pg,
            "mode": "saathi"
        }
        resp = client.post("/api/voice/saathi", json=payload)
        assert resp.status_code == 200, f"HTTP {resp.status_code} on page {pg}"
        data = resp.json()
        assert data["success"] is True
        print(f"  [PASS] Page: '{pg:22s}' -> Response: {data['response_text'][:65]}...")

def test_6_automatic_layer_routing():
    print("\n--- TEST 6: AUTOMATIC LAYER 1 VS LAYER 2 ROUTING (NO MANUAL SELECTION) ---")
    
    # Layer 1 Query: Platform Help
    l1_payload = {
        "message": "Saathi, ye button kahan hai?",
        "text": "Saathi, ye button kahan hai?",
        "language": "hinglish",
        "current_page": "farmer-dashboard"
    }
    resp1 = client.post("/api/voice/saathi", json=l1_payload)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["layer"] == "PLATFORM_HELP", f"Expected PLATFORM_HELP, got {data1['layer']}"
    print(f"  [PASS] L1 Query: 'Saathi, ye button kahan hai?' -> Auto-routed to Layer: {data1['layer']}")
    
    # Layer 2 Query: Guidance Help with Guidance Context
    l2_guidance_ctx = {
        "current_decision": {
            "action": "Apply Imidacloprid 17.8 SL",
            "quantity": "0.5 ml / litre water",
            "timing": "Evening 4:00 PM - 6:00 PM",
            "reason": "Aphid infestation threshold reached"
        },
        "recommendation": {
            "action": "Apply Imidacloprid 17.8 SL",
            "quantity": "0.5 ml / litre water",
            "timing": "Evening 4:00 PM - 6:00 PM",
            "reason": "Aphid infestation threshold reached"
        }
    }
    l2_payload = {
        "message": "Saathi, 0.5 ml kyun?",
        "text": "Saathi, 0.5 ml kyun?",
        "language": "hinglish",
        "guidance_context": l2_guidance_ctx,
        "current_page": "ai-result"
    }
    resp2 = client.post("/api/voice/saathi", json=l2_payload)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["layer"] == "GUIDANCE_HELP", f"Expected GUIDANCE_HELP, got {data2['layer']}"
    print(f"  [PASS] L2 Query: 'Saathi, 0.5 ml kyun?' -> Auto-routed to Layer: {data2['layer']} | Response: {data2['response_text'][:65]}...")

def test_7_consecutive_multi_turn_interaction():
    print("\n--- TEST 7: CONSECUTIVE MULTI-TURN INTERACTION (NO RELOAD) ---")
    
    history = []
    
    # Turn 1: Wake-up call
    t1_payload = {
        "message": "Hey Saathi",
        "language": "en",
        "history": history
    }
    r1 = client.post("/api/voice/saathi", json=t1_payload).json()
    assert r1["success"] is True
    history.append({"role": "user", "text": "Hey Saathi"})
    history.append({"role": "assistant", "text": r1["response_text"]})
    print(f"  [PASS] Turn 1 (Wake-Up): '{r1['response_text']}'")
    
    # Turn 2: Follow-up question
    t2_payload = {
        "message": "Where is the weather page?",
        "language": "en",
        "history": history
    }
    r2 = client.post("/api/voice/saathi", json=t2_payload).json()
    assert r2["success"] is True
    history.append({"role": "user", "text": "Where is the weather page?"})
    history.append({"role": "assistant", "text": r2["response_text"]})
    print(f"  [PASS] Turn 2 (Query):   '{r2['response_text'][:65]}...'")
    
    # Turn 3: Acknowledgment
    t3_payload = {
        "message": "Thank you Saathi",
        "language": "en",
        "history": history
    }
    r3 = client.post("/api/voice/saathi", json=t3_payload).json()
    assert r3["success"] is True
    print(f"  [PASS] Turn 3 (Ack):     '{r3['response_text']}'")

if __name__ == "__main__":
    print("==================================================================")
    print("STARTING STEP 22: SAATHI WAKE-UP & ACTIVATION VALIDATION")
    print("==================================================================")
    test_1_english_activation_phrases()
    test_2_hindi_activation_phrases()
    test_3_hinglish_activation_phrases()
    test_4_natural_variations_and_pronunciations()
    test_5_activation_across_farmer_pages()
    test_6_automatic_layer_routing()
    test_7_consecutive_multi_turn_interaction()
    print("\n==================================================================")
    print("ALL STEP 22 VALIDATION TESTS COMPLETED SUCCESSFULLY! (7/7 PASS)")
    print("==================================================================")

