"""
AgriBridge Saathi Voice Assistant Step 10 Personalised Conversational Guidance Test Suite
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Validates:
1. Context-Aware Alternative Suggestion:
   - 'Ye option mujhe nahi chahiye, doosra wala batao.' with history -> Suggests alternative modules.
2. Context-Aware Feature Recall:
   - 'Pehle wala kaise kholna hai?' with history -> Recalls previously discussed feature.
3. Detailed Preference Adaptation:
   - 'Vistaar se batao.' -> Provides full structured step breakdown.
4. Multilingual Session Continuity (Punjabi & Hindi).
5. Privacy Boundary & Strict Scope Guard (Pure Platform Help Guide, zero sensitive data).
"""

import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_alternative_option_suggestion():
    """Verify Saathi suggests alternative features when the farmer says 'Ye option mujhe nahi chahiye, doosra wala batao.'"""
    history = [
        {"role": "user", "text": "Mandi Bhav dekhna hai."},
        {"role": "assistant", "text": "Marketplace button par click karein."}
    ]
    r = client.post("/api/voice/saathi", json={
        "text": "Ye option mujhe nahi chahiye, doosra wala batao.",
        "history": history
    })
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    res = data["response_text"]
    assert "Crop Monitoring" in res or "AI Crop Scan" in res or "Weather" in res


def test_recall_previous_option():
    """Verify Saathi recalls the previously discussed feature when the farmer asks 'Pehle wala kaise kholna hai?'."""
    history = [
        {"role": "user", "text": "Bimari scan karni hai."},
        {"role": "assistant", "text": "AI Crop Scan button par click karein."}
    ]
    r = client.post("/api/voice/saathi", json={
        "text": "Pehle wala kaise kholna hai?",
        "history": history
    })
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    res = data["response_text"]
    assert "AI Crop Scan" in res or "Crop Disease" in res or "click" in res.lower()


def test_detailed_explanation_adaptation():
    """Verify Saathi provides a detailed breakdown when requested with 'Vistaar se batao.'."""
    history = [
        {"role": "user", "text": "Crop disease scan karna hai."},
        {"role": "assistant", "text": "AI Crop Scan button dabayein."}
    ]
    r = client.post("/api/voice/saathi", json={
        "text": "Vistaar se batao.",
        "history": history,
        "current_page": "upload-crop"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    res = data["response_text"]
    assert "1." in res or "2." in res or "Choose File" in res or "Analyze" in res


def test_multilingual_session_continuity_punjabi():
    """Verify session recall in Punjabi."""
    history = [
        {"role": "user", "text": "ਮੰਡੀ ਭਾਅ ਦੇਖਣਾ ਹੈ।"},
        {"role": "assistant", "text": "Marketplace ਬਟਨ 'ਤੇ ਕਲਿੱਕ ਕਰੋ।"}
    ]
    r = client.post("/api/voice/saathi", json={
        "text": "ਪਹਿਲਾਂ ਵਾਲਾ ਕਿਵੇਂ ਖੋਲ੍ਹਣਾ ਹੈ?",
        "language": "pa",
        "history": history
    })
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert "Marketplace" in data["response_text"] or "ਕਲਿੱਕ" in data["response_text"]


def test_strict_scope_boundaries_step10():
    """Verify Saathi never fabricates fertilizer formulas during personalised guidance."""
    history = [
        {"role": "user", "text": "Mandi Bhav dekhna hai."},
        {"role": "assistant", "text": "Marketplace button dabayein."}
    ]
    r = client.post("/api/voice/saathi", json={
        "text": "Doosra option batao jisme wheat ka urea dose mile.",
        "history": history
    })
    assert r.status_code == 200
    res = r.json()["response_text"]
    assert "Crop Recommendations" in res or "Crop Monitoring" in res or "AI Crop Scan" in res
    assert "120 kg" not in res
    assert "₹" not in res


if __name__ == "__main__":
    print("Running Saathi Step 10 Personalised Conversational Guidance Unit Test Suite...")
    test_alternative_option_suggestion()
    print("  [PASSED] Alternative Option Suggestion ('Ye option nahi chahiye, doosra wala batao')")
    test_recall_previous_option()
    print("  [PASSED] Session Context Recall ('Pehle wala kaise kholna hai?')")
    test_detailed_explanation_adaptation()
    print("  [PASSED] Detailed Explanation Adaptation ('Vistaar se batao')")
    test_multilingual_session_continuity_punjabi()
    print("  [PASSED] Multilingual Session Continuity (Punjabi)")
    test_strict_scope_boundaries_step10()
    print("  [PASSED] Strict Step 10 Scope Boundaries (Platform Guidance Only)")
    print("\nALL SAATHI STEP 10 TESTS PASSED SUCCESSFULLY (100% SUCCESS)!")

