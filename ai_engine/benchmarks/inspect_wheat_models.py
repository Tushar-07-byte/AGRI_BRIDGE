"""
Comprehensive Model Inspection Script for AgriBridge Wheat Models
Phase 0 & Phase 1 Execution
"""

import os
import sys
import json
import hashlib
import time
from pathlib import Path
import numpy as np

# Suppress TF logs
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import tensorflow as tf

def hash_directory(path):
    hashes = []
    for root, dirs, files in sorted(os.walk(path)):
        for f in sorted(files):
            fpath = os.path.join(root, f)
            h = hashlib.sha256()
            with open(fpath, "rb") as fp:
                while chunk := fp.read(65536):
                    h.update(chunk)
            hashes.append((os.path.relpath(fpath, path), h.hexdigest(), os.path.getsize(fpath)))
    return hashes

def load_model_from_dir_or_file(model_path):
    if os.path.isdir(model_path):
        config_path = os.path.join(model_path, "config.json")
        weights_path = os.path.join(model_path, "model.weights.h5")
        if os.path.exists(config_path) and os.path.exists(weights_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            model = tf.keras.models.model_from_json(json.dumps(config))
            model.load_weights(weights_path)
            return model, config
    return tf.keras.models.load_model(model_path), None

def inspect_model(name, model_path):
    print(f"\n=======================================================")
    print(f"INSPECTING: {name}")
    print(f"Path: {model_path}")
    print(f"=======================================================")
    
    if not os.path.exists(model_path):
        print(f"ERROR: Path does not exist: {model_path}")
        return None

    is_dir = os.path.isdir(model_path)
    file_hashes = hash_directory(model_path) if is_dir else [(os.path.basename(model_path), hashlib.sha256(open(model_path, 'rb').read()).hexdigest(), os.path.getsize(model_path))]
    
    total_size = sum(h[2] for h in file_hashes)
    print(f"Format: {'Directory (Unzipped Keras v3)' if is_dir else 'Single File Keras'}")
    print(f"Total Size: {total_size:,} bytes")
    for frel, fh, fsz in file_hashes:
        print(f"  - {frel}: {fsz:,} bytes | SHA256: {fh}")

    # Load Model
    t0 = time.time()
    try:
        model, raw_config = load_model_from_dir_or_file(model_path)
        load_time = time.time() - t0
        print(f"Successfully loaded in {load_time:.2f}s")
    except Exception as e:
        print(f"FAILED TO LOAD: {e}")
        return None

    # Inspect Architecture
    input_shape = model.input_shape
    output_shape = model.output_shape
    num_classes = output_shape[-1] if isinstance(output_shape, tuple) else None

    # Check layers
    layers = model.layers
    num_layers = len(layers)
    trainable_count = sum(np.prod(p.shape) for p in model.trainable_variables)
    non_trainable_count = sum(np.prod(p.shape) for p in model.non_trainable_variables)
    total_params = trainable_count + non_trainable_count

    # Check output activation
    last_layer = layers[-1]
    last_activation = getattr(last_layer, 'activation', None)
    activation_name = getattr(last_activation, '__name__', str(last_activation)) if last_activation else "None"

    # Check for embedded normalization / scaling / preprocessing layers
    preprocessing_layers = []
    for layer in layers:
        l_name = layer.name.lower()
        l_class = layer.__class__.__name__
        if any(x in l_class.lower() for x in ["rescaling", "normalization", "preprocess", "resizing", "center_crop", "random"]):
            preprocessing_layers.append({
                "name": layer.name,
                "class": l_class,
                "config": getattr(layer, "get_config", lambda: {})()
            })

    # Check backbone
    backbone_name = "Custom / Unknown"
    for layer in layers:
        if "efficientnet" in layer.name.lower() or "functional" in layer.__class__.__name__.lower():
            backbone_name = f"{layer.__class__.__name__} ({layer.name})"
            break

    # Count trainable vs frozen layers in backbone if nested
    frozen_layers = []
    trainable_layers = []
    for l in layers:
        if l.trainable:
            trainable_layers.append(l.name)
        else:
            frozen_layers.append(l.name)

    info = {
        "model_name": name,
        "path": model_path,
        "is_directory": is_dir,
        "total_size_bytes": total_size,
        "file_hashes": file_hashes,
        "input_shape": list(input_shape) if isinstance(input_shape, tuple) else str(input_shape),
        "output_shape": list(output_shape) if isinstance(output_shape, tuple) else str(output_shape),
        "num_classes": num_classes,
        "output_activation": activation_name,
        "backbone": backbone_name,
        "total_layers": num_layers,
        "trainable_parameters": int(trainable_count),
        "non_trainable_parameters": int(non_trainable_count),
        "total_parameters": int(total_params),
        "trainable_layers_count": len(trainable_layers),
        "frozen_layers_count": len(frozen_layers),
        "embedded_preprocessing_layers": preprocessing_layers,
        "loss": getattr(model, 'loss', 'Not compiled / Unknown'),
        "optimizer": model.optimizer.__class__.__name__ if hasattr(model, 'optimizer') and model.optimizer else 'None',
    }

    print(f"Input Shape: {info['input_shape']}")
    print(f"Output Shape: {info['output_shape']} ({num_classes} classes)")
    print(f"Output Activation: {activation_name}")
    print(f"Total Params: {total_params:,} (Trainable: {trainable_count:,}, Non-Trainable: {non_trainable_count:,})")
    print(f"Embedded Preprocessing Layers: {len(preprocessing_layers)}")
    for pp in preprocessing_layers:
        print(f"   -> {pp['class']} ({pp['name']}) with config: {pp['config']}")

    return info

def main():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    models_dir = os.path.join(project_root, "ai_engine", "models")

    p1_path = os.path.join(models_dir, "AgriBridge_Wheat_EfficientNetB0_Phase1.keras")
    s2_path = os.path.join(models_dir, "AgriBridge_Wheat_EfficientNetB0_Stage2_Best.keras")

    info_p1 = inspect_model("AgriBridge_Wheat_EfficientNetB0_Phase1", p1_path)
    info_s2 = inspect_model("AgriBridge_Wheat_EfficientNetB0_Stage2_Best", s2_path)

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "phase1_model": info_p1,
        "stage2_model": info_s2
    }

    # Save JSON report
    out_json = os.path.join(project_root, "wheat_model_inspection_report.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved report to: {out_json}")

    # Save TXT report
    out_txt = os.path.join(project_root, "wheat_model_inspection_report.txt")
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write("="*80 + "\n")
        f.write("AGRIBRIDGE WHEAT MODEL INSPECTION REPORT (PHASE 0 & PHASE 1)\n")
        f.write("="*80 + "\n\n")
        for key, info in [("Phase 1 Model", info_p1), ("Stage 2 Model", info_s2)]:
            f.write(f"--- {key} ---\n")
            if info is None:
                f.write("Failed to load\n\n")
                continue
            for k, v in info.items():
                f.write(f"{k}: {v}\n")
            f.write("\n")
    print(f"Saved report to: {out_txt}")

if __name__ == "__main__":
    main()

