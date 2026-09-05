// ============================================================
// AGRIBRIDGE MULTILINGUAL AGRICULTURAL VOICE ASSISTANT
// ============================================================

console.log("VOICE ASSISTANT STARTED");

// Backend API Base URL
const VA_API_URL = (function () {
    const loc = window.location;
    if (loc.origin && (loc.origin.includes("127.0.0.1") || loc.origin.includes("localhost"))) {
        return loc.origin;
    }
    return "http://127.0.0.1:8000";
})();

// Supported BCP-47 Speech Recognition Language Codes
const VA_BCP47 = {
    "en": "en-IN",
    "hi": "hi-IN",
    "bn": "bn-IN",
    "mr": "mr-IN",
    "te": "te-IN",
    "ta": "ta-IN",
    "gu": "gu-IN",
    "kn": "kn-IN",
    "ml": "ml-IN",
    "pa": "pa-IN",
    "or": "or-IN"
};

// Localized Greetings
const VA_GREETINGS = {
    "en": "Hello farmer! How can I help with your crops or farming today?",
    "hi": "नमस्ते किसान भाई! मैं आपकी खेती या फसल से जुड़े सवालों में कैसे मदद कर सकता हूँ?",
    "or": "ନମସ୍କାର ଚାଷୀ ଭାଇ! ଆଜି ଆପଣଙ୍କ ଚାଷ କିମ୍ବା ଫସଲ ସମ୍ବନ୍ଧୀୟ କି ପ୍ରଶ୍ନ ଅଛି?",
    "mr": "नमस्कार शेतकरी बंधूंनो! आज मी तुमच्या शेती किंवा पिकाबद्दल कशी मदत करू शकतो?",
    "bn": "নমস্কার কৃষক ভাই! আজ আপনার কৃষিকাজ বা ফসল সম্পর্কিত কী প্রশ্ন আছে?",
    "te": "నమస్కారం రైతు సోదరులారా! మీ పంట లేదా వ్యవసాయంలో నేను ఎలా సహాయపడగలను?",
    "ta": "வணக்கம் விவசாயி அவர்களே! இன்று உங்கள் பயிர் அல்லது விவசாயம் பற்றி என்ன கேட்க விரும்புகிறீர்கள்?",
    "kn": "ನಮಸ್ಕಾರ ರೈತ ಬಾಂಧವರೇ! ಇಂದು ನಿಮ್ಮ ಕೃಷಿ ಅಥವಾ ಬೆಳೆಯ ಬಗ್ಗೆ ನಾನು ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?",
    "ml": "നമസ്കാരം കർഷക സുഹൃത്തേ! ഇന്ന് നിങ്ങളുടെ കൃഷിയെക്കുറിച്ച് എന്ത് സംശയമാണ് ഉള്ളത്?",
    "gu": "નમસ્તે ખેડૂત મિત્ર! આજે હું તમારી ખેતી કે પાક બાબતે કેવી રીતે મદદ કરી શકું?",
    "pa": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ ਕਿਸਾਨ ਵੀਰੋ! ਅੱਜ ਤੁਹਾਡੀ ਖੇਤੀ ਜਾਂ ਫ਼ਸਲ ਬਾਰੇ ਮੈਂ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?"
};

let vaIsListening = false;
let vaRecognition = null;
let vaMediaRecorder = null;
let vaAudioChunks = [];
let vaLastAudioUrl = "";
let vaLastTextResponse = "";

// ============================================================
// INITIALIZATION
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
    initAssistantUI();
    initSpeechRecognition();
    bindEvents();
    syncGreeting();
    const currentLang = getSelectedLang();
    console.log("SELECTED LANGUAGE:", currentLang);
});

// Sync when language changes in navbar
window.addEventListener("languageChanged", (e) => {
    const newLang = getSelectedLang();
    console.log("SELECTED LANGUAGE:", newLang);
    syncGreeting();
    updateSpeechRecognitionLang();
});

function getFarmerName() {
    try {
        const profile = JSON.parse(localStorage.getItem("farmerProfile") || "{}");
        if (profile.name) return profile.name.trim();
        if (profile.farmerName) return profile.farmerName.trim();
        if (profile.farmer_name) return profile.farmer_name.trim();
    } catch (e) {}

    const directKeys = ["farmerName", "farmer_name", "userName", "name", "user_name"];
    for (const key of directKeys) {
        const val = localStorage.getItem(key);
        if (val && typeof val === "string" && val.trim()) {
            return val.trim();
        }
    }

    try {
        const userObj = JSON.parse(localStorage.getItem("user") || "{}");
        if (userObj.name) return userObj.name.trim();
        if (userObj.farmer_name) return userObj.farmer_name.trim();
        if (userObj.username) return userObj.username.trim();
    } catch (e) {}

    return "";
}

function getSelectedLang() {
    if (typeof getCurrentLanguage === "function") {
        return getCurrentLanguage();
    }
    return (localStorage.getItem("selectedLanguage") || "hi").toLowerCase();
}

function syncGreeting() {
    const lang = getSelectedLang();
    const name = getFarmerName();
    const welcomeEl = document.getElementById("assistant-welcome-message");
    if (welcomeEl) {
        if (name) {
            const localizedNamedGreetings = {
                "en": `Hello ${name}! Welcome to AgriBridge. How can I help you with your crops or farming today?`,
                "hi": `नमस्ते ${name} जी! एग्रीब्रिज (AgriBridge) में आपका स्वागत है। आज आपकी फसल या खेती में मैं कैसे मदद करूँ?`,
                "or": `ନମସ୍କାର ${name} ବାବୁ! ଏଗ୍ରିବ୍ରିଜକୁ ଆପଣଙ୍କୁ ସ୍ୱାଗତ। ଆଜି ଆପଣଙ୍କ ଫସଲ କିମ୍ବା ଚାଷ ସମ୍ବନ୍ଧୀୟ କି ସାହାଯ୍ୟ କରିପାରିବି?`,
                "mr": `नमस्कार ${name} जी! अ‍ॅग्रीब्रिजमध्ये आपले स्वागत आहे. आज आपल्या शेती किंवा पिकाबद्दल मी कशी मदत करू शकतो?`,
                "bn": `নমস্কার ${name} বাবু! এগ্রিব্রিজে আপনাকে স্বাগতম। আজ আপনার ফসল বা কৃষিকাজে আমি কীভাবে সাহায্য করতে পারি?`,
                "te": `నమస్కారం ${name} గారు! అగ్రిబ్రిడ్జ్‌కు స్వాగతం. ఈరోజు మీ పంట లేదా వ్యవసాయంలో నేను ఎలా సహాయపడగలను?`,
                "ta": `வணக்கம் ${name} அவர்களே! அக்ரிபிரிட்ஜிற்கு வரவேற்கிறோம். இன்று உங்கள் பயிர் அல்லது விவசாயம் பற்றி என்ன உதவி வேண்டும்?`,
                "kn": `ನಮಸ್ಕಾರ ${name} ಅವರೇ! ಅಗ್ರಿಬ್ರಿಡ್ಜ್‌ಗೆ ಸುಸ್ವಾಗತ. ಇಂದು ನಿಮ್ಮ ಬೆಳೆ ಅಥವಾ ಕೃಷಿಯ ಬಗ್ಗೆ ನಾನು ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?`,
                "ml": `നമസ്കാരം ${name}! അഗ്രിബ്രിഡ്ജിലേക്ക് സ്വാഗതം. ഇന്ന് നിങ്ങളുടെ വിളയെക്കുറിച്ചോ കൃഷിയെക്കുറിച്ചോ എന്ത് സഹായമാണ് വേണ്ടത്?`,
                "gu": `નમસ્તે ${name} ભાઈ! એગ્રીબ્રિજમાં આપનું સ્વાગત છે. આજે તમારા પાક કે ખેતી બાબતે હું કેવી રીતે મદદ કરી શકું?`,
                "pa": `ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ ${name} ਜੀ! ਐਗਰੀਬ੍ਰਿਜ ਵਿੱਚ ਤੁਹਾਡਾ ਸਵਾਗਤ ਹੈ। ਅੱਜ ਤੁਹਾਡੀ ਖੇਤੀ ਜਾਂ ਫ਼ਸਲ ਬਾਰੇ ਮੈਂ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?`
            };
            welcomeEl.textContent = localizedNamedGreetings[lang] || localizedNamedGreetings["en"];
        } else {
            welcomeEl.textContent = VA_GREETINGS[lang] || VA_GREETINGS["hi"] || VA_GREETINGS["en"];
        }
    }
}

function initAssistantUI() {
    try {
        const profile = JSON.parse(localStorage.getItem("farmerProfile") || "{}");
        const cropEl = document.getElementById("context-crop");
        const stageEl = document.getElementById("context-growth-stage");
        if (profile.crop && cropEl && !cropEl.value) cropEl.value = profile.crop;
        if (profile.growth_stage && stageEl && !stageEl.value) stageEl.value = profile.growth_stage;
    } catch (e) {}
}

function updateSpeechRecognitionLang() {
    if (vaRecognition) {
        const lang = getSelectedLang();
        const bcp47 = VA_BCP47[lang] || "hi-IN";
        try {
            vaRecognition.lang = bcp47;
        } catch (e) {}
    }
}

// ============================================================
// SPEECH RECOGNITION SETUP
// ============================================================

function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        console.warn("SPEECH ERROR: Web Speech API not supported in this browser. MediaRecorder fallback enabled.");
        return;
    }

    try {
        vaRecognition = new SpeechRecognition();
        vaRecognition.continuous = false;
        vaRecognition.interimResults = false;
        updateSpeechRecognitionLang();

        vaRecognition.onstart = () => {
            vaIsListening = true;
            updateListeningUI(true);
            setVoiceStatus("Listening... Speak your farming question.");
            console.log("MICROPHONE STARTED");
        };

        vaRecognition.onresult = (event) => {
            let transcript = "";
            if (event.results && event.results[0] && event.results[0][0]) {
                transcript = event.results[0][0].transcript;
            }
            console.log("TRANSCRIPT:", transcript);
            vaIsListening = false;
            updateListeningUI(false);
            if (transcript && transcript.trim()) {
                handleUserQuestion(transcript.trim());
            } else {
                setVoiceStatus("Sorry, I could not understand your voice. Please try again.");
            }
        };

        vaRecognition.onerror = (event) => {
            console.error("SPEECH ERROR:", event.error);
            vaIsListening = false;
            updateListeningUI(false);

            if (event.error === "not-allowed" || event.error === "permission-denied") {
                setVoiceStatus("Microphone permission is required. Please allow microphone access.");
                appendMessage("Microphone permission is required. Please allow microphone access in your browser settings.", "bot");
            } else if (event.error === "no-speech") {
                setVoiceStatus("No speech detected. Tap microphone and try again.");
            } else if (event.error === "network") {
                setVoiceStatus("Network recognition error. Please type your question below.");
            } else {
                setVoiceStatus("Sorry, I could not understand your voice. Please try again or type below.");
            }
        };

        vaRecognition.onend = () => {
            vaIsListening = false;
            updateListeningUI(false);
        };
    } catch (err) {
        console.error("SPEECH ERROR:", err);
    }
}

// ============================================================
// EVENT BINDINGS
// ============================================================

function bindEvents() {
    const micBtn = document.getElementById("voice-button");
    const stopBtn = document.getElementById("stop-voice-btn");
    const replayBtn = document.getElementById("replay-voice-btn");
    const form = document.getElementById("text-assistant-form");
    const input = document.getElementById("assistant-text-input");

    if (micBtn) {
        micBtn.addEventListener("click", toggleVoice);
    }

    if (stopBtn) {
        stopBtn.addEventListener("click", stopAllAudio);
    }

    if (replayBtn) {
        replayBtn.addEventListener("click", replayLastResponse);
    }

    if (form) {
        form.addEventListener("submit", (e) => {
            e.preventDefault();
            const q = input ? input.value.trim() : "";
            if (q) {
                input.value = "";
                handleUserQuestion(q);
            }
        });
    }
}

// ============================================================
// VOICE RECORDING TOGGLE
// ============================================================

async function toggleVoice() {
    if (vaIsListening) {
        stopListening();
    } else {
        startListening();
    }
}

async function startListening() {
    stopAllAudio();
    const lang = getSelectedLang();
    const bcp47 = VA_BCP47[lang] || "hi-IN";

    // Attempt browser Web Speech Recognition
    if (vaRecognition) {
        try {
            vaRecognition.lang = bcp47;
            vaRecognition.start();
            return;
        } catch (e) {
            console.warn("SPEECH ERROR: recognition.start() notice:", e);
        }
    }

    // MediaRecorder fallback for audio recording
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            vaAudioChunks = [];
            vaMediaRecorder = new MediaRecorder(stream);

            vaMediaRecorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) vaAudioChunks.push(event.data);
            };

            vaMediaRecorder.onstop = () => {
                stream.getTracks().forEach(t => t.stop());
                if (vaAudioChunks.length > 0) {
                    const audioBlob = new Blob(vaAudioChunks, { type: "audio/webm" });
                    uploadAudioQuestion(audioBlob);
                }
            };

            vaMediaRecorder.start();
            vaIsListening = true;
            updateListeningUI(true);
            setVoiceStatus("Listening... Speak your farming question.");
            console.log("MICROPHONE STARTED");
        } catch (err) {
            console.error("SPEECH ERROR: Microphone access error:", err);
            setVoiceStatus("Microphone permission is required. Please allow microphone access.");
            updateListeningUI(false);
        }
    } else {
        setVoiceStatus("Voice recording not supported in this browser. Please type your question.");
        updateListeningUI(false);
    }
}

function stopListening() {
    if (vaRecognition) {
        try { vaRecognition.stop(); } catch (e) {}
    }
    if (vaMediaRecorder && vaMediaRecorder.state !== "inactive") {
        try { vaMediaRecorder.stop(); } catch (e) {}
    }
    vaIsListening = false;
    updateListeningUI(false);
}

function updateListeningUI(listening) {
    const micBtn = document.getElementById("voice-button");
    const stopBtn = document.getElementById("stop-voice-btn");
    if (!micBtn) return;

    if (listening) {
        micBtn.classList.add("listening");
        micBtn.innerHTML = "⏹️";
        if (stopBtn) stopBtn.style.display = "inline-block";
    } else {
        micBtn.classList.remove("listening");
        micBtn.innerHTML = "🎙️";
    }
}

// ============================================================
// QUESTION PROCESSING (TEXT & VOICE)
// ============================================================

async function handleUserQuestion(questionText) {
    if (!questionText || !questionText.trim()) return;

    stopAllAudio();
    appendMessage(questionText, "user");
    setVoiceStatus("Thinking... Analyzing your farming question.");

    const cropEl = document.getElementById("context-crop");
    const stageEl = document.getElementById("context-growth-stage");
    const selectedLang = getSelectedLang();

    let farmProfile = {};
    try {
        farmProfile = JSON.parse(localStorage.getItem("farmerProfile") || "{}") || {};
    } catch (e) {
        farmProfile = {};
    }

    const farmerName = getFarmerName();
    if (farmerName) {
        farmProfile.farmer_name = farmerName;
        farmProfile.name = farmerName;
    }

    const payload = {
        message: questionText,
        text: questionText,
        language: selectedLang,
        language_code: selectedLang,
        crop: cropEl ? cropEl.value : "",
        growth_stage: stageEl ? stageEl.value : "",
        state: farmProfile.state || "",
        district: farmProfile.district || "",
        farm_profile: farmProfile
    };

    const endpointUrl = `${VA_API_URL}/api/voice/ask-text`;
    console.log("SENDING REQUEST:", endpointUrl, payload);

    try {
        const resp = await fetch(endpointUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        if (!resp.ok) {
            const errText = `HTTP Error ${resp.status}`;
            console.error("API ERROR:", errText);
            throw new Error(errText);
        }

        const data = await resp.json();
        console.log("API RESPONSE:", data);
        renderBotResponse(data);

    } catch (err) {
        console.error("BACKEND ERROR:", err);
        setVoiceStatus("AI advisory service is temporarily unavailable. Please try again.");
        appendMessage("AI advisory service is temporarily unavailable. Please make sure the backend server is running and try again.", "bot");
    }
}

async function uploadAudioQuestion(audioBlob) {
    setVoiceStatus("Thinking... Processing your voice audio.");

    const cropEl = document.getElementById("context-crop");
    const stageEl = document.getElementById("context-growth-stage");
    const selectedLang = getSelectedLang();

    let farmProfile = {};
    try {
        farmProfile = JSON.parse(localStorage.getItem("farmerProfile") || "{}") || {};
    } catch (e) {
        farmProfile = {};
    }
    const farmerName = getFarmerName();
    if (farmerName) {
        farmProfile.farmer_name = farmerName;
        farmProfile.name = farmerName;
    }

    const formData = new FormData();
    formData.append("audio", audioBlob, "farmer_audio.webm");
    formData.append("language", selectedLang);
    formData.append("language_code", selectedLang);
    formData.append("farm_profile", JSON.stringify(farmProfile));
    if (cropEl && cropEl.value) formData.append("crop", cropEl.value);
    if (stageEl && stageEl.value) formData.append("growth_stage", stageEl.value);

    const endpointUrl = `${VA_API_URL}/api/voice/ask`;
    console.log("SENDING REQUEST (AUDIO):", endpointUrl);

    try {
        const resp = await fetch(endpointUrl, {
            method: "POST",
            body: formData
        });

        if (!resp.ok) {
            const errText = `HTTP Error ${resp.status}`;
            console.error("API ERROR:", errText);
            throw new Error(errText);
        }

        const data = await resp.json();
        console.log("API RESPONSE:", data);

        if (data.transcript) {
            console.log("TRANSCRIPT:", data.transcript);
            appendMessage(data.transcript, "user");
        }
        renderBotResponse(data);

    } catch (err) {
        console.error("BACKEND ERROR:", err);
        setVoiceStatus("AI advisory service is temporarily unavailable. Please try again.");
        appendMessage("Error processing voice audio. Please try typing your question below.", "bot");
    }
}

// ============================================================
// RESPONSE RENDERING & TEXT-TO-SPEECH
// ============================================================

function renderBotResponse(data) {
    if (!data.success && data.error) {
        setVoiceStatus(data.error);
        appendMessage(data.error, "bot");
        return;
    }

    const text = data.response || data.response_text || data.message || "";
    console.log("AI RESPONSE:", text);

    vaLastTextResponse = text;
    vaLastAudioUrl = data.audio_url || "";

    appendMessage(text, "bot", data.topic, data.audio_url);
    setVoiceStatus("Tap the microphone and ask your farming question");

    const replayBtn = document.getElementById("replay-voice-btn");
    if (replayBtn) replayBtn.style.display = "inline-block";

    // Text-to-Speech Output
    if (data.audio_url) {
        playAudioFile(`${VA_API_URL}${data.audio_url}`);
    } else {
        speakBrowserText(text, getSelectedLang());
    }
}

function playAudioFile(url) {
    const player = document.getElementById("assistant-audio-player");
    if (!player) return;

    console.log("TTS STARTED (Audio URL):", url);
    player.src = url;
    player.play().catch(e => {
        console.warn("TTS ERROR: Autoplay prevented by browser. Click Listen button to hear response.", e);
        // Fallback to browser SpeechSynthesis if audio player blocked
        speakBrowserText(vaLastTextResponse, getSelectedLang());
    });
}

function speakBrowserText(text, lang) {
    if (!("speechSynthesis" in window) || !text) return;

    try {
        console.log("TTS STARTED (SpeechSynthesis):", text);
        window.speechSynthesis.cancel();

        const bcp47 = VA_BCP47[lang] || "hi-IN";
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = bcp47;
        utterance.rate = 0.95;

        // Attempt to find matching voice
        const voices = window.speechSynthesis.getVoices();
        const matchedVoice = voices.find(v => v.lang === bcp47 || v.lang.startsWith(lang));
        if (matchedVoice) {
            utterance.voice = matchedVoice;
        }

        utterance.onerror = (e) => {
            console.error("TTS ERROR:", e);
        };

        window.speechSynthesis.speak(utterance);
    } catch (err) {
        console.error("TTS ERROR:", err);
    }
}

function stopAllAudio() {
    const player = document.getElementById("assistant-audio-player");
    if (player) {
        player.pause();
        player.currentTime = 0;
    }
    if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
    }
    const stopBtn = document.getElementById("stop-voice-btn");
    if (stopBtn) stopBtn.style.display = "none";
}

function replayLastResponse() {
    if (vaLastAudioUrl) {
        playAudioFile(`${VA_API_URL}${vaLastAudioUrl}`);
    } else if (vaLastTextResponse) {
        speakBrowserText(vaLastTextResponse, getSelectedLang());
    }
}

// ============================================================
// UI HELPERS
// ============================================================

function setVoiceStatus(msg) {
    const el = document.getElementById("voice-status");
    if (el) el.textContent = msg;
}

function appendMessage(text, sender, topic = "", audioUrl = "") {
    const feed = document.getElementById("assistant-conversation");
    if (!feed || !text) return;

    const msgWrapper = document.createElement("div");
    msgWrapper.className = `assistant-message ${sender}-message`;

    const icon = document.createElement("div");
    icon.className = "message-icon";
    icon.textContent = sender === "user" ? "👨‍🌾" : "🤖";

    const content = document.createElement("div");
    content.className = "message-content";

    const strong = document.createElement("strong");
    strong.textContent = sender === "user" ? "You" : "AgriBridge";

    const p = document.createElement("p");
    p.textContent = text;

    content.appendChild(strong);
    content.appendChild(p);

    if (sender === "bot") {
        if (topic && topic !== "non_agriculture") {
            const tag = document.createElement("span");
            tag.className = "topic-tag";
            tag.textContent = `🌱 ${topic.replace(/_/g, " ")}`;
            content.appendChild(tag);
        }

        const listenBtn = document.createElement("button");
        listenBtn.type = "button";
        listenBtn.className = "speak-response-btn";
        listenBtn.textContent = "🔊 Listen";
        listenBtn.onclick = () => {
            if (audioUrl) {
                playAudioFile(`${VA_API_URL}${audioUrl}`);
            } else {
                speakBrowserText(text, getSelectedLang());
            }
        };
        content.appendChild(listenBtn);
    }

    msgWrapper.appendChild(icon);
    msgWrapper.appendChild(content);

    feed.appendChild(msgWrapper);
    feed.scrollTop = feed.scrollHeight;
}