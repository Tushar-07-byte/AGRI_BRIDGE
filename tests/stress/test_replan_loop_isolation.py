"""
Action Plan Replan Loop Isolation & Consistency Test
Tests 3 independent fresh plans through the full simulate/recheck replan loop,
measuring exact latencies and verifying trace integrity.
"""

import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime, timedelta

# Ensure UTF-8 stdout
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.models.farmer import Farmer
from app.models.action_plan import ActionPlan, PlanTask

client = TestClient(app)

def run_replan_isolation_tests():
    print("\n" + "="*80)
    print("ACTION PLAN REPLAN LOOP ISOLATION & CONSISTENCY TEST (3 INDEPENDENT RUNS)")
    print("="*80 + "\n")

    db = SessionLocal()
    farmer = db.query(Farmer).first()
    if not farmer:
        farmer = Farmer(name="Demo Farmer")
        db.add(farmer)
        db.commit()
        db.refresh(farmer)
    farmer_id = farmer.id
    db.close()

    runs_summary = []

    for run_idx in range(1, 4):
        print(f"--------------------------------------------------------------------------------")
        print(f"RUN #{run_idx}: FRESH ACTION PLAN & AUTONOMOUS REPLAN CYCLE")
        print(f"--------------------------------------------------------------------------------")

        # 1. Create a fresh action plan with low-rain-risk scenario
        db = SessionLocal()
        plan = ActionPlan(
            farmer_id=farmer_id,
            risk_type="low_rain_optimal",
            risk_level="moderate",
            status="active"
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

        original_task = PlanTask(
            action_plan_id=plan.id,
            title="Apply Foliar Fungicide Spray (Low Rain Window)",
            description="Optimal dry weather window detected. Apply recommended treatment.",
            location="Plot A - North Sector",
            execution_window="Immediate (Next 4 Hours)",
            scheduled_for=datetime.utcnow() + timedelta(hours=2),
            status="pending",
            reasoning="Initial plan formulated: Low rain risk (12% probability). Safe for foliar application."
        )
        db.add(original_task)
        db.commit()
        db.refresh(original_task)
        plan_id = plan.id
        orig_task_id = original_task.id
        db.close()

        print(f"  [1] Created Fresh Plan #{plan_id}")
        print(f"      Initial Task #{orig_task_id}: '{original_task.title}' | Status: [{original_task.status.upper()}]")

        # 2. Trigger recheck/simulate endpoint with high-rain-risk value (85%)
        recheck_payload = {
            "simulated_rain_probability": 85,
            "simulated_condition": "Heavy Monsoon Downpour",
            "simulated_recommended_window": "In 72 Hours (Post-Rain Clear Window)"
        }

        t0 = time.perf_counter()
        recheck_resp = client.post(f"/api/action-plans/{plan_id}/recheck", json=recheck_payload)
        t_recheck = time.perf_counter() - t0

        assert recheck_resp.status_code == 200, f"Recheck API failed ({recheck_resp.status_code}): {recheck_resp.text}"
        recheck_data = recheck_resp.json()
        assert recheck_data["success"] is True, f"Recheck response success != True: {recheck_data}"
        assert recheck_data.get("change_detected") is True or recheck_data.get("weather_change_detected") is True

        new_task_info = recheck_data["new_task"]
        new_task_id = new_task_info["id"]

        print(f"  [2] POST /api/action-plans/{plan_id}/recheck executed in {t_recheck*1000:.2f} ms ({t_recheck:.4f} s)")
        print(f"      Weather Change Detected : True ({recheck_data['change_type']})")
        print(f"      Superseded Task ID      : #{orig_task_id}")
        print(f"      Replacement Task ID     : #{new_task_id}")
        print(f"      New Task Title          : '{new_task_info['title']}'")

        # 3. Confirm in Database: old task superseded, new task active
        db = SessionLocal()
        old_task_db = db.query(PlanTask).filter(PlanTask.id == orig_task_id).first()
        new_task_db = db.query(PlanTask).filter(PlanTask.id == new_task_id).first()

        assert old_task_db.status == "superseded", f"Expected old task #{orig_task_id} to be 'superseded', got '{old_task_db.status}'"
        assert new_task_db.status == "pending", f"Expected new task #{new_task_id} to be 'pending', got '{new_task_db.status}'"
        assert "85%" in new_task_db.reasoning or "rain" in new_task_db.reasoning.lower(), f"New task reasoning missing rain context: {new_task_db.reasoning}"

        print(f"  [3] Database Verification:")
        print(f"      • Task #{orig_task_id} Status : [{old_task_db.status.upper()}] (Superseded confirmed)")
        print(f"      • Task #{new_task_id} Status  : [{new_task_db.status.upper()}] (Active confirmed)")
        print(f"      • New Task Reasoning  : \"{new_task_db.reasoning}\"")
        db.close()

        # 4. Verify Trace endpoint returns full evolution
        t0 = time.perf_counter()
        trace_resp = client.get(f"/api/action-plans/{plan_id}/trace")
        t_trace = time.perf_counter() - t0

        assert trace_resp.status_code == 200, f"Trace API failed ({trace_resp.status_code}): {trace_resp.text}"
        trace_data = trace_resp.json()
        assert trace_data["success"] is True

        events = trace_data["trace"]
        event_types = [e["event_type"] for e in events]
        print(f"  [4] Trace Endpoint (GET /api/action-plans/{plan_id}/trace in {t_trace*1000:.2f} ms):")
        print(f"      Total Trace Events: {len(events)}")
        for e in events:
            print(f"        Step {e['step']}: [{e['event_type']:<22}] -> {e.get('summary') or e.get('task_title') or ''}")

        assert "PLAN_INITIALIZED" in event_types, "PLAN_INITIALIZED missing from trace"
        assert "TASK_SUPERSEDED" in event_types, "TASK_SUPERSEDED missing from trace"
        assert "REPLANNING_TRIGGERED" in event_types, "REPLANNING_TRIGGERED missing from trace"
        assert "ACTIVE_TASK_SCHEDULED" in event_types, "ACTIVE_TASK_SCHEDULED missing from trace"

        runs_summary.append({
            "run": run_idx,
            "plan_id": plan_id,
            "orig_task_id": orig_task_id,
            "new_task_id": new_task_id,
            "recheck_time_ms": t_recheck * 1000,
            "trace_time_ms": t_trace * 1000,
            "trace_events_count": len(events),
            "status": "PASSED"
        })
        print(f"  --> Run #{run_idx} PASSED with 100% policy and trace consistency.\n")

    # =========================================================================
    # FINAL SUMMARY REPORT
    # =========================================================================
    print("="*80)
    print("REPLAN LOOP ISOLATION BENCHMARK SUMMARY (3 RUNS)")
    print("="*80)
    print(f"{'Run #':<8}{'Plan ID':<10}{'Old Task':<12}{'New Task':<12}{'Replan Time':<18}{'Trace Time':<15}{'Result'}")
    print("-"*80)
    for r in runs_summary:
        print(f"{r['run']:<8}#{r['plan_id']:<9}#{r['orig_task_id']:<11}#{r['new_task_id']:<11}{r['recheck_time_ms']:>6.2f} ms        {r['trace_time_ms']:>6.2f} ms      [{r['status']}]")

    avg_recheck = sum(r["recheck_time_ms"] for r in runs_summary) / len(runs_summary)
    avg_trace = sum(r["trace_time_ms"] for r in runs_summary) / len(runs_summary)
    print("-"*80)
    print(f"Average Live Recheck/Replan Latency : {avg_recheck:.2f} ms ({avg_recheck/1000:.4f} s)")
    print(f"Average Trace Render Latency         : {avg_trace:.2f} ms ({avg_trace/1000:.4f} s)")
    print(f"Total Interactive Demo Latency       : {(avg_recheck + avg_trace):.2f} ms (Virtually Instant)")
    print("="*80 + "\n")

if __name__ == "__main__":
    run_replan_isolation_tests()
