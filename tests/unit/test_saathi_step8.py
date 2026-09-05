"""
AgriBridge Saathi Voice Assistant Step 8 Human-Like Conversation & Smart Recovery Test Suite
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Validates:
1. Natural Flow:
   - 'Mandi Bhav ka option kahan hai?' -> Guides to Marketplace button
   - 'Mil gaya.' -> 'Ji, ab uspar click karein.'
   - 'Kar diya.' -> Advances to next step
2. Conversational Interruptions:
   - 'Ruko, pehle ye batao...' -> Handles interruption calmly and listens.
3. Conversational Acknowledgments:
   - 'Accha, samajh gaya.' -> Warm closing acknowledgment.
4. Smart Navigation Recovery:
   - 'Galti se doosra page khul gaya.' -> Guides back to previous workflow.
   - 'Mujhe wapas jaana hai.' -> Guides back to Dashboard.
5. Strict Scope Guard:
   - 'Aaj mandi mein bhav kya hai?' -> Redirects to Marketplace without outputting prices.
"""

import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_natural_flow_mandi_mil_gaya_progression():
    """Verify natural conversational sequence: Location -> 'Mil gaya.' -> 'Ji, ab uspar click karein.' -> 'Kar diya.'"""
    # Turn 1
    r1 = client.post("/api/voice/saathi", json={"text": "Mandi Bhav ka option kahan hai?"})
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["success"] is True
    assert "Marketplace" in d1["response_text"]

    # Turn 2: 'Mil gaya.'
    history = [
        {"role": "user", "text": "Mandi Bhav ka option kahan hai?"},
        {"role": "assistant", "text": d1["response_text"]}
    ]
    r2 = client.post("/api/voice/saathi", json={"text": "Mil gaya.", "history": history})
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["success"] is True
    assert "click" in d2["response_text"].lower() or "uspar" in d2["response_text"].lower()

    # Turn 3: 'Kar diya.'
    history.extend([
        {"role": "user", "text": "Mil gaya."},
        {"role": "assistant", "text": d2["response_text"]}
    ])
    r3 = client.post("/api/voice/saathi", json={"text": "Kar diya.", "history": history, "current_page": "crop-listings"})
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3["success"] is True
    assert "mandi" in d3["response_text"].lower() or "listing" in d3["response_text"].lower() or "rate" in d3["response_text"].lower()


def test_interruption_handling():
    """Verify Saathi handles conversational side interruptions like 'Ruko, pehle ye batao...'."""
    r = client.post("/api/voice/saathi", json={"text": "Ruko, pehle ye batao..."})
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    res = data["response_text"].lower()
    assert "boliye" in res or "sun raha" in res or "listening" in res


def test_warm_acknowledgment():
    """Verify Saathi responds warmly to 'Accha, samajh gaya.'."""
    r = client.post("/api/voice/saathi", json={"text": "Accha, samajh gaya."})
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    res = data["response_text"].lower()
    assert "badhiya" in res or "madad" in res or "wonderful" in res


def test_smart_recovery_wrong_page():
    """Verify Saathi recovers when farmer says 'Galti se doosra page khul gaya.'."""
    history = [
        {"role": "user", "text": "Mandi Bhav dekhna hai."},
        {"role": "assistant", "text": "Marketplace button par click karein."}
    ]
    r = client.post("/api/voice/saathi", json={
        "text": "Galti se doosra page khul gaya.",
        "history": history
    })
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert "Marketplace" in data["response_text"] or "click" in data["response_text"].lower()


def test_smart_recovery_wapas_jaana_hai():
    """Verify Saathi guides farmer to Dashboard when they say 'Mujhe wapas jaana hai.'."""
    r = client.post("/api/voice/saathi", json={"text": "Mujhe wapas jaana hai."})
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    res = data["response_text"].lower()
    assert "dashboard" in res or "wapas" in res or "click" in res


def test_strict_scope_price_inquiry_redirection():
    """Verify Saathi never gives raw prices when farmer asks 'Aaj mandi mein bhav kya hai?'."""
    r = client.post("/api/voice/saathi", json={"text": "Aaj mandi mein bhav kya hai?"})
    assert r.status_code == 200
    res = r.json()["response_text"]
    assert "Marketplace" in res or "Crop Recommendations" in res
    assert "₹" not in res
    assert "2500" not in res


if __name__ == "__main__":
    print("Running Saathi Step 8 Human-Like Conversation & Smart Recovery Unit Test Suite...")
    test_natural_flow_mandi_mil_gaya_progression()
    print("  [PASSED] Natural Dialogue Sequence (Mandi -> 'Mil gaya.' -> 'Kar diya.')")
    test_interruption_handling()
    print("  [PASSED] Conversational Interruption Handling ('Ruko, pehle ye batao...')")
    test_warm_acknowledgment()
    print("  [PASSED] Warm Conversational Acknowledgment ('Accha, samajh gaya.')")
    test_smart_recovery_wrong_page()
    print("  [PASSED] Smart Recovery: 'Galti se doosra page khul gaya.'")
    test_smart_recovery_wapas_jaana_hai()
    print("  [PASSED] Smart Recovery: 'Mujhe wapas jaana hai.'")
    test_strict_scope_price_inquiry_redirection()
    print("  [PASSED] Strict Scope Redirection ('Aaj mandi mein bhav kya hai?')")
    print("\nALL SAATHI STEP 8 TESTS PASSED SUCCESSFULLY (100% SUCCESS)!")

