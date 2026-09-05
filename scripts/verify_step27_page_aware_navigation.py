#!/usr/bin/env python3
"""
STEP 27 VERIFICATION SUITE
Page-Aware Navigation & UI Guidance Validation
=====================================================
Validates:
1. Farmer Dashboard Navigation Guidance (15-Day Weather & Advisory, My Marketplace Listings, Upload Crop Photo).
2. On-Screen Guidance on Weather Page (15-day forecast, rain risk probability, safe spray window).
3. On-Screen Guidance on AI Crop Scan Page (Choose File, Diagnose Disease).
4. On-Screen Guidance on Marketplace Page (Live Mandi rates table, List New Crop).
5. Zero Fabricated Controls Across All 18 Farmer Screens.
6. Multi-Turn End-to-End Navigation Journey (Dashboard -> "Mil gaya" -> Weather Page -> "Ab kya?" -> "Ye samajh nahi aaya").
"""

import os
import sys

# Reconfigure stdout for UTF-8 in Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient

# Add backend directory to path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
from app.services.saathi_service import AGRIBRIDGE_SCREENS, PLATFORM_FEATURES

client = TestClient(app)

def run_tests():
    total_tests = 0
    passed_tests = 0

    print("======================================================================")
    print("STEP 27 VERIFICATION: PAGE-AWARE NAVIGATION & UI GUIDANCE VALIDATION")
    print("======================================================================\n")

    # -------------------------------------------------------------------------
    # TEST 1: Farmer Dashboard Navigation Guidance
    # -------------------------------------------------------------------------
    print("--- Test 1: Guidance on Farmer Dashboard ---")
    dashboard_cases = [
        {
            "query": "Saathi, mujhe weather dekhna hai.",
            "current_page": "farmer-dashboard",
            "lang": "hinglish",
            "expected_keywords": ["15-day weather & advisory", "weather", "dashboard"]
        },
        {
            "query": "Saathi, mujhe mandi bhav dekhna hai.",
            "current_page": "farmer-dashboard",
            "lang": "hinglish",
            "expected_keywords": ["my marketplace listings", "marketplace", "dashboard"]
        },
        {
            "query": "Saathi, mujhe crop photo upload karna hai.",
            "current_page": "farmer-dashboard",
            "lang": "hinglish",
            "expected_keywords": ["upload crop photo", "ai crop scan", "dashboard"]
        }
    ]

    for tc in dashboard_cases:
        total_tests += 1
        payload = {
            "text": tc["query"],
            "language": tc["lang"],
            "current_page": tc["current_page"]
        }
        resp = client.post("/api/voice/saathi", json=payload)
        assert resp.status_code == 200, f"HTTP {resp.status_code}"
        data = resp.json()
        assert data["success"] is True
        res_text = data.get("response_text", "")
        r_lower = res_text.lower()
        matched = all(k in r_lower for k in tc["expected_keywords"])
        status = "PASS" if matched else "FAIL"
        print(f"[{status}] Query: '{tc['query']}' on '{tc['current_page']}'")
        print(f"       Response: {res_text}")
        if matched:
            passed_tests += 1
        else:
            print(f"       MISSING KEYWORDS from {tc['expected_keywords']}")

    # -------------------------------------------------------------------------
    # TEST 2: On-Screen Guidance on Weather Page
    # -------------------------------------------------------------------------
    print("\n--- Test 2: In-Place Context on Weather Page ---")
    weather_cases = [
        {
            "query": "Ab mujhe kya dekhna hai?",
            "current_page": "weather-dashboard",
            "lang": "hinglish",
            "expected_keywords": ["15 din", "mausam forecast", "spray"],
            "forbidden_keywords": ["weather button par click karein"]
        },
        {
            "query": "Saathi, mujhe weather dekhna hai.",
            "current_page": "weather-dashboard",
            "lang": "hinglish",
            "expected_keywords": ["weather page par hi hain", "15 din", "forecast"],
            "forbidden_keywords": ["upar diye gaye 'weather' button par click karein"]
        },
        {
            "query": "What should I look at here?",
            "current_page": "weather-dashboard",
            "lang": "en",
            "expected_keywords": ["15-day", "weather forecast", "spray"],
            "forbidden_keywords": ["click on the 'weather' button"]
        }
    ]

    for tc in weather_cases:
        total_tests += 1
        payload = {
            "text": tc["query"],
            "language": tc["lang"],
            "current_page": tc["current_page"]
        }
        resp = client.post("/api/voice/saathi", json=payload)
        assert resp.status_code == 200, f"HTTP {resp.status_code}"
        data = resp.json()
        assert data["success"] is True
        res_text = data.get("response_text", "")
        r_lower = res_text.lower()
        has_expected = all(k.lower() in r_lower for k in tc["expected_keywords"])
        has_forbidden = any(f.lower() in r_lower for f in tc.get("forbidden_keywords", []))
        matched = has_expected and not has_forbidden
        status = "PASS" if matched else "FAIL"
        print(f"[{status}] Query: '{tc['query']}' on '{tc['current_page']}'")
        print(f"       Response: {res_text}")
        if matched:
            passed_tests += 1
        else:
            print(f"       Failed: expected={tc['expected_keywords']}, forbidden={tc.get('forbidden_keywords')}")

    # -------------------------------------------------------------------------
    # TEST 3: On-Screen Guidance on AI Crop Scan / Disease Detection Page
    # -------------------------------------------------------------------------
    print("\n--- Test 3: In-Place Context on AI Crop Scan Page ---")
    crop_scan_cases = [
        {
            "query": "Photo kahan upload karna hai?",
            "current_page": "upload-crop",
            "lang": "hinglish",
            "expected_keywords": ["choose file", "diagnose disease"]
        },
        {
            "query": "Ab kya karna hai?",
            "current_page": "upload-crop",
            "lang": "hinglish",
            "expected_keywords": ["choose file", "diagnose disease"]
        },
        {
            "query": "फसल की फोटो कैसे अपलोड करूं?",
            "current_page": "upload-crop",
            "lang": "hi",
            "expected_keywords": ["choose file", "diagnose disease"]
        }
    ]

    for tc in crop_scan_cases:
        total_tests += 1
        payload = {
            "text": tc["query"],
            "language": tc["lang"],
            "current_page": tc["current_page"]
        }
        resp = client.post("/api/voice/saathi", json=payload)
        assert resp.status_code == 200, f"HTTP {resp.status_code}"
        data = resp.json()
        assert data["success"] is True
        res_text = data.get("response_text", "")
        r_lower = res_text.lower()
        matched = all(k.lower() in r_lower for k in tc["expected_keywords"])
        status = "PASS" if matched else "FAIL"
        print(f"[{status}] Query: '{tc['query']}' on '{tc['current_page']}'")
        print(f"       Response: {res_text}")
        if matched:
            passed_tests += 1
        else:
            print(f"       MISSING KEYWORDS from {tc['expected_keywords']}")

    # -------------------------------------------------------------------------
    # TEST 4: On-Screen Guidance on Marketplace Page
    # -------------------------------------------------------------------------
    print("\n--- Test 4: In-Place Context on Marketplace Page ---")
    market_cases = [
        {
            "query": "Mandi bhav kahan hai?",
            "current_page": "crop-listings",
            "lang": "hinglish",
            "expected_keywords": ["marketplace screen par hi hain", "mandi rates", "list new crop"]
        },
        {
            "query": "Ab kya?",
            "current_page": "crop-listings",
            "lang": "hinglish",
            "expected_keywords": ["mandi rates", "list new crop"]
        },
        {
            "query": "मंडी भाव कहाँ है?",
            "current_page": "crop-listings",
            "lang": "hi",
            "expected_keywords": ["marketplace", "मंडी भाव", "list new crop"]
        }
    ]

    for tc in market_cases:
        total_tests += 1
        payload = {
            "text": tc["query"],
            "language": tc["lang"],
            "current_page": tc["current_page"]
        }
        resp = client.post("/api/voice/saathi", json=payload)
        assert resp.status_code == 200, f"HTTP {resp.status_code}"
        data = resp.json()
        assert data["success"] is True
        res_text = data.get("response_text", "")
        r_lower = res_text.lower()
        matched = all(k.lower() in r_lower for k in tc["expected_keywords"])
        status = "PASS" if matched else "FAIL"
        print(f"[{status}] Query: '{tc['query']}' on '{tc['current_page']}'")
        print(f"       Response: {res_text}")
        if matched:
            passed_tests += 1
        else:
            print(f"       MISSING KEYWORDS from {tc['expected_keywords']}")

    # -------------------------------------------------------------------------
    # TEST 5: Zero Fabricated Controls Across All 18 Pages
    # -------------------------------------------------------------------------
    print("\n--- Test 5: Real UI Component Validation Across All 18 Farmer Screens ---")
    total_screens = len(AGRIBRIDGE_SCREENS)
    screen_passes = 0

    all_registered_buttons = set()
    for s_id, s_info in AGRIBRIDGE_SCREENS.items():
        all_registered_buttons.update([b.lower() for b in s_info.get("primary_buttons", [])])
        all_registered_buttons.update([b.lower() for b in s_info.get("top_navbar", [])])
    for f_id, f_info in PLATFORM_FEATURES.items():
        all_registered_buttons.add(f_info["button_name"].lower())

    for screen_id, s_info in AGRIBRIDGE_SCREENS.items():
        payload = {
            "text": "Is page par kya karna hai?",
            "language": "hinglish",
            "current_page": screen_id
        }
        resp = client.post("/api/voice/saathi", json=payload)
        assert resp.status_code == 200, f"HTTP {resp.status_code}"
        data = resp.json()
        res_text = data.get("response_text", "")
        nav_info = data.get("navigation") or {}
        btn_meta = nav_info.get("button")
        
        valid = bool(res_text) and (btn_meta is None or btn_meta.lower() in all_registered_buttons or any(b in res_text for b in s_info["primary_buttons"] + s_info["top_navbar"]))
        if valid:
            screen_passes += 1
            print(f"[PASS] Screen '{screen_id}' -> Response: {res_text[:65]}...")
        else:
            print(f"[FAIL] Screen '{screen_id}' -> Unregistered UI element")

    total_tests += 1
    if screen_passes == total_screens:
        passed_tests += 1
        print(f"-> All {total_screens}/{total_screens} farmer screens successfully validated with real UI elements.")

    # -------------------------------------------------------------------------
    # TEST 6: Multi-Turn End-to-End Navigation Journey
    # -------------------------------------------------------------------------
    print("\n--- Test 6: Multi-Turn End-to-End Navigation Journey ---")
    history = []
    journey_passes = 0
    journey_steps = [
        {
            "turn": 1,
            "user": "Mujhe weather dekhna hai.",
            "screen": "farmer-dashboard",
            "lang": "hinglish",
            "check": lambda r: "15-day weather & advisory" in r.lower() or "weather" in r.lower()
        },
        {
            "turn": 2,
            "user": "Mil gaya.",
            "screen": "farmer-dashboard",
            "lang": "hinglish",
            "check": lambda r: "click" in r.lower() or "badhiya" in r.lower() or "ji" in r.lower()
        },
        {
            "turn": 3,
            "user": "Ab kya?",
            "screen": "weather-dashboard",  # Farmer navigated to weather dashboard
            "lang": "hinglish",
            "check": lambda r: "15 din" in r.lower() and "spray" in r.lower()
        },
        {
            "turn": 4,
            "user": "Ye samajh nahi aaya.",
            "screen": "weather-dashboard",
            "lang": "hinglish",
            "check": lambda r: "aasan shabdon mein" in r.lower() or "15 din" in r.lower()
        }
    ]

    for step in journey_steps:
        payload = {
            "text": step["user"],
            "language": step["lang"],
            "current_page": step["screen"],
            "history": history
        }
        resp = client.post("/api/voice/saathi", json=payload)
        assert resp.status_code == 200, f"HTTP {resp.status_code}"
        data = resp.json()
        res_text = data.get("response_text", "")
        history.append({"user": step["user"], "assistant": res_text})
        passed = step["check"](res_text)
        status = "PASS" if passed else "FAIL"
        print(f"Turn {step['turn']} ({step['screen']}): '{step['user']}' -> '{res_text}' [{status}]")
        if passed:
            journey_passes += 1

    total_tests += 1
    if journey_passes == len(journey_steps):
        passed_tests += 1
        print(f"-> Multi-turn journey completely verified ({journey_passes}/{len(journey_steps)} turns).")

    # -------------------------------------------------------------------------
    # FINAL SUMMARY
    # -------------------------------------------------------------------------
    print("\n======================================================================")
    print(f"FINAL RESULT: {passed_tests}/{total_tests} Test Suites Passed ({passed_tests/total_tests*100:.1f}%)")
    print("======================================================================")

    if passed_tests == total_tests:
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())

