"""
AgriBridge Saathi Voice Assistant Step 7 Final Integration & Reliability Test Suite
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Validates:
1. Patient Simplification for Confusion:
   - 'Mujhe samajh nahi aa raha.' on 'upload-crop' -> Explains the current action simply.
   - 'Mujhe samajh nahi aa raha.' without context -> Explains options patiently.
2. Out-of-Scope Redirection:
   - 'Kaun sa khad daalna chahiye?' -> Redirects to 'Crop Recommendations' / 'AI Crop Scan' without fabricating chemical doses.
3. Resilient Error & Empty Input Handling:
   - Blank queries / short acknowledgments handled gracefully.
4. Multilingual Production Readiness (Hindi, Hinglish, Punjabi, Marathi, Tamil, Bengali).
5. Strict Scope Guard (Pure Platform Help Guide).
"""

import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_confusion_simplification_on_upload_crop():
    """Verify Saathi simplifies instructions when farmer says 'Mujhe samajh nahi aa raha' on upload-crop."""
    r = client.post("/api/voice/saathi", json={
        "text": "Mujhe samajh nahi aa raha.",
        "current_page": "upload-crop"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    res = data["response_text"].lower()
    assert "upload photo" in res or "patti" in res or "photo" in res or "aasan" in res


def test_confusion_simplification_without_context():
    """Verify Saathi patiently guides the farmer when they say 'Mujhe samajh nahi aa raha' without context."""
    r = client.post("/api/voice/saathi", json={
        "text": "Mujhe samajh nahi aa raha."
    })
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    res = data["response_text"].lower()
    assert "madad" in res or "kaam" in res or "guide" in res or "bataiye" in res


def test_out_of_scope_redirection():
    """Verify Saathi redirects out-of-scope agricultural questions to platform tools instead of fabricating chemical doses."""
    r = client.post("/api/voice/saathi", json={
        "text": "Fasal mein kaun sa khad kitna daalna chahiye?"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    res = data["response_text"]
    assert "Crop Recommendations" in res or "AI Crop Scan" in res
    assert "urea" not in res.lower()
    assert "kg/ha" not in res.lower()


def test_resilient_short_filler_acknowledgments():
    """Verify Saathi acknowledges short speech fillers gracefully."""
    for filler in ["Haan ji", "Suno", "Hello", "Ji bolo"]:
        r = client.post("/api/voice/saathi", json={"text": filler})
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert len(data["response_text"]) > 0


def test_multilingual_production_readiness():
    """Verify end-to-end reliability across multiple Indian languages."""
    queries = [
        ("ਮੈਨੂੰ ਮੰਡੀ ਭਾਅ ਦੇਖਣਾ ਹੈ।", "pa", "ਮੰਡੀ"),
        ("मला पिकाचा रोग तपासायचा आहे.", "mr", "रोग"),
        ("எனக்கு சந்தை விலை பார்க்க வேண்டும்.", "ta", "Marketplace"),
        ("আমি ফসলের রোগ পরীক্ষা করতে চাই।", "bn", "Crop Scan")
    ]
    for q, expected_lang, keyword in queries:
        r = client.post("/api/voice/saathi", json={"text": q, "language": expected_lang})
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert keyword in data["response_text"] or expected_lang == data["language"]


def test_strict_scope_boundaries_production():
    """Verify Saathi never produces raw market prices or pesticide prescriptions in production mode."""
    r = client.post("/api/voice/saathi", json={
        "text": "Wheat ka mandi bhav kya chal raha hai?"
    })
    assert r.status_code == 200
    res = r.json()["response_text"]
    assert "Marketplace" in res
    assert "₹" not in res
    assert "2275" not in res


if __name__ == "__main__":
    print("Running Saathi Step 7 Final Integration & Reliability Unit Test Suite...")
    test_confusion_simplification_on_upload_crop()
    print("  [PASSED] Patient Simplification on 'upload-crop' ('Mujhe samajh nahi aa raha')")
    test_confusion_simplification_without_context()
    print("  [PASSED] Patient Simplification Without Context")
    test_out_of_scope_redirection()
    print("  [PASSED] Out-of-Scope Redirection (Crop Recommendations / AI Crop Scan)")
    test_resilient_short_filler_acknowledgments()
    print("  [PASSED] Resilient Short Filler Acknowledgments ('Haan ji', 'Suno')")
    test_multilingual_production_readiness()
    print("  [PASSED] Multilingual Production Readiness (pa, mr, ta, bn)")
    test_strict_scope_boundaries_production()
    print("  [PASSED] Strict Production Scope Boundaries (Platform Guidance Only)")
    print("\nALL SAATHI STEP 7 TESTS PASSED SUCCESSFULLY (100% SUCCESS)!")

