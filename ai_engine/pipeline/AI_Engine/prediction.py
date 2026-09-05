# ================================================================
# AGRIBRIDGE AI — DISEASE PREDICTION ENGINE
# ================================================================

import os
import json
import numpy as np
import tensorflow as tf

from tensorflow.keras.preprocessing import image

from model_selection import (
    MODEL_SELECTION,
    PLANT_MODEL_MAP
)


# ================================================================
# IMAGE CONFIGURATION
# ================================================================

IMAGE_SIZE = (224, 224)


# ================================================================
# LOAD MODELS
# ================================================================

AGRIBRIDGE_MODELS = {}


def load_keras_directory(model_path):
    """
    Load a Keras model stored as a directory containing:

        config.json
        metadata.json
        model.weights.h5

    This is the format currently used by the AgriBridge models.
    """

    config_path = os.path.join(
        model_path,
        "config.json"
    )

    weights_path = os.path.join(
        model_path,
        "model.weights.h5"
    )

    if not os.path.exists(config_path):

        raise FileNotFoundError(
            f"Model config not found: {config_path}"
        )

    if not os.path.exists(weights_path):

        raise FileNotFoundError(
            f"Model weights not found: {weights_path}"
        )

    # ------------------------------------------------------------
    # READ MODEL CONFIG
    # ------------------------------------------------------------

    with open(
        config_path,
        "r",
        encoding="utf-8"
    ) as f:

        config = json.load(f)

    # ------------------------------------------------------------
    # RECREATE MODEL ARCHITECTURE
    # ------------------------------------------------------------

    model = tf.keras.models.model_from_json(
        json.dumps(config)
    )

    # ------------------------------------------------------------
    # LOAD WEIGHTS
    # ------------------------------------------------------------

    model.load_weights(
        weights_path
    )

    return model


def load_agribridge_models(base_dir):

    for model_key, config in MODEL_SELECTION.items():
        base_name = os.path.basename(config["model_path"])
        candidates = [
            os.path.join(base_dir, config["model_path"]),
            os.path.join(base_dir, base_name),
            os.path.join(base_dir, "..", "models", base_name),
            os.path.join(base_dir, "..", "..", "models", base_name),
            os.path.join(base_dir, "..", "..", "ai_engine", "models", base_name),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models", base_name)),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ai_engine", "models", base_name)),
        ]

        model_path = None
        for cand in candidates:
            norm_cand = os.path.normpath(cand)
            if os.path.exists(norm_cand):
                model_path = norm_cand
                break

        if not model_path:
            raise FileNotFoundError(
                f"{config.get('model_name', model_key)} model not found. Checked locations: {candidates[:4]}"
            )

        print(
            f"Loading {model_key} from {model_path}..."
        )

        if os.path.isdir(model_path):
            AGRIBRIDGE_MODELS[model_key] = load_keras_directory(model_path)
        else:
            AGRIBRIDGE_MODELS[model_key] = tf.keras.models.load_model(model_path)

        print(
            f"{model_key} loaded successfully."
        )

    return AGRIBRIDGE_MODELS



# ================================================================
# IMAGE PREPROCESSING & LEAF VALIDATION
# ================================================================

def validate_leaf_image_quality(image_path):
    """
    Validates that the uploaded image contains botanical leaf characteristics
    and meets minimum sharpness standards before running neural network inference.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    try:
        from PIL import Image
        img = Image.open(image_path).convert("RGB").resize((224, 224))
        arr = np.array(img, dtype=float)
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

        # Calculate HSV saturation to exclude neutral whites, grays, and blacks
        max_c = np.maximum(np.maximum(r, g), b)
        min_c = np.minimum(np.minimum(r, g), b)
        delta = max_c - min_c
        sat = np.where(max_c > 0, delta / max_c, 0)

        # 1. Botanical Green:
        green_mask = (sat > 0.15) & (g > r * 1.05) & (g > b * 1.05) & (g > 30)

        # 2. Plant Yellow / Brown / Rust Necrosis:
        yellow_brown_mask = (sat > 0.20) & (r > 60) & (g > 50) & (b < r * 0.75) & (abs(r - g) < 60)

        foliage_mask = green_mask | yellow_brown_mask
        foliage_ratio = float(np.mean(foliage_mask))

        # 3. Laplacian Sharpness Variance:
        gray = 0.299 * r + 0.587 * g + 0.114 * b
        laplacian = (
            -4 * gray[1:-1, 1:-1]
            + gray[:-2, 1:-1] + gray[2:, 1:-1]
            + gray[1:-1, :-2] + gray[1:-1, 2:]
        )
        sharpness_var = float(np.var(laplacian))

        # Rejection rules for non-leaf or unusable images
        if foliage_ratio < 0.10:
            raise ValueError(
                "Image rejected: The uploaded image does not appear to contain a recognized crop leaf or plant tissue. "
                "Please upload a photo of an actual plant leaf."
            )

        if sharpness_var < 5.0:
            raise ValueError(
                "Image rejected: The photo is too blurry or low quality for a reliable AI diagnosis. "
                "Please hold your camera steady and capture a clear, well-lit photo."
            )

    except (ValueError, FileNotFoundError):
        raise
    except Exception:
        # If image inspection fails, let the model pipeline proceed with confidence check
        pass


def preprocess_leaf_image(image_path):

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Validate image quality first
    validate_leaf_image_quality(image_path)

    img = image.load_img(
        image_path,
        target_size=IMAGE_SIZE
    )

    img_array = image.img_to_array(
        img
    )

    img_array = np.expand_dims(
        img_array,
        axis=0
    )

    img_array = img_array.astype(
        "float32"
    )

    return img_array


# ================================================================
# DISEASE PREDICTION
# ================================================================

def predict_disease(
    image_path,
    plant
):

    plant_key = (
        plant
        .strip()
        .lower()
    )

    # ------------------------------------------------------------
    # VALIDATE PLANT
    # ------------------------------------------------------------

    if plant_key not in PLANT_MODEL_MAP:
        raise ValueError(f"Unsupported plant: {plant}")

    plant_config = PLANT_MODEL_MAP[plant_key]
    model_key = plant_config["model"]
    valid_class_ids = plant_config["class_ids"]

    # ------------------------------------------------------------
    # CHECK MODEL
    # ------------------------------------------------------------

    if model_key not in AGRIBRIDGE_MODELS:
        raise RuntimeError(f"Model not loaded: {model_key}")

    model = AGRIBRIDGE_MODELS[model_key]

    # ------------------------------------------------------------
    # PREPROCESS (Includes Quality Validation)
    # ------------------------------------------------------------

    img_array = preprocess_leaf_image(
        image_path
    )

    # ------------------------------------------------------------
    # PREDICT
    # ------------------------------------------------------------

    predictions = model.predict(
        img_array,
        verbose=0
    )

    probabilities = predictions[0]

    # ------------------------------------------------------------
    # ONLY ALLOW CLASSES BELONGING TO SELECTED PLANT
    # ------------------------------------------------------------

    plant_probabilities = {
        class_id: float(probabilities[class_id])
        for class_id in valid_class_ids
    }

    predicted_class_id = max(
        plant_probabilities,
        key=plant_probabilities.get
    )

    raw_confidence = plant_probabilities[predicted_class_id]
    total_plant_prob = sum(plant_probabilities.values())
    rel_confidence = (raw_confidence / max(total_plant_prob, 1e-6)) * 100.0

    # ------------------------------------------------------------
    # CONFIDENCE & OUT-OF-DOMAIN THRESHOLD GATE
    # ------------------------------------------------------------
    # If raw probability is nearly zero or relative confidence is too low,
    # reject the prediction rather than providing a false confident diagnosis.

    if raw_confidence < 0.05 and rel_confidence < 30.0:
        raise ValueError(
            f"Low confidence detection ({rel_confidence:.1f}%). The AI model could not reliably identify "
            f"a recognized condition for {plant}. Please upload a clearer, closer photo of the leaf."
        )

    # Final displayed confidence
    # Use raw_confidence as the source of truth — rel_confidence is only
    # meaningful for multi-class plants and should never exceed the actual
    # model probability. For single-class plants rel_confidence is always
    # 100% (division by itself), so taking max() inflated every result.
    displayed_confidence = round(raw_confidence * 100.0, 2)

    # ------------------------------------------------------------
    # RESULT
    # ------------------------------------------------------------

    result = {
        "plant": plant,
        "model": model_key,
        "model_name": MODEL_SELECTION[model_key]["model_name"],
        "class_id": int(predicted_class_id),
        "confidence": displayed_confidence
    }

    return result