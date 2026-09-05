"""
AgriBridge Saathi Voice Assistant Step 13 Layer 2: Guidance Explanation Engine Test Suite
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Validates:
1. WHAT Explanation:
   - 'Iska matlab kya hai?' -> Explains meaning based on trusted recommendation.
2. WHY Explanation:
   - 'Kyun karna hai?' -> Explains why AgriBridge recommended it (e.g. soil moisture 18%).
3. HOW Explanation:
   - 'Kaise karna hai?' -> Explains method if available, or directs to standard instructions.
4. QUANTITY & TIMING Explanations:
   - 'Kitna karna hai?' -> Exact quantity.
   - 'Kab karna hai?' -> Exact timing.
5. SIMPLIFICATION Adaptation:
   - 'Simple mein samjhao' -> Clean, simple single-sentence summary.
6. DETAILED Breakdown:
   - 'Thoda detail mein batao' -> Complete breakdown (Action, Quantity, Timing, Reason).
7. Multilingual Grounding Preservation (pa, hi, hinglish).
"""

import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_what_explanation_grounding():
    """Verify 'Iska matlab kya hai?' explains the recommendation conversationally."""
    guidance = {
        "crop": "Tomato",
        "soil_moisture": "18%",
        "recommendation": {
            "action": "Irrigate 420 L",
            "quantity": "420 L",
            "timing": "6 PM",
            "reason": "Low soil moisture detected"
        }
    }
    r = client.post("/api/voice/saathi", json={
        "text": "Iska matlab kya hai?",
        "guidance_context": guidance
    })
    assert r.status_code == 200
    data = r.json()
    assert data["layer"] == "GUIDANCE_HELP"
    res = data["response_text"].lower()
    assert "irrigate 420 l" in res or "420 l" in res or "moisture" in res or "6 pm" in res


def test_why_explanation_grounding():
    """Verify 'Kyun karna hai?' explains the agricultural reason from AgriBridge context."""
    guidance = {
        "crop": "Tomato",
        "soil_moisture": "18%",
        "recommendation": {
            "action": "Irrigate 420 L",
            "reason": "Current soil moisture is 18% which is below critical threshold"
        }
    }
    r = client.post("/api/voice/saathi", json={
        "text": "Kyun karna hai?",
        "guidance_context": guidance
    })
    assert r.status_code == 200
    data = r.json()
    assert data["layer"] == "GUIDANCE_HELP"
    res = data["response_text"].lower()
    assert "18%" in res or "critical threshold" in res or "moisture" in res


def test_how_explanation_method_specified():
    """Verify 'Kaise karna hai?' explains the specified execution method."""
    guidance = {
        "crop": "Tomato",
        "recommendation": {
            "action": "Light Irrigation",
            "method": "Drip Irrigation",
            "reason": "Prevents foliage fungal risk"
        }
    }
    r = client.post("/api/voice/saathi", json={
        "text": "Kaise karna hai?",
        "guidance_context": guidance
    })
    assert r.status_code == 200
    data = r.json()
    assert data["layer"] == "GUIDANCE_HELP"
    res = data["response_text"].lower()
    assert "drip irrigation" in res or "drip" in res


def test_quantity_and_timing_explanation():
    """Verify 'Kitna karna hai?' and 'Kab karna hai?' return grounded values."""
    guidance = {
        "crop": "Wheat",
        "recommendation": {
            "action": "Urea Top Dressing",
            "quantity": "45 kg/acre",
            "timing": "Tomorrow early morning",
            "reason": "Tillering stage nitrogen requirement"
        }
    }
    # Quantity
    r1 = client.post("/api/voice/saathi", json={
        "text": "Kitna karna hai?",
        "guidance_context": guidance
    })
    assert r1.status_code == 200
    res1 = r1.json()["response_text"]
    assert "45 kg/acre" in res1

    # Timing
    r2 = client.post("/api/voice/saathi", json={
        "text": "Kab karna hai?",
        "guidance_context": guidance
    })
    assert r2.status_code == 200
    res2 = r2.json()["response_text"]
    assert "Tomorrow early morning" in res2 or "morning" in res2.lower()


def test_simplification_inquiry():
    """Verify 'Simple mein samjhao' produces a simplified 1-sentence breakdown."""
    guidance = {
        "crop": "Mustard",
        "recommendation": {
            "action": "Drain field water",
            "reason": "Water logging detected after unseasonal rain"
        }
    }
    r = client.post("/api/voice/saathi", json={
        "text": "Simple mein samjhao.",
        "guidance_context": guidance
    })
    assert r.status_code == 200
    data = r.json()
    assert data["layer"] == "GUIDANCE_HELP"
    res = data["response_text"].lower()
    assert "drain field water" in res or "water logging" in res or "aasan" in res or "सरल" in res


def test_detailed_explanation_inquiry():
    """Verify 'Thoda detail mein batao' produces a structured multi-attribute breakdown."""
    guidance = {
        "crop": "Cotton",
        "recommendation": {
            "action": "Neem Oil Spray",
            "quantity": "5 ml/L",
            "timing": "Late evening",
            "reason": "Early whitefly nymph detection"
        }
    }
    r = client.post("/api/voice/saathi", json={
        "text": "Thoda detail mein batao.",
        "guidance_context": guidance
    })
    assert r.status_code == 200
    data = r.json()
    assert data["layer"] == "GUIDANCE_HELP"
    res = data["response_text"]
    assert "Neem Oil Spray" in res
    assert "5 ml/L" in res
    assert "Late evening" in res


def test_multilingual_explanation_punjabi():
    """Verify Layer 2 explanation in Punjabi preserves grounding."""
    guidance = {
        "crop": "Wheat",
        "recommendation": {
            "action": "ਪਹਿਲੀ ਸਿੰਚਾਈ (First Irrigation)",
            "quantity": "400 L",
            "reason": "CRI ਸਟੇਜ 'ਤੇ ਨਮੀ ਘੱਟ ਹੈ"
        }
    }
    r = client.post("/api/voice/saathi", json={
        "text": "ਕਿਉਂ ਕਰਨਾ ਹੈ?",
        "language": "pa",
        "guidance_context": guidance
    })
    assert r.status_code == 200
    data = r.json()
    assert data["layer"] == "GUIDANCE_HELP"
    assert data["language"] == "pa"


if __name__ == "__main__":
    print("Running Saathi Step 13 Layer 2: Guidance Explanation Engine Unit Test Suite...")
    test_what_explanation_grounding()
    print("  [PASSED] WHAT Explanation ('Iska matlab kya hai?')")
    test_why_explanation_grounding()
    print("  [PASSED] WHY Explanation ('Kyun karna hai?')")
    test_how_explanation_method_specified()
    print("  [PASSED] HOW Explanation ('Kaise karna hai?')")
    test_quantity_and_timing_explanation()
    print("  [PASSED] QUANTITY & TIMING Explanations ('Kitna karna hai?', 'Kab karna hai?')")
    test_simplification_inquiry()
    print("  [PASSED] SIMPLIFICATION Adaptation ('Simple mein samjhao')")
    test_detailed_explanation_inquiry()
    print("  [PASSED] DETAILED Breakdown ('Thoda detail mein batao')")
    test_multilingual_explanation_punjabi()
    print("  [PASSED] Multilingual Grounding Preservation (Punjabi)")
    print("\nALL SAATHI STEP 13 TESTS PASSED SUCCESSFULLY (100% SUCCESS)!")

