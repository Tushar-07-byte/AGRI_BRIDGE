// ============================================================
// AGRIBRIDGE MASTER MULTILINGUAL AGRICULTURAL VOICE HELPLINE
// ============================================================

console.log("VOICE ASSISTANT INITIALIZED");

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
    "hinglish": "hi-IN",
    "pa": "pa-IN",
    "mr": "mr-IN",
    "bn": "bn-IN",
    "gu": "gu-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "kn": "kn-IN",
    "ml": "ml-IN",
    "or": "or-IN",
    "as": "as-IN",
    "ur": "ur-IN"
};

// Localized Greetings
// Saathi First Message (Adapted to user language)
// Meaning: “Namaste ji! Main Saathi hoon. Aap mujhse normal tarike se baat kar sakte hain. Jab bhi aapko meri zarurat ho, bas mujhse baat kijiye.”
const VA_GREETINGS = {
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
    "ur": "سلام جی! میں ساتھی ہوں۔ آپ مجھ سے عام طریقے سے بات کر سکتے ہیں۔ جب بھی آپ کو میری ضرورت ہو، بس مجھ سے بات کیجیے۔"
};

// Global State
let vaIsListening = false;
let vaIsSpeaking = false;
let vaIsProcessing = false;
let vaCurrentRequestId = 0;
let vaRecognition = null;
let vaMediaRecorder = null;
let vaAudioStream = null;
let vaAudioChunks = [];
let vaLastAudioUrl = "";
let vaSessionHistory = []; // Rolling multi-turn conversation memory
let vaSessionContext = {}; // Active personalized farm and crop context
let vaAttachedImageFile = null; // Attached leaf/crop photo

function getSupportedAudioMimeType() {
    const candidateTypes = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/mp4",
        "audio/ogg;codecs=opus",
        "audio/wav"
    ];
    if (typeof MediaRecorder !== "undefined" && typeof MediaRecorder.isTypeSupported === "function") {
        for (const mime of candidateTypes) {
            if (MediaRecorder.isTypeSupported(mime)) {
                return mime;
            }
        }
    }
    return "audio/webm";
}

// ============================================================
// INITIALIZATION
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
    initAssistantUI();
    initSpeechRecognition();
    bindEvents();
    initOnboardingModal();
    syncGreeting();
    setupAudioPlayerListeners();
});

// Sync when language selector changes in navbar
window.addEventListener("languageChanged", () => {
    syncGreeting();
    updateSpeechRecognitionLang();
});

function getFarmerName() {
    const directVaName = localStorage.getItem("va_farmer_name");
    if (directVaName && directVaName.trim()) {
        return directVaName.trim();
    }

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
        const userObj = JSON.parse(localStorage.getItem("agribridge_user") || localStorage.getItem("user") || "{}");
        if (userObj.name) return userObj.name.trim();
        if (userObj.farmer_name) return userObj.farmer_name.trim();
    } catch (e) {}

    return "";
}

function getDetailPreference() {
    return localStorage.getItem("va_detail_preference") || "simple";
}

function initOnboardingModal() {
    const modal = document.getElementById("va-onboarding-modal");
    const form = document.getElementById("va-onboarding-form");
    const nameInput = document.getElementById("va-input-name");
    const radioCards = document.querySelectorAll(".va-pref-card");

    if (!modal || !form) return;

    // Check if farmer has already completed first-time onboarding
    const alreadyOnboarded = localStorage.getItem("va_onboarded") === "true";
    if (!alreadyOnboarded) {
        const existingName = getFarmerName();
        if (nameInput && existingName) {
            nameInput.value = existingName;
        }
        modal.style.display = "flex";
    }

    // Radio card toggle styling
    radioCards.forEach(card => {
        const radio = card.querySelector("input[type='radio']");
        card.addEventListener("click", () => {
            radioCards.forEach(c => c.classList.remove("active"));
            card.classList.add("active");
            if (radio) radio.checked = true;
        });
    });

    form.addEventListener("submit", (e) => {
        e.preventDefault();
        const enteredName = nameInput ? nameInput.value.trim() : "";
        const selectedRadio = document.querySelector("input[name='va-style-pref']:checked");
        const prefStyle = selectedRadio ? selectedRadio.value : "simple";

        if (enteredName) {
            localStorage.setItem("va_farmer_name", enteredName);
        }
        localStorage.setItem("va_detail_preference", prefStyle);
        localStorage.setItem("va_onboarded", "true");

        modal.style.display = "none";
        syncGreeting();
    });
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
            welcomeEl.textContent = `Namaste ${name} ji! ` + (VA_GREETINGS[lang] || VA_GREETINGS["hi"]);
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

        const presetQuery = localStorage.getItem("voiceAssistantPresetQuery");
        if (presetQuery) {
            localStorage.removeItem("voiceAssistantPresetQuery");
            const input = document.getElementById("assistant-text-input");
            if (input) input.value = presetQuery;
            setTimeout(() => {
                if (typeof handleUserQuestion === "function") {
                    handleUserQuestion(presetQuery);
                }
            }, 400);
        }
    } catch (e) {}
}

function setupAudioPlayerListeners() {
    const player = document.getElementById("assistant-audio-player");
    if (!player) return;

    player.onplay = () => {
        vaIsSpeaking = true;
        setAssistantState("SPEAKING");
    };

    player.onended = () => {
        vaIsSpeaking = false;
        setAssistantState("IDLE");
    };

    player.onerror = () => {
        vaIsSpeaking = false;
        setAssistantState("IDLE");
    };
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
// SPEECH RECOGNITION (STT) SETUP
// ============================================================

function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        console.warn("SPEECH NOTICE: Web Speech API not supported. MediaRecorder audio fallback active.");
        return;
    }

    try {
        vaRecognition = new SpeechRecognition();
        vaRecognition.continuous = false;
        vaRecognition.interimResults = false;
        updateSpeechRecognitionLang();

        vaRecognition.onstart = () => {
            vaIsListening = true;
            setAssistantState("LISTENING");
            console.log("MICROPHONE STARTED");
        };

        vaRecognition.onresult = (event) => {
            let transcript = "";
            if (event.results && event.results[0] && event.results[0][0]) {
                transcript = event.results[0][0].transcript;
            }
            console.log("TRANSCRIPT DETECTED:", transcript);
            vaIsListening = false;
            if (transcript && transcript.trim()) {
                handleUserQuestion(transcript.trim());
            } else {
                setAssistantState("IDLE");
                setVoiceStatus("Could not understand clearly. Please tap the mic and try again.");
            }
        };

        vaRecognition.onerror = (event) => {
            console.error("SPEECH ERROR:", event.error);
            vaIsListening = false;
            setAssistantState("IDLE");

            if (event.error === "not-allowed" || event.error === "permission-denied") {
                setVoiceStatus("Microphone permission denied. You can type your question below.");
                appendMessage("Microphone permission was denied. Please allow microphone access in your browser or use the text box below.", "bot");
            } else if (event.error === "no-speech") {
                setVoiceStatus("No speech detected. Tap microphone and ask your question.");
            } else {
                setVoiceStatus("Could not hear clearly. Please tap the mic and ask again or type below.");
            }
        };

        vaRecognition.onend = () => {
            vaIsListening = false;
            if (!vaIsSpeaking) {
                setAssistantState("IDLE");
            }
        };
    } catch (err) {
        console.error("SPEECH INIT ERROR:", err);
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
        micBtn.addEventListener("click", () => {
            if (vaIsProcessing) {
                console.log("[FRONTEND] Request in progress, ignoring mic click");
                return;
            }
            // INTERRUPTIBLE VOICE: If speaking, clicking mic immediately stops TTS and starts listening
            if (vaIsSpeaking) {
                stopAllAudio();
                startListening();
            } else if (vaIsListening) {
                stopListening();
            } else {
                startListening();
            }
        });
    }

    if (stopBtn) {
        stopBtn.addEventListener("click", stopAllAudio);
    }

    if (replayBtn) {
        replayBtn.addEventListener("click", replayLastResponse);
    }

    const attachImgBtn = document.getElementById("attach-image-btn");
    const imgInput = document.getElementById("assistant-image-input");
    const removeImgBtn = document.getElementById("remove-image-btn");
    const imgPreviewBar = document.getElementById("image-preview-bar");
    const imgPreviewName = document.getElementById("image-preview-name");

    if (attachImgBtn && imgInput) {
        attachImgBtn.addEventListener("click", () => {
            imgInput.click();
        });
    }

    if (imgInput) {
        imgInput.addEventListener("change", () => {
            if (imgInput.files && imgInput.files[0]) {
                vaAttachedImageFile = imgInput.files[0];
                if (imgPreviewBar && imgPreviewName) {
                    imgPreviewName.textContent = `Attached photo: ${vaAttachedImageFile.name}`;
                    imgPreviewBar.style.display = "flex";
                }
            }
        });
    }

    if (removeImgBtn) {
        removeImgBtn.addEventListener("click", () => {
            vaAttachedImageFile = null;
            if (imgInput) imgInput.value = "";
            if (imgPreviewBar) imgPreviewBar.style.display = "none";
        });
    }

    if (form) {
        form.addEventListener("submit", (e) => {
            e.preventDefault();
            if (vaIsProcessing) return;
            const q = input ? input.value.trim() : "";
            if (q || vaAttachedImageFile) {
                if (input) input.value = "";
                const imgToSend = vaAttachedImageFile;
                vaAttachedImageFile = null;
                if (imgInput) imgInput.value = "";
                if (imgPreviewBar) imgPreviewBar.style.display = "none";
                handleUserQuestion(q || "कृपया इस फोटो की जांच करके बीमारी बताएं।", imgToSend);
            }
        });
    }
}

// Quick Suggestion Trigger
window.triggerQuickPrompt = function (promptText) {
    if (!promptText || vaIsProcessing) return;
    stopAllAudio();
    handleUserQuestion(promptText);
};

// ============================================================
// VOICE RECORDING & INTERRUPT LOGIC
// ============================================================

async function startListening() {
    if (vaIsProcessing) return;
    stopAllAudio();

    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            vaAudioStream = stream;
            vaAudioChunks = [];

            const mimeType = getSupportedAudioMimeType();
            try {
                vaMediaRecorder = new MediaRecorder(stream, { mimeType: mimeType });
            } catch (err) {
                console.warn("[FRONTEND] Failed initializing MediaRecorder with preferred mimeType, falling back:", err);
                vaMediaRecorder = new MediaRecorder(stream);
            }

            vaMediaRecorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) {
                    vaAudioChunks.push(event.data);
                }
            };

            vaMediaRecorder.onstop = () => {
                if (vaAudioStream) {
                    vaAudioStream.getTracks().forEach(t => t.stop());
                    vaAudioStream = null;
                }
                console.log("[FRONTEND] Recording stopped");
                if (vaAudioChunks.length > 0) {
                    const actualMime = vaMediaRecorder.mimeType || mimeType || "audio/webm";
                    const audioBlob = new Blob(vaAudioChunks, { type: actualMime });
                    console.log(`[FRONTEND] Audio blob: size=${audioBlob.size} bytes, type=${audioBlob.type}`);
                    uploadAudioQuestion(audioBlob);
                } else {
                    console.warn("[FRONTEND] No audio chunks recorded.");
                    setAssistantState("IDLE");
                }
            };

            vaMediaRecorder.start();
            vaIsListening = true;
            setAssistantState("LISTENING");
            console.log("[FRONTEND] Recording started");
        } catch (err) {
            console.error("[FRONTEND] Microphone access error:", err);
            setVoiceStatus("Microphone permission required. Please type your question below.");
            setAssistantState("IDLE");
        }
    } else {
        setVoiceStatus("Voice recording not supported in this browser. Please type your question.");
        setAssistantState("IDLE");
    }
}

function stopListening() {
    if (vaMediaRecorder && vaMediaRecorder.state !== "inactive") {
        try {
            vaMediaRecorder.stop();
        } catch (e) {
            console.error("[FRONTEND] Error stopping MediaRecorder:", e);
        }
    }
    vaIsListening = false;
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
    vaIsSpeaking = false;
    setAssistantState("IDLE");
}

// ============================================================
// VISUAL STATE MACHINE
// ============================================================

function setAssistantState(state) {
    const micBtn = document.getElementById("voice-button");
    const pulseWrapper = document.getElementById("pulse-wrapper");
    const stopBtn = document.getElementById("stop-voice-btn");
    const replayBtn = document.getElementById("replay-voice-btn");

    if (!micBtn) return;

    micBtn.classList.remove("listening", "thinking", "speaking");
    if (pulseWrapper) pulseWrapper.classList.remove("pulse-red", "pulse-amber", "pulse-green");

    if (state === "LISTENING") {
        micBtn.classList.add("listening");
        if (pulseWrapper) pulseWrapper.classList.add("pulse-red");
        micBtn.innerHTML = "🔴";
        setVoiceStatus("🎙️ Listening... Speak naturally to Saathi in any language");
        if (stopBtn) stopBtn.style.display = "none";
    } else if (state === "PROCESSING") {
        micBtn.classList.add("thinking");
        if (pulseWrapper) pulseWrapper.classList.add("pulse-amber");
        micBtn.innerHTML = "⏳";
        setVoiceStatus("Thinking... Connecting with Saathi");
        if (stopBtn) stopBtn.style.display = "none";
    } else if (state === "SPEAKING") {
        micBtn.classList.add("speaking");
        if (pulseWrapper) pulseWrapper.classList.add("pulse-green");
        micBtn.innerHTML = "🔊";
        setVoiceStatus("Saathi is speaking... (Tap mic anytime to interrupt)");
        if (stopBtn) stopBtn.style.display = "inline-block";
        if (replayBtn) replayBtn.style.display = "inline-block";
    } else { // IDLE
        micBtn.innerHTML = "🎙️";
        setVoiceStatus("Tap the microphone and speak naturally to Saathi in any language");
        if (stopBtn) stopBtn.style.display = "none";
    }
}

function setVoiceStatus(msg) {
    const el = document.getElementById("voice-status");
    if (el) el.textContent = msg;
}

// ============================================================
// QUESTION PROCESSING (MULTI-TURN ROLLING CONTEXT)
// ============================================================

async function handleUserQuestion(questionText, imageFile = null) {
    if ((!questionText || !questionText.trim()) && !imageFile) return;
    if (vaIsProcessing) return;

    stopAllAudio();
    vaIsProcessing = true;
    const thisRequestId = ++vaCurrentRequestId;
    
    let displayMsg = questionText;
    if (imageFile) {
        displayMsg = questionText ? `📷 [Photo Attached] ${questionText}` : `📷 [Photo Attached]`;
    }
    appendMessage(displayMsg, "user");
    setAssistantState("PROCESSING");

    // Add to session history
    vaSessionHistory.push({ role: "user", text: questionText || "कृपया इस फोटो की जांच करें।" });
    if (vaSessionHistory.length > 10) {
        vaSessionHistory = vaSessionHistory.slice(-10);
    }

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
    const detailPref = getDetailPreference();
    if (farmerName) {
        farmProfile.farmer_name = farmerName;
        farmProfile.name = farmerName;
    }

    const endpointUrl = `${VA_API_URL}/api/voice/saathi`;

    try {
        let resp;
        if (imageFile) {
            const formData = new FormData();
            formData.append("image", imageFile, imageFile.name || "crop_leaf.jpg");
            if (questionText) formData.append("text", questionText);
            formData.append("language", selectedLang);
            if (farmerName) formData.append("farmer_name", farmerName);
            formData.append("history", JSON.stringify(vaSessionHistory));
            if (vaSessionContext && Object.keys(vaSessionContext).length > 0) {
                formData.append("context", JSON.stringify(vaSessionContext));
            }
            if (farmProfile && Object.keys(farmProfile).length > 0) {
                formData.append("farm_context", JSON.stringify(farmProfile));
            }
            formData.append("mode", "saathi");
            formData.append("assistant", "saathi");
            formData.append("current_page", "voice-assistant");
            formData.append("screen_name", "Voice Farming Assistant");
            formData.append("available_buttons", JSON.stringify(["Dashboard", "Crop Monitoring", "AI Crop Scan", "Marketplace", "Weather", "Voice AI", "Command Center"]));

            resp = await fetch(endpointUrl, {
                method: "POST",
                body: formData
            });
        } else {
            const payload = {
                message: questionText,
                text: questionText,
                language: selectedLang,
                farmer_name: farmerName,
                history: vaSessionHistory,
                context: vaSessionContext,
                farm_info: farmProfile,
                farm_context: farmProfile,
                mode: "saathi",
                assistant: "saathi",
                current_page: "voice-assistant",
                screen_name: "Voice Farming Assistant",
                available_buttons: ["Dashboard", "Crop Monitoring", "AI Crop Scan", "Marketplace", "Weather", "Voice AI", "Command Center"]
            };

            resp = await fetch(endpointUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
        }

        if (!resp.ok) {
            throw new Error(`HTTP Error ${resp.status}`);
        }

        const data = await resp.json();

        if (thisRequestId !== vaCurrentRequestId) {
            console.warn(`[FRONTEND] Stale text response discarded for request ${thisRequestId}`);
            return;
        }

        renderBotResponse(data);

    } catch (err) {
        if (thisRequestId !== vaCurrentRequestId) return;
        console.error("BACKEND ERROR:", err);
        setAssistantState("IDLE");
        setVoiceStatus("Saathi service temporarily unavailable. Please try again.");
        appendMessage("Saathi is temporarily unavailable. Please make sure the backend server is running and try again.", "bot");
    } finally {
        if (thisRequestId === vaCurrentRequestId) {
            vaIsProcessing = false;
        }
    }
}

async function uploadAudioQuestion(audioBlob) {
    vaIsProcessing = true;
    const thisRequestId = ++vaCurrentRequestId;
    setAssistantState("PROCESSING");

    const selectedLang = getSelectedLang();
    const farmerName = getFarmerName();

    const formData = new FormData();
    const filename = (audioBlob.type && audioBlob.type.includes("mp4")) ? "farmer_audio.mp4" : "farmer_audio.webm";
    formData.append("audio", audioBlob, filename);
    if (selectedLang) formData.append("language", selectedLang);
    formData.append("history", JSON.stringify(vaSessionHistory));
    if (vaSessionContext && Object.keys(vaSessionContext).length > 0) {
        formData.append("context", JSON.stringify(vaSessionContext));
    }
    if (farmerName) formData.append("farmer_name", farmerName);
    formData.append("mode", "saathi");
    formData.append("assistant", "saathi");
    formData.append("current_page", "voice-assistant");
    formData.append("screen_name", "Voice Farming Assistant");
    formData.append("available_buttons", JSON.stringify(["Dashboard", "Crop Monitoring", "AI Crop Scan", "Marketplace", "Weather", "Voice AI", "Command Center"]));

    console.log(`[FRONTEND] FormData fields: audio (${filename}, ${audioBlob.size} bytes, ${audioBlob.type}), language=${selectedLang}, farmer_name=${farmerName}, mode=saathi, history length=${vaSessionHistory.length}`);

    const endpointUrl = `${VA_API_URL}/api/voice/saathi`;

    try {
        const resp = await fetch(endpointUrl, {
            method: "POST",
            body: formData
        });

        if (!resp.ok) {
            throw new Error(`HTTP Error ${resp.status}`);
        }

        const data = await resp.json();

        if (thisRequestId !== vaCurrentRequestId) {
            console.warn(`[FRONTEND] Stale response discarded. Current request is ${vaCurrentRequestId}, got response for ${thisRequestId}`);
            return;
        }

        console.log("[FRONTEND] Received API response:", data);
        console.log(`[FRONTEND] Transcript returned by backend: "${data.transcript || ''}"`);
        console.log(`[FRONTEND] Final answer displayed: "${data.response || data.response_text || ''}"`);

        if (data.transcript && data.transcript.trim()) {
            appendMessage(data.transcript.trim(), "user");
            vaSessionHistory.push({ role: "user", text: data.transcript.trim() });
        }

        renderBotResponse(data);

    } catch (err) {
        if (thisRequestId !== vaCurrentRequestId) return;
        console.error("[FRONTEND] BACKEND AUDIO ERROR:", err);
        setAssistantState("IDLE");
        setVoiceStatus("Error processing voice. Please try typing your question below.");
        appendMessage("Error processing voice audio. Please try typing your question below.", "bot");
    } finally {
        if (thisRequestId === vaCurrentRequestId) {
            vaIsProcessing = false;
        }
    }
}

// ============================================================
// RESPONSE RENDERING & TEXT-TO-SPEECH
// ============================================================

function renderBotResponse(data) {
    if (!data.success && data.error) {
        setAssistantState("IDLE");
        setVoiceStatus(data.error);
        appendMessage(data.error, "bot");
        return;
    }

    const text = data.response || data.response_text || data.message || "";
    vaLastTextResponse = text;
    vaLastAudioUrl = data.audio_url || "";

    // Add bot response to rolling history
    vaSessionHistory.push({ role: "assistant", text: text });

    // Merge and persist updated context
    if (data.context && typeof data.context === "object") {
        vaSessionContext = Object.assign({}, vaSessionContext, data.context);
    }

    // Sync detected crop back to dropdown if user didn't have one selected
    const activeCrop = (data.context && data.context.crop) || data.detected_crop;
    if (activeCrop) {
        const cropEl = document.getElementById("context-crop");
        if (cropEl && !cropEl.value) {
            cropEl.value = activeCrop;
        }
    }

    appendMessage(text, "bot", data.topic, data.audio_url, data.navigation_action, data.language_name || data.language);

    // Text-to-Speech Output
    if (data.audio_url) {
        playAudioFile(`${VA_API_URL}${data.audio_url}`);
    } else {
        speakBrowserText(text, data.language || getSelectedLang());
    }
}

function playAudioFile(url) {
    const player = document.getElementById("assistant-audio-player");
    if (!player) return;

    player.src = url;
    player.play().catch(e => {
        console.warn("Autoplay notice:", e);
        speakBrowserText(vaLastTextResponse, getSelectedLang());
    });
}

function speakBrowserText(text, lang) {
    if (!("speechSynthesis" in window) || !text) {
        setAssistantState("IDLE");
        return;
    }

    try {
        window.speechSynthesis.cancel();

        const bcp47 = VA_BCP47[lang] || "hi-IN";
        const cleanText = text.replace(/[\*\#\-\_]/g, " ").replace(/\s+/g, " ").trim();
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.lang = bcp47;
        utterance.rate = 0.92;

        utterance.onstart = () => {
            vaIsSpeaking = true;
            setAssistantState("SPEAKING");
        };

        utterance.onend = () => {
            vaIsSpeaking = false;
            setAssistantState("IDLE");
        };

        utterance.onerror = () => {
            vaIsSpeaking = false;
            setAssistantState("IDLE");
        };

        const voices = window.speechSynthesis.getVoices();
        const matchedVoice = voices.find(v => v.lang === bcp47 || v.lang.startsWith(lang));
        if (matchedVoice) {
            utterance.voice = matchedVoice;
        }

        window.speechSynthesis.speak(utterance);
    } catch (err) {
        console.error("SpeechSynthesis error:", err);
        setAssistantState("IDLE");
    }
}

function replayLastResponse() {
    if (vaLastAudioUrl) {
        playAudioFile(`${VA_API_URL}${vaLastAudioUrl}`);
    } else if (vaLastTextResponse) {
        speakBrowserText(vaLastTextResponse, getSelectedLang());
    }
}

// ============================================================
// UI MESSAGE RENDERING
// ============================================================

function appendMessage(text, sender, topic = "", audioUrl = "", navAction = null, langName = "") {
    const feed = document.getElementById("assistant-conversation");
    if (!feed || !text) return;

    const msgWrapper = document.createElement("div");
    msgWrapper.className = `assistant-message ${sender}-message`;

    const icon = document.createElement("div");
    icon.className = "message-icon";
    icon.textContent = sender === "user" ? "👨‍🌾" : "🤝";

    const content = document.createElement("div");
    content.className = "message-content";

    const strong = document.createElement("strong");
    strong.textContent = sender === "user" ? (getFarmerName() || "You") : "Saathi (साथी)";

    const p = document.createElement("p");
    p.textContent = text;

    content.appendChild(strong);
    content.appendChild(p);

    if (sender === "bot") {
        const metaRow = document.createElement("div");
        metaRow.className = "message-meta-row";

        if (langName) {
            const langTag = document.createElement("span");
            langTag.className = "topic-tag";
            langTag.style.background = "#e8f5e9";
            langTag.style.color = "#2e7d32";
            langTag.textContent = `🌐 ${langName}`;
            metaRow.appendChild(langTag);
        }

        const listenBtn = document.createElement("button");
        listenBtn.type = "button";
        listenBtn.className = "speak-response-btn";
        listenBtn.innerHTML = "🔊 Listen Again";
        listenBtn.onclick = () => {
            if (audioUrl) {
                playAudioFile(`${VA_API_URL}${audioUrl}`);
            } else {
                speakBrowserText(text, getSelectedLang());
            }
        };
        metaRow.appendChild(listenBtn);
        content.appendChild(metaRow);

        // App Navigation Card
        if (navAction && navAction.target) {
            const navCard = document.createElement("div");
            navCard.className = "voice-nav-card";
            navCard.innerHTML = `
                <div class="nav-card-info">
                    <span class="nav-card-icon">🚀</span>
                    <span>Ready to open <strong>${navAction.label || 'Page'}</strong></span>
                </div>
                <a href="${navAction.target}" class="nav-card-btn">
                    Open ${navAction.label || 'Page'} →
                </a>
            `;
            content.appendChild(navCard);
        }
    }

    msgWrapper.appendChild(icon);
    msgWrapper.appendChild(content);

    feed.appendChild(msgWrapper);
    feed.scrollTop = feed.scrollHeight;
}