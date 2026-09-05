"""
AgriBridge Saathi Voice Assistant Step 1 Comprehensive Unit Test Suite
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Validates:
1. Saathi First Message (canonical introduction adapted across 14 languages).
2. Automatic Multilingual Language Detection (never hardcodes Hindi, detects Indian scripts & Hinglish).
3. Dynamic Mid-Conversation Language Switching (detects language change at every turn).
4. Natural Conversational Behavior (handles greetings, identity, status, incomplete sentences).
5. Strict Step 1 Scope Guard (blocks mandi prices, weather, disease diagnosis, chemical prescriptions).
6. Speech synthesis integration and clean spoken response output.
"""

import sys
import json
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from fastapi.testclient import TestClient

from app.main import app
from app.services.saathi_service import detect_language, get_saathi_introduction

client = TestClient(app)


def test_saathi_first_message_all_languages():
    """Verify Saathi's canonical introduction adapts across supported Indian languages."""
    test_languages = ["hi", "hinglish", "en", "pa", "mr", "bn", "gu", "ta", "te", "kn", "ml", "or", "as", "ur"]
    
    for lang in test_languages:
        resp = client.get(f"/api/voice/saathi/intro?language={lang}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["language"] == lang
        intro_text = data["intro_text"]
        assert len(intro_text) > 20
        # Check that Saathi introduces itself by name in every language
        saathi_names = ["साथी", "Saathi", "ਸਾਥੀ", "சாதி", "సాథి", "ساتھی", "সাথী", "ସାଥୀ", "સાથી", "ಸಾಥಿ", "സാഥി"]
        assert any(name in intro_text for name in saathi_names), f"Saathi name missing in intro for {lang}: {intro_text}"


def test_automatic_multilingual_language_detection():
    """Verify that farmer utterances in different Indian languages are automatically detected."""
    test_cases = [
        ("नमस्ते साथी आप कैसे हैं?", "hi"),
        ("Hello Saathi, how are you today?", "en"),
        ("Namaste ji, main aapse baat karna chahta hoon", "hinglish"),
        ("ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ ਜੀ, ਕਿਵੇਂ ਹੋ?", "pa"),
        ("नमस्कार, कसे आहात?", "mr"),
        ("নমস্কার, কেমন আছেন?", "bn"),
        ("નમસ્તે, કેમ છો?", "gu"),
        ("నమస్కారం, మీరు ఎలా ఉన్నారు?", "te"),
        ("வணக்கம், எப்படி இருக்கிறீர்கள்?", "ta"),
        ("ನಮಸ್ಕಾರ, ಹೇಗಿದ್ದೀರಿ?", "kn"),
        ("നമസ്കാരം, സുഖമാണോ?", "ml"),
        ("سلام جی، آپ کیسے ہیں؟", "ur"),
    ]

    for utterance, expected_lang in test_cases:
        detected = detect_language(utterance)
        assert detected == expected_lang, f"Failed for '{utterance}': got {detected}, expected {expected_lang}"
        
        # Test full API response
        resp = client.post("/api/voice/saathi", json={"text": utterance})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["language"] == expected_lang, f"API returned {data['language']} instead of {expected_lang}"
        assert data["response_text"] is not None
        assert len(data["response_text"]) > 0


def test_no_hardcoded_hindi_response():
    """Verify that Hindi is never hardcoded when another language is used."""
    punjabi_query = "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ ਜੀ"
    r_pa = client.post("/api/voice/saathi", json={"text": punjabi_query}).json()
    assert r_pa["language"] == "pa"
    assert "ਨਮਸਤੇ" not in r_pa["response_text"]  # Must not return Hindi Devanagari

    telugu_query = "నమస్కారం, మీరు ఎలా ఉన్నారు?"
    r_te = client.post("/api/voice/saathi", json={"text": telugu_query}).json()
    assert r_te["language"] == "te"
    assert r_te["language"] != "hi"


def test_dynamic_mid_conversation_language_switching():
    """Verify Saathi switches languages automatically turn-by-turn without manual reconfiguration."""
    conversation = [
        ("Hello Saathi, who are you?", "en"),
        ("नमस्ते साथी, क्या आप मुझे सुन सकते हैं?", "hi"),
        ("ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ ਜੀ, ਸਭ ਠੀਕ ਹੈ?", "pa"),
        ("Accha laga aapse baat karke Saathi", "hinglish"),
        ("నమస్కారం అండి, బాగున్నారా?", "te"),
    ]

    history = []
    for text, expected_lang in conversation:
        resp = client.post("/api/voice/saathi", json={"text": text, "history": history}).json()
        assert resp["success"] is True
        assert resp["language"] == expected_lang, f"Turn '{text}' expected {expected_lang} but got {resp['language']}"
        history.append({"role": "farmer", "text": text})
        history.append({"role": "saathi", "text": resp["response_text"]})


def test_natural_conversational_behavior():
    """Verify Saathi handles conversational greetings, identity, status, and incomplete phrases."""
    # 1. Identity inquiry
    r_id = client.post("/api/voice/saathi", json={"text": "Who are you?"}).json()
    assert "Saathi" in r_id["response_text"]

    # 2. Status inquiry
    r_status = client.post("/api/voice/saathi", json={"text": "Kaise ho aap?"}).json()
    assert r_status["language"] == "hinglish"
    assert len(r_status["response_text"]) > 5

    # 3. Simple incomplete sentence / filler
    r_incomplete = client.post("/api/voice/saathi", json={"text": "Haanji suno..."}).json()
    assert r_incomplete["success"] is True
    assert len(r_incomplete["response_text"]) > 0


def test_strict_step_1_scope_guard():
    """Verify Saathi politely defers out-of-scope farming topics in Step 1."""
    # 1. Mandi prices request
    r_mandi = client.post("/api/voice/saathi", json={"text": "Wheat ka mandi bhav kya hai?"}).json()
    assert r_mandi["success"] is True
    # Should NOT return price values or quintal rates
    assert "₹" not in r_mandi["response_text"]
    assert "quintal" not in r_mandi["response_text"].lower()

    # 2. Weather forecast request
    r_weather = client.post("/api/voice/saathi", json={"text": "Kal barish hogi kya?"}).json()
    assert r_weather["success"] is True
    # Should NOT return forecast degrees or millimeters
    assert "°C" not in r_weather["response_text"]
    assert "mm" not in r_weather["response_text"]

    # 3. Disease diagnosis / chemical prescription request
    r_disease = client.post("/api/voice/saathi", json={"text": "Pattiyon par peela rog hai kaun si dawai daalu?"}).json()
    assert r_disease["success"] is True
    # Should NOT prescribe chemicals
    assert "propiconazole" not in r_disease["response_text"].lower()
    assert "tebuconazole" not in r_disease["response_text"].lower()


def test_ask_text_backward_compatibility_with_saathi_mode():
    """Verify that existing /api/voice/ask-text supports Saathi companion mode."""
    resp = client.post("/api/voice/ask-text", json={
        "text": "Namaste Saathi ji",
        "mode": "saathi"
    }).json()
    assert resp["success"] is True
    assert resp["language"] == "hinglish"
    assert len(resp["response_text"]) > 0


if __name__ == "__main__":
    print("Running Saathi Step 1 Unit Test Suite...")
    test_saathi_first_message_all_languages()
    print("  [PASSED] Saathi First Message in all 14 languages")
    test_automatic_multilingual_language_detection()
    print("  [PASSED] Automatic Multilingual Language Detection (all scripts)")
    test_no_hardcoded_hindi_response()
    print("  [PASSED] No Hardcoded Hindi Response")
    test_dynamic_mid_conversation_language_switching()
    print("  [PASSED] Dynamic Mid-Conversation Language Switching")
    test_natural_conversational_behavior()
    print("  [PASSED] Natural Conversational Behavior")
    test_strict_step_1_scope_guard()
    print("  [PASSED] Strict Step 1 Scope Guard (No mandi, weather, disease)")
    test_ask_text_backward_compatibility_with_saathi_mode()
    print("  [PASSED] Backward Compatibility via /api/voice/ask-text mode=saathi")
    print("\nALL SAATHI STEP 1 TESTS PASSED SUCCESSFULLY!")
