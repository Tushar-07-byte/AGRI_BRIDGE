"""
AgriBridge Saathi Master Verification Runner (Steps 1 to 20 + Crop Monitoring)
Run all 21 test suites in sequence with a clean summary report.

Usage:
    python scripts/verify_all_saathi_steps.py
"""

import sys
import subprocess
from pathlib import Path

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parents[1]
PYTHON_EXE = ROOT_DIR / "backend" / ".venv" / "Scripts" / "python.exe"
if not PYTHON_EXE.exists():
    PYTHON_EXE = Path(sys.executable)

TEST_SUITES = [
    ("Step 1: First Message & Multilingual Detection", "tests/unit/test_saathi_step1.py"),
    ("Step 2: Platform Navigation & UI Buttons", "tests/unit/test_saathi_step2.py"),
    ("Step 3: Natural Spoken Queries & Audio TTS", "tests/unit/test_saathi_step3.py"),
    ("Step 4: Multi-Turn Conversation Continuity", "tests/unit/test_saathi_step4.py"),
    ("Step 5: Guided Platform Navigation Walkthrough", "tests/unit/test_saathi_step5.py"),
    ("Step 6: Intelligent Screen & UI Awareness", "tests/unit/test_saathi_step6.py"),
    ("Step 7: Production Reliability & Scope Guard", "tests/unit/test_saathi_step7.py"),
    ("Step 8: Human-Like Conversation & Recovery", "tests/unit/test_saathi_step8.py"),
    ("Step 9: Proactive Inactivity & Stuck State Help", "tests/unit/test_saathi_step9.py"),
    ("Step 10: Personalised Session Adaptation", "tests/unit/test_saathi_step10.py"),
    ("Step 11: Layer 2 Guidance Context Foundation", "tests/unit/test_saathi_step11.py"),
    ("Step 12: Layer 2 Trusted Guidance Ingestion", "tests/unit/test_saathi_step12.py"),
    ("Step 13: Layer 2 Guidance Explanation Engine", "tests/unit/test_saathi_step13.py"),
    ("Step 14: Layer 2 Natural Multi-Turn Follow-Ups", "tests/unit/test_saathi_step14.py"),
    ("Step 15: Layer 2 Personalised Communication", "tests/unit/test_saathi_step15.py"),
    ("Step 16: Layer 2 Action Plan Step Guidance", "tests/unit/test_saathi_step16.py"),
    ("Step 17: Layer 2 Replanning & Decision History", "tests/unit/test_saathi_step17.py"),
    ("Step 18: Layer 2 Safety, Grounding & Safeguards", "tests/unit/test_saathi_step18.py"),
    ("Step 19: Layer 2 Full Voice + TTS Integration", "tests/unit/test_saathi_step19.py"),
    ("Step 20: Layer 2 Error Handling & Production", "tests/unit/test_saathi_step20.py"),
    ("Ultra Crop Monitoring Dynamic Integration", "tests/integration/test_ultra_crop_monitoring.py"),
]

def run_all_steps():
    print("=" * 80)
    print("      AGRIBRIDGE SAATHI VOICE ASSISTANT — COMPLETE VERIFICATION RUNNER")
    print("=" * 80)
    
    passed_count = 0
    total_count = len(TEST_SUITES)
    
    for idx, (title, test_file) in enumerate(TEST_SUITES, 1):
        file_path = ROOT_DIR / test_file
        if not file_path.exists():
            print(f"[{idx:02d}/{total_count:02d}] ❌ FILE NOT FOUND: {test_file}")
            continue
            
        print(f"\n[{idx:02d}/{total_count:02d}] Running: {title} ({test_file})...")
        env = dict(**subprocess.os.environ)
        env["PYTHONPATH"] = str(ROOT_DIR / "backend")
        
        proc = subprocess.run(
            [str(PYTHON_EXE), str(file_path)],
            cwd=str(ROOT_DIR),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        
        if proc.returncode == 0:
            print(f"  --> ✅ PASSED: {title}")
            passed_count += 1
        else:
            print(f"  --> ❌ FAILED: {title}")
            print(proc.stdout)
            print(proc.stderr)
            
    print("\n" + "=" * 80)
    print(f"FINAL SUMMARY: {passed_count}/{total_count} Test Suites Passed ({int(passed_count/total_count*100)}% Success Rate)")
    print("=" * 80)
    
    if passed_count == total_count:
        print("\n🎉 ALL SAATHI STEPS 1–20 ARE OPERATIONAL AND PASSING!")
        sys.exit(0)
    else:
        print("\n⚠️ SOME TEST SUITES FAILED. PLEASE REVIEW LOGS ABOVE.")
        sys.exit(1)

if __name__ == "__main__":
    run_all_steps()
