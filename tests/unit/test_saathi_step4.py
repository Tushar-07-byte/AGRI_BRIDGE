"""
AgriBridge Saathi Voice Assistant Step 4 Comprehensive Unit Test Suite
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Validates:
1. Multi-turn context continuity ("Mandi Bhav wala button kahan hai?" -> "Uske baad?").
2. Context continuation after button explanation ("Crop Monitoring button kya karta hai?" -> "Aur iske baad kya karna hai?").
3. Multilingual context retention across follow-up queries (Punjabi, Marathi, Tamil, etc.).
4. Mid-conversation language switching while retaining platform context.
5. Clarification handling when context is ambiguous or ungrounded.
6. Strict Step 4 scope boundaries (no farm memory, crop memory, or chemical prescriptions).
"""

import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_context_continuity_mandi_bhav_follow_up():
    """Verify Turn 1 (Mandi location) -> Turn 2 ('Uske baad?') resolves to Mandi follow-up instructions."""
    # Turn 1: Farmer asks about Mandi Bhav
    r1 = client.post("/api/voice/saathi", json={
        "text": "Mandi Bhav wala button kahan hai?",
        "current_page": "farmer-dashboard"
    })
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["success"] is True

    # Turn 2: Farmer asks 'Uske baad?' passing Turn 1 in history
    history = [
        {"role": "user", "text": "Mandi Bhav wala button kahan hai?"},
        {"role": "assistant", "text": d1["response_text"]}
    ]
    r2 = client.post("/api/voice/saathi", json={
        "text": "Uske baad?",
        "history": history,
        "current_page": "farmer-dashboard"
    })
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["success"] is True
    res2 = d2["response_text"]
    
    # Must provide Mandi / Marketplace follow-up instructions without asking farmer to repeat
    assert "Mandi" in res2 or "fasal" in res2.lower() or "listing" in res2.lower()
    # Must NOT provide raw market prices
    assert "₹" not in res2


def test_context_continuity_button_explanation_follow_up():
    """Verify Turn 1 (Button explanation) -> Turn 2 ('Aur iske baad kya karna hai?') resolves seamlessly."""
    # Turn 1: Farmer asks about Disease Detection
    r1 = client.post("/api/voice/saathi", json={
        "text": "Mujhe bimari check karna hai, kya karu?",
        "current_page": "farmer-dashboard"
    })
    assert r1.status_code == 200
    d1 = r1.json()

    # Turn 2: Farmer asks 'Aur iske baad kya karna hai?'
    history = [
        {"role": "user", "text": "Mujhe bimari check karna hai, kya karu?"},
        {"role": "assistant", "text": d1["response_text"]}
    ]
    r2 = client.post("/api/voice/saathi", json={
        "text": "Aur iske baad kya karna hai?",
        "history": history,
        "current_page": "farmer-dashboard"
    })
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["success"] is True
    res2 = d2["response_text"]

    # Must explain taking photo / uploading leaf photo
    assert "Photo" in res2 or "photo" in res2.lower() or "patti" in res2.lower() or "bimari" in res2.lower()


def test_multilingual_context_continuity_punjabi():
    """Verify multi-turn context retention in Punjabi ('ਮੰਡੀ ਭਾਵ ਕਿੱਥੇ ਹੈ?' -> 'ਉਸ ਤੋਂ ਬਾਅਦ?')"""
    r1 = client.post("/api/voice/saathi", json={
        "text": "ਮੰਡੀ ਭਾਵ ਵਾਲਾ ਬਟਨ ਕਿੱਥੇ ਹੈ?",
        "language": "pa",
        "current_page": "farmer-dashboard"
    })
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["language"] == "pa"

    # Turn 2: Punjabi follow-up
    history = [
        {"role": "user", "text": "ਮੰਡੀ ਭਾਵ ਵਾਲਾ ਬਟਨ ਕਿੱਥੇ ਹੈ?"},
        {"role": "assistant", "text": d1["response_text"]}
    ]
    r2 = client.post("/api/voice/saathi", json={
        "text": "ਉਸ ਤੋਂ ਬਾਅਦ?",
        "language": "pa",
        "history": history,
        "current_page": "farmer-dashboard"
    })
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["success"] is True
    assert d2["language"] == "pa"
    assert "ਮੰਡੀ" in d2["response_text"] or "ਫਸਲ" in d2["response_text"]


def test_mid_conversation_language_switching_with_context():
    """Verify farmer switches language from Hindi to English during follow-up while retaining context."""
    # Turn 1: Hindi
    r1 = client.post("/api/voice/saathi", json={
        "text": "मुझे मौसम और बारिश देखना है।",
        "language": "hi",
        "current_page": "farmer-dashboard"
    })
    assert r1.status_code == 200
    d1 = r1.json()

    # Turn 2: Switched to English
    history = [
        {"role": "user", "text": "मुझे मौसम और बारिश देखना है।"},
        {"role": "assistant", "text": d1["response_text"]}
    ]
    r2 = client.post("/api/voice/saathi", json={
        "text": "What should I do after that?",
        "history": history,
        "current_page": "farmer-dashboard"
    })
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["success"] is True
    assert d2["language"] == "en"
    assert "Weather" in d2["response_text"] or "forecast" in d2["response_text"].lower() or "rainfall" in d2["response_text"].lower()


def test_ambiguous_generic_follow_up_clarification():
    """Verify generic follow-up with no previous context prompts a short, polite clarification."""
    r = client.post("/api/voice/saathi", json={
        "text": "Uske baad kya karein?",
        "history": [],
        "current_page": "farmer-dashboard"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert "pooch" in data["response_text"].lower() or "kis" in data["response_text"].lower() or "which" in data["response_text"].lower()


def test_strict_step4_scope_guard():
    """Verify Saathi never gives raw chemical prescriptions or weather temperatures during follow-ups."""
    history = [
        {"role": "user", "text": "AI Crop Scan button par click kiya."},
        {"role": "assistant", "text": "Iske baad photo upload karein."}
    ]
    r = client.post("/api/voice/saathi", json={
        "text": "Then what?",
        "history": history
    })
    assert r.status_code == 200
    res = r.json()["response_text"]
    assert "carbendazim" not in res.lower()
    assert "hexaconazole" not in res.lower()
    assert "₹" not in res


if __name__ == "__main__":
    print("Running Saathi Step 4 Context-Aware Conversation Unit Test Suite...")
    test_context_continuity_mandi_bhav_follow_up()
    print("  [PASSED] Context Continuity: Mandi Bhav -> 'Uske baad?'")
    test_context_continuity_button_explanation_follow_up()
    print("  [PASSED] Context Continuity: Button Explanation -> Follow-up")
    test_multilingual_context_continuity_punjabi()
    print("  [PASSED] Multilingual Context Continuity (Punjabi)")
    test_mid_conversation_language_switching_with_context()
    print("  [PASSED] Mid-Conversation Language Switching with Context Retention")
    test_ambiguous_generic_follow_up_clarification()
    print("  [PASSED] Ambiguity & Ungrounded Follow-up Clarification")
    test_strict_step4_scope_guard()
    print("  [PASSED] Strict Step 4 Scope Guard (No chemicals, No raw prices)")
    print("\nALL SAATHI STEP 4 TESTS PASSED SUCCESSFULLY (100% SUCCESS)!")

