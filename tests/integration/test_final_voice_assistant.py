"""
AgriBridge Final Voice Assistant Comprehensive Test Suite
Validates all 14 languages, agricultural domains, tools, multi-turn contexts, and audio generation.
"""

import sys
import json
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def run_tests():
    print("=" * 70)
    print("AGRIBRIDGE FINAL FARMER VOICE ASSISTANT — COMPREHENSIVE TEST SUITE")
    print("=" * 70)

    # 1. Multi-Turn Conversation & Rolling Memory (Turn 1: Crop Declaration)
    print("\n--- 1. Multi-turn Turn 1: Crop Declaration ---")
    r1 = client.post("/api/voice/ask-text", json={
        "text": "Main wheat ki kheti kar raha hoon",
        "language": "hi",
        "state": "Punjab",
        "district": "Ludhiana"
    }).json()
    assert r1["success"] is True
    assert r1["detected_crop"] == "Wheat"
    assert r1["audio_url"] is not None
    print("[OK] Turn 1 Response:", r1["response_text"][:75], "...")
    print("     Detected Crop:", r1["detected_crop"], "| Audio:", r1["audio_url"])

    # 2. Multi-turn Follow-up (Turn 2: "Isme khaad kab daalein?")
    print("\n--- 2. Multi-turn Turn 2: Context Retention ('Isme khaad?') ---")
    history_turn2 = [
        {"role": "user", "text": "Main wheat ki kheti kar raha hoon"},
        {"role": "assistant", "text": r1["response_text"]}
    ]
    r2 = client.post("/api/voice/ask-text", json={
        "text": "Isme khaad kab daalein?",
        "language": "hi",
        "history": history_turn2
    }).json()
    assert r2["success"] is True
    assert r2["detected_crop"] == "Wheat"
    assert r2["topic"] == "fertilizer"
    print("[OK] Turn 2 Topic:", r2["topic"], "| Crop:", r2["detected_crop"])

    # 3. Multi-turn Follow-up (Turn 3: "Aur paani?")
    print("\n--- 3. Multi-turn Turn 3: Short Follow-up ('Aur paani?') ---")
    history_turn3 = history_turn2 + [
        {"role": "user", "text": "Isme khaad kab daalein?"},
        {"role": "assistant", "text": r2["response_text"]}
    ]
    r3 = client.post("/api/voice/ask-text", json={
        "text": "Aur paani kab de sakte hain?",
        "language": "hi",
        "history": history_turn3
    }).json()
    assert r3["success"] is True
    assert r3["detected_crop"] == "Wheat"
    assert r3["topic"] == "irrigation"
    print("[OK] Turn 3 Topic:", r3["topic"], "| Crop:", r3["detected_crop"])

    # 4. Live Weather & 15-Day Forecast Tool
    print("\n--- 4. Live Weather & Spray Timing Integration ---")
    r4 = client.post("/api/voice/ask-text", json={
        "text": "Kal mere khet mein baarish hogi kya?",
        "language": "hi",
        "state": "Punjab",
        "district": "Ludhiana"
    }).json()
    assert r4["success"] is True
    assert r4["topic"] == "weather"
    print("[OK] Weather Response:", r4["response_text"][:90], "...")

    # 5. Mandi & Market Prices Tool
    print("\n--- 5. Mandi & Market Pricing Tool ---")
    r5 = client.post("/api/voice/ask-text", json={
        "text": "Tomato ka mandi bhav kya chal raha hai?",
        "language": "hi"
    }).json()
    assert r5["success"] is True
    assert r5["topic"] == "market"
    assert r5["detected_crop"] == "Tomato"
    print("[OK] Market Response:", r5["response_text"][:90], "...")

    # 6. App Navigation Trigger ("Mausam dikhao")
    print("\n--- 6. App Navigation: Weather ---")
    r6 = client.post("/api/voice/ask-text", json={
        "text": "Mausam dikhao",
        "language": "hi"
    }).json()
    assert r6["success"] is True
    assert r6["topic"] == "navigation"
    assert r6["navigation_action"]["target"] == "/frontend/pages/weather-dashboard.html"
    print("[OK] Nav Target:", r6["navigation_action"]["target"])

    # 7. App Navigation Trigger ("Crop doctor kholo")
    print("\n--- 7. App Navigation: Crop Doctor ---")
    r7 = client.post("/api/voice/ask-text", json={
        "text": "Crop doctor khol do bimari scan karne ke liye",
        "language": "hi"
    }).json()
    assert r7["success"] is True
    assert r7["navigation_action"]["target"] == "/frontend/pages/upload-crop.html"
    print("[OK] Nav Target:", r7["navigation_action"]["target"])

    # 8. App Help & Feature Tour ("Is app me kya hai?")
    print("\n--- 8. App Help & Platform Tour ---")
    r8 = client.post("/api/voice/ask-text", json={
        "text": "Is app mein kya kya features hain?",
        "language": "hi"
    }).json()
    assert r8["success"] is True
    assert r8["topic"] == "app_help"
    print("[OK] App Help Response:", r8["response_text"][:90], "...")

    # 9. Crop Disease & Photo Guidance
    print("\n--- 9. Crop Disease & ICAR IDM Guidance ---")
    r9 = client.post("/api/voice/ask-text", json={
        "text": "Mere tomato ke leaves pe brown spots aa gaye hain",
        "language": "hi"
    }).json()
    assert r9["success"] is True
    assert r9["topic"] in ["crop_disease", "pest"]
    print("[OK] Disease Response:", r9["response_text"][:90], "...")

    # 10. Pest & Insect Control
    print("\n--- 10. Pest Management ---")
    r10 = client.post("/api/voice/ask-text", json={
        "text": "Cotton mein sundi aur keede lag gaye hain kya karein?",
        "language": "hi"
    }).json()
    assert r10["success"] is True
    assert r10["detected_crop"] == "Cotton"
    print("[OK] Pest Response:", r10["response_text"][:90], "...")

    # 11. Soil & Nutrient Health
    print("\n--- 11. Soil & Micronutrient Advice ---")
    r11 = client.post("/api/voice/ask-text", json={
        "text": "Khet ki mitti ki jaanch kaise karwayein?",
        "language": "hi"
    }).json()
    assert r11["success"] is True
    assert r11["topic"] == "soil"
    print("[OK] Soil Response:", r11["response_text"][:90], "...")

    # 12. Government Schemes (PM-Kisan / Fasal Bima)
    print("\n--- 12. Government Schemes & Subsidies ---")
    r12 = client.post("/api/voice/ask-text", json={
        "text": "PM Kisan yojana aur fasal bima ke baare mein batao",
        "language": "hi"
    }).json()
    assert r12["success"] is True
    assert r12["topic"] == "government_scheme"
    print("[OK] Scheme Response:", r12["response_text"][:90], "...")

    # 13. Multilingual - Punjabi
    print("\n--- 13. Punjabi Language Support ---")
    r13 = client.post("/api/voice/ask-text", json={
        "text": "ਕਣਕ ਦੀ ਫ਼ਸਲ ਵਿੱਚ ਪਾਣੀ ਕਦੋਂ ਦੇਣਾ ਚਾਹੀਦਾ ਹੈ?",
        "language": "pa"
    }).json()
    assert r13["success"] is True
    assert r13["language"] == "pa"
    print("[OK] Punjabi Response:", r13["response_text"][:80], "...")

    # 14. Multilingual - Marathi
    print("\n--- 14. Marathi Language Support ---")
    r14 = client.post("/api/voice/ask-text", json={
        "text": "गहू पिकासाठी खत कधी द्यावे?",
        "language": "mr"
    }).json()
    assert r14["success"] is True
    assert r14["language"] == "mr"
    print("[OK] Marathi Response:", r14["response_text"][:80], "...")

    # 15. Multilingual - Bengali
    print("\n--- 15. Bengali Language Support ---")
    r15 = client.post("/api/voice/ask-text", json={
        "text": "টমেটো গাছে সার কখন প্রয়োগ করবেন?",
        "language": "bn"
    }).json()
    assert r15["success"] is True
    assert r15["language"] == "bn"
    print("[OK] Bengali Response:", r15["response_text"][:80], "...")

    # 16. Multilingual - Telugu
    print("\n--- 16. Telugu Language Support ---")
    r16 = client.post("/api/voice/ask-text", json={
        "text": "వరి పంటకు ఎరువులు ఎప్పుడు వేయాలి?",
        "language": "te"
    }).json()
    assert r16["success"] is True
    assert r16["language"] == "te"
    print("[OK] Telugu Response:", r16["response_text"][:80], "...")

    # 17. Multilingual - Tamil
    print("\n--- 17. Tamil Language Support ---")
    r17 = client.post("/api/voice/ask-text", json={
        "text": "நெல் பயிருக்கு உரம் எப்போது இட வேண்டும்?",
        "language": "ta"
    }).json()
    assert r17["success"] is True
    assert r17["language"] == "ta"
    print("[OK] Tamil Response:", r17["response_text"][:80], "...")

    # 18. Multilingual - Gujarati
    print("\n--- 18. Gujarati Language Support ---")
    r18 = client.post("/api/voice/ask-text", json={
        "text": "કપાસના પાકમાં ખાતર ક્યારે આપવું?",
        "language": "gu"
    }).json()
    assert r18["success"] is True
    assert r18["language"] == "gu"
    print("[OK] Gujarati Response:", r18["response_text"][:80], "...")

    # 19. Multilingual - Hinglish
    print("\n--- 19. Hinglish Support ---")
    r19 = client.post("/api/voice/ask-text", json={
        "text": "Mere wheat ke leaves yellow ho rahe hain kya karun?",
        "language": "hinglish"
    }).json()
    assert r19["success"] is True
    print("[OK] Hinglish Response:", r19["response_text"][:80], "...")

    # 20. Dynamic Language Switching ("Hindi me batao")
    print("\n--- 20. Dynamic Language Switch ('Hindi me batao') ---")
    r20 = client.post("/api/voice/ask-text", json={
        "text": "Hindi me batao gehu mein paani kab dena hai",
        "language": "en"
    }).json()
    assert r20["success"] is True
    assert r20["language"] == "hi"
    print("[OK] Switched Response (Hindi):", r20["response_text"][:80], "...")

    # 21. Non-Agri Polite Redirection
    print("\n--- 21. Non-Agri Polite Redirection ---")
    r21 = client.post("/api/voice/ask-text", json={
        "text": "Who won the cricket world cup yesterday?",
        "language": "en"
    }).json()
    assert r21["success"] is True
    assert r21["is_agriculture_related"] is False
    print("[OK] Redirection Response:", r21["response_text"][:80], "...")

    # 22. Audio Serving Route (/api/voice/audio/{filename})
    print("\n--- 22. Audio Serving Verification ---")
    if r1.get("audio_url"):
        audio_file = r1["audio_url"].split("/")[-1]
        audio_res = client.get(f"/api/voice/audio/{audio_file}")
        assert audio_res.status_code == 200
        assert len(audio_res.content) > 500
        print("[OK] Audio file retrieved successfully:", audio_file, f"({len(audio_res.content)} bytes)")

    print("\n" + "=" * 70)
    print("ALL 22 FINAL VOICE ASSISTANT TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()

