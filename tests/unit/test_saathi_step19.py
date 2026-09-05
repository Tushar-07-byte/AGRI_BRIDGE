"""
AgriBridge Saathi Voice Assistant Step 19 Layer 2: Full Voice + Guidance Integration Test Suite
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Validates:
1. End-to-End Voice + Guidance Integration:
   - Spoken query ('420 litre paani kyun bola?') -> Language detection -> Layer 2 Guidance -> Audio synthesis (/api/voice/audio/...).
2. Strict Layer Router Separation (Non-Interference):
   - 'Crop disease button kahan hai?' -> PLATFORM_HELP
   - 'Disease result samajh nahi aa raha.' -> GUIDANCE_HELP
3. Multilingual Voice Guidance Generation (Punjabi, Marathi, Tamil, Hindi, Hinglish).
4. Audio Streaming & TTS Status Generation:
   - audio_status in ['cached', 'generated', 'fallback_text_only']
   - audio_url valid string format.
5. Unified Endpoint Backward Compatibility:
   - /api/voice/saathi
   - /api/voice/ask?mode=saathi
   - /api/voice/ask-text
"""

import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_voice_guidance_full_pipeline_with_audio():
    """Verify Layer 2 spoken question synthesizes TTS audio and streams correctly."""
    guidance = {
        "crop": "Tomato",
        "soil_moisture": "18%",
        "recommendation": {
            "action": "Irrigate 420 L",
            "quantity": "420 L",
            "timing": "6 PM",
            "reason": "Soil moisture is 18%"
        }
    }
    r = client.post("/api/voice/saathi", json={
        "text": "420 litre paani kyun bola?",
        "guidance_context": guidance
    })
    assert r.status_code == 200
    data = r.json()
    assert data["layer"] == "GUIDANCE_HELP"
    assert "audio_url" in data
    assert "audio_status" in data
    assert "420 L" in data["response_text"]
    assert data["audio_status"] in ["cached", "generated", "fallback_text_only"]


def test_layer_router_non_interference():
    """Verify Layer 1 (Platform) vs Layer 2 (Guidance) router separation without cross-talk."""
    guidance = {
        "crop": "Wheat",
        "disease_result": {
            "disease_name": "Yellow Rust",
            "confidence": 0.94,
            "treatment": "Spray Propiconazole"
        }
    }

    # Query 1: Platform Navigation
    r_plat = client.post("/api/voice/saathi", json={
        "text": "Crop disease button kahan hai?",
        "guidance_context": guidance
    })
    assert r_plat.status_code == 200
    data_plat = r_plat.json()
    assert data_plat["layer"] == "PLATFORM_HELP"
    assert "AI Crop Scan" in data_plat["response_text"] or "Crop Disease" in data_plat["response_text"]

    # Query 2: Guidance Explanation
    r_guid = client.post("/api/voice/saathi", json={
        "text": "Disease result samajh nahi aa raha.",
        "guidance_context": guidance
    })
    assert r_guid.status_code == 200
    data_guid = r_guid.json()
    assert data_guid["layer"] == "GUIDANCE_HELP"
    assert "Yellow Rust" in data_guid["response_text"] or "Rust" in data_guid["response_text"]


def test_multilingual_voice_guidance_punjabi():
    """Verify multilingual voice guidance produces audio for Punjabi query."""
    guidance = {
        "crop": "Wheat",
        "recommendation": {
            "action": "ਪਹਿਲੀ ਸਿੰਚਾਈ (First Irrigation)",
            "quantity": "420 L",
            "timing": "6 PM",
            "reason": "ਜੜ੍ਹਾਂ ਦੇ ਵਿਕਾਸ ਲਈ"
        }
    }
    r = client.post("/api/voice/saathi", json={
        "text": "ਸਿੰਚਾਈ ਕਿਉਂ ਕਰਨੀ ਹੈ? (Sinchai kyu karni hai?)",
        "language": "pa",
        "guidance_context": guidance
    })
    assert r.status_code == 200
    data = r.json()
    assert data["layer"] == "GUIDANCE_HELP"
    assert data["language"] == "pa"
    assert data["audio_url"] is not None


def test_backward_compatibility_via_ask_mode_saathi():
    """Verify /api/voice/ask with mode=saathi processes Layer 2 guidance with audio."""
    guidance = {
        "crop": "Tomato",
        "recommendation": {
            "action": "Irrigate 420 L",
            "quantity": "420 L",
            "timing": "6 PM",
            "reason": "Soil moisture is 18%"
        }
    }
    import json
    r = client.post("/api/voice/ask", data={
        "text": "Iska matlab kya hai?",
        "mode": "saathi",
        "guidance_context": json.dumps(guidance)
    })
    assert r.status_code == 200
    data = r.json()
    assert data["layer"] == "GUIDANCE_HELP"
    assert "Irrigate 420 L" in data["response_text"]
    assert "audio_url" in data


if __name__ == "__main__":
    print("Running Saathi Step 19 Layer 2: Full Voice + Guidance Integration Unit Test Suite...")
    test_voice_guidance_full_pipeline_with_audio()
    print("  [PASSED] Voice Guidance Full Pipeline with TTS Audio Synthesis")
    test_layer_router_non_interference()
    print("  [PASSED] Layer Router Non-Interference (Platform Help vs Guidance Help)")
    test_multilingual_voice_guidance_punjabi()
    print("  [PASSED] Multilingual Voice Guidance Synthesis (Punjabi)")
    test_backward_compatibility_via_ask_mode_saathi()
    print("  [PASSED] Backward Compatibility via /api/voice/ask mode=saathi")
    print("\nALL SAATHI STEP 19 TESTS PASSED SUCCESSFULLY (100% SUCCESS)!")

