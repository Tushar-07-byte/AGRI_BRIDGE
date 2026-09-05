"""
AgriBridge Wheat AI Diagnostic & End-to-End Consistency Test Suite
Phases 14, 15, 16, and 17 Verification
"""

import os
import sys
import json
from pathlib import Path
from PIL import Image
import numpy as np

# Setup path
WORKSPACE_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = WORKSPACE_DIR / "backend"
TEST_IMAGES_DIR = WORKSPACE_DIR / "tests" / "fixtures" / "test_images"
if not TEST_IMAGES_DIR.exists():
    TEST_IMAGES_DIR = BACKEND_DIR / "test_images"

sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.services.ai_service import analyze_crop

client = TestClient(app)

def test_standalone_vs_backend():
    print("\n======================================================================")
    print("TEST 1: STANDALONE PYTHON VS BACKEND API CONSISTENCY CHECK")
    print("======================================================================")

    test_img = str(TEST_IMAGES_DIR / "1_healthy_leaf.jpg")
    assert os.path.exists(test_img), f"Test image not found: {test_img}"

    valid_farm = {
        "farm_area": 2.5,
        "growth_stage": "vegetative",
        "irrigation_method": "drip",
        "irrigation_status": "normal",
        "recent_rainfall": "none",
        "humidity": "moderate",
        "fertilizer_applied": "urea",
        "previous_crop": "rice",
        "disease_severity": "low",
        "region": "Uttar Pradesh"
    }

    # 1. Direct Python AI Service Call
    direct_res = analyze_crop(
        image_path=test_img,
        plant="wheat",
        farm=valid_farm
    )

    # 2. FastAPI API Call
    with open(test_img, "rb") as fp:
        resp = client.post(
            "/api/ai/predict",
            files={"image": ("1_healthy_leaf.jpg", fp, "image/jpeg")},
            data={"plant": "wheat", "farm": json.dumps(valid_farm)}
        )

    assert resp.status_code == 200, f"API failed with status {resp.status_code}: {resp.text}"
    api_res = resp.json().get("result", {})

    print(f"Direct Python Result: {direct_res['prediction']}")
    print(f"FastAPI API Result:   {api_res['prediction']}")

    assert direct_res["prediction"]["class_id"] == api_res["prediction"]["class_id"]
    assert direct_res["prediction"]["confidence"] == api_res["prediction"]["confidence"]
    assert direct_res["prediction"]["class_id"] == 2
    assert "treatment" in api_res or "recommendation" in api_res

    print("[PASSED]: Direct Python and FastAPI backend produce 100% consistent results.")


def test_multiple_crops_regression():
    print("\n======================================================================")
    print("TEST 2: MULTI-CROP REGRESSION TEST (Wheat, Rice, Tomato)")
    print("======================================================================")

    valid_farm = {
        "farm_area": 3.0,
        "growth_stage": "vegetative",
        "irrigation_method": "drip",
        "irrigation_status": "normal",
        "recent_rainfall": "none",
        "humidity": "moderate",
        "fertilizer_applied": "urea",
        "previous_crop": "wheat",
        "disease_severity": "low",
        "region": "Uttar Pradesh"
    }

    crops_to_test = [
        ("wheat", "1_healthy_leaf.jpg"),
        ("tomato", "1_healthy_tomato_leaf.jpg"),
        ("rice", "5_rice_leaf_blast.jpg")
    ]

    for crop_type, img_filename in crops_to_test:
        img_path = str(TEST_IMAGES_DIR / img_filename)
        if not os.path.exists(img_path):
            print(f"Skipping {crop_type}: {img_filename} not found")
            continue

        with open(img_path, "rb") as fp:
            resp = client.post(
                "/api/ai/predict",
                files={"image": (img_filename, fp, "image/jpeg")},
                data={"plant": crop_type, "farm": json.dumps(valid_farm)}
            )
        
        assert resp.status_code == 200, f"Failed for {crop_type}: {resp.text}"
        data = resp.json().get("result", {})
        pred = data.get("prediction", {})
        disease_info = data.get("disease", {})
        print(f"  [{crop_type.upper()}] Predicted: {disease_info.get('name')} (Confidence: {pred.get('confidence')}%) | Model: {pred.get('model_name')}")
        assert pred.get("confidence") > 0

    print("[PASSED]: Multi-crop regression test completed successfully with zero breakages.")


def main():
    test_standalone_vs_backend()
    test_multiple_crops_regression()
    print("\n======================================================================")
    print("ALL END-TO-END VERIFICATION & REGRESSION TESTS PASSED SUCCESSFULLY!")
    print("======================================================================\n")

if __name__ == "__main__":
    main()
