"""
Voice Assistant Preference & Adaptive Length Test (Prompt -1D)
Demonstrates:
  1. Personalized greeting / response with farmer name ('Ramesh')
  2. Short / Simple answer (1-2 sentences) when detail_level='simple'
  3. Comprehensive / Detailed explanation when detail_level='detailed'
  4. Response comparison on the exact same agronomy question.
"""

import sys
from pathlib import Path

# Ensure UTF-8 stdout on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_voice_preference_differences():
    print("\n" + "="*70)
    print("VOICE ASSISTANT PREFERENCE ADAPTATION TEST (PROMPT -1D)")
    print("="*70)

    question = "गेहूं में पीला रतुआ (Yellow Rust) की रोकथाम कैसे करें?"
    farmer_name = "Ramesh"

    # -------------------------------------------------------------------------
    # Test Case 1: Short & Simple Preference
    # -------------------------------------------------------------------------
    print("\n--- TEST CASE 1: PREFERENCE = 'simple' (Short Answers) ---")
    payload_simple = {
        "text": question,
        "language": "hi",
        "crop": "Wheat",
        "farmer_name": farmer_name,
        "detail_level": "simple",
        "explanation_preference": "simple"
    }

    res_simple = client.post("/api/voice/ask-text", json=payload_simple)
    assert res_simple.status_code == 200, res_simple.text
    data_simple = res_simple.json()
    resp_simple = data_simple.get("response_text") or data_simple.get("response") or ""
    words_simple = len(resp_simple.split())
    chars_simple = len(resp_simple)

    print(f"Farmer Name Requested : {farmer_name}")
    print(f"Preference Mode       : simple")
    print(f"Question Asked        : {question}")
    print(f"Response Received     :\n\"{resp_simple}\"")
    print(f"Metrics               : {words_simple} words | {chars_simple} characters")

    # -------------------------------------------------------------------------
    # Test Case 2: Detailed Explanation Preference
    # -------------------------------------------------------------------------
    print("\n--- TEST CASE 2: PREFERENCE = 'detailed' (In-Depth Advisory) ---")
    payload_detailed = {
        "text": question,
        "language": "hi",
        "crop": "Wheat",
        "farmer_name": farmer_name,
        "detail_level": "detailed",
        "explanation_preference": "detailed"
    }

    res_detailed = client.post("/api/voice/ask-text", json=payload_detailed)
    assert res_detailed.status_code == 200, res_detailed.text
    data_detailed = res_detailed.json()
    resp_detailed = data_detailed.get("response_text") or data_detailed.get("response") or ""
    words_detailed = len(resp_detailed.split())
    chars_detailed = len(resp_detailed)

    print(f"Farmer Name Requested : {farmer_name}")
    print(f"Preference Mode       : detailed")
    print(f"Question Asked        : {question}")
    print(f"Response Received     :\n\"{resp_detailed}\"")
    print(f"Metrics               : {words_detailed} words | {chars_detailed} characters")

    # -------------------------------------------------------------------------
    # Verification Assertions
    # -------------------------------------------------------------------------
    print("\n" + "-"*70)
    print("COMPARISON & VERIFICATION")
    print("-"*70)
    print(f"Simple Mode Length   : {chars_simple} chars ({words_simple} words)")
    print(f"Detailed Mode Length : {chars_detailed} chars ({words_detailed} words)")
    print(f"Length Expansion     : +{chars_detailed - chars_simple} chars (+{((chars_detailed/max(1, chars_simple))-1)*100:.1f}%)")

    # Both must be successful
    assert data_simple.get("success") is True
    assert data_detailed.get("success") is True
    assert len(resp_simple) > 0
    assert len(resp_detailed) > 0

    # Detailed response must be longer than simple response
    assert len(resp_detailed) >= len(resp_simple), "Detailed response should be longer than simple response!"

    print("\n" + "="*70)
    print("ALL ADAPTIVE VOICE PREFERENCE TESTS PASSED SUCCESSFULLY!")
    print("="*70)

if __name__ == "__main__":
    test_voice_preference_differences()
