"""
Comparative Evaluation of Phase 1 vs Stage 2 Wheat Models
"""

import os
import sys
import json
import numpy as np
from PIL import Image

# Suppress TF logs
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import tensorflow as tf

def load_model_custom(path):
    if os.path.isdir(path):
        config_path = os.path.join(path, "config.json")
        weights_path = os.path.join(path, "model.weights.h5")
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        m = tf.keras.models.model_from_json(json.dumps(cfg))
        m.load_weights(weights_path)
        return m
    return tf.keras.models.load_model(path)

def main():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    models_dir = os.path.join(project_root, "ai_engine", "models")

    p1_path = os.path.join(models_dir, "AgriBridge_Wheat_EfficientNetB0_Phase1.keras")
    s2_path = os.path.join(models_dir, "AgriBridge_Wheat_EfficientNetB0_Stage2_Best.keras")

    m_p1 = load_model_custom(p1_path)
    m_s2 = load_model_custom(s2_path)

    classes = ["BlackPoint", "FusariumFootRot", "HealthyLeaf", "LeafBlight", "WheatBlast"]

    test_img_dir = os.path.join(project_root, "backend", "test_images")
    images = [os.path.join(test_img_dir, f) for f in os.listdir(test_img_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]

    print(f"\n======================================================================")
    print(f"EVALUATING PHASE 1 vs STAGE 2 ON AVAILABLE TEST IMAGES ({len(images)} images)")
    print(f"======================================================================")

    results = []

    for img_path in images:
        fname = os.path.basename(img_path)
        img = Image.open(img_path).convert("RGB").resize((224, 224))
        arr = np.array(img, dtype=np.float32)
        batch = np.expand_dims(arr, axis=0)  # Shape (1, 224, 224, 3), range [0, 255]

        # Phase 1 prediction
        pred_p1 = m_p1.predict(batch, verbose=0)[0]
        top_idx_p1 = int(np.argmax(pred_p1))
        conf_p1 = float(pred_p1[top_idx_p1])

        # Stage 2 prediction
        pred_s2 = m_s2.predict(batch, verbose=0)[0]
        top_idx_s2 = int(np.argmax(pred_s2))
        conf_s2 = float(pred_s2[top_idx_s2])

        item = {
            "file": fname,
            "phase1": {
                "class_id": top_idx_p1,
                "class_name": classes[top_idx_p1],
                "confidence": conf_p1,
                "all_probs": [float(p) for p in pred_p1]
            },
            "stage2": {
                "class_id": top_idx_s2,
                "class_name": classes[top_idx_s2],
                "confidence": conf_s2,
                "all_probs": [float(p) for p in pred_s2]
            }
        }
        results.append(item)

        print(f"\nImage: {fname}")
        print(f"  Phase 1: {classes[top_idx_p1]} (conf: {conf_p1*100:.2f}%) | Probs: {[round(p, 4) for p in pred_p1]}")
        print(f"  Stage 2: {classes[top_idx_s2]} (conf: {conf_s2*100:.2f}%) | Probs: {[round(p, 4) for p in pred_s2]}")

    # Save evaluation summary
    out_json = os.path.join(project_root, "wheat_test_images_comparison.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved comparative evaluation to {out_json}")

if __name__ == "__main__":
    main()

