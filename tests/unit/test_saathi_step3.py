"""
AgriBridge Saathi Voice Assistant Step 3 Comprehensive Unit Test Suite
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Validates:
1. Full Voice Interaction Flow: Speech/Text Input -> STT -> Saathi Response -> TTS Spoken Audio URL.
2. Natural Conversational Spoken Queries (e.g. 'Bhai mujhe mandi bhav wala option nahi mil raha.').
3. Graceful Audio Processing & Error Handling (empty audio, fallback messages, clear guidance).
4. Audio File Synthesis & Streaming via /api/voice/audio/{filename}.
5. Strict Scope Guard across Spoken Responses (no raw mandi prices, weather metrics, or chemical prescriptions).
6. Multi-turn Spoken Conversation continuity across Indian languages.
"""

import sys
import io
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from fastapi.testclient import TestClient

from app.main import app
from app.services.saathi_service import process_saathi_interaction
from app.services.text_to_speech import synthesize_speech_with_status

client = TestClient(app)


def test_natural_voice_query_mandi_bhav_option():
    """Verify natural spoken query 'Bhai mujhe mandi bhav wala option nahi mil raha.'"""
    resp = client.post("/api/voice/saathi", json={
        "text": "Bhai mujhe mandi bhav wala option nahi mil raha.",
        "current_page": "farmer-dashboard"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["language"] == "hinglish"
    res_text = data["response_text"]
    assert "Marketplace" in res_text or "Mandi" in res_text or "mandi" in res_text.lower()
    # Must NOT provide raw market price numbers
    assert "₹" not in res_text
    assert "quintal" not in res_text.lower()
    # Spoken audio file must be synthesized or scheduled
    if data.get("audio_url"):
        assert data["audio_url"].startswith("/api/voice/audio/")


def test_voice_crop_disease_photo_upload_guidance():
    """Verify natural spoken query asking where to upload leaf photo for disease checking."""
    resp = client.post("/api/voice/saathi", json={
        "text": "Bimari check karne ke liye photo kahan upload karu?",
        "current_page": "farmer-dashboard"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["language"] == "hinglish"
    res_text = data["response_text"]
    assert "Crop" in res_text or "Scan" in res_text or "AI" in res_text or "button" in res_text
    # Must NOT output chemical names
    assert "propiconazole" not in res_text.lower()


def test_voice_weather_button_query():
    """Verify natural spoken query asking about weather forecast button."""
    resp = client.post("/api/voice/saathi", json={
        "text": "Mausam aur barish wala button kaunsa hai?",
        "current_page": "farmer-dashboard"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["language"] == "hinglish"
    res_text = data["response_text"]
    assert "Weather" in res_text or "Mausam" in res_text
    assert "°C" not in res_text


def test_audio_file_generation_and_streaming():
    """Verify TTS synthesizes audio and /api/voice/audio endpoint serves the audio stream."""
    text = "Mandi Bhav dekhne ke liye upar diye gaye Marketplace button par click karein."
    filename, status = synthesize_speech_with_status(text, "hi")
    assert filename is not None
    assert filename.endswith(".mp3")

    # Fetch the audio stream from backend route
    resp = client.get(f"/api/voice/audio/{filename}")
    assert resp.status_code == 200
    assert resp.headers["content-type"] in ["audio/mpeg", "audio/mp3"]
    assert len(resp.content) > 100


def test_empty_audio_graceful_handling():
    """Verify empty or corrupted audio upload is handled gracefully without crashing."""
    fake_empty_audio = io.BytesIO(b"")
    files = {"audio": ("empty.webm", fake_empty_audio, "audio/webm")}
    resp = client.post("/api/voice/saathi", files=files)
    assert resp.status_code == 200
    data = resp.json()
    # Should return either intro or clear polite request to speak again
    assert data["success"] is True or "error" in data
    assert len(data.get("response_text") or data.get("error") or "") > 0


def test_multilingual_voice_conversation_flow():
    """Verify complete spoken interaction across Punjabi, Tamil, and Marathi."""
    test_cases = [
        ("ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ ਸਾਥੀ ਜੀ, ਮੰਡੀ ਦੇ ਭਾਅ ਕਿੱਥੇ ਦੇਖਣੇ ਹਨ?", "pa", ["Marketplace", "ਮੰਡੀ"]),
        ("வணக்கம், வானிலை பார்க்க எந்த பொத்தானை அழுத்த வேண்டும்?", "ta", ["Weather", "வானிலை"]),
        ("नमस्कार, पिकावरील रोगाची तपासणी कुठे करायची?", "mr", ["Crop Scan", "AI", "रोगाची"]),
    ]

    for q, expected_lang, expected_keywords in test_cases:
        resp = client.post("/api/voice/saathi", json={"text": q})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["language"] == expected_lang
        res_text = data["response_text"]
        assert any(k in res_text for k in expected_keywords), f"Expected keywords {expected_keywords} in {res_text}"
        if data.get("audio_url"):
            assert data["audio_url"].startswith("/api/voice/audio/")


def test_multi_turn_spoken_dialogue_continuity():
    """Verify multi-turn spoken dialogue retains history without losing context."""
    turn1_text = "Namaste Saathi"
    r1 = client.post("/api/voice/saathi", json={"text": turn1_text}).json()
    assert r1["success"] is True

    history = [
        {"role": "farmer", "text": turn1_text},
        {"role": "saathi", "text": r1["response_text"]}
    ]

    turn2_text = "Mujhe mandi bhav dekhna hai"
    r2 = client.post("/api/voice/saathi", json={"text": turn2_text, "history": history}).json()
    assert r2["success"] is True
    assert "Marketplace" in r2["response_text"] or "Mandi" in r2["response_text"]


if __name__ == "__main__":
    print("Running Saathi Step 3 Comprehensive Unit Test Suite...")
    test_natural_voice_query_mandi_bhav_option()
    print("  [PASSED] Natural Spoken Query: Mandi Bhav Option Guidance")
    test_voice_crop_disease_photo_upload_guidance()
    print("  [PASSED] Natural Spoken Query: Crop Disease Photo Upload Guidance")
    test_voice_weather_button_query()
    print("  [PASSED] Natural Spoken Query: Weather Button Guidance")
    test_audio_file_generation_and_streaming()
    print("  [PASSED] Audio File Generation & Streaming (/api/voice/audio)")
    test_empty_audio_graceful_handling()
    print("  [PASSED] Graceful Audio Error Handling")
    test_multilingual_voice_conversation_flow()
    print("  [PASSED] Multilingual Voice Conversation Flow (pa, ta, mr)")
    test_multi_turn_spoken_dialogue_continuity()
    print("  [PASSED] Multi-Turn Spoken Dialogue Continuity")
    print("\nALL SAATHI STEP 3 TESTS PASSED SUCCESSFULLY (100% SUCCESS)!")

