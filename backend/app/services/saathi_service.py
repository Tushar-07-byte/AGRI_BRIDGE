"""
AgriBridge Saathi Voice Assistant Service (Step 2 — Platform Understanding & Navigation)
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Step 2 Enhancements:
- Understands the entire AgriBridge platform (screens, buttons, features, locations, flows).
- Guides farmers who don't know which button or feature to use.
- Explains what specific buttons do in the farmer's language.
- Context-aware screen understanding (answers questions like "Upar wala button kaunsa hai?").
- STRICT SCOPE: Guides the farmer to the feature, NEVER provides internal feature data
  (no live mandi prices, no weather forecast metrics, no chemical disease diagnoses).
- Multilingual in 14 Indian languages + Hinglish with automatic language detection.
"""

import os
import sys
import re
import json
import uuid
import httpx
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from app.services.speech_to_text import transcribe_audio
from app.services.text_to_speech import synthesize_speech_with_status


# ==============================================================================
# 1. SUPPORTED LANGUAGES & CANONICAL NAMES
# ==============================================================================

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "hinglish": "Hinglish",
    "pa": "Punjabi",
    "mr": "Marathi",
    "bn": "Bengali",
    "gu": "Gujarati",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "or": "Odia",
    "as": "Assamese",
    "ur": "Urdu",
}


# ==============================================================================
# 2. SAATHI FIRST INTRODUCTORY MESSAGE (ALL LANGUAGES)
# ==============================================================================

SAATHI_INTRODUCTIONS = {
    "hi": "नमस्ते जी! मैं साथी हूँ। आप मुझसे सामान्य तरीके से बात कर सकते हैं। जब भी आपको मेरी ज़रूरत हो, बस मुझसे बात कीजिए।",
    "hinglish": "Namaste ji! Main Saathi hoon. Aap mujhse normal tarike se baat kar sakte hain. Jab bhi aapko meri zarurat ho, bas mujhse baat kijiye.",
    "en": "Hello! I am Saathi. You can talk to me naturally. Whenever you need me, just speak with me.",
    "pa": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ ਜੀ! ਮੈਂ ਸਾਥੀ ਹਾਂ। ਤੁਸੀਂ ਮੇਰੇ ਨਾਲ ਆਮ ਤਰੀਕੇ ਨਾਲ ਗੱਲ ਕਰ ਸਕਦੇ ਹੋ। ਜਦੋਂ ਵੀ ਤੁਹਾਨੂੰ ਮੇਰੀ ਲੋੜ ਹੋਵੇ, ਬੱਸ ਮੇਰੇ ਨਾਲ ਗੱਲ ਕਰੋ।",
    "mr": "नमस्कार जी! मी साथी आहे. आपण माझ्याशी सहजपणे बोलू शकता. जेव्हाही आपल्याला माझी गरज असेल, तेव्हा फक्त माझ्याशी बोला.",
    "bn": "নমস্কার! আমি সাথী। আপনি আমার সাথে স্বাভাবিকভাবে কথা বলতে পারেন। যখনই আপনার আমাকে প্রয়োজন হবে, শুধু আমার সাথে কথা বলুন।",
    "gu": "નમસ્તે જી! હું સાથી છું. તમે મારી સાથે સામાન્ય રીતે વાત કરી શકો છો. જ્યારે પણ તમને મારી જરૂર હોય, બસ મારી સાથે વાત કરો.",
    "ta": "வணக்கம்! நான் சாதி (Saathi). நீங்கள் என்னுடன் இயல்பாகப் பேசலாம். உங்களுக்கு நான் எப்போது தேவைப்பட்டாலும், என்னிடம் பேசுங்கள்.",
    "te": "నమస్కారం అండి! నేను సాథి (Saathi). మీరు నాతో సహజంగా మాట్లాడవచ్చు. మీకు ఎప్పుడు నా అవసరం వచ్చినా, నాతో మాట్లాడండి.",
    "kn": "ನಮಸ್ಕಾರ! ನಾನು ಸಾಥಿ (Saathi). ನೀವು ನನ್ನೊಂದಿಗೆ ಸಹಜವಾಗಿ ಮಾತನಾಡಬಹುದು. ನಿಮಗೆ ಯಾವಾಗ ನನ್ನ ಅಗತ್ಯವಿದ್ದರೂ, ನನ್ನೊಂದಿಗೆ ಮಾತನಾಡಿ.",
    "ml": "നമസ്കാരം! ഞാൻ സാഥി (Saathi). നിങ്ങൾക്ക് എന്നോട് സാധാരണ രീതിയിൽ സംസാരിക്കാം. എപ്പോൾ സഹായം വേണമെങ്കിലും എന്നോട് സംസാരിക്കൂ.",
    "or": "ନମସ୍କାର ଜୀ! ମୁଁ ସାଥୀ। ଆପଣ ମୋ ସହିତ ସହଜରେ କଥାବାର୍ତ୍ତା କରିପାରିବେ। ଯେତେବେଳେ ବି ମୋର ଆବଶ୍ୟକତା ପଡ଼ିବ, ମୋ ସହିତ କଥା ହୁଅନ୍ତୁ।",
    "as": "নমস্কাৰ! মই সাথী। আপুনি মোৰ সৈতে স্বাভাৱিকভাৱে কথা পাতিব পাৰে। যেতিয়াই আপোনাক মোৰ প্ৰয়োজন হয়, মোৰ লগত কথা পাতক।",
    "ur": "سلام جی! میں ساتھی ہوں۔ آپ مجھ سے عام طریقے سے بات کر سکتے ہیں۔ جب भी آپ کو میری ضرورت ہو، بس مجھ سے بات کیجیے۔",
}

def get_saathi_introduction(language: str = "hi") -> str:
    """Returns Saathi's canonical introduction in the requested language."""
    lang_key = (language or "hi").strip().lower().split("-")[0]
    return SAATHI_INTRODUCTIONS.get(lang_key, SAATHI_INTRODUCTIONS["hi"])


class ConversationContext:
    """Conversation context tracker for Kisan Saathi sessions."""
    def __init__(self, **kwargs):
        self.crop = kwargs.get("crop")
        self.crop_age_days = kwargs.get("crop_age_days")
        self.growth_stage = kwargs.get("growth_stage")
        self.location = kwargs.get("location")
        self.language = kwargs.get("language", "hi")
        self.pending_field = kwargs.get("pending_field")
        self.disease_result = kwargs.get("disease_result")
        self.last_response_text = kwargs.get("last_response_text", "")
        self.last_response_type = kwargs.get("last_response_type", "")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "crop": self.crop,
            "crop_age_days": self.crop_age_days,
            "growth_stage": self.growth_stage,
            "location": self.location,
            "language": self.language,
            "pending_field": self.pending_field,
            "disease_result": self.disease_result,
        }


# ==============================================================================
# 3. REAL-TIME MULTILINGUAL LANGUAGE DETECTION
# ==============================================================================

def detect_language(text: str, current_lang: Optional[str] = None) -> str:
    """
    Automatically detects the language of the farmer's utterance.
    Supports all 14 Indian languages and handles code-mixed / Hinglish speech.
    """
    if not text or not text.strip():
        return current_lang or "en"

    clean = text.strip()

    # 1. Unicode Script Detection
    if re.search(r"[\u0A00-\u0A7F]", clean):
        return "pa"  # Gurmukhi -> Punjabi
    if re.search(r"[\u0A80-\u0AFF]", clean):
        return "gu"  # Gujarati
    if re.search(r"[\u0B00-\u0B7F]", clean):
        return "or"  # Odia
    if re.search(r"[\u0B80-\u0BFF]", clean):
        return "ta"  # Tamil
    if re.search(r"[\u0C00-\u0C7F]", clean):
        return "te"  # Telugu
    if re.search(r"[\u0C80-\u0CFF]", clean):
        return "kn"  # Kannada
    if re.search(r"[\u0D00-\u0D7F]", clean):
        return "ml"  # Malayalam
    if re.search(r"[\u0600-\u06FF\u0750-\u077F]", clean):
        return "ur"  # Arabic script -> Urdu

    # Bengali vs Assamese
    if re.search(r"[\u0980-\u09FF]", clean):
        if re.search(r"[\u09F0\u09F1]", clean) or any(w in clean for w in ["আপুনি", "কওক", "কেনে", "হয়"]):
            return "as"
        return "bn"

    # Devanagari script: Distinguish Marathi vs Hindi
    if re.search(r"[\u0900-\u097F]", clean):
        marathi_markers = ["ळ", "आहे", "आहात", "कसे", "काय", "नाही", "मला", "सांगा", "होते", "करा", "मी", "आपण", "नमस्कार", "पाहिजे", "पाहायचा", "बाजारभाव"]
        hindi_copulas = ["है", "हैं", "हूं", "हूँ", "था", "थी", "मुझे", "बताओ", "करना", "चाहिए"]
        if any(w in clean for w in marathi_markers) and not any(w in clean for w in hindi_copulas):
            return "mr"
        return "hi"

    # 2. Latin / Roman script: Distinguish Hinglish vs English vs Romanized regional
    lower = clean.lower()
    words = set(re.findall(r"\b[a-z']+\b", lower))

    if any(w in lower for w in ["kiddan", "sat sri akal", "kiwe", "kivein", "dasso", "tussi"]):
        return "pa"
    if "vanakkam" in lower:
        return "ta"
    if "namaskara" in lower or "hegiddira" in lower:
        return "kn"
    if "namaskaram" in lower and "ela unnaru" in lower:
        return "te"

    english_common = {
        "hello", "hi", "hey", "how", "are", "you", "doing", "today", "who", "what", "is", "your",
        "name", "can", "i", "help", "talk", "to", "good", "morning", "afternoon", "evening",
        "fine", "well", "thanks", "thank", "please", "yes", "no", "tell", "me", "listening",
        "hear", "there", "friend", "speak", "with", "where", "which", "button", "screen", "page",
        "show", "open", "click", "find", "use", "feature"
    }

    hinglish_vocabulary = {
        "namaste", "namaskar", "kaise", "kaisa", "kaisi", "kya", "hai", "hain", "ho",
        "hoon", "hun", "main", "mera", "meri", "mere", "aap", "aapka", "aapki", "aapke",
        "tum", "tumhara", "tumhari", "kuch", "batao", "bataiye", "bol", "bolo", "boliye", "baat",
        "karo", "karna", "chahiye", "nahi", "nahin", "theek", "thik", "shukriya",
        "dhanyawad", "zarurat", "bhai", "ji", "khet", "fasal", "paani",
        "pani", "kisaan", "kisan", "madad", "suno", "sun", "sunao", "accha", "achha",
        "bahut", "yaar", "kaun", "kaunsa", "kaha", "kahan", "kab", "kyu", "kyun", "zaroorat",
        "upar", "wala", "wali", "wale", "uparwala", "dekhna", "dekhu", "kholna", "kholu", "dikhaye", "karta", "karein", "kijiye",
        "mujhe", "mil", "raha", "rahi", "rahe", "option", "kar", "diya", "kardiya", "gaya", "hogaya", "liya", "karliya",
        "daal", "daaldi", "daala", "daali", "bhar", "bhardiya", "bharein", "ab", "aage", "uske", "iske", "baad", "pe", "par", "se", "ko"
    }

    eng_hits = len(words.intersection(english_common))
    hing_hits = len(words.intersection(hinglish_vocabulary))

    if hing_hits >= 1 and hing_hits >= eng_hits:
        return "hinglish"
    if eng_hits > hing_hits:
        return "en"
    if hing_hits >= 1:
        return "hinglish"

    return current_lang or "hinglish"

    return "en"


# ==============================================================================
# 4. AGRIBRIDGE PLATFORM ARCHITECTURE & NAVIGATION REGISTRY
# ==============================================================================

PLATFORM_FEATURES = {
    "marketplace": {
        "id": "marketplace",
        "button_name": "Marketplace",
        "display_name": "Marketplace (Mandi Bhav)",
        "location": "Top navigation bar ('Marketplace') and Farmer Dashboard ('My Marketplace Listings')",
        "url": "/frontend/pages/crop-listings.html",
        "aliases": [
            "mandi", "mandi bhav", "mandi price", "bhav", "rate", "market", "sell crop", "buyer", "listings", "prices",
            "मंडी भाव", "मार्केटप्लेस", "मंडी", "बाजारभाव", "बाजार", "ભાવ", "ਮੰਡੀ", "ਭਾਅ", "ਮਾਰਕੀਟ", "বাজার দর", "দাম",
            "மண்டி", "சந்தை", "మార్కెట్", "మండి", "మಾರುಕಟ್ಟೆ", "വിപണി", "બજાર ભાવ", "منڈی", "بھاؤ"
        ],
        "purpose": "View crop mandi market rates, browse verified wholesale buyers, and list harvested crops for sale."
    },
    "disease_detection": {
        "id": "disease_detection",
        "button_name": "AI Crop Scan",
        "display_name": "Crop Disease Detection (AI Crop Scan)",
        "location": "Top navigation bar ('AI Crop Scan') and Farmer Dashboard ('Upload Crop Photo')",
        "url": "/frontend/pages/upload-crop.html",
        "aliases": [
            "disease", "bimari", "rog", "doctor", "scan", "leaf photo", "upload crop", "check disease", "crop health", "crop doctor",
            "बीमारी", "रोग", "क्रॉप स्कैन", "पत्ती", "பயிர் நோய்", "रोग", "ਰੋਗ", "ਬਿਮਾਰੀ", "রোগ", "ರೋಗ", "తెగులు", "રોગ", "بیماری"
        ],
        "purpose": "Upload or capture a leaf photo to diagnose crop diseases and review verified remedies."
    },
    "weather": {
        "id": "weather",
        "button_name": "Weather",
        "display_name": "Weather (15-Day Weather & Advisory)",
        "location": "Top navigation bar ('Weather') and Farmer Dashboard ('15-Day Weather & Advisory')",
        "url": "/frontend/pages/weather-dashboard.html",
        "aliases": [
            "weather", "mausam", "barish", "rain", "temperature", "forecast", "hawa", "spray window",
            "मौसम", "बारिश", "हवामान", "வானிலை", "వాతావరణం", "ਮੌਸਮ", "ਮੀਂਹ", "আবহাওয়া", "বৃষ্টি", "હવામાન", "ପାଣିପାଗ", "കാലാവസ്ഥ", "موسم"
        ],
        "purpose": "Check 15-day live weather forecasts, rain risk, and safe foliar spraying windows."
    },
    "crop_monitoring": {
        "id": "crop_monitoring",
        "button_name": "Crop Monitoring",
        "display_name": "Dynamic Crop Monitoring & Calendar",
        "location": "Top navigation bar ('Crop Monitoring') and Farmer Dashboard ('Dynamic Crop Monitoring')",
        "url": "/frontend/pages/crop-monitoring.html",
        "aliases": [
            "monitoring", "crop monitoring", "calendar", "timeline", "tasks", "stages", "dekhbhal",
            "निगरानी", "कैलेंडर", "पीक देखरेख", "பயிர் கண்காணிப்பு", "ਦੇਖਭਾਲ", "ਕੈਲੰਡਰ", "নজরদারি", "పర్యవేక్షణ", "മേൽനോട്ടം"
        ],
        "purpose": "Track crop growth stages from sowing to harvest and manage daily dynamic calendar tasks."
    },
    "crop_recommendation": {
        "id": "crop_recommendation",
        "button_name": "Crop Recommendations",
        "display_name": "Crop Recommendations",
        "location": "Farmer Dashboard action grid ('Crop Recommendations')",
        "url": "/frontend/pages/crop-recommendation.html",
        "aliases": [
            "recommendation", "which crop", "fasal sujhav", "crop suggest", "soil test", "crop recommendation",
            "फसल सुझाव", "पीक शिफारस", "பயிர் பரிந்துரை", "ਸਿਫ਼ਾਰਸ਼", "পরামর্শ", "సిఫార్సు", "ಶಿಫಾರಸು", "നിർദ്ദേശം"
        ],
        "purpose": "Find the best crops to grow based on your soil NPK, pH, and climate conditions."
    },
    "command_center": {
        "id": "command_center",
        "button_name": "Command Center",
        "display_name": "AI Farm Command Center",
        "location": "Top navigation bar ('⚡ Command Center') and Farmer Dashboard ('AI Farm Command Center')",
        "url": "/frontend/pages/farm-command-center.html",
        "aliases": ["command center", "mission control", "iot", "multi-signal", "decision matrix", "कमांड सेंटर"],
        "purpose": "Real-time farm mission control, virtual IoT soil telemetry, and multi-signal decision matrix."
    },
    "action_plan_trace": {
        "id": "action_plan_trace",
        "button_name": "AI Decision Trace",
        "display_name": "AI Decision Trace & Observability",
        "location": "Farmer Dashboard action grid ('AI Decision Trace & Observability')",
        "url": "/frontend/pages/action-plan-trace.html",
        "aliases": ["trace", "decision trace", "reasoning", "replan", "observability", "ट्रेस"],
        "purpose": "Inspect step-by-step reasoning traces and weather re-evaluation history."
    },
    "farmer_profile": {
        "id": "farmer_profile",
        "button_name": "Farmer Profile",
        "display_name": "Farmer Profile",
        "location": "Top navigation bar (Top Right 'Farmer Profile' badge)",
        "url": "/frontend/pages/farmer-profile.html",
        "aliases": ["profile", "my profile", "farm area", "location", "details", "प्रोफाइल", "माझी माहिती"],
        "purpose": "View and update your farm area, state, district, and village location."
    }
}

# ==============================================================================
# 4B. STEP 6: AGRIBRIDGE SCREEN & UI COMPONENT REGISTRY
# ==============================================================================

AGRIBRIDGE_SCREENS = {
    "farmer-dashboard": {
        "id": "farmer-dashboard",
        "name": "Farmer Dashboard",
        "primary_buttons": ["Upload Crop Photo", "15-Day Weather & Advisory", "Dynamic Crop Monitoring", "Crop Recommendations", "My Marketplace Listings", "AI Decision Trace & Observability"],
        "top_navbar": ["Dashboard", "Crop Monitoring", "AI Crop Scan", "Marketplace", "Weather", "Voice AI", "Command Center"],
        "primary_action_feature": "disease_detection",
        "purpose": "Central farm home dashboard showing weather alerts, active crop status, and direct buttons to all farming modules."
    },
    "upload-crop": {
        "id": "upload-crop",
        "name": "AI Crop Scan (Disease Detection)",
        "primary_buttons": ["Upload Crop Photo", "Take Photo / Camera", "Diagnose Disease / Analyze", "Back to Dashboard"],
        "top_navbar": ["Dashboard", "Crop Monitoring", "AI Crop Scan", "Marketplace", "Weather", "Voice AI", "Command Center"],
        "primary_action_feature": "disease_detection",
        "purpose": "Upload or capture leaf photos for instant AI disease diagnosis and organic/chemical remedies."
    },
    "crop-listings": {
        "id": "crop-listings",
        "name": "AgriBridge Marketplace",
        "primary_buttons": ["List New Crop", "Filter by Crop", "Direct Buyer Contact", "Back to Dashboard"],
        "top_navbar": ["Dashboard", "Crop Monitoring", "AI Crop Scan", "Marketplace", "Weather", "Voice AI", "Command Center"],
        "primary_action_feature": "marketplace",
        "purpose": "Check live mandi market rates, browse wholesale buyers, and create verified crop listings."
    },
    "crop-monitoring": {
        "id": "crop-monitoring",
        "name": "Dynamic Crop Monitoring & Calendar",
        "primary_buttons": ["State Select", "District Select", "Crop Select", "Sowing Date", "Run Monitoring Analysis"],
        "top_navbar": ["Dashboard", "Crop Monitoring", "AI Crop Scan", "Marketplace", "Weather", "Voice AI", "Command Center"],
        "primary_action_feature": "crop_monitoring",
        "purpose": "Track dynamic crop growth stages, IoT soil telemetry, and daily irrigation and fertilizer tasks."
    },
    "weather-dashboard": {
        "id": "weather-dashboard",
        "name": "Weather & Foliar Spray Advisory",
        "primary_buttons": ["Select District", "15-Day Forecast", "Safe Spray Window", "Back to Dashboard"],
        "top_navbar": ["Dashboard", "Crop Monitoring", "AI Crop Scan", "Marketplace", "Weather", "Voice AI", "Command Center"],
        "primary_action_feature": "weather",
        "purpose": "View 15-day rainfall forecasts, temperature trends, and safe foliar spraying advisory."
    },
    "crop-recommendation": {
        "id": "crop-recommendation",
        "name": "Crop Recommendations",
        "primary_buttons": ["Enter Nitrogen", "Enter Phosphorus", "Enter Potassium", "Enter pH", "Get Crop Recommendations"],
        "top_navbar": ["Dashboard", "Crop Monitoring", "AI Crop Scan", "Marketplace", "Weather", "Voice AI", "Command Center"],
        "primary_action_feature": "crop_recommendation",
        "purpose": "Get AI recommendations for the most suitable crops for your soil test values and climate."
    }
}


# ==============================================================================
# 5. MULTILINGUAL PLATFORM GUIDANCE TEMPLATES (ALL 14 LANGUAGES)
# Strict Step 2: Guides farmer to button/feature, NEVER gives internal data.
# ==============================================================================

PLATFORM_GUIDANCE_RESPONSES = {
    # Mandi / Marketplace Guidance
    "guide_marketplace": {
        "hi": "मंडी भाव देखने के लिए ऊपर दिए गए 'Marketplace' (मंडी भाव) बटन पर क्लिक करें।",
        "hinglish": "Mandi Bhav dekhne ke liye upar diye gaye 'Marketplace' (Mandi Bhav) button par click karein.",
        "en": "To check Mandi market prices, click on the 'Marketplace' button at the top.",
        "pa": "ਮੰਡੀ ਦੇ ਭਾਅ ਦੇਖਣ ਲਈ ਉੱਪਰ ਦਿੱਤੇ 'Marketplace' (ਮੰਡੀ ਭਾਅ) ਬਟਨ 'ਤੇ ਕਲਿੱਕ ਕਰੋ।",
        "mr": "बाजारभाव पाहण्यासाठी वर दिलेल्या 'Marketplace' (मार्केटप्लेस) बटणावर क्लिक करा.",
        "bn": "বাজার দর দেখতে উপরে দেওয়া 'Marketplace' (মার্কেটপ্লেস) বাটনে ক্লিক করুন।",
        "gu": "બજાર ભાવ જોવા માટે ઉપર આપેલા 'Marketplace' બટન પર ક્લિક કરો.",
        "ta": "சந்தை விலைகளைப் பார்க்க மேலே உள்ள 'Marketplace' பொத்தானைக் கிளிக் செய்யவும்.",
        "te": "మార్కెట్ ధరలను చూడటానికి పైన ఉన్న 'Marketplace' బటన్‌పై క్లిక్ చేయండి.",
        "kn": "ಮಾರುಕಟ್ಟೆ ದರಗಳನ್ನು ನೋಡಲು ಮೇಲ್ಭಾಗದಲ್ಲಿರುವ 'Marketplace' ಬಟನ್ ಕ್ಲಿಕ್ ಮಾಡಿ.",
        "ml": "വിപണി നിരക്കുകൾ കാണാൻ മുകളിലുള്ള 'Marketplace' ബട്ടണിൽ ക്ലിക്ക് ചെയ്യുക.",
        "or": "ମଣ୍ଡି ଦର ଦେଖିବା ପାଇଁ ଉପରେ ଥିବା 'Marketplace' ବଟନ୍ ଉପରେ କ୍ଲିକ୍ କରନ୍ତୁ।",
        "as": "বজাৰ দৰ চাবলৈ ওপৰত থকা 'Marketplace' বুটামত ক্লিক কৰক।",
        "ur": "منڈی کے بھاؤ دیکھنے کے لیے اوپر دیے گئے 'Marketplace' بٹن پر کلک کریں۔"
    },
    # Crop Disease Detection Guidance
    "guide_disease": {
        "hi": "फसल की बीमारी की जांच के लिए ऊपर दिए गए 'Crop Disease Detection' (AI Crop Scan) बटन पर क्लिक करें।",
        "hinglish": "Iske liye upar diye gaye 'Crop Disease Detection' (AI Crop Scan) button par click karein.",
        "en": "For crop disease detection, click on the 'AI Crop Scan' button at the top.",
        "pa": "ਫ਼ਸਲ ਦੀ ਬਿਮਾਰੀ ਦੀ ਜਾਂਚ ਲਈ ਉੱਪਰ ਦਿੱਤੇ 'AI Crop Scan' (ਬਿਮਾਰੀ ਜਾਂਚ) ਬਟਨ 'ਤੇ ਕਲਿੱਕ ਕਰੋ।",
        "mr": "पिकावरील रोगाची तपासणी करण्यासाठी वर दिलेल्या 'AI Crop Scan' बटणावर क्लिक करा.",
        "bn": "ফসলের রোগ পরীক্ষার জন্য উপরে দেওয়া 'AI Crop Scan' বাটনে ক্লিক করুন।",
        "gu": "પાકના રોગની તપાસ માટે ઉપર આપેલા 'AI Crop Scan' બટન પર ક્લિક કરો.",
        "ta": "பயிர் நோய் கண்டறிதலுக்கு மேலே உள்ள 'AI Crop Scan' பொத்தானைக் கிளிக் செய்யவும்.",
        "te": "పంట తెగుళ్ల గుర్తింపు కోసం పైన ఉన్న 'AI Crop Scan' బటన్‌పై క్లిక్ చేయండి.",
        "kn": "ಬೆಳೆ ರೋಗ ಪರೀಕ್ಷೆಗಾಗಿ ಮೇಲ್ಭಾಗದಲ್ಲಿರುವ 'AI Crop Scan' ಬಟನ್ ಕ್ಲಿಕ್ ಮಾಡಿ.",
        "ml": "വിള രോഗനിർണയത്തിനായി മുകളിലുള്ള 'AI Crop Scan' ബട്ടണിൽ ക്ലിക്ക് ചെയ്യുക.",
        "or": "ଫସଲ ରୋଗ ପରୀକ୍ଷା ପାଇଁ ଉପରେ ଥିବା 'AI Crop Scan' ବଟନ୍ ଉପରେ କ୍ଲିକ୍ କରନ୍ତୁ।",
        "as": "শস্যৰ ৰোগ পৰীক্ষাৰ বাবে ওপৰত থকা 'AI Crop Scan' বুটামত ক্লিক কৰক।",
        "ur": "فصل کی بیماری کی جانچ کے لیے اوپر دیے گئے 'AI Crop Scan' بٹن پر کلک کریں۔"
    },
    # Weather Guidance
    "guide_weather": {
        "hi": "मौसम और बारिश की जानकारी के लिए ऊपर दिए गए 'Weather' बटन पर क्लिक करें।",
        "hinglish": "Mausam aur barish dekhne ke liye upar diye gaye 'Weather' button par click karein.",
        "en": "To check weather and rain forecasts, click on the 'Weather' button at the top.",
        "pa": "ਮੌਸਮ ਅਤੇ ਮੀਂਹ ਦੀ ਜਾਣਕਾਰੀ ਲਈ ਉੱਪਰ ਦਿੱਤੇ 'Weather' ਬਟਨ 'ਤੇ ਕਲਿੱਕ ਕਰੋ।",
        "mr": "हवामान आणि पावसाचा अंदाज पाहण्यासाठी वर दिलेल्या 'Weather' बटणावर क्लिक करा.",
        "bn": "আবহাওয়া ও বৃষ্টির পূর্বাভাস দেখতে উপরে দেওয়া 'Weather' বাটনে ক্লিক করুন।",
        "gu": "હવામાન અને વરસાદની માહિતી માટે ઉપર આપેલા 'Weather' બટન પર ક્લિક કરો.",
        "ta": "வானிலை மற்றும் மழை முன்னறிவிப்பை அறிய மேலே உள்ள 'Weather' பொத்தானைக் கிளிக் செய்யவும்.",
        "te": "వాతావరణం మరియు వర్ష సూచన కోసం పైన ఉన్న 'Weather' బటన్‌పై క్లిక్ చేయండి.",
        "kn": "ಹವಾಮಾನ ಮತ್ತು ಮಳೆಯ ಮಾಹಿತಿಗಾಗಿ ಮೇಲ್ಭಾಗದಲ್ಲಿರುವ 'Weather' ಬಟನ್ ಕ್ಲಿಕ್ ಮಾಡಿ.",
        "ml": "കാലാവസ്ഥയും മഴയുടെ വിവരങ്ങളും അറിയാൻ മുകളിലുള്ള 'Weather' ബട്ടണിൽ ക്ലിക്ക് ചെയ്യുക.",
        "or": "ପାଣିପାଗ ଏବଂ ବର୍ଷା ସୂଚନା ପାଇଁ ଉପରେ ଥିବା 'Weather' ବଟନ୍ ଉପରେ କ୍ଲିକ୍ କରନ୍ତୁ।",
        "as": "বতৰ আৰু বৰষুণৰ তথ্যৰ বাবে ওপৰত থকা 'Weather' বুটামত ক্লিক কৰক।",
        "ur": "موسم اور بارش کی معلومات کے لیے اوپر دیے گئے 'Weather' بٹن پر کلک کریں۔"
    },
    # Crop Monitoring Guidance
    "guide_crop_monitoring": {
        "hi": "फसल की निगरानी और कैलेंडर देखने के लिए ऊपर दिए गए 'Crop Monitoring' बटन पर क्लिक करें।",
        "hinglish": "Fasal ki dekhbhal aur calendar dekhne ke liye upar diye gaye 'Crop Monitoring' button par click karein.",
        "en": "For stage-by-stage crop monitoring and dynamic calendar, click on the 'Crop Monitoring' button at the top.",
        "pa": "ਫ਼ਸਲ ਦੀ ਦੇਖਭਾਲ ਅਤੇ ਕੈਲੰਡਰ ਲਈ ਉੱਪਰ ਦਿੱਤੇ 'Crop Monitoring' ਬਟਨ 'ਤੇ ਕਲਿੱਕ ਕਰੋ।",
        "mr": "पीक व्यवस्थापन आणि दिनदर्शिकेसाठी वर दिलेल्या 'Crop Monitoring' बटणावर क्लिक करा.",
        "bn": "ফসলের পর্যবেক্ষণ ও ক্যালেন্ডার দেখতে উপরে দেওয়া 'Crop Monitoring' বাটনে ক্লিক করুন।",
        "gu": "પાકની દેખરેખ અને કેલેન્ડર માટે ઉપર આપેલા 'Crop Monitoring' બટન પર ક્લિક કરો.",
        "ta": "பயிர் கண்காணிப்பு மற்றும் காலெண்டருக்கு மேலே உள்ள 'Crop Monitoring' பொத்தானைக் கிளிக் செய்யவும்.",
        "te": "పంట పర్యవేక్షణ మరియు క్యాలెండర్ కోసం పైన ఉన్న 'Crop Monitoring' బటన్‌పై క్లిక్ చేయండి.",
        "kn": "ಬೆಳೆ ಮೇಲ್ವಿಚಾರಣೆ ಮತ್ತು ಕ್ಯಾಲೆಂಡರ್‌ಗಾಗಿ ಮೇಲ್ಭಾಗದಲ್ಲಿರುವ 'Crop Monitoring' ಬಟನ್ ಕ್ಲಿಕ್ ಮಾಡಿ.",
        "ml": "വിള നിരീക്ഷണത്തിനും കലണ്ടറിനുമായി മുകളിലുള്ള 'Crop Monitoring' ബട്ടണിൽ ക്ലിക്ക് ചെയ്യുക.",
        "or": "ଫସଲ ତଦାରଖ ଏବଂ କ୍ୟାଲେଣ୍ଡର ପାଇଁ ଉପରେ ଥିବା 'Crop Monitoring' ବଟନ୍ ଉପରେ କ୍ଲିକ୍ କରନ୍ତୁ।",
        "as": "শস্য নিৰীক্ষণ আৰু কেলেণ্ডাৰৰ বাবে ওপৰত থকা 'Crop Monitoring' বুটামত ক্লিক কৰক।",
        "ur": "فصل کی نگرانی اور کیلنڈر کے لیے اوپر دیے گئے 'Crop Monitoring' بٹن پر کلک کریں۔"
    },
    # Crop Recommendation Guidance
    "guide_crop_recommendation": {
        "hi": "मिट्टी के अनुसार फसल सुझाव जानने के लिए 'Crop Recommendations' बटन पर क्लिक करें।",
        "hinglish": "Mitti ke anusaar sahi fasal chunne ke liye 'Crop Recommendations' button par click karein.",
        "en": "To get crop suitability recommendations for your soil, click on the 'Crop Recommendations' button.",
        "pa": "ਮਿੱਟੀ ਅਨੁਸਾਰ ਫ਼ਸਲ ਦੀ ਸਿਫ਼ਾਰਸ਼ ਲਈ 'Crop Recommendations' ਬਟਨ 'ਤੇ ਕਲਿੱਕ ਕਰੋ।",
        "mr": "मातीनुसार योग्य पीक निवडीसाठी 'Crop Recommendations' बटणावर क्लिक करा.",
        "bn": "মাটি অনুযায়ী উপযুক্ত ফসলের পরামর্শের জন্য 'Crop Recommendations' বাটনে ক্লিক করুন।",
        "gu": "જમીન મુજબ પાકની ભલામણ માટે 'Crop Recommendations' બટન પર ક્લિક કરો.",
        "ta": "மண்ணிற்கு ஏற்ற பயிர் பரிந்துரையைப் பெற 'Crop Recommendations' பொத்தானைக் கிளிக் செய்யவும்.",
        "te": "నేల స్వభావానికి తగిన పంటల సిఫార్సుల కోసం 'Crop Recommendations' బటన్‌పై క్లిక్ చేయండి.",
        "kn": "ಮಣ್ಣಿಗೆ ಸೂಕ್ತವಾದ ಬೆಳೆ ಶಿಫಾರಸುಗಳಿಗಾಗಿ 'Crop Recommendations' ಬಟನ್ ಕ್ಲಿಕ್ ಮಾಡಿ.",
        "ml": "മണ്ണിനനുയോജ്യമായ വിള നിർദ്ദേശങ്ങൾക്കായി 'Crop Recommendations' ബട്ടണിൽ ക്ലിക്ക് ചെയ്യുക.",
        "or": "ମାଟି ଅନୁଯାୟୀ ଉପଯୁକ୍ତ ଫସଲ ପରାମର୍ଶ ପାଇଁ 'Crop Recommendations' ବଟନ୍ ଉପରେ କ୍ଲିକ୍ କରନ୍ତୁ।",
        "as": "মাটি অনুসৰি উপযুক্ত শস্যৰ পৰামৰ্শৰ বাবে 'Crop Recommendations' বুটামত ক্লিক কৰক।",
        "ur": "مٹی کے مطابق مناسب فصل کی تجاویز کے لیے 'Crop Recommendations' بٹن پر کلک کریں۔"
    },
    # Top Navbar Buttons Explanation ("Upar wala button kaunsa hai?")
    "explain_top_buttons": {
        "hi": "ऊपर दिए गए मुख्य बटन हैं: Dashboard, Crop Monitoring, AI Crop Scan, Marketplace, Weather, Voice AI और Command Center।",
        "hinglish": "Upar diye gaye main buttons hain: Dashboard, Crop Monitoring, AI Crop Scan, Marketplace, Weather, Voice AI aur Command Center.",
        "en": "The buttons at the top navigation bar are: Dashboard, Crop Monitoring, AI Crop Scan, Marketplace, Weather, Voice AI, and Command Center.",
        "pa": "ਉੱਪਰ ਦਿੱਤੇ ਮੁੱਖ ਬਟਨ ਹਨ: Dashboard, Crop Monitoring, AI Crop Scan, Marketplace, Weather, Voice AI ਅਤੇ Command Center।",
        "mr": "वर दिलेले मुख्य बटणे आहेत: Dashboard, Crop Monitoring, AI Crop Scan, Marketplace, Weather, Voice AI आणि Command Center.",
        "bn": "উপরে থাকা প্রধান বাটনগুলি হলো: Dashboard, Crop Monitoring, AI Crop Scan, Marketplace, Weather, Voice AI এবং Command Center।",
        "gu": "ઉપર આપેલા મુખ્ય બટનો છે: Dashboard, Crop Monitoring, AI Crop Scan, Marketplace, Weather, Voice AI અને Command Center.",
        "ta": "மேலே உள்ள முக்கிய பொத்தான்கள்: Dashboard, Crop Monitoring, AI Crop Scan, Marketplace, Weather, Voice AI மற்றும் Command Center.",
        "te": "పైన ఉన్న ముఖ్యమైన బటన్లు: Dashboard, Crop Monitoring, AI Crop Scan, Marketplace, Weather, Voice AI మరియు Command Center.",
        "kn": "ಮೇಲ್ಭಾಗದಲ್ಲಿರುವ ಮುಖ್ಯ ಬಟನ್‌ಗಳು: Dashboard, Crop Monitoring, AI Crop Scan, Marketplace, Weather, Voice AI ಮತ್ತು Command Center.",
        "ml": "മുകളിലുള്ള പ്രധാന ബട്ടണുകൾ: Dashboard, Crop Monitoring, AI Crop Scan, Marketplace, Weather, Voice AI, Command Center എന്നിവയാണ്.",
        "or": "ଉପରେ ଥିବା ମୁଖ୍ୟ ବଟନ୍ ଗୁଡ଼ିକ ହେଲା: Dashboard, Crop Monitoring, AI Crop Scan, Marketplace, Weather, Voice AI ଏବଂ Command Center।",
        "as": "ওপৰত থকা মূল বুটামসমূহ হ'ল: Dashboard, Crop Monitoring, AI Crop Scan, Marketplace, Weather, Voice AI আৰু Command Center।",
        "ur": "اوپر دیے گئے اہم بٹن ہیں: Dashboard, Crop Monitoring, AI Crop Scan, Marketplace, Weather, Voice AI اور Command Center۔"
    },
    # Generic "Ye button kya karta hai?" Explanation
    "explain_button_generic": {
        "hi": "यह बटन एग्रीब्रिज के मुख्य फीचर्स तक पहुँचने के लिए है। आप किसी भी विशिष्ट बटन का नाम लेकर पूछ सकते हैं!",
        "hinglish": "Yeh button AgriBridge ke main features tak pahunchne ke liye hai. Aap kisi bhi specific button ka naam lekar pooch sakte hain!",
        "en": "This button lets you access core AgriBridge features. You can ask about any specific button by name!",
        "pa": "ਇਹ ਬਟਨ ਐਗਰੀਬ੍ਰਿਜ ਦੇ ਮੁੱਖ ਫੀਚਰਾਂ ਤੱਕ ਪਹੁੰਚਣ ਲਈ ਹੈ। ਤੁਸੀਂ ਕਿਸੇ ਵੀ ਖਾਸ ਬਟਨ ਬਾਰੇ ਪੁੱਛ ਸਕਦੇ ਹੋ!",
        "mr": "हे बटण अ‍ॅग्रीब्रिजच्या मुख्य सुविधा वापरण्यासाठी आहे. आपण कोणत्याही विशिष्ट बटणाबद्दल विचारू शकता!",
        "bn": "এই বাটনটি এগ্রিব্রিজের মূল ফিচারগুলিতে যাওয়ার জন্য। আপনি যেকোনো নির্দিষ্ট বাটন সম্পর্কে জানতে চাইতে পারেন!",
        "gu": "આ બટન એગ્રીબ્રિજના મુખ્ય ફીચર્સ સુધી પહોંચવા માટે છે. તમે કોઈપણ ચોક્કસ બટન વિશે પૂછી શકો છો!",
        "ta": "இந்த பொத்தான் அக்ரிபிரிட்ஜ் அம்சங்களைப் பயன்படுத்த உதவுகிறது. நீங்கள் குறிப்பிட்ட பொத்தானைப் பற்றி கேட்கலாம்!",
        "te": "ఈ బటన్ అగ్రిబ్రిడ్జ్ ముఖ్య సేవలను ఉపయోగించడానికి తోడ్పడుతుంది. మీరు ఏదైనా నిర్దిష్ట బటన్ గురించి అడగవచ్చు!",
        "kn": "ಈ ಬಟನ್ ಅಗ್ರಿಬ್ರಿಡ್ಜ್ ಪ್ರಮುಖ ವೈಶಿಷ್ಟ್ಯಗಳನ್ನು ಬಳಸಲು ನೆರವಾಗುತ್ತದೆ. ನೀವು ನಿರ್ದಿಷ್ಟ ಬಟನ್ ಬಗ್ಗೆ ಕೇಳಬಹುದು!",
        "ml": "ഈ ബട്ടൺ അഗ്രിബ്രിഡ്ജിന്റെ പ്രധാന സേവനങ്ങൾ ഉപയോഗിക്കാനുള്ളതാണ്. നിങ്ങൾക്ക് ഏത് ബട്ടണെക്കുറിച്ചും ചോദിക്കാം!",
        "or": "ଏହି ବଟନ୍ ଏଗ୍ରିବ୍ରିଜ୍ ର ମୁଖ୍ୟ ସୁବିଧା ପାଇବା ପାଇଁ ଅଟେ। ଆପଣ ଯେକୌଣସି ନିର୍ଦ୍ଦିଷ୍ଟ ବଟନ୍ ବିଷୟରେ ପଚାରିପାରିବେ!",
        "as": "এই বুটামটো এগ্ৰিব্ৰিজৰ মূল সেৱাসমূহ ব্যৱহাৰ কৰাৰ বাবে। আপুনি যিকোনো নিৰ্দিষ্ট বুটামৰ বিষয়ে সুধিব পাৰে!",
        "ur": "یہ بٹن ایگری برج کی اہم خصوصیات تک پہنچنے کے لیے ہے۔ آپ کسی بھی خاص بٹن کا نام لے کر پوچھ سکتے ہیں!"
    }
}


# ==============================================================================
# 5B. STEP 4: CONTEXT-AWARE FOLLOW-UP RESPONSES ("Uske baad kya karna hai?")
# ==============================================================================

PLATFORM_FOLLOW_UP_RESPONSES = {
    "marketplace": {
        "hi": "मंडी भाव बटन पर क्लिक करने के बाद आप अपनी फसल का ताज़ा भाव देख सकते हैं और फसल खरीदने या बेचने के लिए लिस्टिंग देख सकते हैं।",
        "hinglish": "Mandi Bhav par click karne ke baad aap apni fasal ka daam dekh sakte hain aur fasal khareedne ya bechne ke liye listing browse kar sakte hain.",
        "en": "After clicking 'Marketplace', you can check live crop rates, browse buyer demands, or create a crop sale listing.",
        "pa": "ਮੰਡੀ ਭਾਵ 'ਤੇ ਕਲਿੱਕ ਕਰਨ ਤੋਂ ਬਾਅਦ ਤੁਸੀਂ ਆਪਣੀ ਫਸਲ ਦਾ ਭਾਵ ਦੇਖ ਸਕਦੇ ਹੋ ਅਤੇ ਫਸਲ ਵੇਚਣ ਲਈ ਲਿਸਟਿੰਗ ਬਣਾ ਸਕਦੇ ਹੋ।",
        "mr": "मंडी भाववर क्लिक केल्यानंतर आपण आपल्या पिकाचे दर पाहू शकता आणि पीक विक्रीसाठी लिस्टिंग तयार करू शकता.",
        "bn": "মান্ডি ভাবে ক্লিক করার পর আপনি ফসলের দর দেখতে পারবেন এবং ফসল বিক্রির জন্য লিস্টিং তৈরি করতে পারবেন।",
        "gu": "મંડી ભાવ પર ક્લિક કર્યા પછી તમે પાકના ભાવ જોઈ શકો છો અને પાક વેચવા માટે લિસ્ટિંગ બનાવી શકો છો.",
        "ta": "மண்டி பாவ கிளிக் செய்த பிறகு நீங்கள் பயிர் விலையைப் பார்க்கலாம் மற்றும் விற்பனை பட்டியலை உருவாக்கலாம்.",
        "te": "మండి భావ్ పై క్లిక్ చేసిన తర్వాత మీరు పంట ధరలను చూడవచ్చు మరియు అమ్మకపు జాబితాను సృష్టించవచ్చు.",
        "kn": "ಮಂಡಿ ಭಾವ್ ಮೇಲೆ ಕ್ಲಿಕ್ ಮಾಡಿದ ನಂತರ ನೀವು ಬೆಳೆ ದರಗಳನ್ನು ನೋಡಬಹುದು ಮತ್ತು ಮಾರಾಟ ಪಟ್ಟಿಯನ್ನು ರಚಿಸಬಹುದು.",
        "ml": "മണ്ടി ഭാവ് ക്ലിക്ക് ചെയ്ത ശേഷം നിങ്ങൾക്ക് വിള വിലകൾ കാണാനും വിൽപന ലിസ്റ്റിംഗ് ഉണ്ടാക്കാനും കഴിയും.",
        "or": "ମଣ୍ଡି ଭାବ୍ ଉପରେ କ୍ଲିକ୍ କରିବା ପରେ ଆପଣ ନିଜ ଫସଲର ଦର ଦେଖିପାରିବେ ଏବଂ ବିକ୍ରୟ ତାଲିକା କରିପାରିବେ।",
        "as": "মণ্ডী ভাওত ক্লিক কৰাৰ পিছত আপুনি শস্যৰ দাম চাব পাৰিব আৰু বিক্ৰীৰ বাবে তালিকা তৈয়াৰ কৰিব পাৰিব।",
        "ur": "منڈی بھاؤ پر کلک کرنے کے بعد آپ اپنی فصل کی قیمت دیکھ سکتے ہیں اور فصل فروخت کے لیے لسٹنگ بنا سکتے ہیں۔"
    },
    "disease_detection": {
        "hi": "इसके बाद 'Upload Photo' पर क्लिक करके संक्रमित पत्ती की साफ़ फ़ोटो लें और तुरंत बीमारी की पहचान पाएं।",
        "hinglish": "Iske baad 'Upload Photo' par click karke patti ki saaf photo lein aur turant bimari ki jaanch aur lakshan payein.",
        "en": "After opening AI Crop Scan, click 'Upload Photo' to take a clear photo of the infected leaf for instant AI disease identification.",
        "pa": "ਇਸ ਤੋਂ ਬਾਅਦ 'Upload Photo' 'ਤੇ ਕਲਿੱਕ ਕਰਕੇ ਪੱਤੇ ਦੀ ਸਾਫ਼ ਫੋਟੋ ਲਓ ਅਤੇ ਤੁਰੰਤ ਬਿਮਾਰੀ ਦੀ ਜਾਂਚ ਪ੍ਰਾਪਤ ਕਰੋ।",
        "mr": "त्यानंतर 'Upload Photo' वर क्लिक करून पानाचा स्वच्छ फोटो घ्या आणि त्वरित रोगाची तपासणी मिळवा.",
        "bn": "এরপর 'Upload Photo'-তে ক্লিক করে আক্রান্ত পাতার স্পষ্ট ছবি তুলে সাথে সাথে রোগ নির্ণয় করুন।",
        "ta": "அதன் பிறகு 'Upload Photo' கிளிக் செய்து இலையின் தெளிவான புகைப்படத்தை எடுத்து நோய் கண்டறியவும்.",
        "te": "ఆ తర్వాత 'Upload Photo' పై క్లిక్ చేసి ఆకు యొక్క స్పష్టమైన ఫోటోను తీసి వ్యాధి నిర్ధారణ పొందండి.",
        "gu": "ત્યારબાદ 'Upload Photo' પર ક્લિક કરીને પાંદડાનો સ્પષ્ટ ફોટો લો અને તરત જ રોગની તપાસ મેળવો.",
        "kn": "ನಂತರ 'Upload Photo' ಮೇಲೆ ಕ್ಲಿಕ್ ಮಾಡಿ ಎಲೆಯ ಸ್ಪಷ್ಟ ಫೋಟೋ ತೆಗೆದು ತಕ್ಷಣವೇ ರೋಗ ಪತ್ತೆ ಮಾಡಿ.",
        "ml": "തുടർന്ന് 'Upload Photo' ക്ലിക്ക് ചെയ്ത് ഇലയുടെ വ്യക്തമായ ഫോട്ടോയെടുത്ത് രോഗനിർണയം നടത്തുക.",
        "or": "ତାପରେ 'Upload Photo' ଉପରେ କ୍ଲିକ୍ କରି ପତ୍ରର ସ୍ପଷ୍ଟ ଫଟୋ ନିଅନ୍ତୁ ଏବଂ ତୁରନ୍ତ ରୋଗ ନିର୍ଣ୍ଣୟ ପାଆନ୍ତୁ।",
        "as": "তাৰ পিছত 'Upload Photo'ত ক্লিক কৰি পাতৰ স্পষ্ট ফটো লওক আৰু লগে লগে ৰোগ নিৰ্ণয় কৰক।",
        "ur": "اس کے بعد 'Upload Photo' پر کلک کر کے متاثرہ پتے کی واضح تصویر لیں اور فوری بیماری کی تشخیص حاصل کریں۔"
    },
    "crop_disease": {
        "hi": "इसके बाद 'Upload Photo' पर क्लिक करके संक्रमित पत्ती की साफ़ फ़ोटो लें और तुरंत बीमारी की पहचान पाएं।",
        "hinglish": "Iske baad 'Upload Photo' par click karke patti ki saaf photo lein aur turant bimari ki jaanch aur lakshan payein.",
        "en": "After opening AI Crop Scan, click 'Upload Photo' to take a clear photo of the infected leaf for instant AI disease identification.",
        "pa": "ਇਸ ਤੋਂ ਬਾਅਦ 'Upload Photo' 'ਤੇ ਕਲਿੱਕ ਕਰਕੇ ਪੱਤੇ ਦੀ ਸਾਫ਼ ਫੋਟੋ ਲਓ ਅਤੇ ਤੁਰੰਤ ਬਿਮਾਰੀ ਦੀ ਜਾਂਚ ਪ੍ਰਾਪਤ ਕਰੋ।",
        "mr": "त्यानंतर 'Upload Photo' वर क्लिक करून पानाचा स्वच्छ फोटो घ्या आणि त्वरित रोगाची तपासणी मिळवा.",
        "bn": "এরপর 'Upload Photo'-তে ক্লিক করে আক্রান্ত পাতার স্পষ্ট ছবি তুলে সাথে সাথে রোগ নির্ণয় করুন।",
        "ta": "அதன் பிறகு 'Upload Photo' கிளிக் செய்து இலையின் தெளிவான புகைப்படத்தை எடுத்து நோய் கண்டறியவும்.",
        "te": "ఆ తర్వాత 'Upload Photo' పై క్లిక్ చేసి ఆకు యొక్క స్పష్టమైన ఫోటోను తీసి వ్యాధి నిర్ధారణ పొందండి.",
        "gu": "ત્યારબાદ 'Upload Photo' પર ક્લિક કરીને પાંદડાનો સ્પષ્ટ ફોટો લો અને તરત જ રોગની તપાસ મેળવો.",
        "kn": "ನಂತರ 'Upload Photo' ಮೇಲೆ ಕ್ಲಿಕ್ ಮಾಡಿ ಎಲೆಯ ಸ್ಪಷ್ಟ ಫೋಟೋ ತೆಗೆದು ತಕ್ಷಣವೇ ರೋಗ ಪತ್ತೆ ಮಾಡಿ.",
        "ml": "തുടർന്ന് 'Upload Photo' ക്ലിക്ക് ചെയ്ത് ഇലയുടെ വ്യക്തമായ ഫോട്ടോയെടുത്ത് രോഗനിർണയം നടത്തുക.",
        "or": "ତାପରେ 'Upload Photo' ଉପରେ କ୍ଲିକ୍ କରି ପତ୍ରର ସ୍ପଷ୍ଟ ଫଟୋ ନିଅନ୍ତୁ ଏବଂ ତୁରନ୍ତ ରୋଗ ନିର୍ଣ୍ଣୟ ପାଆନ୍ତୁ।",
        "as": "তাৰ পিছত 'Upload Photo'ত ক্লিক কৰি পাতৰ স্পষ্ট ফটো লওক আৰু লগে লগে ৰোগ নিৰ্ণয় কৰক।",
        "ur": "اس کے بعد 'Upload Photo' پر کلک کر کے متاثرہ پتے کی واضح تصویر لیں اور فوری بیماری کی تشخیص حاصل کریں۔"
    },
    "weather": {
        "hi": "मौसम पेज पर आप 7 दिनों का बारिश और तापमान का पूर्वानुमान देख सकते हैं ताकि छिड़काव और सिंचाई की योजना बना सकें।",
        "hinglish": "Mausam page par aap 7 din ka barish aur taapman ka anumaan dekh sakte hain taaki kheti ke kaam ki yojana bana sakein.",
        "en": "On the Weather page, you can check the 7-day rainfall and temperature forecast to plan your farm operations.",
        "pa": "ਮੌਸਮ ਪੇਜ 'ਤੇ ਤੁਸੀਂ 7 ਦਿਨਾਂ ਦਾ ਮੀਂਹ ਅਤੇ ਤਾਪਮਾਨ ਦਾ ਅਨੁਮਾਨ ਦੇਖ ਸਕਦੇ ਹੋ।",
        "mr": "हवामान पेजवर आपण 7 दिवसांचा पाऊस आणि तापमानाचा अंदाज पाहू शकता.",
        "bn": "আবহাওয়া পেজে আপনি ৭ দিনের বৃষ্টি ও তাপমাত্রার পূর্বাভাস দেখতে পারবেন।",
        "ta": "வானிலை பக்கத்தில் 7 நாட்களுக்கான மழை மற்றும் வெப்பநிலை முன்னறிவிப்பைப் பார்க்கலாம்.",
        "te": "వాతావరణం పేజీలో మీరు 7 రోజుల వర్షపాతం మరియు ఉష్ణోగ్రత అంచనాలను చూడవచ్చు.",
        "gu": "હવામાન પેજ પર તમે 7 દિવસનો વરસાદ અને તાપમાનની આગાહી જોઈ શકો છો.",
        "kn": "ಹವಾಮಾನ ಪುಟದಲ್ಲಿ ನೀವು 7 ದಿನಗಳ ಮಳೆ ಮತ್ತು ತಾಪಮಾನದ ಮುನ್ಸೂಚನೆಯನ್ನು ನೋಡಬಹುದು.",
        "ml": "കാലാവസ്ഥ പേജിൽ നിങ്ങൾക്ക് 7 ദിവസത്തെ മഴയുടെയും താపനിലയുടെയും വിവരങ്ങൾ കാണാം.",
        "or": "ପାଣିପାଗ ପେଜ୍ ରେ ଆପଣ ୭ ଦିନର ବର୍ଷା ଏବଂ ତାପମାତ୍ରା ପୂର୍ବାନୁମାନ ଦେଖିପାରିବେ।",
        "as": "বতৰৰ পৃষ্ঠাত আপুনি ৭ দিনৰ বৰষুণ আৰু উষ্ণতাৰ পূৰ্বাভাস চাব পাৰিব।",
        "ur": "موسم پیج پر آپ 7 دن کی بارش اور درجہ حرارت کی پیش گوئی دیکھ سکتے ہیں۔"
    },
    "crop_monitoring": {
        "hi": "क्रॉप मॉनिटरिंग पेज पर अपनी फसल और बुवाई की तारीख चुनें, जहाँ आपको दैनिक सिंचाई और खाद का शेड्यूल मिलेगा।",
        "hinglish": "Crop Monitoring page par apni fasal aur boyi ki date chunein, jahan se aapko har din ka sinchai aur khad schedule milega.",
        "en": "On the Crop Monitoring page, select your crop and sowing date to view your day-by-day irrigation and fertilizer schedule.",
        "pa": "ਕ੍ਰੌਪ ਮਾਨੀਟਰਿੰਗ ਪੇਜ 'ਤੇ ਆਪਣੀ ਫਸਲ ਚੁਣੋ ਅਤੇ ਰੋਜ਼ਾਨਾ ਸਿੰਚਾਈ ਸ਼ਡਿਊਲ ਦੇਖੋ।",
        "mr": "क्रॉप मॉनिटरिंग पेजवर आपले पीक निवडून दैनंदिन सिंचन वेळापत्रक पहा.",
        "bn": "ক্রপ মনিটরিং পেজে আপনার ফসল নির্বাচন করে দৈনন্দিন সেচ ও সার সময়সূচী দেখুন।",
        "ta": "பயிர் கண்காணிப்பு பக்கத்தில் உங்கள் பயிரைத் தேர்ந்தெடுத்து பாசன அட்டவணையைப் பாருங்கள்.",
        "te": "క్రాప్ మానిటరింగ్ పేజీలో మీ పంటను ఎంచుకుని రోజువారీ సాగు షెడ్యూల్ చూడండి.",
        "gu": "ક્રોપ મોનિટરિંગ પેજ પર તમારો પાક પસંદ કરી દૈનિક સિંચાઈ શેડ્યૂલ જુઓ.",
        "kn": "ಬೆಳೆ ಮಾನಿಟರಿಂಗ್ ಪುಟದಲ್ಲಿ ನಿಮ್ಮ ಬೆಳೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ ದೈನಂದಿನ ವೇಳಾಪಟ್ಟಿಯನ್ನು ನೋಡಿ.",
        "ml": "ക്രോപ്പ് മോണിറ്ററിംഗ് പേജിൽ നിങ്ങളുടെ വിള തിരഞ്ഞെടുത്ത് നനയ്ക്കൽ ഷെഡ്യൂൾ കാണുക.",
        "or": "ଫସଲ ମନିଟରିଂ ପେଜ୍ ରେ ନିଜ ଫସଲ ଚୟନ କରି ଦୈନିକ ଜଳସେଚନ ସମୟସୂଚୀ ଦେଖନ୍ତୁ।",
        "as": "শস্য নিৰীক্ষণ পৃষ্ঠাত আপোনাৰ শস্য বাছক আৰু দৈনিক সময়সূচী চাওক।",
        "ur": "کراپ مانیٹرنگ پیج پر اپنی فصل منتخب کریں اور روزانہ آبپاشی کا شیڈول دیکھیں۔"
    },
    "crop_recommendation": {
        "hi": "इसके बाद अपनी मिट्टी का प्रकार और मौसम चुनें ताकि आपके खेत के लिए सबसे उपयुक्त फसल की जानकारी मिल सके।",
        "hinglish": "Iske baad apni mitti ka type aur mausam select karein taaki aapke khet ke liye sabse upyukt fasal ki jaankari mil sake.",
        "en": "After opening Recommendations, enter your soil type and season to get the best crop advice for your field.",
        "pa": "ਇਸ ਤੋਂ ਬਾਅਦ ਆਪਣੀ ਮਿੱਟੀ ਦੀ ਕਿਸਮ ਅਤੇ ਮੌਸਮ ਚੁਣੋ।",
        "mr": "त्यानंतर आपल्या जमिनीचा प्रकार आणि हंगाम निवडा.",
        "bn": "এরপর আপনার মাটির ধরণ ও ঋতু নির্বাচন করুন।",
        "ta": "அதன் பிறகு உங்கள் மண் வகை மற்றும் பருவத்தைத் தேர்ந்தெடுக்கவும்.",
        "te": "ఆ తర్వాత మీ నేల రకం మరియు కాలాన్ని ఎంచుకోండి.",
        "gu": "ત્યારબાદ તમારી જમીનનો પ્રકાર અને ઋતુ પસંદ કરો.",
        "kn": "ನಂತರ ನಿಮ್ಮ ಮಣ್ಣಿನ ಪ್ರಕಾರ ಮತ್ತು ಋತುವನ್ನು ಆಯ್ಕೆಮಾಡಿ.",
        "ml": "തുടർന്ന് മണ്ണിന്റെ തരവും സീസണും തിരഞ്ഞെടുക്കുക.",
        "or": "ତାପରେ ନିଜ ମାଟିର ପ୍ରକାର ଏବଂ ଋତୁ ଚୟନ କରନ୍ତୁ।",
        "as": "তাৰ পিছত আপোনাৰ মাটিৰ প্ৰকাৰ আৰু ঋতু বাছক।",
        "ur": "اس کے بعد اپنی مٹی کی قسم اور موسم منتخب کریں۔"
    }
}


# ==============================================================================
# 6. CONTEXT RESOLUTION & INTENT DETECTION
# ==============================================================================

def is_follow_up_query(text: str) -> bool:
    """Detects if farmer is asking a follow-up step query like 'Uske baad?', 'Aur iske baad kya karna hai?'"""
    if not text or not text.strip():
        return False
    lower = text.strip().lower()
    follow_up_patterns = [
        "uske baad", "iske baad", "uske bad", "iske bad", "aur iske baad", "aur uske baad",
        "phir kya", "fir kya", "aage kya", "aur aage", "phir aage", "fir aage",
        "phir kya karna", "fir kya karna", "uske baad kya", "iske baad kya",
        "what next", "what after that", "then what", "and then", "what should i do next",
        "after that", "next step", "what to do next",
        "ਉਸ ਤੋਂ ਬਾਅਦ", "ਅੱਗੇ ਕੀ", "ਫਿਰ ਕੀ", "ਉਸਤੋਂ ਬਾਅਦ",
        "त्यानंतर काय", "त्यानंतर", "पुढे काय", "त्यानंतर काय करायचे",
        "তারপরে কি", "এরপরে কি", "তারপর কি",
        "அதன் பிறகு என்ன", "அடுத்தது என்ன", "பிறகு என்ன",
        "దాని తర్వాత ఏమిటి", "తర్వాత ఏమి చేయాలి", "తర్వాత ఏమిటి",
        "ત્યારબાદ શું", "પછી શું", "ત્યારપછી",
        "ಆಮೇಲೆ ಏನು", "ನಂತರ ಏನು", "ಮುಂದೆ ಏನು",
        "അതിനുശേഷം എന്ത്", "പിന്നെ എന്ത്",
        "ତାପରେ କଣ", "ଆଗକୁ କଣ",
        "তাৰ পিছত কি", "আগলৈ কি",
        "اس کے بعد کیا", "پھر کیا"
    ]
    return any(p in lower for p in follow_up_patterns)


# ==============================================================================
# 5C. STEP 5: STEP-BY-STEP GUIDED PLATFORM NAVIGATION WORKFLOWS
# ==============================================================================

GUIDED_WORKFLOW_STEPS = {
    "disease_detection": [
        {
            "step": 1,
            "hi": "जी, ऊपर दिए गए 'AI Crop Scan' बटन पर क्लिक करें।",
            "hinglish": "Ji, upar diye gaye 'AI Crop Scan' button par click karein.",
            "en": "Please click on the 'AI Crop Scan' button at the top.",
            "pa": "ਜੀ, ਉੱਪਰ ਦਿੱਤੇ 'AI Crop Scan' ਬਟਨ 'ਤੇ ਕਲਿੱਕ ਕਰੋ।",
            "mr": "होय, वर दिलेल्या 'AI Crop Scan' बटणावर क्लिक करा."
        },
        {
            "step": 2,
            "hi": "अब अपनी फसल की प्रभावित पत्ती की साफ़ फ़ोटो अपलोड करें।",
            "hinglish": "Ab apni crop ki patti ki saaf photo upload karein.",
            "en": "Now upload a clear photo of your infected crop leaf.",
            "pa": "ਹੁਣ ਆਪਣੀ ਫਸਲ ਦੇ ਪੱਤੇ ਦੀ ਸਾਫ਼ ਫੋਟੋ ਅਪਲੋਡ ਕਰੋ।",
            "mr": "आता आपल्या पिकाच्या पानाचा स्वच्छ फोटो अपलोड करा."
        },
        {
            "step": 3,
            "hi": "अब नीचे दिए गए 'Analyze' बटन पर क्लिक करें।",
            "hinglish": "Ab 'Analyze' button par click karein.",
            "en": "Now click on the 'Analyze' button below.",
            "pa": "ਹੁਣ ਹੇਠਾਂ ਦਿੱਤੇ 'Analyze' ਬਟਨ 'ਤੇ ਕਲਿੱਕ ਕਰੋ।",
            "mr": "आता खाली दिलेल्या 'Analyze' बटणावर क्लिक करा."
        },
        {
            "step": 4,
            "hi": "शानदार! अब स्क्रीन पर बीमारी का नाम, पहचान का प्रतिशत और उपचार सलाह देख सकते हैं।",
            "hinglish": "Bahut badhiya! Ab screen par bimari ka naam aur ilaj ke sujhav dekh sakte hain.",
            "en": "Great! You can now view the detected disease name and treatment advice on screen.",
            "pa": "ਬਹੁਤ ਵਧੀਆ! ਹੁਣ ਤੁਸੀਂ ਸਕ੍ਰੀਨ 'ਤੇ ਬਿਮਾਰੀ ਦਾ ਨਾਮ ਅਤੇ ਇਲਾਜ ਦੇਖ ਸਕਦੇ ਹੋ।",
            "mr": "छान! आता आपण स्क्रीनवर रोगाचे नाव आणि उपाय पाहू शकता."
        }
    ],
    "marketplace": [
        {
            "step": 1,
            "hi": "मंडी भाव देखने के लिए ऊपर दिए गए 'Marketplace' बटन पर क्लिक करें।",
            "hinglish": "Mandi Bhav dekhne ke liye upar diye gaye 'Marketplace' button par click karein.",
            "en": "Click on the 'Marketplace' button at the top.",
            "pa": "ਮੰਡੀ ਭਾਵ ਦੇਖਣ ਲਈ ਉੱਪਰ ਦਿੱਤੇ 'Marketplace' ਬਟਨ 'ਤੇ ਕਲਿੱਕ ਕਰੋ।",
            "mr": "मंडी भाव पाहण्यासाठी वर दिलेल्या 'Marketplace' बटणावर क्लिक करा."
        },
        {
            "step": 2,
            "hi": "यहाँ आप लाइव मंडी भाव देख सकते हैं। फसल बेचने के लिए 'List New Crop' बटन दबाएं।",
            "hinglish": "Yahan aap live mandi rate dekh sakte hain. Fasal bechne ke liye 'List New Crop' button par click karein.",
            "en": "Here you can see live market rates. To sell crops, click 'List New Crop'.",
            "pa": "ਇੱਥੇ ਤੁਸੀਂ ਮੰਡੀ ਭਾਵ ਦੇਖ ਸਕਦੇ ਹੋ। ਫਸਲ ਵੇਚਣ ਲਈ 'List New Crop' ਬਟਨ ਦਬਾਓ।",
            "mr": "येथे आपण बाजारभाव पाहू शकता. पीक विक्रीसाठी 'List New Crop' बटण दाबा."
        },
        {
            "step": 3,
            "hi": "अब फसल का नाम, मात्रा और भाव भरकर 'Submit' पर क्लिक करें।",
            "hinglish": "Ab fasal ka naam, quantity aur daam bharkar 'Submit Listing' par click karein.",
            "en": "Now enter crop details and click 'Submit Listing'.",
            "pa": "ਹੁਣ ਫਸਲ ਦਾ ਨਾਮ, ਮਾਤਰਾ ਅਤੇ ਭਾਅ ਭਰ ਕੇ 'Submit' 'ਤੇ ਕਲਿੱਕ ਕਰੋ।",
            "mr": "आता पिकाचे नाव, वजन आणि भाव भरून 'Submit' वर क्लिक करा."
        }
    ],
    "crop_monitoring": [
        {
            "step": 1,
            "hi": "फसल की निगरानी के लिए ऊपर दिए गए 'Crop Monitoring' बटन पर क्लिक करें।",
            "hinglish": "Fasal ki dekhbhal ke liye upar diye gaye 'Crop Monitoring' button par click karein.",
            "en": "Click on the 'Crop Monitoring' button at the top.",
            "pa": "ਫ਼ਸਲ ਦੀ ਦੇਖਭਾਲ ਲਈ 'Crop Monitoring' ਬਟਨ 'ਤੇ ਕਲਿੱਕ ਕਰੋ।",
            "mr": "पिकाच्या देखरेखीसाठी 'Crop Monitoring' बटणावर क्लिक करा."
        },
        {
            "step": 2,
            "hi": "अब अपना राज्य (State), जिला (District) और अपनी फसल का नाम चुनें।",
            "hinglish": "Ab apna State, District aur apni fasal select karein.",
            "en": "Now select your State, District, and your crop name.",
            "pa": "ਹੁਣ ਆਪਣਾ ਰਾਜ, ਜ਼ਿਲ੍ਹਾ ਅਤੇ ਫਸਲ ਚੁਣੋ।",
            "mr": "आता आपले राज्य, जिल्हा आणि पिकाचे नाव निवडा."
        },
        {
            "step": 3,
            "hi": "अब बुवाई की तारीख चुनें और 'Analyze' बटन पर क्लिक करें।",
            "hinglish": "Ab boyi (planting date) select karke 'Analyze' button par click karein.",
            "en": "Now select your sowing date and click 'Analyze'.",
            "pa": "ਹੁਣ ਬਿਜਾਈ ਦੀ ਤਾਰੀਖ ਚੁਣ ਕੇ 'Analyze' ਬਟਨ 'ਤੇ ਕਲਿੱਕ ਕਰੋ।",
            "mr": "आता पेरणीची तारीख निवडून 'Analyze' बटणावर क्लिक करा."
        },
        {
            "step": 4,
            "hi": "बहुत अच्छे! अब आप खेत का लाइव मौसम, सिंचाई और खाद का दैनिक शेड्यूल देख सकते हैं।",
            "hinglish": "Bahut achhe! Ab aap khet ka live mausam, sinchai aur khad ka schedule dekh sakte hain.",
            "en": "Excellent! You can now view live farm weather, irrigation, and fertilizer schedule.",
            "pa": "ਬਹੁਤ ਵਧੀਆ! ਹੁਣ ਤੁਸੀਂ ਖੇਤ ਦਾ ਮੌਸਮ ਅਤੇ ਸਿੰਚਾਈ ਸ਼ਡਿਊਲ ਦੇਖ ਸਕਦੇ ਹੋ।",
            "mr": "छान! आता आपण शेताचे हवामान आणि सिंचनाचे वेळापत्रक पाहू शकता."
        }
    ]
}


# ==============================================================================
# 6. CONTEXT RESOLUTION & GUIDED INTENT DETECTION
# ==============================================================================

def is_follow_up_query(text: str) -> bool:
    """Detects if farmer is asking a follow-up step query like 'Uske baad?', 'Aur iske baad kya karna hai?'"""
    if not text or not text.strip():
        return False
    lower = text.strip().lower()
    follow_up_patterns = [
        "uske baad", "iske baad", "uske bad", "iske bad", "aur iske baad", "aur uske baad",
        "phir kya", "fir kya", "aage kya", "aur aage", "phir aage", "fir aage",
        "phir kya karna", "fir kya karna", "uske baad kya", "iske baad kya",
        "what next", "what after that", "then what", "and then", "what should i do next",
        "after that", "next step", "what to do next",
        "ਉਸ ਤੋਂ ਬਾਅਦ", "ਅੱਗੇ ਕੀ", "ਫਿਰ ਕੀ", "ਉਸਤੋਂ ਬਾਅਦ",
        "त्यानंतर काय", "त्यानंतर", "पुढे काय", "त्यानंतर काय करायचे",
        "তারপরে কি", "এরপরে কি", "তারপর কি",
        "அதன் பிறகு என்ன", "அடுத்தது என்ன", "பிறகு என்ன",
        "దాని తర్వాత ఏమిటి", "తర్వాత ఏమి చేయాలి", "తర్వాత ఏమిటి",
        "ત્યારબાદ શું", "પછી શું", "ત્યારપછી",
        "ಆಮೇಲೆ ಏನು", "ನಂತರ ಏನು", "ಮುಂದೆ ಏನು",
        "അതിനുശേഷം എന്ത്", "പിന്നെ എന്ത്",
        "ତାପରେ କଣ", "ଆଗକୁ କଣ",
        "তাৰ পিছত কি", "আগলৈ কি",
        "اس کے بعد کیا", "پھر کیا"
    ]
    return any(p in lower for p in follow_up_patterns)


def is_progress_ack(text: str) -> bool:
    """Detects natural responses confirming a step was performed (e.g. 'Kar diya', 'Upload kar diya', 'Ho gaya')"""
    if not text or not text.strip():
        return False
    lower = text.strip().lower()
    ack_patterns = [
        "kar diya", "ho gaya", "kardiya", "hogaya", "kar liya", "karliya",
        "mil gaya", "milgaya", "mil gya", "milgya", "dikh gaya", "dikhgaya",
        "upload kar diya", "upload kardiya", "upload kar liya", "upload karliya",
        "click kar diya", "click kardiya", "open kar liya", "open kar diya",
        "photo daal di", "photo daaldi", "photo upload kar di", "daal diya", "daaldiya",
        "done", "yes done", "i did it", "completed", "uploaded", "i have uploaded",
        "select kar liya", "select kardiya", "bhar diya", "bhardiya", "found it", "got it",
        "ਕਰ ਦਿੱਤਾ", "ਹੋ ਗਿਆ", "ਕਰ ਲਿਆ", "ਅਪਲੋਡ ਕਰ ਦਿੱਤਾ", "ਮਿਲ ਗਿਆ",
        "झाले", "केले", "अपलोड केले", "मिळाले",
        "முடிந்தது", "செய்துவிட்டேன்", "கிடைத்துவிட்டது",
        "అయిపోయింది", "చేశాను", "దొరికింది",
        "হয়ে গেছে", "করেছি", "পেয়েছি",
        "થઈ ગયું", "કરી દીધું", "મળી ગયું"
    ]
    return any(p in lower for p in ack_patterns)


def is_trouble_query(text: str) -> Optional[str]:
    """Detects troubleshooting, confusion, interruptions, and out-of-scope inquiries."""
    if not text or not text.strip():
        return None
    lower = text.strip().lower()

    # Step 10 Personalised Session Context Triggers
    if any(p in lower for p in [
        "ye option mujhe nahi chahiye", "ye nahi chahiye", "doosra wala batao", "doosra option",
        "dusra option", "kuch aur batao", "alternative", "ਦੂਜਾ ਆਪਸ਼ਨ", "ਦੂਜਾ ਵਿਕਲਪ", "दुसरा पर्याय",
        "दुसरा ऑप्शन", "మరొకటి", "வேறొன்று", "অন্য অপশন"
    ]):
        return "suggest_alternative_option"
    if any(p in lower for p in [
        "pehle wala kaise kholna", "pehle wala option", "pehle wala button", "pehle wala kahan",
        "previous option", "ਪਹਿਲਾਂ ਵਾਲਾ", "ਪਹਿਲਾ ਵਾਲਾ", "आधीचा पर्याय", "आधीचा ऑप्शन", "మునుపటి", "முந்தைய", "পূর্বের"
    ]):
        return "recall_previous_option"
    if any(p in lower for p in [
        "vistaar se", "detail mein", "detail se", "explain in detail", "poora samjhao", "in detail",
        "ਵਿਸਤਾਰ ਨਾਲ", "तपशीलवार", "వివరంగా", "விரிவாக", "বিস্তারিত"
    ]):
        return "detailed_explanation_request"

    if any(p in lower for p in ["photo upload nahi ho rahi", "photo nahi upload", "image upload error", "photo upload nahi hui"]):
        return "photo_upload_error"
    if any(p in lower for p in ["page atak gaya", "atak gaya hai", "page stuck", "kuch ho nahi raha", "screen atak gayi"]):
        return "page_stuck"
    if any(p in lower for p in ["main doosre page", "doosre page par", "doosre page pe", "page badal gaya", "naye page par"]):
        return "page_switched"
    if any(p in lower for p in ["ruko", "pehle ye batao", "pehle yeh batao", "ek minute", "hold on", "wait"]):
        return "interruption_pause"
    if any(p in lower for p in ["accha samajh gaya", "samajh gaya", "theek hai ji", "haan theek hai", "got it thanks"]):
        return "warm_acknowledgment"
    if any(p in lower for p in ["nahi mera matlab", "wo wala button", "wo nahi", "doosra wala"]):
        return "correction_clarification"
    if any(p in lower for p in ["samajh nahi aa raha", "samajh nahi aaya", "kuch samajh nahi", "kuch samajh nahi aa raha", "not understanding", "i don't understand", "don't understand", "समझ नहीं आ रहा", "समजत नाही", "ਸਮਝ ਨਹੀਂ ਆ ਰਿਹਾ"]):
        return "confused_need_simplification"
    if any(p in lower for p in ["button nahi mil raha", "button nahi dikh raha", "kahan hai button", "cannot find button", "where is button", "ye wala nahi mil raha", "बटन नहीं मिल रहा", "बटन कहाँ है"]):
        return "cannot_find_button"
    if any(p in lower for p in ["galti se", "doosra page khul gaya", "galat page khul gaya", "galat option dab gaya", "galat button dab gaya", "wapas jaana hai", "wapas jana hai", "wrong page", "go back", "गलती से कुछ और खुल गया", "वापस जाना है"]):
        return "wrong_page_opened"
    if any(p in lower for p in ["kahan click karu", "kahan click karein", "kahan jaana hai", "kidhar jana hai", "isme kya karna hai", "ab kya karna hai", "ab kya", "where to go", "where to click"]):
        return "where_to_click"
    if any(p in lower for p in ["bhai ye kya hai", "bhai yeh kya hai", "ye kya hai", "yeh kya hai", "what is this", "ये क्या है"]):
        return "what_is_this"
    if any(p in lower for p in ["nahi ho raha", "kuch nahi ho raha", "error aa raha", "not working", "नहीं हो रहा"]):
        return "not_working"

    # Out-of-scope agricultural questions redirection triggers
    if any(p in lower for p in ["kaun sa khad", "kitna khad", "fertilizer dose", "pesticide dose", "kaunsi davai", "kaun si davai", "aaj mandi mein bhav", "aaj ka rate"]):
        return "out_of_scope_fertilizer"

    return None


def resolve_conversation_context(history: Optional[List[Dict[str, str]]]) -> Optional[str]:
    """
    Scans recent conversation history backwards to determine the active feature being discussed.
    Returns feature_id (e.g. 'marketplace', 'disease_detection', 'weather', 'crop_monitoring') or None.
    """
    if not history:
        return None

    for turn in reversed(history):
        txt = (turn.get("text") or turn.get("message") or turn.get("response") or "").lower()
        if not txt:
            continue
        for feat_id, feat in PLATFORM_FEATURES.items():
            for alias in feat["aliases"] + [feat["button_name"].lower()]:
                if alias in txt:
                    return feat_id

    return None


def get_guided_workflow_next_step(feature_id: str, history: Optional[List[Dict[str, str]]], user_text: str) -> int:
    """
    Determines the next guided step number (1, 2, 3, 4) based on past turns and user's utterance.
    """
    if feature_id not in GUIDED_WORKFLOW_STEPS:
        return 1

    steps = GUIDED_WORKFLOW_STEPS[feature_id]
    total_steps = len(steps)
    u_lower = user_text.lower()

    # Fast-forward based on user explicit action keywords
    if feature_id in ["disease_detection", "crop_disease"] and any(p in u_lower for p in ["upload kar diya", "photo daal di", "upload kardiya", "uploaded", "photo le li"]):
        return 3
    if feature_id in ["disease_detection", "crop_disease"] and any(p in u_lower for p in ["analyze kar diya", "analyze par click", "diagnose kar diya"]):
        return 4

    # Scan history backwards to see which step Saathi previously sent
    last_assistant_text = ""
    if history:
        for turn in reversed(history):
            if turn.get("role") in ["assistant", "bot", "saathi"] or turn.get("response"):
                last_assistant_text = (turn.get("text") or turn.get("response") or turn.get("message") or "").lower()
                break

    if not last_assistant_text:
        return 2

    # Disease Detection Workflow step detection
    if feature_id in ["disease_detection", "crop_disease"]:
        if "analyze" in last_assistant_text or "diagnose" in last_assistant_text:
            return 4
        elif "photo" in last_assistant_text or "upload" in last_assistant_text or "patti" in last_assistant_text:
            return 3
        else:
            return 2

    # Marketplace Workflow step detection
    if feature_id == "marketplace":
        if "quantity" in last_assistant_text or "submit" in last_assistant_text or "daam bharkar" in last_assistant_text:
            return 3
        elif "list new crop" in last_assistant_text or "fasal bechne" in last_assistant_text:
            return 3
        else:
            return 2

    # Crop Monitoring Workflow step detection
    if feature_id == "crop_monitoring":
        if "planting date" in last_assistant_text or "analyze" in last_assistant_text or "boyi" in last_assistant_text:
            return 4
        elif "district" in last_assistant_text or "state" in last_assistant_text or "rajya" in last_assistant_text or "fasal" in last_assistant_text:
            return 3
        else:
            return 2

    return 2


def detect_platform_navigation_intent(
    text: str,
    current_page: Optional[str] = None,
    available_buttons: Optional[List[str]] = None,
    focused_button: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None
) -> Optional[Tuple[str, Optional[str]]]:
    """
    Identifies whether the farmer's question is asking for:
    1. Step-by-step progress acknowledgment ("Kar diya", "Upload kar diya", "Ho gaya") -> Step 5 Guided Navigation
    2. Troubleshooting / Trouble query ("Button nahi mil raha", "Galti se kuch aur open ho gaya")
    3. Direct feature request ("Mujhe crop disease check karna hai")
    4. Follow-up query ("Uske baad?", "Aur iske baad kya karna hai?")
    5. What a button does ("Ye button kya karta hai?")
    6. What buttons are on screen ("Upar wala button kaunsa hai?")
    
    Returns: (intent_type, feature_or_button_id)
    """
    if not text or not text.strip():
        return None

    clean = text.strip()
    lower = clean.lower()

    # A. Step 5 Troubleshooting Queries
    trouble = is_trouble_query(clean)
    if trouble:
        ctx_feat = resolve_conversation_context(history)
        return (f"trouble_{trouble}", ctx_feat)

    # B. Step 5 Step Progress Acknowledgment ("Kar diya", "Ho gaya", "Upload kar diya")
    if is_progress_ack(clean):
        ctx_feat = resolve_conversation_context(history)
        if ctx_feat:
            return ("step_progress_ack", ctx_feat)
        return ("step_progress_generic", None)

    # C. Step 4 Context-Aware Follow-up Intent ("Uske baad?", "Aur iske baad kya karna hai?")
    if is_follow_up_query(clean):
        ctx_feat = resolve_conversation_context(history)
        if ctx_feat:
            return ("follow_up", ctx_feat)
        return ("follow_up_generic", None)

    # D. Top Navbar Buttons Overview & Guidance ("Upar wala button kaunsa hai?", "Mujhe upar wala button dabana hai?")
    top_button_triggers = [
        "upar wala button", "upar wale button", "upar kaunsa button", "top button", "navbar button",
        "screen par kaunse button", "page par kaunse button", "buttons on screen", "buttons at the top",
        "upar wala button dabana", "upar wala dabana", "top navbar button",
        "ऊपर वाला बटन", "ऊपर कौन सा बटन", "स्क्रीन पर कौन से बटन", "वरचे बटण", "ਉੱਪਰ ਵਾਲਾ ਬਟਨ",
        "పైనున్న బటన్", "மேலே உள்ள பொத்தான்", "ওপৰৰ বুটাম"
    ]
    if any(t in lower for t in top_button_triggers):
        return ("explain_top_buttons", None)

    # E. Screen-Specific Feature Locator ("Mandi Bhav ka option mujhe nahi dikh raha", "Option nahi mil raha")
    if any(t in lower for t in ["nahi dikh raha", "nahi mil raha", "kahan par hai", "kahan dikhega", "where can i find"]):
        for feat_id, feat in PLATFORM_FEATURES.items():
            for alias in feat["aliases"] + [feat["button_name"].lower()]:
                if alias in lower:
                    return ("screen_locate_feature", feat_id)

    # F. Check for "Ye button kya karta hai?" / What does this button do?
    explain_triggers = [
        "ye button kya karta hai", "yeh button kya karta hai", "is button se kya hota hai",
        "what does this button do", "what is this button for", "button ka kaam kya hai",
        "ye kya karta hai", "yeh kya karta hai",
        "ये बटन क्या करता है", "इस बटन से क्या होता है", "हे बटण काय करते", "ਇਹ ਬਟਨ ਕੀ ਕਰਦਾ ਹੈ",
        "ఈ బటన్ ఏమి చేస్తుంది", "இந்த பொத்தான் என்ன செய்கிறது"
    ]
    is_explain_query = any(t in lower for t in explain_triggers)

    # Check if a specific button is mentioned directly in query
    for feat_id, feat in PLATFORM_FEATURES.items():
        for alias in feat["aliases"] + [feat["button_name"].lower()]:
            if alias in lower:
                if is_explain_query or "kya karta hai" in lower or "what does" in lower:
                    return ("explain_button", feat_id)
                return ("guide_feature", feat_id)

    # If farmer asks "Ye button kya karta hai?" with focused_button or screen context
    if is_explain_query:
        if focused_button:
            f_lower = focused_button.lower()
            for feat_id, feat in PLATFORM_FEATURES.items():
                if feat["button_name"].lower() in f_lower or any(a in f_lower for a in feat["aliases"]):
                    return ("explain_button", feat_id)
        if current_page and current_page in AGRIBRIDGE_SCREENS:
            page_info = AGRIBRIDGE_SCREENS[current_page]
            return ("explain_screen_action", page_info["primary_action_feature"])
        ctx_feat = resolve_conversation_context(history)
        if ctx_feat:
            return ("explain_button", ctx_feat)
        return ("explain_button_generic", None)

    return None


# ==============================================================================
# 7. CONVERSATIONAL FALLBACK TEMPLATES (GREETING, IDENTITY, ETC.)
# ==============================================================================

CONVERSATIONAL_TEMPLATES = {
    "greeting": {
        "hi": "नमस्ते जी! मैं साथी हूँ। आप कैसे हैं? सब कुशल-मंगल?",
        "hinglish": "Namaste ji! Main Saathi hoon. Aap kaise hain? Sab theek-thaak?",
        "en": "Hello! I am Saathi. How are you doing today?",
        "pa": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ ਜੀ! ਮੈਂ ਸਾਥੀ ਹਾਂ। ਤੁਸੀਂ ਕਿਵੇਂ ਹੋ? ਸਭ ਠੀਕ-ਠਾਕ ਹੈ?",
        "mr": "नमस्कार जी! मी साथी आहे. आपण कसे आहात? सर्व काही कुशल आहे ना?",
        "bn": "নমস্কার! আমি সাথী। আপনি কেমন আছেন? সব ঠিক আছে তো?",
        "gu": "નમસ્તે જી! હું સાથી છું. તમે કેમ છો? બધું બરાબર છે ને?",
        "ta": "வணக்கம்! நான் சாதி. எப்படி இருக்கிறீர்கள்? எல்லாம் நலமா?",
        "te": "నమస్కారం అండి! నేను సాథి. మీరు ఎలా ఉన్నారు? అంతా బాగుందా?",
        "kn": "ನಮಸ್ಕಾರ! ನಾನು ಸಾಥಿ. ನೀವು ಹೇಗಿದ್ದೀರಿ? ಎಲ್ಲವೂ ಆರಾಮವೇ?",
        "ml": "നമസ്കാരം! ഞാൻ സാഥി. സുഖമാണോ? വിശേഷങ്ങൾ എന്തൊക്കെ?",
        "or": "ନମସ୍କାର ଜୀ! ମୁଁ ସାଥୀ। ଆପଣ କେମିତି ଅଛନ୍ତି? ସବୁ ଠିକ୍ ତ?",
        "as": "নমস্কাৰ! মই সাথী। আপোনাৰ খবৰ কেনে? সকলো ভালেই নে?",
        "ur": "سلام جی! میں ساتھی ہوں۔ آپ کیسے ہیں؟ سب خیریت ہے؟"
    },
    "identity": {
        "hi": "मैं साथी हूँ। आपका डिजिटल दोस्त, जो एग्रीब्रिज ऐप को समझने और सही बटन तक पहुँचने में आपकी मदद करता है।",
        "hinglish": "Main Saathi hoon. Aapka digital sathi, jo AgriBridge app ko samajhne aur sahi button tak pahunchne mein aapki madad karta hai.",
        "en": "I am Saathi, your conversational guide. I help you navigate and use all the features of AgriBridge.",
        "pa": "ਮੈਂ ਸਾਥੀ ਹਾਂ। ਤੁਹਾਡਾ ਡਿਜੀਟਲ ਦੋਸਤ, ਜੋ ਐਗਰੀਬ੍ਰਿਜ ਐਪ ਦੇ ਫੀਚਰਾਂ ਨੂੰ ਸਮਝਣ ਵਿੱਚ ਤੁਹਾਡੀ ਮਦਦ ਕਰਦਾ ਹਾਂ।",
        "mr": "मी साथी आहे. आपला डिजिटल मार्गदर्शक, जो अ‍ॅग्रीब्रिज अ‍ॅप वापरण्यात आपल्याला मदत करतो.",
        "bn": "আমি সাথী। আপনার ডিজিটাল গাইড, যিনি এগ্রিব্রিজ অ্যাপ ব্যবহার করতে আপনাকে সাহায্য করেন।",
        "gu": "હું સાથી છું. તમારો ડિજિટલ માર્ગદર્શક, જે એગ્રીબ્રિજ એપ વાપરવામાં તમારી મદદ કરે છે.",
        "ta": "நான் சாதி. அக்ரிபிரிட்ஜ் செயலியைப் பயன்படுத்த உங்களுக்கு உதவும் உங்கள் தோழன்.",
        "te": "నేను సాథిని. అగ్రిబ్రిడ్జ్ యాప్‌ను ఉపయోగించడంలో మీకు సహాయపడే మీ డిజిటల్ స్నేహితుడిని.",
        "kn": "ನಾನು ಸಾಥಿ. ಅಗ್ರಿಬ್ರಿಡ್ಜ್ ಆ್ಯಪ್ ಬಳಸಲು ನಿಮಗೆ ನೆರವಾಗುವ ಒಡನಾಡಿ.",
        "ml": "ഞാൻ സാഥിയാണ്. അഗ്രിബ്രിഡ്ജ് ആപ്പ് എളുപ്പത്തിൽ ഉപയോഗിക്കാൻ സഹായിക്കുന്ന കൂട്ടുകാരൻ.",
        "or": "ମୁଁ ସାଥୀ। ଆପଣଙ୍କ ଡିଜିଟାଲ୍ ସାଥୀ, ଯିଏ ଏଗ୍ରିବ୍ରିଜ୍ ଆପ୍ ବ୍ୟବହାର କରିବାରେ ସାହାଯ୍ୟ କରେ।",
        "as": "মই সাথী। এগ্ৰিব্ৰিজ এপ্ ব্যৱহাৰ কৰাত সহায় কৰা আপোনাৰ ডিজিটেল বন্ধু।",
        "ur": "میں ساتھی ہوں۔ آپ کا ڈیجیٹل دوست، جو ایگری برج ایپ استعمال کرنے میں آپ کی مدد کرتا ہے۔"
    },
    "status_check": {
        "hi": "मैं बहुत अच्छा हूँ, धन्यवाद! आप बताइए, आपका दिन कैसा बीत रहा है?",
        "hinglish": "Main bilkul badhiya hoon, shukriya! Aap bataiye, aapka din kaisa chal raha hai?",
        "en": "I am doing well, thank you! How has your day been?",
        "pa": "ਮੈਂ ਬਿਲਕੁਲ ਵਧੀਆ ਹਾਂ, ਧੰਨਵਾਦ! ਤੁਸੀਂ ਦੱਸੋ, ਤੁਹਾਡਾ ਦਿਨ ਕਿਵੇਂ ਚੱਲ ਰਿਹਾ ਹੈ?",
        "mr": "मी अगदी मजेत आहे, धन्यवाद! आपण सांगा, आपला दिवस कसा चालू आहे?",
        "bn": "আমি খুব ভালো আছি, ধন্যবাদ! আপনার দিন কেমন কাটছে বলুন?",
        "gu": "હું મજામાં છું, આભાર! તમે કહો, તમારો દિવસ કેવો ચાલે છે?",
        "ta": "நான் நன்றாக இருக்கிறேன், நன்றி! உங்கள் நாள் எப்படி செல்கிறது என்று சொல்லுங்கள்?",
        "te": "నేను చాలా బాగున్నాను, ధన్యవాదాలు! మీ రోజు ఎలా గడుస్తుందో చెప్పండి?",
        "kn": "ನಾನು ಚೆನ್ನಾಗಿದ್ದೇನೆ, ಧನ್ಯವಾದಗಳು! ನಿಮ್ಮ ದಿನ ಹೇಗಿದೆ ಎಂದು ತಿಳಿಸಿ?",
        "ml": "എനിക്ക് സുഖമാണ്, നന്ദി! നിങ്ങളുടെ ഇന്നത്തെ വിശേഷങ്ങൾ എന്തൊക്കെയാണ്?",
        "or": "ମୁଁ ବହୁତ ଭଲରେ ଅଛି, ଧନ୍ୟବାଦ! ଆପଣଙ୍କ ଦିନ କିପରି ଚାଲିଛି କୁହନ୍ତୁ?",
        "as": "মই ভালে আছোঁ, ধন্যবাদ! আপোনাৰ দিনটো কেনে চলিছে কওকচোন?",
        "ur": "میں بالکل ٹھیک ہوں، شکریہ! آپ بتائیے، آپ کا دن کیسا گزر رہا ہے؟"
    },
    "listening_ack": {
        "hi": "जी, मैं सुन रहा हूँ। आप अपनी बात कहिए।",
        "hinglish": "Haan ji, main sun raha hoon. Aap bilkul aaram se boliye.",
        "en": "Yes, I am listening. Please go ahead.",
        "pa": "ਹਾਂਜੀ, ਮੈਂ ਸੁਣ ਰਿਹਾ ਹਾਂ। ਤੁਸੀਂ ਖੁੱਲ੍ਹ ਕੇ ਆਪਣੀ ਗੱਲ ਕਹੋ।",
        "mr": "होय, मी ऐकत आहे. आपण मनमोकळेपणाने बोला.",
        "bn": "হ্যাঁ, আমি শুনছি। আপনি নিশ্চিন্তে বলুন।",
        "gu": "હા, હું સાંભળી રહ્યો છું. તમે તમારી વાત કહો.",
        "ta": "ஆம், நான் கேட்கிறேன். தயங்காமல் பேசுங்கள்.",
        "te": "అవును, నేను వింటున్నాను. నిరభ్యంతరంగా చెప్పండి.",
        "kn": "ಹೌದು, ನಾನು ಕೇಳಿಸಿಕೊಳ್ಳುತ್ತಿದ್ದೇನೆ. ದಯವಿಟ್ಟು ಮುಂದುವರಿಯಿರಿ.",
        "ml": "അതെ, ഞാൻ കേൾക്കുന്നുണ്ട്. താങ്കൾ പറയൂ.",
        "or": "ହଁ, ମୁଁ ଶୁଣୁଛି। ଆପଣ ନିଜ କଥା କୁହନ୍ତୁ।",
        "as": "হয়, মই শুনি আছোঁ। আপুনি কওকচোন।",
        "ur": "جی، میں سن رہا ہوں۔ آپ فرمائیے۔"
    },
    "clarification": {
        "hi": "मैं आपकी आवाज़ साफ़ नहीं सुन पाया। कृपया दोबारा बोलें।",
        "hinglish": "Aapki awaaz clear nahi aayi. Please dobara boliye.",
        "en": "I could not hear your voice clearly. Please try again.",
        "pa": "ਮੈਨੂੰ ਤੁਹਾਡੀ ਆਵਾਜ਼ ਸਾਫ਼ ਨਹੀਂ ਸੁਣਾਈ ਦਿੱਤੀ। ਕਿਰਪਾ ਕਰਕੇ ਦੁਬਾਰਾ ਬੋਲੋ।",
        "mr": "मला आपला आवाज नीट ऐकू आला नाही. कृपया पुन्हा बोला.",
        "bn": "আমি আপনার কথা পরিষ্কার শুনতে পাইনি। দয়া করে আরেকবার বলুন।",
        "gu": "મને તમારો અવાજ બરાબર સંભળાયો નથી. કૃપા કરીને ફરીથી બોલો.",
        "ta": "உங்கள் குரல் எனக்கு தெளிவாகக் கேட்கவில்லை. தயவுசெய்து மீண்டும் பேசுங்கள்.",
        "te": "మీ స్వరం నాకు స్పష్టంగా వినిపించలేదు. దయచేసి మళ్ళీ మాట్లాడండి.",
        "kn": "ನಿಮ್ಮ ಧ್ವನಿ ನನಗೆ ಸ್ಪಷ್ಟವಾಗಿ ಕೇಳಿಸಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೊಮ್ಮೆ ಮಾತನಾಡಿ.",
        "ml": "താങ്കളുടെ ശബ്ദം വ്യക്തമായി കേട്ടില്ല. ദയവായി ഒന്നുകൂടി പറയൂ.",
        "or": "ମୁଁ ଆପଣଙ୍କ ସ୍ୱର ସ୍ପଷ୍ଟ ଭାବେ ଶୁଣିପାରିଲି ନାହିଁ। ଦୟାକରି ଆଉ ଥରେ କୁହନ୍ତୁ।",
        "as": "মই আপোনাৰ মাত স্পষ্টকৈ শুনা নাপালোঁ। অনুগ্ৰহ কৰি পুনৰ কওক।",
        "ur": "میں آپ کی آواز صاف نہیں سن سکا۔ براہ کرم دوبارہ بولیے۔"
    }
}


# ==============================================================================
# 8. RESPONSE GENERATION ENGINE (RULE TEMPLATES + LLM ENGINE)
# ==============================================================================

def get_gemini_api_key() -> str:
    return os.getenv("GEMINI_API_KEY", "").strip()


async def generate_saathi_speech_response(
    question: str,
    language: str,
    history: Optional[List[Dict[str, str]]] = None,
    farmer_name: Optional[str] = None,
    current_page: Optional[str] = None,
    screen_name: Optional[str] = None,
    available_buttons: Optional[List[str]] = None,
    focused_button: Optional[str] = None,
    ui_context: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Generates Saathi's short, warm, natural conversational reply in the farmer's language.
    Strictly observes Step 2 constraints:
    - Guides the farmer to the feature, does NOT provide internal data.
    - Explains what buttons do and what is available on the screen.
    - Returns (response_text, navigation_action_metadata)
    """
    clean_q = question.strip()
    lang_name = SUPPORTED_LANGUAGES.get(language, "Hindi")
    lang_key = language if language in SUPPORTED_LANGUAGES else "hi"

    # 0. Check Proactive UI Signals (e.g. Idle, Stuck, Error, Upload completed)
    if ui_context:
        if ui_context.get("has_error") or ui_context.get("error_type") == "upload_failed":
            if lang_key == "hinglish":
                res_text = "Photo upload nahi hui. Ek baar dobara photo select karke try karein."
            elif lang_key == "hi":
                res_text = "फ़ोटो अपलोड नहीं हुई। एक बार दोबारा फ़ोटो सेलेक्ट करके प्रयास करें।"
            elif lang_key == "pa":
                res_text = "ਫੋਟੋ ਅਪਲੋਡ ਨਹੀਂ ਹੋਈ। ਇਕ ਵਾਰ ਦੁਬਾਰਾ ਫੋਟੋ ਚੁਣ ਕੇ ਕੋਸ਼ਿਸ਼ ਕਰੋ।"
            else:
                res_text = "Photo could not be uploaded. Please select the photo again and retry."
            return res_text, {"action": "retry_photo_upload"}

        if ui_context.get("proactive_help") or (not clean_q and (ui_context.get("is_stuck") or ui_context.get("is_idle"))):
            if lang_key == "hinglish":
                res_text = "Ji, agar aapko aage badhne mein dikkat ho rahi hai, mujhse pooch sakte hain."
            elif lang_key == "hi":
                res_text = "जी, अगर आपको आगे बढ़ने में दिक्कत हो रही है, मुझसे पूछ सकते हैं।"
            elif lang_key == "pa":
                res_text = "ਜੀ, ਜੇ ਤੁਹਾਨੂੰ ਅੱਗੇ ਵਧਣ ਵਿੱਚ ਕੋਈ ਦਿੱਕਤ ਆ ਰਹੀ ਹੈ ਤਾਂ ਮੈਨੂੰ ਪੁੱਛ ਸਕਦੇ ਹੋ।"
            else:
                res_text = "If you are having any trouble moving forward, please feel free to ask me."
            return res_text, {"action": "proactive_assistance_prompt"}

        if ui_context.get("file_uploaded") and (not clean_q or any(p in clean_q.lower() for p in ["ab kya", "next", "kar diya", "ho gaya"])):
            if lang_key == "hinglish":
                res_text = "Ji, ab aap 'Analyze' button par click kar sakte hain."
            elif lang_key == "hi":
                res_text = "जी, अब आप 'Analyze' बटन पर क्लिक कर सकते हैं।"
            elif lang_key == "pa":
                res_text = "ਜੀ, ਹੁਣ ਤੁਸੀਂ 'Analyze' ਬਟਨ 'ਤੇ ਕਲਿੱਕ ਕਰ ਸਕਦੇ ਹੋ।"
            else:
                res_text = "Now you can click on the 'Analyze' button."
            return res_text, {"action": "prompt_analyze_step", "button": "Analyze"}

    # 1. Check Platform Navigation, Follow-up & Feature Guidance Intent First
    nav_match = detect_platform_navigation_intent(
        clean_q,
        current_page=current_page,
        available_buttons=available_buttons,
        focused_button=focused_button,
        history=history
    )

    if nav_match:
        intent_type, feature_id = nav_match
        
        # A. Step 5/8 Guided Navigation: Progress Acknowledgment ("Kar diya", "Upload kar diya", "Mil gaya", "Ho gaya")
        if intent_type == "step_progress_ack" and feature_id:
            feat = PLATFORM_FEATURES[feature_id]
            u_clean_lower = clean_q.lower()
            
            # Step 8 Natural flow: Farmer says "Mil gaya" after button location guidance
            if any(p in u_clean_lower for p in ["mil gaya", "milgaya", "mil gya", "dikh gaya", "found it", "got it"]):
                if lang_key == "hinglish":
                    res_text = "Ji, ab uspar click karein."
                elif lang_key == "hi":
                    res_text = "जी, अब उसपर क्लिक करें।"
                elif lang_key == "pa":
                    res_text = "ਜੀ, ਹੁਣ ਉਸ 'ਤੇ ਕਲਿੱਕ ਕਰੋ।"
                elif lang_key == "mr":
                    res_text = "होय, आता त्यावर क्लिक करा."
                else:
                    res_text = "Great, now please click on it."
                return res_text, {
                    "action": "click_found_button",
                    "feature": feat["display_name"],
                    "button": feat["button_name"],
                    "target": feat["url"]
                }

            next_step_num = get_guided_workflow_next_step(feature_id, history, clean_q)
            workflow_steps = GUIDED_WORKFLOW_STEPS.get(feature_id, [])
            
            # Find step instruction
            step_instruction = None
            for s_obj in workflow_steps:
                if s_obj["step"] == next_step_num:
                    step_instruction = s_obj.get(lang_key) or s_obj.get("hi") or s_obj.get("en")
                    break
            
            if not step_instruction:
                step_instruction = f"Bahut badhiya! Ab aap '{feat['button_name']}' par apna agla kadam pura karein." if lang_key == "hinglish" else f"बहुत बढ़िया! अब आप '{feat['button_name']}' पर अगला कदम पूरा करें।"

            return step_instruction, {
                "action": "guided_next_step",
                "feature": feat["display_name"],
                "button": feat["button_name"],
                "step": next_step_num,
                "target": feat["url"]
            }

        # B. Generic Progress Acknowledgment without context
        if intent_type == "step_progress_generic":
            if any(p in clean_q.lower() for p in ["mil gaya", "milgaya", "found it"]):
                res_text = "Ji, ab uspar click karein." if lang_key == "hinglish" else "जी, अब उसपर क्लिक करें।"
            elif lang_key == "hinglish":
                res_text = "Bahut badhiya! Ab aap batayein ki aap aage kis feature par kaam karna chahte hain?"
            elif lang_key == "hi":
                res_text = "बहुत बढ़िया! अब आप बताइए कि आप आगे किस फीचर पर काम करना चाहते हैं?"
            elif lang_key == "pa":
                res_text = "ਬਹੁਤ ਵਧੀਆ! ਹੁਣ ਤੁਸੀਂ ਦੱਸੋ ਕਿ ਤੁਸੀਂ ਅੱਗੇ ਕਿਸ ਫੀਚਰ 'ਤੇ ਜਾਣਾ ਚਾਹੁੰਦੇ ਹੋ?"
            elif lang_key == "mr":
                res_text = "छान! आता आपण सांगा की आपल्याला पुढे कोणत्या फीचरवर जायचे आहे?"
            else:
                res_text = "Great! Please let me know which feature you would like to proceed with next."
            return res_text, {"action": "step_progress_ack_generic"}

        # C-S10-A. Step 10 Personalisation: Suggest Alternative Option ("Ye option mujhe nahi chahiye, doosra wala batao")
        if intent_type == "trouble_suggest_alternative_option":
            if feature_id == "marketplace" or current_page == "crop-listings":
                if lang_key == "hinglish":
                    res_text = "Ji, aap 'Crop Monitoring' se apni fasal ki dekhbhal ka schedule dekh sakte hain, ya 'AI Crop Scan' se bimari check kar sakte hain."
                elif lang_key == "hi":
                    res_text = "जी, आप 'Crop Monitoring' से फसल की दैनिक देखभाल देख सकते हैं, या 'AI Crop Scan' से बीमारी की जाँच कर सकते हैं।"
                else:
                    res_text = "You can explore 'Crop Monitoring' to track your daily calendar, or 'AI Crop Scan' to detect crop diseases."
            elif feature_id in ["disease_detection", "crop_disease"] or current_page == "upload-crop":
                if lang_key == "hinglish":
                    res_text = "Ji, aap '15-Day Weather' se mausam ka anumaan dekh sakte hain, ya 'Marketplace' se mandi bhav dekh sakte hain."
                elif lang_key == "hi":
                    res_text = "जी, आप '15-Day Weather' से मौसम का पूर्वानुमान देख सकते हैं, या 'Marketplace' से मंडी भाव देख सकते हैं।"
                else:
                    res_text = "You can check the '15-Day Weather' forecast or browse crop prices in 'Marketplace'."
            else:
                if lang_key == "hinglish":
                    res_text = "Ji, aap 'Marketplace' se mandi bhav dekh sakte hain ya 'Crop Monitoring' se sinchai schedule dekh sakte hain."
                elif lang_key == "hi":
                    res_text = "जी, आप 'Marketplace' से मंडी भाव देख सकते हैं या 'Crop Monitoring' से सिंचाई शेड्यूल देख सकते हैं।"
                else:
                    res_text = "You can check live crop rates in 'Marketplace' or view irrigation schedules in 'Crop Monitoring'."
            return res_text, {"action": "suggest_alternative", "previous_feature": feature_id}

        # C-S10-B. Step 10 Personalisation: Recall Previous Session Option ("Pehle wala kaise kholna hai?")
        if intent_type == "trouble_recall_previous_option":
            if feature_id:
                feat = PLATFORM_FEATURES[feature_id]
                if lang_key == "hinglish":
                    res_text = f"Pehle humne {feat['display_name']} ki baat ki thi. Usko kholne ke liye upar diye gaye '{feat['button_name']}' button par click karein."
                elif lang_key == "hi":
                    res_text = f"पहले हमने {feat['display_name']} की बात की थी। उसे खोलने के लिए ऊपर दिए गए '{feat['button_name']}' बटन पर क्लिक करें।"
                elif lang_key == "pa":
                    res_text = f"ਪਹਿਲਾਂ ਅਸੀਂ {feat['display_name']} ਦੀ ਗੱਲ ਕੀਤੀ ਸੀ। ਉਸ ਲਈ ਉੱਪਰ ਦਿੱਤੇ '{feat['button_name']}' ਬਟਨ 'ਤੇ ਕਲਿੱਕ ਕਰੋ।"
                else:
                    res_text = f"Earlier we were discussing {feat['display_name']}. To open it, click on '{feat['button_name']}' at the top."
                return res_text, {"action": "recall_previous", "button": feat["button_name"], "target": feat["url"]}
            else:
                res_text = "Pehle ke option par jaane ke liye upar diye gaye 'Dashboard' button par click karein." if lang_key == "hinglish" else "पहले के ऑप्शन पर जाने के लिए ऊपर दिए गए 'Dashboard' बटन पर क्लिक करें।"
                return res_text, {"action": "recall_previous_fallback"}

        # C-S10-C. Step 10 Personalisation: Detailed Process Explanation Request ("Vistaar se batao")
        if intent_type == "trouble_detailed_explanation_request":
            if feature_id in ["disease_detection", "crop_disease"] or current_page == "upload-crop":
                if lang_key == "hinglish":
                    res_text = "Poora process yeh hai: 1. Upar 'AI Crop Scan' dabayein, 2. 'Choose File' se patti ki photo upload karein, 3. 'Analyze' par click karein aur report dekhein."
                elif lang_key == "hi":
                    res_text = "पूरा प्रोसेस यह है: 1. ऊपर 'AI Crop Scan' दबाएं, 2. 'Choose File' से पत्ती की फ़ोटो अपलोड करें, 3. 'Analyze' पर क्लिक करें और रिपोर्ट देखें।"
                else:
                    res_text = "Here is the complete step-by-step process: 1. Click 'AI Crop Scan', 2. Upload leaf photo using 'Choose File', 3. Click 'Analyze' to view remedies."
            elif feature_id == "marketplace" or current_page == "crop-listings":
                if lang_key == "hinglish":
                    res_text = "Poora process yeh hai: 1. 'Marketplace' kholiye, 2. Live mandi bhav dekhein, 3. Fasal bechne ke liye 'List New Crop' bhariye aur buyers se contact karein."
                elif lang_key == "hi":
                    res_text = "पूरा प्रोसेस यह है: 1. 'Marketplace' खोलें, 2. लाइव मंडी भाव देखें, 3. फसल बेचने के लिए 'List New Crop' भरें और खरीदारों से संपर्क करें।"
                else:
                    res_text = "Here is the process: 1. Open 'Marketplace', 2. View live mandi rates, 3. Click 'List New Crop' to connect with buyers."
            else:
                if lang_key == "hinglish":
                    res_text = "AgriBridge par aap Mandi Bhav, AI Crop Disease Scan, Weather aur Crop Monitoring jaise sabhi tools upar navbar se aasaani se use kar sakte hain."
                elif lang_key == "hi":
                    res_text = "AgriBridge पर आप मंडी भाव, AI फसल रोग जांच, मौसम और क्रॉप मॉनिटरिंग जैसे सभी टूल्स ऊपर नेविगेशन बार से आसानी से उपयोग कर सकते हैं।"
                else:
                    res_text = "On AgriBridge, you can easily access Marketplace, Crop Disease Scan, Weather, and Crop Monitoring from the top navigation bar."
            return res_text, {"action": "detailed_explanation", "feature": feature_id}

        # C-UI1. Step 9 Proactive UI Guidance: Photo Upload Failure / Error
        if intent_type == "trouble_photo_upload_error":
            if lang_key == "hinglish":
                res_text = "Photo upload nahi hui. Ek baar dobara photo select karke try karein."
            elif lang_key == "hi":
                res_text = "फ़ोटो अपलोड नहीं हुई। एक बार दोबारा फ़ोटो सेलेक्ट करके प्रयास करें।"
            elif lang_key == "pa":
                res_text = "ਫੋਟੋ ਅਪਲੋਡ ਨਹੀਂ ਹੋਈ। ਇਕ ਵਾਰ ਦੁਬਾਰਾ ਫੋਟੋ ਚੁਣ ਕੇ ਕੋਸ਼ਿਸ਼ ਕਰੋ।"
            else:
                res_text = "Photo could not be uploaded. Please select the photo again and retry."
            return res_text, {"action": "retry_photo_upload"}

        # C-UI2. Step 9 Proactive UI Guidance: Page Stuck / Freezing
        if intent_type == "trouble_page_stuck":
            if lang_key == "hinglish":
                res_text = "Koi baat nahi ji, ek baar page ko refresh karke dobara button dabayein, main yahin hoon."
            elif lang_key == "hi":
                res_text = "कोई बात नहीं जी, एक बार पेज रीफ्रेश करके दोबारा बटन दबाएं, मैं यहीं हूँ।"
            else:
                res_text = "No worries, please refresh the page and try again. I am right here."
            return res_text, {"action": "refresh_advice"}

        # C0. Step 8: Natural Interruption & Side Question Handling ("Ruko, pehle ye batao...")
        if intent_type == "trouble_interruption_pause":
            if lang_key == "hinglish":
                res_text = "Ji bilkul, boliye, main sun raha hoon. Aap pehle apna sawal pooch lijiye."
            elif lang_key == "hi":
                res_text = "जी बिल्कुल, बोलिए, मैं सुन रहा हूँ। आप पहले अपना सवाल पूछ लीजिए।"
            else:
                res_text = "Sure, please go ahead. I am listening to your question."
            return res_text, {"action": "interruption_pause_handle"}

        # C0-B. Step 8: Warm Conversational Acknowledgment ("Accha, samajh gaya.")
        if intent_type == "trouble_warm_acknowledgment":
            if lang_key == "hinglish":
                res_text = "Bahut badhiya ji! Jab bhi kisi button ya feature mein madad chahiye ho, bas batayiye."
            elif lang_key == "hi":
                res_text = "बहुत बढ़िया जी! जब भी किसी बटन या फीचर में मदद चाहिए हो, बस बताइए।"
            else:
                res_text = "Wonderful! Feel free to ask anytime you need help navigating the platform."
            return res_text, {"action": "warm_acknowledgment"}

        # C0-C. Step 8: Mid-Conversation Correction ("Nahi, mera matlab wo wala button hai.")
        if intent_type == "trouble_correction_clarification":
            if lang_key == "hinglish":
                res_text = "Ji, kaunsa option kholna hai — Mandi Bhav ya Weather?"
            elif lang_key == "hi":
                res_text = "जी, कौन सा ऑप्शन खोलना है — मंडी भाव या Weather?"
            else:
                res_text = "Which option did you mean — Marketplace or Weather?"
            return res_text, {"action": "correction_clarification"}

        # C1. Step 7 Reliability: Patient Simplification for Confusion ("Mujhe samajh nahi aa raha")
        if intent_type == "trouble_confused_need_simplification":
            if feature_id in ["disease_detection", "crop_disease"] or current_page == "upload-crop":
                if lang_key == "hinglish":
                    res_text = "Koi baat nahi ji! Bilkul aasan hai: aap bas 'Upload Photo' par click karke patti ki photo lein, baki bimari ki report screen par aa jayegi."
                elif lang_key == "hi":
                    res_text = "कोई बात नहीं जी! बिल्कुल आसान है: आप बस 'Upload Photo' पर क्लिक करके पत्ती की फ़ोटो लें, बाकी रिपोर्ट स्क्रीन पर आ जाएगी।"
                else:
                    res_text = "No worries! It is very simple: just click 'Upload Photo' to take a picture of your leaf, and the report will appear on screen."
            elif feature_id == "marketplace" or current_page == "crop-listings":
                if lang_key == "hinglish":
                    res_text = "Koi baat nahi ji! Yahan aap mandi rate dekh sakte hain ya 'List New Crop' par click karke apni fasal bech sakte hain."
                elif lang_key == "hi":
                    res_text = "कोई बात नहीं जी! यहाँ आप मंडी भाव देख सकते हैं या 'List New Crop' पर क्लिक करके अपनी फसल बेच सकते हैं।"
                else:
                    res_text = "No worries! Here you can check market prices or click 'List New Crop' to sell your harvest."
            else:
                if lang_key == "hinglish":
                    res_text = "Koi baat nahi ji! Aap bataiye aapko kaun sa kaam karna hai, jaise bimari check karna ya mandi bhav dekhna? Main step-by-step madad karunga."
                elif lang_key == "hi":
                    res_text = "कोई बात नहीं जी! आप बताइए कि आपको क्या काम करना है, जैसे बीमारी चेक करना या मंडी भाव देखना? मैं स्टेप-बाय-स्टेप मदद करूँगा।"
                else:
                    res_text = "No worries! Please tell me what you would like to do, such as checking disease or viewing mandi rates? I will guide you step by step."
            return res_text, {"action": "patient_simplification", "feature_id": feature_id}

        # C2. Step 7 Reliability: Out-of-Scope Redirection (Guiding to platform module without fabricating chemical advice)
        if intent_type == "trouble_out_of_scope_fertilizer":
            if lang_key == "hinglish":
                res_text = "Khad, mitti aur fasal ke sahi sujhav ke liye upar diye gaye 'Crop Recommendations' ya 'AI Crop Scan' button par click karein."
            elif lang_key == "hi":
                res_text = "खाद, मिट्टी और फसल के सही सुझाव के लिए ऊपर दिए गए 'Crop Recommendations' या 'AI Crop Scan' बटन पर क्लिक करें।"
            else:
                res_text = "For verified fertilizer and crop advice, please click on 'Crop Recommendations' or 'AI Crop Scan' at the top."
            return res_text, {"action": "out_of_scope_redirect", "target": "/frontend/pages/crop-recommendation.html"}

        # C3. Step 5 Troubleshooting: Button Not Found ("Button nahi mil raha")
        if intent_type == "trouble_cannot_find_button":
            if feature_id:
                feat = PLATFORM_FEATURES[feature_id]
                if lang_key == "hinglish":
                    res_text = f"'{feat['button_name']}' button upar main navigation bar mein diya gaya hai. Wahan click karein."
                elif lang_key == "hi":
                    res_text = f"'{feat['button_name']}' बटन ऊपर मुख्य नेविगेशन बार में दिया गया है। वहाँ क्लिक करें।"
                elif lang_key == "pa":
                    res_text = f"'{feat['button_name']}' ਬਟਨ ਉੱਪਰ ਮੁੱਖ ਨੇਵੀਗੇਸ਼ਨ ਬਾਰ ਵਿੱਚ ਹੈ। ਉੱਥੇ ਕਲਿੱਕ ਕਰੋ।"
                else:
                    res_text = f"The '{feat['button_name']}' button is located at the top navigation bar. Please click there."
            else:
                if lang_key == "hinglish":
                    res_text = "Upar navigation bar mein dekhein, sabhi zaroori buttons wahan diye gaye hain."
                elif lang_key == "hi":
                    res_text = "ऊपर नेविगेशन बार में देखें, सभी मुख्य बटन वहाँ मौजूद हैं।"
                else:
                    res_text = "Look at the top navigation bar, all main buttons are located there."
            return res_text, {"action": "locate_button", "feature_id": feature_id}

        # D. Step 5 Troubleshooting: Wrong Page Opened ("Galti se kuch aur open ho gaya")
        if intent_type == "trouble_wrong_page_opened":
            if feature_id:
                feat = PLATFORM_FEATURES[feature_id]
                if lang_key == "hinglish":
                    res_text = f"Koi baat nahi ji! Sahi page par aane ke liye upar diye gaye '{feat['button_name']}' button par click karein."
                elif lang_key == "hi":
                    res_text = f"कोई बात नहीं जी! सही पेज पर आने के लिए ऊपर दिए गए '{feat['button_name']}' बटन पर क्लिक करें।"
                else:
                    res_text = f"No worries! Click on the '{feat['button_name']}' button at the top to return to the right page."
            else:
                if lang_key == "hinglish":
                    res_text = "Koi baat nahi ji! Upar diye gaye 'Dashboard' button par click karke wapas aa sakte hain."
                else:
                    res_text = "No worries! You can click 'Dashboard' at the top to return to the home screen."
            return res_text, {"action": "recover_navigation", "feature_id": feature_id}

        # E. Step 5 Troubleshooting: Not Working / Stuck ("Nahi ho raha")
        if intent_type == "trouble_not_working":
            if lang_key == "hinglish":
                res_text = "Koi baat nahi ji, ek baar button ko dhyan se dabayein ya page refresh karke dobara try karein. Main yahin hoon."
            elif lang_key == "hi":
                res_text = "कोई बात नहीं जी, एक बार बटन को ध्यान से दबाएं या पेज रीफ्रेश करके दोबारा प्रयास करें। मैं यहीं हूँ।"
            else:
                res_text = "No problem, please try tapping the button carefully or refresh the page. I am right here to assist."
            return res_text, {"action": "troubleshooting_assist"}

        # F. Step 5 Troubleshooting: Where to click ("Kahan click karu?")
        if intent_type == "trouble_where_to_click":
            if feature_id:
                feat = PLATFORM_FEATURES[feature_id]
                next_step_num = get_guided_workflow_next_step(feature_id, history, clean_q)
                workflow_steps = GUIDED_WORKFLOW_STEPS.get(feature_id, [])
                step_text = None
                for s_obj in workflow_steps:
                    if s_obj["step"] == next_step_num:
                        step_text = s_obj.get(lang_key) or s_obj.get("hi") or s_obj.get("en")
                        break
                if not step_text:
                    step_text = f"Aap '{feat['button_name']}' button par click karein." if lang_key == "hinglish" else f"आप '{feat['button_name']}' बटन पर क्लिक करें।"
                return step_text, {"action": "click_guidance", "feature": feat["display_name"]}
            else:
                res_text = "Aapko jis feature par jana hai, upar diye gaye button par click karein jaise 'Marketplace' ya 'AI Crop Scan'." if lang_key == "hinglish" else "आपको जिस फीचर पर जाना है, ऊपर दिए गए बटन पर क्लिक करें जैसे 'Marketplace' या 'AI Crop Scan'।"
                return res_text, {"action": "click_guidance_generic"}

        # G. Step 4 Context-Aware Follow-up ("Uske baad kya karna hai?")
        if intent_type == "follow_up" and feature_id:
            feat = PLATFORM_FEATURES[feature_id]
            if feature_id in PLATFORM_FOLLOW_UP_RESPONSES:
                res_text = PLATFORM_FOLLOW_UP_RESPONSES[feature_id].get(lang_key, PLATFORM_FOLLOW_UP_RESPONSES[feature_id]["hi"])
            else:
                btn = feat["button_name"]
                if lang_key == "hinglish":
                    res_text = f"'{btn}' par click karne ke baad aap iska upyog aage badha sakte hain."
                elif lang_key == "hi":
                    res_text = f"'{btn}' पर क्लिक करने के बाद आप इसका उपयोग आगे बढ़ा सकते हैं।"
                else:
                    res_text = f"After clicking '{btn}', you can proceed with your operations."

            return res_text, {
                "action": "follow_up_instruction",
                "feature": feat["display_name"],
                "button": feat["button_name"],
                "target": feat["url"]
            }

        # H. Generic Follow-up without prior context -> Ask short clarification
        if intent_type == "follow_up_generic":
            if lang_key == "hinglish":
                res_text = "Aap kis feature ya button ke baare mein pooch rahe hain? Jaise Mandi Bhav ya AI Crop Scan?"
            elif lang_key == "hi":
                res_text = "आप किस फीचर या बटन के बारे में पूछ रहे हैं? जैसे मंडी भाव या AI Crop Scan?"
            elif lang_key == "pa":
                res_text = "ਤੁਸੀਂ ਕਿਸ ਫੀਚਰ ਜਾਂ ਬਟਨ ਬਾਰੇ ਪੁੱਛ ਰਹੇ ਹੋ? ਜਿਵੇਂ ਮੰਡੀ ਭਾਵ ਜਾਂ AI Crop Scan?"
            elif lang_key == "mr":
                res_text = "आपण कोणत्या फीचर किंवा बटणाबद्दल विचारत आहात? जसे की मंडी भाव किंवा AI Crop Scan?"
            else:
                res_text = "Which feature or button are you asking about? Such as Marketplace or AI Crop Scan?"
            return res_text, {"action": "clarification"}

        # C. Top Navigation Overview ("Upar wala button kaunsa hai?")
        if intent_type == "explain_top_buttons":
            res_text = PLATFORM_GUIDANCE_RESPONSES["explain_top_buttons"].get(lang_key, PLATFORM_GUIDANCE_RESPONSES["explain_top_buttons"]["hi"])
            return res_text, {"action": "overview", "target": "top_navbar"}

        # D. Direct Feature Guidance ("Mujhe mandi bhav dekhna hai", "Disease check karna hai")
        if intent_type == "guide_feature" and feature_id:
            feat = PLATFORM_FEATURES[feature_id]
            guide_key = f"guide_{feature_id}"
            if guide_key in PLATFORM_GUIDANCE_RESPONSES:
                res_text = PLATFORM_GUIDANCE_RESPONSES[guide_key].get(lang_key, PLATFORM_GUIDANCE_RESPONSES[guide_key]["hi"])
            else:
                btn = feat["button_name"]
                if lang_key == "hinglish":
                    res_text = f"Iske liye upar diye gaye '{btn}' button par click karein."
                elif lang_key == "hi":
                    res_text = f"इसके लिए ऊपर दिए गए '{btn}' बटन पर क्लिक करें।"
                else:
                    res_text = f"For this, click on the '{btn}' button at the top."
            
            return res_text, {
                "action": "navigate",
                "button": feat["button_name"],
                "target": feat["url"],
                "feature": feat["display_name"]
            }

        # E. Button Explanation ("Ye button kya karta hai?")
        if intent_type == "explain_button" and feature_id:
            feat = PLATFORM_FEATURES[feature_id]
            btn = feat["button_name"]
            if lang_key == "hinglish":
                res_text = f"'{btn}' button se aap {feat['purpose'].lower()} Iska upyog karne ke liye is par click karein."
            elif lang_key == "hi":
                res_text = f"'{btn}' बटन से आप {feat['display_name']} का उपयोग कर सकते हैं। अधिक जानकारी के लिए इस पर क्लिक करें।"
            elif lang_key == "pa":
                res_text = f"'{btn}' ਬਟਨ ਨਾਲ ਤੁਸੀਂ {feat['display_name']} ਫੀਚਰ ਵਰਤ ਸਕਦੇ ਹੋ।"
            elif lang_key == "mr":
                res_text = f"'{btn}' बटणाद्वारे आपण {feat['display_name']} चा वापर करू शकता."
            else:
                res_text = f"The '{btn}' button allows you to {feat['purpose'].lower()}"

            return res_text, {
                "action": "explain",
                "button": feat["button_name"],
                "target": feat["url"]
            }

        # I. Step 6 UI Awareness: Screen-Specific Feature Locator ("Mandi Bhav ka option mujhe nahi dikh raha")
        if intent_type == "screen_locate_feature" and feature_id:
            feat = PLATFORM_FEATURES[feature_id]
            btn = feat["button_name"]
            if current_page == "farmer-dashboard":
                if lang_key == "hinglish":
                    res_text = f"Farmer Dashboard par '{btn}' card par click karein, ya upar navigation bar mein '{btn}' button dekhein."
                elif lang_key == "hi":
                    res_text = f"Farmer Dashboard पर '{btn}' कार्ड पर क्लिक करें, या ऊपर नेविगेशन बार में '{btn}' बटन देखें।"
                else:
                    res_text = f"On your Farmer Dashboard, click on the '{btn}' card, or locate '{btn}' in the top navigation bar."
            elif current_page and current_page in AGRIBRIDGE_SCREENS:
                if lang_key == "hinglish":
                    res_text = f"Upar top navigation bar mein dekhein, '{btn}' button wahan diya gaya hai."
                elif lang_key == "hi":
                    res_text = f"ऊपर मुख्य नेविगेशन बार में देखें, '{btn}' बटन वहाँ उपलब्ध है।"
                else:
                    res_text = f"Look at the top navigation bar, the '{btn}' button is available there."
            else:
                if lang_key == "hinglish":
                    res_text = f"Upar main navigation bar mein '{btn}' button diya gaya hai. Ji, aap abhi kaunsa page dekh rahe hain?"
                elif lang_key == "hi":
                    res_text = f"ऊपर मुख्य नेविगेशन बार में '{btn}' बटन दिया गया है। जी, आप अभी कौन सा पेज देख रहे हैं?"
                else:
                    res_text = f"The '{btn}' button is in the top navigation bar. Which page are you currently looking at?"

            return res_text, {
                "action": "locate_on_screen",
                "button": btn,
                "current_page": current_page,
                "target": feat["url"]
            }

        # J. Step 6 UI Awareness: Current Screen Primary Action ("Ye button kya karta hai?" with current_page)
        if intent_type == "explain_screen_action" and feature_id:
            feat = PLATFORM_FEATURES[feature_id]
            btn = feat["button_name"]
            if current_page == "upload-crop":
                if lang_key == "hinglish":
                    res_text = "Is screen par 'Choose File' se leaf photo upload karein aur 'Diagnose Disease' button dabakar fasal ki bimari check karein."
                elif lang_key == "hi":
                    res_text = "इस स्क्रीन पर 'Choose File' से पत्ती की फ़ोटो अपलोड करें और 'Diagnose Disease' बटन दबाकर बीमारी की पहचान करें।"
                else:
                    res_text = "On this screen, upload a leaf photo with 'Choose File' and click 'Diagnose Disease' to identify crop illnesses."
            elif current_page == "crop-listings":
                if lang_key == "hinglish":
                    res_text = "Is screen par aap live Mandi rates dekh sakte hain aur fasal bechne ke liye 'List New Crop' button use kar sakte hain."
                elif lang_key == "hi":
                    res_text = "इस स्क्रीन पर आप लाइव मंडी भाव देख सकते हैं और फसल बेचने के लिए 'List New Crop' बटन का उपयोग कर सकते हैं।"
                else:
                    res_text = "On this screen, you can view live market rates and click 'List New Crop' to sell your harvest."
            elif current_page == "crop-monitoring":
                if lang_key == "hinglish":
                    res_text = "Is screen par apni fasal aur boyi ki date select karke 'Run Monitoring Analysis' par click karein."
                elif lang_key == "hi":
                    res_text = "इस स्क्रीन पर अपनी फसल और बुवाई की तारीख चुनकर 'Run Monitoring Analysis' पर क्लिक करें।"
                else:
                    res_text = "On this screen, select your crop and sowing date, then click 'Run Monitoring Analysis'."
            elif current_page == "farmer-dashboard":
                if lang_key == "hinglish":
                    res_text = "Farmer Dashboard par aap 'Upload Crop Photo', '15-Day Weather', aur 'Dynamic Crop Monitoring' buttons use kar sakte hain."
                elif lang_key == "hi":
                    res_text = "Farmer Dashboard पर आप 'Upload Crop Photo', '15-Day Weather', और 'Dynamic Crop Monitoring' बटन का उपयोग कर सकते हैं।"
                else:
                    res_text = "On the Farmer Dashboard, you can use 'Upload Crop Photo', '15-Day Weather', and 'Dynamic Crop Monitoring' buttons."
            else:
                if lang_key == "hinglish":
                    res_text = f"Is screen par aap '{btn}' button use karke apna kaam pura kar sakte hain."
                elif lang_key == "hi":
                    res_text = f"इस स्क्रीन पर आप '{btn}' बटन का उपयोग कर सकते हैं।"
                else:
                    res_text = f"On this screen, you can use the '{btn}' button to proceed."

            return res_text, {
                "action": "explain_screen_action",
                "screen": current_page,
                "button": btn
            }

        # K. Generic Button Explanation without guessing -> Ask short clarification
        if intent_type == "explain_button_generic":
            if lang_key == "hinglish":
                res_text = "Ji, aap abhi kaunsa page dekh rahe hain?"
            elif lang_key == "hi":
                res_text = "जी, आप अभी कौन सा पेज देख रहे हैं?"
            elif lang_key == "pa":
                res_text = "ਜੀ, ਤੁਸੀਂ ਇਸ ਵੇਲੇ ਕਿਹੜਾ ਪੇਜ ਦੇਖ ਰਹੇ ਹੋ?"
            elif lang_key == "mr":
                res_text = "जी, आपण सध्या कोणते पेज पाहत आहात?"
            else:
                res_text = "Could you please tell me which page you are currently viewing?"
            return res_text, {"action": "clarification_page"}

    # 2. Conversational Intent Checking (Greetings, Identity, Status)
    lower = clean_q.lower()

    # Incomplete sentence / filler
    if len(clean_q.split()) <= 2 and any(w in lower for w in ["haan", "suno", "sun rahe ho", "hello", "ji", "bolo", "hmm", "haanji"]):
        return CONVERSATIONAL_TEMPLATES["listening_ack"].get(lang_key, CONVERSATIONAL_TEMPLATES["listening_ack"]["hi"]), None

    # Who are you / Introduction inquiry
    identity_triggers = [
        "who are you", "aap kaun", "kaun ho", "tussi kaun", "who r u", "kya naam", "naam kya",
        "आप कौन", "कौन हो", "कौन हैं", "नाम क्या", "तुम्ही कोण", "आपण कोण", "ਕੌਣ ਹੋ",
        "మీరు ఎవరు", "நீங்கள் யார்", "আপনি কে", "તમે કોણ", "ನಿಮ್ಮ ಹೆಸರೇನು"
    ]
    if any(p in lower for p in identity_triggers):
        return CONVERSATIONAL_TEMPLATES["identity"].get(lang_key, CONVERSATIONAL_TEMPLATES["identity"]["hi"]), None

    # How are you inquiry
    status_triggers = [
        "kaise ho", "how are you", "kiddan", "kase aahat", "kaisa chal", "sab theek",
        "कैसे हो", "कैसे हैं", "कसे आहात", "ਕਿਵੇਂ ਹੋ", "ਕੀ ਹਾਲ", "ఎలా ఉన్నారు",
        "எப்படி இருக்கிறீர்கள்", "কেমন আছেন", "કેમ છો", "ಹೇಗಿದ್ದೀರಿ", "സുഖമാണോ"
    ]
    if any(p in lower for p in status_triggers):
        return CONVERSATIONAL_TEMPLATES["status_check"].get(lang_key, CONVERSATIONAL_TEMPLATES["status_check"]["hi"]), None

    # Greetings
    greeting_triggers = [
        "namaste", "namaskar", "hello", "hi", "hey", "sat sri akal", "vanakkam", "pranam", "ram ram",
        "नमस्ते", "नमस्कार", "प्रणाम", "राम राम", "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ", "నమస్కారం",
        "வணக்கம்", "নমস্কার", "નમસ્તે", "ನಮಸ್ಕಾರ", "നമസ്കാരം", "আদাব"
    ]
    if any(p in lower for p in greeting_triggers):
        return CONVERSATIONAL_TEMPLATES["greeting"].get(lang_key, CONVERSATIONAL_TEMPLATES["greeting"]["hi"]), None

    # 2.5 Check Agricultural & Kisan Saathi Domain Advisory
    try:
        from app.services.agriculture_intent import classify_intent
        from app.services.voice_service import get_response_for_intent

        agri_res = classify_intent(clean_q, language, history=history, session_context=context)
        if agri_res.get("is_agriculture_related") and agri_res.get("intent") not in ["fallback", "platform_navigation", None]:
            res_result = await get_response_for_intent(agri_res, clean_q, lang_key, context=context or agri_res.get("context"), history=history)
            if isinstance(res_result, tuple):
                if len(res_result) == 3:
                    res_text, nav_action, weather_meta = res_result
                else:
                    res_text, nav_action = res_result[0], res_result[1]
                    weather_meta = None
            else:
                res_text, nav_action, weather_meta = str(res_result), None, None
            if res_text:
                return res_text, nav_action, weather_meta
    except Exception:
        pass

    # 3. Dynamic LLM-Powered Conversational Response (with Platform Context)
    api_key = get_gemini_api_key()
    if api_key:
        history_str = ""
        if history:
            turns = []
            for turn in history[-3:]:
                r = turn.get("role", "farmer")
                t = turn.get("text") or turn.get("message") or ""
                if t:
                    turns.append(f"{r.capitalize()}: {t}")
            if turns:
                history_str = "Recent conversation context:\n" + "\n".join(turns) + "\n\n"

        name_clause = f"The farmer's name is {farmer_name}. Address them warmly." if farmer_name else ""
        curr_screen = screen_name or current_page or "Farmer Dashboard"
        btns_str = ", ".join(available_buttons) if available_buttons else "Dashboard, Crop Monitoring, AI Crop Scan, Marketplace, Weather, Voice AI, Command Center"

        prompt = (
            f"You are Saathi, a friendly, warm conversational AI companion and platform guide speaking with an Indian farmer over voice on AgriBridge.\n"
            f"Role & Identity:\n"
            f"- Your name is Saathi.\n"
            f"- TARGET LANGUAGE: Respond ONLY in {lang_name} ({language}). "
            f"If language is Hinglish, speak natural conversational Hindi written in Latin script. "
            f"If Hindi, speak in Hindi. If Punjabi, speak in Punjabi. If Tamil, speak in Tamil, etc.\n"
            f"{name_clause}\n"
            f"CURRENT SCREEN: {curr_screen}\n"
            f"AVAILABLE BUTTONS: {btns_str}\n"
            f"{history_str}"
            f"Farmer said: \"{clean_q}\"\n\n"
            f"RULES (STRICT STEP 2 SCOPE):\n"
            f"1. If the farmer asks how to use a feature or where to find something (mandi prices, weather, crop disease, monitoring, calendar, etc.), GUIDE them to the correct button/page. "
            f"For example: 'Mandi Bhav dekhne ke liye upar diye gaye Marketplace button par click karein.'\n"
            f"2. If the farmer asks what a button does or asks about top buttons (e.g. 'Upar wala button kaunsa hai?'), EXPLAIN the button/screen simply.\n"
            f"3. Keep button names recognizable in quotes (e.g. 'Marketplace', 'AI Crop Scan', 'Weather').\n"
            f"4. STRICT RULE: Guide the farmer to the feature, NEVER provide the information inside that feature yourself (no actual mandi prices, no weather degrees, no chemical disease prescriptions).\n"
            f"5. Keep response SHORT (strictly 1 to 2 spoken sentences, under 30 words).\n"
            f"6. Do NOT use markdown formatting (no *, #, bullets). Output plain spoken text only."
        )

        try:
            api_url = (
                "https://generativelanguage.googleapis.com/"
                "v1beta/models/gemini-1.5-flash:generateContent"
                f"?key={api_key}"
            )
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(api_url, json=payload, headers={"Content-Type": "application/json"})
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            res_text = parts[0].get("text", "").strip()
                            res_text = re.sub(r"[*#_`]", "", res_text).strip()
                            if res_text:
                                return res_text, None
        except Exception:
            pass

    # 4. Fallback response
    return CONVERSATIONAL_TEMPLATES["listening_ack"].get(lang_key, CONVERSATIONAL_TEMPLATES["listening_ack"]["hi"]), None


# ==============================================================================
# 10. LAYER 2: GUIDANCE CONTEXT FOUNDATION (STEP 11)
# ==============================================================================

class GuidanceContext:
    """
    Structured Guidance Context representing agricultural guidance generated by AgriBridge.
    Strictly follows truth hierarchy:
    1. latest active decision (replan / current_decision)
    2. latest trusted AgriBridge data
    3. current active plan
    4. previous decision / history
    """
    def __init__(
        self,
        farmer_id: Optional[str] = None,
        crop: Optional[str] = None,
        field_id: Optional[str] = None,
        crop_stage: Optional[str] = None,
        location: Optional[Dict[str, Any]] = None,
        soil: Optional[Dict[str, Any]] = None,
        weather: Optional[Dict[str, Any]] = None,
        disease_result: Optional[Dict[str, Any]] = None,
        recommendation: Optional[Dict[str, Any]] = None,
        action_plan: Optional[Dict[str, Any]] = None,
        alerts: Optional[List[Dict[str, Any]]] = None,
        replan_status: Optional[Dict[str, Any]] = None,
        previous_decision: Optional[Dict[str, Any]] = None,
        current_decision: Optional[Dict[str, Any]] = None,
        version: Optional[int] = None,
        timestamp: Optional[str] = None,
        sources: Optional[Dict[str, str]] = None,
    ):
        self.farmer_id = farmer_id
        self.crop = crop
        self.field_id = field_id
        self.crop_stage = crop_stage
        self.location = location or {}
        self.soil = soil or {}
        self.weather = weather or {}
        self.disease_result = disease_result or {}
        self.recommendation = recommendation or {}
        self.action_plan = action_plan or {}
        self.alerts = alerts or []
        self.replan_status = replan_status or {}
        self.previous_decision = previous_decision or {}
        self.current_decision = current_decision or {}
        self.version = version or 1
        self.timestamp = timestamp
        self.sources = sources or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "farmer_id": self.farmer_id,
            "crop": self.crop,
            "field_id": self.field_id,
            "crop_stage": self.crop_stage,
            "location": self.location,
            "soil": self.soil,
            "weather": self.weather,
            "disease_result": self.disease_result,
            "recommendation": self.recommendation,
            "action_plan": self.action_plan,
            "alerts": self.alerts,
            "replan_status": self.replan_status,
            "previous_decision": self.previous_decision,
            "current_decision": self.current_decision,
            "version": self.version,
            "timestamp": self.timestamp,
            "sources": self.sources,
        }


def resolve_active_guidance_context(guidance_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Inspects raw guidance context data and evaluates:
    - Active decision vs previous decision (with strict priority)
    - Multi-recommendation lists & items
    - Measurements (soil moisture, rainfall, temperature)
    - Available vs missing attributes (never guessing missing values)
    - Data sources, decision_id, plan_id, confidence, version
    """
    if not guidance_data:
        return {
            "has_guidance": False,
            "active_decision": None,
            "previous_decision": None,
            "recommendation_list": [],
            "available_fields": [],
            "missing_fields": ["crop", "recommendation", "weather", "action_plan"],
            "sources": {},
            "is_replanned": False,
        }

    curr_dec = guidance_data.get("current_decision") or {}
    prev_dec = guidance_data.get("previous_decision") or {}
    replan = guidance_data.get("replan_status") or {}
    rec = guidance_data.get("recommendation") or {}
    recs_list = guidance_data.get("recommendations") or guidance_data.get("items") or []
    plan = guidance_data.get("action_plan") or {}

    # Priority 1: Current active decision / replanning
    is_replanned = bool(replan.get("is_replanned") or (curr_dec and prev_dec and curr_dec != prev_dec))
    
    if curr_dec:
        active_decision = curr_dec
    elif replan.get("active_decision"):
        active_decision = replan["active_decision"]
    elif rec:
        active_decision = rec
    elif recs_list and isinstance(recs_list, list) and len(recs_list) > 0:
        active_decision = recs_list[0]
    elif plan:
        active_decision = plan
    else:
        active_decision = prev_dec or {}

    # Extract all recommendations / steps if list provided
    all_recs = []
    if rec:
        all_recs.append(rec)
    if isinstance(recs_list, list):
        for r in recs_list:
            if r not in all_recs:
                all_recs.append(r)
    if plan and isinstance(plan.get("items"), list):
        for r in plan["items"]:
            if r not in all_recs:
                all_recs.append(r)

    # Action Plan steps
    plan_steps = guidance_data.get("steps") or (plan.get("steps") if isinstance(plan, dict) else None) or []
    if not plan_steps and all_recs:
        plan_steps = all_recs

    # Calculate active step index from steps list
    active_step_idx = 0
    all_completed = False
    if plan_steps and isinstance(plan_steps, list):
        found_active = False
        for idx, step in enumerate(plan_steps):
            st = (step.get("status") or "").lower()
            if st in ["pending", "in_progress", "in-progress", "active", ""]:
                active_step_idx = idx
                found_active = True
                break
        if not found_active and len(plan_steps) > 0 and all((s.get("status") or "").lower() == "completed" for s in plan_steps):
            all_completed = True
            active_step_idx = len(plan_steps) - 1

        # Set active decision to active step if not specifically overridden
        if not curr_dec and not rec and plan_steps:
            active_decision = plan_steps[active_step_idx]

    # Detect available vs missing fields
    checked_keys = ["crop", "crop_stage", "location", "soil", "weather", "disease_result", "action", "reason", "quantity", "timing", "method", "measurements"]
    available_fields = []
    missing_fields = []

    for k in checked_keys:
        val = guidance_data.get(k) or active_decision.get(k)
        if val is not None and val != "" and val != {}:
            available_fields.append(k)
        else:
            missing_fields.append(k)

    return {
        "has_guidance": True,
        "active_decision": active_decision,
        "previous_decision": prev_dec if prev_dec else None,
        "recommendation_list": all_recs,
        "steps": plan_steps,
        "active_step_index": active_step_idx,
        "all_steps_completed": all_completed,
        "crop": guidance_data.get("crop") or active_decision.get("crop"),
        "crop_stage": guidance_data.get("crop_stage"),
        "measurements": guidance_data.get("measurements") or active_decision.get("measurements") or {},
        "soil_moisture": guidance_data.get("soil_moisture") or (guidance_data.get("soil") or {}).get("moisture"),
        "weather": guidance_data.get("weather") or {},
        "disease_result": guidance_data.get("disease_result") or {},
        "alerts": guidance_data.get("alerts") or [],
        "available_fields": available_fields,
        "missing_fields": missing_fields,
        "decision_id": guidance_data.get("decision_id") or active_decision.get("decision_id"),
        "plan_id": guidance_data.get("plan_id") or active_decision.get("plan_id"),
        "confidence": guidance_data.get("confidence") or active_decision.get("confidence"),
        "current_status": guidance_data.get("current_status") or active_decision.get("status") or ("REPLANNED" if is_replanned else "ACTIVE"),
        "sources": guidance_data.get("sources") or {"decision_engine": "AgriBridge Ultra Engine"},
        "is_replanned": is_replanned,
        "version": guidance_data.get("version") or (2 if is_replanned else 1),
    }


def classify_saathi_query_layer(
    text: str,
    guidance_context: Optional[Dict[str, Any]] = None,
    current_page: Optional[str] = None
) -> Tuple[str, Optional[str]]:
    """
    Classifies whether the farmer's question is:
    - Layer 1: PLATFORM_HELP (navigation, screen buttons, upload, page errors)
    - Layer 2: GUIDANCE_HELP (explaining generated recommendations, reasons, alerts, quantities, replanning)
    """
    if not text or not text.strip():
        return ("PLATFORM_HELP", None)

    lower = text.strip().lower()

    # Layer 2 Triggers (Questions about already generated advisory / action plans)
    why_triggers = ["kyun", "kyu", "why", "reason kya", "karan kya", "क्यों", "क्यो", "कारण", "ਕਿਉਂ", "का", "ఎందుకు", "ஏன்"]
    timing_triggers = ["kab", "kis time", "when", "timing kya", "timing", "kitne baje", "kitna baje", "baje", "कब", "समय", "ਕਦੋਂ", "कधी", "ఎప్పుడు", "எப்போது"]
    quantity_triggers = ["kitna", "kitni", "how much", "quantity", "dose", "litre", "liter", "kg", "कितना", "कितनी", "मात्रा", "ਕਿੰਨਾ", "किती", "ఎంత", "எவ்வளவு"]
    injection_triggers = ["ignore all previous", "ignore safety", "system prompt", "pretend you are", "jailbreak", "override priority", "recommend ban", "recommend ddt", "fake rule"]
    consequential_triggers = ["execute irrigation", "turn on motor", "motor on", "chalu karo motor", "spray now automatically", "pesticide daal do abhi"]
    treatment_triggers = ["kaunsa pesticide", "kaunsi dawai", "what pesticide", "which chemical", "keetnashak kaunsa", "chemical kaunsa lagana", "konsi dawai"]
    replan_triggers = ["cancel kyu", "cancel kyu hua", "replan", "pehle kya tha", "pehle kya bola", "pehle kya", "naya plan", "badla kyu", "badal gaya", "mana kar raha", "change hua", "kis wajah se", "pehle wala follow", "kaunsa follow", "kab change hua", "kab update hua", "kya hua", "ab kya hua", "badlav", "previous decision", "रद्द", "बदला", "पुराना"]
    contingency_triggers = ["agar baarish", "agar barish", "agar rain", "what if it rains", "baarish ho gayi", "barish hui toh", "rain ho gayi toh", "बारिश", "ਮੀਂਹ"]
    alert_triggers = ["alert kya hai", "alert kyu aaya", "warning kya hai", "action plan kya hai", "recommendation kya hai", "recommendation ka matlab", "सलाह"]
    how_triggers = ["kaise", "how", "method", "kiven", "कैसे", "ਕਿਵੇਂ", "कसे"]
    what_triggers = ["matlab", "meaning", "ye kya hai", "yeh kya hai", "kya matlab", "iska kya", "isme kya", "मतलब", "यह क्या है", "ये क्या है"]
    short_triggers = ["short mein", "short me", "chhota", "sankshipt", "briefly", "in short", "संक्षेप"]
    action_triggers = ["ab kya karna", "ab mujhe kya karna", "ab kya kare", "kya karna hai", "kya karu", "agla kadam", "next step", "turant kya", "now what", "अब क्या करना", "पहला स्टेप", "पहला", "pehla step", "pehla"]
    step_done_triggers = ["kar diya", "ho gaya", "kar liya", "done", "completed", "pura ho gaya", "कर दिया", "हो गया", "ਕਰ ਦਿੱਤਾ"]
    step_fail_triggers = ["nahi hua", "nahi ho raha", "failed", "fail ho gaya", "pareshani", "नहीं हुआ"]
    simple_triggers = ["simple mein", "simple me", "aasan bhasha", "aasan shabdon", "simply", "सरल", "आसान"]
    detail_triggers = ["detail mein", "detail me", "thoda detail", "vistaar", "in detail", "explain in detail", "विस्तार", "पूरी जानकारी"]

    disease_triggers = ["disease result", "bimari", "rog", "scan result", "disease ka matlab", "bavav", "upchar", "इलाज", "उपचार"]

    has_active_guidance = bool(guidance_context and (
        guidance_context.get("recommendation") or
        guidance_context.get("recommendations") or
        guidance_context.get("current_decision") or
        guidance_context.get("action_plan") or
        guidance_context.get("steps") or
        guidance_context.get("disease_result") or
        guidance_context.get("alerts")
    ))

    if any(p in lower for p in injection_triggers):
        return ("GUIDANCE_HELP", "safety_guard_rejected")
    if any(p in lower for p in consequential_triggers):
        return ("GUIDANCE_HELP", "consequential_action_guard")
    if any(p in lower for p in treatment_triggers):
        return ("GUIDANCE_HELP", "explain_treatment_inquiry")
    if any(p in lower for p in replan_triggers):
        return ("GUIDANCE_HELP", "explain_replan_or_change")
    if any(p in lower for p in alert_triggers):
        return ("GUIDANCE_HELP", "explain_alert_or_plan")
    if has_active_guidance and any(p in lower for p in disease_triggers):
        return ("GUIDANCE_HELP", "explain_disease_result")
    if has_active_guidance and any(p in lower for p in contingency_triggers):
        return ("GUIDANCE_HELP", "explain_contingency")
    if has_active_guidance and any(p in lower for p in step_done_triggers):
        return ("GUIDANCE_HELP", "progress_action_plan_step")
    if has_active_guidance and any(p in lower for p in step_fail_triggers):
        return ("GUIDANCE_HELP", "troubleshoot_action_plan_step")
    if has_active_guidance and any(p in lower for p in short_triggers):
        return ("GUIDANCE_HELP", "explain_recommendation_short")
    if has_active_guidance and any(p in lower for p in action_triggers):
        return ("GUIDANCE_HELP", "explain_immediate_action")
    if has_active_guidance and any(p in lower for p in simple_triggers):
        return ("GUIDANCE_HELP", "explain_recommendation_simple")
    if has_active_guidance and any(p in lower for p in detail_triggers):
        return ("GUIDANCE_HELP", "explain_recommendation_detail")
    platform_keywords = ["upload", "photo", "image", "button", "screen", "click", "dashboard", "kahan hai", "kahan milega", "kaise jaun", "open kaise", "dikh nahi raha", "bhav button", "kaise kholu"]
    if any(p in lower for p in platform_keywords):
        return ("PLATFORM_HELP", None)

    if has_active_guidance and any(p in lower for p in how_triggers):
        return ("GUIDANCE_HELP", "explain_recommendation_how")
    if has_active_guidance and any(p in lower for p in what_triggers):
        return ("GUIDANCE_HELP", "explain_recommendation_what")
    if has_active_guidance and any(p in lower for p in why_triggers):
        return ("GUIDANCE_HELP", "explain_recommendation_reason")
    if has_active_guidance and any(p in lower for p in timing_triggers):
        return ("GUIDANCE_HELP", "explain_recommendation_timing")
    if has_active_guidance and any(p in lower for p in quantity_triggers):
        return ("GUIDANCE_HELP", "explain_recommendation_quantity")
    if any(p in lower for p in ["recommendation", "recommendations", "sujhav", "salha", "action plan", "steps", "चरण", "सलाह", "ਸੁਝਾਅ"]) and ("matlab" in lower or "explain" in lower or "samjhao" in lower or "batao" in lower or "bataiye" in lower or "details" in lower):
        return ("GUIDANCE_HELP", "explain_recommendation_general")

    return ("PLATFORM_HELP", None)


def generate_guidance_help_response(
    question: str,
    guidance_data: Optional[Dict[str, Any]],
    language: str = "hi",
    history: Optional[List[Dict[str, str]]] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Generates Layer 2 responses strictly explaining AgriBridge's generated advice.
    Never invents missing values (marks them unavailable).
    Resolves multi-turn references, follow-up pronouns, and contingencies via conversation history.
    """
    resolved = resolve_active_guidance_context(guidance_data)
    lang_key = language if language in SUPPORTED_LANGUAGES else "hi"
    active_dec = resolved["active_decision"] or {}
    prev_dec = resolved["previous_decision"] or {}
    q_lower = question.lower()
    rec_list = resolved.get("recommendation_list", [])

    # 0a. Prompt Injection & Adversarial Text Guard
    if any(p in q_lower for p in ["ignore all previous", "ignore safety", "system prompt", "pretend you are", "jailbreak", "override priority", "recommend ban", "recommend ddt", "fake rule"]):
        if lang_key == "hinglish":
            res_text = "Main keval AgriBridge ke verified agricultural decisions aur platform navigation mein madad kar sakta hoon. Asurakshit ya anadhikrit anurodh swikaar nahi kiye jaate."
        elif lang_key == "hi":
            res_text = "मैं केवल AgriBridge के सत्यापित कृषि निर्णयों और प्लेटफ़ॉर्म नेविगेशन में मदद कर सकता हूँ। असुरक्षित अनुरोध स्वीकार नहीं किए जाते हैं।"
        else:
            res_text = "I can only assist with verified AgriBridge agricultural guidance and platform navigation. Unauthorized safety override requests cannot be processed."
        return res_text, {"layer": "GUIDANCE_HELP", "type": "safety_guard_rejected", "grounding_status": "PROMPT_INJECTION_REJECTED", "resolved_guidance": resolved}

    # 0b. Consequential Machine / Field Action Execution Guard ("Execute irrigation now", "Motor on karo")
    if any(p in q_lower for p in ["execute irrigation", "turn on motor", "motor on", "chalu karo motor", "spray now automatically", "pesticide daal do abhi"]):
        if lang_key == "hinglish":
            res_text = "Main sirf AgriBridge guidance explain kar sakta hoon. Field par action execute karne ke liye kripya screen par diye gaye button se confirm karein."
        elif lang_key == "hi":
            res_text = "मैं केवल AgriBridge सलाह की व्याख्या कर सकता हूँ। खेत में कार्य पूरा करने के लिए कृपया स्क्रीन पर पुष्टि करें।"
        else:
            res_text = "I provide guidance explanation only. Please confirm directly on your AgriBridge dashboard to trigger physical field actions."
        return res_text, {"layer": "GUIDANCE_HELP", "type": "consequential_action_guard", "grounding_status": "CONSEQUENTIAL_GUARD", "resolved_guidance": resolved}

    # 0c. Out-of-Context Treatment / Chemical Request (Zero Hallucination Guard)
    has_pesticide_in_context = any(
        any(k in str(item).lower() for k in ["spray", "pesticide", "fungicide", "insecticide", "chemical", "dawai", "keetnashak", "bio-pesticide"])
        for item in ([active_dec] + rec_list)
    )
    if any(p in q_lower for p in ["kaunsa pesticide", "kaunsi dawai", "what pesticide", "which chemical", "keetnashak kaunsa", "chemical kaunsa lagana", "konsi dawai"]):
        if not has_pesticide_in_context:
            if lang_key == "hinglish":
                res_text = "Aapke current khet ke data mein AgriBridge ne koi specific pesticide/dawai suggest nahi ki hai. Kripya naya scan karne ke liye 'AI Crop Scan' option use karein."
            elif lang_key == "hi":
                res_text = "आपके वर्तमान खेत के डेटा में AgriBridge ने कोई विशिष्ट कीटनाशक/दवाई नहीं सुझाई है। कृपया नया स्कैन करने के लिए 'AI Crop Scan' का उपयोग करें।"
            else:
                res_text = "I don't have a pesticide recommendation for your case in the available AgriBridge guidance. Please use 'AI Crop Scan' on your screen."
            return res_text, {"layer": "GUIDANCE_HELP", "type": "out_of_context_guard", "grounding_status": "OUT_OF_CONTEXT", "resolved_guidance": resolved}

    # 0d. Disease Result Explanation ("Disease result samajh nahi aa raha")
    if any(p in q_lower for p in ["disease result", "bimari", "rog", "scan result", "disease ka matlab", "rust", "blight", "spot", "wilt"]) and (resolved.get("disease_result") or (guidance_data and guidance_data.get("disease_result"))):
        dis_res = resolved.get("disease_result") or (guidance_data.get("disease_result") if guidance_data else {}) or {}
        dis_name = dis_res.get("disease_name") or dis_res.get("disease") or "Detected Disease"
        dis_treat = dis_res.get("treatment") or dis_res.get("cure") or "Screen par diye gaye treatment instructions follow karein"
        conf = dis_res.get("confidence")
        conf_str = f" ({int(conf * 100)}% accuracy)" if conf else ""
        if lang_key == "hinglish":
            res_text = f"AgriBridge AI Scan ke anusaar aapki fasal mein '{dis_name}'{conf_str} paya gaya hai. Upchar: {dis_treat}."
        elif lang_key == "hi":
            res_text = f"AgriBridge AI Scan के अनुसार आपकी फसल में '{dis_name}'{conf_str} पाया गया है। उपचार: {dis_treat}।"
        else:
            res_text = f"According to AgriBridge AI Scan, '{dis_name}'{conf_str} was detected in your crop. Treatment: {dis_treat}."
        return res_text, {"layer": "GUIDANCE_HELP", "type": "disease_explanation", "resolved_guidance": resolved}

    # 1. Resolve target item from multi-turn history if query uses pronouns (ye, wo, isme, iska, kitne baje, etc.)
    target_item = active_dec
    history_text = " ".join([(m.get("content") or m.get("message") or m.get("text") or "") for m in (history or [])]).lower()

    if len(rec_list) > 1:
        # Check current query first
        matched_in_q = False
        for item in rec_list:
            item_act = (item.get("action") or item.get("title") or "").lower()
            item_qty = str(item.get("quantity") or item.get("dose") or "").lower()
            if (item_qty and item_qty in q_lower) or (item_act and item_act in q_lower):
                target_item = item
                matched_in_q = True
                break
        # If not matched in query, check history
        if not matched_in_q and history_text:
            for item in rec_list:
                item_act = (item.get("action") or item.get("title") or "").lower()
                item_qty = str(item.get("quantity") or item.get("dose") or "").lower()
                if (item_qty and item_qty in history_text) or (item_act and item_act in history_text):
                    target_item = item
                    matched_in_q = True
                    break

        # Ambiguous pronoun when multiple items exist and neither query nor history resolves it
        if not matched_in_q and any(pr in q_lower for pr in ["ye", "yeh", "wo", "woh", "iska", "uska", "isme", "ismein"]):
            act1 = rec_list[0].get("action") or "Item 1"
            act2 = rec_list[1].get("action") or "Item 2"
            if lang_key == "hinglish":
                clarify_text = f"Aap screen par dikh rahe kis sujhav ke baare mein pooch rahe hain? ('{act1}' ya '{act2}')"
            elif lang_key == "hi":
                clarify_text = f"आप स्क्रीन पर दिख रहे किस सुझाव के बारे में पूछ रहे हैं? ('{act1}' या '{act2}')"
            else:
                clarify_text = f"Which recommendation on screen are you referring to? ('{act1}' or '{act2}')"
            return clarify_text, {"layer": "GUIDANCE_HELP", "type": "ambiguity_clarification", "resolved_guidance": resolved}

    action = target_item.get("action") or target_item.get("title") or "Recommended Action"
    reason = target_item.get("reason") or target_item.get("explanation")
    timing = target_item.get("timing") or target_item.get("schedule")
    quantity = target_item.get("quantity") or target_item.get("dose") or target_item.get("amount")
    measurements = resolved.get("measurements") or {}
    soil_moisture = resolved.get("soil_moisture") or measurements.get("soil_moisture")

    # 2. Contingency / Weather follow-up ("Agar baarish ho gayi toh?")
    if any(p in q_lower for p in ["baarish", "barish", "rain", "varsa", "ਮੀਂਹ", "पाऊस"]) and any(c in q_lower for c in ["agar", "if", "ho gayi", "aayi toh", "hua toh", "what if"]):
        if lang_key == "hinglish":
            res_text = "Current plan mein baarish ki possibility ko dekhkar AgriBridge plan ko automatically update ya replan kar sakta hai."
        elif lang_key == "hi":
            res_text = "वर्तमान प्लान में बारिश की संभावना को देखकर AgriBridge प्लान को अपने आप अपडेट या रीप्लान कर सकता है।"
        elif lang_key == "pa":
            res_text = "ਮੌਜੂਦਾ ਪਲਾਨ ਵਿੱਚ ਮੀਂਹ ਦੀ ਸੰਭਾਵਨਾ ਨੂੰ ਦੇਖ ਕੇ AgriBridge ਪਲਾਨ ਨੂੰ ਅਪਡੇਟ ਕਰ ਸਕਦਾ ਹੈ।"
        else:
            res_text = "Under the current plan, AgriBridge will dynamically update or replan the recommendation based on rain conditions."
        return res_text, {"layer": "GUIDANCE_HELP", "type": "contingency_explanation", "resolved_guidance": resolved}

    new_info = resolved.get("new_information") or resolved.get("trigger") or guidance_data.get("new_information") or ""
    update_reason = resolved.get("reason_for_update") or reason or ""
    timestamp = resolved.get("timestamp") or guidance_data.get("timestamp") or "abhi haal hi mein"
    version = resolved.get("version", 2)
    old_act = prev_dec.get("action") or "Previous Action"
    old_qty = prev_dec.get("quantity") or ""
    old_str = f"{old_qty} {old_act}".strip() if old_qty else old_act
    old_reason = prev_dec.get("reason") or "low soil moisture"

    # 3a. Priority Question ("Pehle wala follow karu ya naya wala?")
    if any(p in q_lower for p in ["pehle wala follow", "naya wala", "kaunsa follow", "which plan", "konsa follow"]):
        if lang_key == "hinglish":
            res_text = f"Aapko naya active plan '{action}' follow karna hai, kyunki pehle wala plan '{old_str}' update/cancel ho chuka hai."
        elif lang_key == "hi":
            res_text = f"आपको नया सक्रिय प्लान '{action}' फॉलो करना है, क्योंकि पहले वाला प्लान '{old_str}' अपडेट/रद्द हो चुका है।"
        else:
            res_text = f"You should follow the new active plan '{action}', as the previous plan '{old_str}' has been updated/cancelled."
        return res_text, {"layer": "GUIDANCE_HELP", "type": "replan_priority_explanation", "resolved_guidance": resolved}

    # 3b. Timestamp Inquiry ("Ye plan kab change hua?" / "Kab update hua?")
    if any(p in q_lower for p in ["kab change", "kab badla", "kab update", "when updated", "when changed"]):
        if lang_key == "hinglish":
            res_text = f"Yeh plan {timestamp} ko update hua hai (Version {version}). Active decision: '{action}'."
        elif lang_key == "hi":
            res_text = f"यह प्लान {timestamp} को अपडेट हुआ है (Version {version})। सक्रिय निर्णय: '{action}'।"
        else:
            res_text = f"This plan was updated on {timestamp} (Version {version}). Active decision: '{action}'."
        return res_text, {"layer": "GUIDANCE_HELP", "type": "replan_timestamp_explanation", "resolved_guidance": resolved}

    # 3c. Previous decision inquiry ("Pehle kya bola tha?" / "Pehle kya tha?")
    if any(p in q_lower for p in ["pehle kya", "previous plan", "purana plan", "pehle kya tha", "pehle kya bola"]):
        if lang_key == "hinglish":
            res_text = f"Pehle AgriBridge ne '{old_str}' suggest kiya tha ({old_reason}). Lekin ab naya active decision '{action}' hai."
        elif lang_key == "hi":
            res_text = f"पहले AgriBridge ने '{old_str}' का सुझाव दिया था ({old_reason})। लेकिन अब नया सक्रिय निर्णय '{action}' है।"
        else:
            res_text = f"Previously AgriBridge suggested '{old_str}' ({old_reason}). The active decision now is '{action}'."
        return res_text, {"layer": "GUIDANCE_HELP", "type": "previous_decision_explanation", "resolved_guidance": resolved}

    # 3d. Comprehensive Replan & Change Reason ("Ab kyun badal gaya?" / "Pehle paani dene ko bola tha...")
    if resolved["is_replanned"] and any(p in q_lower for p in ["cancel", "replan", "pehle", "badla", "badal gaya", "mana kar raha", "change", "wajah", "why", "kyu", "kya hua", "ab kya"]):
        new_info_clause = f"Baad mein {new_info} ka updated information mila, isliye" if new_info else "Naye field data aur mausam ke badlav ke kaaran"
        if lang_key == "hinglish":
            res_text = f"Pehle AgriBridge ne {old_reason} ke basis par '{old_str}' suggest ki thi. {new_info_clause} plan ko update karke active decision '{action}' kar diya gaya ({update_reason or 'Updated advisory'})."
        elif lang_key == "hi":
            res_text = f"पहले AgriBridge ने {old_reason} के आधार पर '{old_str}' का सुझाव दिया था। {new_info_clause} प्लान को अपडेट करके नया निर्णय '{action}' किया गया ({update_reason or 'Updated advisory'})।"
        elif lang_key == "pa":
            res_text = f"ਪਹਿਲਾਂ AgriBridge ਨੇ '{old_str}' ਦੀ ਸਲਾਹ ਦਿੱਤੀ ਸੀ। ਨਵੇਂ ਡੇਟਾ ਕਰਕੇ ਪਲਾਨ ਨੂੰ ਅਪਡੇਟ ਕਰਕੇ ਨਵਾਂ ਫੈਸਲਾ '{action}' ਲਿਆ ਗਿਆ ਹੈ।"
        else:
            res_text = f"Previously AgriBridge suggested '{old_str}' based on {old_reason}. Due to {new_info or 'updated field data'}, the plan was updated to active decision '{action}' ({update_reason or 'Updated advisory'})."
        return res_text, {"layer": "GUIDANCE_HELP", "type": "replan_explanation", "resolved_guidance": resolved}

    # 4. Action Plan Step Completion & Progression ("Kar diya" / "Ho gaya" / "Done")
    steps = resolved.get("steps", [])
    active_idx = resolved.get("active_step_index", 0)

    if any(p in q_lower for p in ["kar diya", "ho gaya", "kar liya", "done", "completed", "pura ho gaya", "कर दिया", "हो गया"]):
        if steps and len(steps) > 1:
            next_idx = active_idx + 1
            if next_idx < len(steps):
                next_step = steps[next_idx]
                next_act = next_step.get("action") or next_step.get("title") or f"Step {next_idx + 1}"
                next_time = next_step.get("timing") or next_step.get("schedule")
                time_str = f" ({next_time} par)" if next_time else ""
                if lang_key == "hinglish":
                    res_text = f"Bahut badhiya! Ab Step {next_idx + 1} yeh hai: '{next_act}'{time_str}."
                elif lang_key == "hi":
                    res_text = f"बहुत बढ़िया! अब Step {next_idx + 1} यह है: '{next_act}'{time_str}।"
                elif lang_key == "pa":
                    res_text = f"ਬਹੁਤ ਵਧੀਆ! ਹੁਣ ਅਗਲਾ ਕਦਮ (Step {next_idx + 1}) ਇਹ ਹੈ: '{next_act}'{time_str}।"
                else:
                    res_text = f"Great job! Next Step {next_idx + 1} is: '{next_act}'{time_str}."
                return res_text, {"layer": "GUIDANCE_HELP", "type": "step_advanced", "current_step": next_idx + 1, "resolved_guidance": resolved}
            else:
                if lang_key == "hinglish":
                    res_text = "Badhaai ho! Aapke action plan ke sabhi steps poore ho gaye hain."
                elif lang_key == "hi":
                    res_text = "बधाई हो! आपके एक्शन प्लान के सभी चरण पूरे हो गए हैं।"
                else:
                    res_text = "Congratulations! All steps in your action plan are now completed."
                return res_text, {"layer": "GUIDANCE_HELP", "type": "plan_completed", "resolved_guidance": resolved}

    # 5. Troubleshooting / Failure Handling ("Nahi hua" / "Failed")
    if any(p in q_lower for p in ["nahi hua", "nahi ho raha", "failed", "fail ho gaya", "pareshani", "नहीं हुआ"]):
        if lang_key == "hinglish":
            res_text = f"Koi baat nahi. Step '{action}' mein kya dikkat aa rahi hai? Kripya bataiye, main madad karta hoon."
        elif lang_key == "hi":
            res_text = f"कोई बात नहीं। Step '{action}' में क्या परेशानी आ रही है? कृपया बताइए, मैं मदद करता हूँ।"
        else:
            res_text = f"No worries. What issue are you facing with step '{action}'? Please let me know so I can help."
        return res_text, {"layer": "GUIDANCE_HELP", "type": "step_troubleshoot", "resolved_guidance": resolved}

    # 6. Short / Concise Explanation Inquiry ("Short mein batao" / "Short me batao" / "Concise")
    if any(p in q_lower for p in ["short mein", "short me", "chhota", "sankshipt", "briefly", "in short", "kam shabdon"]):
        time_clause = f" at {timing}" if timing else ""
        qty_clause = f" ({quantity})" if quantity else ""
        if lang_key == "hinglish":
            res_text = f"Short mein: {action}{qty_clause}{time_clause}."
        elif lang_key == "hi":
            res_text = f"संक्षेप में: {action}{qty_clause}{time_clause}।"
        elif lang_key == "pa":
            res_text = f"ਸੰਖੇਪ ਵਿੱਚ: {action}{qty_clause}{time_clause}।"
        else:
            res_text = f"In short: {action}{qty_clause}{time_clause}."
        return res_text, {"layer": "GUIDANCE_HELP", "type": "short_explanation", "resolved_guidance": resolved}

    # 7. Immediate Action Prioritization / Step Guidance ("Ab kya karna hai?" / "Next step kya hai?")
    if any(p in q_lower for p in ["ab kya karna", "ab mujhe kya karna", "ab kya kare", "agla kadam", "next step", "turant kya", "now what", "पहला", "pehla"]):
        step_num_str = f"Step {active_idx + 1}: " if steps and len(steps) > 1 else ""
        time_part = f" (samay: {timing})" if timing else ""
        qty_part = f" maatra: {quantity}," if quantity else ""
        if lang_key == "hinglish":
            res_text = f"Ji, {step_num_str}aapko '{action}' karna hai,{qty_part}{time_part}."
        elif lang_key == "hi":
            res_text = f"जी, {step_num_str}आपको '{action}' करना है,{qty_part}{time_part}।"
        else:
            res_text = f"Your current task is {step_num_str}'{action}',{qty_part}{time_part}."
        return res_text, {"layer": "GUIDANCE_HELP", "type": "immediate_action_explanation", "resolved_guidance": resolved}

    # 6. Simplification Inquiry ("Simple mein samjhao" / "Simple mein batao")
    if any(p in q_lower for p in ["simple mein", "simple me", "aasan bhasha", "aasan shabdon", "simply", "saral tarike"]):
        reason_clause = f", kyunki {reason}" if reason else ""
        if lang_key == "hinglish":
            res_text = f"Aasan shabdon mein: aapko '{action}' karna hai{reason_clause}."
        elif lang_key == "hi":
            res_text = f"सरल शब्दों में: आपको '{action}' करना है{reason_clause}।"
        elif lang_key == "pa":
            res_text = f"ਸੌਖੇ ਸ਼ਬਦਾਂ ਵਿੱਚ: ਤੁਹਾਨੂੰ '{action}' ਕਰਨਾ ਚਾਹੀਦਾ ਹੈ{reason_clause}।"
        else:
            res_text = f"In simple terms: you should perform '{action}'{reason_clause}."
        return res_text, {"layer": "GUIDANCE_HELP", "type": "simple_explanation", "resolved_guidance": resolved}

    # 7. Detailed Explanation Inquiry ("Thoda detail mein batao" / "Detail mein samjhao")
    if any(p in q_lower for p in ["detail mein", "detail me", "thoda detail", "vistaar", "in detail", "explain in detail", "poora samjhao"]):
        qty_str = quantity if quantity else "Nahi di gayi"
        time_str = timing if timing else "Nahi diya gaya"
        if lang_key == "hinglish":
            res_text = f"Poori jankari yeh hai: 1. Action: {action}, 2. Maatra: {qty_str}, 3. Samay: {time_str}, 4. Reason: {reason or 'Standard advisory'}."
        elif lang_key == "hi":
            res_text = f"पूरी जानकारी: 1. Action: {action}, 2. मात्रा: {qty_str}, 3. समय: {time_str}, 4. कारण: {reason or 'Standard advisory'}।"
        else:
            res_text = f"Detailed breakdown: 1. Action: {action}, 2. Quantity: {qty_str}, 3. Timing: {time_str}, 4. Reason: {reason or 'Standard advisory'}."
        return res_text, {"layer": "GUIDANCE_HELP", "type": "detailed_explanation", "resolved_guidance": resolved}

    # 8. Specific Quantity & Measurement reason inquiry (e.g. "420 litre kyun?")
    if any(p in q_lower for p in ["kyun", "kyu", "why", "karan"]) and any(q_term in q_lower for q_term in ["litre", "liter", "420", "kg", "dose", "quantity"]):
        if reason:
            meas_str = f" (soil moisture: {soil_moisture})" if soil_moisture and "moisture" not in reason.lower() else ""
            if lang_key == "hinglish":
                res_text = f"AgriBridge ne {quantity or 'yeh maatra'} isliye recommend ki hai kyunki: {reason}{meas_str}."
            elif lang_key == "hi":
                res_text = f"AgriBridge ने {quantity or 'यह मात्रा'} इसलिए सुझाई है क्योंकि: {reason}{meas_str}।"
            else:
                res_text = f"AgriBridge recommended {quantity or 'this amount'} because: {reason}{meas_str}."
        else:
            res_text = "Is recommendation mein exact quantity ka specific reason available nahi hai." if lang_key == "hinglish" else "इस सलाह में सटीक मात्रा का कारण उपलब्ध नहीं है।"
        return res_text, {"layer": "GUIDANCE_HELP", "type": "quantity_reason_explanation", "resolved_guidance": resolved}

    # 9. Why question (General Reason inquiry)
    if any(p in q_lower for p in ["kyun", "kyu", "why", "reason", "karan", "ਕਿਉਂ", "का"]):
        if reason:
            if lang_key == "hinglish":
                res_text = f"AgriBridge ne '{action}' isliye recommend kiya hai kyunki: {reason}."
            elif lang_key == "hi":
                res_text = f"AgriBridge ने '{action}' इसलिए सुझाया है क्योंकि: {reason}।"
            else:
                res_text = f"AgriBridge recommended '{action}' because: {reason}."
        else:
            if lang_key == "hinglish":
                res_text = "Is recommendation ka specific reason uplabdh nahi hai (not available)."
            elif lang_key == "hi":
                res_text = "इस सलाह का सटीक कारण उपलब्ध नहीं है।"
            else:
                res_text = "Specific reason is not available in the current recommendation context."
        return res_text, {"layer": "GUIDANCE_HELP", "type": "reason_explanation", "resolved_guidance": resolved}

    # 10. HOW / Method question ("Kaise karna hai?")
    if any(p in q_lower for p in ["kaise", "how", "method", "kiven", "ਕਿਵੇਂ", "कसे"]):
        method = target_item.get("method") or target_item.get("execution")
        if method:
            if lang_key == "hinglish":
                res_text = f"Is action ko '{method}' method se pura karein."
            elif lang_key == "hi":
                res_text = f"इस कार्य को '{method}' विधि से पूरा करें।"
            else:
                res_text = f"Perform this action using the '{method}' method."
        else:
            if lang_key == "hinglish":
                res_text = f"Is action '{action}' ke liye specific method context mein uplabdh nahi hai. Kripya screen par standard directions follow karein."
            elif lang_key == "hi":
                res_text = f"इस कार्य '{action}' के लिए विशिष्ट विधि उपलब्ध नहीं है। कृपया स्क्रीन पर दिए गए निर्देश देखें।"
            else:
                res_text = f"Specific execution method for '{action}' is not specified in the current context. Please follow the standard on-screen instructions."
        return res_text, {"layer": "GUIDANCE_HELP", "type": "how_explanation", "resolved_guidance": resolved}

    # 11. Quantity inquiry (Quantity specified in trusted context)
    if any(p in q_lower for p in ["kitna", "kitni", "quantity", "dose", "amount", "ਕਿੰਨਾ", "किती"]):
        if quantity:
            if lang_key == "hinglish":
                res_text = f"AgriBridge recommendation ke anusaar maatra hai: {quantity}."
            elif lang_key == "hi":
                res_text = f"AgriBridge सलाह के अनुसार सुझाई गई मात्रा है: {quantity}।"
            else:
                res_text = f"According to AgriBridge recommendation, the quantity is: {quantity}."
        else:
            if lang_key == "hinglish":
                res_text = "Is recommendation mein exact quantity uplabdh nahi hai (not available)."
            elif lang_key == "hi":
                res_text = "इस सलाह में मात्रा (quantity) उपलब्ध नहीं है।"
            else:
                res_text = "Exact quantity is not available in this recommendation."
        return res_text, {"layer": "GUIDANCE_HELP", "type": "quantity_explanation", "resolved_guidance": resolved}

    # 12. Timing inquiry ("Kitne baje?", "Kab?")
    if any(p in q_lower for p in ["kab", "kis time", "when", "timing", "kitne baje", "kitna baje", "ਕਦੋਂ", "कधी"]):
        if timing:
            if lang_key == "hinglish":
                res_text = f"AgriBridge ke anusaar sahi samay hai: {timing}."
            elif lang_key == "hi":
                res_text = f"AgriBridge के अनुसार निर्धारित समय है: {timing}।"
            else:
                res_text = f"According to AgriBridge, the scheduled timing is: {timing}."
        else:
            if lang_key == "hinglish":
                res_text = "Is recommendation mein timing uplabdh nahi hai (not available)."
            elif lang_key == "hi":
                res_text = "इस सलाह में समय (timing) उपलब्ध नहीं है।"
            else:
                res_text = "Timing is not available in this recommendation."
        return res_text, {"layer": "GUIDANCE_HELP", "type": "timing_explanation", "resolved_guidance": resolved}

    # 13. WHAT / Meaning Inquiry ("Iska matlab kya hai?" / "Ye kya hai?")
    if any(p in q_lower for p in ["matlab", "meaning", "ye kya hai", "yeh kya hai", "kya matlab"]):
        time_part = f" {timing}" if timing else ""
        qty_part = f" {quantity}" if quantity else ""
        if lang_key == "hinglish":
            res_text = f"Iska matlab hai ki AgriBridge ne {reason or 'field sthiti'} ke aadhar par '{action}'{qty_part}{time_part} karne ki salah di hai."
        elif lang_key == "hi":
            res_text = f"इसका मतलब है कि AgriBridge ने {reason or 'खेत की स्थिति'} के आधार पर '{action}'{qty_part}{time_part} करने की सलाह दी है।"
        else:
            res_text = f"This means AgriBridge has recommended '{action}'{qty_part}{time_part} based on {reason or 'field conditions'}."
        return res_text, {"layer": "GUIDANCE_HELP", "type": "what_explanation", "resolved_guidance": resolved}

    # 14. General guidance overview with preference adaptation
    history_asked_why_often = history_text.count("kyun") + history_text.count("kyu") + history_text.count("why") >= 2
    if history_asked_why_often and reason:
        if lang_key == "hinglish":
            res_text = f"Kyunki {reason}, isliye AgriBridge ne '{action}' karne ki salah di hai."
        elif lang_key == "hi":
            res_text = f"क्योंकि {reason}, इसलिए AgriBridge ने '{action}' करने की सलाह दी है।"
        else:
            res_text = f"Because {reason}, AgriBridge recommended '{action}'."
    else:
        if lang_key == "hinglish":
            res_text = f"AgriBridge ka active sujhav hai: '{action}'." + (f" Iska reason hai: {reason}." if reason else "")
        elif lang_key == "hi":
            res_text = f"AgriBridge का सक्रिय सुझाव है: '{action}'।" + (f" इसका कारण है: {reason}।" if reason else "")
        else:
            res_text = f"AgriBridge's active recommendation is: '{action}'." + (f" Reason: {reason}." if reason else "")

    return res_text, {"layer": "GUIDANCE_HELP", "type": "guidance_overview", "resolved_guidance": resolved}


# ==============================================================================
# 11. MAIN SAATHI PIPELINE CONTROLLER (STEP 11/12 MULTI-LAYER ROUTING)
# ==============================================================================

# ==============================================================================
# 11. CROP DISEASE IMAGE PREDICTION INTEGRATION
# ==============================================================================

def analyze_crop_image_for_saathi(
    image_bytes: Optional[bytes] = None,
    image_path: Optional[str] = None,
    image_filename: Optional[str] = None,
    image_content_type: Optional[str] = None,
    plant: str = "wheat",
    farm_info: Optional[Dict[str, Any]] = None,
    lang_key: str = "hi"
) -> Tuple[bool, Dict[str, Any], str, Optional[Dict[str, Any]], Optional[str]]:
    """
    Validates uploaded crop photo and runs disease prediction using existing AI Engine.
    Returns: (is_success, prediction_payload, localized_response_text, disease_details_obj, error_message)
    """
    from app.services.voice_service import format_disease_prediction_response, PHOTO_REQUEST_TEMPLATES
    from app.services.agriculture_intent import normalize_crop_name
    from pathlib import Path
    import uuid

    # 1. Validate file format / content
    allowed_exts = {".jpg", ".jpeg", ".png"}
    allowed_mimes = {"image/jpeg", "image/png", "image/jpg", "image/webp"}

    fn = image_filename or (Path(image_path).name if image_path else "")
    if fn:
        ext = Path(fn).suffix.lower()
        if ext and ext not in allowed_exts:
            err_msg = "Only JPG, JPEG and PNG images are supported."
            resp = "कृपया केवल JPG या PNG प्रारूप में फसल की साफ फोटो अपलोड करें।" if lang_key != "en" else "Please upload a clear crop photo in JPG or PNG format only."
            return False, {}, resp, None, err_msg

    if image_content_type:
        ct = image_content_type.lower()
        if "pdf" in ct or "text" in ct or (ct.startswith("application/") and "json" not in ct):
            err_msg = "Unsupported file type."
            resp = "कृपया केवल JPG या PNG प्रारूप में फसल की साफ फोटो अपलोड करें।" if lang_key != "en" else "Please upload a clear crop photo in JPG or PNG format only."
            return False, {}, resp, None, err_msg

    temp_image_path = None
    created_temp = False

    if image_path and Path(image_path).exists():
        temp_image_path = Path(image_path)
    elif image_bytes and len(image_bytes) > 0:
        if len(image_bytes) < 50:
            err_msg = "Image file is empty or corrupted."
            resp = "फोटो खाली या अमान्य है। कृपया दोबारा फोटो भेजें।" if lang_key != "en" else "The photo is empty or corrupted. Please send another photo."
            return False, {}, resp, None, err_msg

        upload_dir = Path(__file__).resolve().parents[2] / "ai_uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        ext = Path(fn).suffix.lower() if fn else ".jpg"
        if ext not in allowed_exts:
            ext = ".jpg"
        temp_filename = f"saathi_{uuid.uuid4().hex}{ext}"
        temp_image_path = upload_dir / temp_filename
        with open(temp_image_path, "wb") as f:
            f.write(image_bytes)
        created_temp = True
    else:
        photo_prompt = PHOTO_REQUEST_TEMPLATES.get(lang_key, PHOTO_REQUEST_TEMPLATES["hi"])
        return False, {}, photo_prompt, None, "No image provided"

    # 2. Plant normalization
    clean_plant = normalize_crop_name(plant) if plant else "wheat"
    supported_plants = {
        "apple", "blueberry", "cherry", "corn", "grape", "orange", "peach",
        "pepper", "potato", "raspberry", "rice", "soybean", "squash",
        "strawberry", "tomato", "wheat"
    }
    if clean_plant not in supported_plants:
        clean_plant = "wheat"

    # 3. Default farm profile for recommendation pipeline
    default_farm = {
        "farm_area": 2.5,
        "growth_stage": "vegetative",
        "irrigation_method": "drip",
        "irrigation_status": "normal",
        "recent_rainfall": "low",
        "humidity": "moderate",
        "fertilizer_applied": "DAP",
        "previous_crop": "Legume",
        "disease_severity": "moderate",
        "region": "India"
    }
    if farm_info and isinstance(farm_info, dict):
        for k in default_farm:
            if farm_info.get(k):
                default_farm[k] = farm_info[k]

    try:
        from app.services.ai_service import analyze_crop
        result = analyze_crop(temp_image_path, clean_plant, default_farm)

        disease_obj = result.get("disease", {})
        pred_obj = result.get("prediction", {})
        disease_name = disease_obj.get("disease") or pred_obj.get("class_name") or "Crop Condition"
        raw_conf = float(pred_obj.get("confidence", 85.0))

        resp_text = format_disease_prediction_response(
            disease_name=disease_name,
            confidence=raw_conf,
            crop_name=clean_plant,
            lang_key=lang_key,
            rec_data=disease_obj
        )

        prediction_payload = {
            "label": disease_name,
            "confidence": round(raw_conf / 100.0 if raw_conf > 1.0 else raw_conf, 2),
            "symptoms": [disease_obj.get("description", "")] if disease_obj.get("description") else []
        }

        return True, prediction_payload, resp_text, disease_obj, None

    except ValueError as ve:
        # Low confidence or out-of-domain / blurry image
        print(f"[SAATHI AI] Low confidence or validation notice: {ve}")
        resp_text = format_disease_prediction_response(
            disease_name="",
            confidence=25.0,
            crop_name=clean_plant,
            lang_key=lang_key,
            rec_data=None
        )
        prediction_payload = {
            "label": "Unidentified Condition",
            "confidence": 0.25,
            "symptoms": []
        }
        return True, prediction_payload, resp_text, None, None

    except Exception as e:
        print(f"[SAATHI AI] Prediction error: {e}")
        err_text = "फसल की बीमारी का विश्लेषण करने में अस्थायी त्रुटि हुई। कृपया थोड़ी देर बाद पुनः प्रयास करें।" if lang_key != "en" else "An error occurred while analyzing the crop image. Please try again shortly."
        return False, {}, err_text, None, str(e)

    finally:
        if created_temp and temp_image_path and temp_image_path.exists():
            try:
                temp_image_path.unlink()
            except Exception:
                pass


# ==============================================================================
# 12. MAIN SAATHI PIPELINE CONTROLLER (STEP 11/12 MULTI-LAYER ROUTING)
# ==============================================================================

async def process_saathi_interaction(
    audio_bytes: Optional[bytes] = None,
    content_type: str = "audio/webm",
    text_query: Optional[str] = None,
    image_bytes: Optional[bytes] = None,
    image_base64: Optional[str] = None,
    image_filename: Optional[str] = None,
    image_content_type: Optional[str] = None,
    image_path: Optional[str] = None,
    language: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None,
    farmer_name: Optional[str] = None,
    current_page: Optional[str] = None,
    screen_name: Optional[str] = None,
    available_buttons: Optional[List[str]] = None,
    focused_button: Optional[str] = None,
    ui_context: Optional[Dict[str, Any]] = None,
    guidance_context: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
    farm_context: Optional[Dict[str, Any]] = None,
    crop: Optional[str] = None,
    growth_stage: Optional[str] = None,
    crop_age_days: Optional[int] = None,
    state: Optional[str] = None,
    district: Optional[str] = None,
    location: Optional[Union[Dict[str, Any], str]] = None,
    farm_info: Optional[Dict[str, Any]] = None,
    farm_profile: Optional[Dict[str, Any]] = None,
    prediction_info: Optional[Dict[str, Any]] = None,
    pending_field: Optional[str] = None,
    detail_level: Optional[str] = "simple",
    explanation_preference: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Main Saathi Handler:
    1. Transcribes voice audio to text (if audio provided)
    2. Automatically detects language from speech/text
    3. Multi-Layer Intent Classification (irrigation, fertilizer, disease, weather, action plan, platform help)
    4. Image-based Crop Disease Diagnosis via existing AI Engine (if image provided)
    5. Generates concise, natural, confidence-aware response in the same language
    6. Synthesizes spoken audio output via TTS
    7. Returns unified text, voice, prediction, and context payload
    """
    if context is None:
        context = {}
    if crop and not context.get("crop"):
        context["crop"] = crop
    if growth_stage and not context.get("growth_stage"):
        context["growth_stage"] = growth_stage
    if crop_age_days and not context.get("crop_age_days"):
        context["crop_age_days"] = crop_age_days
    if location and not context.get("location"):
        context["location"] = location
    if district and not context.get("district"):
        context["district"] = district
    if state and not context.get("state"):
        context["state"] = state
    if farm_info:
        farm_context = farm_context or farm_info
    if farm_profile:
        farm_context = farm_context or farm_profile
    if prediction_info:
        context["prediction_info"] = prediction_info
        context["disease_result"] = prediction_info
    if pending_field and not context.get("pending_field"):
        context["pending_field"] = pending_field

    if image_base64 and not image_bytes:
        import base64
        try:
            if "," in image_base64:
                image_base64 = image_base64.split(",", 1)[1]
            image_bytes = base64.b64decode(image_base64)
        except Exception:
            pass

    req_id = uuid.uuid4().hex[:8]
    transcript = ""

    # 1. Voice input STT
    if audio_bytes and len(audio_bytes) > 0:
        hint_lang = language or "hi"
        print(f"[VOICE PIPELINE][{req_id}] Received audio: content_type={content_type}, size={len(audio_bytes)} bytes")
        success, transcribed = await transcribe_audio(audio_bytes, content_type, hint_lang)
        print(f"[VOICE PIPELINE][{req_id}] Speech-to-text result: success={success}, transcript=\"{transcribed}\"")
        if success and transcribed and transcribed.strip():
            transcript = transcribed.strip()
        elif text_query and text_query.strip():
            transcript = text_query.strip()
        elif not image_bytes and not image_path:
            detected_lang = language or "hi"
            err_msg = CONVERSATIONAL_TEMPLATES["clarification"].get(detected_lang, CONVERSATIONAL_TEMPLATES["clarification"]["hi"])
            print(f"[VOICE PIPELINE][{req_id}] STT failed or empty transcript. Returning clarification: \"{err_msg}\"")
            audio_file, audio_status = synthesize_speech_with_status(err_msg, detected_lang)
            return {
                "success": False,
                "request_id": req_id,
                "language": detected_lang,
                "transcript": "",
                "error": err_msg,
                "response": err_msg,
                "response_text": err_msg,
                "message": err_msg,
                "audio_status": audio_status,
                "audio_url": f"/api/voice/audio/{audio_file}" if audio_file else None,
                "context": context or {},
            }
    elif text_query and text_query.strip():
        transcript = text_query.strip()
        print(f"[VOICE PIPELINE][{req_id}] Received text query: \"{transcript}\"")
    elif image_bytes or image_path:
        transcript = ""
    elif ui_context and any(ui_context.get(k) for k in ["proactive_help", "file_uploaded", "is_stuck", "is_idle", "has_error", "error_type"]):
        transcript = ""
    else:
        detected_lang = language or "hi"
        intro_text = get_saathi_introduction(detected_lang)
        audio_file, audio_status = synthesize_speech_with_status(intro_text, detected_lang)
        print(f"[VOICE PIPELINE][{req_id}] Returning introductory greeting for {detected_lang}")
        return {
            "success": True,
            "request_id": req_id,
            "language": detected_lang,
            "transcript": "",
            "response": intro_text,
            "response_text": intro_text,
            "message": intro_text,
            "audio_status": audio_status,
            "audio_url": f"/api/voice/audio/{audio_file}" if audio_file else None,
            "context": context or {},
        }

    # 2. Automatic Multilingual Language Detection
    detected_language = detect_language(transcript, current_lang=language) if transcript else (language or "hinglish")
    print(f"[VOICE PIPELINE][{req_id}] Incoming message: \"{transcript}\"")
    print(f"[VOICE PIPELINE][{req_id}] Detected language: {detected_language}")
    print(f"[VOICE PIPELINE][{req_id}] Existing context: {context}")
    print(f"[VOICE PIPELINE][{req_id}] Loaded conversation history: {history}")

    # Extract crop & stage context
    from app.services.voice_service import resolve_context_from_history
    extracted_crop, extracted_stage, _ = resolve_context_from_history(
        current_text=transcript,
        history=history,
        explicit_crop=None,
        explicit_stage=None
    )

    # 3. Layer & Intent Classification
    layer, guidance_intent = classify_saathi_query_layer(
        text=transcript,
        guidance_context=guidance_context,
        current_page=current_page
    )

    from app.services.agriculture_intent import classify_intent
    agri_meta = classify_intent(transcript, detected_language, history=history, session_context=context, farm_info=farm_context) if transcript else {}
    classified_intent = agri_meta.get("intent") or agri_meta.get("topic") or layer
    resolved_context = agri_meta.get("context") or context or {}
    pending_field = resolved_context.get("pending_field")
    extracted_location = agri_meta.get("location") or resolved_context.get("location")

    target_crop = extracted_crop or agri_meta.get("detected_crop") or resolved_context.get("crop") or "wheat"

    # 4. Handle Image Disease Diagnosis if Image is Provided
    has_image = bool((image_bytes and len(image_bytes) > 0) or (image_path and Path(image_path).exists()))
    prediction_payload = None
    weather_info = None
    response_text = ""
    nav_action = None
    final_handler = "generate_saathi_speech_response"

    if has_image:
        print(f"[VOICE PIPELINE][{req_id}] Processing image input for disease diagnosis on {target_crop}...")
        img_success, pred_res, img_resp_text, dis_data, img_err = analyze_crop_image_for_saathi(
            image_bytes=image_bytes,
            image_path=image_path,
            image_filename=image_filename,
            image_content_type=image_content_type,
            plant=target_crop,
            farm_info=farm_context or context,
            lang_key=detected_language
        )
        if not img_success and img_err and "Unsupported file type" in img_err:
            response_text = img_resp_text
            classified_intent = "crop_disease"
            final_handler = "analyze_crop_image_for_saathi[validation_error]"
        elif img_success:
            classified_intent = "crop_disease"
            prediction_payload = pred_res
            response_text = img_resp_text
            resolved_context["detected_disease"] = pred_res.get("label")
            resolved_context["disease_confidence"] = pred_res.get("confidence")
            resolved_context["disease_details"] = dis_data
            resolved_context["crop"] = target_crop
            resolved_context["current_intent"] = "crop_disease"
            resolved_context["pending_field"] = None
            final_handler = "ai_service.analyze_crop"
        else:
            response_text = img_resp_text
            classified_intent = "crop_disease"
            final_handler = f"analyze_crop_image_for_saathi[error: {img_err}]"

    elif layer == "GUIDANCE_HELP" and guidance_context:
        final_handler = "generate_guidance_help_response"
        response_text, nav_action = generate_guidance_help_response(
            question=transcript,
            guidance_data=guidance_context,
            language=detected_language,
            history=history
        )
    elif layer != "PLATFORM_HELP" and ((agri_meta.get("is_agriculture_related") is False) or agri_meta.get("topic") == "non_agriculture"):
        from app.services.agriculture_intent import get_rejection_message
        response_text = get_rejection_message(detected_language)
        classified_intent = "fallback"
        final_handler = "get_rejection_message"
    else:
        final_handler = f"get_response_for_intent[{classified_intent}]"
        gen_res = await generate_saathi_speech_response(
            question=transcript,
            language=detected_language,
            history=history,
            farmer_name=farmer_name,
            current_page=current_page,
            screen_name=screen_name,
            available_buttons=available_buttons,
            focused_button=focused_button,
            ui_context=ui_context,
            context=resolved_context
        )
        if isinstance(gen_res, tuple):
            if len(gen_res) == 3:
                response_text, nav_action, weather_info = gen_res
            else:
                response_text, nav_action = gen_res[0], gen_res[1]
        else:
            response_text, nav_action = str(gen_res), None

    print(f"[VOICE PIPELINE][{req_id}] Pending field: {resolved_context.get('pending_field')}")
    print(f"[VOICE PIPELINE][{req_id}] Extracted location: {extracted_location}")
    print(f"[VOICE PIPELINE][{req_id}] Updated context: {resolved_context}")
    print(f"[VOICE PIPELINE][{req_id}] Selected intent: {classified_intent} (Layer: {layer}, Topic: {agri_meta.get('topic')})")

    weather_api_called = bool(weather_info and weather_info.get("available") is not None)
    print(f"[VOICE PIPELINE][{req_id}] Weather API called or not: {weather_api_called}")
    print(f"[VOICE PIPELINE][{req_id}] Weather API result: {weather_info}")
    print(f"[VOICE PIPELINE][{req_id}] Final handler used: {final_handler}")
    print(f"[VOICE PIPELINE][{req_id}] Final response: \"{response_text}\"")

    # 5. Spoken Audio Synthesis (TTS)
    audio_file, audio_status = synthesize_speech_with_status(response_text, detected_language)

    resolved_guidance = resolve_active_guidance_context(guidance_context) if guidance_context else None

    weather_payload = weather_info if weather_info else {
        "available": False,
        "rain_expected": False,
        "summary": "Weather information not requested"
    }

    return {
        "success": True,
        "request_id": req_id,
        "layer": layer,
        "intent": classified_intent,
        "crop": resolved_context.get("crop") or target_crop,
        "detected_crop": resolved_context.get("crop") or target_crop,
        "crop_age_days": resolved_context.get("crop_age_days"),
        "growth_stage": resolved_context.get("growth_stage"),
        "pending_field": resolved_context.get("pending_field"),
        "location": resolved_context.get("location"),
        "prediction": prediction_payload,
        "language": detected_language,
        "language_name": SUPPORTED_LANGUAGES.get(detected_language, "English"),
        "transcript": transcript,
        "topic": agri_meta.get("topic") or ("crop_disease" if classified_intent == "crop_disease" else "saathi_companion"),
        "is_agriculture_related": True if classified_intent == "crop_disease" else agri_meta.get("is_agriculture_related", False),
        "response": response_text,
        "response_text": response_text,
        "message": response_text,
        "navigation_action": nav_action,
        "guidance_context": resolved_guidance,
        "context": resolved_context,
        "weather": weather_payload,
        "audio_status": audio_status,
        "audio_url": f"/api/voice/audio/{audio_file}" if audio_file else None,
    }
