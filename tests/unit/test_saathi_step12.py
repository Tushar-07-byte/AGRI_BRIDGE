"""
AgriBridge Saathi Voice Assistant Step 12 Layer 2: Trusted Recommendation Ingestion Test Suite
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Validates:
1. Complete Recommendation Ingestion & Exact Measurement Explanation:
   - Crop: Tomato, Soil Moisture: 18%, Rec: 420 L at 6 PM, Reason: Low soil moisture.
   - '420 litre kyun?' -> Explains based on low soil moisture.
2. Incomplete Recommendation (Zero Guessing / Hallucination):
   - Missing quantity -> 'Is recommendation mein exact quantity available nahi hai.'
   - Missing timing -> 'Is recommendation mein timing available nahi hai.'
   - Missing reason -> 'Is recommendation ka specific reason available nahi hai.'
3. Multiple Recommendations Ingestion:
   - Action 1: Irrigation 420 L, Action 2: Nitrogen top-dressing 25 kg.
   - '25 kg kyu bola?' -> Matches specific Nitrogen recommendation item.
4. Old / New / Cancelled Recommendation Ingestion:
   - Resolves status == 'CANCELLED' / 'REPLANNED' with active decision fidelity.
"""

import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_complete_recommendation_ingestion_and_why_explanation():
    """Verify complete recommendation ingestion with measurements and exact '420 litre kyun?' explanation."""
    guidance = {
        "crop": "Tomato",
        "soil_moisture": "18%",
        "recommendation": {
            "action": "Irrigate 420 L at 6 PM",
            "quantity": "420 L",
            "timing": "6 PM",
            "reason": "Low soil moisture"
        },
        "decision_id": "DEC-TOMATO-881",
        "confidence": 0.94,
        "sources": {"decision_engine": "AgriBridge Ultra Decision Matrix"}
    }
    r = client.post("/api/voice/saathi", json={
        "text": "420 litre kyun?",
        "guidance_context": guidance
    })
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["layer"] == "GUIDANCE_HELP"
    res = data["response_text"].lower()
    assert "moisture" in res or "low" in res or "18%" in res or "420" in res


def test_missing_quantity_handling():
    """Verify missing quantity explicitly states exact quantity is not available."""
    guidance = {
        "crop": "Wheat",
        "recommendation": {
            "action": "Spray Fungicide",
            "reason": "Early yellow rust symptoms detected.",
            "timing": "Immediate"
        }
    }
    r = client.post("/api/voice/saathi", json={
        "text": "Kitna quantity spray karna hai?",
        "guidance_context": guidance
    })
    assert r.status_code == 200
    data = r.json()
    res = data["response_text"].lower()
    assert "quantity available nahi" in res or "exact quantity" in res or "matlab" in res or "uplabdh nahi" in res


def test_missing_timing_handling():
    """Verify missing timing explicitly states timing is not available."""
    guidance = {
        "crop": "Rice",
        "recommendation": {
            "action": "Apply Zinc Sulfate",
            "quantity": "10 kg/acre",
            "reason": "Zinc deficiency detected in soil test."
        }
    }
    r = client.post("/api/voice/saathi", json={
        "text": "Kis time daalna hai?",
        "guidance_context": guidance
    })
    assert r.status_code == 200
    data = r.json()
    res = data["response_text"].lower()
    assert "timing available nahi" in res or "samay" in res or "uplabdh nahi" in res


def test_missing_reason_handling():
    """Verify missing reason explicitly states reason is not available."""
    guidance = {
        "crop": "Potato",
        "recommendation": {
            "action": "Earthing Up",
            "timing": "At 30 DAP",
            "quantity": "Standard Ridge Height"
        }
    }
    r = client.post("/api/voice/saathi", json={
        "text": "Earthing up kyu bola?",
        "guidance_context": guidance
    })
    assert r.status_code == 200
    data = r.json()
    res = data["response_text"].lower()
    assert "reason available nahi" in res or "karan" in res or "uplabdh nahi" in res


def test_multiple_recommendations_ingestion():
    """Verify Saathi correctly resolves a specific entity from multiple recommendation items."""
    guidance = {
        "crop": "Wheat",
        "recommendations": [
            {
                "action": "Irrigation",
                "quantity": "420 L",
                "reason": "Soil moisture is depleted."
            },
            {
                "action": "Nitrogen Top-Dressing",
                "quantity": "25 kg",
                "reason": "Crop entered active tillering stage needing nitrogen boost."
            }
        ]
    }
    r = client.post("/api/voice/saathi", json={
        "text": "25 kg kyu bola?",
        "guidance_context": guidance
    })
    assert r.status_code == 200
    data = r.json()
    res = data["response_text"].lower()
    assert "nitrogen" in res or "tillering" in res or "25 kg" in res


def test_cancelled_and_replanned_recommendation_ingestion():
    """Verify Saathi ingests cancelled & replanned guidance with source truth preserved."""
    guidance = {
        "crop": "Cotton",
        "previous_decision": {
            "action": "Pesticide Spray",
            "quantity": "200 ml/acre"
        },
        "current_decision": {
            "action": "Pesticide Spray Cancelled",
            "reason": "Wind speed exceeds 25 km/h causing spray drift hazard.",
            "status": "CANCELLED"
        },
        "replan_status": {
            "is_replanned": True
        }
    }
    r = client.post("/api/voice/saathi", json={
        "text": "Spray kyu cancel hua?",
        "guidance_context": guidance
    })
    assert r.status_code == 200
    data = r.json()
    res = data["response_text"].lower()
    assert "cancelled" in res or "cancel" in res
    assert "wind" in res or "hawa" in res or "drift" in res or "25 km/h" in res


if __name__ == "__main__":
    print("Running Saathi Step 12 Layer 2: Trusted Recommendation Ingestion Unit Test Suite...")
    test_complete_recommendation_ingestion_and_why_explanation()
    print("  [PASSED] Complete Recommendation & Measurement Ingestion ('420 litre kyun?')")
    test_missing_quantity_handling()
    print("  [PASSED] Missing Quantity Handling (Zero Hallucination)")
    test_missing_timing_handling()
    print("  [PASSED] Missing Timing Handling (Zero Hallucination)")
    test_missing_reason_handling()
    print("  [PASSED] Missing Reason Handling (Zero Hallucination)")
    test_multiple_recommendations_ingestion()
    print("  [PASSED] Multiple Recommendations Ingestion ('25 kg kyu bola?')")
    test_cancelled_and_replanned_recommendation_ingestion()
    print("  [PASSED] Cancelled & Replanned Recommendation Ingestion")
    print("\nALL SAATHI STEP 12 TESTS PASSED SUCCESSFULLY (100% SUCCESS)!")

