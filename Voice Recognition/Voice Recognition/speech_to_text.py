"""
AgriBridge Speech-to-Text (STT) Service

Converts farmer speech audio into localized text using Gemini Multimodal Audio API
with support for all 14 Indian languages + Hinglish.
"""

import os
import io
import uuid
import base64
import httpx
from pathlib import Path
from typing import Optional, Tuple


def get_gemini_api_key() -> str:
    return os.getenv("GEMINI_API_KEY", "").strip()


async def transcribe_audio(
    audio_bytes: bytes,
    content_type: str = "audio/webm",
    target_language: str = "hi"
) -> Tuple[bool, str]:
    """
    Transcribe speech audio to text in the target language.
    Returns: (success: bool, transcript: str)
    """
    if not audio_bytes or len(audio_bytes) < 100:
        print(f"[STT] Audio rejected: empty or too small ({len(audio_bytes) if audio_bytes else 0} bytes)")
        return False, "Audio is empty or too short."

    api_key = get_gemini_api_key()
    if not api_key:
        print("[STT] GEMINI_API_KEY is not configured.")
        return False, "GEMINI_API_KEY is not configured for voice transcription."

    # Clean and normalize MIME type for Gemini Multimodal API
    raw_mime = (content_type or "audio/webm").split(";")[0].strip().lower()
    if raw_mime in ["audio/m4a", "audio/x-m4a"]:
        clean_mime = "audio/mp4"
    elif raw_mime in ["audio/x-wav"]:
        clean_mime = "audio/wav"
    elif raw_mime in ["audio/x-opus"]:
        clean_mime = "audio/ogg"
    elif raw_mime in ["audio/webm", "audio/mp4", "audio/wav", "audio/ogg", "audio/mp3", "audio/mpeg"]:
        clean_mime = raw_mime
    else:
        clean_mime = "audio/webm"

    print(f"[STT] Transcribing audio: {len(audio_bytes)} bytes | MIME: {clean_mime} (raw: {content_type}) | Target lang: {target_language}")

    try:
        encoded_audio = base64.b64encode(audio_bytes).decode("utf-8")
        
        prompt = (
            f"Please accurately transcribe the speech in this audio file into text. "
            f"The speaker is an Indian farmer speaking in {target_language} (or Hindi, English, Hinglish, Punjabi, Marathi, Telugu, Tamil, Bengali, Gujarati). "
            f"Output ONLY the exact transcribed text, nothing else. Do not add explanations, quotes, or markdown formatting."
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": clean_mime,
                                "data": encoded_audio
                            }
                        },
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }

        # Try models in order: gemini-1.5-flash, gemini-2.0-flash, gemini-1.5-pro
        models_to_try = [
            "gemini-1.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-pro"
        ]

        async with httpx.AsyncClient(timeout=25.0) as client:
            for model_name in models_to_try:
                api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                try:
                    resp = await client.post(api_url, json=payload, headers={"Content-Type": "application/json"})
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            content = candidates[0].get("content", {})
                            parts = content.get("parts", [])
                            if parts:
                                transcript = parts[0].get("text", "").strip()
                                if transcript:
                                    print(f"[STT] Success via {model_name}: \"{transcript}\"")
                                    return True, transcript
                    else:
                        print(f"[STT] Model {model_name} HTTP {resp.status_code}: {resp.text[:200]}")
                except Exception as model_err:
                    print(f"[STT] Model {model_name} error: {model_err}")

        print("[STT] Could not transcribe speech from audio.")
        return False, "Could not recognize speech."

    except Exception as e:
        print(f"[STT] Exception during transcription: {str(e)}")
        return False, f"Speech recognition error: {str(e)}"

