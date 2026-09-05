import sys
import json
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = WORKSPACE_DIR / "backend"
TEST_IMAGES_DIR = WORKSPACE_DIR / "tests" / "fixtures" / "test_images"
if not TEST_IMAGES_DIR.exists():
    TEST_IMAGES_DIR = BACKEND_DIR / "test_images"

sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app

def run_stress_test():
    client = TestClient(app)
    test_dir = TEST_IMAGES_DIR

    test_cases = [
        ("Case 1: Healthy Tomato Leaf", "1_healthy_tomato_leaf.jpg", "tomato", 200),
        ("Case 2: Diseased Tomato Leaf", "2_diseased_tomato_leaf.jpg", "tomato", 200),
        ("Case 3: Blurry / Low-Quality Photo", "3_blurry_leaf.jpg", "tomato", 400),
        ("Case 4: Non-Leaf Object (Desk/Laptop)", "4_non_leaf_object.jpg", "tomato", 400),
        ("Case 5: Rice Leaf Blast (Rice Model)", "5_rice_leaf_blast.jpg", "rice", 200),
        ("Case 6: Wheat Leaf Rust (Wheat Model)", "6_wheat_leaf_rust.jpg", "wheat", 200),
    ]

    farm_profile = {
        "farm_area": 2.5,
        "growth_stage": "vegetative",
        "irrigation_method": "drip",
        "irrigation_status": "normal",
        "recent_rainfall": "low",
        "humidity": "moderate",
        "fertilizer_applied": "NPK",
        "previous_crop": "wheat",
        "disease_severity": "moderate",
        "region": "Ludhiana, Punjab"
    }

    print("=" * 85)
    print("AGRIBRIDGE AI PIPELINE STRESS TEST SUITE — 6 BENCHMARK CASES")
    print("=" * 85)

    passed_count = 0

    for label, filename, plant, expected_status in test_cases:
        file_path = test_dir / filename
        assert file_path.exists(), f"Missing test image: {file_path}"
        with open(file_path, "rb") as f:
            res = client.post(
                "/api/ai/predict",
                data={"plant": plant, "farm": json.dumps(farm_profile)},
                files={"image": (filename, f, "image/jpeg")}
            )
        
        status_match = res.status_code == expected_status
        if status_match:
            passed_count += 1
            verdict = "[PASS]"
        else:
            verdict = f"[FAIL - Expected {expected_status}, Got {res.status_code}]"

        print(f"\n{verdict} {label} ({filename}) on plant='{plant}'")
        print(f"HTTP Status: {res.status_code}")
        
        data = res.json()
        if res.status_code == 200:
            pred = data.get("result", {}).get("prediction", {})
            disease = data.get("result", {}).get("disease", {})
            timing = data.get("result", {}).get("timing_advice", {})
            print(f"  * Model Route: {pred.get('model')} ({pred.get('model_name')})")
            print(f"  * Predicted Disease: {disease.get('disease')}")
            print(f"  * Confidence Score: {pred.get('confidence')}%")
            print(f"  * Chemical Option: {disease.get('chemical_option') or 'None (Zero Chemical)'}")
            print(f"  * Timing Status: {timing.get('status')}")
            print(f"  * Timing Advice: {timing.get('advice')}")
        else:
            print(f"  * Expected Failure Gate Triggered: {data.get('detail')}")

    print("\n" + "=" * 85)
    print(f"STRESS TEST SUMMARY: {passed_count}/{len(test_cases)} CASES PASSED PROPERLY ({passed_count/len(test_cases)*100:.0f}%)")
    print("=" * 85)

if __name__ == "__main__":
    run_stress_test()

