"""
AgriBridge Master Farmer Voice Helpline & Advisory Service

Features:
1. Multi-turn conversation context retention (remembers active crop, location, and topic).
2. Auto-language detection & dynamic language switching across 14 languages + Hinglish.
3. Intelligent tool integration (Live Weather Forecasts, Mandi Market Rates, ICAR Disease DB, App Navigation).
4. App Help & Navigation Triggers (guides farmers on how to use AgriBridge and opens pages).
5. Safe, ICAR-aligned, human-like voice responses (20-60s spoken max, no raw code/markdown).
"""

import os
import re
import json
import httpx
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from app.services.agriculture_intent import (
    classify_intent,
    get_rejection_message,
    detect_language_switch,
    extract_crop_entity,
    detect_navigation_intent,
    SUPPORTED_LANGUAGES,
)
from app.services.speech_to_text import transcribe_audio
from app.services.text_to_speech import synthesize_speech, synthesize_speech_with_status
from app.services.weather_service import get_current_weather, get_forecast
from app.services.timing_advice_service import calculate_timing_advice
from app.data.india_districts import find_district

BACKEND_DIR = Path(__file__).resolve().parents[2]
AI_HANDOFF_DIR = BACKEND_DIR / "AI_Engine" / "AgriBridge_AI_Backend_Handoff"
RECOMMENDATION_DB_PATH = AI_HANDOFF_DIR / "recommendation_database.json"

_cached_rec_db = None

def _load_recommendation_database() -> Dict[str, Any]:
    global _cached_rec_db
    if _cached_rec_db is not None:
        return _cached_rec_db
    try:
        if RECOMMENDATION_DB_PATH.exists():
            with open(RECOMMENDATION_DB_PATH, "r", encoding="utf-8") as f:
                _cached_rec_db = json.load(f)
        else:
            _cached_rec_db = {}
    except Exception:
        _cached_rec_db = {}
    return _cached_rec_db


def get_gemini_api_key() -> str:
    return os.getenv("GEMINI_API_KEY", "").strip()


# ============================================================
# INDICATIVE MANDI & MSP MARKET DATA (INDIA CONTEXT)
# ============================================================

MANDI_PRICE_DATABASE = {
    "Wheat": {"msp": "₹2,275 / quintal", "mandi_range": "₹2,300 - ₹2,450 / quintal", "trend": "Steady / Favorable"},
    "Rice": {"msp": "₹2,183 / quintal (Common), ₹2,203 (Grade A)", "mandi_range": "₹2,250 - ₹2,600 / quintal", "trend": "Strong demand"},
    "Tomato": {"msp": "Market determined", "mandi_range": "₹15 - ₹35 / kg (₹1,500 - ₹3,500 / qtl)", "trend": "Volatile / Seasonal"},
    "Potato": {"msp": "Market determined", "mandi_range": "₹12 - ₹22 / kg (₹1,200 - ₹2,200 / qtl)", "trend": "Stable"},
    "Cotton": {"msp": "₹6,620 / quintal (Medium), ₹7,020 (Long)", "mandi_range": "₹6,800 - ₹7,300 / quintal", "trend": "Active buying"},
    "Soybean": {"msp": "₹4,600 / quintal", "mandi_range": "₹4,400 - ₹4,800 / quintal", "trend": "Steady"},
    "Corn": {"msp": "₹2,090 / quintal", "mandi_range": "₹2,100 - ₹2,350 / quintal", "trend": "Moderate"},
    "Mustard": {"msp": "₹5,650 / quintal", "mandi_range": "₹5,400 - ₹5,800 / quintal", "trend": "High demand"},
    "Gram": {"msp": "₹5,440 / quintal", "mandi_range": "₹5,500 - ₹6,000 / quintal", "trend": "Firm"},
    "Onion": {"msp": "Market determined", "mandi_range": "₹18 - ₹30 / kg", "trend": "Seasonal fluctuation"},
    "Chilli": {"msp": "Market determined", "mandi_range": "₹140 - ₹210 / kg (Dry)", "trend": "High value"},
    "Sugarcane": {"msp": "₹315 / quintal (FRP)", "mandi_range": "₹315 - ₹340 / quintal", "trend": "Mill regulated"}
}


# ============================================================
# MULTI-TURN CONTEXT RESOLUTION
# ============================================================

def resolve_context_from_history(
    current_text: str,
    history: Optional[List[Dict[str, str]]] = None,
    explicit_crop: Optional[str] = None,
    explicit_stage: Optional[str] = None
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extract active crop, stage, and previous topic by scanning current text
    and previous conversation turns.
    """
    detected_crop = extract_crop_entity(current_text) or explicit_crop or None
    active_stage = explicit_stage or None
    last_topic = None

    if history and isinstance(history, list):
        for turn in reversed(history):
            msg = turn.get("text") or turn.get("message") or turn.get("content") or ""
            if not detected_crop:
                crop_in_hist = extract_crop_entity(msg)
                if crop_in_hist:
                    detected_crop = crop_in_hist

            # Check if stage was mentioned
            if not active_stage:
                lower = msg.lower()
                for st in ["seedling", "vegetative", "flowering", "fruiting", "maturity"]:
                    if st in lower:
                        active_stage = st.capitalize()

    return detected_crop, active_stage, last_topic


# ============================================================
# APP HELP & PLATFORM TOUR LOCALIZED GENERATOR
# ============================================================

def generate_app_help_response(language: str) -> str:
    lang = (language or "hi").strip().lower().split("-")[0]
    responses = {
        "hi": "एग्रीब्रिज में आपका स्वागत है! इस ऐप में आप: 1. मौसम और 15-दिन का पूर्वानुमान देख सकते हैं, 2. अपनी फसल की फोटो खींचकर बीमारी की जांच कर सकते हैं, 3. मंडी भाव और अपनी फसल बेचने की लिस्टिंग बना सकते हैं, और 4. खेती से जुड़े हर सवाल का जवाब पा सकते हैं। आप बस बोलकर कहें, जैसे 'मौसम दिखाओ' या 'क्रॉप डॉक्टर खोलो'!",
        "en": "Welcome to AgriBridge! In this app, you can: 1. Check live weather and 15-day forecasts, 2. Scan crop photos for instant disease diagnosis, 3. Check mandi prices and list crops for verified buyers, and 4. Ask me any farming advice by voice. Just say 'Show weather' or 'Open crop doctor'!",
        "hinglish": "AgriBridge mein welcome! Is app mein aap: 1. Live Weather aur 15-day forecast dekh sakte hain, 2. Crop photo scan karke bimari check kar sakte hain, 3. Mandi bhav dekh kar apni fasal bech sakte hain, aur 4. Mujhse bolkar koi bhi kheti ki advice le sakte hain. Aap bas boliye 'Mausam dikhao' ya 'Crop doctor kholo'!",
        "pa": "ਐਗਰੀਬ੍ਰਿਜ ਵਿੱਚ ਤੁਹਾਡਾ ਸਵਾਗਤ ਹੈ! ਇਸ ਐਪ ਵਿੱਚ ਤੁਸੀਂ: 1. ਮੌਸਮ ਅਤੇ 15-ਦਿਨਾਂ ਦਾ ਅਨੁਮਾਨ ਦੇਖ ਸਕਦੇ ਹੋ, 2. ਫ਼ਸਲ ਦੀ ਫੋਟੋ ਸਕੈਨ ਕਰਕੇ ਬਿਮਾਰੀ ਦਾ ਪਤਾ ਲਗਾ ਸਕਦੇ ਹੋ, 3. ਮੰਡੀ ਦੇ ਭਾਅ ਦੇਖ ਸਕਦੇ ਹੋ, ਅਤੇ 4. ਮੇਰੇ ਨਾਲ ਬੋਲ ਕੇ ਖੇਤੀ ਸਲਾਹ ਲੈ ਸਕਦੇ ਹੋ।",
        "mr": "अ‍ॅग्रीब्रिजमध्ये आपले स्वागत आहे! या अ‍ॅपमध्ये आपण: 1. हवामान आणि 15 दिवसांचा अंदाज पाहू शकता, 2. पिकाचा फोटो काढून रोग तपासू शकता, 3. बाजारभाव आणि पिके विकू शकता, आणि 4. बोलून शेतीचा सल्ला घेऊ शकता. फक्त 'हवामान दाखवा' किंवा 'क्रॉप डॉक्टर उघडा' म्हणा!",
        "bn": "এগ্রিব্রিজে স্বাগতম! এই অ্যাপে আপনি: ১. আবহাওয়ার পূর্বাভাস দেখতে পারেন, ২. ফসলের ছবি স্ক্যান করে রোগ নির্ণয় করতে পারেন, ৩. বাজার দর দেখতে পারেন এবং ৪. মুখে বলে যে কোনো কৃষি পরামর্শ নিতে পারেন।",
        "gu": "એગ્રીબ્રિજમાં આપનું સ્વાગત છે! આ એપમાં તમે: 1. હવામાનની આગાહી જોઈ શકો છો, 2. પાકના ફોટાથી રોગની તપાસ કરી શકો છો, 3. બજાર ભાવ જોઈ શકો છો અને 4. બોલીને ખેતીની સલાહ લઈ શકો છો.",
        "ta": "அக்ரிபிரிட்ஜிற்கு வரவேற்கிறோம்! இந்த செயலியில்: 1. நேரலை வானிலை பார்க்கலாம், 2. பயிர் படம் மூலம் நோய் கண்டறியலாம், 3. சந்தை விலைகளை அறியலாம், 4. குரல் மூலம் விவசாய ஆலோசனை பெறலாம்.",
        "te": "అగ్రిబ్రిడ్జ్‌కు స్వాగతం! ఈ యాప్‌లో: 1. వాతావరణ సమాచారం తెలుసుకోవచ్చు, 2. పంట ఫోటోతో తెగులు నిర్ధారణ చేయవచ్చు, 3. మార్కెట్ ధరలు చూడవచ్చు, 4. మాట్లాడి వ్యవసాయ సలహాలు పొందవచ్చు.",
        "kn": "ಅಗ್ರಿಬ್ರಿಡ್ಜ್‌ಗೆ ಸುಸ್ವಾಗತ! ಈ ಆ್ಯಪ್‌ನಲ್ಲಿ: 1. ಹವಾಮಾನ ಮುನ್ಸೂಚನೆ ತಿಳಿಯಬಹುದು, 2. ಬೆಳೆ ಫೋಟೋ ಸ್ಕ್ಯಾನ್ ಮಾಡಿ ರೋಗ ಪತ್ತೆಹಚ್ಚಬಹುದು, 3. ಮಾರುಕಟ್ಟೆ ದರಗಳನ್ನು ನೋಡಬಹುದು, 4. ಧ್ವನಿಯ ಮೂಲಕ ಕೃಷಿ ಸಲಹೆ ಪಡೆಯಬಹುದು.",
        "ml": "അഗ്രിബ്രിഡ്ജിലേക്ക് സ്വാഗതം! ഈ ആപ്പിൽ: 1. കാലാവസ്ഥാ വിവരങ്ങൾ അറിയാം, 2. വിളയുടെ ഫോട്ടോ വഴി രോഗനിർണയം നടത്താം, 3. വിപണി വിലകൾ കാണാം, 4. ശബ്ദത്തിലൂടെ കാർഷിക ഉപദേശം നേടാം.",
        "or": "ଏଗ୍ରିବ୍ରିଜକୁ ସ୍ୱାଗତ! ଏହି ଆପ୍‌ରେ ଆପଣ: ୧. ପାଣିପାଗ ପୂର୍ବାନୁମାନ, ୨. ଫସଲ ଫଟୋରୁ ରୋଗ ଚିହ୍ନଟ, ୩. ମଣ୍ଡି ଦର ଏବଂ ୪. ମୋ ସହିତ କଥା ହୋଇ ଚାଷ ପରାମର୍ଶ ପାଇପାରିବେ।",
        "as": "এগ্ৰিব্ৰিজলৈ স্বাগতম! এই এপটোত আপুনি: ১. বতৰৰ আগজাননী, ২. শস্যৰ ফটোৰে ৰোগ পৰীক্ষা, ৩. বজাৰ দৰ চাব পাৰে আৰু ৪. মুখেৰে কৈ যিকোনো কৃষি পৰামৰ্শ লব পাৰে।",
        "ur": "ایگری برج میں خوش آمدید! اس ایپ میں آپ: 1. لائیو موسم دیکھ سکتے ہیں، 2. فصل کی تصویر سے بیماری چیک کر سکتے ہیں، 3. منڈی کے ریٹ دیکھ سکتے ہیں اور 4. بول کر زرعی مشورہ لے سکتے ہیں۔"
    }
    return responses.get(lang, responses["hi"])


# ============================================================
# MANDI & MARKET LOCALIZED GENERATOR
# ============================================================

def generate_market_response(crop: Optional[str], language: str) -> str:
    lang = (language or "hi").strip().lower().split("-")[0]
    crop_name = crop or "Wheat"
    data = MANDI_PRICE_DATABASE.get(crop_name, MANDI_PRICE_DATABASE["Wheat"])
    msp = data["msp"]
    mandi = data["mandi_range"]

    responses = {
        "hi": f"{crop_name} का वर्तमान अनुमानित मंडी भाव {mandi} चल रहा है (सरकारी एमएसपी: {msp})। आप हमारे 'मार्केटप्लेस' पेज पर जाकर सीधे सत्यापित खरीदारों के साथ सौदा कर सकते हैं।",
        "en": f"Current estimated mandi rate for {crop_name} is {mandi} (Govt MSP: {msp}). You can visit the Marketplace page to connect with verified buyers.",
        "hinglish": f"{crop_name} ka current mandi bhav lagbhag {mandi} chal raha hai (Govt MSP: {msp}). Aap Marketplace section mein verified buyers ke sath direct commit kar sakte hain.",
        "pa": f"{crop_name} ਦਾ ਮੌਜੂਦਾ ਮੰਡੀ ਭਾਅ {mandi} ਹੈ (ਸਰਕਾਰੀ ਐਮਐਸਪੀ: {msp})। ਤੁਸੀਂ ਸਾਡੇ ਮਾਰਕੀਟਪਲੇਸ ਪੇਜ 'ਤੇ ਖ਼ਰੀਦਦਾਰਾਂ ਨਾਲ ਸੰਪਰਕ ਕਰ ਸਕਦੇ ਹੋ।",
        "mr": f"{crop_name} चा सध्याचा बाजारभाव {mandi} सुरू आहे (शासकीय हमीभाव: {msp}). आपण मार्केटप्लेस पेजवर जाऊन थेट खरेदीदारांशी व्यवहार करू शकता.",
        "bn": f"{crop_name}-এর বর্তমান বাজার দর {mandi} (সরকারি এমএসপি: {msp})। আপনি আমাদের মার্কেটপ্লেস পেজে যাচাইকৃত ক্রেতাদের সাথে যোগাযোগ করতে পারেন।",
        "gu": f"{crop_name}નો હાલનો બજાર ભાવ {mandi} ચાલી રહ્યો છે (સરકારી ટેકાનો ભાવ: {msp}). તમે માર્કેટપ્લેસ પેજ પર જઈને ખરીદદારો સાથે જોડાઈ શકો છો.",
        "ta": f"{crop_name} பயிரின் தற்போதைய சந்தை விலை {mandi} (அரசு குறைந்தபட்ச ஆதரவு விலை: {msp}). நீங்கள் சந்தை பக்கத்திற்கு சென்று வாங்குபவர்களை அணுகலாம்.",
        "te": f"{crop_name} ప్రస్తుత మార్కెట్ ధర {mandi} గా ఉంది (ప్రభుత్వ మద్దతు ధర: {msp}). మీరు మార్కెట్‌ప్లేస్ పేజీలో ధృవీకరించబడిన కొనుగోలుదారులతో కనెక్ట్ అవ్వవచ్చు.",
        "kn": f"{crop_name} ಬೆಳೆಯ ಪ್ರಸ್ತುತ ಮಾರುಕಟ್ಟೆ ದರ {mandi} ಇದೆ (ಸರ್ಕಾರಿ ಬೆಂಬಲ ಬೆಲೆ: {msp}). ನೀವು ಮಾರ್ಕೆಟ್‌ಪ್ಲೇಸ್‌ನಲ್ಲಿ ನೇರವಾಗಿ ಖರೀದಿದಾರರನ್ನು ಸಂಪರ್ಕಿಸಬಹುದು.",
        "ml": f"{crop_name} വിളയുടെ നിലവിലെ വിപണി വില {mandi} ആണ് (സർക്കാർ താങ്ങുവില: {msp}). കൂടുതൽ വിവരങ്ങൾക്ക് മാർക്കറ്റ്‌പ്ലേസ് സന്ദർശിക്കുക.",
        "or": f"{crop_name}ର ବର୍ତ୍ତମାନର ମଣ୍ଡି ଦର {mandi} ରହିଛି (ସରକାରୀ ଏମଏସପି: {msp})। ଆପଣ ମାର୍କେଟପ୍ଲେସ ପେଜରେ ଯାଞ୍ଚ ହୋଇଥିବା କ୍ରେତାଙ୍କ ସହ ଯୋଗାଯୋଗ କରିପାରିବେ।",
        "as": f"{crop_name}ৰ বৰ্তমান বজাৰ দৰ {mandi} (চৰকাৰী এমএছপি: {msp})। আপুনি মার্কেটপ্লেচত গ্ৰাহকৰ লগত যোগাযোগ কৰিব পাৰে।",
        "ur": f"{crop_name} کا موجودہ منڈی ریٹ {mandi} ہے (سرکاری ایم ایس پی: {msp})۔ آپ مارکیٹ پلیس پر خریداروں سے رابطہ کر سکتے ہیں۔"
    }
    return responses.get(lang, responses["hi"])


# ============================================================
# WEATHER ADVISORY LOCALIZED GENERATOR
# ============================================================

def generate_weather_voice_response(
    weather_data: Dict[str, Any],
    timing_data: Optional[Dict[str, Any]],
    crop: Optional[str],
    language: str,
    location: Optional[str] = None
) -> str:
    lang = (language or "hi").strip().lower().split("-")[0]
    crop_name = crop or "फसल"
    temp = weather_data.get("temperature", "--")
    cond = weather_data.get("weather_condition", "सामान्य")
    loc_str = location or ("आपके क्षेत्र" if lang in ["hi", "mr"] else ("aapke area" if lang == "hinglish" else "your area"))

    if timing_data and timing_data.get("rain_risk"):
        prob = timing_data.get("rain_probability", 70)
        when = timing_data.get("when", "अगले 24-48 घंटों में")
        dry = timing_data.get("short_dry_day", "2-3 दिन बाद")
        
        if lang == "en":
            return f"Current temperature is {temp}°C with {cond} in {loc_str}. Warning: {prob}% chance of rain expected {when}. Delay spraying and irrigation for your {crop_name} until {dry} when dry weather returns."
        elif lang == "hinglish":
            return f"{loc_str} mein current temperature {temp}°C aur mausam {cond} hai. Dhyan dijiye: {when} {prob}% baarish ka anuman hai. Apni {crop_name} fasal par sinchai ya spray {dry} tak postpone karein."
        elif lang == "pa":
            return f"{loc_str} ਵਿੱਚ ਇਸ ਵੇਲੇ ਤਾਪਮਾਨ {temp}°C ਹੈ। ਚਿਤਾਵਨੀ: {when} {prob}% ਮੀਂਹ ਦੀ ਸੰਭਾਵਨਾ ਹੈ। ਆਪਣੀ {crop_name} 'ਤੇ ਸਿੰਚਾਈ {dry} ਤੱਕ ਰੋਕੋ।"
        elif lang == "mr":
            return f"{loc_str} मध्ये सध्या तापमान {temp}°C आहे. सावधानता: {when} {prob}% पावसाचा अंदाज आहे. आपल्या {crop_name} पिकावर पाणी देणे {dry} पर्यंत पुढे ढकला."
        else: # Default Hindi
            return f"मौसम पूर्वानुमान के अनुसार {loc_str} में वर्तमान तापमान {temp}°C और मौसम {cond} है। ध्यान दें: {when} {prob}% बारिश की संभावना है। अपनी {crop_name} की फसल पर सिंचाई या दवा का छिड़काव {dry} तक टालें।"
    else:
        if lang == "en":
            return f"According to the weather forecast for {loc_str}, the current temperature is {temp}°C with {cond}. No significant rain is expected in the next 48 hours. Favorable conditions for standard field operations on your {crop_name}."
        elif lang == "hinglish":
            return f"Mausam ke anusaar {loc_str} mein temperature {temp}°C aur mausam {cond} hai. Agle 48 ghante baarish ka anuman nahi hai. Aapki {crop_name} ke liye mausam anukool hai."
        elif lang == "pa":
            return f"{loc_str} ਵਿੱਚ ਮੌਜੂਦਾ ਤਾਪਮਾਨ {temp}°C ਹੈ ਅਤੇ ਮੀਂਹ ਦਾ ਕੋਈ ਖ਼ਤਰਾ ਨਹੀਂ ਹੈ। ਤੁਹਾਡੀ {crop_name} ਲਈ ਮੌਸਮ ਅਨੁਕੂਲ ਹੈ।"
        elif lang == "mr":
            return f"{loc_str} मध्ये सध्या तापमान {temp}°C असून पुढील 48 तासांत पावसाची शक्यता नाही. {crop_name} पिकासाठी हवामान अनुकूल आहे."
        else: # Default Hindi
            return f"मौसम पूर्वानुमान के अनुसार {loc_str} में वर्तमान तापमान {temp}°C और मौसम {cond} है। अगले 48 घंटों में बारिश की संभावना नहीं है। आपकी {crop_name} की फसल के लिए मौसम अनुकूल है।"


# ============================================================
# COMPREHENSIVE LOCALIZED KNOWLEDGE TEMPLATES (14 LANGUAGES)
# ============================================================

LOCALIZED_KNOWLEDGE = {
    "irrigation": {
        "en": "Check topsoil moisture before watering your {crop}. In drip systems, maintain 2-3 hours morning cycles. If heavy rain is forecast in 48 hours, pause irrigation to prevent waterlogging and root rot.",
        "hi": "अपनी {crop} की फसल में मिट्टी की नमी देखकर ही पानी दें। ड्रिप सिंचाई में सुबह के समय 2-3 घंटे चलाएं। यदि अगले 48 घंटे में बारिश का अनुमान हो तो पानी देना टालें ताकि जड़ें सुरक्षित रहें।",
        "hinglish": "Apni {crop} mein soil moisture check karke hi pani dein. Morning time mein light irrigation karein. Agar 48 hours mein rain expected hai, toh waterlogging se bachne ke liye irrigation delay karein.",
        "pa": "ਆਪਣੀ {crop} ਦੀ ਫ਼ਸਲ ਲਈ ਜ਼ਮੀਨ ਵਿੱਚ ਨਮੀ ਵੇਖ ਕੇ ਹਲਕੀ ਸਿੰਚਾਈ ਕਰੋ। ਸਵੇਰ ਵੇਲੇ ਪਾਣੀ ਦੇਣਾ ਵਧੀਆ ਹੈ। ਜੇਕਰ ਮੀਂਹ ਦੀ ਸੰਭਾਵਨਾ ਹੋਵੇ ਤਾਂ ਸਿੰਚਾਈ ਰੋਕੋ।",
        "mr": "आपल्या {crop} पिकासाठी जमिनीतील ओलावा तपासून हलके पाणी द्या. ठिबक सिंचन सकाळी चालवणे उत्तम. पुढील 48 तासांत पाऊस असल्यास पाणी देणे टाळा.",
        "bn": "আপনার {crop} ফসলে মাটির আর্দ্রতা বুঝে হালকা সেচ দিন। সকালে জলসেচ করা সবচেয়ে ভালো। বৃষ্টির সম্ভাবনা থাকলে সেচ বন্ধ রাখুন।",
        "gu": "તમારા {crop} પાકમાં જમીનનો ભેજ ચકાસીને હળવું પિયત આપો. સવારના સમયે પિયત આપવું ઉત્તમ રહેશે. વરસાદની આગાહી હોય તો પિયત ટાળો.",
        "ta": "உங்கள் {crop} பயிருக்கு மண்ணின் ஈரப்பதத்தை அறிந்து மிதமான பாசனம் செய்யவும். மழை பெய்ய வாய்ப்பிருந்தால் பாசனத்தை தள்ளிப்போடுங்கள்.",
        "te": "మీ {crop} పంటకు నేలలో తేమను బట్టి తేలికపాటి సాగునీరు అందించండి. వర్షం సూచన ఉంటే నీరు పెట్టడం వాయిదా వేయండి.",
        "kn": "ನಿಮ್ಮ {crop} ಬೆಳೆಗೆ ಮಣ್ಣಿನ ತೇವಾಂಶವನ್ನು ನೋಡಿ ಹಗುರವಾದ ನೀರಾವರಿ ಒದಗಿಸಿ. ಮಳೆಯ ಮುನ್ಸೂಚನೆ ಇದ್ದರೆ ನೀರು ಕೊಡುವುದನ್ನು ಮುಂದೂಡಿ.",
        "ml": "നിങ്ങളുടെ {crop} വിളയ്ക്ക് മണ്ണിന്റെ ഈർപ്പം അനുസരിച്ച് നേരിയ നന നൽകുക. മഴയ്ക്ക് സാധ്യതയുണ്ടെങ്കിൽ നന മാറ്റിവയ്ക്കുക.",
        "or": "ଆପଣଙ୍କ {crop} ଫସଲ ପାଇଁ ମାଟିର ଆର୍ଦ୍ରତା ଦେଖି ହାଲୁକା ଜଳସେଚନ କରନ୍ତୁ। ବର୍ଷା ସମ୍ଭାବନା ଥିଲେ ପାଣି ଦେବା ବନ୍ଦ ରଖନ୍ତୁ।",
        "as": "আপোনাৰ {crop} শস্যত মাটিৰ আৰ্দ্ৰতা চাই পাতলীয়া পানী দিয়ক। বৰষুণৰ সম্ভাৱনা থাকিলে পানী দিয়া বন্ধ ৰাখক।",
        "ur": "اپنی {crop} کی فصل میں مٹی کی نمی دیکھ کر ہلکا پانی دیں۔ اگر بارش کا امکان ہو تو آبپاشی ملتوی رکھیں۔"
    },
    "fertilizer": {
        "en": "Apply balanced NPK fertilizer based on crop stage for your {crop}. Mix well-rotted cow dung manure or vermicompost. Avoid excessive urea during flowering stage to prevent flower dropping.",
        "hi": "{crop} की फसल में संतुलित NPK और गोबर की सड़ी खाद या वर्मीकम्पोस्ट का प्रयोग करें। फूल आने के समय अतिरिक्त यूरिया न डालें ताकि फूल झड़ने से बच सकें।",
        "hinglish": "{crop} ki crop ke liye balanced NPK aur organic compost use karein. Flowering stage par extra nitrogen/urea se bachein taaki flowers drop na hon.",
        "pa": "{crop} ਦੀ ਫ਼ਸਲ ਲਈ ਸੰਤੁਲਿਤ NPK ਅਤੇ ਰੂੜੀ ਖਾਦ ਦੀ ਵਰਤੋਂ ਕਰੋ। ਫੁੱਲ ਪੈਣ ਸਮੇਂ ਵਧੇਰੇ ਯੂਰੀਆ ਪਾਉਣ ਤੋਂ ਬਚੋ।",
        "mr": "{crop} पिकासाठी संतुलित NPK आणि शेणखत वापरा. फुले येण्याच्या काळात अतिरिक्त युरिया वापरणे टाळा.",
        "bn": "{crop} ফসলে সুষম NPK এবং জৈব সার ব্যবহার করুন। ফুল আসার সময় অতিরিক্ত ইউরিয়া প্রয়োগ এড়িয়ে চলুন।",
        "gu": "{crop} પાક માટે સંતુલિત NPK અને દેશી ખાતરનો ઉપયોગ કરો. ફૂલ આવવાના સમયે વધુ પડતો યુરિયા ન નાખવો.",
        "ta": "{crop} பயிருக்கு சமச்சீர் NPK மற்றும் இயற்கை உரங்களை இடவும். பூக்கும் தருணத்தில் அதிகப்படியான யூரியாவை தவிர்க்கவும்.",
        "te": "{crop} పంటకు సమతుల్య NPK మరియు సేంద్రీయ ఎరువులను వాడండి. పూత దశలో అధిక యూరియా వాడకాన్ని నివారించండి.",
        "kn": "{crop} ಬೆಳೆಗೆ ಸಮತೋಲಿತ NPK ಮತ್ತು ಸಾವಯವ ಗೊಬ್ಬರವನ್ನು ಬಳಸಿ. ಹೂ ಬಿಡುವ ಹಂತದಲ್ಲಿ ಹೆಚ್ಚಿನ ಯೂರಿಯಾವನ್ನು ತಪ್ಪಿಸಿ.",
        "ml": "{crop} വിളയ്ക്ക് സന്തുലിതമായ NPK വളങ്ങളും ജൈവവളങ്ങളും നൽകുക. പൂവിടുന്ന ഘട്ടത്തിൽ അമിതമായ യൂറിയ ഒഴിവാക്കുക.",
        "or": "{crop} ଫସଲ ପାଇଁ ସନ୍ତୁଳିତ NPK ଏବଂ ଜୈବିକ ଖତ ବ୍ୟବହାର କରନ୍ତୁ। ଫୁଲ ଆସିବା ସମୟରେ ଅତ୍ୟଧିକ ୟୁରିଆ ପ୍ରୟୋଗ କରନ୍ତୁ ନାହିଁ।",
        "as": "{crop} শস্যৰ বাবে সুষম NPK আৰু জৈৱিক সাৰ ব্যৱহাৰ কৰক। ফুল অহাৰ সময়ত অধিক ইউৰিয়া নিদিব।",
        "ur": "{crop} کی فصل کے لیے متوازن NPK اور نامیاتی کھاد استعمال کریں۔ پھول آنے کے وقت زیادہ یوریا سے پرہیز کریں۔"
    },
    "crop_disease": {
        "en": "For disease symptoms like spots or yellowing on your {crop}, first isolate severely affected leaves. Spray bio-fungicides like Trichoderma or neem formulation early in the morning. You can scan leaf photos on our Crop Doctor page for an instant AI check!",
        "hi": "{crop} में पत्तियों पर पीलेपन या धब्बों के लक्षण दिखने पर प्रभावित पत्तियों को हटाएं। सुबह के समय नीम तेल या ट्राइकोडर्मा का छिड़काव करें। सटीक जांच के लिए आप ऐप के 'क्रॉप डॉक्टर' पेज पर पत्ते की फोटो भी स्कैन कर सकते हैं!",
        "hinglish": "{crop} mein leaves par yellowing ya spots dikhein toh affected leaves remove karein. Early morning neem oil spray karein. Accurate check ke liye hamare 'Crop Doctor' page par leaf ki photo scan karein!",
        "pa": "{crop} ਵਿੱਚ ਪੱਤਿਆਂ 'ਤੇ ਬਿਮਾਰੀ ਜਾਂ ਪੀਲਾਪਣ ਦਿਸਣ 'ਤੇ ਨਿੰਮ ਦੇ ਤੇਲ ਦਾ ਛਿੜਕਾਅ ਕਰੋ। ਸਹੀ ਜਾਂਚ ਲਈ ਸਾਡੇ 'ਕ੍ਰੌਪ ਡਾਕਟਰ' ਪੇਜ 'ਤੇ ਫੋਟੋ ਸਕੈਨ ਕਰੋ।",
        "mr": "{crop} पिकावर रोगाची लक्षणे किंवा पिवळे डाग दिसल्यास कडुनिंब तेलाची फवारणी करा. अचूक तपासणीसाठी आमच्या 'क्रॉप डॉक्टर' पेजवर फोटो स्कॅन करा.",
        "bn": "{crop} ফসলে পাতার দাগ বা হলুদ ভাব দেখা দিলে নিম তেলের স্প্রে করুন। সঠিক রোগ নির্ণয়ের জন্য আমাদের 'ক্রপ ডাক্তার' পেজে ছবি স্ক্যান করুন।",
        "gu": "{crop} પાકમાં પાંદડા પર ડાઘ કે પીળાશ જણાય તો લીમડાના તેલનો છંટકાવ કરો. સચોટ તપાસ માટે અમારા 'ક્રોપ ડોક્ટર' પેજ પર ફોટો સ્કેન કરો.",
        "ta": "{crop} பயிரில் இலை புள்ளிகள் அல்லது மஞ்சள் நிறம் தென்பட்டால் வேப்பெண்ணெய் தெளிக்கவும். துல்லியமான பரிசோதனைக்கு எங்கள் 'பயிர் மருத்துவர்' பக்கத்தில் புகைப்படம் ஸ்கேன் செய்யவும்.",
        "te": "{crop} పంటలో తెగులు లేదా పసుపు మచ్చలు కనిపిస్తే వేపనూనె పిచికారీ చేయండి. ఖచ్చితమైన వివరాల కోసం 'క్రాప్ డాక్టర్' పేజీలో ఫోటో స్కాన్ చేయండి.",
        "kn": "{crop} ಬೆಳೆಯಲ್ಲಿ ಎಲೆ ಚುಕ್ಕೆ ಅಥವಾ ಹಳದಿ ಬಣ್ಣ ಕಂಡುಬಂದರೆ ಬೇವಿನ ಎಣ್ಣೆ ಸಿಂಪಡಿಸಿ. ನಿಖರ ಪರಿಶೀಲನೆಗಾಗಿ ನಮ್ಮ 'ಕ್ರಾಪ್ ಡಾಕ್ಟರ್' ಪುಟದಲ್ಲಿ ಫೋಟೋ ಸ್ಕ್ಯಾನ್ ಮಾಡಿ.",
        "ml": "{crop} വിളകളിൽ ഇലപ്പുള്ളിയോ മഞ്ഞളിപ്പോ കണ്ടാൽ വേപ്പെണ്ണ തളിക്കുക. കൃത്യമായ പരിശോധനയ്ക്ക് ഞങ്ങളുടെ 'ക്രോപ്പ് ഡോക്ടർ' പേജിൽ ഫോട്ടോ സ്കാൻ ചെയ്യുക.",
        "or": "{crop} ଫସଲରେ ପତ୍ର ହଳଦିଆ କିମ୍ବା ଦାଗ ଦେଖାଗଲେ ନିମ ତେଲ ସ୍ପ୍ରେ କରନ୍ତୁ। ସଠିକ୍ ପରୀକ୍ଷା ପାଇଁ 'କ୍ରପ୍ ଡାକ୍ତର' ପେଜ୍‌ରେ ଫଟୋ ସ୍କାନ୍ କରନ୍ତୁ।",
        "as": "{crop} শস্যত পাতৰ দাগ বা হালধীয়া ৰং দেখা পালে নিম তেল প্ৰয়োগ কৰক। সঠিক পৰীক্ষাৰ বাবে 'ক্ৰপ ডাক্তৰ'ত ফটো স্কেন কৰক।",
        "ur": "{crop} کی فصل میں پتوں پر دھبے یا پیلا پن نظر آئے تو نیم کے تیل کا اسپرے کریں۔ درست تشخیص کے لیے 'کراپ ڈاکٹر' پر تصویر اسکین کریں۔"
    },
    "pest": {
        "en": "To protect your {crop} from insect pests like aphids or caterpillars, install yellow sticky traps and spray 5ml/L neem oil solution during evening hours. For severe infestation, consult official CIBRC label directions.",
        "hi": "{crop} को कीटों जैसे माहू या सुंडी से बचाने के लिए खेत में पीले चिपचिपे ट्रैप लगाएं और शाम को 5 मिली/लीटर नीम तेल का छिड़काव करें। अधिक प्रकोप होने पर नजदीकी कृषि केंद्र से सलाह लें।",
        "hinglish": "{crop} ko pests aur insects se bachane ke liye yellow sticky traps lagayein aur evening time neem oil spray karein. Severe attack par official label guidelines follow karein.",
        "pa": "{crop} ਨੂੰ ਕੀੜਿਆਂ ਤੋਂ ਬਚਾਉਣ ਲਈ ਪੀਲੇ ਟਰੈਪ ਲਗਾਓ ਅਤੇ ਸ਼ਾਮ ਵੇਲੇ ਨਿੰਮ ਦੇ ਤੇਲ ਦਾ ਛਿੜਕਾਅ ਕਰੋ।",
        "mr": "{crop} पिकाचे किडींपासून संरक्षण करण्यासाठी शेतात पिवळे चिकट ट्रॅप लावा आणि संध्याकाळी कडुनिंब तेलाची फवारणी करा.",
        "bn": "{crop} ফসলে পোকামাকড়ের উপদ্রব কমাতে হলুদ ফাঁদ ব্যবহার করুন এবং সন্ধ্যায় নিম তেল স্প্রে করুন।",
        "gu": "{crop} પાકને જીવાતથી બચાવવા માટે પીળા સ્ટીકી ટ્રેપ લગાવો અને સાંજે લીમડાના તેલનો છંટકાવ કરો.",
        "ta": "{crop} பயிரை பூச்சிகளிடமிருந்து பாதுகாக்க மஞ்சள் நிற பொறிகளை வைத்து, மாலையில் வேப்பெண்ணெய் தெளிக்கவும்.",
        "te": "{crop} పంటను కీటకాల నుండి రక్షించడానికి పసుపు జిగురు ట్రాప్‌లను ఏర్పాటు చేసి, సాయంత్రం వేపనూనె పిచికారీ చేయండి.",
        "kn": "{crop} ಬೆಳೆಯನ್ನು ಕೀಟಗಳಿಂದ ರಕ್ಷಿಸಲು ಹಳದಿ ಬಲೆಗಳನ್ನು ಹಾಕಿ ಸಂಜೆ ಬೇವಿನ ಎಣ್ಣೆ ಸಿಂಪಡಿಸಿ.",
        "ml": "{crop} വിളകളിൽ കീടബാധ തടയാൻ മഞ്ഞക്കെണികൾ സ്ഥാപിക്കുകയും വൈകുന്നേരം വേപ്പെണ്ണ തളിക്കുകയും ചെയ്യുക.",
        "or": "{crop} ଫସଲକୁ ପୋକରୁ ରକ୍ଷା କରିବା ପାଇଁ ହଳଦିଆ ଟ୍ରାପ୍ ଲଗାନ୍ତୁ ଏବଂ ସନ୍ଧ୍ୟାରେ ନିମ ତେଲ ସ୍ପ୍ରେ କରନ୍ତୁ।",
        "as": "{crop} শস্যক পোক-পতংগৰ পৰা ৰক্ষা কৰিবলৈ হালধীয়া ফান্দ ব্যৱহাৰ কৰক আৰু নিম তেল ছটিয়াব।",
        "ur": "{crop} کو کیڑوں سے بچانے کے لیے پیلے ٹریپس لگائیں اور شام کے وقت نیم کے تیل کا اسپرے کریں۔"
    },
    "soil": {
        "en": "Maintain healthy soil for your {crop} with organic matter and balanced pH between 6.5 and 7.5. Conduct a soil test every 2 years to apply exact micronutrients like Zinc and Boron.",
        "hi": "{crop} के लिए मिट्टी की जांच करवाएं और पीएच मान 6.5 से 7.5 के बीच रखें। जैविक खाद डालकर मिट्टी की उर्वरा शक्ति बढ़ाएं और आवश्यकतानुसार जिंक व बोरॉन का प्रयोग करें।",
        "hinglish": "{crop} ke liye soil testing zaroor karwayein aur balanced pH maintain karein. Organic manure daal kar soil fertility improve karein.",
        "pa": "{crop} ਲਈ ਮਿੱਟੀ ਦੀ ਪਰਖ ਕਰਵਾਓ ਅਤੇ ਰੂੜੀ ਖਾਦ ਪਾ ਕੇ ਜ਼ਮੀਨ ਦੀ ਉਪਜਾਊ ਸ਼ਕਤੀ ਵਧਾਓ।",
        "mr": "{crop} पिकासाठी माती परीक्षण करून सेंद्रिय खतांचा वापर करा आणि जमिनीची सुपीकता टिकवून ठेवा.",
        "bn": "{crop} ফসলের জন্য মাটি পরীক্ষা করান এবং জৈব সার ব্যবহার করে মাটির উর্বরতা বৃদ্ধি করুন।",
        "gu": "{crop} પાક માટે જમીન ચકાસણી કરાવો અને દેશી ખાતર નાખીને જમીનની ફળદ્રુપતા વધારો.",
        "ta": "{crop} பயிருக்கு மண் பரிசோதனை செய்து இயற்கை எரு இட்டு மண்ணின் வளத்தை அதிகரிக்கவும்.",
        "te": "{crop} పంటకు నేల పరీక్ష చేయించి సేంద్రీయ ఎరువులతో భూసారాన్ని పెంచండి.",
        "kn": "{crop} ಬೆಳೆಗೆ ಮಣ್ಣು ಪರೀಕ್ಷೆ ಮಾಡಿಸಿ ಸಾವಯವ ಗೊಬ್ಬರ ಬಳಸಿ ಮಣ್ಣಿನ ಫಲವತ್ತತೆ ಹೆಚ್ಚಿಸಿ.",
        "ml": "{crop} വിളയ്ക്ക് മണ്ണ് പരിശോധന നടത്തുകയും ജൈവവളം ചേർത്ത് മണ്ണിന്റെ ഫലഭൂയിഷ്ഠത കൂട്ടുകയും ചെയ്യുക.",
        "or": "{crop} ପାଇଁ ମାଟି ପରୀକ୍ଷା କରାନ୍ତୁ ଏବଂ ଜୈବିକ ଖତ ପ୍ରୟୋଗ କରି ମାଟିର ଉର୍ବରତା ବୃଦ୍ଧି କରନ୍ତୁ।",
        "as": "{crop}ৰ বাবে মাটি পৰীক্ষা কৰাওক আৰু জৈৱিক সাৰ ব্যৱহাৰ কৰি মাটিৰ উৰ্বৰতা বৃদ্ধি কৰক।",
        "ur": "{crop} کی فصل کے لیے مٹی کی جانچ کروائیں اور نامیاتی کھاد ڈال کر مٹی کی زرخیزی بڑھائیں۔"
    },
    "government_scheme": {
        "en": "Key farmer schemes include PM-KISAN (₹6,000 annual income support), Pradhan Mantri Fasal Bima Yojana (crop insurance against weather loss), and Kisan Credit Card (subsidized 4% interest loans). Visit your local CSC or agriculture office to apply.",
        "hi": "प्रमुख किसान योजनाओं में पीएम-किसान (₹6,000 वार्षिक सहायता), फसल बीमा योजना (मौसम से नुकसान पर सुरक्षा) और किसान क्रेडिट कार्ड (4% सस्ती दर पर ऋण) शामिल हैं। नजदीकी सीएससी या कृषि कार्यालय से आवेदन करें।",
        "hinglish": "Major government schemes hain: PM-KISAN (₹6,000 annual support), PM Fasal Bima Yojana (crop insurance) aur Kisan Credit Card (low interest loan). Apply karne ke liye local CSC centre visit karein.",
        "pa": "ਮੁੱਖ ਕਿਸਾਨ ਯੋਜਨਾਵਾਂ ਵਿੱਚ ਪੀਐਮ-ਕਿਸਾਨ (₹6,000 ਸਾਲਾਨਾ ਸਹਾਇਤਾ), ਫ਼ਸਲ ਬੀਮਾ ਯੋਜਨਾ ਅਤੇ ਕਿਸਾਨ ਕ੍ਰੈਡਿਟ ਕਾਰਡ ਸ਼ਾਮਲ ਹਨ।",
        "mr": "प्रमुख सरकारी योजनांमध्ये पीएम-किसान (₹6,000 वार्षिक मदत), पीक विमा योजना आणि किसान क्रेडिट कार्ड (4% सवलतीचे कर्ज) यांचा समावेश आहे.",
        "bn": "প্রধান সরকারি প্রকল্পগুলির মধ্যে রয়েছে পিএম-কিষাণ (বার্ষিক ₹৬,০০০ সহায়তা), ফসল বিমা যোজনা এবং কিষাণ ক্রেডিট কার্ড।",
        "gu": "મુખ્ય ખેડૂત યોજનાઓમાં પીએમ-કિસાન (વાર્ષિક ₹6,000 સહાય), પાક વીમા યોજના અને કિસાન ક્રેડિટ કાર્ડ સામેલ છે.",
        "ta": "முக்கிய திட்டங்கள்: பிஎம்-கிசான் (ஆண்டுக்கு ₹6,000 உதவி), பயிர் காப்பீட்டு திட்டம் மற்றும் கிசான் கிரெடிட் கார்டு.",
        "te": "ప్రధాన పథకాలు: పీఎం-కిసాన్ (ఏటా ₹6,000 సహాయం), పంట బీమా యోజన మరియు కిసాన్ క్రెడిట్ కార్డ్.",
        "kn": "ಪ್ರಮುಖ ಯೋಜನೆಗಳು: ಪಿಎಂ-ಕಿಸಾನ್ (ವಾರ್ಷಿಕ ₹6,000 ನೆರವು), ಬೆಳೆ ವಿಮೆ ಯೋಜನೆ ಮತ್ತು ಕಿಸಾನ್ ಕ್ರೆಡಿಟ್ ಕಾರ್ಡ್.",
        "ml": "പ്രധാന പദ്ധതികൾ: പിഎം-കിസാൻ (പ്രതിവർഷം ₹6,000 സഹായം), വിള ഇൻഷുറൻസ് പദ്ധതി, കിസാൻ ക്രെഡിറ്റ് കാർഡ്.",
        "or": "ପ୍ରମୁଖ ଯୋଜନା: ପିଏମ୍-କିଷାନ୍ (ବାର୍ଷିକ ₹୬,୦୦୦ ସହାୟତା), ଫସଲ ବୀମା ଯୋଜନା ଏବଂ କିଷାନ୍ କ୍ରେଡିଟ୍ କାର୍ଡ।",
        "as": "মুখ্য আঁচনিসমূহ: পিএম-কিষাণ (বছৰি ₹৬,০০০ সাহায্য), শস্য বীমা আৰু কিষাণ ক্ৰেডিট কাৰ্ড।",
        "ur": "اہم سرکاری اسکیموں میں پی ایم کسان (سالانہ 6,000 روپے)، فصل بیمہ یوجنا اور کسان کریڈٹ کارڈ شامل ہیں۔"
    },
    "crop_cultivation": {
        "en": "For optimal yield in your {crop} crop, ensure certified disease-free seeds and proper plant-to-plant spacing. Monitor crop growth stages closely and scout for pests weekly.",
        "hi": "{crop} की अधिक पैदावार के लिए प्रमाणित बीजों का चयन करें और कतार से कतार की उचित दूरी रखें। फसल की बढ़वार की नियमित निगरानी करें।",
        "hinglish": "{crop} ki acchi yield ke liye certified seeds use karein aur proper spacing maintain karein. Growth stages par weekly field inspect karein.",
        "pa": "{crop} ਦੀ ਵਧੀਆ ਪੈਦਾਵਾਰ ਲਈ ਪ੍ਰਮਾਣਿਤ ਬੀਜ ਵਰਤੋ ਅਤੇ ਨਿਯਮਿਤ ਦੇਖਭਾਲ ਕਰੋ।",
        "mr": "{crop} पिकाच्या चांगल्या उत्पादनासाठी प्रमाणित बियाणे वापरा आणि योग्य अंतर ठेवा.",
        "bn": "{crop} ফসলের ভালো ফলনের জন্য উন্নত জাতের বীজ ব্যবহার করুন এবং নিয়মিত পরিচর্যা করুন।",
        "gu": "{crop} પાકના સારા ઉત્પાદન માટે પ્રમાણિત બીજ વાપરો અને યોગ્ય અંતર રાખો.",
        "ta": "{crop} பயிரில் அதிக மகசூல் பெற சான்றளிக்கப்பட்ட விதைகளைப் பயன்படுத்தி சரியான இடைவெளியில் நடவும்.",
        "te": "{crop} పంటలో అధిక దిగుబడి కోసం ధృవీకరించబడిన విత్తనాలను వాడండి మరియు సరైన యాజమాన్య పద్ధతులు పాటించండి.",
        "kn": "{crop} ಬೆಳೆಯಲ್ಲಿ ಉತ್ತಮ ಇಳುವರಿಗಾಗಿ ಪ್ರಮಾಣೀಕೃತ ಬೀಜಗಳನ್ನು ಬಳಸಿ ಮತ್ತು ನಿಯಮಿತವಾಗಿ ಕೃಷಿ ಕಾರ್ಯಗಳನ್ನು ಮಾಡಿ.",
        "ml": "{crop} വിളവിൽ നിന്ന് മികച്ച വിളവ് ലഭിക്കാൻ ഗുണമേന്മയുള്ള വിത്തുകൾ ഉപയോഗിക്കുക.",
        "or": "{crop} ଫସଲର ଉତ୍ତମ ଅମଳ ପାଇଁ ଉନ୍ନତ ମଞ୍ଜି ବ୍ୟବହାର କରନ୍ତୁ ଏବଂ ନିୟମିତ ଯତ୍ନ ନିଅନ୍ତୁ।",
        "as": "{crop} শস্যৰ ভাল উৎপাদনৰ বাবে প্ৰমাণিত বীজ ব্যৱহাৰ কৰক আৰু নিয়মীয়া পৰিচৰ্যা কৰক।",
        "ur": "{crop} کی بہتر پیداوار کے لیے تصدیق شدہ بیج استعمال کریں اور پودوں کے درمیان مناسب فاصلہ رکھیں۔"
    },
    "farm_management": {
        "en": "For field preparation, perform 2-3 deep ploughings, clear weeds, and mix 4-5 tonnes of well-rotted cow dung manure per acre. Ensure proper field leveling and soil testing before sowing.",
        "hi": "खेत की तैयारी के लिए मिट्टी की 2-3 बार गहरी जुताई करें, खरपतवार साफ करें और प्रति एकड़ 4-5 टन सड़ी गोबर की खाद मिलाएं। बुवाई से पहले खेत को समतल कर लें।",
        "hinglish": "Khet ki taiyari ke liye 2-3 baar deep ploughing (jutai) karein, weeds saaf karein aur 4-5 ton organic gobar ki khaad mix karein. Sowing se pehle land ko level kar lein.",
        "pa": "ਖੇਤ ਦੀ ਤਿਆਰੀ ਲਈ ਜ਼ਮੀਨ ਦੀ 2-3 ਵਾਰ ਡੂੰਘੀ ਵਾਹੀ ਕਰੋ, ਨਦੀਨ ਸਾਫ਼ ਕਰੋ ਅਤੇ ਰੂੜੀ ਖਾਦ ਪਾਓ।",
        "mr": "शेताच्या मशागतीसाठी जमिनीची 2-3 वेळा खोल नांगरणी करा, तण काढून टाका आणि शेणखत मिसळा.",
        "bn": "জমি তৈরির জন্য ২-৩ বার গভীর চাষ দিন, আগাছা পরিষ্কার করুন এবং জৈব সার মেশান।",
        "gu": "ખેત તૈયારી માટે જમીનને 2-3 વખત ઊંડી ખેડ કરો, નીંદણ સાફ કરો અને દેશી ખાતર ઉમેરો.",
        "ta": "நிலத்தை தயார் செய்ய 2-3 முறை ஆழமாக உழுது, களைகளை அகற்றி இயற்கை எரு இடவும்.",
        "te": "పొలం తయారీ కోసం 2-3 సార్లు లోతుగా దుక్కి దున్ని, కలుపు తొలగించి సేంద్రీయ ఎరువు వేయండి.",
        "kn": "ಜಮೀನು ಸಿದ್ಧತೆಗಾಗಿ 2-3 ಬಾರಿ ಆಳವಾಗಿ ಉಳುಮೆ ಮಾಡಿ, ಕಳೆ ತೆಗೆದು ಸಾವಯವ ಗೊಬ್ಬರ ಹಾಕಿ.",
        "ml": "നിലമൊരുക്കലിനായി 2-3 തവണ ആഴത്തിൽ ഉഴുതുമറിച്ച് കളകൾ നീക്കം ചെയ്ത് ജൈവവളം ചേർക്കുക.",
        "or": "ଜମି ପ୍ରସ୍ତୁତି ପାଇଁ ୨-୩ ଥର ଗଭୀର ଚାଷ କରନ୍ତୁ, ଘାସ ସଫା କରନ୍ତୁ ଏବଂ ଜୈବିକ ଖତ ମିଶାନ୍ତୁ।",
        "as": "মাটি প্ৰস্তুতৰ বাবে ২-৩ বাৰ ভালদৰে হাল বাওক, বন-বাত পৰিষ্কাৰ কৰক আৰু সাৰ প্ৰয়োগ কৰক।",
        "ur": "کھیت کی تیاری کے لیے 2-3 بار گہری جوتائی کریں، جڑی بوٹیاں صاف کریں اور گوبر کی کھاد ملائیں۔"
    },
    "action_plan": {
        "en": "A customized step-by-step action plan for your {crop} from sowing to harvest is ready. You can track daily tasks, irrigation, and fertilizer schedules on the Crop Monitoring and Command Center pages.",
        "hi": "आपकी {crop} के लिए बुवाई से लेकर कटाई तक का चरणबद्ध एक्शन प्लान तैयार है। आप हमारे 'क्रॉप मॉनिटरिंग' और 'कमांड सेंटर' में दैनिक कार्य, सिंचाई और खाद का शेड्यूल देख सकते हैं।",
        "hinglish": "Aapki {crop} ke liye complete step-by-step action plan ready hai. Sowing se harvest tak daily tasks, irrigation aur fertilizer schedule dekhne ke liye 'Crop Monitoring' section check karein.",
        "pa": "ਤੁਹਾਡੀ {crop} ਲਈ ਬਿਜਾਈ ਤੋਂ ਲੈ ਕੇ ਵਾਢੀ ਤੱਕ ਦਾ ਐਕਸ਼ਨ ਪਲਾਨ ਤਿਆਰ ਹੈ। ਤੁਸੀਂ 'ਕ੍ਰੌਪ ਮਾਨੀਟਰਿੰਗ' ਵਿੱਚ ਰੋਜ਼ਾਨਾ ਕੰਮ ਦੇਖ ਸਕਦੇ ਹੋ।",
        "mr": "आपल्या {crop} पिकासाठी पेरणीपासून काढणीपर्यंतचे नियोजन तयार आहे. आपण 'क्रॉप मॉनिटरिंग' मध्ये दैनंदिन कामांचे वेळापत्रक पाहू शकता.",
        "bn": "আপনার {crop} ফসলের জন্য বপন থেকে কাটা পর্যন্ত কর্মপরিকল্পনা প্রস্তুত। 'ক্রপ মনিটরিং' পাতায় দৈনিক কাজের তালিকা দেখুন।",
        "gu": "તમારા {crop} પાક માટે વાવણીથી લણણી સુધીનો એક્શન પ્લાન તૈયાર છે. તમે 'ક્રોપ મોનિટરિંગ' માં દૈનિક કાર્યો જોઈ શકો છો.",
        "ta": "உங்கள் {crop} பயிருக்கான விதைப்பு முதல் அறுவடை வரையிலான செயல் திட்டம் தயாராக உள்ளது. 'பயிர் கண்காணிப்பு' பக்கத்தில் தினசரி பணிகளை பார்க்கலாம்.",
        "te": "మీ {crop} పంట కోసం విత్తనం నుండి కోత వరకు సమగ్ర కార్యాచరణ ప్రణాళిక సిద్ధంగా ఉంది. 'పంట పర్యవేక్షణ' లో రోజువారీ పనులు చూడవచ్చు.",
        "kn": "ನಿಮ್ಮ {crop} ಬೆಳೆಗೆ ಬಿತ್ತನೆಯಿಂದ ಕೊಯ್ಲಿನವರೆಗೆ ಹಂತ-ಹಂತದ ಕ್ರಿಯಾ ಯೋಜನೆ ಸಿದ್ಧವಾಗಿದೆ. 'ಕ್ರಾಪ್ ಮಾನಿಟರಿಂಗ್' ಪುಟದಲ್ಲಿ ದೈನಂದಿನ ಕಾರ್ಯಗಳನ್ನು ವೀಕ್ಷಿಸಿ.",
        "ml": "നിങ്ങളുടെ {crop} വിളയ്ക്കായി വിതയ്ക്കൽ മുതൽ വിളവെടുപ്പ് വരെയുള്ള ആക്ഷൻ പ്ലാൻ തയ്യാറാണ്. 'ക്രോപ്പ് മോണിറ്ററിംഗ്' പേജിൽ ദിനചര്യകൾ കാണാം.",
        "or": "ଆପଣଙ୍କ {crop} ଫସଲ ପାଇଁ ବିହନ ବୁଣିବା ଠାରୁ ଅମଳ ପର୍ଯ୍ୟନ୍ତ କାର୍ଯ୍ୟ ଯୋଜନା ପ୍ରସ୍ତୁତ। 'କ୍ରପ୍ ମନିଟରିଂ'ରେ ଦୈନିକ କାର୍ଯ୍ୟସୂଚୀ ଦେଖନ୍ତୁ।",
        "as": "আপোনাৰ {crop} শস্যৰ বাবে সম্পূৰ্ণ কৰ্মপৰিকল্পনা সাজু হৈছে। 'ক্ৰপ মনিটৰিং' পেজত দৈনিক কামৰ সময়সূচী চাওক।",
        "ur": "آپ کی {crop} کے لیے بوائی سے کٹائی تک کا مکمل ایکشن پلان تیار ہے۔ آپ 'کراپ مانیٹرنگ' میں روزانہ کا شیڈول دیکھ سکتے ہیں۔"
    },
    "weather": {
        "en": "Weather conditions are currently favorable with no immediate severe rain risk over the next 48 hours. Check the Weather page for live 15-day forecasts and safe spraying windows.",
        "hi": "वर्तमान में मौसम सामान्य और अनुकूल है। अगले 48 घंटों में भारी बारिश का कोई गंभीर खतरा नहीं है। 15-दिन का सटीक पूर्वानुमान और स्प्रे विंडो देखने के लिए 'मौसम' पेज देखें।",
        "hinglish": "Current mausam favorable hai aur agle 48 hours mein heavy rain ka koi risk nahi hai. Live 15-day forecast aur spray timing ke liye 'Weather' section check karein.",
        "pa": "ਮੌਸਮ ਅਨੁਕੂਲ ਹੈ ਅਤੇ ਅਗਲੇ 48 ਘੰਟਿਆਂ ਵਿੱਚ ਭਾਰੀ ਮੀਂਹ ਦਾ ਕੋਈ ਖ਼ਤਰਾ ਨਹੀਂ ਹੈ। 15 ਦਿਨਾਂ ਦੇ ਅਨੁਮਾਨ ਲਈ 'ਮੌਸਮ' ਪੇਜ ਦੇਖੋ।",
        "mr": "सध्या हवामान अनुकूल असून पुढील 48 तासांत मुसळधार पावसाचा धोका नाही. 15 दिवसांच्या अंदाजासाठी 'हवामान' पेज तपासा.",
        "bn": "আবহাওয়া বর্তমানে অনুকূল এবং আগামী ৪৮ ঘণ্টায় ভারী বৃষ্টির সম্ভাবনা নেই। ১৫ দিনের পূর্বাভাসের জন্য 'আবহাওয়া' পেজ দেখুন।",
        "gu": "હાલ હવામાન અનુકૂળ છે અને આગામી 48 કલાકમાં ભારે વરસાદનો કોઈ ખતરો નથી. 15 દિવસની આગાહી માટે 'હવામાન' પેજ જુઓ.",
        "ta": "தற்போது வானிலை சாதகமாக உள்ளது, அடுத்த 48 மணி நேரத்தில் கனமழைக்கு வாய்ப்பில்லை. 15 நாள் முன்னறிவிப்புக்கு 'வானிலை' பக்கத்தை பார்க்கவும்.",
        "te": "ప్రస్తుతం వాతావరణం అనుకూలంగా ఉంది, రాబోయే 48 గంటల్లో భారీ వర్ష సూచన లేదు. 15 రోజుల సమాచారం కోసం 'వాతావరణం' పేజీని చూడండి.",
        "kn": "ಪ್ರಸ್ತುತ ಹವಾಮಾನವು ಅನುಕೂಲಕರವಾಗಿದೆ, ಮುಂದಿನ 48 ಗಂಟೆಗಳಲ್ಲಿ ಭಾರಿ ಮಳೆಯ ಅಪಾಯವಿಲ್ಲ. 15 ದಿನಗಳ ಮುನ್ಸೂಚನೆಗಾಗಿ 'ಹವಾಮಾನ' ಪುಟವನ್ನು ನೋಡಿ.",
        "ml": "നിലവിൽ കാലാവസ്ഥ അനുകൂലമാണ്, അടുത്ത 48 മണിക്കൂറിൽ കനത്ത മഴയ്ക്ക് സാധ്യതയില്ല. കൂടുതൽ വിവരങ്ങൾക്ക് 'കാലാവസ്ഥ' പേജ് കാണുക.",
        "or": "ବର୍ତ୍ତମାନ ପାଣିପାଗ ଅନୁକୂଳ ଅଛି ଏବଂ ଆଗାମୀ ୪୮ ଘଣ୍ଟାରେ ପ୍ରବଳ ବର୍ଷାର ଆଶଙ୍କା ନାହିଁ। ୧୫ ଦିନର ପୂର୍ବାନୁମାନ ପାଇଁ 'ପାଣିପାଗ' ପେଜ୍ ଦେଖନ୍ତୁ।",
        "as": "বতৰ বৰ্তমান অনুকূল আৰু অহা ৪৮ ঘণ্টাত ডাঙৰ বৰষুণৰ আশংকা নাই। ১৫ দিনৰ আগজাননীৰ বাবে 'বতৰ' পেজ চাওক।",
        "ur": "فی الحال موسم سازگار ہے اور اگلے 48 گھنٹوں میں تیز بارش کا کوئی خطرہ نہیں ہے۔ 15 دن کی پیشگوئی کے لیے 'موسم' پیج دیکھیں۔"
    },
    "greeting": {
        "en": "Hello farmer! I am your AgriBridge agricultural advisor. How can I help you with your crops, weather, fertilizer, or soil today?",
        "hi": "नमस्ते किसान भाई! मैं आपका एग्रीब्रिज कृषि सलाहकार हूँ। आज आपकी फसल, मौसम, खाद या खेती से जुड़े सवालों में मैं कैसे मदद करूँ?",
        "hinglish": "Namaste farmer ji! Main aapka AgriBridge agriculture helpline advisor hoon. Aaj aapki crop, weather, fertilizer ya irrigation mein kaise help karun?",
        "pa": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ ਕਿਸਾਨ ਵੀਰੋ! ਮੈਂ ਤੁਹਾਡਾ ਐਗਰੀਬ੍ਰਿਜ ਖੇਤੀ ਸਲਾਹਕਾਰ ਹਾਂ। ਅੱਜ ਫ਼ਸਲ ਜਾਂ ਮੌਸਮ ਬਾਰੇ ਕੀ ਮਦਦ ਚਾਹੀਦੀ ਹੈ?",
        "mr": "नमस्कार शेतकरी बंधूंनो! मी आपला अ‍ॅग्रीब्रिज कृषी सल्लागार आहे. आज आपल्या पिकाबद्दल किंवा शेतीबद्दल मी कशी मदत करू शकतो?",
        "bn": "নমস্কার কৃষক ভাই! আমি আপনার এগ্রিব্রিজ কৃষি উপদেষ্টা। আজ ফসল বা কৃষিকাজে আমি কীভাবে সাহায্য করতে পারি?",
        "gu": "નમસ્તે ખેડૂત મિત્ર! હું તમારો એગ્રીબ્રિજ કૃષિ સલાહકાર છું. આજે તમારી ખેતી કે પાક બાબતે હું કેવી રીતે મદદ કરી શકું?",
        "ta": "வணக்கம் விவசாயி அவர்களே! நான் உங்கள் அக்ரிபிரிட்ஜ் வேளாண் ஆலோசகர். இன்று உங்கள் பயிர் அல்லது விவசாயம் பற்றி என்ன உதவி வேண்டும்?",
        "te": "నమస్కారం రైతు సోదరులారా! నేను మీ అగ్రిబ్రిడ్జ్ వ్యవసాయ సలహాదారుని. ఈరోజు మీ పంట లేదా వ్యవసాయంలో నేను ఎలా సహాయపడగలను?",
        "kn": "ನಮಸ್ಕಾರ ರೈತ ಬಾಂಧವರೇ! ನಾನು ನಿಮ್ಮ ಅಗ್ರಿಬ್ರಿಡ್ಜ್ ಕೃಷಿ ಸಲಹೆಗಾರ. ಇಂದು ನಿಮ್ಮ ಬೆಳೆ ಅಥವಾ ಕೃಷಿಯ ಬಗ್ಗೆ ನಾನು ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?",
        "ml": "നമസ്കാരം കർഷക സുഹൃത്തേ! ഞാൻ നിങ്ങളുടെ അഗ്രിബ്രിഡ്ജ് കാർഷിക ഉപദേശകനാണ്. ഇന്ന് കൃഷിയെക്കുറിച്ച് എന്ത് സഹಾಯമാണ് വേണ്ടത്?",
        "or": "ନମସ୍କାର ଚାଷୀ ଭାଇ! ମୁଁ ଆପଣଙ୍କ ଏଗ୍ରିବ୍ରିଜ୍ କୃଷି ପରାମର୍ଶଦାତା। ଆଜି ଆପଣଙ୍କ ଫସଲ କିମ୍ବା ଚାଷ ସମ୍ବନ୍ଧୀୟ କି ସାହାଯ୍ୟ କରିପାରିବି?",
        "as": "নমস্কাৰ কৃষক ভাই! মই আপোনাৰ এগ্ৰিব্ৰিজ কৃষি উপদেষ্টা। আজি শস্য বা কৃষি সম্পৰ্কে কি সহায় লাগে?",
        "ur": "سلام کسان بھائی! میں آپ کا ایگری برج زرعی مشیر ہوں۔ آج اپنی فصل، موسم یا کھاد کے بارے میں پوچھیے۔"
    }
}


# ============================================================
# KISAN SAATHI NATURAL FOLLOW-UP QUESTION TEMPLATES
# ============================================================

FOLLOW_UP_QUESTIONS = {
    "irrigation": {
        "en": "Which crop are you growing?",
        "hi": "आप कौन सी फसल उगा रहे हैं?",
        "hinglish": "Aap kaun si fasal uga rahe hain?",
        "pa": "ਤੁਸੀਂ ਕਿਹੜੀ ਫ਼ਸਲ ਉਗਾ ਰਹੇ ਹੋ?",
        "mr": "आपण कोणते पीक घेत आहात?",
        "bn": "আপনি কোন ফসল চাষ করছেন?",
        "gu": "તમે કયો પાક ઉગાડી રહ્યા છો?",
        "ta": "நீங்கள் என்ன பயிர் பயிரிடுகிறீர்கள்?",
        "te": "మీరు ఏ పంటను సాగు చేస్తున్నారు?",
        "kn": "ನೀವು ಯಾವ ಬೆಳೆಯನ್ನು ಬೆಳೆಯುತ್ತಿದ್ದೀರಿ?",
        "ml": "നിങ്ങൾ ഏത് വിളയാണ് കൃഷി ചെയ്യുന്നത്?",
        "or": "ଆପଣ କେଉଁ ଫସଲ ଚାଷ କରୁଛନ୍ତି?",
        "as": "আপুনি কি শস্যৰ খেতি কৰিছে?",
        "ur": "آپ کون سی فصل اگا رہے ہیں؟"
    },
    "crop_guidance": {
        "en": "Which crop are you growing?",
        "hi": "आप कौन सी फसल उगा रहे हैं?",
        "hinglish": "Aap kaun si fasal uga rahe hain?",
        "pa": "ਤੁਸੀਂ ਕਿਹੜੀ ਫ਼ਸਲ ਉਗਾ ਰਹੇ ਹੋ?",
        "mr": "आपण कोणते पीक घेत आहात?",
        "bn": "আপনি কোন ফসল চাষ করছেন?",
        "gu": "તમે કયો પાક ઉગાડી રહ્યા છો?",
        "ta": "நீங்கள் என்ன பயிர் பயிரிடுகிறீர்கள்?",
        "te": "మీరు ఏ పంటను సాగు చేస్తున్నారు?",
        "kn": "ನೀವು ಯಾವ ಬೆಳೆಯನ್ನು ಬೆಳೆಯುತ್ತಿದ್ದೀರಿ?",
        "ml": "നിങ്ങൾ ഏത് വിളയാണ് കൃഷി ചെയ്യുന്നത്?",
        "or": "ଆପଣ କେଉଁ ଫସଲ ଚାଷ କରୁଛନ୍ତି?",
        "as": "আপুনি কি শস্যৰ খেতি কৰিছে?",
        "ur": "آپ کون سی فصل اگا رہے ہیں؟"
    },
    "crop_disease": {
        "en": "Which crop is affected?",
        "hi": "कौन सी फसल प्रभावित है?",
        "hinglish": "Kaun si fasal prabhavit hai?",
        "pa": "ਕਿਹੜੀ ਫ਼ਸਲ ਪ੍ਰਭਾਵਿਤ ਹੈ?",
        "mr": "कोणते पीक बाधित झाले आहे?",
        "bn": "কোন ফসলটি ক্ষতিগ্রস্ত হয়েছে?",
        "gu": "કયો પાક પ્રભાવિત થયો છે?",
        "ta": "எந்த பயிர் பாதிக்கப்பட்டுள்ளது?",
        "te": "ఏ పంట తెగులు బారిన పడింది?",
        "kn": "ಯಾವ ಬೆಳೆ ಬಾಧಿತವಾಗಿದೆ?",
        "ml": "ഏത് വിളയ്ക്കാണ് രോഗബാധ?",
        "or": "କେଉଁ ଫସଲ ପ୍ରਭਾਵିତ ହୋଇଛି?",
        "as": "কোনটো শস্য আক্ৰান্ত হৈছে?",
        "ur": "کون سی فصل متاثر ہے؟"
    },
    "action_plan": {
        "en": "Which crop would you like a plan for?",
        "hi": "आप किस फसल के लिए योजना बनाना चाहते हैं?",
        "hinglish": "Aap kis fasal ke liye yojana banana chahte hain?",
        "pa": "ਤੁਸੀਂ ਕਿਹੜੀ ਫ਼ਸਲ ਲਈ ਪਲਾਨ ਬਣਾਉਣਾ ਚਾਹੁੰਦੇ ਹੋ?",
        "mr": "आपण कोणत्या पिकासाठी नियोजन करू इच्छिता?",
        "bn": "আপনি কোন ফসলের জন্য পরিকল্পনা তৈরি করতে চান?",
        "gu": "તમે કયા પાક માટે પ્લાન બનાવવા માંગો છો?",
        "ta": "எந்த பயிருக்கான திட்டத்தை உருவாக்க விரும்புகிறீர்கள்?",
        "te": "మీరు ఏ పంట కోసం ప్రణాళికను రూపొందించాలనుకుంటున్నారు?",
        "kn": "ನೀವು ಯಾವ ಬೆಳೆಗೆ ಯೋಜನೆ ರಚಿಸಲು ಬಯಸುತ್ತೀರಿ?",
        "ml": "ഏത് വിളയ്ക്കാണ് ആക്ഷൻ പ്ലാൻ തയ്യാറാക്കേണ്ടത്?",
        "or": "ଆପଣ କେଉଁ ଫସଲ ପାଇଁ ଯୋଜନା କରିବାକୁ ଚାହାଁନ୍ତି?",
        "as": "আপুনি কি শস্যৰ বাবে পৰিকল্পনা কৰিব বিচাৰে?",
        "ur": "آپ کس فصل کے لیے منصوبہ بنانا چاہتے ہیں؟"
    }
}

AGE_FOLLOW_UP_QUESTIONS = {
    "hi": "{crop} की फसल अभी कितने दिन की है?",
    "hinglish": "{crop} ki fasal abhi kitne din ki hai?",
    "en": "How many days old is your {crop} crop?",
    "pa": "{crop} ਦੀ ਫ਼ਸਲ ਅਜੇ ਕਿੰਨੇ ਦਿਨਾਂ ਦੀ ਹੈ?",
    "mr": "{crop} पीक सध्या किती दिवसांचे आहे?",
    "bn": "{crop} ফসল এখন কত দিনের?",
    "gu": "{crop} પાક અત્યારે કેટલા દિવસનો છે?",
    "ta": "{crop} பயிர் இப்போது எத்தனை நாட்கள் ஆகிறது?",
    "te": "{crop} పంటకు ఇప్పుడు ఎన్ని రోజులు అయింది?",
    "kn": "{crop} ಬೆಳೆ ಈಗ ಎಷ್ಟು ದಿನಗಳದ್ದಾಗಿದೆ?",
    "ml": "{crop} വിളയ്ക്ക് ഇപ്പോൾ എത്ര ദിവസമായി?",
    "or": "{crop} ଫସଲ ଏବେ କେତେ ଦିନର ହୋଇଛି?",
    "as": "{crop} শস্য এতিয়া কিমান দিনৰ হৈছে?",
    "ur": "{crop} کی فصل ابھی کتنے دن کی ہے؟",
}

WHEAT_CRI_IRRIGATION = {
    "hi": "गेहूं की 20-25 दिन की अवस्था (CRI स्टेज) पहली और सबसे महत्वपूर्ण सिंचाई के लिए उपयुक्त है। इस समय खेत में हल्की सिंचाई करें ताकि जड़ों का विकास अच्छा हो सके। यदि अगले 48 घंटे में बारिश का अनुमान हो तो सिंचाई टालें।",
    "hinglish": "Gehu ki 20-25 din ki stage (CRI stage) pehli aur sabse zaroori sinchai ka sahi samay hai. Khet mein halki sinchai karein taaki roots ka vikas accha ho. Agar agle 48 ghante mein baarish ka anuman ho toh paani dena taalein.",
    "en": "For 20-25 days old Wheat (CRI stage), this is the critical time for the first irrigation. Provide light irrigation to support strong root establishment. Delay watering if rain is forecasted in the next 48 hours.",
    "pa": "ਕਣਕ ਦੀ 20-25 ਦਿਨਾਂ ਦੀ ਅਵਸਥਾ (CRI ਸਟੇਜ) ਪਹਿਲੀ ਅਤੇ ਸਭ ਤੋਂ ਜ਼ਰੂਰੀ ਸਿੰਚਾਈ ਦਾ ਸਮਾਂ ਹੈ। ਇਸ ਸਮੇਂ ਹਲਕੀ ਸਿੰਚਾਈ ਕਰੋ ਤਾਂ ਜੋ ਜੜ੍ਹਾਂ ਚੰਗੀ ਤਰ੍ਹਾਂ ਵਿਕਸਿਤ ਹੋਣ। ਜੇਕਰ ਮੀਂਹ ਦੀ ਸੰਭਾਵਨਾ ਹੋਵੇ ਤਾਂ ਪਾਣੀ ਦੇਣਾ ਰੋਕੋ।",
    "mr": "गव्हाच्या २०-२५ दिवसांच्या अवस्थेत (CRI स्टेज) पहिले पाणी देणे अत्यंत महत्त्वाचे आहे. मुळांच्या चांगल्या वाढीसाठी हलके पाणी द्यावे. पुढील ४८ तासांत पावसाचा अंदाज असल्यास सिंचन टाळावे.",
    "bn": "গমের ২০-২৫ দিনের অবস্থায় (CRI স্টেজ) প্রথম এবং সবচেয়ে গুরুত্বপূর্ণ সেচ দেওয়া উচিত। শিকড়ের সঠিক বৃদ্ধির জন্য হালকা সেচ দিন। বৃষ্টির সম্ভাবনা থাকলে সেচ স্থগিত রাখুন।",
    "gu": "ઘઉંના ૨૦-૨૫ દિવસના પાકમાં (CRI સ્ટેજ) પ્રથમ અને મહત્વપૂર્ણ પિયત આપવું જોઈએ. મૂળના સારા વિકાસ માટે હળવું પિયત આપો. વરસાદની આગાહી હોય તો પિયત ટાળો.",
    "ta": "கோதுமை பயிரின் 20-25 நாள் வளர்ச்சி நிலை (CRI நிலை) முதல் பாசனத்திற்கு மிகவும் முக்கியமானது. வேர்கள் நன்றாக வளர மிதமான பாசனம் செய்யவும்.",
    "te": "గోధుమ 20-25 రోజుల దశ (CRI దశ) మొదటి మరియు కీలకమైన సాగునీటికి సరైన సమయం. వేర్లు బలంగా పెరగడానికి తేలికపాటి నీరు పెట్టండి.",
    "kn": "ಗೋಧಿ ಬೆಳೆಯ 20-25 ದಿನಗಳ ಹಂತ (CRI ಹಂತ) ಮೊದಲ ನೀರಾವರಿಗೆ ಅತ್ಯಂತ ಸೂಕ್ತವಾಗಿದೆ. ಬೇರುಗಳ ಬೆಳವಣಿಗೆಗೆ ಹಗುರವಾದ ನೀರು ನೀಡಿ.",
    "ml": "ഗോതമ്പിന്റെ 20-25 ദിവസത്തെ വളർച്ചാ ഘട്ടം ആദ്യ നനയ്ക്ക് അനുയോജ്യമാണ്. വേരുകൾ ബലപ്പെടാൻ നേരിയ നന നൽകുക.",
    "or": "ଗହମର ୨୦-୨୫ ଦିନର ଅବସ୍ଥା (CRI ଷ୍ଟେଜ୍) ପ୍ରଥମ ଜଳସେଚନ ପାଇଁ ଉପଯୁକ୍ତ। ଚେରର ଭଲ ବିକାଶ ପାଇଁ ହାଲୁକା ପାଣି ଦିଅନ୍ତୁ।",
    "as": "ঘেঁহুৰ ২০-২৫ দিনৰ অৱস্থাত প্ৰথম জলসিঞ্চন কৰা উচিত। শিপাৰ বিকাশৰ বাবে পাতলীয়া পানী দিয়ক।",
    "ur": "گندم کی 20-25 دن کی حالت (CRI مرحلہ) پہلی اور اہم ترین آبپاشی کے لیے موزوں ہے۔ ہلکا پانی لگائیں تاکہ جڑوں کی نشوونما اچھی ہو۔"
}

def get_age_irrigation_advice(crop_name: Optional[str], age_days: int, lang_key: str) -> str:
    crop_lower = (crop_name or "wheat").lower()
    crop_disp = CROP_LOCALIZED_NAMES.get(crop_lower, {}).get(lang_key, (crop_name.capitalize() if crop_name else "Wheat"))
    
    if crop_lower in ["wheat", "gehu"] and 15 <= age_days <= 35:
        return WHEAT_CRI_IRRIGATION.get(lang_key, WHEAT_CRI_IRRIGATION["hi"])
        
    templates = {
        "hi": f"{crop_disp} की {age_days} दिन की अवस्था में मिट्टी की ऊपरी परत में नमी देखकर ही हल्की सिंचाई करें। सुबह के समय पानी देना सबसे अच्छा रहता है। यदि बारिश की संभावना हो तो सिंचाई रोकें।",
        "hinglish": f"{crop_disp} ki {age_days} din ki stage par soil moisture check karke hi halki sinchai karein. Morning time mein pani dena behtar hai. Agar baarish ka risk ho toh sinchai delay karein.",
        "en": f"For your {age_days}-day-old {crop_disp}, check topsoil moisture before applying a light irrigation. Morning watering is recommended, and delay if rain is expected in 48 hours.",
        "pa": f"{crop_disp} ਦੀ {age_days} ਦਿਨਾਂ ਦੀ ਫ਼ਸਲ ਲਈ ਜ਼ਮੀਨ ਵਿੱਚ ਨਮੀ ਵੇਖ ਕੇ ਹਲਕੀ ਸਿੰਚਾਈ ਕਰੋ। ਸਵੇਰ ਵੇਲੇ ਪਾਣੀ ਦੇਣਾ ਵਧੀਆ ਹੈ।",
        "mr": f"{crop_disp} पिकाच्या {age_days} दिवसांच्या अवस्थेत मातीतील ओलावा तपासून हलके पाणी द्या. सकाळी पाणी देणे उत्तम.",
        "bn": f"{crop_disp} ফসলের {age_days} দিনের অবস্থায় মাটির আর্দ্রতা দেখে হালকা সেচ দিন।",
        "gu": f"{crop_disp} પાકની {age_days} દિવસની અવસ્થામાં જમીનનો ભેજ જોઈને હળવું પિયત આપો.",
        "ta": f"{crop_disp} பயிரின் {age_days} நாள் வளர்ச்சி நிலையில் மண்ணின் ஈரப்பதம் அறிந்து மிதமான பாசனம் செய்யவும்.",
        "te": f"{crop_disp} పంట {age_days} రోజుల దశలో నేలలో తేమను బట్టి తేలికపాటి సాగునీరు అందించండి.",
        "kn": f"{crop_disp} ಬೆಳೆಯ {age_days} ದಿನಗಳ ಹಂತದಲ್ಲಿ ಮಣ್ಣಿನ ತೇವಾಂಶ ನೋಡಿ ಹಗುರವಾದ ನೀರಾವರಿ ನೀಡಿ.",
        "ml": f"{crop_disp} വിളയുടെ {age_days} ദിവസത്തെ ഘട്ടത്തിൽ മണ്ണിന്റെ ഈർപ്പം നോക്കി നേരിയ നന നൽകുക.",
        "or": f"{crop_disp} ଫସଲର {age_days} ଦିନର ଅବସ୍ଥାରେ ମାଟିର ଆର୍ଦ୍ରତା ଦେଖି ହାଲୁକା ଜଳସେଚନ କରନ୍ତୁ।",
        "as": f"{crop_disp} শস্যৰ {age_days} দিনৰ অৱস্থাত মাটিৰ আৰ্দ্ৰতা চাই পাতলীয়া পানী দিয়ক।",
        "ur": f"{crop_disp} کی {age_days} دن کی حالت میں مٹی کی نمی دیکھ کر ہلکا پانی دیں۔"
    }
    return templates.get(lang_key, templates["hi"])


CROP_LOCALIZED_NAMES = {
    "wheat": {
        "hi": "गेहूं", "hinglish": "Gehu", "en": "Wheat", "pa": "ਕਣਕ", "mr": "गहू", "bn": "গম", "gu": "ઘઉં", "ta": "கோதுமை", "te": "గోధుమ", "kn": "ಗೋಧಿ", "ml": "ഗോതമ്പ്", "or": "ଗହମ", "as": "গম", "ur": "گندم"
    },
    "tomato": {
        "hi": "टमाटर", "hinglish": "Tamatar", "en": "Tomato", "pa": "ਟਮਾਟਰ", "mr": "टोमॅटो", "bn": "টমেটো", "gu": "ટામેટા", "ta": "தக்காளி", "te": "టమోటా", "kn": "ಟೊಮೆಟೊ", "ml": "തക്കാളി", "or": "ଟମାଟୋ", "as": "টমেটো", "ur": "ٹماٹر"
    },
    "rice": {
        "hi": "धान", "hinglish": "Dhan", "en": "Rice", "pa": "ਝੋਨਾ", "mr": "भात", "bn": "ধান", "gu": "ડાંગર", "ta": "நெல்", "te": "వరి", "kn": "ಭತ್ತ", "ml": "നെല്ല്", "or": "ଧାନ", "as": "ধান", "ur": "چاول"
    },
    "potato": {
        "hi": "आलू", "hinglish": "Aloo", "en": "Potato", "pa": "ਆਲੂ", "mr": "बटाटा", "bn": "আলু", "gu": "બટાકા", "ta": "உருளைக்கிழங்கு", "te": "బంగాళాదుంప", "kn": "ಆಲೂಗಡ್ಡೆ", "ml": "ഉരുളക്കിഴങ്ങ്", "or": "ଆଳୁ", "as": "আলু", "ur": "آلو"
    },
    "cotton": {
        "hi": "कपास", "hinglish": "Kapas", "en": "Cotton", "pa": "ਨਰਮਾ", "mr": "कापूस", "bn": "তুলা", "gu": "કપાસ", "ta": "பருத்தி", "te": "పత్తి", "kn": "ಹತ್ತಿ", "ml": "പരുത്തി", "or": "କପା", "as": "কপাহ", "ur": "کپاس"
    },
    "onion": {
        "hi": "प्याज", "hinglish": "Pyaz", "en": "Onion", "pa": "ਪਿਆਜ਼", "mr": "कांदा", "bn": "পেঁয়াজ", "gu": "ડુંગળી", "ta": "வெங்காயம்", "te": "ఉల్లిపాయ", "kn": "ಈರುಳ್ಳಿ", "ml": "സവാള", "or": "ପିଆଜ", "as": "পিয়াঁজ", "ur": "پیاز"
    },
    "chilli": {
        "hi": "मिर्च", "hinglish": "Mirch", "en": "Chilli", "pa": "ਮਿਰਚ", "mr": "मिरची", "bn": "লঙ্কা", "gu": "મરચાં", "ta": "மிளகாய்", "te": "మిరపకాయ", "kn": "ಮೆಣಸಿನಕಾಯಿ", "ml": "പച്ചമുളക്", "or": "ଲଙ୍କା", "as": "জলকীয়া", "ur": "مرچ"
    },
    "sugarcane": {
        "hi": "गन्ना", "hinglish": "Ganna", "en": "Sugarcane", "pa": "ਗੰਨਾ", "mr": "ऊस", "bn": "আঁখ", "gu": "શેરડી", "ta": "கரும்பு", "te": "చెరకు", "kn": "ಕಬ್ಬು", "ml": "കരിമ്പ്", "or": "ଆଖୁ", "as": "কুঁহিয়াৰ", "ur": "گنا"
    },
    "mustard": {
        "hi": "सरसों", "hinglish": "Sarson", "en": "Mustard", "pa": "ਸਰ੍ਹੋਂ", "mr": "मोहरी", "bn": "সরিষা", "gu": "રાય", "ta": "கடுகு", "te": "ఆవాలు", "kn": "ಸಾಸಿವೆ", "ml": "കടുക്", "or": "ସୋରିଷ", "as": "সৰিয়হ", "ur": "سرسوں"
    },
    "soybean": {
        "hi": "सोयाबीन", "hinglish": "Soyabean", "en": "Soybean", "pa": "ਸੋਇਆਬੀਨ", "mr": "सोयाबीन", "bn": "সয়াবিন", "gu": "સોયાબીન", "ta": "சோயாபீன்", "te": "సోయాబీన్", "kn": "ಸೋಯಾಬೀನ್", "ml": "സോയാബീൻ", "or": "ସୋୟାବିନ୍", "as": "ছয়াবিন", "ur": "سویا بین"
    }
}


# ============================================================
# KISAN SAATHI FOLLOW-UP & STAGE ADVISORY TEMPLATES
# ============================================================

FOLLOW_UP_IRRIGATION_TEMPLATES = {
    "wheat": {
        "hi": "गेहूं में पहली सिंचाई (CRI स्टेज, 20-25 दिन) के बाद दूसरी सिंचाई कल्ले फूटते समय यानी 40-45 दिन की अवस्था पर करनी चाहिए। मिट्टी में नमी देखकर ही 40-45 दिन पर हल्का पानी दें।",
        "hinglish": "Gehu mein pehli CRI sinchai (20-25 din) ke baad agli sinchai tillering stage par lagbhag 40-45 din par karni chahiye. Mitti ki nami dekh kar hi agla paani dein.",
        "en": "After the first CRI irrigation (20-25 days), the second irrigation for Wheat is recommended at the tillering stage around 40-45 days. Check topsoil moisture before watering.",
        "pa": "ਕਣਕ ਵਿੱਚ ਪਹਿਲੀ ਸਿੰਚਾਈ (20-25 ਦਿਨ) ਤੋਂ ਬਾਅਦ ਦੂਜੀ ਸਿੰਚਾਈ ਫੁਟਾਰੇ ਵੇਲੇ ਯਾਨੀ 40-45 ਦਿਨਾਂ 'ਤੇ ਕਰੋ। ਜ਼ਮੀਨ ਵਿੱਚ ਨਮੀ ਵੇਖ ਕੇ ਹੀ ਅਗਲਾ ਪਾਣੀ ਦਿਓ।",
        "mr": "गव्हामध्ये पहिल्या पाण्यानंतर (२०-२५ दिवस) दुसरे पाणी फुटवे फुटण्याच्या अवस्थेत म्हणजेच ४०-४५ दिवसांनी द्यावे. मातीतील ओलावा तपासूनच हलके पाणी द्या.",
        "bn": "গমের প্রথম সেচের (২০-২৫ দিন) পর দ্বিতীয় সেচ কুশি বের হওয়ার সময় অর্থাৎ ৪০-৪৫ দিনের মাথায় দেওয়া উচিত। মাটিতে আর্দ্রতা দেখে হালকা জল দিন।",
        "gu": "ઘઉંમાં પ્રથમ પિયત (૨૦-૨૫ દિવસ) પછી બીજું પિયત ફુટાવ સમયે એટલે કે ૪૦-૪૫ દિવસે આપવું જોઈએ. જમીનનો ભેજ જોઈને જ હળવું પિયત આપો.",
        "ta": "கோதுமையில் முதல் பாசனத்திற்குப் பிறகு (20-25 நாட்கள்), இரண்டாவது பாசனம் 40-45 நாட்களில் தூர்கட்டும் பருவத்தில் செய்யப்பட வேண்டும்.",
        "te": "గోధుమలో మొదటి సాగునీటి (20-25 రోజులు) తర్వాత రెండవ నీరు 40-45 రోజుల పిలకల దశలో అందించాలి.",
        "kn": "ಗೋಧಿಯಲ್ಲಿ ಮೊದಲ ನೀರಾವರಿಯ ನಂತರ (20-25 ದಿನಗಳು), ಎರಡನೇ ನೀರಾವರಿಯನ್ನು 40-45 ದಿನಗಳ ತೆನೆ ಒಡೆಯುವ ಹಂತದಲ್ಲಿ ನೀಡಬೇಕು.",
        "ml": "ഗോതമ്പിൽ ആദ്യ നനയ്ക്ക് ശേഷം (20-25 ദിവസം) രണ്ടാമത്തെ നന 40-45 ദിവസത്തെ വളർച്ചാ ഘട്ടത്തിൽ നൽകണം.",
        "or": "ଗହମରେ ପ୍ରଥମ ଜଳସେଚନ (୨୦-୨୫ ଦିନ) ପରେ ଦ୍ୱିତୀୟ ଜଳସେଚନ ୪୦-୪୫ ଦିନରେ ଦିଅନ୍ତୁ।",
        "as": "ঘেঁহুত প্ৰথম জলসিঞ্চনৰ পিছত দ্বিতীয় জলসিঞ্চন ৪০-৪৫ দিনত কৰিব লাগে।",
        "ur": "گندم میں پہلی آبپاشی (20-25 دن) کے بعد دوسری آبپاشی 40-45 دن پر کرنی چاہیے۔"
    },
    "default": {
        "hi": "अपनी {crop} की फसल में अगली सिंचाई मिट्टी की ऊपरी 2-3 इंच परत की नमी सूखने पर ही करें। आमतौर पर पिछली सिंचाई के 15-20 दिन बाद हल्की सिंचाई की आवश्यकता होती है।",
        "hinglish": "Apni {crop} fasal mein agli sinchai soil moisture check karke karein. Usually pichhli sinchai ke 15-20 din baad light watering zaroori hoti hai.",
        "en": "For your {crop}, schedule the next irrigation when the top 2-3 inches of soil feel dry. Typically, light irrigation is needed 15-20 days after the previous watering.",
        "pa": "ਆਪਣੀ {crop} ਦੀ ਫ਼ਸਲ ਲਈ ਅਗਲੀ ਸਿੰਚਾਈ ਜ਼ਮੀਨ ਦੀ ਨਮੀ ਵੇਖ ਕੇ 15-20 ਦਿਨਾਂ ਬਾਅਦ ਕਰੋ।",
        "mr": "आपल्या {crop} पिकासाठी पुढचे पाणी मातीतील ओलावा तपासून १५-२० दिवसांनी द्या.",
        "bn": "আপনার {crop} ফসলে পরবর্তী সেচ মাটির আর্দ্রতা দেখে ১৫-২০ দিন পর দিন।",
        "gu": "તમારા {crop} પાકમાં આગામી પિયત જમીનનો ભેજ જોઈને ૧૫-૨૦ દિવસ પછી આપો.",
        "ta": "உங்கள் {crop} பயிருக்கு அடுத்த பாசனத்தை மண்ணின் ஈரப்பதத்தை அறிந்து 15-20 நாட்களுக்குப் பிறகு செய்யவும்.",
        "te": "మీ {crop} పంటకు తదుపరి సాగునీరు నేలలో తేమను బట్టి 15-20 రోజుల తర్వాత అందించండి.",
        "kn": "ನಿಮ್ಮ {crop} ಬೆಳೆಗೆ ಮುಂದಿನ ನೀರಾವರಿಯನ್ನು ಮಣ್ಣಿನ ತೇವಾಂಶ ನೋಡಿ 15-20 ದಿನಗಳ ನಂತರ ನೀಡಿ.",
        "ml": "നിങ്ങളുടെ {crop} വിളയ്ക്ക് അടുത്ത നന മണ്ണിന്റെ ഈർപ്പം നോക്കി 15-20 ദിവസത്തിന് ശേഷം നൽകുക.",
        "or": "ଆପଣଙ୍କ {crop} ଫସଲରେ ପରବର୍ତ୍ତୀ ଜଳସେଚନ ମାଟିର ଆର୍ଦ୍ରତା ଦେଖି ୧୫-୨୦ ଦିନ ପରେ କରନ୍ତୁ।",
        "as": "আপোনাৰ {crop} শস্যত পৰৱৰ্তী জলসিঞ্চন ১৫-২০ দিনৰ পিছত কৰক।",
        "ur": "اپنی {crop} کی فصل میں اگلی آبپاشی مٹی کی نمی دیکھ کر 15-20 دن بعد کریں۔"
    }
}

STAGE_FERTILIZER_GUIDANCE = {
    "wheat": {
        "early": { # 15-35 days
            "hi": "20-25 दिन के गेहूं में पहली सिंचाई के बाद प्रति एकड़ लगभग 30-35 किलोग्राम यूरिया का टॉप ड्रेसिंग (छिड़काव) करें। यदि पत्तियों में पीलापन दिखे, तो जिंक सल्फेट का छिड़काव भी कर सकते हैं।",
            "hinglish": "20-25 din ke gehu ke liye pehli sinchai ke baad 30-35 kg per acre Urea ka top-dressing karein. Agar yellowing ya zinc ki kami lage toh Zinc sulphate use kar sakte hain.",
            "en": "For 20-25 days old Wheat, top-dress 30-35 kg Urea per acre immediately following the first irrigation. If you notice leaf yellowing, spray zinc sulphate.",
            "pa": "20-25 ਦਿਨਾਂ ਦੀ ਕਣਕ ਲਈ ਪਹਿਲੀ ਸਿੰਚਾਈ ਤੋਂ ਬਾਅਦ ਪ੍ਰਤੀ ਏਕੜ 30-35 ਕਿਲੋ ਯੂਰੀਆ ਪਾਓ। ਜੇਕਰ ਪੀਲਾਪਣ ਹੋਵੇ ਤਾਂ ਜ਼ਿੰਕ ਸਲਫੇਟ ਦਾ ਛਿੜਕਾਅ ਕਰੋ।",
            "mr": "२०-२५ दिवसांच्या गव्हासाठी पहिल्या पाण्यानंतर एकरी ३०-३५ किलो युरिया खत द्यावे. पिवळेपणा असल्यास झिंक सल्फेटची फवारणी करावी.",
            "bn": "২০-২৫ দিনের গমের জন্য প্রথম সেচের পর প্রতি একরে ৩০-৩৫ কেজি ইউরিয়া প্রয়োগ করুন। পাতা হলুদ হলে জিঙ্ক সালফেট স্প্রে করুন।",
            "gu": "૨૦-૨૫ દિવસના ઘઉં માટે પ્રથમ પિયત પછી એકરે ૩૦-૩૫ કિલો યુરિયા આપો. પીળાશ જણાય તો ઝિંક સલ્ફેટ છાંટો.",
            "ta": "20-25 நாள் கோதுமைக்கு முதல் பாசனத்திற்குப் பிறகு ஏக்கருக்கு 30-35 கிலோ யூரியா இடவும்.",
            "te": "20-25 రోజుల గోధుమకు మొదటి సాగునీటి తర్వాత ఎకరానికి 30-35 కిలోల యూరియాను వేయండి.",
            "kn": "20-25 ದಿನಗಳ ಗೋಧಿಗೆ ಮೊದಲ ನೀರಾವರಿಯ ನಂತರ ಎಕರೆಗೆ 30-35 ಕೆಜಿ ಯೂರಿಯಾ ಹಾಕಿ.",
            "ml": "20-25 ദിവസത്തെ ഗോതമ്പിന് ആദ്യ നനയ്ക്ക് ശേഷം ഏക്കറിന് 30-35 കിലോ യൂറിയ നൽകുക.",
            "or": "୨୦-୨୫ ଦିନର ଗହମ ପାଇଁ ପ୍ରଥମ ଜଳସେଚନ ପରେ ଏକର ପିଛା ୩୦-୩୫ କେଜି ୟୁରିଆ ଦିଅନ୍ତୁ।",
            "as": "২০-২৫ দিনৰ ঘেঁহুৰ বাবে প্ৰথম জলসিঞ্চনৰ পিছত প্ৰতি একৰত ৩০-৩৫ কেজি ইউৰিয়া প্ৰয়োগ কৰক।",
            "ur": "20-25 دن کی گندم کے لیے پہلی آبپاشی کے بعد فی ایکڑ 30-35 کلو یوریا ڈالیں۔"
        }
    }
}

def get_followup_irrigation_advice(crop_name: Optional[str], age_days: Optional[int], lang_key: str) -> str:
    crop_lower = (crop_name or "wheat").lower()
    crop_disp = CROP_LOCALIZED_NAMES.get(crop_lower, {}).get(lang_key, (crop_name.capitalize() if crop_name else "Wheat"))
    
    if crop_lower in ["wheat", "gehu"]:
        return FOLLOW_UP_IRRIGATION_TEMPLATES["wheat"].get(lang_key, FOLLOW_UP_IRRIGATION_TEMPLATES["wheat"]["hi"])
    
    tmpl = FOLLOW_UP_IRRIGATION_TEMPLATES["default"].get(lang_key, FOLLOW_UP_IRRIGATION_TEMPLATES["default"]["hi"])
    return tmpl.replace("{crop}", crop_disp)

def get_stage_fertilizer_advice(crop_name: Optional[str], age_days: Optional[int], lang_key: str) -> str:
    crop_lower = (crop_name or "wheat").lower()
    crop_disp = CROP_LOCALIZED_NAMES.get(crop_lower, {}).get(lang_key, (crop_name.capitalize() if crop_name else "Wheat"))
    age_val = age_days if age_days is not None else 25

    templates = {
        "hi": f"{crop_disp} की {age_val} दिन की फसल में खाद प्रयोग से पहले कुछ महत्वपूर्ण बातें जांच लें:\n"
              f"1. क्या बुवाई के समय बेसल डोज (DAP/NPK) दी गई थी और कितनी मात्रा डाली गई थी?\n"
              f"2. क्या पत्तियों में पीलापन या पोषक तत्वों की कमी के लक्षण दिख रहे हैं?\n"
              f"3. क्या मिट्टी परीक्षण की रिपोर्ट उपलब्ध है?\n"
              f"सामान्यतः पहली हल्की सिंचाई के बाद पर्याप्त नमी में ही आवश्यकतानुसार यूरिया या सूक्ष्म पोषक तत्वों की टॉप-ड्रेसिंग की जाती है। बिना जांच के अधिक मात्रा में खाद न डालें।",
        "hinglish": f"{crop_disp} ki {age_val} din ki stage par fertilizer apply karne se pehle ye baatein check karein:\n"
                    f"1. Kya sowing ke time basal dose (DAP/NPK) dali gayi thi aur kitni quantity thi?\n"
                    f"2. Kya leaves mein yellowing ya deficiency ke symptoms dikh rahe hain?\n"
                    f"3. Kya soil test report available hai?\n"
                    f"Normally pehli light irrigation ke baad moisture hone par hi balanced top-dressing karni chahiye. Unverified fixed dose daalne se bachein.",
        "en": f"Before applying fertilizer to your {age_val}-day-old {crop_disp}, verify the following:\n"
              f"1. Was a basal fertilizer dose (DAP/NPK) applied at sowing, and in what quantity?\n"
              f"2. Are there visible deficiency symptoms such as leaf yellowing?\n"
              f"3. Is a soil test report available?\n"
              f"Top-dressing is typically done only after the first light irrigation when adequate moisture is present. Avoid applying unverified fixed doses without assessing prior basal application.",
        "pa": f"{crop_disp} ਦੀ {age_val} ਦਿਨਾਂ ਦੀ ਫ਼ਸਲ ਵਿੱਚ ਖਾਦ ਪਾਉਣ ਤੋਂ ਪਹਿਲਾਂ ਜਾਂਚੋ: ਕੀ ਬਿਜਾਈ ਵੇਲੇ ਬੇਸਲ ਖਾਦ ਪਾਈ ਸੀ? ਕੀ ਪੀਲਾਪਣ ਹੈ? ਮਿੱਟੀ ਪਰਖ ਅਨੁਸਾਰ ਹੀ ਸੰਤੁਲਿਤ ਖਾਦ ਪਾਓ।",
        "mr": f"{crop_disp} च्या {age_val} दिवसांच्या पिकात खत देण्यापूर्वी तपासा: पेरणीवेळी बेसल डोस दिला होता का? पानांवर पिवळेपणा आहे का? माती परीक्षणानुसारच संतुलित खत द्या.",
    }
    return templates.get(lang_key, templates["hi"])


def generate_stage_action_plan(crop_name: Optional[str], age_days: Optional[int], lang_key: str) -> str:
    crop_lower = (crop_name or "wheat").lower()
    crop_disp = CROP_LOCALIZED_NAMES.get(crop_lower, {}).get(lang_key, (crop_name.capitalize() if crop_name else "Wheat"))
    age_val = age_days if age_days is not None else 25

    if crop_lower in ["wheat", "gehu"] and 15 <= age_val <= 35:
        templates = {
            "hi": f"{age_val} दिन के {crop_disp} (CRI अवस्था) के लिए आज की मुख्य कार्य योजना:\n"
                  f"1. मिट्टी की ऊपरी 2-3 इंच परत में नमी की जांच करें।\n"
                  f"2. मौसम व बारिश का पूर्वानुमान देखें; यदि बारिश की संभावना न हो और मिट्टी सूखी हो तो हल्की सिंचाई करें।\n"
                  f"3. खेत में जलभराव न होने दें और जड़ों की बढ़वार सुरक्षित रखें।\n"
                  f"4. पत्तियों में पीलापन या कीट के शुरुआती लक्षणों की निगरानी करें।\n"
                  f"5. बिना आवश्यकता के अनावश्यक कीटनाशक या रासायनिक छिड़काव से बचें।",
            "hinglish": f"{age_val} din ke {crop_disp} (CRI stage) ke liye aaj ka action plan:\n"
                        f"1. Soil moisture check karein (top 2-3 inches).\n"
                        f"2. Rain forecast check karein; agar baarish na ho aur mitti sukhi ho toh light irrigation karein.\n"
                        f"3. Khet mein waterlogging na hone dein aur crown roots ko protect karein.\n"
                        f"4. Yellow leaves ya pests ke early symptoms inspect karein.\n"
                        f"5. Unnecessary chemical fertilizer ya pesticide sprays avoid karein.",
            "en": f"Today's action plan for your {age_val}-day-old {crop_disp} (CRI stage):\n"
                  f"1. Check topsoil moisture in the upper 2-3 inches.\n"
                  f"2. Review the rainfall forecast before planning any irrigation.\n"
                  f"3. Irrigate only if needed, applying a light watering and avoiding waterlogging.\n"
                  f"4. Monitor crown root development and inspect leaves for yellowing or disease symptoms.\n"
                  f"5. Avoid premature or unnecessary chemical fertilizer and pesticide applications.",
            "pa": f"{age_val} ਦਿਨਾਂ ਦੀ {crop_disp} (CRI ਸਟੇਜ) ਲਈ ਅੱਜ ਦੀ ਕਾਰਜ ਯੋਜਨਾ: ਮਿੱਟੀ ਵਿੱਚ ਨਮੀ ਵੇਖੋ, ਮੀਂਹ ਦਾ ਪੂਰਵ-ਅਨੁਮਾਨ ਚੈੱਕ ਕਰੋ, ਲੋੜ ਪੈਣ 'ਤੇ ਹੀ ਹਲਕੀ ਸਿੰਚਾਈ ਕਰੋ ਅਤੇ ਪੀਲੇਪਣ ਦੀ ਜਾਂਚ ਕਰੋ।",
            "mr": f"{age_val} दिवसांच्या {crop_disp} (CRI अवस्था) साठी आजची कार्ययोजना: मातीतील ओलावा तपासा, पावसाचा अंदाज घ्या, गरजेनुसार हलके पाणी द्या आणि अनावश्यक फवारणी टाळा.",
        }
        return templates.get(lang_key, templates["hi"])

    templates = {
        "hi": f"{crop_disp} की {age_val} दिन की अवस्था के लिए आज की कार्य योजना:\n"
              f"1. खेत की मिट्टी में नमी के स्तर की जांच करें।\n"
              f"2. आगामी 48 घंटों के मौसम पूर्वानुमान के अनुसार ही सिंचाई या छिड़काव का निर्णय लें।\n"
              f"3. खेत में कीट, रोग या खरपतवार के शुरुआती लक्षणों का निरीक्षण करें।\n"
              f"4. आवश्यकतानुसार ही संतुलित पोषक तत्वों का प्रयोग करें।",
        "hinglish": f"{crop_disp} ki {age_val} din ki stage ke liye aaj ka action plan:\n"
                    f"1. Field mein soil moisture level check karein.\n"
                    f"2. Agle 48 hours ke weather forecast ke according hi sinchai ka nirnay lein.\n"
                    f"3. Pests ya disease symptoms ka regular inspection karein.\n"
                    f"4. Zaroorat ke anusaar hi balanced nutrients use karein.",
        "en": f"Today's action plan for your {age_val}-day-old {crop_disp}:\n"
              f"1. Inspect topsoil moisture levels across the field.\n"
              f"2. Check the 48-hour local weather forecast before irrigating.\n"
              f"3. Scout for early signs of weeds, pests, or leaf discoloration.\n"
              f"4. Apply inputs only based on diagnosed field requirements.",
    }
    return templates.get(lang_key, templates["hi"])


LOCATION_FOLLOW_UP_QUESTIONS = {
    "hi": "आपके खेत का स्थान कौन सा है?",
    "hinglish": "Aapke khet ka sthan kaun sa hai?",
    "en": "What is your farm location?",
    "pa": "ਤੁਹਾਡੇ ਖੇਤ ਦਾ ਸਥਾਨ ਕਿਹੜਾ ਹੈ?",
    "mr": "आपल्या शेताचे ठिकाण कोणते आहे?",
    "bn": "আপনার খামারের অবস্থান কোথায়?",
    "gu": "તમારા ખેતરનું સ્થળ કયું છે?",
    "ta": "உங்கள் பண்ணை எங்கு அமைந்துள்ளது?",
    "te": "మీ పొలం ఏ ప్రాంతంలో ఉంది?",
    "kn": "ನಿಮ್ಮ ತೋಟ/ಹೊಲ ಎಲ್ಲಿದೆ?",
    "ml": "നിങ്ങളുടെ ഫാം എവിടെയാണ് സ്ഥിതി ചെയ്യുന്നത്?",
    "or": "ଆପଣଙ୍କ ଜମି କେଉଁ ସ୍ଥାନରେ ଅବସ୍ଥିତ?",
    "as": "আপোনাৰ পথাৰৰ স্থান ক'ত?",
    "ur": "آپ کے کھیت کا مقام کون سا ہے؟",
}

# ============================================================
# CROP DISEASE PROMPTS & ADVISORY TEMPLATES
# ============================================================

PHOTO_REQUEST_TEMPLATES = {
    "hi": "कृपया प्रभावित पत्तियों और पूरे पौधे की साफ फोटो भेजें। फोटो में पत्तियां स्पष्ट दिखनी चाहिए।",
    "hinglish": "Kripya prabhavit pattiyon aur pure paudhe ki saaf photo bhejein. Photo mein pattiyan spasht dikhni chahiyein.",
    "en": "Please send a clear photo of the affected leaves and the whole plant. The leaves should be clearly visible in the photo.",
    "pa": "ਕਿਰਪਾ ਕਰਕੇ ਪ੍ਰਭਾਵਿਤ ਪੱਤਿਆਂ ਅਤੇ ਪੂਰੇ ਬੂਟੇ ਦੀ ਸਾਫ਼ ਫ਼ੋਟੋ ਭੇਜੋ। ਫ਼ੋਟੋ ਵਿੱਚ ਪੱਤੇ ਸਾਫ਼ ਦਿਖਾਈ ਦੇਣੇ ਚਾਹੀਦੇ ਹਨ।",
    "mr": "कृपया बाधित पाने आणि संपूर्ण झाडाचा स्पष्ट फोटो पाठवा. फोटोमध्ये पाने स्पष्ट दिसली पाहिजेत.",
    "bn": "দয়া করে আক্রান্ত পাতা এবং পুরো গাছের একটি পরিষ্কার ছবি পাঠান। ছবিতে পাতাগুলি স্পষ্টভাবে দৃশ্যমান হওয়া উচিত।",
    "gu": "કૃપા કરીને અસરગ્રસ્ત પાંદડા અને આખા છોડનો સ્પષ્ટ ફોટો મોકલો. ફોટામાં પાંદડા સ્પષ્ટ દેખાવા જોઈએ.",
    "ta": "பாதிக்கப்பட்ட இலைகள் மற்றும் முழு செடியின் தெளிவான புகைப்படத்தை அனுப்பவும். புகைப்படத்தில் இலைகள் தெளிவாகத் தெரிய வேண்டும்.",
    "te": "దయచేసి ప్రభావితమైన ఆకులు మరియు మొత్తం మొక్క యొక్క స్పష్టమైన ఫోటోను పంపండి. ఫోటోలో ఆకులు స్పష్టంగా కనిపించాలి.",
    "kn": "ದಯವಿಟ್ಟು ಬಾಧಿತ ಎಲೆಗಳು ಮತ್ತು ಇಡೀ ಸಸ್ಯದ ಸ್ಪಷ್ಟ ಫೋಟೋವನ್ನು ಕಳುಹಿಸಿ. ಫೋಟೋದಲ್ಲಿ ಎಲೆಗಳು ಸ್ಪಷ್ಟವಾಗಿ ಕಾಣಿಸಬೇಕು.",
    "ml": "ബാധിച്ച ഇലകളുടെയും ചെടിയുടെയും വ്യക്തമായ ഫോട്ടോ അയക്കുക. ഫോട്ടോയിൽ ഇലകൾ വ്യക്തമായി കാണണം.",
    "or": "ଦୟାକରି ପ୍ରଭାବିତ ପତ୍ର ଏବଂ ସମ୍ପୂର୍ଣ୍ଣ ଗଛର ଏକ ସ୍ପଷ୍ଟ ଫଟୋ ପଠାନ୍ତୁ। ଫଟୋରେ ପତ୍ରଗୁଡ଼ିକ ସ୍ପଷ୍ଟ ଦେଖାଯିବା ଉଚିତ।",
    "as": "অনুগ্ৰহ কৰি আক্ৰান্ত পাত আৰু গোটেই গছজোপাৰ এখন পৰিষ্কাৰ ফটো পঠিয়াওক।",
    "ur": "براہ کرم متاثرہ پتوں اور پورے پودے کی واضح تصویر بھیجیں۔ تصویر میں پتے واضح نظر آنے چاہئیں۔",
}

def format_disease_prediction_response(
    disease_name: str,
    confidence: float,
    crop_name: Optional[str],
    lang_key: str = "hi",
    rec_data: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Format confidence-aware, localized response for crop disease prediction.
    - High Confidence (>= 75%): "मॉडल के अनुसार यह समस्या संभवतः..."
    - Medium Confidence (50% <= c < 75%): "फोटो के आधार पर यह समस्या हो सकती है..."
    - Low Confidence (< 50%): "फोटो से स्पष्ट पहचान नहीं हो पा रही है..."
    """
    crop_lower = (crop_name or "wheat").lower()
    crop_disp = CROP_LOCALIZED_NAMES.get(crop_lower, {}).get(lang_key, (crop_name.capitalize() if crop_name else "Crop"))
    
    desc = ""
    if rec_data and isinstance(rec_data, dict):
        desc = rec_data.get("description", "")
        if desc and not desc.endswith("."):
            desc += "."

    conf_pct = round(float(confidence), 1)

    # Low confidence (< 50%) or unclear
    if conf_pct < 50.0:
        if lang_key == "en":
            return "The condition could not be clearly identified from the photo. Please send a clearer, close-up photo of the leaf with good lighting."
        elif lang_key == "hinglish":
            return "Photo se spasht pehchan nahi ho pa rahi hai. Kripya patti ke paas se achhi roshni mein saaf photo dobara bhejein."
        else:
            return "फोटो से स्पष्ट पहचान नहीं हो पा रही है। कृपया पत्ती के पास से एक अच्छी रोशनी वाली साफ फोटो दोबारा भेजें।"

    # High confidence (>= 75%)
    if conf_pct >= 75.0:
        if lang_key == "en":
            return (
                f"According to the model, this condition is likely {disease_name} on your {crop_disp} ({conf_pct}% confidence). "
                f"{desc} Please confirm the diagnosis with a local agricultural expert and follow the registered product label before applying treatments."
            ).strip()
        elif lang_key == "hinglish":
            return (
                f"Model ke anusaar yeh samasya sambhavtah {disease_name} hai ({conf_pct}% confidence). "
                f"{desc} Upchar shuru karne se pehle local krishi visheshagya se confirm kar lein aur product label ke nirdesh follow karein."
            ).strip()
        else:
            return (
                f"मॉडल के अनुसार यह समस्या संभवतः {disease_name} है (सटीकता: {conf_pct}%)। "
                f"{desc} उपचार शुरू करने से पहले स्थानीय कृषि विशेषज्ञ से पुष्टि कर लें और उत्पाद के लेबल पर दिए गए निर्देशों का पालन करें।"
            ).strip()

    # Medium confidence (50% to 75%)
    if lang_key == "en":
        return (
            f"Based on the photo, this condition could possibly be {disease_name} on your {crop_disp} ({conf_pct}% confidence). "
            f"Inspect the underside of the leaves and surrounding plants to confirm, and consult your local agricultural office."
        ).strip()
    elif lang_key == "hinglish":
        return (
            f"Photo ke aadhar par yeh problem {disease_name} ho sakti hai ({conf_pct}% confidence). "
            f"Sahi pushti ke liye pattiyon ke nichle hisse ki jaanch karein aur local krishi adhikari se salah lein."
        ).strip()
    else:
        return (
            f"फोटो के आधार पर यह समस्या {disease_name} हो सकती है (सटीकता: {conf_pct}%)। "
            f"सटीक पुष्टि के लिए पत्तियों के निचले हिस्से की भी जांच करें और स्थानीय कृषि केंद्र से सलाह लें।"
        ).strip()


def generate_disease_treatment_advice(
    disease_name: str,
    crop_name: Optional[str],
    lang_key: str = "hi",
    rec_data: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate safe, agronomic treatment advice for diagnosed disease without unverified fixed doses.
    """
    crop_lower = (crop_name or "wheat").lower()
    crop_disp = CROP_LOCALIZED_NAMES.get(crop_lower, {}).get(lang_key, (crop_name.capitalize() if crop_name else "Crop"))
    
    org_opt = ""
    chem_opt = ""
    if rec_data and isinstance(rec_data, dict):
        org = rec_data.get("organic_option") or rec_data.get("bio_fungicide") or ""
        chem = rec_data.get("chemical_option") or rec_data.get("treatment") or ""
        if org:
            org_opt = f"जैविक उपाय: {org}।" if lang_key != "en" else f"Organic measure: {org}."
        if chem:
            chem_opt = f"रासायनिक विकल्प: {chem}।" if lang_key != "en" else f"Chemical option: {chem}."

    if lang_key == "en":
        return (
            f"Management guidance for {disease_name} in {crop_disp}:\n"
            f"1. Cultural & Organic: Prune and safely destroy heavily infected leaves to reduce spread. Apply neem oil or biological bio-fungicide formulations in early stages.\n"
            f"2. Field Management: Ensure proper airflow and avoid overhead irrigation to keep foliage dry.\n"
            f"3. Chemical Care: {chem_opt if chem_opt else 'If chemical intervention is necessary, consult a registered fungicide.'} "
            f"Always verify diagnosis with a local agricultural extension officer and strictly follow product label dilution and safety guidelines. Avoid applying unverified fixed chemical doses."
        )
    elif lang_key == "hinglish":
        return (
            f"{crop_disp} mein {disease_name} ke bachav aur upchar ke kadam:\n"
            f"1. Organic & Cultural Upay: Prabhavit pattiyon ko todkar khet se door nasht karein. Shuruati stage mein neem oil ya bio-fungicide ka prayog karein.\n"
            f"2. Field Care: Khet mein hawa ka aawagaman banaye rakhein aur waterlogging se bachein taaki nami kam rahe.\n"
            f"3. Dawa: {chem_opt if chem_opt else 'Zaroorat padne par registered fungicide ka istemal karein.'} "
            f"Bina pushti ke koi bhi chemical na daalein. Hamesha local krishi adhikari ki salah aur product label ke nirdeshon ka palan karein."
        )
    else:
        return (
            f"{crop_disp} में {disease_name} के सुरक्षित प्रबंधन और उपचार के कदम:\n"
            f"1. जैविक व कृषि उपाय: अधिक प्रभावित पत्तियों को तोड़कर खेत से दूर सुरक्षित रूप से नष्ट करें। शुरुआती अवस्था में नीम तेल या जैविक फफूंदनाशी का प्रयोग करें।\n"
            f"2. खेत की देखभाल: खेत में जल निकासी अच्छी रखें और पत्तियों को अधिक समय तक गीला न रहने दें।\n"
            f"3. रासायनिक सलाह: {chem_opt if chem_opt else 'आवश्यकता पड़ने पर अनुशंसित फफूंदनाशी का उपयोग किया जा सकता है।'} "
            f"बिना जांच और पुष्टि के कोई भी रासायनिक दवा न डालें। हमेशा उत्पाद के लेबल पर दिए गए निर्देशों और स्थानीय कृषि अधिकारी की सलाह का पालन करें।"
        )


def generate_disease_cause_advice(
    disease_name: str,
    crop_name: Optional[str],
    lang_key: str = "hi",
    rec_data: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Explain causes of the diagnosed disease (fungal spores, weather, humidity, dense canopy).
    """
    crop_lower = (crop_name or "wheat").lower()
    crop_disp = CROP_LOCALIZED_NAMES.get(crop_lower, {}).get(lang_key, (crop_name.capitalize() if crop_name else "Crop"))

    if lang_key == "en":
        return (
            f"{disease_name} in {crop_disp} is typically triggered by favorable weather conditions such as high humidity, "
            f"dense crop canopy, wet foliage from rain or heavy dew, and fungal spores carried by wind. "
            f"Waterlogging and excess nitrogen can also increase crop susceptibility."
        )
    elif lang_key == "hinglish":
        return (
            f"{crop_disp} mein {disease_name} aamtaur par zyada nami, barish ya os ke karan pattiyon par paani tike rehne, "
            f"hawa se fungal spores aane aur ghanipan ke karan lagti hai. Excess moisture aur nitrogen bhi ise badhate hain."
        )
    else:
        return (
            f"{crop_disp} में {disease_name} का मुख्य कारण अधिक नमी, बारिश या ओस के कारण पत्तियों का लंबे समय तक गीला रहना, "
            f"हवा द्वारा फफूंद के बीजाणुओं (spores) का फैलना और खेत में सघन बुवाई होना है। जलभराव व अत्यधिक यूरिया से भी इसका प्रकोप बढ़ सकता है।"
        )


def generate_disease_spread_advice(
    disease_name: str,
    crop_name: Optional[str],
    lang_key: str = "hi",
    rec_data: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Explain spread risks and contagion prevention for the diagnosed disease.
    """
    crop_lower = (crop_name or "wheat").lower()
    crop_disp = CROP_LOCALIZED_NAMES.get(crop_lower, {}).get(lang_key, (crop_name.capitalize() if crop_name else "Crop"))

    if lang_key == "en":
        return (
            f"Yes, {disease_name} can spread to adjacent plants and susceptible crops through wind, splashing rain, and contaminated farm equipment. "
            f"To prevent spread: remove and burn infected residues, sanitize cutting tools, maintain plant spacing, and avoid working in wet fields."
        )
    elif lang_key == "hinglish":
        return (
            f"Haan, {disease_name} hawa, baarish ke chheenton aur farm tools ke zariye aas-paas ke paudhon mein fail sakti hai. "
            f"Iske failav ko rokne ke liye infected pattiyon ko khet se bahar karein, khet ke aozaron ko saaf rakhein aur geeli fasal mein kaam na karein."
        )
    else:
        return (
            f"हाँ, {disease_name} हवा, बारिश के छींटों और कृषि औजारों के माध्यम से पास के पौधों और अनुकूल फसलों में फैल सकती है। "
            f"फैलाव रोकने के लिए संक्रमित पत्तियों को खेत से बाहर निकालकर नष्ट करें, औजारों को साफ रखें और गीले खेत में अनावश्यक हलचल से बचें।"
        )

SOIL_MOISTURE_FOLLOW_UP_QUESTIONS = {
    "hi": "क्या आपके खेत की मिट्टी अभी सूखी है या उसमें नमी है?",
    "hinglish": "Kya aapke khet ki mitti abhi sukhi hai ya usmein nami hai?",
    "en": "Is your field soil currently dry or does it have moisture?",
    "pa": "ਕੀ ਤੁਹਾਡੇ ਖੇਤ ਦੀ ਮਿੱਟੀ ਇਸ ਵੇਲੇ ਸੁੱਕੀ ਹੈ ਜਾਂ ਉਸ ਵਿੱਚ ਨਮੀ ਹੈ?",
    "mr": "आपल्या शेतातील माती सध्या कोरडी आहे की त्यात ओलावा आहे?",
    "bn": "আপনার জমির মাটি কি এখন শুকনো নাকি আর্দ্রতা আছে?",
    "gu": "શું તમારા ખેતરની માટી અત્યારે સૂકી છે કે તેમાં ભેજ છે?",
    "ta": "உங்கள் நிலத்தின் மண் இப்போது உலர்ந்துள்ளதா அல்லது ஈரமாக உள்ளதா?",
    "te": "మీ పొలంలో నేల ప్రస్తుతం పొడిగా ఉందా లేదా తేమగా ఉందా?",
    "kn": "ನಿಮ್ಮ ಹೊಲದ ಮಣ್ಣು ಈಗ ಒಣಗಿದೆಯೇ ಅಥವಾ ತೇವಾಂಶವಿದೆಯೇ?",
    "ml": "നിങ്ങളുടെ തോട്ടത്തിലെ മണ്ണ് ഇപ്പോൾ ഉണങ്ങിയതാണോ അതോ ഈർപ്പമുണ്ടോ?",
    "or": "ଆପଣଙ୍କ ଜମିର ମାଟି ଏବେ ଶୁଖିଲା ଅଛି ନା ଆର୍ଦ୍ରତା ରହିଛି?",
    "as": "আপোনাৰ পথাৰৰ মাটি এতিয়া শুকান নে আৰ্দ্ৰতা আছে?",
    "ur": "کیا آپ کے کھیت کی مٹی ابھی سوکھی ہے یا اس میں نمی ہے؟",
}

async def generate_weather_aware_irrigation_advice(
    crop_name: Optional[str],
    crop_age_days: Optional[int],
    location: Optional[str],
    soil_moisture: Optional[str] = None,
    soil_type: Optional[str] = None,
    irrigation_method: Optional[str] = None,
    lang_key: str = "hi",
    weather_override: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Optional[Dict[str, Any]], Dict[str, Any]]:
    """
    Combines farm context (crop, age, soil moisture, location) with live weather & rain forecast.
    Produces cautious, agronomic irrigation advice without inventing data.
    """
    crop_lower = (crop_name or "wheat").lower()
    crop_disp = CROP_LOCALIZED_NAMES.get(crop_lower, {}).get(lang_key, (crop_name.capitalize() if crop_name else "Wheat"))
    age_val = crop_age_days if crop_age_days is not None else 25
    loc_display = location or ("आपके क्षेत्र" if lang_key in ["hi", "mr"] else ("aapke area" if lang_key == "hinglish" else "your area"))

    weather_available = False
    rain_expected = False
    rain_prob = 0
    temp = 28.0
    weather_cond = "Clear"
    weather_summary = ""

    # 1. Fetch live weather & timing advice for location
    if weather_override is not None:
        weather_available = weather_override.get("available", False)
        rain_expected = weather_override.get("rain_expected", False)
        rain_prob = weather_override.get("rain_probability", 70 if rain_expected else 10)
        temp = weather_override.get("temperature", 28.0)
        weather_cond = weather_override.get("weather_condition", "Rain" if rain_expected else "Clear sky")
        weather_summary = weather_override.get("summary", f"Temperature: {temp}°C, Condition: {weather_cond}")
    elif location:
        try:
            from app.services.timing_advice_service import resolve_farm_coordinates, calculate_timing_advice
            from app.services.weather_service import get_current_weather

            lat, lon, loc_resolved = resolve_farm_coordinates(region_str=location)
            cw = await get_current_weather(lat, lon)
            timing = await calculate_timing_advice(region_str=location, crop_name=crop_name)

            weather_available = True
            temp = cw.get("temperature", 28.0)
            weather_cond = cw.get("weather_condition", "Partly cloudy")
            rain_prob = timing.get("rain_probability", cw.get("rain_probability", 0))
            rain_expected = bool(timing.get("rain_risk") or rain_prob >= 40 or cw.get("rainfall", 0) > 0)
            
            if lang_key == "en":
                weather_summary = f"Current temperature is {temp}°C with {weather_cond} in {loc_resolved} (Rain risk: {rain_prob}%)."
            elif lang_key == "hinglish":
                weather_summary = f"{loc_resolved} mein current temperature {temp}°C aur mausam {weather_cond} hai (Baarish chance: {rain_prob}%)."
            else:
                weather_summary = f"{loc_resolved} में वर्तमान तापमान {temp}°C और मौसम {weather_cond} है (बारिश की संभावना: {rain_prob}%)।"
        except Exception:
            weather_available = False
            rain_expected = False
            weather_summary = "Weather service temporarily unavailable."
    else:
        weather_available = False
        rain_expected = False
        weather_summary = "Location not provided."

    weather_dict = {
        "available": weather_available,
        "rain_expected": rain_expected,
        "summary": weather_summary,
        "rain_probability": rain_prob,
        "temperature": temp,
    }

    # 2. Build Cautious Advice
    # CASE A: Weather available and rain is expected
    if weather_available and rain_expected:
        if lang_key == "en":
            resp_text = (
                f"Based on the weather forecast for {loc_display}, rain is expected in the next 24 to 48 hours ({rain_prob}% chance). "
                f"Consider postponing irrigation for your {age_val}-day-old {crop_disp} to prevent waterlogging and protect roots. "
                f"Always check topsoil moisture before making a final decision."
            )
        elif lang_key == "hinglish":
            resp_text = (
                f"Mausam aur baarish ki sambhavna ke anusaar, {loc_display} mein agle 24 se 48 hours mein baarish ka risk ({rain_prob}%) hai. "
                f"Isliye abhi apne {age_val} din ke {crop_disp} mein sinchai postpone karne par vichar karein taaki khet mein waterlogging na ho. "
                f"Pehle mitti ki nami check karke hi nirnay lein."
            )
        else: # Default Hindi
            resp_text = (
                f"मौसम और बारिश की संभावना के अनुसार, {loc_display} में अगले 24 से 48 घंटों में बारिश की संभावना ({rain_prob}%) है। "
                f"इसलिए अभी अपने {age_val} दिन के {crop_disp} में सिंचाई टालने पर विचार करें ताकि खेत में जलभराव न हो और जड़ें सुरक्षित रहें। "
                f"मिट्टी की नमी जांचकर ही अंतिम निर्णय लें।"
            )

    # CASE B: Weather available and no rain expected (Favorable / Dry)
    elif weather_available and not rain_expected:
        if lang_key == "en":
            resp_text = (
                f"According to the weather forecast for {loc_display}, no significant rain is expected in the next 48 hours (temperature {temp}°C). "
                f"For your {age_val}-day-old {crop_disp}, if the soil feels dry, a light irrigation may be needed. "
                f"Ensure no waterlogging occurs in the field and always check soil moisture before deciding."
            )
        elif lang_key == "hinglish":
            resp_text = (
                f"Mausam ke anusaar {loc_display} mein agle 48 hours mein baarish ka anuman nahi hai (temperature {temp}°C). "
                f"Aapke {age_val} din ke {crop_disp} ke liye, agar mitti thodi sukhi hai toh halki sinchai ki zaroorat ho sakti hai. "
                f"Dhyan rahe khet mein waterlogging na hone dein aur mitti ki nami check karke hi decision lein."
            )
        else: # Default Hindi
            resp_text = (
                f"मौसम के अनुसार {loc_display} में अगले 48 घंटों में बारिश की संभावना नहीं है (तापमान {temp}°C)। "
                f"आपके {age_val} दिन के {crop_disp} के लिए, यदि मिट्टी थोड़ी सूखी है तो हल्की सिंचाई की जरूरत हो सकती है। "
                f"ध्यान रहे खेत में जलभराव न होने दें और पहले मिट्टी की नमी जांचकर ही निर्णय लें।"
            )

    # CASE C: Weather unavailable / failed / missing location
    else:
        if lang_key == "en":
            resp_text = (
                f"Live weather data for {loc_display} could not be retrieved. "
                f"For your {age_val}-day-old {crop_disp}, do not irrigate based solely on crop age. "
                f"Check the top 2-3 inches of soil moisture first; if dry, a light irrigation may be needed. "
                f"Ensure the field does not get waterlogged."
            )
        elif lang_key == "hinglish":
            resp_text = (
                f"{loc_display} ke liye live mausam ki jankari abhi uplabdh nahi ho saki. "
                f"Aapke {age_val} din ke {crop_disp} ke liye keval crop age dekhkar sinchai na karein. "
                f"Pehle mitti ki oopri 2-3 inch parat mein nami check karein; agar mitti sukhi ho toh halki sinchai ki zaroorat ho sakti hai. "
                f"Khet mein waterlogging na hone dein."
            )
        else: # Default Hindi
            resp_text = (
                f"{loc_display} के लिए मौसम की सटीक जानकारी अभी उपलब्ध नहीं हो सकी है। "
                f"आपके {age_val} दिन के {crop_disp} के लिए केवल फसल की अवस्था देखकर सिंचाई न करें। "
                f"पहले मिट्टी की ऊपरी 2-3 इंच परत में नमी की जांच करें; यदि मिट्टी सूखी हो तो हल्की सिंचाई की जरूरत हो सकती है। "
                f"खेत में जलभराव न होने दें।"
            )

    return resp_text, None, weather_dict


# ============================================================
# KISAN SAATHI MASTER INTERNAL RESPONSE DISPATCHER
# ============================================================

async def get_response_for_intent(
    intent_result: Dict[str, Any],
    text: str,
    language: str = "hi",
    context: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, str]]] = None
) -> Tuple[str, Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Kisan Saathi Master Response Dispatcher:
    - Identifies missing critical information (crop -> crop_age -> location -> soil_moisture).
    - Asks single, natural follow-up questions when needed.
    - Resolves contextual guidance once crop is known.
    - Retrieves live weather when location is provided and yields weather-aware cautious irrigation guidance.
    - Handles follow-up irrigation, stage fertilizer, and next-step actions using context.
    - Returns (response_text, navigation_action, weather_dict).
    """
    intent = intent_result.get("intent", "fallback")
    sub_intent = intent_result.get("sub_intent")
    detected_lang = intent_result.get("language") or language or "hi"
    lang_key = (detected_lang).strip().lower().split("-")[0]
    if lang_key not in SUPPORTED_LANGUAGES:
        lang_key = "hi"
        
    ctx = intent_result.get("context") or context or {}
    detected_crop = intent_result.get("detected_crop") or ctx.get("crop") or extract_crop_entity(text)
    if not detected_crop and context and isinstance(context, dict):
        detected_crop = context.get("crop") or context.get("crop_name") or context.get("crop_type")

    nav_action = intent_result.get("navigation_action")
    resolved_pending = intent_result.get("resolved_pending_field")
    crop_age_days = intent_result.get("crop_age_days") or ctx.get("crop_age_days")
    location = intent_result.get("location") or ctx.get("location")
    soil_moisture = intent_result.get("soil_moisture") or ctx.get("soil_moisture")
    
    # 1. App Help / Navigation
    if intent == "app_help":
        return generate_app_help_response(lang_key), nav_action, None
        
    # 2. Mandi / Market Prices
    if intent == "mandi":
        crop_disp = detected_crop.capitalize() if detected_crop else "Wheat"
        return generate_market_response(crop_disp, lang_key), nav_action or {"action": "navigate", "route": "marketplace", "target": "/frontend/pages/crop-listings.html", "label": "Marketplace"}, None

    # 3. Weather
    if intent == "weather":
        if not location:
            loc_q = LOCATION_FOLLOW_UP_QUESTIONS.get(lang_key, LOCATION_FOLLOW_UP_QUESTIONS["hi"])
            return loc_q, nav_action, {"available": False, "rain_expected": False, "summary": "Location required"}

        try:
            from app.services.timing_advice_service import resolve_farm_coordinates, calculate_timing_advice
            from app.services.weather_service import get_current_weather
            lat, lon, loc_resolved = resolve_farm_coordinates(region_str=location)
            cw = await get_current_weather(lat, lon)
            timing = await calculate_timing_advice(region_str=location, crop_name=detected_crop or "Crop")
            rain_prob = timing.get("rain_probability", cw.get("rain_probability", 0))
            rain_expected = bool(timing.get("rain_risk") or rain_prob >= 40 or cw.get("rainfall", 0) > 0)
            weather_text = generate_weather_voice_response(cw, timing, detected_crop, lang_key, location=loc_resolved or location)
            weather_meta = {
                "available": True,
                "rain_expected": rain_expected,
                "summary": weather_text,
                "rain_probability": rain_prob,
                "temperature": cw.get("temperature", 28.0)
            }
            return weather_text, nav_action or {"action": "navigate", "route": "weather", "target": "/frontend/pages/weather-dashboard.html", "label": "Live Weather"}, weather_meta
        except Exception:
            if lang_key == "en":
                fail_text = f"Live weather data for {location} could not be retrieved at the moment. Please try again in a little while."
            elif lang_key == "hinglish":
                fail_text = f"{location} ke liye live mausam ki jankari abhi uplabdh nahi ho saki. Kripya thodi der baad dobara try karein."
            else:
                fail_text = f"{location} के लिए लाइव मौसम की जानकारी अभी प्राप्त नहीं हो सकी है। कृपया थोड़ी देर बाद पुनः प्रयास करें।"
            return fail_text, nav_action, {"available": False, "rain_expected": False, "summary": "Weather service temporarily unavailable"}

    # 4. Fallback / Non-Agri
    if intent == "fallback":
        return get_rejection_message(lang_key), None, None

    # 5. Action Plan (Stage-Aware)
    if intent == "action_plan":
        action_text = generate_stage_action_plan(detected_crop, crop_age_days, lang_key)
        return action_text, nav_action, None

    # 6. Fertilizer / Crop Guidance (Safe & Cautious)
    if intent in ["crop_guidance", "fertilizer"] or sub_intent == "fertilizer_followup":
        fert_text = get_stage_fertilizer_advice(detected_crop, crop_age_days, lang_key)
        return fert_text, nav_action, None

    # 7. Irrigation Intent Sequencing & Follow-up
    if intent == "irrigation":
        # Check 1: Crop missing
        if not detected_crop:
            followup_dict = FOLLOW_UP_QUESTIONS.get("irrigation", {})
            followup_text = followup_dict.get(lang_key, followup_dict.get("hi", followup_dict.get("en", "")))
            return followup_text, nav_action, None

        crop_lower = (detected_crop or "wheat").lower()
        crop_disp = CROP_LOCALIZED_NAMES.get(crop_lower, {}).get(lang_key, (detected_crop.capitalize() if detected_crop else "Wheat"))

        # Check 2: Crop age missing
        if crop_age_days is None:
            age_q_template = AGE_FOLLOW_UP_QUESTIONS.get(lang_key, AGE_FOLLOW_UP_QUESTIONS["hi"])
            age_q = age_q_template.replace("{crop}", crop_disp)
            age_q = age_q.replace("की फसल की फसल", "की फसल").replace("ਦੀ ਫ਼ਸਲ ਦੀ ਫ਼ਸਲ", "ਦੀ ਫ਼ਸਲ").replace("crop crop", "crop")
            return age_q, nav_action, None

        # Check 3: Follow-up irrigation ("अब पानी कब दूं?", "next watering", etc.)
        followup_irr_markers = [
            "ab pani", "ab paani", "next", "kab du", "kab dun", "agli sinchai", "dusri sinchai", "second irrigation", "agla pani", "agla paani", "water next", "irrigate next", "water again",
            "अब पानी", "फिर पानी", "अगला पानी", "अगली सिंचाई", "दूसरी सिंचाई"
        ]
        if sub_intent == "irrigation_followup" or any(p in text.lower() for p in followup_irr_markers):
            return get_followup_irrigation_advice(detected_crop, crop_age_days, lang_key), nav_action, None

        # Check 4: Age just answered -> Give CRI advice and request location
        if resolved_pending == "crop_age" and not location:
            if lang_key == "en":
                cri_text = f"For your {crop_age_days}-day-old {crop_disp} (CRI stage), the first irrigation is crucial. What is your farm location so we can evaluate local weather conditions?"
            elif lang_key == "hinglish":
                cri_text = f"{crop_disp} ki {crop_age_days} din ki CRI stage pehli aur sabse zaroori sinchai ka time hai. Aapke khet ka sthan kaun sa hai taaki live weather ke sath sahi salah mil sake?"
            else:
                cri_text = f"{crop_disp} की {crop_age_days} दिन की अवस्था (CRI स्टेज) पहली और सबसे महत्वपूर्ण सिंचाई का समय है। आपके खेत का स्थान कौन सा है ताकि मौसम के अनुसार सटीक सलाह दी जा सके?"
            return cri_text, nav_action, None

        # Check 5: Location missing
        if not location:
            loc_q = LOCATION_FOLLOW_UP_QUESTIONS.get(lang_key, LOCATION_FOLLOW_UP_QUESTIONS["hi"])
            return loc_q, nav_action, None

        # All known -> generate live weather-aware cautious advice
        advice_text, nav_act, weather_meta = await generate_weather_aware_irrigation_advice(
            crop_name=detected_crop,
            crop_age_days=crop_age_days,
            location=location,
            soil_moisture=soil_moisture,
            soil_type=ctx.get("soil_type"),
            irrigation_method=ctx.get("irrigation_method"),
            lang_key=lang_key,
        )
        return advice_text, nav_act or nav_action, weather_meta

    # 7.5 Crop Disease & Plant Health
    if intent == "crop_disease":
        detected_disease = ctx.get("detected_disease")
        disease_conf = ctx.get("disease_confidence") or 0.0
        rec_data = ctx.get("disease_details")
        lower_t = text.lower() if text else ""

        # Follow-up: Treatment
        if sub_intent == "disease_treatment" or any(w in lower_t for w in ["दवा", "इलाज", "उपचार", "रोकथाम", "treatment", "medicine", "cure", "spray", "dawa", "ilaj", "upchar", "अब क्या करूं", "what should i do", "ab kya karun", "what next"]):
            if detected_disease:
                return generate_disease_treatment_advice(detected_disease, detected_crop or "Crop", lang_key, rec_data), nav_action or {"action": "navigate", "route": "crop_monitoring", "target": "/frontend/pages/farmer-dashboard.html", "label": "Crop Health"}, None
            photo_prompt = PHOTO_REQUEST_TEMPLATES.get(lang_key, PHOTO_REQUEST_TEMPLATES["hi"])
            return photo_prompt, nav_action, None

        # Follow-up: Cause
        if sub_intent == "disease_cause" or any(w in lower_t for w in ["क्यों", "कारण", "cause", "why", "kyu", "karan", "reason"]):
            if detected_disease:
                return generate_disease_cause_advice(detected_disease, detected_crop or "Crop", lang_key, rec_data), nav_action, None
            photo_prompt = PHOTO_REQUEST_TEMPLATES.get(lang_key, PHOTO_REQUEST_TEMPLATES["hi"])
            return photo_prompt, nav_action, None

        # Follow-up: Spread
        if sub_intent == "disease_spread" or any(w in lower_t for w in ["फैल", "फैलेगी", "फैलाव", "spread", "contagious", "fail", "failav"]):
            if detected_disease:
                return generate_disease_spread_advice(detected_disease, detected_crop or "Crop", lang_key, rec_data), nav_action, None
            photo_prompt = PHOTO_REQUEST_TEMPLATES.get(lang_key, PHOTO_REQUEST_TEMPLATES["hi"])
            return photo_prompt, nav_action, None

        # If already diagnosed and user is inquiring
        if detected_disease and disease_conf > 0:
            return format_disease_prediction_response(detected_disease, disease_conf, detected_crop or "Crop", lang_key, rec_data), nav_action, None

        # Missing photo -> Ask for clear photo
        photo_prompt = PHOTO_REQUEST_TEMPLATES.get(lang_key, PHOTO_REQUEST_TEMPLATES["hi"])
        return photo_prompt, nav_action, None

    # 8. Domain Knowledge Mapping
    topic_map = {
        "irrigation": "irrigation",
        "crop_guidance": "fertilizer",
        "crop_disease": "crop_disease",
        "farm_management": "farm_management",
        "action_plan": "action_plan",
        "greeting": "greeting",
    }
    target_topic = topic_map.get(intent, intent)
    if target_topic not in LOCALIZED_KNOWLEDGE:
        target_topic = "crop_cultivation"
        
    topic_dict = LOCALIZED_KNOWLEDGE.get(target_topic, LOCALIZED_KNOWLEDGE.get("crop_cultivation", {}))
    template = topic_dict.get(lang_key, topic_dict.get("hi", topic_dict.get("en", "")))
    
    # Resolve localized crop name if crop entity is detected
    if detected_crop:
        crop_lower = detected_crop.lower()
        if crop_lower in CROP_LOCALIZED_NAMES:
            crop_str = CROP_LOCALIZED_NAMES[crop_lower].get(lang_key, detected_crop.capitalize())
        else:
            crop_str = detected_crop.capitalize()
    else:
        crop_str = ("फसल" if lang_key in ["hi", "mr"] else ("fasal" if lang_key == "hinglish" else ("ਫ਼ਸਲ" if lang_key == "pa" else "crop")))

    res_text = template.replace("{crop}", crop_str)
    res_text = res_text.replace("फसल की फसल", "फसल").replace("ਫ਼ਸਲ ਦੀ ਫ਼ਸਲ", "ਫ਼ਸਲ").replace("crop crop", "crop").replace("fasal ki fasal", "fasal")
    
    return res_text, nav_action, None


# ============================================================
# GEMINI GENERATIVE AGRICULTURAL REASONING (WITH FALLBACK)
# ============================================================

async def generate_agricultural_answer(
    question: str,
    language: str,
    topic: str,
    crop: Optional[str] = None,
    growth_stage: Optional[str] = None,
    state: Optional[str] = None,
    district: Optional[str] = None,
    farm_info: Optional[Dict[str, Any]] = None,
    prediction_info: Optional[Dict[str, Any]] = None,
    weather_info: Optional[Dict[str, Any]] = None,
    timing_info: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, str]]] = None,
    detail_level: Optional[str] = "simple",
    farmer_name: Optional[str] = None,
) -> str:
    """Generate concise or detailed, localized, human-like voice response."""
    api_key = get_gemini_api_key()
    lang_key = (language or "hi").strip().lower().split("-")[0]
    target_lang_name = SUPPORTED_LANGUAGES.get(lang_key, "Hindi")
    active_crop = crop or "crop"

    # Context compilation
    context_lines = []
    if crop:
        context_lines.append(f"Active Crop: {crop}")
    if growth_stage:
        context_lines.append(f"Growth Stage: {growth_stage}")
    if district and state:
        context_lines.append(f"Location: {district}, {state}")
    if farm_info:
        for k, v in farm_info.items():
            if v and k not in ["farmer_name", "name"]:
                context_lines.append(f"{k.replace('_', ' ').title()}: {v}")
    if weather_info:
        context_lines.append(f"Live Weather: {weather_info.get('temperature', '')}°C, {weather_info.get('weather_condition', '')}, Rain: {weather_info.get('rainfall', 0)}mm")
    if timing_info and timing_info.get("rain_risk"):
        context_lines.append(f"Weather Spray Timing Alert: Rain Risk {timing_info.get('rain_probability')}% on {timing_info.get('when')}. Delay spray until {timing_info.get('short_dry_day')}.")
    if prediction_info:
        context_lines.append(f"Disease: {prediction_info.get('disease', '')} ({prediction_info.get('confidence', '')}%)")
        if prediction_info.get("treatment"):
            context_lines.append(f"Verified Treatment: {prediction_info['treatment']}")

    history_str = ""
    if history:
        turns = []
        for turn in history[-4:]:
            role = turn.get("role", "farmer")
            txt = turn.get("text") or turn.get("message") or ""
            if txt:
                turns.append(f"{role.capitalize()}: {txt}")
        if turns:
            history_str = "CONVERSATION HISTORY:\n" + "\n".join(turns) + "\n\n"

    context_str = "\n".join(context_lines) if context_lines else "General agricultural context."

    if (detail_level or "").lower() == "detailed":
        length_constraint = (
            "2. LENGTH & DETAIL: The farmer prefers DETAILED explanations. "
            "Provide a comprehensive, thorough response (4 to 6 spoken sentences) with full agronomic reasoning, specific steps, and actionable guidance."
        )
    else:
        length_constraint = (
            "2. LENGTH & DETAIL: The farmer prefers SHORT/SIMPLE answers. "
            "Keep your response strictly to 1 to 2 short, simple spoken sentences maximum (under 25 words). Be direct, practical and concise."
        )

    greeting_instruction = ""
    if farmer_name and str(farmer_name).strip():
        fname = str(farmer_name).strip()
        greeting_instruction = f"The farmer's name is {fname}. Address them warmly and respectfully by name (e.g. '{fname} ji' or 'Hello {fname}').\n"

    if api_key:
        prompt = (
            f"You are the AgriBridge AI Agricultural Helpline Advisor speaking with an Indian farmer over a phone call.\n"
            f"Target Language: {target_lang_name} ({lang_key})\n"
            f"{greeting_instruction}\n"
            f"{history_str}"
            f"FARM & LIVE SENSOR CONTEXT:\n{context_str}\n\n"
            f"CURRENT FARMER QUESTION: {question}\n"
            f"TOPIC INTENT: {topic}\n\n"
            f"VOICE HELPLINE RULES:\n"
            f"1. Respond directly in {target_lang_name} (if Hinglish, use natural spoken Hindi in Latin script).\n"
            f"{length_constraint}\n"
            f"3. Speak with a warm, respectful, practical advisor tone (e.g. 'हाँ, समझ गया...', 'एक काम कीजिए...').\n"
            f"4. Do NOT hallucinate risky chemical volumes; recommend bio/organic options or official product label instructions.\n"
            f"5. Maintain multi-turn context (if the farmer asks 'isme paani?', know 'isme' refers to {active_crop}).\n"
            f"6. Do NOT output markdown symbols (#, **, bullets) or raw JSON."
        )

        try:
            api_url = (
                "https://generativelanguage.googleapis.com/"
                "v1beta/models/gemini-1.5-flash:generateContent"
                f"?key={api_key}"
            )
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(api_url, json=payload, headers={"Content-Type": "application/json"})
                resp.raise_for_status()
                data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    answer = parts[0].get("text", "").strip()
                    if answer:
                        return answer
        except Exception:
            pass

    # High-Quality Localized Fallback Knowledge Engine
    topic_key = topic if topic in LOCALIZED_KNOWLEDGE else "crop_cultivation"
    if topic in ["pest", "crop_disease"]:
        topic_key = "crop_disease"

    topic_dict = LOCALIZED_KNOWLEDGE.get(topic_key, LOCALIZED_KNOWLEDGE["crop_cultivation"])
    template = topic_dict.get(lang_key, topic_dict.get("hi", topic_dict["en"]))
    raw_answer = template.format(crop=active_crop)

    if (detail_level or "").lower() == "simple":
        sentences = [s.strip() for s in re.split(r'([.?!।])', raw_answer) if s.strip()]
        if len(sentences) >= 2:
            raw_answer = sentences[0] + sentences[1]

    if farmer_name and str(farmer_name).strip():
        fname = str(farmer_name).strip()
        if lang_key in ["hi", "hinglish"]:
            raw_answer = f"{fname} जी, {raw_answer}"
        elif lang_key == "pa":
            raw_answer = f"{fname} ਜੀ, {raw_answer}"
        else:
            raw_answer = f"Hello {fname}, {raw_answer}"

    return raw_answer


# ============================================================
# MASTER PROCESSOR ENTRY POINT
# ============================================================

async def process_voice_query(
    audio_bytes: Optional[bytes] = None,
    content_type: str = "audio/webm",
    text_query: Optional[str] = None,
    language: str = "hi",
    crop: Optional[str] = None,
    growth_stage: Optional[str] = None,
    state: Optional[str] = None,
    district: Optional[str] = None,
    farm_info: Optional[Dict[str, Any]] = None,
    prediction_info: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, str]]] = None,
    detail_level: Optional[str] = "simple",
    farmer_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Process farmer query through complete agricultural voice pipeline:
    STT -> Multi-turn Context Resolution -> Intent & Navigation Routing -> Tool Execution -> Spoken TTS.
    """
    default_lang = (language or "hi").strip().lower().split("-")[0]
    transcript = ""

    # Step 1: Speech-to-Text if voice audio provided
    if audio_bytes and len(audio_bytes) > 0:
        success, transcribed = await transcribe_audio(audio_bytes, content_type, default_lang)
        if success and transcribed:
            transcript = transcribed
        elif text_query:
            transcript = text_query
        else:
            return {
                "success": False,
                "language": default_lang,
                "error": "Could not recognize speech clearly. Please try speaking again or type your question below.",
            }
    elif text_query:
        transcript = text_query.strip()
    else:
        return {
            "success": False,
            "language": default_lang,
            "error": "No voice audio or text query provided.",
        }

    # Step 2: Intent, Entity & Navigation Classification
    intent_result = classify_intent(transcript, default_lang)
    active_lang = intent_result.get("language") or default_lang
    topic = intent_result.get("topic", "non_agriculture")
    is_agri = intent_result.get("is_agriculture_related", False)
    nav_action = intent_result.get("navigation_action")

    # Step 3: Multi-turn Context & Crop Resolution
    detected_crop, active_stage, _ = resolve_context_from_history(
        current_text=transcript,
        history=history,
        explicit_crop=intent_result.get("detected_crop") or crop,
        explicit_stage=growth_stage
    )
    if not detected_crop and farm_info:
        detected_crop = farm_info.get("crop") or farm_info.get("crop_type")

    # Step 4: Handle Navigation Triggers
    if nav_action:
        nav_confirmation = {
            "hi": f"बिल्कुल! मैं आपके लिए {nav_action['label']} खोल रहा हूँ।",
            "en": f"Sure! Opening the {nav_action['label']} page for you now.",
            "hinglish": f"Bilkul! Main aapke liye {nav_action['label']} open kar raha hoon.",
            "pa": f"ਬਿਲਕੁਲ! ਮੈਂ ਤੁਹਾਡੇ ਲਈ {nav_action['label']} ਖੋਲ੍ਹ ਰਿਹਾ ਹਾਂ।",
            "mr": f"नक्कीच! मी आपल्यासाठी {nav_action['label']} उघडत आहे.",
            "bn": f"নিশ্চয়ই! আমি আপনার জন্য {nav_action['label']} খুলছি।",
            "gu": f"ચોક્કસ! હું તમારા માટે {nav_action['label']} ખોલી રહ્યો છું.",
            "ta": f"நிச்சயமாக! உங்களுக்காக {nav_action['label']} பக்கத்தை திறக்கிறேன்.",
            "te": f"తప్పకుండా! మీ కోసం {nav_action['label']} పేజీని తెరుస్తున్నాను.",
            "kn": f"ಖಂಡಿತ! ನಿಮಗಾಗಿ {nav_action['label']} ಪುಟವನ್ನು ತೆರೆಯುತ್ತಿದ್ದೇನೆ.",
            "ml": f"തീർച്ചയായും! നിങ്ങൾക്കായി {nav_action['label']} പേജ് തുറക്കുന്നു.",
            "or": f"ନିଶ୍ଚୟ! ମୁଁ ଆପଣଙ୍କ ପାଇଁ {nav_action['label']} ଖୋଲୁଛି।",
            "as": f"নিশ্চয়! মই আপোনাৰ বাবে {nav_action['label']} খুলিছো।",
            "ur": f"بالکل! میں آپ کے لیے {nav_action['label']} کھول رہا ہوں۔"
        }
        resp_text = nav_confirmation.get(active_lang, nav_confirmation["hi"])
        audio_file = synthesize_speech(resp_text, active_lang)
        return {
            "success": True,
            "language": active_lang,
            "transcript": transcript,
            "is_agriculture_related": True,
            "topic": "navigation",
            "detected_crop": detected_crop,
            "navigation_action": nav_action,
            "response_text": resp_text,
            "response": resp_text,
            "message": resp_text,
            "audio_url": f"/api/voice/audio/{audio_file}" if audio_file else None,
        }

    # Step 5: Handle App Help & Platform Tour
    if topic == "app_help":
        resp_text = generate_app_help_response(active_lang)
        audio_file = synthesize_speech(resp_text, active_lang)
        return {
            "success": True,
            "language": active_lang,
            "transcript": transcript,
            "is_agriculture_related": True,
            "topic": "app_help",
            "detected_crop": detected_crop,
            "navigation_action": None,
            "response_text": resp_text,
            "response": resp_text,
            "message": resp_text,
            "audio_url": f"/api/voice/audio/{audio_file}" if audio_file else None,
        }

    # Step 6: Handle Non-Agricultural Inquiries (Polite Friendly Redirection)
    if not is_agri or topic == "non_agriculture":
        rejection_text = get_rejection_message(active_lang)
        audio_file = synthesize_speech(rejection_text, active_lang)
        return {
            "success": True,
            "language": active_lang,
            "transcript": transcript,
            "is_agriculture_related": False,
            "topic": "non_agriculture",
            "detected_crop": detected_crop,
            "navigation_action": None,
            "response_text": rejection_text,
            "response": rejection_text,
            "message": rejection_text,
            "audio_url": f"/api/voice/audio/{audio_file}" if audio_file else None,
        }

    # Step 7: Tool Execution

    # 7A. Mandi & Market Price Tool
    if topic == "market":
        resp_text = generate_market_response(detected_crop, active_lang)
        audio_file = synthesize_speech(resp_text, active_lang)
        return {
            "success": True,
            "language": active_lang,
            "transcript": transcript,
            "is_agriculture_related": True,
            "topic": "market",
            "detected_crop": detected_crop,
            "navigation_action": {"action": "navigate", "route": "marketplace", "target": "/frontend/pages/crop-listings.html", "label": "Marketplace"},
            "response_text": resp_text,
            "response": resp_text,
            "message": resp_text,
            "audio_url": f"/api/voice/audio/{audio_file}" if audio_file else None,
        }

    # 7B. Weather & Timing Advice Tool
    weather_data = None
    timing_data = None
    farmer_district = district or (farm_info.get("district") if farm_info else None) or "Ludhiana"
    farmer_state = state or (farm_info.get("state") if farm_info else None) or "Punjab"

    if topic in ["weather", "irrigation"] or "baarish" in transcript.lower() or "rain" in transcript.lower():
        dist_info = find_district(farmer_state, farmer_district)
        if dist_info:
            try:
                cw = await get_current_weather(dist_info["latitude"], dist_info["longitude"])
                timing_data = await calculate_timing_advice(
                    region_str=f"{farmer_district}, {farmer_state}",
                    crop_name=detected_crop or "Crop"
                )
                weather_data = cw
            except Exception:
                pass

    if topic == "weather" and weather_data:
        resp_text = generate_weather_voice_response(weather_data, timing_data, detected_crop, active_lang)
        audio_file = synthesize_speech(resp_text, active_lang)
        return {
            "success": True,
            "language": active_lang,
            "transcript": transcript,
            "is_agriculture_related": True,
            "topic": "weather",
            "detected_crop": detected_crop,
            "weather_data": weather_data,
            "timing_data": timing_data,
            "navigation_action": {"action": "navigate", "route": "weather", "target": "/frontend/pages/weather-dashboard.html", "label": "Live Weather"},
            "response_text": resp_text,
            "response": resp_text,
            "message": resp_text,
            "audio_url": f"/api/voice/audio/{audio_file}" if audio_file else None,
        }

    # 7C. Disease & Recommendation DB Integration
    rec_info = prediction_info or {}
    if topic == "crop_disease" and prediction_info and "model" in prediction_info and "class_id" in prediction_info:
        db = _load_recommendation_database()
        key = f"{prediction_info['model']}_{prediction_info['class_id']}"
        rec_data = db.get(key)
        if rec_data:
            rec_info["disease"] = rec_data.get("disease", rec_info.get("disease", ""))
            rec_info["treatment"] = rec_data.get("treatment", "")

    # Step 8: Generate Localized Agricultural Response
    response_text = await generate_agricultural_answer(
        question=transcript,
        language=active_lang,
        topic=topic,
        crop=detected_crop,
        growth_stage=active_stage,
        state=farmer_state,
        district=farmer_district,
        farm_info=farm_info,
        prediction_info=rec_info,
        weather_info=weather_data,
        timing_info=timing_data,
        history=history,
        detail_level=detail_level,
        farmer_name=farmer_name,
    )

    # Step 9: Synthesize Speech with Resilience Status
    audio_filename, audio_status = synthesize_speech_with_status(response_text, active_lang)

    return {
        "success": True,
        "language": active_lang,
        "transcript": transcript,
        "is_agriculture_related": True,
        "topic": topic,
        "detected_crop": detected_crop,
        "navigation_action": None,
        "response_text": response_text,
        "response": response_text,
        "message": response_text,
        "audio_url": f"/api/voice/audio/{audio_filename}" if audio_filename else None,
        "audio_status": audio_status,
    }
