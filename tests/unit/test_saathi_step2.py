"""
AgriBridge Saathi Voice Assistant Step 2 Comprehensive Unit Test Suite
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Validates:
1. Platform Understanding & Navigation Guidance (Mandi Bhav, Disease Detection, Weather, Monitoring, Recommendations).
2. Button Function Explanation ("Ye button kya karta hai?", "What does this button do?").
3. Context-Aware Screen Overview ("Upar wala button kaunsa hai?").
4. Strict Step 2 Scope (Guides the farmer to features; NEVER provides internal prices, diagnoses, or forecasts).
5. Multilingual and mixed-language execution with recognizable button names across Indian languages.
"""

import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from fastapi.testclient import TestClient

from app.main import app
from app.services.saathi_service import detect_language, detect_platform_navigation_intent

client = TestClient(app)


def test_platform_navigation_guidance_mandi():
    """Verify Saathi guides farmer to Marketplace / Mandi Bhav button without giving price numbers."""
    queries = [
        ("Mujhe mandi bhav dekhna hai", "hinglish"),
        ("मुझे मंडी भाव देखना है", "hi"),
        ("ਮੈਨੂੰ ਮੰਡੀ ਦੇ ਭਾਅ ਦੇਖਣੇ ਹਨ", "pa"),
        ("मला बाजारभाव पाहायचा आहे", "mr"),
        ("I want to see mandi market prices", "en")
    ]

    for q, expected_lang in queries:
        resp = client.post("/api/voice/saathi", json={"text": q})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["language"] == expected_lang
        res_text = data["response_text"]
        # Must guide to Marketplace button
        assert "Marketplace" in res_text or "मंडी" in res_text or "ਮੰਡੀ" in res_text or "market" in res_text.lower()
        # Must NOT provide price figures or quintal rates
        assert "₹" not in res_text
        assert "quintal" not in res_text.lower()


def test_platform_navigation_guidance_disease():
    """Verify Saathi guides farmer to AI Crop Scan / Disease Detection button without chemical prescription."""
    queries = [
        ("Mujhe disease check karna hai, kya karu?", "hinglish"),
        ("फसल में बीमारी की जांच करनी है", "hi"),
        ("How do I check for crop disease?", "en"),
        ("ਫ਼ਸਲ ਦੀ ਬਿਮਾਰੀ ਚੈੱਕ ਕਰਨੀ ਹੈ", "pa")
    ]

    for q, expected_lang in queries:
        resp = client.post("/api/voice/saathi", json={"text": q})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["language"] == expected_lang
        res_text = data["response_text"]
        # Must guide to Crop Disease Detection / AI Crop Scan button
        assert "Crop" in res_text or "Scan" in res_text or "Disease" in res_text or "बीमारी" in res_text or "ਬਿਮਾਰੀ" in res_text
        # Must NOT give chemical prescriptions
        assert "propiconazole" not in res_text.lower()
        assert "tebuconazole" not in res_text.lower()


def test_platform_navigation_guidance_weather():
    """Verify Saathi guides farmer to Weather button without forecast metrics."""
    resp = client.post("/api/voice/saathi", json={"text": "Mausam aur barish dekhna hai"}).json()
    assert resp["success"] is True
    assert resp["language"] == "hinglish"
    assert "Weather" in resp["response_text"] or "Mausam" in resp["response_text"]
    assert "°C" not in resp["response_text"]


def test_button_explanation_ye_button_kya_karta_hai():
    """Verify Saathi explains button functionality in farmer's language."""
    # 1. With explicit button name in query
    r1 = client.post("/api/voice/saathi", json={"text": "AI Crop Scan button kya karta hai?"}).json()
    assert r1["success"] is True
    assert "Crop" in r1["response_text"] or "Scan" in r1["response_text"] or "photo" in r1["response_text"].lower()

    # 2. With focused_button passed in UI context
    r2 = client.post("/api/voice/saathi", json={
        "text": "Ye button kya karta hai?",
        "focused_button": "Marketplace",
        "current_page": "farmer-dashboard"
    }).json()
    assert r2["success"] is True
    assert "Marketplace" in r2["response_text"] or "mandi" in r2["response_text"].lower() or "button" in r2["response_text"].lower()


def test_context_aware_top_buttons_inquiry():
    """Verify Saathi explains top navbar buttons when farmer asks 'Upar wala button kaunsa hai?'."""
    queries = [
        "Upar wala button kaunsa hai?",
        "ऊपर वाला बटन कौन सा है?",
        "What are the buttons at the top?"
    ]

    for q in queries:
        resp = client.post("/api/voice/saathi", json={
            "text": q,
            "current_page": "farmer-dashboard",
            "available_buttons": ["Dashboard", "Crop Monitoring", "AI Crop Scan", "Marketplace", "Weather", "Voice AI", "Command Center"]
        }).json()
        assert resp["success"] is True
        res_text = resp["response_text"]
        # Must list or reference top buttons
        assert any(btn in res_text for btn in ["Dashboard", "Crop Monitoring", "AI Crop Scan", "Marketplace", "Weather", "Voice AI", "Command Center"])


def test_multilingual_button_name_preservation():
    """Verify button names remain recognizable even when explanation is translated."""
    # Punjabi
    r_pa = client.post("/api/voice/saathi", json={"text": "ਮੈਂ ਮੰਡੀ ਦੇ ਭਾਅ ਦੇਖਣਾ ਚਾਹੁੰਦਾ ਹਾਂ"}).json()
    assert r_pa["language"] == "pa"
    assert "Marketplace" in r_pa["response_text"] or "ਮੰਡੀ" in r_pa["response_text"]

    # Marathi
    r_mr = client.post("/api/voice/saathi", json={"text": "मला पिकावरील रोग तपासायचा आहे"}).json()
    assert r_mr["language"] == "mr"
    assert "Crop Scan" in r_mr["response_text"] or "AI" in r_mr["response_text"] or "रोगाची" in r_mr["response_text"]


def test_backward_compatibility_with_ask_text_endpoint():
    """Verify /api/voice/ask-text endpoint with mode=saathi executes Step 2 platform navigation."""
    resp = client.post("/api/voice/ask-text", json={
        "text": "Mujhe mandi bhav dekhna hai",
        "mode": "saathi",
        "current_page": "farmer-dashboard"
    }).json()
    assert resp["success"] is True
    assert resp["language"] == "hinglish"
    assert "Marketplace" in resp["response_text"] or "Mandi" in resp["response_text"]


if __name__ == "__main__":
    print("Running Saathi Step 2 Comprehensive Unit Test Suite...")
    test_platform_navigation_guidance_mandi()
    print("  [PASSED] Platform Navigation: Mandi / Marketplace Guidance")
    test_platform_navigation_guidance_disease()
    print("  [PASSED] Platform Navigation: Crop Disease Detection Guidance")
    test_platform_navigation_guidance_weather()
    print("  [PASSED] Platform Navigation: Weather & Rain Guidance")
    test_button_explanation_ye_button_kya_karta_hai()
    print("  [PASSED] Button Explanation: 'Ye button kya karta hai?'")
    test_context_aware_top_buttons_inquiry()
    print("  [PASSED] Context-Aware Screen Overview: 'Upar wala button kaunsa hai?'")
    test_multilingual_button_name_preservation()
    print("  [PASSED] Multilingual Button Name Preservation")
    test_backward_compatibility_with_ask_text_endpoint()
    print("  [PASSED] Backward Compatibility via /api/voice/ask-text mode=saathi")
    print("\nALL SAATHI STEP 2 TESTS PASSED SUCCESSFULLY (100% SUCCESS)!")

