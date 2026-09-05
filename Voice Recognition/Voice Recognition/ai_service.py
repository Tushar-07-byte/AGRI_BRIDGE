import sys
import json
from pathlib import Path

# ============================================================
# PATHS
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parents[2]

AI_HANDOFF_DIR = (
    BACKEND_DIR
    / "AI_Engine"
    / "AgriBridge_AI_Backend_Handoff"
)

AI_ENGINE_DIR = (
    AI_HANDOFF_DIR
    / "AI_Engine"
)

RECOMMENDATION_DB = (
    AI_HANDOFF_DIR
    / "recommendation_database.json"
)


# ============================================================
# IMPORT AI ENGINE
# ============================================================

sys.path.insert(0, str(AI_ENGINE_DIR))

from prediction import (
    load_agribridge_models,
    predict_disease
)

from backend_pipeline import (
    agribridge_predict
)

from app.services.timing_advice_service import calculate_timing_advice


# ============================================
# AI STATE & THREAD-SAFE READINESS
# ============================================

import threading

_AI_LOCK = threading.Lock()
AI_LOADED = False
AI_WARMUP_STATUS = "WARMING"
AI_WARMUP_ERROR = None
RECOMMENDATIONS = {}


def get_ai_readiness():
    """
    Returns current readiness of EfficientNet models and recommendation database.
    Status can be 'READY', 'WARMING', or 'FAILED'.
    """
    global AI_LOADED, AI_WARMUP_STATUS, AI_WARMUP_ERROR, RECOMMENDATIONS
    try:
        from prediction import AGRIBRIDGE_MODELS
        loaded_keys = list(AGRIBRIDGE_MODELS.keys())
    except Exception:
        loaded_keys = []

    return {
        "status": AI_WARMUP_STATUS,
        "is_ready": (AI_WARMUP_STATUS == "READY"),
        "models_loaded": loaded_keys,
        "recommendations_loaded": bool(RECOMMENDATIONS),
        "error": AI_WARMUP_ERROR
    }


# ============================================
# INITIALIZE AI (THREAD-SAFE WARMUP)
# ============================================

def initialize_ai():
    global AI_LOADED, AI_WARMUP_STATUS, AI_WARMUP_ERROR, RECOMMENDATIONS

    if AI_LOADED and AI_WARMUP_STATUS == "READY":
        return

    with _AI_LOCK:
        if AI_LOADED and AI_WARMUP_STATUS == "READY":
            return

        try:
            AI_WARMUP_STATUS = "WARMING"
            print("Initializing AgriBridge AI (Pre-warming EfficientNet models)...")

            # Load ML models using existing mechanism
            load_agribridge_models(
                str(AI_HANDOFF_DIR)
            )

            # Load recommendation database
            with open(
                RECOMMENDATION_DB,
                "r",
                encoding="utf-8"
            ) as file:
                RECOMMENDATIONS = json.load(file)

            AI_LOADED = True
            AI_WARMUP_STATUS = "READY"
            AI_WARMUP_ERROR = None
            print("AgriBridge AI initialized successfully. Model readiness: READY.")

        except Exception as e:
            AI_WARMUP_STATUS = "FAILED"
            AI_WARMUP_ERROR = str(e)
            print(f"AgriBridge AI Model Initialization FAILED: {e}")
            raise e


# ============================================================
# DISEASE PREDICTION
# ============================================================

def analyze_crop(
    image_path,
    plant,
    farm
):

    initialize_ai()

    # --------------------------------------------------------
    # First get ML prediction
    # --------------------------------------------------------

    prediction = predict_disease(
        str(image_path),
        plant
    )

    # --------------------------------------------------------
    # Find recommendation
    # --------------------------------------------------------

    recommendation_key = (
        f"{prediction['model']}_"
        f"{prediction['class_id']}"
    )

    disease_data = RECOMMENDATIONS.get(
        recommendation_key
    )

    if disease_data is None:

        raise ValueError(
            "No recommendation found for "
            f"{recommendation_key}"
        )

    # --------------------------------------------------------
    # Run complete AgriBridge pipeline
    # --------------------------------------------------------

    result = agribridge_predict(
        str(image_path),
        plant,
        disease_data,
        farm,
        prediction=prediction
    )

    return result


# ============================================================
# TIMING ADVICE DELEGATION
# ============================================================

async def get_timing_advice_for_prediction(farm_info: dict, disease_data: dict) -> dict:
    """
    Delegates to shared timing_advice_service.calculate_timing_advice
    """
    crop_name = disease_data.get("crop")
    return await calculate_timing_advice(
        farm_info=farm_info,
        crop_name=crop_name,
        disease_data=disease_data
    )
