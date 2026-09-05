"""
AgriBridge Voice Assistant Master Router

Endpoints:
- POST /api/voice/classify: Classify intent, entity, language & navigation
- POST /api/voice/ask: Main voice/audio endpoint (supports audio and multipart text)
- POST /api/voice/ask-text: JSON text fallback endpoint with multi-turn history
- GET /api/voice/audio/{filename}: Serve generated speech audio files
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services.agriculture_intent import classify_intent, get_rejection_message
from app.services.voice_service import process_voice_query

router = APIRouter(prefix="/api/voice", tags=["Voice Assistant"])

BACKEND_DIR = Path(__file__).resolve().parents[2]
AUDIO_DIR = BACKEND_DIR / "uploads" / "voice_audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# PYDANTIC MODELS
# ============================================================

class ClassifyRequest(BaseModel):
    text: str
    language: Optional[str] = "hi"


class TextAskRequest(BaseModel):
    text: Optional[str] = None
    message: Optional[str] = None
    language: Optional[str] = "hi"
    language_code: Optional[str] = None
    crop: Optional[str] = None
    growth_stage: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    farm_info: Optional[Dict[str, Any]] = None
    farm_profile: Optional[Dict[str, Any]] = None
    prediction_info: Optional[Dict[str, Any]] = None
    history: Optional[List[Dict[str, str]]] = None
    detail_level: Optional[str] = "simple"
    explanation_preference: Optional[str] = None
    farmer_name: Optional[str] = None
    mode: Optional[str] = None
    assistant: Optional[str] = None
    current_page: Optional[str] = None
    screen_name: Optional[str] = None
    available_buttons: Optional[List[str]] = None
    focused_button: Optional[str] = None
    ui_context: Optional[Dict[str, Any]] = None
    guidance_context: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    farm_context: Optional[Dict[str, Any]] = None
    image_path: Optional[str] = None
    image_base64: Optional[str] = None
    image_url: Optional[str] = None


class SaathiRequest(BaseModel):
    text: Optional[str] = None
    message: Optional[str] = None
    language: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None
    farmer_name: Optional[str] = None
    current_page: Optional[str] = None
    screen_name: Optional[str] = None
    available_buttons: Optional[List[str]] = None
    focused_button: Optional[str] = None
    ui_context: Optional[Dict[str, Any]] = None
    guidance_context: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    farm_context: Optional[Dict[str, Any]] = None
    image_path: Optional[str] = None
    image_base64: Optional[str] = None
    image_url: Optional[str] = None


# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/classify")
async def classify_voice_intent(request: ClassifyRequest):
    """
    Classify whether a question is agriculture-related, identify crop & navigation targets.
    """
    result = classify_intent(request.text, request.language or "hi")
    return result


@router.post("/ask")
async def ask_voice_assistant(
    audio: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    message: Optional[str] = Form(None),
    language: Optional[str] = Form("hi"),
    language_code: Optional[str] = Form(None),
    crop: Optional[str] = Form(None),
    growth_stage: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    district: Optional[str] = Form(None),
    farm_info: Optional[str] = Form(None),
    farm_profile: Optional[str] = Form(None),
    prediction_info: Optional[str] = Form(None),
    history: Optional[str] = Form(None),
    detail_level: Optional[str] = Form("simple"),
    explanation_preference: Optional[str] = Form(None),
    farmer_name: Optional[str] = Form(None),
    mode: Optional[str] = Form(None),
    assistant: Optional[str] = Form(None),
    guidance_context: Optional[str] = Form(None),
    context: Optional[str] = Form(None),
    farm_context: Optional[str] = Form(None),
):
    """
    Main Voice Helpline Endpoint:
    Accepts audio bytes or form text with multi-turn conversation history.
    Supports Saathi companion mode and crop photo uploads.
    """
    audio_bytes = None
    content_type = "audio/webm"
    if audio is not None:
        audio_bytes = await audio.read()
        content_type = audio.content_type or "audio/webm"

    image_bytes = None
    image_filename = None
    image_content_type = None
    if image is not None:
        image_bytes = await image.read()
        image_filename = getattr(image, "filename", None)
        image_content_type = getattr(image, "content_type", None)

    query_text = text or message or None
    query_lang = language_code or language or None

    parsed_history = None
    if history:
        try:
            parsed_history = json.loads(history) if isinstance(history, str) else history
        except Exception:
            parsed_history = None

    parsed_guidance = None
    if guidance_context:
        try:
            parsed_guidance = json.loads(guidance_context) if isinstance(guidance_context, str) else guidance_context
        except Exception:
            parsed_guidance = None

    parsed_context = None
    if context:
        try:
            parsed_context = json.loads(context) if isinstance(context, str) else context
        except Exception:
            parsed_context = None

    parsed_farm_context = None
    if farm_context:
        try:
            parsed_farm_context = json.loads(farm_context) if isinstance(farm_context, str) else farm_context
        except Exception:
            parsed_farm_context = None

    # Saathi Conversational Companion Mode
    if mode == "saathi" or assistant == "saathi":
        from app.services.saathi_service import process_saathi_interaction
        return await process_saathi_interaction(
            audio_bytes=audio_bytes,
            content_type=content_type,
            text_query=query_text,
            image_bytes=image_bytes,
            image_filename=image_filename,
            image_content_type=image_content_type,
            language=query_lang,
            history=parsed_history,
            farmer_name=farmer_name,
            guidance_context=parsed_guidance,
            context=parsed_context,
            farm_context=parsed_farm_context,
        )

    raw_farm = farm_info or farm_profile
    parsed_farm_info = None
    if raw_farm:
        try:
            parsed_farm_info = json.loads(raw_farm) if isinstance(raw_farm, str) else raw_farm
        except Exception:
            parsed_farm_info = None

    parsed_prediction_info = None
    if prediction_info:
        try:
            parsed_prediction_info = json.loads(prediction_info) if isinstance(prediction_info, str) else prediction_info
        except Exception:
            parsed_prediction_info = None

    effective_detail = explanation_preference or detail_level or "simple"

    result = await process_voice_query(
        audio_bytes=audio_bytes,
        content_type=content_type,
        text_query=query_text,
        language=query_lang or "hi",
        crop=crop,
        growth_stage=growth_stage,
        state=state,
        district=district,
        farm_info=parsed_farm_info,
        prediction_info=parsed_prediction_info,
        history=parsed_history,
        detail_level=effective_detail,
        farmer_name=farmer_name,
    )
    return result


@router.post("/ask-text")
async def ask_text_assistant(request: TextAskRequest):
    """
    JSON Text Endpoint with Multi-Turn Conversation History.
    Supports Saathi companion mode.
    """
    query_text = request.text or request.message or ""
    query_lang = request.language_code or request.language or None

    # Saathi Conversational Companion Mode
    if request.mode == "saathi" or request.assistant == "saathi":
        from app.services.saathi_service import process_saathi_interaction
        return await process_saathi_interaction(
            audio_bytes=None,
            text_query=query_text,
            language=query_lang,
            history=request.history,
            farmer_name=request.farmer_name,
            current_page=request.current_page,
            screen_name=request.screen_name,
            available_buttons=request.available_buttons,
            focused_button=request.focused_button,
            ui_context=request.ui_context,
            guidance_context=request.guidance_context,
            context=request.context,
            farm_context=request.farm_context,
            image_path=request.image_path,
            image_base64=request.image_base64,
        )

    query_farm = request.farm_info or request.farm_profile
    effective_detail = request.explanation_preference or request.detail_level or "simple"

    result = await process_voice_query(
        audio_bytes=None,
        text_query=query_text,
        language=query_lang or "hi",
        crop=request.crop,
        growth_stage=request.growth_stage,
        state=request.state,
        district=request.district,
        farm_info=query_farm,
        prediction_info=request.prediction_info,
        history=request.history,
        detail_level=effective_detail,
        farmer_name=request.farmer_name,
    )
    return result


@router.get("/saathi/intro")
async def saathi_intro_endpoint(language: Optional[str] = "hi"):
    """
    Saathi First Introductory Message:
    'Namaste ji! Main Saathi hoon. Aap mujhse normal tarike se baat kar sakte hain. Jab bhi aapko meri zarurat ho, bas mujhse बात kijiye.'
    Automatically adapted to the requested/detected language.
    """
    from app.services.saathi_service import get_saathi_introduction
    from app.services.text_to_speech import synthesize_speech_with_status
    intro_text = get_saathi_introduction(language or "hi")
    audio_file, audio_status = synthesize_speech_with_status(intro_text, language or "hi")
    return {
        "success": True,
        "language": language or "hi",
        "intro_text": intro_text,
        "response": intro_text,
        "response_text": intro_text,
        "audio_status": audio_status,
        "audio_url": f"/api/voice/audio/{audio_file}" if audio_file else None,
    }


@router.post("/saathi")
async def ask_saathi_endpoint(req: Request):
    """
    Step 2 Saathi Dedicated Multilingual Platform & Navigation Interaction Endpoint:
    Voice/Text Input -> Language Detection -> Platform Understanding & Guidance -> Voice/Text Output.
    Dynamically accepts both JSON and Multipart Form/File payloads with UI context and crop photos.
    """
    from app.services.saathi_service import process_saathi_interaction

    content_type_header = req.headers.get("content-type", "").lower()
    audio_bytes = None
    image_bytes = None
    image_filename = None
    image_content_type = None
    image_path = None
    image_base64 = None
    content_type = "audio/webm"
    query_text = None
    query_lang = None
    query_history = None
    query_name = None
    current_page = None
    screen_name = None
    available_buttons = None
    focused_button = None
    ui_context = None
    guidance_context = None
    query_context = None
    query_farm_context = None

    if "application/json" in content_type_header:
        try:
            body = await req.json()
        except Exception:
            body = {}
        query_text = body.get("text") or body.get("message")
        query_lang = body.get("language")
        query_history = body.get("history")
        query_name = body.get("farmer_name")
        current_page = body.get("current_page")
        screen_name = body.get("screen_name")
        available_buttons = body.get("available_buttons")
        focused_button = body.get("focused_button")
        ui_context = body.get("ui_context")
        guidance_context = body.get("guidance_context")
        query_context = body.get("context")
        query_farm_context = body.get("farm_context") or body.get("farm_info")
        image_path = body.get("image_path")
        image_base64 = body.get("image_base64")
    else:
        # Form or Multipart Audio / Image
        try:
            form = await req.form()
            query_text = form.get("text") or form.get("message")
            query_lang = form.get("language")
            query_name = form.get("farmer_name")
            current_page = form.get("current_page")
            screen_name = form.get("screen_name")
            focused_button = form.get("focused_button")
            image_path = form.get("image_path")
            image_base64 = form.get("image_base64")
            raw_buttons = form.get("available_buttons")
            if raw_buttons:
                try:
                    available_buttons = json.loads(raw_buttons) if isinstance(raw_buttons, str) else raw_buttons
                except Exception:
                    available_buttons = None

            raw_history = form.get("history")
            if raw_history:
                try:
                    query_history = json.loads(raw_history) if isinstance(raw_history, str) else raw_history
                except Exception:
                    query_history = None

            raw_ui_ctx = form.get("ui_context")
            if raw_ui_ctx:
                try:
                    ui_context = json.loads(raw_ui_ctx) if isinstance(raw_ui_ctx, str) else raw_ui_ctx
                except Exception:
                    ui_context = None

            raw_guidance = form.get("guidance_context")
            if raw_guidance:
                try:
                    guidance_context = json.loads(raw_guidance) if isinstance(raw_guidance, str) else raw_guidance
                except Exception:
                    guidance_context = None

            raw_context = form.get("context")
            if raw_context:
                try:
                    query_context = json.loads(raw_context) if isinstance(raw_context, str) else raw_context
                except Exception:
                    query_context = None

            raw_farm_ctx = form.get("farm_context") or form.get("farm_info")
            if raw_farm_ctx:
                try:
                    query_farm_context = json.loads(raw_farm_ctx) if isinstance(raw_farm_ctx, str) else raw_farm_ctx
                except Exception:
                    query_farm_context = None

            if "audio" in form and hasattr(form["audio"], "read"):
                audio_upload = form["audio"]
                audio_bytes = await audio_upload.read()
                content_type = getattr(audio_upload, "content_type", "audio/webm") or "audio/webm"

            # Image upload support
            img_field = form.get("image") or form.get("file") or form.get("photo")
            if img_field is not None and hasattr(img_field, "read"):
                image_bytes = await img_field.read()
                image_filename = getattr(img_field, "filename", None)
                image_content_type = getattr(img_field, "content_type", None)
        except Exception:
            pass

    result = await process_saathi_interaction(
        audio_bytes=audio_bytes,
        content_type=content_type,
        text_query=query_text,
        image_bytes=image_bytes,
        image_filename=image_filename,
        image_content_type=image_content_type,
        image_path=image_path,
        image_base64=image_base64,
        language=query_lang,
        history=query_history,
        farmer_name=query_name,
        current_page=current_page,
        screen_name=screen_name,
        available_buttons=available_buttons,
        focused_button=focused_button,
        ui_context=ui_context,
        guidance_context=guidance_context,
        context=query_context,
        farm_context=query_farm_context,
    )
    return result


@router.get("/audio/{filename}")
async def get_voice_audio(filename: str):
    """
    Serve generated speech audio file.
    """
    safe_filename = Path(filename).name
    filepath = AUDIO_DIR / safe_filename

    if not filepath.exists() or not filepath.is_file():
        raise HTTPException(status_code=404, detail="Audio file not found or expired.")

    return FileResponse(
        path=str(filepath),
        media_type="audio/mpeg",
        filename=safe_filename,
    )
