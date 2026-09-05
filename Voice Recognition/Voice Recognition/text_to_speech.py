"""
AgriBridge Text-to-Speech (TTS) Master Service

Converts agricultural response text to clear, natural spoken audio across 14 Indian
languages + Hinglish with markdown sanitization and safe file management.
"""

import os
import re
import time
import uuid
import hashlib
from pathlib import Path
from typing import Optional, Tuple
from gtts import gTTS

BACKEND_DIR = Path(__file__).resolve().parents[2]
AUDIO_DIR = BACKEND_DIR / "uploads" / "voice_audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Direct & Acoustic Fallback mapping for gTTS
GTTS_LANG_MAP = {
    "en": "en",
    "hi": "hi",
    "hinglish": "hi",
    "mr": "mr",
    "bn": "bn",
    "te": "te",
    "ta": "ta",
    "kn": "kn",
    "ml": "ml",
    "gu": "gu",
    "pa": "pa",
    "ur": "ur",
    "as": "bn",  # Assamese acoustic fallback
    "or": "hi",  # Odia acoustic fallback
}


def sanitize_text_for_speech(text: str) -> str:
    """
    Remove markdown symbols, bullet points, headers, bracketed links,
    and JSON tokens so speech synthesis sounds natural and human.
    """
    if not text:
        return ""

    # Remove code blocks and inline code
    t = re.sub(r"```[\s\S]*?```", "", text)
    t = re.sub(r"`([^`]+)`", r"\1", t)

    # Remove headers (# Title)
    t = re.sub(r"^#{1,6}\s*", "", t, flags=re.MULTILINE)

    # Remove markdown bold/italics (**, *, __, _)
    t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)
    t = re.sub(r"\*([^*]+)\*", r"\1", t)
    t = re.sub(r"__([^_]+)__", r"\1", t)
    t = re.sub(r"_([^_]+)_", r"\1", t)

    # Convert bullet points / numbered lists to natural speech pauses
    t = re.sub(r"^\s*[-*•]\s*", ". ", t, flags=re.MULTILINE)
    t = re.sub(r"^\s*\d+[\.)]\s*", ". ", t, flags=re.MULTILINE)

    # Remove URLs and markdown links [text](url) -> text
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    t = re.sub(r"https?://\S+", "", t)

    # Replace multiple newlines or spaces with single space
    t = re.sub(r"\s+", " ", t).strip()

    return t


def cleanup_old_audio_files(max_age_seconds: int = 3600):
    """Safely delete generated audio files older than max_age_seconds, preserving protected demo audio."""
    try:
        now = time.time()
        for p in AUDIO_DIR.glob("*.mp3"):
            # Never delete demo files or permanent sample audio
            if p.name.startswith("demo_"):
                continue
            if now - p.stat().st_mtime > max_age_seconds:
                p.unlink(missing_ok=True)
    except Exception:
        pass


def synthesize_speech_with_status(
    text: str,
    language: str = "hi"
) -> Tuple[Optional[str], str]:
    """
    Synthesizes speech audio from text in the target Indian language.
    Returns: (filename or None, status: 'cached' | 'generated' | 'text_fallback')
    """
    if not text or not text.strip():
        return None, "text_fallback"

    cleanup_old_audio_files()

    clean_text = sanitize_text_for_speech(text)
    if not clean_text:
        return None, "text_fallback"

    lang_code = (language or "hi").strip().lower().split("-")[0]
    gtts_lang = GTTS_LANG_MAP.get(lang_code, "hi")

    # Consistent hash-based filename for caching identical responses
    text_hash = hashlib.md5(f"{gtts_lang}:{clean_text[:120]}".encode("utf-8")).hexdigest()[:12]
    filename = f"voice_{text_hash}.mp3"
    filepath = AUDIO_DIR / filename

    # 1. Cache hit: Return immediately without outbound network request
    if filepath.exists() and filepath.stat().st_size > 500:
        return filename, "cached"

    # 2. Outbound gTTS synthesis
    try:
        tts = gTTS(text=clean_text, lang=gtts_lang, slow=False, timeout=5.0)
        tts.save(str(filepath))
        return filename, "generated"
    except Exception as e:
        # Graceful text fallback: network timeout, offline venue, or rate limit
        print(f"TTS Synthesis notice for lang '{gtts_lang}' (fallback to text): {e}")
        return None, "text_fallback"


def synthesize_speech(
    text: str,
    language: str = "hi"
) -> Optional[str]:
    """
    Legacy wrapper returning just the filename or None.
    """
    filename, _ = synthesize_speech_with_status(text, language)
    return filename
