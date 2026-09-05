"""
Comprehensive Test Suite for Unified Kisan Saathi Agricultural Assistant
Testing:
- Multilingual STT / Text Language Detection (Odia, Hindi, Hinglish, English)
- Odia Numeral Extraction & Crop Entity Parsing
- Multi-Turn Conversation Context & Follow-up Resolution
- Stage-Aware Irrigation (e.g., Wheat 25-day CRI Crown Root Initiation)
- Weather-Aware Delay & Real Open-Meteo Integration
- Stage-Aware Cautious Fertilizer Advice
- Crop Disease Scan Guidance & Diagnosis Follow-up
- Stage-Appropriate 5-Day Daily Action Plans
- Navigation & App Help
- Non-Agriculture Safe Fallback
- 100% Voice and Text Parity
"""

import asyncio
import pytest
from backend.app.services.agriculture_intent import (
    classify_intent,
    extract_crop_entity,
    extract_crop_age_days,
    extract_location,
    is_short_followup_answer,
    get_stage_from_days,
    normalize_digits,
)
from backend.app.services.saathi_service import (
    detect_language,
    process_saathi_interaction,
    ConversationContext,
)
from backend.app.services.voice_service import process_voice_query
from backend.app.data.india_districts import search_district_by_name


# ==============================================================================
# 1. ODIA NUMERALS & LANGUAGE DETECTION TESTS
# ==============================================================================

def test_odia_numeral_conversion():
    assert normalize_digits("୨୫") == "25"
    assert normalize_digits("୧୦୦") == "100"
    assert normalize_digits("ମୋ ଫସଲ ୨୫ ଦିନର") == "ମୋ ଫସଲ 25 ଦିନର"


def test_language_detection():
    # Odia script
    assert detect_language("ମୋ ଗହମ ଫସଲରେ କେବେ ପାଣି ଦେବି?") == "or"
    assert detect_language("୨୫ ଦିନର") == "or"
    assert detect_language("ବେଙ୍ଗାଲୁରୁ") == "or"

    # Hindi script
    assert detect_language("मेरे गेहूं के खेत में कब पानी देना चाहिए?") == "hi"

    # English
    assert detect_language("When should I irrigate my wheat field?") == "en"

    # Hinglish
    assert detect_language("Mere wheat crop mein kab pani dena chahiye?") == "hinglish"


def test_crop_and_age_extraction_odia():
    # Odia crop & age
    text = "ମୋ ଗହମ ଫସଲ ୨୫ ଦିନର ହୋଇଛି"
    crop = extract_crop_entity(text)
    assert crop.lower() == "wheat"

    age, stage = extract_crop_age_days(text)
    assert age == 25
    assert stage == "Vegetative"


def test_location_search_aliases():
    bengaluru = search_district_by_name("ବେଙ୍ଗାଲୁରୁ")
    assert bengaluru is not None
    assert "Bengaluru" in bengaluru["name"] or "Bangalore" in bengaluru["name"]

    bhubaneswar = search_district_by_name("ଭୁବନେଶ୍ୱର")
    assert bhubaneswar is not None
    assert "Khordha" in bhubaneswar["name"] or "Bhubaneswar" in bhubaneswar["name"]

    cuttack = search_district_by_name("Cuttack")
    assert cuttack is not None
    assert cuttack["state"] == "Odisha"


# ==============================================================================
# 2. MULTI-TURN CONVERSATION & PENDING FOLLOW-UP RESOLUTION
# ==============================================================================

def test_odia_multi_turn_irrigation_flow():
    """
    Simulates a 3-turn Odia dialogue:
    Turn 1: "ମୁଁ ମୋ ଫସଲରେ କେବେ ପାଣି ଦେବି?" (Missing crop & age)
    Turn 2: "ଗହମ" (Provides crop, missing age)
    Turn 3: "୨୫ ଦିନର" (Provides age -> gets 25-day CRI stage advice)
    """
    async def run_flow():
        # Turn 1
        t1_res = await process_saathi_interaction(
            text_query="ମୁଁ ମୋ ଫସଲରେ କେବେ ପାଣି ଦେବି?",
            language="or"
        )
        assert t1_res["success"] is True
        assert t1_res["language"] == "or"
        assert t1_res["pending_field"] == "crop"
        assert "କେଉଁ ଫସଲ" in t1_res["response"] or "ଫସଲର ନାମ" in t1_res["response"]

        history = [
            {"role": "user", "text": "ମୁଁ ମୋ ଫସଲରେ କେବେ ପାଣି ଦେବି?"},
            {"role": "assistant", "text": t1_res["response"]}
        ]

        # Turn 2: User answers "ଗହମ"
        t2_res = await process_saathi_interaction(
            text_query="ଗହମ",
            language="or",
            history=history
        )
        assert t2_res["success"] is True
        assert t2_res["detected_crop"].lower() == "wheat"
        assert t2_res["pending_field"] == "crop_age_days"
        assert "କେତେ ଦିନ" in t2_res["response"] or "ବୟସ" in t2_res["response"]
        # Verify it does NOT treat "ଗହମ" as a fallback or generic greeting!
        assert "ନମସ୍କାର ଜୀ! ମୁଁ ସାଥୀ" not in t2_res["response"]

        history.extend([
            {"role": "user", "text": "ଗହମ"},
            {"role": "assistant", "text": t2_res["response"]}
        ])

        # Turn 3: User answers "୨୫ ଦିନର"
        t3_res = await process_saathi_interaction(
            text_query="୨୫ ଦିନର",
            language="or",
            history=history
        )
        assert t3_res["success"] is True
        assert t3_res["detected_crop"].lower() == "wheat"
        assert t3_res["crop_age_days"] == 25
        assert t3_res["pending_field"] is None
        # Must contain CRI stage crown root initiation advice in Odia
        assert "CRI" in t3_res["response"] or "ଶିଖର ମୂଳ" in t3_res["response"] or "ଜଳସେଚନ" in t3_res["response"]

    asyncio.run(run_flow())


def test_hindi_irrigation_with_full_context():
    """
    Hindi direct single-turn query with crop and age:
    "मेरे 25 दिन के गेहूं में कब पानी देना चाहिए?"
    """
    async def run_flow():
        res = await process_saathi_interaction(
            text_query="मेरे 25 दिन के गेहूं में कब पानी देना चाहिए?",
            language="hi"
        )
        assert res["success"] is True
        assert res["language"] == "hi"
        assert res["detected_crop"].lower() == "wheat"
        assert res["crop_age_days"] == 25
        assert "CRI" in res["response"] or "ताज जड़" in res["response"] or "सिंचाई" in res["response"]

    asyncio.run(run_flow())


# ==============================================================================
# 3. WEATHER-AWARE IRRIGATION & REAL OPEN-METEO INTEGRATION
# ==============================================================================

def test_weather_query_and_rain_delay():
    """
    Weather query with location:
    "ଆଜି ବେଙ୍ଗାଲୁରୁରେ ବର୍ଷା ହେବ କି?"
    """
    async def run_flow():
        res = await process_saathi_interaction(
            text_query="ଆଜି ବେଙ୍ଗାଲୁରୁରେ ବର୍ଷା ହେବ କି?",
            language="or"
        )
        assert res["success"] is True
        assert res["intent"] == "weather"
        assert res["location"] is not None
        # Weather response should provide temperature/rain info
        assert "ତାପମାତ୍ରା" in res["response"] or "ବର୍ଷା" in res["response"] or "ପାଣିପାଗ" in res["response"]

    asyncio.run(run_flow())


# ==============================================================================
# 4. STAGE-AWARE FERTILIZER GUIDANCE
# ==============================================================================

def test_stage_aware_fertilizer_advice():
    """
    Fertilizer advice for 25-day wheat crop:
    "୨୫ ଦିନର ଗହମ ଫସଲରେ କେଉଁ ଖତ ବା ୟୁରିଆ ଦେବି?"
    """
    async def run_flow():
        res = await process_saathi_interaction(
            text_query="୨୫ ଦିନର ଗହମ ଫସଲରେ କେଉଁ ଖତ ବା ୟୁରିଆ ଦେବି?",
            language="or"
        )
        assert res["success"] is True
        assert res["intent"] == "fertilizer"
        assert res["detected_crop"].lower() == "wheat"
        assert res["crop_age_days"] == 25
        # Should provide stage-aware fertilizer advice (Urea / NPK split dose)
        assert "ୟୁରିଆ" in res["response"] or "ସାର" in res["response"] or "CRI" in res["response"]

    asyncio.run(run_flow())


# ==============================================================================
# 5. CROP DISEASE DETECTION & DIAGNOSIS FOLLOW-UP
# ==============================================================================

def test_crop_disease_prompt_for_photo():
    """
    Disease query without previous scan:
    "ମୋ ଫସଲ ପତ୍ରରେ ହଳଦିଆ ଦାଗ ଦେଖାଯାଉଛି, କଣ କରିବି?"
    """
    async def run_flow():
        res = await process_saathi_interaction(
            text_query="ମୋ ଫସଲ ପତ୍ରରେ ହଳଦିଆ ଦାଗ ଦେଖାଯାଉଛି, କଣ କରିବି?",
            language="or"
        )
        assert res["success"] is True
        assert res["intent"] == "crop_disease"
        # Should prompt for leaf photo and provide navigation link to upload-crop
        assert "ଫଟୋ" in res["response"] or "AI Crop Scan" in res["response"]
        assert res["navigation_action"] is not None
        assert "upload-crop" in res["navigation_action"]["target"]

    asyncio.run(run_flow())


def test_crop_disease_with_existing_prediction():
    """
    Disease query when scan is already completed (prediction_info in context):
    """
    async def run_flow():
        prediction = {
            "disease_name": "Wheat Yellow Rust (Puccinia striiformis)",
            "confidence": 0.94,
            "is_healthy": False
        }
        res = await process_saathi_interaction(
            text_query="ଏହି ରୋଗକୁ କିପରି ଭଲ କରିବି?",
            language="or",
            crop="wheat",
            prediction_info=prediction
        )
        assert res["success"] is True
        assert res["intent"] == "crop_disease"
        assert "Yellow Rust" in res["response"] or "ରୋଗ" in res["response"]
        # Ensure safe advisory without overdose
        assert "ସୁରକ୍ଷିତ" in res["response"] or "ଚିକିତ୍ସା" in res["response"] or "ନିମ" in res["response"]

    asyncio.run(run_flow())


# ==============================================================================
# 6. PRACTICAL 5-DAY DAILY ACTION PLAN
# ==============================================================================

def test_five_step_action_plan():
    """
    Action plan request for 25-day growing wheat:
    "ଆଗାମୀ ୫ ଦିନ ପାଇଁ ମୋତେ ଏକ କାର୍ଯ୍ୟ ଯୋଜନା ଦିଅନ୍ତୁ"
    """
    async def run_flow():
        res = await process_saathi_interaction(
            text_query="ଆଗାମୀ ୫ ଦିନ ପାଇଁ ମୋତେ ଏକ କାର୍ଯ୍ୟ ଯୋଜନା ଦିଅନ୍ତୁ",
            language="or",
            crop="wheat",
            crop_age_days=25
        )
        assert res["success"] is True
        assert res["intent"] == "action_plan"
        # Should contain 5 numbered action steps in Odia
        assert "୧." in res["response"] or "1." in res["response"]
        assert "୨." in res["response"] or "2." in res["response"]
        assert "୫." in res["response"] or "5." in res["response"]
        assert "କାର୍ଯ୍ୟ ଯୋଜନା" in res["response"] or "action plan" in res["response"].lower()

    asyncio.run(run_flow())


# ==============================================================================
# 7. SAFE NON-AGRICULTURE FALLBACK
# ==============================================================================

def test_safe_non_agri_fallback():
    """
    Non-agriculture query:
    "Who is the president of America?"
    """
    async def run_flow():
        res = await process_saathi_interaction(
            text_query="Who is the president of America?",
            language="en"
        )
        assert res["success"] is True
        assert res["intent"] == "fallback"
        assert "agriculture" in res["response"].lower() or "farming" in res["response"].lower()

    asyncio.run(run_flow())


# ==============================================================================
# 8. 100% VOICE AND TEXT PARITY
# ==============================================================================

def test_voice_and_text_parity():
    """
    Verifies that calling process_voice_query produces the exact same structure and advisory
    as process_saathi_interaction.
    """
    async def run_flow():
        q = "When should I irrigate my 25 day wheat crop?"
        res_text = await process_saathi_interaction(text_query=q, language="en")
        res_voice = await process_voice_query(text_query=q, language="en")

        assert res_text["success"] == res_voice["success"]
        assert res_text["intent"] == res_voice["intent"]
        assert res_text["detected_crop"] == res_voice["detected_crop"]
        assert res_text["crop_age_days"] == res_voice["crop_age_days"]
        assert res_text["response"] == res_voice["response"]

    asyncio.run(run_flow())
