"""
AgriBridge Consolidated Master Test Suite Runner
Executes all Unit, Integration, and Stress Test Suites with unified environment and reporting.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

# Configure UTF-8 encoding for Windows stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TESTS_ROOT = Path(__file__).resolve().parent
WORKSPACE_ROOT = TESTS_ROOT.parent
BACKEND_DIR = WORKSPACE_ROOT / "backend"
PYTHON_EXE = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
if not PYTHON_EXE.exists():
    PYTHON_EXE = sys.executable

# Test Groups
TEST_GROUPS = {
    "Unit Tests": [
        TESTS_ROOT / "unit" / "test_auth_system.py",
        TESTS_ROOT / "unit" / "test_auth_loop.py",
        TESTS_ROOT / "unit" / "test_session_fix.py",
        TESTS_ROOT / "unit" / "test_confidence_standardization.py",
        TESTS_ROOT / "unit" / "test_field_agent_role_standardization.py",
        TESTS_ROOT / "unit" / "test_task_lifecycle_status.py",
        TESTS_ROOT / "unit" / "test_voice_preference_adaptation.py",
        TESTS_ROOT / "unit" / "test_recommendation_route_compatibility.py",
        TESTS_ROOT / "unit" / "test_cleanup_safety.py",
        TESTS_ROOT / "unit" / "test_farm_decision_context.py",
        TESTS_ROOT / "unit" / "test_saathi_step1.py",
    ],
    "Integration Tests": [
        TESTS_ROOT / "integration" / "test_disease_verification_flow.py",
        TESTS_ROOT / "integration" / "test_action_plan_flow.py",
        TESTS_ROOT / "integration" / "test_borderline_escalation.py",
        TESTS_ROOT / "integration" / "test_complete_user_journey.py",
        TESTS_ROOT / "integration" / "test_crop_monitoring_handoff.py",
        TESTS_ROOT / "integration" / "test_final_voice_assistant.py",
        TESTS_ROOT / "integration" / "test_orchestration_audit.py",
        TESTS_ROOT / "integration" / "test_replanning_trace.py",
        TESTS_ROOT / "integration" / "test_fastapi_orchestration_integration.py",
        TESTS_ROOT / "integration" / "test_weather_integration.py",
        TESTS_ROOT / "integration" / "test_wheat_end_to_end.py",
    ],
    "Stress & Robustness Tests": [
        TESTS_ROOT / "stress" / "stress_test_ai_pipeline.py",
        TESTS_ROOT / "stress" / "test_ai_non_happy_paths.py",
        TESTS_ROOT / "stress" / "test_real_world_stress_conditions.py",
        TESTS_ROOT / "stress" / "test_replan_loop_isolation.py",
        TESTS_ROOT / "stress" / "test_stress_replanning.py",
    ]
}

def run_suite():
    print("=" * 75)
    print("  AGRIBRIDGE MASTER CONSOLIDATED TEST SUITE RUNNER")
    print(f"  Workspace Root : {WORKSPACE_ROOT}")
    print(f"  Python Bin     : {PYTHON_EXE}")
    print("=" * 75 + "\n")

    results = {}
    total_passed = 0
    total_failed = 0
    start_total = time.time()

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{BACKEND_DIR}{os.pathsep}{WORKSPACE_ROOT / 'ai_engine'}"

    for group_name, files in TEST_GROUPS.items():
        print(f"\n--- [ {group_name.upper()} ] ---")
        for test_path in files:
            if not test_path.exists():
                print(f"  [SKIPPED] {test_path.name} (File not found)")
                continue

            test_name = test_path.name
            print(f"  Running {test_name}...", end=" ", flush=True)
            t0 = time.time()

            proc = subprocess.run(
                [str(PYTHON_EXE), str(test_path)],
                cwd=str(BACKEND_DIR),
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            elapsed = time.time() - t0

            if proc.returncode == 0:
                print(f"[PASSED] ({elapsed:.2f}s)")
                total_passed += 1
                status = "PASSED"
            else:
                print(f"[FAILED] ({elapsed:.2f}s, code: {proc.returncode})")
                total_failed += 1
                status = "FAILED"

            results[test_name] = {
                "group": group_name,
                "status": status,
                "code": proc.returncode,
                "time": elapsed,
                "stdout": proc.stdout,
                "stderr": proc.stderr
            }

    total_time = time.time() - start_total

    print("\n" + "=" * 75)
    print("  TEST EXECUTION MATRIX SUMMARY")
    print("=" * 75)
    for tname, res in results.items():
        badge = f"[{res['status']}]"
        print(f"  {badge:<10} {tname:<45} {res['time']:>6.2f}s")
        if res["status"] == "FAILED":
            tail = (res["stderr"][-300:] or res["stdout"][-300:]).strip()
            print(f"    └─ Error: {tail}")

    print("\n" + "-" * 75)
    print(f"  TOTAL: {total_passed + total_failed} Tests | PASSED: {total_passed} | FAILED: {total_failed} | Time: {total_time:.2f}s")
    print("=" * 75 + "\n")

    return total_failed == 0

if __name__ == "__main__":
    success = run_suite()
    sys.exit(0 if success else 1)
