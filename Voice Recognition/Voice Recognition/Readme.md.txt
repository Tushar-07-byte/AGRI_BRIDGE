# 🎙️ AgriBridge Kisan Saathi — Voice Recognition & AI Assistant

This package contains the complete **Voice Recognition, Speech-to-Text (STT), Text-to-Speech (TTS), and Contextual AI Assistant (Kisan Saathi)** module.

---

## 📁 1. Where to Place the Files

Copy and replace the files into your existing project directories:

```text
AgriBridge/
├── backend/
│   └── app/
│       ├── routes/
│       │   └── voice.py                  <-- (Replace / Paste here)
│       └── services/
│           ├── speech_to_text.py         <-- (Replace / Paste here)
│           ├── text_to_speech.py         <-- (Replace / Paste here)
│           ├── saathi_service.py         <-- (Replace / Paste here)
│           ├── voice_service.py          <-- (Replace / Paste here)
│           └── agriculture_intent.py     <-- (Replace / Paste here)
│
└── frontend/
    ├── pages/
    │   └── voice-assistant.html          <-- (Replace / Paste here)
    ├── scripts/
    │   └── voice-assistant.js            <-- (Replace / Paste here)
    └── styles/
        └── voice-assistant.css           <-- (Replace / Paste here)

⚙️ 2. Install Required Python Packages
Make sure your virtual environment is activated and install these dependencies:

bash


cd backend
pip install gTTS httpx python-multipart fastapi uvicorn
🔑 3. Configure Environment Variable (.env)
Ensure you have a .env file inside the backend/ directory with a valid Gemini API key (used for high-accuracy multilingual Speech-to-Text):

env


GEMINI_API_KEY=your_gemini_api_key_here
Note: If you don't have a key, you can get a free one at Google AI Studio
.

🚀 4. How to Run & Test
Step 1: Start Backend Server
From the backend/ folder:

bash


uvicorn app.main:app --reload --port 8000
Verify routes are active by opening http://127.0.0.1:8000/docs in your browser.

Step 2: Open Voice Assistant in Frontend
Open frontend/pages/voice-assistant.html using VS Code Live Server (or open http://127.0.0.1:5500/frontend/pages/voice-assistant.html).
Allow Microphone Permissions when prompted by the browser.
🧪 5. Quick Test Queries to Try
Voice / Text Query in Hindi:

Speak/Type: "मेरे खेत में पानी कब देना है?"
Saathi will remember your crop context across follow-ups ("गेहूं", "25 दिन की है", etc.).
Weather-Aware Advisory:

Speak/Type: "बेंगलुरु के पास" 
→
→ Saathi checks live rain forecast before recommending irrigation.
Crop Disease Photo Diagnosis:

Click the 📷 icon, attach a crop leaf photo, and ask: "यह बीमारी कौन सी है?"
Follow-up: "अब क्या करूं?" / "क्या यह दूसरी फसल में फैलेगी?"
6:43 AM
