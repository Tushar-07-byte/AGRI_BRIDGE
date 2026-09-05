"""
AgriBridge Master Agriculture Intent, Topic & Navigation Classifier

Classifies farmer utterances into rich agricultural intents, navigation actions,
crop entities, and detects language switching across 14 Indian languages + Hinglish.
"""

import os
import re
from typing import Any, Dict, List, Optional, Tuple

# ============================================================
# SUPPORTED LANGUAGES & CODE NORMALIZATION
# ============================================================

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

# ============================================================
# POLITE REJECTION / REDIRECTION MESSAGES (14 LANGUAGES)
# ============================================================

REJECTION_MESSAGES = {
    "en": "I am your AgriBridge farming advisor. I can help you with crop health, weather, fertilizers, irrigation, mandi prices, and using AgriBridge. How can I help with your farm today?",
    "hi": "मैं आपका एग्रीब्रिज कृषि सलाहकार हूँ। मैं फसल, मौसम, खाद, सिंचाई, मंडी भाव और ऐप के उपयोग में आपकी मदद कर सकता हूँ। आज अपनी खेती के बारे में पूछिए!",
    "hinglish": "Main aapka AgriBridge farming advisor hoon. Main crops, weather, fertilizer, irrigation aur mandi bhav mein help kar sakta hoon. Aaj farming ke baare mein kya poochna chahte hain?",
    "pa": "ਮੈਂ ਤੁਹਾਡਾ ਐਗਰੀਬ੍ਰਿਜ ਖੇਤੀ ਸਲਾਹਕਾਰ ਹਾਂ। ਮੈਂ ਫ਼ਸਲ, ਮੌਸਮ, ਖਾਦ, ਸਿੰਚਾਈ ਅਤੇ ਮੰਡੀ ਦੇ ਭਾਅ ਬਾਰੇ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ। ਅੱਜ ਖੇਤੀ ਬਾਰੇ ਕੀ ਪੁੱਛਣਾ ਚਾਹੁੰਦੇ ਹੋ?",
    "mr": "मी आपला अ‍ॅग्रीब्रिज कृषी सल्लागार आहे. मी पिके, हवामान, खते, सिंचन आणि बाजारभावाबाबत मदत करू शकतो. आज आपल्या शेतीबद्दल काय विचारू इच्छिता?",
    "bn": "আমি আপনার এগ্রিব্রিজ কৃষি উপদেষ্টা। আমি ফসল, আবহাওয়া, সার, সেচ এবং বাজার দর সম্পর্কে সাহায্য করতে পারি। আজ কৃষিকাজ সম্পর্কে কী জানতে চান?",
    "gu": "હું તમારો એગ્રીબ્રિજ કૃષિ સલાહકાર છું. હું પાક, હવામાન, ખાતર, સિંચાઈ અને બજાર ભાવ બાબતે મદદ કરી શકું છું. આજે ખેતી વિશે શું પૂછવું છે?",
    "ta": "நான் உங்கள் அக்ரிபிரிட்ஜ் வேளாண் ஆலோசகர். பயிர்கள், வானிலை, உரங்கள், பாசனம் மற்றும் சந்தை விலைகள் பற்றி உதவ முடியும். இன்று விவசாயம் பற்றி என்ன கேட்க விரும்புகிறீர்கள்?",
    "te": "నేను మీ అగ్రిబ్రిడ్జ్ వ్యవసాయ సలహాదారుని. పంటలు, వాతావరణం, ఎరువులు, సాగునీరు మరియు మార్కెట్ ధరలపై సహాయం చేయగలను. ఈరోజు మీ వ్యవసాయం గురించి ఏమి తెలుసుకోవాలనుకుంటున్నారు?",
    "kn": "ನಾನು ನಿಮ್ಮ ಅಗ್ರಿಬ್ರಿಡ್ಜ್ ಕೃಷಿ ಸಲಹೆಗಾರ. ಬೆಳೆ, ಹವಾಮಾನ, ಗೊಬ್ಬರ, ನೀರಾವರಿ ಮತ್ತು ಮಾರುಕಟ್ಟೆ ದರಗಳ ಬಗ್ಗೆ ಸಹಾಯ ಮಾಡಬಲ್ಲೆ. ಇಂದು ಕೃಷಿಯ ಬಗ್ಗೆ ಏನು ತಿಳಿಯಲು ಬಯಸುತ್ತೀರಿ?",
    "ml": "ഞാൻ നിങ്ങളുടെ അഗ്രിബ്രിഡ്ജ് കാർഷിക ഉപദേശകനാണ്. വിളകൾ, കാലാവസ്ഥ, വളം, നനയ്ക്കൽ, വിപണി വിലകൾ എന്നിവയിൽ സഹായിക്കാനാകും. ഇന്ന് കൃഷിയെക്കുറിച്ച് എന്ത് സംശയമാണ് ഉള്ളത്?",
    "or": "ମୁଁ ଆପଣଙ୍କ ଏଗ୍ରିବ୍ରିଜ୍ କୃଷି ପରାମର୍ଶଦାତା। ମୁଁ ଫସଲ, ପାଣିପାଗ, ଖତ, ଜଳସେଚନ ଏବଂ ମଣ୍ଡି ଦର ବିଷୟରେ ସାହାଯ୍ୟ କରିପାରିବି। ଆଜି ଚାଷ ବିଷୟରେ କ'ଣ ଜାଣିବାକୁ ଚାହାଁନ୍ତି?",
    "as": "মই আপোনাৰ এগ্ৰিব্ৰিজ কৃষি উপদেষ্টা। মই শস্য, বতৰ, সাৰ, জলসিঞ্চন আৰু বজাৰ দৰ সম্পৰ্কে সহায় কৰিব পাৰোঁ। আজি কৃষি সম্পৰ্কে কি জানিব বিচাৰে?",
    "ur": "میں آپ کا ایگری برج زرعی مشیر ہوں۔ میں فصل، موسم، کھاد، آبپاشی اور منڈی کے بھاؤ میں مدد کر سکتا ہوں۔ آج اپنی کھیتی کے بارے میں پوچھیے!",
}

def get_rejection_message(language: str) -> str:
    """Return polite friendly redirection in the specified language."""
    lang_key = (language or "hi").strip().lower().split("-")[0]
    return REJECTION_MESSAGES.get(lang_key, REJECTION_MESSAGES["hi"])


# ============================================================
# EXPLICIT NON-AGRICULTURE PATTERNS (FILTER OUT TRIVIA/JOKES/CODE)
# ============================================================

NON_AGRI_PATTERNS = [
    r"\b(joke|jokes|funny|riddle|comedy|laugh)\b",
    r"\b(chutkula|chutkule|haso|majak)\b",
    r"\b(who is (the )?(prime minister|president|king|queen|actor|actress|celebrity))\b",
    r"\b(capital of|largest city|who won|world cup|cricket score|football score)\b",
    r"\b(write (a )?(resume|cv|cover letter|essay|poem|song|story|code|python|java|javascript|html))\b",
    r"\b(income tax|gst return|crypto|bitcoin|stock market|share price|invest in shares)\b",
    r"\b(movie|cinema|netflix|song|singer|bollywood|hollywood)\b",
    r"\b(translate this sentence|write an email|solve this math|algebra|calculus)\b",
    r"(चुटकुला|मजाक|जोक|हंसो)",
    r"(ହସକଥା|ମଜାକ|ଗପ)",
    r"(विनोद|जोक|गाणे|चित्रपट)",
    r"(কৌতুক|মজার কথা|গান|সিনেমা)",
    r"(జోక్|హాస్యం|సినిమా|పాట)",
    r"(ஜோக்|நகைச்சுவை|பாடல்|திரைப்படம்)",
    r"(ಜೋಕ್|ಹಾಸ್ಯ|ಹಾಡು|ಸಿನಿಮಾ)",
    r"(തമാശ|പാട്ട്|സിനിമ)",
    r"(જોક્સ|મજાક|ગીત|સિનેમા)",
    r"(ਚੁਟਕਲਾ|ਮਜ਼ਾਕ|ਗਾਣਾ|ਫਿਲਮ)",
]

# ============================================================
# LANGUAGE SWITCHING DETECTOR
# ============================================================

LANGUAGE_SWITCH_PATTERNS = [
    (r"\b(hindi|hindi mein|hindi me|हिंदी|हिन्दी)\b", "hi"),
    (r"\b(english|in english|अंग्रेजी|अंग्रेज़ी)\b", "en"),
    (r"\b(hinglish|hinglish me|hinglish mein)\b", "hinglish"),
    (r"\b(punjabi|punjabi vich|ਪੰਜਾਬੀ|पंजाबी)\b", "pa"),
    (r"\b(marathi|marathi madhe|मराठी)\b", "mr"),
    (r"\b(bengali|bangla|বাংলা|बंगाली)\b", "bn"),
    (r"\b(gujarati|gujarati ma|ગુજરાતી|गुजराती)\b", "gu"),
    (r"\b(tamil|tamilil|தமிழ்|तमिल)\b", "ta"),
    (r"\b(telugu|telugulo|తెలుగు|तेलुगु)\b", "te"),
    (r"\b(kannada|kannadadalli|ಕನ್ನಡ|कन्नड़)\b", "kn"),
    (r"\b(malayalam|malayalathil|മലയാളം|मलयालम)\b", "ml"),
    (r"\b(odia|oriya|ଓଡ଼ିଆ|ओड़िया)\b", "or"),
    (r"\b(assamese|axomiya|অসমীয়া|असमिया)\b", "as"),
    (r"\b(urdu|urdu mein|اردو|उर्दू)\b", "ur"),
]

def detect_language_switch(text: str) -> Optional[str]:
    """Detect if the user is explicitly requesting a language change."""
    if not text:
        return None
    lower = text.lower()
    switch_triggers = [
        "me batao", "mein batao", "me bolo", "mein bolo", "me samjhao",
        "in ", "switch to ", "change language to ", "speak in ", "talk in ",
        "ਵਿੱਚ ਦੱਸੋ", "मध्ये सांगा", "তে বলুন", "માં કહો", "இல் சொல்லுங்கள்",
        "లో చెప్పండి", "ದಲ್ಲಿ ಹೇಳಿ", "ൽ പറയൂ", "ରେ କୁହନ୍ତୁ", "ত কওক", "میں بتائیں"
    ]
    is_switch_request = any(trig in lower for trig in switch_triggers) or lower.startswith("hindi") or lower.startswith("english") or lower.startswith("punjabi")
    if is_switch_request:
        for pattern, lang_code in LANGUAGE_SWITCH_PATTERNS:
            if re.search(pattern, lower):
                return lang_code
    return None


# ============================================================
# CROP ENTITY EXTRACTION & NORMALIZATION
# ============================================================

CROP_ALIASES = {
    "wheat": [
        "wheat", "gehu", "gehun", "gehoon", "kanak", "gehoon",
        "गेहूं", "गेहूँ", "गहू", "গম", "గోధుమ", "கோதுமை", "ಗೋಧಿ", "ഗോതമ്പ്", "ઘઉં", "ਕਣਕ", "گندم"
    ],
    "rice": [
        "rice", "paddy", "dhan", "dhaan", "chawal", "chaval", "jhona",
        "धान", "चावल", "तांदूळ", "ধান", "వరి", "நெல்", "ಭತ್ತ", "നെല്ല്", "ડાંગર", "ਝੋਨਾ", "چاول"
    ],
    "maize": [
        "maize", "corn", "makka", "makki", "bhutta",
        "मक्का", "मकई", "মাকৈ", "మొక్కజొన్న", "மக்காச்சோளம்", "ಮೆಕ್ಕೆಜೋಳ", "മക്കച്ചോളം", "મકાઈ", "ਮੱਕੀ", "مکئی"
    ],
    "tomato": [
        "tomato", "tamatar",
        "टमाटर", "टोमॅटो", "টমেটো", "టమోటా", "தக்காளி", "ಟೊಮೆಟೊ", "തക്കാളി", "ટામેટા", "ਟਮਾਟਰ", "ٹماٹر"
    ],
    "potato": [
        "potato", "aalu", "aloo", "alu", "batata",
        "आलू", "बटाटा", "আলু", "బంగాళాదుంప", "உருளைக்கிழங்கு", "ಆಲೂಗಡ್ಡೆ", "ഉരുളക്കിഴങ്ങ്", "બટાકા", "ਆਲੂ", "آلو"
    ],
    "cotton": [
        "cotton", "kapas", "kapaas", "narma",
        "कपास", "कापूस", "তুলা", "పత్తి", "பருத்தி", "ಹತ್ತಿ", "കપાસ", "ਨਰਮা", "کپاس"
    ],
    "onion": [
        "onion", "pyaj", "pyaaz", "pyaz", "kanda",
        "प्याज", "कांदा", "পেঁয়াজ", "ఉల్లిపాయ", "வெங்காயம்", "ಈರುಳ್ಳಿ", "സവാള", "ડુંગળી", "ਪਿਆਜ਼", "پیاز"
    ],
    "chilli": [
        "chilli", "chili", "mirch", "mirchi",
        "मिर्च", "मिरची", "লঙ্কা", "మిరపకాయ", "மிளகாய்", "ಮೆಣಸಿನಕಾಯಿ", "പച്ചമുളക്", "મરચાં", "ਮਿਰਚ", "مرچ"
    ],
    "sugarcane": [
        "sugarcane", "ganna", "oos",
        "गन्ना", "ऊस", "আঁখ", "చెరకు", "கரும்பு", "ಕಬ್ಬು", "കരിമ്പ്", "શેરડી", "ਗੰਨਾ", "گنا"
    ],
    "mustard": [
        "mustard", "sarson", "rai", "toria",
        "सरसों", "রাই", "ఆవాలు", "கடுகு", "ಸಾಸಿವೆ", "കടുക്", "રાય", "ਸਰ੍ਹੋਂ", "سرسوں"
    ],
    "soybean": [
        "soybean", "soya", "soyabean",
        "सोयाबीन", "সোয়াবিন", "సోయాబీన్", "ಸೋಯಾಬೀನ್", "سویا بین"
    ],
    "gram": [
        "gram", "chana", "chane", "chickpea",
        "चना", "हरभरा", "ছোলা", "శనగలు", "கொண்டைக்கடலை", "ಕಡಲೆ", "കടല", "ચણા", "ਛੋਲੇ", "چنا"
    ],
    "apple": [
        "apple", "seb",
        "सेब", "सफरचंद", "আপেল", "ఆపిల్", "ஆப்பிள்", "ಆಪಲ್", "ആപ്പിൾ", "સફરજન", "ਸੇਬ", "سیب"
    ],
    "grape": [
        "grape", "grapes", "angur", "angoor",
        "अंगूर", "द्राक्षे", "আঙুর", "ద్రాక్ష", "திராட்சை", "ದ್ರಾಕ್ಷಿ", "മുന്തിരി", "દ્રાક્ષ", "ਅੰਗੂਰ", "انگور"
    ]
}

def normalize_crop_name(name: Optional[str]) -> Optional[str]:
    """Normalize any crop name string into lowercase canonical identifier."""
    if not name or not str(name).strip():
        return None
    clean = str(name).strip().lower()
    for standard_crop, aliases in CROP_ALIASES.items():
        if clean == standard_crop:
            return standard_crop
        for alias in aliases:
            if clean == alias.lower() or alias.lower() in clean:
                return standard_crop
    return clean

def extract_crop_entity(text: str) -> Optional[str]:
    """Extract canonical crop name (e.g. 'wheat', 'rice') from natural utterance."""
    if not text:
        return None
    lower = text.lower()
    for standard_crop, aliases in CROP_ALIASES.items():
        for alias in aliases:
            if alias.isascii():
                if re.search(rf"\b{re.escape(alias)}\b", lower, re.IGNORECASE):
                    return standard_crop
            else:
                if alias in lower:
                    return standard_crop
    return None


# ============================================================
# CROP AGE / NUMBER / SOIL / IRRIGATION / SEASON EXTRACTION
# ============================================================

NUMBER_WORDS = {
    # Hindi Devanagari
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "छह": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10,
    "ग्यारह": 11, "बारह": 12, "तेरह": 13, "चौदह": 14, "पंद्रह": 15, "सोलह": 16, "सत्रह": 17, "अठारह": 18, "उन्नीस": 19,
    "बीस": 20, "इक्कीस": 21, "बाईस": 22, "तेईस": 23, "चौबीस": 24, "पच्चीस": 25, "छब्बीस": 26, "सत्ताईस": 27, "अट्ठाईस": 28, "उनतीस": 29,
    "तीस": 30, "इकतीस": 31, "बत्तीस": 32, "तैंतीस": 33, "चौंतीस": 34, "पैंतीस": 35, "छत्तीस": 36, "सैंतीस": 37, "अड़तीस": 38, "उनतालीस": 39,
    "चालीस": 40, "पैंतालीस": 45, "पचास": 50, "पचपन": 55, "साठ": 60, "पैंसठ": 65, "सत्तर": 70, "पचहत्तर": 75, "अस्सी": 80, "नब्बे": 90, "सौ": 100,
    # Hinglish / Romanized Hindi
    "ek": 1, "do": 2, "teen": 3, "char": 4, "paanch": 5, "panch": 5, "chhah": 6, "che": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10,
    "gyarah": 11, "barah": 12, "terah": 13, "chaudah": 14, "pandrah": 15, "solah": 16, "satrah": 17, "atharah": 18, "unnees": 19,
    "bees": 20, "ikkees": 21, "baees": 22, "teyees": 23, "chaubees": 24, "pachis": 25, "pachees": 25, "chhabees": 26, "sattaees": 27, "atthaees": 28, "untees": 29,
    "tees": 30, "paintis": 35, "paintees": 35, "chalis": 40, "chalees": 40, "paintalis": 45, "pachas": 50, "pachaas": 50, "saath": 60, "sattar": 70, "assi": 80, "nabbe": 90, "sau": 100,
    # English
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "twenty-one": 21, "twenty one": 21, "twenty-two": 22, "twenty two": 22, "twenty-three": 23, "twenty three": 23,
    "twenty-four": 24, "twenty four": 24, "twenty-five": 25, "twenty five": 25, "twenty-six": 26, "twenty six": 26,
    "twenty-seven": 27, "twenty seven": 27, "twenty-eight": 28, "twenty eight": 28, "twenty-nine": 29, "twenty nine": 29,
    "thirty": 30, "thirty-five": 35, "thirty five": 35, "forty": 40, "forty-five": 45, "forty five": 45, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100,
}

def extract_crop_age(text: str) -> Optional[int]:
    """
    Extract crop age in days from natural utterance.
    Supports days, weeks (*7), and months (*30).
    """
    if not text:
        return None
    clean = text.strip().lower()

    # 1. Check for Months
    month_match = re.search(r"(\d+(?:\.\d+)?)\s*(mahina|mahine|months?|महीने|महीना)", clean)
    if month_match:
        try:
            return int(float(month_match.group(1)) * 30)
        except Exception:
            pass
    if any(m in clean for m in ["dedh mahina", "dedh mahine", "डेढ़ महीना", "डेढ़ महीने", "1.5 months", "1.5 month"]):
        return 45
    if any(m in clean for m in ["ek mahina", "ek mahine", "one month", "एक महीना", "एक महीने"]):
        return 30
    if any(m in clean for m in ["do mahine", "two months", "दो महीने"]):
        return 60
    if any(m in clean for m in ["teen mahine", "three months", "तीन महीने"]):
        return 90

    # 2. Check for Weeks
    week_match = re.search(r"(\d+)\s*(hafte|hafta|weeks?|हफ्ते|हफ्ता|सप्ताह)", clean)
    if week_match:
        try:
            return int(week_match.group(1)) * 7
        except Exception:
            pass
    if any(w in clean for m_word, num in NUMBER_WORDS.items() for w in [f"{m_word} hafte", f"{m_word} weeks", f"{m_word} हफ्ते", f"{m_word} सप्ताह"]):
        for m_word, num in NUMBER_WORDS.items():
            if any(k in clean for k in [f"{m_word} hafte", f"{m_word} weeks", f"{m_word} हफ्ते", f"{m_word} सप्ताह"]):
                return num * 7
    if any(w in clean for w in ["teen hafte", "three weeks", "तीन हफ्ते", "तीन सप्ताह"]):
        return 21
    if any(w in clean for w in ["ek hafta", "one week", "एक हफ्ता", "एक सप्ताह"]):
        return 7
    if any(w in clean for w in ["do hafte", "two weeks", "दो हफ्ते", "दो सप्ताह"]):
        return 14
    if any(w in clean for w in ["char hafte", "four weeks", "चार हफ्ते", "चार सप्ताह"]):
        return 28

    # 3. Check for Digits with explicit Days / Din
    digit_match = re.search(r"\b(\d{1,3})\s*(?:दिन|din|days?|दिनों|dino|day|दिन की|din ki)\b", clean)
    if digit_match:
        try:
            val = int(digit_match.group(1))
            if 1 <= val <= 365:
                return val
        except Exception:
            pass

    # If utterance is essentially just a number (e.g., "25", "25.", "25 ki hai", "it is 25")
    only_digit = re.search(r"\b(\d{1,3})\s*(?:ki hai|hai|old|\.|\!)?$", clean)
    if only_digit:
        try:
            val = int(only_digit.group(1))
            if 1 <= val <= 365:
                return val
        except Exception:
            pass

    # 4. Check for Number words with Days / Din or as standalone value
    for word, num in NUMBER_WORDS.items():
        if re.search(rf"\b{re.escape(word)}\s+(?:दिन|din|days?|दिनों|dino|day|दिन की|din ki)\b", clean):
            return num
        if re.match(rf"^(?:it is\s+|crop is\s+|abhi\s+|fasal\s+)?{re.escape(word)}(?:\s+(?:ki hai|hai|old|\.|\!))?$", clean):
            return num

    return None

def extract_soil_type(text: str) -> Optional[str]:
    """Extract soil type entity from text."""
    if not text:
        return None
    lower = text.lower()
    if any(w in lower for w in ["sandy", "balui", "balu", "रेतीली", "बलुई", "रेती"]):
        return "sandy"
    if any(w in lower for w in ["clay", "chikni", "चिकनी"]):
        return "clay"
    if any(w in lower for w in ["loam", "loamy", "domat", "दोमट"]):
        return "loam"
    if any(w in lower for w in ["black soil", "kali mitti", "काली मिट्टी", "काळी माती"]):
        return "black"
    if any(w in lower for w in ["red soil", "lal mitti", "लाल मिट्टी"]):
        return "red"
    return None

def extract_irrigation_method(text: str) -> Optional[str]:
    """Extract irrigation method from text."""
    if not text:
        return None
    lower = text.lower()
    if any(w in lower for w in ["drip", "ड्रिप", "टपक"]):
        return "drip"
    if any(w in lower for w in ["sprinkler", "fuhara", "फुहारा", "स्प्रिंकलर"]):
        return "sprinkler"
    if any(w in lower for w in ["flood", "khula pani", "कैरियां", "खुला पानी"]):
        return "flood"
    return None

def extract_season(text: str) -> Optional[str]:
    """Extract cropping season from text."""
    if not text:
        return None
    lower = text.lower()
    if any(w in lower for w in ["rabi", "रबी", "sardi", "winter"]):
        return "rabi"
    if any(w in lower for w in ["kharif", "खरीफ", "monsoon", "barsat"]):
        return "kharif"
    if any(w in lower for w in ["zaid", "जायद", "summer", "garmi"]):
        return "zaid"
    return None


def extract_location_entity(text: str) -> Optional[str]:
    """
    Extract location / district / city entity from natural utterance.
    Supports Hindi, English, Hinglish expressions (e.g. 'बेंगलुरु के पास', 'Ludhiana', 'near Pune', 'Guntur mein').
    """
    if not text:
        return None
    clean = text.strip()
    lower = clean.lower()

    # Direct city/state aliases
    city_map = {
        "bengaluru": "Bengaluru",
        "bangalore": "Bengaluru",
        "बेंगलुरु": "Bengaluru",
        "बैंगलोर": "Bengaluru",
        "ಬೆಂಗಳೂರು": "Bengaluru",
        "ludhiana": "Ludhiana",
        "लुधियाना": "Ludhiana",
        "ਲੁਧਿਆਣਾ": "Ludhiana",
        "pune": "Pune",
        "पुणे": "Pune",
        "guntur": "Guntur",
        "गुंटूर": "Guntur",
        "గుంటూరు": "Guntur",
        "nashik": "Nashik",
        "नासिक": "Nashik",
        "नाशिक": "Nashik",
        "nagpur": "Nagpur",
        "नागपुर": "Nagpur",
        "indore": "Indore",
        "इंदौर": "Indore",
        "bhopal": "Bhopal",
        "भोपाल": "Bhopal",
        "jaipur": "Jaipur",
        "जयपुर": "Jaipur",
        "delhi": "Delhi",
        "दिल्ली": "Delhi",
        "amritsar": "Amritsar",
        "अमृतसर": "Amritsar",
        "ਅੰਮ੍ਰਿਤਸਰ": "Amritsar",
        "patna": "Patna",
        "पटना": "Patna",
        "lucknow": "Lucknow",
        "लखनऊ": "Lucknow",
        "kanpur": "Kanpur",
        "कानपुर": "Kanpur",
        "varanasi": "Varanasi",
        "वाराणसी": "Varanasi",
        "surat": "Surat",
        "सूरत": "Surat",
        "ahmedabad": "Ahmedabad",
        "अहमदाबाद": "Ahmedabad",
        "rajkot": "Rajkot",
        "राजकोट": "Rajkot",
        "hyderabad": "Hyderabad",
        "हैदराबाद": "Hyderabad",
        "chennai": "Chennai",
        "चेन्नई": "Chennai",
        "coimbatore": "Coimbatore",
        "कोयंबटूर": "Coimbatore",
        "madurai": "Madurai",
        "மதுரை": "Madurai",
        "kolkata": "Kolkata",
        "कोलकाता": "Kolkata",
        "chandigarh": "Chandigarh",
        "चंडीगढ़": "Chandigarh",
        "punjab": "Punjab",
        "पंजाब": "Punjab",
        "haryana": "Haryana",
        "हरियाणा": "Haryana",
        "karnataka": "Karnataka",
        "कर्नाटक": "Karnataka",
        "maharashtra": "Maharashtra",
        "महाराष्ट्र": "Maharashtra",
        "gujarat": "Gujarat",
        "गुजरात": "Gujarat",
        "rajasthan": "Rajasthan",
        "राजस्थान": "Rajasthan",
        "uttar pradesh": "Uttar Pradesh",
        "उत्तर प्रदेश": "Uttar Pradesh",
        "madhya pradesh": "Madhya Pradesh",
        "मध्य प्रदेश": "Madhya Pradesh",
        "bihar": "Bihar",
        "बिहार": "Bihar",
        "andhra pradesh": "Andhra Pradesh",
        "आंध्र प्रदेश": "Andhra Pradesh",
        "tamil nadu": "Tamil Nadu",
        "तमिलनाडु": "Tamil Nadu",
        "telangana": "Telangana",
        "तेलंगाना": "Telangana",
        "kerala": "Kerala",
        "केरल": "Kerala",
        "west bengal": "West Bengal",
        "पश्चिम बंगाल": "West Bengal",
        "odisha": "Odisha",
        "ओडिशा": "Odisha",
        "mysore": "Mysore",
        "mysuru": "Mysore",
        "मैसूर": "Mysore",
        "ಮೈಸೂರು": "Mysore",
        "karnal": "Karnal",
        "करनाल": "Karnal",
        "rohtak": "Rohtak",
        "रोहतक": "Rohtak",
        "meerut": "Meerut",
        "मेरठ": "Meerut",
        "latur": "Latur",
        "लातूर": "Latur",
        "solapur": "Solapur",
        "सोलापुर": "Solapur",
        "patiala": "Patiala",
        "पटियाला": "Patiala",
        "bathinda": "Bathinda",
        "बठिंडा": "Bathinda",
        "hisar": "Hisar",
        "हिसार": "Hisar",
        "aligarh": "Aligarh",
        "अलीगढ़": "Aligarh",
        "agra": "Agra",
        "आगरा": "Agra",
        "gorakhpur": "Gorakhpur",
        "गोरखपुर": "Gorakhpur",
        "bareilly": "Bareilly",
        "बरेली": "Bareilly",
        "kolhapur": "Kolhapur",
        "कोल्हापुर": "Kolhapur",
        "sangli": "Sangli",
        "सांगली": "Sangli",
        "satara": "Satara",
        "सातारा": "Satara",
        "belagavi": "Belagavi",
        "belgaum": "Belagavi",
        "बेलगाम": "Belagavi",
        "dharwad": "Dharwad",
        "धारवाड़": "Dharwad",
        "hubli": "Hubballi",
        "hubballi": "Hubballi",
        "vijayawada": "Vijayawada",
        "विजयवाड़ा": "Vijayawada",
        "warangal": "Warangal",
        "वारंगल": "Warangal",
        "tirupati": "Tirupati",
        "तिरुपति": "Tirupati",
    }

    for k, v in city_map.items():
        if k in lower or k in clean:
            return v

    try:
        from app.data.india_districts import INDIA_DISTRICTS
        for state, districts in INDIA_DISTRICTS.items():
            if state.lower() in lower:
                return state
            for d in districts:
                d_name = d["name"]
                if re.search(r"\b" + re.escape(d_name.lower()) + r"\b", lower):
                    return d_name
    except ImportError:
        pass

    non_loc_words = {
        "paani", "pani", "khet", "fasal", "wheat", "gehu", "rice", "dhan", "chawal", "makka", "corn",
        "din", "days", "sukhi", "sukha", "nami", "geeli", "moist", "dry", "wet", "namaste", "hello", "hi",
        "kisan", "saathi", "batao", "bataiye", "kab", "kya", "kaise", "kare", "de", "dena", "hai", "nahi",
        "ha", "haan", "yes", "no", "fertilizer", "khad", "dawa", "rog", "keet", "sinchai",
        "today", "tomorrow", "yesterday", "now", "rain", "raining", "rainy", "barish", "baarish", "mausam", "weather",
        "aaj", "kal", "parso", "subah", "shaam", "dophar", "field", "farm", "crop", "water",
        "खेत", "फसल", "पानी", "गेहूं", "धान", "चावल", "मक्का", "आलू", "टमाटर", "दिन", "दिनों",
        "नमी", "सूखी", "गीली", "नमस्ते", "किसान", "साथी", "सिंचाई", "खाद", "यूरिया", "रोग", "कीड़ा",
        "है", "हैं", "नहीं", "हाँ", "बताओ", "कब", "क्या", "कैसे", "डालूं", "देना", "आज", "कल", "बारिश", "मौसम"
    }

    # Explicit preposition patterns: "near Karnal", "in Ludhiana", "बेंगलुरु के पास", "करनाल में", "जिला मेरठ"
    prep_patterns = [
        r"\b(?:near|in|at|around|from|district|dist|city)\s+([a-zA-Z\u0900-\u097F]+)",
        r"\b(?:जिला|शहर|डिस्ट्रिक्ट)\s+([a-zA-Z\u0900-\u097F]+)",
        r"([a-zA-Z\u0900-\u097F]+)\s+(?:ke paas|ke pass|district|dist|city|के पास)\b",
        r"([a-zA-Z\u0900-\u097F]+)\s+(?:mein|me|में|से)\b",
    ]

    for pattern in prep_patterns:
        m = re.search(pattern, lower)
        if m:
            cand = m.group(1).strip()
            if len(cand) >= 3 and cand.lower() not in non_loc_words:
                return cand.title()

    return None


def extract_soil_moisture(text: str) -> Optional[str]:
    """
    Extract soil moisture status from user utterance.
    Values:
      - 'slightly_dry': थोड़ी सूखी, thodi sukhi, slightly dry, halki sukhi, etc.
      - 'dry': सूखी, sukhi, sukha, dry, etc.
      - 'moist': नमी है, nami, moist, moisture, etc.
      - 'wet': गीली, geeli, wet, jal-bhav, etc.
    """
    if not text:
        return None
    lower = text.strip().lower()

    if any(w in lower for w in ["thodi sukhi", "thodi sukhi hai", "थोड़ी सूखी", "थोड़ी सूखी है", "slightly dry", "halki sukhi", "kam nami", "some dryness"]):
        return "slightly_dry"
    if any(w in lower for w in ["sukhi", "sukhi hai", "सूखी", "सूखी है", "sukha", "dry", "completely dry", "bilkul sukhi", "sukha hai", "कोरडी"]):
        return "dry"
    if any(w in lower for w in ["nami hai", "nami", "नमी है", "नमी", "moist", "moisture", "has moisture", "good moisture", "ओलावा"]):
        return "moist"
    if any(w in lower for w in ["geeli", "geeli hai", "गीली", "गीली है", "wet", "waterlogged", "bahut geeli", "पाणी साचले"]):
        return "wet"

    return None


def resolve_farm_context(
    text: str,
    history: Optional[List[Dict[str, Any]]] = None,
    session_context: Optional[Dict[str, Any]] = None,
    farm_info: Optional[Dict[str, Any]] = None,
    farm_profile: Optional[Dict[str, Any]] = None,
    default_language: str = "hi"
) -> Dict[str, Any]:
    """
    Lightweight Personalized Farm and Crop Context Engine:
    Maintains, normalizes, and updates the core agricultural context fields across conversation turns.
    Fields supported:
      - crop: canonical crop name (e.g. 'wheat', 'rice', 'tomato')
      - crop_age_days: age in days (integer)
      - location: district / state info
      - soil_moisture: 'slightly_dry', 'dry', 'moist', 'wet'
      - soil_type: 'loam', 'sandy', 'clay', 'black', 'red'
      - irrigation_method: 'drip', 'sprinkler', 'flood'
      - season: 'rabi', 'kharif', 'zaid'
      - current_intent: active intent (e.g. 'irrigation', 'fertilizer', 'crop_disease')
      - original_question: initial user query
      - pending_field: 'crop', 'crop_age', 'location', 'soil_moisture', or None
      - language: current conversation language code
    """
    ctx: Dict[str, Any] = {
        "crop": None,
        "crop_age_days": None,
        "location": None,
        "soil_moisture": None,
        "soil_type": None,
        "irrigation_method": None,
        "season": None,
        "current_intent": None,
        "original_question": None,
        "pending_field": None,
        "detected_disease": None,
        "disease_confidence": None,
        "disease_details": None,
        "disease_image_url": None,
        "language": default_language or "hi"
    }

    # 1. Seed from session_context if provided
    if session_context and isinstance(session_context, dict):
        for k in ctx.keys():
            if session_context.get(k) is not None:
                ctx[k] = session_context[k]
        if ctx.get("crop"):
            ctx["crop"] = normalize_crop_name(ctx["crop"])

    # 2. Seed from farm_info / farm_profile if available
    profile_data = farm_info or farm_profile
    if profile_data and isinstance(profile_data, dict):
        if not ctx["crop"]:
            raw_c = profile_data.get("crop") or profile_data.get("crop_name") or profile_data.get("crop_type")
            if raw_c:
                ctx["crop"] = normalize_crop_name(raw_c)
        if not ctx["soil_type"]:
            ctx["soil_type"] = profile_data.get("soil_type") or profile_data.get("soil")
        if not ctx["irrigation_method"]:
            ctx["irrigation_method"] = profile_data.get("irrigation_method") or profile_data.get("irrigation_type")
        if not ctx["location"]:
            state = profile_data.get("state")
            dist = profile_data.get("district")
            if state or dist:
                ctx["location"] = f"{dist}, {state}".strip(", ")

    # 3. Parse History Turns chronologically to reconstruct state evolution
    if history and isinstance(history, list):
        for turn in history:
            role = str(turn.get("role", "")).lower()
            msg = turn.get("text") or turn.get("message") or turn.get("content") or ""
            if not msg:
                continue

            if role in ["user", "farmer"]:
                if not ctx["original_question"]:
                    ctx["original_question"] = msg
                
                # Check for explicit crop mention
                hist_crop = extract_crop_entity(msg)
                if hist_crop:
                    hist_crop_norm = normalize_crop_name(hist_crop)
                    if ctx["crop"] and ctx["crop"] != hist_crop_norm:
                        ctx["crop"] = hist_crop_norm
                        ctx["crop_age_days"] = None  # Reset age for newly switched crop
                    else:
                        ctx["crop"] = hist_crop_norm

                # Check for crop age
                hist_age = extract_crop_age(msg)
                if hist_age is not None:
                    ctx["crop_age_days"] = hist_age

                # Check for location
                hist_loc = extract_location_entity(msg)
                if hist_loc:
                    ctx["location"] = hist_loc

                # Check for soil moisture
                hist_sm = extract_soil_moisture(msg)
                if hist_sm:
                    ctx["soil_moisture"] = hist_sm

                # Check soil / irrigation / season
                st = extract_soil_type(msg)
                if st: ctx["soil_type"] = st
                im = extract_irrigation_method(msg)
                if im: ctx["irrigation_method"] = im
                sn = extract_season(msg)
                if sn: ctx["season"] = sn

            elif role in ["assistant", "bot", "saathi"]:
                last_ast = msg.lower()
                # A question from assistant typically contains a question mark or is a short follow-up prompt
                is_short_prompt = len(msg.split()) <= 20 or "?" in msg or "क्या" in msg or "कौन" in msg or "कितने" in msg
                
                is_crop_q = is_short_prompt and any(q in last_ast for q in [
                    "फसल उगा रहे", "कौन सी फसल", "फसल प्रभावित", "किस फसल",
                    "which crop", "crop are you growing", "crop is affected", "what crop",
                    "kaun si fasal", "konsi fasal", "fasal uga rahe", "fasal prabhavit", "kis fasal",
                    "ਕਿਹੜੀ ਫ਼ਸਲ", "ਕਿਹੜੀ ਫਸਲ", "कोणते पीक", "কোন ফসল", "કયો પાક",
                    "என்ன பயிர்", "ఏ పంట", "ಯಾವ ಬೆಳೆ", "ഏത് വിള", "କେଉଁ ଫସଲ", "কি শস্য", "کون سی فصل"
                ])
                is_age_q = is_short_prompt and any(q in last_ast for q in [
                    "कितने दिन", "कितने दिनों", "अवस्था क्या", "अवस्था कौन", "उम्र क्या", "कितने समय",
                    "how many days", "how old", "days old", "crop stage is it", "growth stage is it",
                    "kitne din", "kitne dino", "stage kya hai", "kitne din ki hai",
                    "ਕਿੰਨੇ ਦਿਨਾਂ", "ਕਿੰਨੇ ਦਿਨ", "किती दिवस", "किती दिवसांचे",
                    "কত দিন", "કેટલા દિવસ", "எத்தனை நாள்", "ఎన్ని రోజులు",
                    "ಎಷ್ಟು ದಿನ", "ಎತ್ರ ദിവസം", "କେତେ ଦିନ", "কিমান দিন", "کتنے دن"
                ])
                is_loc_q = is_short_prompt and any(q in last_ast for q in [
                    "स्थान कौन सा", "स्थान क्या", "स्थान बताइए", "खेत कहाँ", "किस जिले",
                    "which location", "farm location", "where is your farm", "location of your farm",
                    "sthan kaun", "sthan kya", "khet kahan", "ਕਿਹੜਾ ਸਥਾਨ", "ਸਥਾਨ", "ठिकाण", "ಸ್ಥಳ", "స్థలం", "இருப்பிடம்", "স্থান", "સ્થળ"
                ])
                is_moisture_q = is_short_prompt and any(q in last_ast for q in [
                    "मिट्टी अभी सूखी", "सूखी है या", "नमी है या", "मिट्टी सूखी",
                    "soil currently dry", "soil is dry", "dry or does it have moisture",
                    "mitti abhi sukhi", "mitti sukhi hai ya", "सूखी है या उसमें नमी"
                ])
                is_image_q = is_short_prompt and any(q in last_ast for q in [
                    "फोटो भेजें", "साफ फोटो", "फोटो अपलोड", "प्रभावित पत्तियों",
                    "send a clear photo", "upload a photo", "clear photo", "photo of the affected",
                    "photo bhejein", "saaf photo", "photo upload", "prabhavit pattiyon"
                ])
                if is_crop_q:
                    ctx["pending_field"] = "crop"
                elif is_age_q:
                    ctx["pending_field"] = "crop_age"
                elif is_loc_q:
                    ctx["pending_field"] = "location"
                elif is_moisture_q:
                    ctx["pending_field"] = "soil_moisture"
                elif is_image_q:
                    ctx["pending_field"] = "crop_image"
                else:
                    ctx["pending_field"] = None

    # 4. Update with Current Utterance
    prior_pending = ctx.get("pending_field")
    ctx["_resolved_pending_field"] = None
    if text and text.strip():
        curr_text = text.strip()
        ctx["language"] = detect_language_from_text(curr_text, default_language=ctx.get("language") or default_language)
        
        curr_crop = extract_crop_entity(curr_text)
        if curr_crop:
            curr_crop_norm = normalize_crop_name(curr_crop)
            if ctx["crop"] and ctx["crop"] != curr_crop_norm:
                ctx["crop"] = curr_crop_norm
                ctx["crop_age_days"] = None  # Reset age on crop switch
            else:
                ctx["crop"] = curr_crop_norm

        curr_age = extract_crop_age(curr_text)
        if curr_age is not None:
            ctx["crop_age_days"] = curr_age

        curr_loc = extract_location_entity(curr_text)
        if not curr_loc and prior_pending == "location":
            cand = re.sub(r"[^\w\s]", "", curr_text).strip()
            if 1 <= len(cand.split()) <= 4 and len(cand) >= 2:
                curr_loc = cand.title()
        if curr_loc:
            ctx["location"] = curr_loc

        curr_sm = extract_soil_moisture(curr_text)
        if curr_sm:
            ctx["soil_moisture"] = curr_sm

        curr_st = extract_soil_type(curr_text)
        if curr_st: ctx["soil_type"] = curr_st
        curr_im = extract_irrigation_method(curr_text)
        if curr_im: ctx["irrigation_method"] = curr_im
        curr_sn = extract_season(curr_text)
        if curr_sn: ctx["season"] = curr_sn

        # Check pending field state resolution & next step in sequence
        if prior_pending == "crop" and ctx["crop"]:
            ctx["_resolved_pending_field"] = "crop"
            if ctx.get("current_intent") == "irrigation":
                if ctx["crop_age_days"] is None:
                    ctx["pending_field"] = "crop_age"
                elif ctx["location"] is None:
                    ctx["pending_field"] = "location"
                else:
                    ctx["pending_field"] = None
            else:
                ctx["pending_field"] = None
        elif prior_pending == "crop_age" and ctx["crop_age_days"] is not None:
            ctx["_resolved_pending_field"] = "crop_age"
            if ctx.get("current_intent") == "irrigation":
                if ctx["location"] is None:
                    ctx["pending_field"] = "location"
                else:
                    ctx["pending_field"] = None
            else:
                ctx["pending_field"] = None
        elif (prior_pending == "location" and ctx["location"]) or (curr_loc and ctx["location"]):
            ctx["_resolved_pending_field"] = "location"
            ctx["pending_field"] = None
        elif prior_pending == "soil_moisture" and ctx["soil_moisture"]:
            ctx["_resolved_pending_field"] = "soil_moisture"
            ctx["pending_field"] = None
        else:
            ctx["_resolved_pending_field"] = None

    return ctx


def reconstruct_conversation_context(history: Optional[List[Dict[str, str]]]) -> Dict[str, Any]:
    """Backward compatibility wrapper for legacy callers."""
    return resolve_farm_context("", history=history)


# ============================================================
# APP NAVIGATION & FEATURE HELP INTENTS
# ============================================================

NAVIGATION_ROUTES = {
    "weather": {
        "url": "/frontend/pages/weather-dashboard.html",
        "label": "Live Weather & 15-Day Forecast",
        "keywords": [
            "weather page", "weather dikhao", "mausam dikhao", "mausam dekhein", "weather dashboard",
            "forecast page", "open weather", "weather section", "मौसम दिखाओ", "मौसम खोलो", "हवामान दाखवा",
            "ਪਾਣੀਪਾਗ", "ਮੌਸਮ ਦੇਖੋ", "வானிலை காட்டு"
        ]
    },
    "crop_diagnosis": {
        "url": "/frontend/pages/upload-crop.html",
        "label": "AI Crop Disease Doctor / Upload",
        "keywords": [
            "crop doctor", "crop diagnosis", "upload crop", "scan crop", "photo check", "leaf photo",
            "bimari check", "doctor kholo", "doctor page", "photo upload", "disease scanner",
            "क्रॉप डॉक्टर", "फोटो अपलोड", "बीमारी जांच", "रोग निदान", "পোকামাকড় পরীক্ষা"
        ]
    },
    "recommendations": {
        "url": "/frontend/pages/crop-recommendation.html",
        "label": "Crop Recommendation Engine",
        "keywords": [
            "recommendation page", "which crop to grow", "crop suggestion", "fasal sujhav",
            "recommendation engine", "फसल सुझाव", "पीक शिफारस", "பயிர் பரிந்துரை"
        ]
    },
    "marketplace": {
        "url": "/frontend/pages/crop-listings.html",
        "label": "Verified Marketplace & Listings",
        "keywords": [
            "marketplace", "listings", "mandi listings", "sell crop", "buyer list", "crop market",
            "fasal bechna", "marketplace dikhao", "मार्केटप्लेस", "मंडी लिस्टिंग", "खरेदीदार यादी"
        ]
    },
    "dashboard": {
        "url": "/frontend/pages/farmer-dashboard.html",
        "label": "Farmer Command Center",
        "keywords": [
            "dashboard", "home", "main page", "farmer home", "command center", "डैशबोर्ड", "मुख्य पृष्ठ"
        ]
    },
    "profile": {
        "url": "/frontend/pages/farmer-profile.html",
        "label": "Farm & Farmer Profile",
        "keywords": [
            "my profile", "farm profile", "profile page", "khet ki details", "mera profile", "प्रोफाइल", "माझी माहिती"
        ]
    }
}

def detect_navigation_intent(text: str) -> Optional[Dict[str, str]]:
    """Detect if the user is asking to open or navigate to an app page."""
    if not text:
        return None
    lower = text.lower()
    
    # Generic action verbs
    action_verbs = ["kholo", "khol do", "dikhao", "dikhaye", "open", "show", "navigate", "take me to", "goto", "go to", "खोलो", "दिखाओ", "दाखवा", "ખોલો", "ਖੋਲ੍ਹੋ", "തുറക്കൂ", "ತೆರೆ"]
    has_action = any(verb in lower for verb in action_verbs)

    for route_key, route_info in NAVIGATION_ROUTES.items():
        for kw in route_info["keywords"]:
            if kw in lower or (has_action and route_key in lower):
                return {
                    "action": "navigate",
                    "route": route_key,
                    "target": route_info["url"],
                    "label": route_info["label"]
                }
    return None

# ============================================================
# APP HELP & PLATFORM TOUR INTENTS
# ============================================================

APP_HELP_KEYWORDS = [
    "is app mein kya hai", "app me kya kya hai", "app kaise use kare", "how to use this app",
    "what does this app do", "help with app", "agribridge kya hai", "app ke bare mein batao",
    "feature kya hai", "is app se kya hoga", "एग्रीब्रिज क्या है", "ऐप कैसे चलाएं", "ऐप में क्या है",
    "या अ‍ॅपमध्ये काय आहे", "এই অ্যাপে কী আছে", "ਇਸ ਐਪ ਵਿੱਚ ਕੀ ਹੈ", "ఈ యాప్‌లో ఏముంది",
    "app tour", "app features", "help me use", "what can you do"
]

def is_app_help_query(text: str) -> bool:
    if not text:
        return False
    lower = text.lower()
    if any(kw in lower for kw in APP_HELP_KEYWORDS):
        return True
    has_app_mention = any(w in lower for w in ["app", "agribridge", "application", "ऐप", "एग्रीब्रिज", "ਅੈਪ", "యాప్", "ஆப்"])
    has_inquiry = any(w in lower for w in ["kya", "kaise", "what", "how", "help", "feature", "batao", "samjhao", "guide", "कया", "कैसे", "मदद", "ਦੱਸੋ", "చెప్పండి"])
    if has_app_mention and has_inquiry:
        return True
    return False

# ============================================================
# TOPIC KEYWORD MAPS
# ============================================================

TOPIC_KEYWORDS = {
    "weather": [
        "weather", "rain", "rainfall", "temperature", "forecast", "heat", "cold", "frost", "storm", "wind", "humidity",
        "barish", "mausam", "baarish", "garmi", "sardi", "hawa", "toofan", "pani barsega",
        "मौसम", "बारिश", "वर्षा", "तापमान", "हवा", "पाला", "ओले", "कोहरा", "धूप",
        "ପାଣିପାଗ", "ବର୍ଷା", "ତାପମାତ୍ରା", "ଖରା",
        "हवामान", "पाऊस", "तापमान", "थंडी",
        "আবহাওয়া", "বৃষ্টি", "তাপমাত্রা",
        "వాతావరణం", "వర్షం", "ఉష్ణోగ్రత",
        "வானிலை", "மழை", "வெப்பநிலை",
        "ಹವಾಮಾನ", "ಮಳೆ", "ತಾಪಮಾನ",
        "കാലാവസ്ഥ", "മഴ", "താപനില",
        "હવામાન", "વરસાદ", "તાપમાન",
        "ਮੌਸਮ", "ਮੀਂਹ", "ਤਾਪਮਾਨ"
    ],
    "irrigation": [
        "irrigate", "irrigation", "water", "watering", "drip", "sprinkler", "flood", "canal", "dry field", "moisture",
        "paani", "sinchai", "drip", "palewa", "nami",
        "पानी", "सिंचाई", "पलेवा", "नमी", "ड्रिप", "फुहारा", "जल",
        "ଜଳସେଚନ", "ପାଣି ଦେବା", "ଜଳ",
        "पाणी देणे", "सिंचन", "ठिबक", "तुषार",
        "জলসেচ", "পানি দেওয়া",
        "నీరు", "సాగునీరు", "డ్రిప్", "స్ప్రింక్లర్",
        "பாசனம்", "தண்ணீர் பாய்ச்சுதல்", "சொட்டு நீர்",
        "ನೀರಾವರಿ", "ನೀರುಣಿಸುವುದು", "ಹನಿ ನೀರಾವರಿ",
        "നനയ്ക്കൽ", "ജലസേചനം", "ഡ്രിപ്പ്",
        "પિયત", "સિંચાઈ", "ટપક પદ્ધતિ",
        "ਸਿੰਚਾਈ", "ਪਾਣੀ ਦੇਣਾ", "ਫੁਹਾਰਾ"
    ],
    "fertilizer": [
        "fertilizer", "manure", "urea", "dap", "npk", "potash", "zinc", "nitrogen", "compost", "nutrient", "micronutrient",
        "khaad", "khad", "gobar", "poshak",
        "खाद", "उर्वरक", "यूरिया", "डीएपी", "पोटाश", "जिंक", "गोबर", "पोषक तत्व",
        "ଖତ", "ସାର", "ୟୁରିଆ", "ଡିଏପି",
        "खत", "युरिया", "शेणखत", "डीएपी",
        "সার", "ইউরিয়া", "জৈব সার",
        "ఎరువులు", "యూరియా", "రసాయనిక ఎరువు",
        "உரம்", "யூரியா", "இயற்கை உரம்",
        "ಗೊಬ್ಬರ", "ಯೂರಿಯಾ", "ರಸಗೊಬ್ಬರ",
        "വളം", "യൂറിയ", "ജൈവവളം",
        "ખાતર", "યુરિયા", "દેશી ખાતર",
        "ਖਾਦ", "ਯੂਰੀਆ", "ਰੂੜੀ ਖਾਦ"
    ],
    "crop_disease": [
        "disease", "blight", "rot", "wilt", "rust", "leaf spot", "fungus", "mildew", "yellow leaf", "yellowing",
        "curl", "canker", "scab", "blast", "spot", "infection", "sick", "dying", "turning yellow", "black spots",
        "bimari", "rog", "peela", "peele", "daag", "dhabba", "sukha",
        "बीमारी", "रोग", "पीली", "पीला", "सड़न", "झुलसा", "फफूंद", "दाग", "धब्बा", "पत्ती सूख", "मुरझाना",
        "ରୋଗ", "ପତ୍ର ହଳଦିଆ", "ଶୁଖିଯିବା", "ପଚା", "ଦାଗ",
        "रोग", "करपा", "पाने पिवळी", "कूज", "बुरशी",
        "রোগ", "পাতার দাগ", "পচন", "হলুদ পাতা",
        "వ్యాధి", "తెగులు", "ఆకులు పసుపు", "కుళ్లు",
        "நோய்", "இலை கருகல்", "மஞ்சள் இலை", "அழுகல்",
        "ರೋಗ", "ಎಲೆ ಹಳದಿ", "ಕೊಳೆ ರೋಗ",
        "രോഗം", "ഇല മഞ്ഞളിപ്പ്", "ചീയൽ",
        "રોગ", "સુકારો", "પીળા પાન", "સડો",
        "ਬਿਮਾਰੀ", "ਰੋਗ", "ਪੀਲੇ ਪੱਤੇ", "ਸੜਨ"
    ],
    "pest": [
        "pest", "insect", "bug", "worm", "caterpillar", "aphid", "borer", "whitefly", "mite", "locust", "termites",
        "keeda", "keede", "illli", "illi", "sundi", "dimak", "kide",
        "कीड़ा", "कीट", "इल्ली", "माहू", "सुंडी", "दीमक", "सफेद मक्खी",
        "ପୋକ", "କୀଟ", "ଶୁଣ୍ଢୀ",
        "किडे", "अळी", "मावा", "तुडतुडे",
        "পোকা", "কীটপতঙ্গ",
        "పురుగు", "కీటకం", "లద్దెపురుగు",
        "பூச்சி", "புழு", "வண்டு",
        "ಕೀಟ", "ಹುಳು", "ಜಿಗಿಹುಳು",
        "കീടം", "പുഴു", "പ്രാണി",
        "જીવાત", "ઈયળ", "મોલો",
        "ਕੀੜੇ", "ਸੁੰਡੀ", "ਤੇਲਾ"
    ],
    "market": [
        "mandi", "msp", "price", "rate", "buyer", "sell", "market", "bhav", "daam", "kimat",
        "मंडी", "भाव", "दाम", "एमएसपी", "खरीदार", "बेचना", "बाजार",
        "ମଣ୍ଡି", "ଦର", "ମୂଲ୍ୟ", "ବିକ୍ରି",
        "बाजारभाव", "मंडी", "दर", "खरेदीदार",
        "মান্ডি", "দাম", "দর", "বিক্রি",
        "మార్కెట్", "ధర", "మండి", "కొనుగోలుదారు",
        "சந்தை", "விலை", "மண்டி", "வாங்குபவர்",
        "ಮಾರುಕಟ್ಟೆ", "ಬೆಲೆ", "ಮಂಡಿ",
        "വിപണി", "വില", "മാർക്കറ്റ്",
        "બજાર", "ભાવ", "વેચાણ",
        "ਮੰਡੀ", "ਭਾਅ", "ਰੇਟ", "ਵਿਕਰੀ"
    ],
    "government_scheme": [
        "pm kisan", "kisan credit", "subsidy", "scheme", "loan", "fasal bima", "insurance", "krishi yojana",
        "योजना", "सब्सिडी", "ऋण", "लोन", "बीमा", "किसान क्रेडिट", "मुआवजा", "सरकारी योजना",
        "ଯୋଜନା", "ସବସିଡି", "ଋଣ", "ବୀମା",
        "योजना", "अनुदान", "कर्ज", "विमा",
        "যোজনা", "ভর্তুকি", "ঋণ", "বীমা",
        "పథకం", "సబ్సిడీ", "రుణం", "బీమా",
        "திட்டம்", "மானியம்", "கடன்", "காப்பீடு",
        "ಯೋಜನೆ", "ಸಬ್ಸಿಡಿ", "ಸಾಲ", "ವಿಮೆ",
        "പദ്ധതി", "സബ്‌സിഡി", "വായ്പ", "ഇൻഷുറൻസ്",
        "યોજના", "સબસિડી", "ધિરાણ", "વીમો",
        "ਯੋਜਨਾ", "ਸਬਸਿਡੀ", "ਕਰਜ਼ਾ", "ਬੀਮਾ"
    ],
    "soil": [
        "soil", "ph", "clay", "sand", "loam", "black soil", "soil health", "salinity", "mitti", "zameen",
        "मिट्टी", "मृदा", "जमीन", "खेत की मिट्टी", "जांच",
        "ମାଟି", "ଜମି", "ମୃତ୍ତିକା",
        "माती", "जमीन",
        "মাটি", "জমি",
        "నేల", "మట్టి",
        "மண்", "நிலம்",
        "ಮಣ್ಣು", "ಭೂಮಿ",
        "മണ്ണ്", "നിലം",
        "માટી", "જમીન",
        "ਮਿੱਟੀ", "ਜ਼ਮੀਨ"
    ],
    "crop_cultivation": [
        "sow", "sowing", "seed", "variety", "yield", "harvest", "harvesting", "germination", "crop", "plant",
        "grow", "cultivation", "flowering", "fruiting", "maturity", "seedling", "vegetative",
        "buwai", "beej", "fasal", "katai", "upaj",
        "बोना", "बुवाई", "बीज", "फसल", "पौधा", "उपज", "कटाई", "पैदावार", "फूल आना",
        "ବୁଣିବା", "ମଞ୍ଜି", "ଫସଲ", "ଅମଳ", "ଗଛ",
        "पेरणी", "बियाणे", "पीक", "कापणी", "उत्पादन",
        "বপন", "বীজ", "ফসল", "চাষ",
        "విత్తనం", "పంట", "సాగు", "కోత",
        "விதை", "பயிர்", "சாகுபடி", "அறுவடை",
        "ಬಿತ್ತನೆ", "ಬೀಜ", "ಬೆಳೆ", "ಕೊಯ್ಲು",
        "വിത്ത്", "വിള", "കൃഷി", "വിളവെടുപ്പ്",
        "વાવણી", "બીજ", "પાક", "લણણી",
        "ਬਿਜਾਈ", "ਬੀਜ", "ਫ਼ਸਲ", "ਵਾਢੀ"
    ]
}

GREETING_KEYWORDS = [
    "hi", "hello", "hey", "namaste", "namaskar", "pranam", "ram ram", "good morning",
    "good afternoon", "good evening", "satsriakal", "sat sri akal", "vanakkam", "adab",
    "kaisa hai", "kaise ho", "who are you", "what can you do", "help me", "introduce yourself",
    "नमस्ते", "नमस्कार", "प्रणाम", "राम राम", "जय किसान", "हेलो", "हाय", "कैसे हो", "आप कौन हैं",
    "ନମସ୍କାର", "ପ୍ରଣାମ", "ଜୟ କୃଷକ", "ହେଲୋ", "କେମିତି ଅଛନ୍ତି",
    "नमस्कार", "राम राम", "हॅलो", "कसे आहात",
    "নমস্কার", "সালাম", "হ্যালো", "কেমন আছেন",
    "నమస్కారం", "హలో", "ఎలా ఉన్నారు",
    "வணக்கம்", "ஹலோ", "எப்படி இருக்கிறீர்கள்",
    "ನಮಸ್ಕಾರ", "ಹಲೋ", "ಹೇಗಿದ್ದೀರಿ",
    "നമസ്കാരം", "ഹലോ", "സുഖമാണോ",
    "નમસ્તે", "નમસ્કાર", "જય શ્રી કૃષ્ણ", "હેલો", "કેમ છો",
    "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ", "ਹੈਲੋ", "ਕਿਵੇਂ ਹੋ",
    "سلام", "آداب", "کیسے ہیں"
]

def extract_farmer_name(text: str) -> Optional[str]:
    """Extract farmer name if mentioned in greeting or introduction."""
    if not text:
        return None
    patterns = [
        r"(?:my name is|i am|this is|i'm)\s+([A-Za-z]+)",
        r"(?:mera naam|main|hum)\s+([A-Za-z\u0900-\u097F]+)",
        r"(?:hello|hi|hey|namaste|namaskar)\s+([A-Za-z]+)",
        r"(?:hello|hi|hey|namaste|namaskar)\s+([A-Za-z]+)\s+here",
        r"([A-Za-z]+)\s+(?:here|speaking)",
    ]
    lower = text.strip()
    for pat in patterns:
        m = re.search(pat, lower, re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            if name.lower() not in ["agribridge", "there", "sir", "madam", "farmer", "kisan", "bhai", "ji", "to", "the", "a"]:
                return name.capitalize()
    return None

# ============================================================
# REAL-TIME LANGUAGE DETECTION
# ============================================================

def detect_language_from_text(text: str, default_language: str = "hi") -> str:
    """
    Detect language from actual utterance text:
    - Script-based detection for regional Indian languages (pa, gu, or, ta, te, kn, ml, ur, bn/as)
    - Devanagari script vocabulary analysis for Marathi vs Hindi
    - Latin / Roman script vocabulary analysis for Hinglish vs English
    """
    if not text or not text.strip():
        return default_language or "hi"

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
    if re.search(r"[\u0980-\u09FF]", clean):
        if re.search(r"[\u09F0\u09F1]", clean) or any(w in clean for w in ["আপুনি", "কওক", "কেনে", "হয়"]):
            return "as"
        return "bn"

    # 2. Devanagari script: Distinguish Marathi vs Hindi
    if re.search(r"[\u0900-\u097F]", clean):
        marathi_markers = ["ळ", "आहे", "आहात", "कसे", "काय", "नाही", "मला", "सांगा", "होते", "करा", "मी", "आपण", "नमस्कार", "पाहिजे", "पाहायचा", "बाजारभाव"]
        hindi_copulas = ["है", "हैं", "हूं", "हूँ", "था", "थी", "मुझे", "बताओ", "करना", "चाहिए", "डालें", "डालूँ", "करें", "होगी"]
        if any(w in clean for w in marathi_markers) and not any(w in clean for w in hindi_copulas):
            return "mr"
        return "hi"

    # 3. Latin / Roman script: Distinguish Hinglish vs English
    lower = clean.lower()
    words = set(re.findall(r"\b[a-z']+\b", lower))

    hinglish_vocabulary = {
        "mere", "mera", "meri", "khet", "mein", "me", "paani", "pani", "kab", "dena", "hai", "hain", "ho", "hoon", "hun",
        "gehu", "gehun", "kaunsi", "kaunsa", "kaunse", "konsi", "konse", "khaad", "khad", "daalun", "daalu", "dale", "daalein", "daalo",
        "karna", "karein", "kare", "karu", "hogi", "hoga", "kya", "kaise", "kaisa", "kaisi", "batao", "bataiye", "bol", "bolo",
        "aaj", "kal", "parso", "fasal", "patti", "pattiyan", "daag", "dhabbe", "sukha", "peela", "keeda", "keede", "rog", "bimari",
        "tamatar", "bhav", "daam", "kimat", "mandi", "zameen", "buwai", "katai", "sinchai", "sinchaee", "yojana", "banao", "namaste",
        "aap", "aapka", "aapki", "tum", "bhai", "ji", "chahiye", "nahi", "nahin", "theek", "thik", "bahut", "achha", "accha", "dekhbhal"
    }

    english_common = {
        "what", "how", "when", "where", "which", "why", "who", "is", "are", "do", "does", "did", "will", "would", "should",
        "can", "could", "my", "your", "our", "their", "the", "a", "an", "in", "on", "at", "to", "for", "from", "with",
        "water", "field", "farm", "crop", "crops", "fertilizer", "soil", "prepare", "sowing", "care", "disease", "leaves",
        "spots", "yellow", "rain", "tomorrow", "today", "weather", "market", "price", "today's", "mandi", "app", "use",
        "this", "create", "plan", "need", "affecting"
    }

    hing_hits = len(words.intersection(hinglish_vocabulary))
    eng_hits = len(words.intersection(english_common))

    if hing_hits >= 1 and hing_hits >= eng_hits:
        return "hinglish"
    if eng_hits > hing_hits:
        return "en"
    if hing_hits >= 1:
        return "hinglish"

    return default_language if default_language in ["en", "hi", "hinglish"] else "en"


# ============================================================
# MASTER INTENT CLASSIFICATION FUNCTION
# ============================================================

def classify_intent(
    text: str,
    default_language: str = "hi",
    history: Optional[List[Dict[str, Any]]] = None,
    session_context: Optional[Dict[str, Any]] = None,
    farm_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Master Kisan Saathi classifier with Personalized Context Engine:
    - Extracts context from utterance & history (crop, age, soil, irrigation, location).
    - Preserves established crop and crop age for follow-ups (e.g. 'अब पानी कब दूं?', 'इसमें कौन सी खाद डालूं?').
    - Returns standardized routing dictionary with full 'context' object.
    """
    if not text or not text.strip():
        ctx = resolve_farm_context("", history=history, session_context=session_context, farm_info=farm_info, default_language=default_language)
        return {
            "success": True,
            "intent": "fallback",
            "domain": "general",
            "topic": "non_agriculture",
            "language": default_language or "hi",
            "confidence": 0.0,
            "is_agriculture_related": False,
            "detected_crop": ctx.get("crop"),
            "context": ctx,
            "navigation_action": None,
            "language_switch": None,
        }

    clean_text = text.strip()
    lower_text = clean_text.lower()

    # 1. Resolve Context across History, Session Context, and Current Utterance
    ctx = resolve_farm_context(
        clean_text,
        history=history,
        session_context=session_context,
        farm_info=farm_info,
        default_language=default_language
    )

    switched_lang = detect_language_switch(clean_text)
    active_lang = switched_lang or ctx.get("language") or default_language or "hi"
    ctx["language"] = active_lang

    crop_entity = ctx.get("crop") or extract_crop_entity(clean_text)

    # 2. Check for Explicit Unrelated Intent Triggers (weather, mandi, navigation, app help)
    has_explicit_weather = any(re.search(pat, lower_text, re.IGNORECASE) for pat in [
        r"(कल|आज|परसों)?\s*(बारिश|मौसम|तापमान|हवामान|वर्षा)\s*(होगी|कैसा|कितना|आएगी|का\s*अनुमान|रहेगा|alert|forecast)",
        r"(will\s+it\s+rain|weather\s+forecast|what\s+is\s+the\s+weather|temperature\s+today|temperature\s+tomorrow|rain\s+today)",
        r"\b(weather|mausam|hawa|barish|barsat|rain|rainy)\b",
    ])
    has_explicit_mandi = any(re.search(pat, lower_text, re.IGNORECASE) for pat in [
        r"(मंडी\s*में\s*(टमाटर|गेहूं|धान|फसल)?\s*(का\s*)?भाव|बाजार\s*भाव|दाम\s*क्या\s*है|एमएसपी|रेट\s*क्या\s*है|कीमत\s*क्या\s*है|भाव\s*क्या\s*है)",
        r"(mandi\s*(mein|me)?\s*(tamatar|tomato|gehu|dhan|aalu|aloo)?\s*(ka\s*)?bhav|market\s*price|aaj\s*ka\s*bhav|rate\s*kya\s*hai|daam\s*kya\s*hai)",
        r"\b(mandi|bhav|market\s+rate|wholesale\s+price)\b",
    ])
    has_explicit_nav = any(re.search(pat, lower_text, re.IGNORECASE) for pat in [
        r"(how\s+(do\s+i|to)\s+use\s+(this\s+)?app|how\s+does\s+this\s+app\s+work)",
        r"(कहाँ\s*(पर\s*)?है|बटन\s*दिखाओ|पेज\s*खोलो|screen\s*open|navigate\s*to)",
    ])

    is_explicit_unrelated = has_explicit_weather or has_explicit_mandi or has_explicit_nav

    # 3. Check Pending Context Answering from Conversation Flow
    resolved_field = ctx.get("_resolved_pending_field")
    if not is_explicit_unrelated and resolved_field:
        # Case A: Pending Crop Answering / Crop Provided
        if resolved_field == "crop":
            target_intent = ctx.get("current_intent") or "irrigation"
            target_domain = "farm" if target_intent == "irrigation" else "crop"
            target_topic = "irrigation" if target_intent == "irrigation" else "crop_cultivation"
            return {
                "success": True,
                "intent": target_intent,
                "domain": target_domain,
                "topic": target_topic,
                "language": active_lang,
                "confidence": 0.98,
                "is_agriculture_related": True,
                "detected_crop": ctx["crop"],
                "crop_age_days": ctx.get("crop_age_days"),
                "location": ctx.get("location"),
                "soil_moisture": ctx.get("soil_moisture"),
                "resolved_pending_field": "crop",
                "context": ctx,
                "navigation_action": None,
                "language_switch": switched_lang,
            }

        # Case B: Pending Crop Age Answering
        elif resolved_field == "crop_age":
            target_intent = ctx.get("current_intent") or "irrigation"
            target_domain = "farm" if target_intent == "irrigation" else "crop"
            target_topic = "irrigation" if target_intent == "irrigation" else "crop_cultivation"
            target_crop = ctx.get("crop") or "wheat"
            return {
                "success": True,
                "intent": target_intent,
                "domain": target_domain,
                "topic": target_topic,
                "language": active_lang,
                "confidence": 0.98,
                "is_agriculture_related": True,
                "detected_crop": target_crop,
                "crop_age_days": ctx["crop_age_days"],
                "location": ctx.get("location"),
                "soil_moisture": ctx.get("soil_moisture"),
                "resolved_pending_field": "crop_age",
                "context": ctx,
                "navigation_action": None,
                "language_switch": switched_lang,
            }

        # Case C: Pending Location Answering
        elif resolved_field == "location":
            target_intent = ctx.get("current_intent") or "irrigation"
            target_domain = "farm" if target_intent == "irrigation" else "crop"
            target_topic = "irrigation" if target_intent == "irrigation" else "weather"
            target_crop = ctx.get("crop") or "wheat"
            return {
                "success": True,
                "intent": target_intent,
                "domain": target_domain,
                "topic": target_topic,
                "language": active_lang,
                "confidence": 0.98,
                "is_agriculture_related": True,
                "detected_crop": target_crop,
                "crop_age_days": ctx.get("crop_age_days"),
                "location": ctx["location"],
                "soil_moisture": ctx.get("soil_moisture"),
                "resolved_pending_field": "location",
                "context": ctx,
                "navigation_action": None,
                "language_switch": switched_lang,
            }

        # Case D: Pending Soil Moisture Answering
        elif resolved_field == "soil_moisture":
            target_intent = ctx.get("current_intent") or "irrigation"
            target_domain = "farm" if target_intent == "irrigation" else "crop"
            target_topic = "irrigation"
            target_crop = ctx.get("crop") or "wheat"
            return {
                "success": True,
                "intent": target_intent,
                "domain": target_domain,
                "topic": target_topic,
                "language": active_lang,
                "confidence": 0.98,
                "is_agriculture_related": True,
                "detected_crop": target_crop,
                "crop_age_days": ctx.get("crop_age_days"),
                "location": ctx.get("location"),
                "soil_moisture": ctx["soil_moisture"],
                "resolved_pending_field": "soil_moisture",
                "context": ctx,
                "navigation_action": None,
                "language_switch": switched_lang,
            }

    # 4. Check for App Navigation Commands
    nav_action = detect_navigation_intent(clean_text)
    if nav_action:
        return {
            "success": True,
            "intent": "navigation",
            "domain": "app",
            "topic": "navigation",
            "language": active_lang,
            "confidence": 0.95,
            "is_agriculture_related": True,
            "navigation_action": nav_action,
            "detected_crop": crop_entity,
            "context": ctx,
            "language_switch": switched_lang,
        }

    # 5. Check for App Help Query (Domain 1: app_help)
    app_help_patterns = [
        r"(how\s+(do\s+i|to)\s+use\s+(this\s+)?app|how\s+does\s+this\s+(app|website)\s+work|what\s+can\s+this\s+app\s+do|app\s+tour|help\s+with\s+app)",
        r"(ऐप|एग्रीब्रिज|वेबसाइट)\s*(कैसे|का)\s*(इस्तेमाल|उपयोग|चलाएं|चलती|काम|मदद)",
        r"(app|agribridge|website)\s*(kaise|kya)\s*(use|chalti|chalayein|karna|help)",
        r"(यह|ये)\s*(वेबसाइट|ऐप)\s*कैसे\s*(चलती|काम)",
    ]
    if is_app_help_query(clean_text) or any(re.search(pat, lower_text, re.IGNORECASE) for pat in app_help_patterns):
        return {
            "success": True,
            "intent": "app_help",
            "domain": "app",
            "topic": "app_help",
            "language": active_lang,
            "confidence": 0.95,
            "is_agriculture_related": True,
            "navigation_action": None,
            "detected_crop": crop_entity,
            "context": ctx,
            "language_switch": switched_lang,
        }

    # 6. Check for Follow-up Fertilizer Queries (e.g. "इसमें कौन सी खाद डालूं?", "what fertilizer for this?")
    fertilizer_followup_patterns = [
        r"(इसमें|इस\s*फसल\s*में|गेहूं|धान|फसल)\s*(में|को)?\s*(कौन\s*सी|क्या)\s*(खाद|उर्वरक|यूरिया|डीएपी|पोषक)",
        r"(खाद\s*कौन\s*सी\s*डालूं|खाद\s*क्या\s*डालें|कौन\s*सी\s*खाद\s*डालूं|कौन\s*सी\s*खाद\s*देनी\s*है|उर्वरक\s*क्या\s*डालें)",
        r"(isme|is\s*fasal\s*mein|gehu\s*mein)\s*(kaunsi|konsi|kya)\s*(khaad|khad|fertilizer)\s*(daalun|daalu|dale|daalein|deni)",
        r"(which|what)\s+fertilizer\s+(to\s+apply|for\s+this|should\s+i\s+add)",
    ]
    if any(re.search(pat, lower_text, re.IGNORECASE) for pat in fertilizer_followup_patterns):
        ctx["current_intent"] = "fertilizer"
        return {
            "success": True,
            "intent": "crop_guidance",
            "domain": "crop",
            "topic": "fertilizer",
            "language": active_lang,
            "confidence": 0.96,
            "is_agriculture_related": True,
            "detected_crop": crop_entity or ctx.get("crop"),
            "crop_age_days": ctx.get("crop_age_days"),
            "sub_intent": "fertilizer_followup",
            "context": ctx,
            "navigation_action": None,
            "language_switch": switched_lang,
        }

    # 7. Check for Follow-up Irrigation Queries (e.g. "अब पानी कब दूं?", "When to water next?")
    irrigation_followup_patterns = [
        r"(अब|फिर|अगला|अगली\s*बार|बाद\s*में)\s*(पानी|सिंचाई)\s*कब\s*(दूँ|दूं|देना|डालना|लगाना|करनी|करें|दें)",
        r"(पानी|सिंचाई)\s*(अब|फिर|अगली\s*बार|बाद\s*में)\s*कब\s*(दूँ|दूं|देना|डालना|लगाना|करनी|करें|दें)",
        r"(ab|phir|next|agla|agli)\s*(paani|pani|water|sinchai|irrigation)\s*(kab|du|doon|dena|daalun|daalna|lagayein|karein|karni|dein)",
        r"(paani|pani|sinchai)\s*(ab|phir|next|agla|agli)\s*(kab|du|doon|dena|daalun|daalna|lagayein|karein|karni|dein)",
        r"(when\s+to\s+water\s+next|next\s+irrigation|when\s+should\s+i\s+water\s+again|when\s+to\s+irrigate\s+next|water\s+next|irrigate\s+next)",
    ]
    if any(re.search(pat, lower_text, re.IGNORECASE) for pat in irrigation_followup_patterns):
        ctx["current_intent"] = "irrigation"
        return {
            "success": True,
            "intent": "irrigation",
            "domain": "farm",
            "topic": "irrigation",
            "language": active_lang,
            "confidence": 0.96,
            "is_agriculture_related": True,
            "detected_crop": crop_entity or ctx.get("crop"),
            "crop_age_days": ctx.get("crop_age_days"),
            "sub_intent": "irrigation_followup",
            "context": ctx,
            "navigation_action": None,
            "language_switch": switched_lang,
        }

    # 8A. Check for Explicit Today's Action Plan ("आज मेरी कार्य योजना क्या है?", "आज मुझे क्या करना चाहिए?")
    action_plan_patterns = [
        r"(कार्य\s*योजना|action\s*plan|आज\s*(मेरी\s*)?कार्य\s*योजना|आज\s*की\s*योजना|आज\s*(मुझे\s*)?क्या\s*करना\s*(है|चाहिए)|today'?s\s+action\s+plan|plan\s+for\s+today|what\s+should\s+i\s+do\s+today)",
        r"(aaj\s*(meri\s*)?karya\s*yojana|aaj\s*ka\s*plan|aaj\s*(mujhe\s*)?kya\s*karna\s*(hai|chahiye))",
    ]
    if any(re.search(pat, lower_text, re.IGNORECASE) for pat in action_plan_patterns):
        ctx["current_intent"] = "action_plan"
        return {
            "success": True,
            "intent": "action_plan",
            "domain": "planning",
            "topic": "crop_cultivation",
            "language": active_lang,
            "confidence": 0.96,
            "is_agriculture_related": True,
            "detected_crop": crop_entity or ctx.get("crop"),
            "crop_age_days": ctx.get("crop_age_days"),
            "sub_intent": "stage_action_plan",
            "context": ctx,
            "navigation_action": None,
            "language_switch": switched_lang,
        }

    # 8B. Check for Disease Follow-Up Queries (Treatment, Cause, Spread)
    disease_treatment_patterns = [
        r"(क्या\s*दवा\s*(डालूं|डालें|लगाएं|दें)|दवा\s*(बताइए|बताओ|क्या\s*है)|इसका\s*इलाज\s*कैसे\s*करें|इलाज\s*बताओ|रोकथाम\s*बताएं|क्या\s*उपचार\s*है)",
        r"(kya\s*dawa\s*(daalun|daalein|lagayein|dein)|dawa\s*(batao|bataiye|kya\s*hai)|iska\s*ilaj\s*kaise\s*karein|ilaj\s*batao|upchar\s*bataiye)",
        r"(what\s+medicine\s+to\s+(apply|spray|use)|how\s+to\s+treat\s+it|how\s+to\s+cure\s+this|treatment\s+for\s+this|what\s+should\s+i\s+spray|cure\s+for\s+this\s+disease)",
    ]
    disease_cause_patterns = [
        r"(यह\s*बीमारी\s*क्यों\s*(हुई|लगती\s*है|आई)|बीमारी\s*का\s*कारण\s*क्या\s*है|रोग\s*क्यों\s*लगा)",
        r"(yeh\s*bimari\s*kyu\s*(hui|lagti\s*hai|aayi)|bimari\s*ka\s*karan\s*kya\s*hai|rog\s*kyu\s*laga)",
        r"(why\s+did\s+this\s+disease\s+(occur|happen)|what\s+caused\s+this\s+disease|cause\s+of\s+this\s+disease|why\s+this\s+happened)",
    ]
    disease_spread_patterns = [
        r"(क्या\s*यह\s*(दूसरी|अन्य)\s*फसल\s*(में\s*)?भी\s*फैल\s*सकती\s*है|क्या\s*यह\s*बीमारी\s*फैलेगी|फैलाव\s*कैसे\s*रोकें)",
        r"(kya\s*yeh\s*(doosri|dusri|other)\s*fasal\s*(mein\s*)?bhi\s*fail\s*sakti\s*hai|kya\s*yeh\s*bimari\s*failegi|failne\s*se\s*kaise\s*rokein)",
        r"(can\s+this\s+spread\s+to\s+other\s+crops|will\s+it\s+spread|how\s+to\s+prevent\s+spreading|is\s+it\s+contagious)",
    ]

    if any(re.search(pat, lower_text, re.IGNORECASE) for pat in disease_cause_patterns):
        ctx["current_intent"] = "crop_disease"
        return {
            "success": True,
            "intent": "crop_disease",
            "domain": "crop_health",
            "topic": "crop_disease",
            "sub_intent": "disease_cause",
            "language": active_lang,
            "confidence": 0.96,
            "is_agriculture_related": True,
            "detected_crop": crop_entity or ctx.get("crop"),
            "crop_age_days": ctx.get("crop_age_days"),
            "context": ctx,
            "navigation_action": None,
            "language_switch": switched_lang,
        }

    if any(re.search(pat, lower_text, re.IGNORECASE) for pat in disease_spread_patterns):
        ctx["current_intent"] = "crop_disease"
        return {
            "success": True,
            "intent": "crop_disease",
            "domain": "crop_health",
            "topic": "crop_disease",
            "sub_intent": "disease_spread",
            "language": active_lang,
            "confidence": 0.96,
            "is_agriculture_related": True,
            "detected_crop": crop_entity or ctx.get("crop"),
            "crop_age_days": ctx.get("crop_age_days"),
            "context": ctx,
            "navigation_action": None,
            "language_switch": switched_lang,
        }

    if any(re.search(pat, lower_text, re.IGNORECASE) for pat in disease_treatment_patterns):
        ctx["current_intent"] = "crop_disease"
        return {
            "success": True,
            "intent": "crop_disease",
            "domain": "crop_health",
            "topic": "crop_disease",
            "sub_intent": "disease_treatment",
            "language": active_lang,
            "confidence": 0.96,
            "is_agriculture_related": True,
            "detected_crop": crop_entity or ctx.get("crop"),
            "crop_age_days": ctx.get("crop_age_days"),
            "context": ctx,
            "navigation_action": None,
            "language_switch": switched_lang,
        }

    # 8C. Check for General Follow-up / Next Step Queries ("अब क्या करूं?", "अगला कदम क्या है?")
    next_step_patterns = [
        r"(अब\s*(मुझे\s*)?क्या\s*करना\s*(है|चाहिए)|अगला\s*कदम\s*क्या\s*है|आगे\s*क्या\s*करें|अब\s*क्या\s*करूं)",
        r"(ab\s*(mujhe\s*)?kya\s*karna\s*hai|ab\s*kya\s*karun|ab\s*kya\s*karein|agla\s*kadam\s*kya\s*hai|aage\s*kya\s*karein|what\s+next|what\s+should\s+i\s+do\s+now|next\s+step)",
    ]
    if any(re.search(pat, lower_text, re.IGNORECASE) for pat in next_step_patterns):
        if ctx.get("current_intent") == "crop_disease" or ctx.get("detected_disease"):
            return {
                "success": True,
                "intent": "crop_disease",
                "domain": "crop_health",
                "topic": "crop_disease",
                "sub_intent": "disease_treatment",
                "language": active_lang,
                "confidence": 0.95,
                "is_agriculture_related": True,
                "detected_crop": crop_entity or ctx.get("crop"),
                "crop_age_days": ctx.get("crop_age_days"),
                "context": ctx,
                "navigation_action": None,
                "language_switch": switched_lang,
            }
        elif ctx.get("current_intent") == "irrigation":
            return {
                "success": True,
                "intent": "irrigation",
                "domain": "farm",
                "topic": "irrigation",
                "language": active_lang,
                "confidence": 0.95,
                "is_agriculture_related": True,
                "detected_crop": crop_entity or ctx.get("crop"),
                "crop_age_days": ctx.get("crop_age_days"),
                "context": ctx,
                "navigation_action": None,
                "language_switch": switched_lang,
            }
        elif ctx.get("current_intent") == "fertilizer":
            return {
                "success": True,
                "intent": "crop_guidance",
                "domain": "crop",
                "topic": "fertilizer",
                "language": active_lang,
                "confidence": 0.95,
                "is_agriculture_related": True,
                "detected_crop": crop_entity or ctx.get("crop"),
                "crop_age_days": ctx.get("crop_age_days"),
                "context": ctx,
                "navigation_action": None,
                "language_switch": switched_lang,
            }
        else:
            ctx["current_intent"] = "action_plan"
            return {
                "success": True,
                "intent": "action_plan",
                "domain": "planning",
                "topic": "crop_cultivation",
                "language": active_lang,
                "confidence": 0.95,
                "is_agriculture_related": True,
                "detected_crop": crop_entity or ctx.get("crop"),
                "crop_age_days": ctx.get("crop_age_days"),
                "sub_intent": "stage_action_plan",
                "context": ctx,
                "navigation_action": None,
                "language_switch": switched_lang,
            }

    # 9. Check for General Irrigation Query (Domain 4: irrigation)
    irrigation_patterns = [
        r"(मेरे\s+खेत|खेत|फसल|पौधों?)\s*(में|को)?\s*पानी\s*कब\s*(देना|डालना|दूँ|दूं|डालूँ|डालू|लगाना|लगाएं|लगाऊँ|लगाऊं|चाहिए)",
        r"पानी\s*कब\s*(देना|डालना|दूँ|दूं|डालूँ|डालू|लगाना|लगाएं|लगाऊँ|लगाऊं|करना)",
        r"(तो\s*क्या|क्या)\s*(आज|अभी)\s*पानी\s*(देना|डालना|दूँ|दूं|लगाना|चाहिए|दें)",
        r"(to\s*kya|kya)\s*(aaj|abhi)\s*(paani|pani)\s*(dena|daalun|lagana|chahiye|dein)",
        r"(should\s+i\s+water\s+today|should\s+i\s+irrigate\s+today|can\s+i\s+water\s+today)",
        r"(सिंचाई|सिचाई)\s*(कब|समय|करनी|करना|की\s*जरूरत|शेड्यूल)",
        r"खेत\s*की\s*(सिंचाई|सिचाई)",
        r"(बारिश|वर्षा|rain)\s*के\s*बाद\s*(खेत\s*में\s*)?पानी\s*(कब|देना|डालना|लगाना)",
        r"(when\s+(should\s+i|to)\s+water|water\s+my\s+field|how\s+much\s+water\s+for\s+my\s+crop|watering\s+schedule|irrigation\s+timing|when\s+to\s+irrigate)",
        r"(mere\s+khet\s+mein\s+)?(paani|pani)\s*kab\s*(dena|daalna|dalna|karna|daalu|daalun|lagana|de)",
        r"(sinchai|sinchaee|sinchayee)\s*kab\s*(karni|karna|hogi)",
        r"khet.*(pani|paani|sinchai|sinchaee|watering)",
        r"\b(irrigation|watering|irrigate)\b",
    ]
    if any(re.search(pat, lower_text, re.IGNORECASE) for pat in irrigation_patterns):
        ctx["current_intent"] = "irrigation"
        if not ctx.get("crop"):
            ctx["pending_field"] = "crop"
        elif ctx.get("crop_age_days") is None:
            ctx["pending_field"] = "crop_age"
        elif ctx.get("location") is None:
            ctx["pending_field"] = "location"
        else:
            ctx["pending_field"] = None
        return {
            "success": True,
            "intent": "irrigation",
            "domain": "farm",
            "topic": "irrigation",
            "language": active_lang,
            "confidence": 0.95,
            "is_agriculture_related": True,
            "detected_crop": crop_entity or ctx.get("crop"),
            "crop_age_days": ctx.get("crop_age_days"),
            "location": ctx.get("location"),
            "soil_moisture": ctx.get("soil_moisture"),
            "context": ctx,
            "navigation_action": None,
            "language_switch": switched_lang,
        }

    # 10. Check for Weather Query (Domain 5: weather)
    weather_patterns = [
        r"(will\s+it\s+rain|is\s+it\s+going\s+to\s+rain|weather\s+forecast|what\s+is\s+the\s+weather|temperature\s+tomorrow|rain\s+tomorrow|forecast\s+for)",
        r"(कल|आज|परसों)?\s*(बारिश|मौसम|तापमान|हवामान|वर्षा)\s*(होगी|होने\s*वाली|कैसा|कितना|आएगी|का\s*अनुमान|रहेगा|होगी\s*क्या|है\s*क्या)",
        r"(कल\s+बारिश\s+होगी|मौसम\s+कैसा\s+रहेगा|बारिश\s+होगी\s+क्या|आज\s+बारिश\s+होगी|बारिश\s+होने\s+वाली\s+है\s+क्या)",
        r"(kal\s+rain\s+hogi|kal\s+barish\s+hogi|mausam\s+kaisa|weather\s+kaisa|aaj\s+barish|rain\s+hogi\s+kya|barish\s+hone\s+wali\s+hai\s+kya|barish\s+hogi)",
        r"\b(weather|mausam|hawaaman|hawaan|forecast|rainfall|temperature)\b",
    ]
    if any(re.search(pat, lower_text, re.IGNORECASE) for pat in weather_patterns):
        ctx["current_intent"] = "weather"
        if not ctx.get("location"):
            ctx["pending_field"] = "location"
        else:
            ctx["pending_field"] = None
        return {
            "success": True,
            "intent": "weather",
            "domain": "weather",
            "topic": "weather",
            "language": active_lang,
            "confidence": 0.95,
            "is_agriculture_related": True,
            "detected_crop": crop_entity or ctx.get("crop"),
            "crop_age_days": ctx.get("crop_age_days"),
            "location": ctx.get("location"),
            "context": ctx,
            "navigation_action": None,
            "language_switch": switched_lang,
        }

    # 11. Check for Crop Disease & Pest Query (Domain 6: crop_disease)
    disease_patterns = [
        r"(leaves\s+have\s+spots|spots\s+on\s+leaves|crop\s+leaves\s+have\s+spots|what\s+disease|leaf\s+yellowing|yellow\s+leaves|fungal\s+infection|pest\s+attack|insects\s+eating|rot\s+in\s+stem|blight|dark\s+brown\s+spots|brown\s+spots|black\s+spots)",
        r"(पत्तियों|पत्ते|पत्ती|पौधों?|फसल)\s*(में|पर|की|pe|par|me)?\s*(पीले|काले|सफेद|भूरे|लाल)?\s*(दाग|धब्बे|पीलापन|कीड़ा|सड़न|फफूंद|छेद|बीमारी|रोग|लक्षण)",
        r"(पत्तियों\s+पर\s+दाग|पत्ते\s+पीले|फसल\s+में\s+बीमारी|रोग\s+लगा\s+है|बीमारी\s+लग\s+गई|कीड़ा\s+लगा\s+है|इल्ली|सुंडी|झुलसा|रतुआ|ब्लाइट)",
        r"(धब्बे|दाग|पीलापन|झुलसा|सड़न|फफूंद|बीमारी|रोग)\s*(दिख\s*रहे|लगे\s*हैं|लगी\s*है|हो\s*गया|आ\s*गया|है|क्या\s*है)",
        r"(pattiyon\s*(par|pe)?\s*(peele|kale|safed|brown)?\s*(daag|dhabbe|spots?)|patti\s*pe\s*spot|crop\s+leaves\s+have\s+spots|leaves\s+(par|pe)\s+spots|fasal\s+mein\s+bimari|keeda\s+lag\s+gaya|yellow\s+ho\s+rahi|kya\s+bimari\s+hai|bimari\s+lag\s+gayi)",
        r"\b(disease|blight|fungus|fungal|bimari|rog|keeda|keede|pests?|insects?|infestation|rust|leaf\s*spot)\b",
    ]
    if any(re.search(pat, lower_text, re.IGNORECASE) for pat in disease_patterns):
        ctx["current_intent"] = "crop_disease"
        if not ctx.get("detected_disease"):
            ctx["pending_field"] = "crop_image"
        return {
            "success": True,
            "intent": "crop_disease",
            "domain": "crop_health",
            "topic": "crop_disease",
            "language": active_lang,
            "confidence": 0.95,
            "is_agriculture_related": True,
            "detected_crop": crop_entity or ctx.get("crop"),
            "context": ctx,
            "navigation_action": None,
            "language_switch": switched_lang,
        }

    # 12. Check for Mandi & Market Prices Query (Domain 7: mandi)
    mandi_patterns = [
        r"(market\s+price|tomato\s+price|today'?s\s+market\s+price|mandi\s+rate|what\s+is\s+the\s+.*price|mandi\s+price|selling\s+rate|crop\s+price|wholesale\s+price)",
        r"(मंडी\s*में\s*(टमाटर|गेहूं|धान|फसल)?\s*(का\s*)?भाव|बाजार\s*भाव|दाम\s*क्या\s*है|एमएसपी|रेट\s*क्या\s*है|कीमत\s*क्या\s*है|भाव\s*क्या\s*है)",
        r"(mandi\s*(mein|me)?\s*(tamatar|tomato|gehu|dhan|aalu|aloo)?\s*(ka\s*)?bhav|market\s*price|aaj\s*ka\s*bhav|rate\s*kya\s*hai|daam\s*kya\s*hai|price\s*kya\s*hai)",
        r"\b(mandi|bhav|market\s+rate|msp)\b",
    ]
    if any(re.search(pat, lower_text, re.IGNORECASE) for pat in mandi_patterns):
        return {
            "success": True,
            "intent": "mandi",
            "domain": "market",
            "topic": "market",
            "language": active_lang,
            "confidence": 0.95,
            "is_agriculture_related": True,
            "detected_crop": crop_entity or ctx.get("crop"),
            "context": ctx,
            "navigation_action": None,
            "language_switch": switched_lang,
        }

    # 13. Check for Crop Guidance / Fertilizer / Nutrition Query (Domain 3: crop_guidance)
    crop_guidance_patterns = [
        r"(what\s+fertilizer|which\s+fertilizer|fertilizer\s+does\s+my|how\s+should\s+i\s+care\s+for\s+my\s+.*crop|crop\s+nutrition|urea\s+dose|npk\s+ratio|manure\s+for)",
        r"(गेहूं|धान|कपास|फसल)\s*(में|की)?\s*(कौन\s*सी\s*खाद|उर्वरक|देखभाल|यूरिया|डीएपी|एनपीके|पोषक\s*तत्व|खाद\s*डालें|खाद\s*कब)",
        r"(खाद\s*डालें|उर्वरक\s*डालें|खाद\s*कब\s*डालें|फसल\s*की\s*देखभाल)",
        r"(gehu|dhan|cotton|fasal)\s*(mein|me)?\s*(kaunsi|konsi)\s*(khaad|khad|fertilizer)\s*(daalun|dale|daalein)",
        r"\b(fertilizer|manure|urea|dap|npk|khaad|khad|urvarak)\b",
    ]
    if any(re.search(pat, lower_text, re.IGNORECASE) for pat in crop_guidance_patterns):
        ctx["current_intent"] = "crop_guidance"
        return {
            "success": True,
            "intent": "crop_guidance",
            "domain": "crop",
            "topic": "fertilizer",
            "language": active_lang,
            "confidence": 0.95,
            "is_agriculture_related": True,
            "detected_crop": crop_entity or ctx.get("crop"),
            "crop_age_days": ctx.get("crop_age_days"),
            "context": ctx,
            "navigation_action": None,
            "language_switch": switched_lang,
        }

    # 14. Check for Explicit Non-Agri Disqualification
    for pattern in NON_AGRI_PATTERNS:
        if re.search(pattern, lower_text, re.IGNORECASE) and not crop_entity:
            return {
                "success": True,
                "intent": "fallback",
                "domain": "general",
                "topic": "non_agriculture",
                "language": active_lang,
                "confidence": 0.90,
                "is_agriculture_related": False,
                "detected_crop": None,
                "context": ctx,
                "navigation_action": None,
                "language_switch": switched_lang,
            }

    # 15. Secondary Keyword-Score Topic Matching
    matched_topics: Dict[str, int] = {}
    for topic_name, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in lower_text)
        if score > 0:
            matched_topics[topic_name] = score

    if matched_topics:
        best_topic = max(matched_topics.items(), key=lambda x: x[1])[0]
        topic_to_intent_domain = {
            "irrigation": ("irrigation", "farm"),
            "fertilizer": ("crop_guidance", "crop"),
            "crop_disease": ("crop_disease", "crop_health"),
            "pest": ("crop_disease", "crop_health"),
            "weather": ("weather", "weather"),
            "market": ("mandi", "market"),
            "soil": ("farm_management", "farm"),
            "crop_cultivation": ("crop_guidance", "crop"),
            "government_scheme": ("farm_management", "farm"),
        }
        mapped_intent, mapped_domain = topic_to_intent_domain.get(best_topic, ("crop_guidance", "crop"))
        ctx["current_intent"] = mapped_intent
        return {
            "success": True,
            "intent": mapped_intent,
            "domain": mapped_domain,
            "topic": best_topic,
            "language": active_lang,
            "confidence": 0.85,
            "is_agriculture_related": True,
            "detected_crop": crop_entity or ctx.get("crop"),
            "crop_age_days": ctx.get("crop_age_days"),
            "context": ctx,
            "navigation_action": None,
            "language_switch": switched_lang,
        }

    # 16. Crop mentioned without specific sub-topic
    if crop_entity:
        return {
            "success": True,
            "intent": ctx.get("current_intent") or "crop_guidance",
            "domain": "crop",
            "topic": "crop_cultivation",
            "language": active_lang,
            "confidence": 0.80,
            "is_agriculture_related": True,
            "detected_crop": crop_entity,
            "crop_age_days": ctx.get("crop_age_days"),
            "context": ctx,
            "navigation_action": None,
            "language_switch": switched_lang,
        }

    # 17. Check for Greetings & Friendly Introductions
    is_greeting = any(
        re.search(rf"\b{re.escape(gw)}\b", lower_text, re.IGNORECASE) if gw.isascii() else gw in lower_text
        for gw in GREETING_KEYWORDS
    )
    if is_greeting:
        extracted_name = extract_farmer_name(clean_text)
        return {
            "success": True,
            "intent": "greeting",
            "domain": "general",
            "topic": "greeting",
            "farmer_name": extracted_name,
            "language": active_lang,
            "confidence": 0.95,
            "is_agriculture_related": True,
            "detected_crop": ctx.get("crop"),
            "context": ctx,
            "navigation_action": None,
            "language_switch": switched_lang,
        }

    # 18. Conversational Follow-up words (e.g. "aur paani?", "isme khaad?", "kab dalu?")
    followup_words = ["isme", "aur", "kab", "kya", "kitna", "batao", "why", "when", "how", "and", "then", "ಇದರಲ್ಲಿ", "ఇందులో", "यात", "ਇਸ ਵਿੱਚ"]
    if any(fw in lower_text for fw in followup_words):
        return {
            "success": True,
            "intent": ctx.get("current_intent") or "crop_guidance",
            "domain": "crop",
            "topic": "followup",
            "language": active_lang,
            "confidence": 0.70,
            "is_agriculture_related": True,
            "detected_crop": ctx.get("crop"),
            "crop_age_days": ctx.get("crop_age_days"),
            "context": ctx,
            "navigation_action": None,
            "language_switch": switched_lang,
        }

    # 19. Default Fallback
    return {
        "success": True,
        "intent": "fallback",
        "domain": "general",
        "topic": "non_agriculture",
        "language": active_lang,
        "confidence": 0.40,
        "is_agriculture_related": False,
        "detected_crop": ctx.get("crop"),
        "context": ctx,
        "navigation_action": None,
        "language_switch": switched_lang,
    }

