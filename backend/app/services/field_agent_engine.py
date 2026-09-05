"""
AgriBridge Field Agent Human-in-the-Loop Engine
Handles:
1. Configurable Disease Confidence Gating (LOW -> Locked Chemical Recommendation & Escalation; ACCEPTABLE -> Normal flow)
2. IoT Telemetry Sensor Anomaly Evaluation (Out-of-range, missing, and nuanced zero-value detection)
3. Field Agent Task Lifecycle (PENDING -> ACCEPTED / REJECTED -> IN_PROGRESS -> FIELD_VISIT -> VERIFIED)
4. Audit Trail and Verification State Management
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Config directory path
CONFIG_DIR = Path(__file__).resolve().parent.parent / "field_agent" / "config"

# In-memory store for active tasks (backed by DB action plans when available)
_TASK_STORE: Dict[str, Dict[str, Any]] = {}
_AUDIT_LOG: List[Dict[str, Any]] = []


def _load_json_config(filename: str, default: Dict[str, Any]) -> Dict[str, Any]:
    file_path = CONFIG_DIR / filename
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default


def get_confidence_config() -> Dict[str, Any]:
    return _load_json_config("disease_confidence_config.json", {
        "disease_low_confidence_threshold": 0.60,
        "confidence_status_definitions": {
            "LOW": {
                "field_agent_escalation": True,
                "chemical_recommendation_status": "LOCKED",
                "lock_reason": "LOW_DISEASE_CONFIDENCE",
                "farmer_message": "AI confidence is low for this disease prediction. Chemical treatment recommendation is temporarily locked. A Field Agent verification is required before treatment guidance can be provided."
            },
            "ACCEPTABLE": {
                "field_agent_escalation": False,
                "chemical_recommendation_rule": "UNLOCKED_ONLY_IF_VERIFIED_KB_EXISTS"
            }
        }
    })


def get_sensor_anomaly_config() -> Dict[str, Any]:
    return _load_json_config("sensor_anomaly_config.json", {
        "sensors": {
            "soil_moisture": {
                "unit": "% VWC",
                "valid_min": 5.0,
                "valid_max": 95.0,
                "allow_zero_without_anomaly": False,
                "zero_interpretation": "Zero value indicates disconnected sensor probe or detached wire.",
                "anomaly_reasons": {
                    "ZERO_READING": "UNUSUAL_SENSOR_READING",
                    "OUT_OF_RANGE": "SENSOR_VALUE_OUT_OF_RANGE"
                }
            }
        }
    })



# ==============================================================================
# 1. DISEASE CONFIDENCE GATING & CHEMICAL LOCK
# ==============================================================================

def evaluate_disease_confidence(
    confidence: float,
    disease_name: str,
    crop_name: str = "Wheat",
    verified_treatment_exists: bool = True,
    treatment_details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Evaluates model confidence score against the configurable threshold.
    Strictly locks chemical recommendations if confidence < threshold.
    """
    cfg = get_confidence_config()
    threshold = float(cfg.get("disease_low_confidence_threshold", 0.60))

    # Normalize fraction or percentage (e.g. 54.0% -> 0.54)
    norm_conf = confidence / 100.0 if confidence > 1.0 else confidence
    norm_conf = max(0.0, min(1.0, norm_conf))

    if norm_conf < threshold:
        # -------------------------------------------------------------
        # LOW CONFIDENCE GATE
        # -------------------------------------------------------------
        return {
            "confidence_status": "LOW",
            "confidence_score": round(norm_conf, 4),
            "confidence_threshold": threshold,
            "field_agent_escalation": True,
            "escalation_reason": "LOW_CONFIDENCE_DISEASE_PREDICTION",
            "chemical_recommendation": {
                "status": "LOCKED",
                "reason": "LOW_DISEASE_CONFIDENCE",
                "pesticide_name": None,
                "dosage": None,
                "application_schedule": None
            },
            "farmer_message": (
                "AI confidence is low for this disease prediction. "
                "Chemical treatment recommendation is temporarily locked. "
                "A Field Agent verification is required before treatment guidance can be provided."
            ),
            "recommended_action": "Inspection uncertainty requires on-site verification by an Agri-Field Agent."
        }
    else:
        # -------------------------------------------------------------
        # ACCEPTABLE / HIGH CONFIDENCE GATE
        # -------------------------------------------------------------
        if verified_treatment_exists and treatment_details:
            chem_status = "AVAILABLE"
            chem_data = treatment_details
        elif verified_treatment_exists:
            chem_status = "AVAILABLE"
            chem_data = {
                "chemical": "Approved ICAR formulation",
                "dosage": "Follow certified label dosage",
                "phi": "Observe Pre-Harvest Interval (PHI)"
            }
        else:
            chem_status = "UNAVAILABLE"
            chem_data = None

        return {
            "confidence_status": "ACCEPTABLE",
            "confidence_score": round(norm_conf, 4),
            "confidence_threshold": threshold,
            "field_agent_escalation": False,
            "escalation_reason": None,
            "chemical_recommendation": {
                "status": chem_status,
                "reason": None if chem_status == "AVAILABLE" else "NO_VERIFIED_TREATMENT_IN_KB",
                "treatment_details": chem_data
            },
            "farmer_message": f"Disease {disease_name} detected with acceptable AI confidence.",
            "recommended_action": "Review verified agricultural advisory and apply if applicable."
        }


# ==============================================================================
# 2. IOT SENSOR TELEMETRY ANOMALY DETECTION
# ==============================================================================

def evaluate_sensor_telemetry(
    sensor_id: str,
    sensor_type: str,
    value: Optional[float],
    crop_name: str = "Wheat",
    farm_id: str = "FARM_01",
    field_id: str = "PLOT_A",
    previous_value: Optional[float] = None
) -> Dict[str, Any]:
    """
    Evaluates IoT telemetry against physical operating limits and nuanced zero-value rules.
    """
    cfg = get_sensor_anomaly_config()
    sensors = cfg.get("sensors", {})
    sensor_norm = sensor_type.strip().lower()

    if value is None:
        return {
            "sensor_id": sensor_id,
            "sensor_type": sensor_type,
            "observed_value": None,
            "anomaly_detected": True,
            "anomaly_type": "MISSING_DATA",
            "escalation_reason": "SENSOR_DATA_MISSING",
            "field_agent_escalation": True,
            "priority": "HIGH",
            "interpretation": f"Telemetry signal missing from sensor {sensor_id} on {farm_id}."
        }

    spec = sensors.get(sensor_norm, {
        "unit": "unit",
        "valid_min": 0.0,
        "valid_max": 100.0,
        "allow_zero_without_anomaly": True,
        "anomaly_reasons": {
            "OUT_OF_RANGE": "SENSOR_VALUE_OUT_OF_RANGE",
            "ZERO_READING": "UNUSUAL_SENSOR_READING"
        }
    })

    val = float(value)
    min_v = float(spec.get("valid_min", 0.0))
    max_v = float(spec.get("valid_max", 100.0))
    allow_zero = spec.get("allow_zero_without_anomaly", True)

    # 1. Check for Zero-Value anomaly
    if val == 0.0 and not allow_zero:
        return {
            "sensor_id": sensor_id,
            "sensor_type": sensor_type,
            "observed_value": val,
            "unit": spec.get("unit", ""),
            "expected_range": [min_v, max_v],
            "anomaly_detected": True,
            "anomaly_type": "ZERO_READING",
            "escalation_reason": "UNUSUAL_SENSOR_READING",
            "field_agent_escalation": True,
            "priority": "HIGH",
            "interpretation": spec.get("zero_interpretation", f"Suspicious zero reading on {sensor_type}.")
        }

    # 2. Check for Out-of-Range anomaly
    if val < min_v or val > max_v:
        return {
            "sensor_id": sensor_id,
            "sensor_type": sensor_type,
            "observed_value": val,
            "unit": spec.get("unit", ""),
            "expected_range": [min_v, max_v],
            "anomaly_detected": True,
            "anomaly_type": "OUT_OF_RANGE",
            "escalation_reason": "SENSOR_VALUE_OUT_OF_RANGE",
            "field_agent_escalation": True,
            "priority": "MEDIUM",
            "interpretation": f"Sensor value {val} is outside physical limits [{min_v}, {max_v}] {spec.get('unit', '')}."
        }

    # 3. Check for Rapid Rate of Change anomaly
    max_rate = spec.get("max_hourly_rate_of_change_pct")
    if previous_value is not None and max_rate is not None:
        drop = abs(val - float(previous_value))
        if drop > max_rate:
            return {
                "sensor_id": sensor_id,
                "sensor_type": sensor_type,
                "observed_value": val,
                "previous_value": previous_value,
                "unit": spec.get("unit", ""),
                "anomaly_detected": True,
                "anomaly_type": "RAPID_CHANGE",
                "escalation_reason": "SENSOR_DATA_ANOMALY",
                "field_agent_escalation": True,
                "priority": "HIGH",
                "interpretation": f"Abnormal sudden shift ({drop} {spec.get('unit', '')}) detected within single reporting period."
            }

    # Normal Reading
    return {
        "sensor_id": sensor_id,
        "sensor_type": sensor_type,
        "observed_value": val,
        "unit": spec.get("unit", ""),
        "expected_range": [min_v, max_v],
        "anomaly_detected": False,
        "escalation_reason": None,
        "field_agent_escalation": False,
        "priority": "LOW",
        "interpretation": "Telemetry normal."
    }


# ==============================================================================
# 3. FIELD AGENT TASK LIFECYCLE MANAGEMENT
# ==============================================================================

def create_field_agent_task(
    trigger_type: str,
    reason: str,
    payload: Dict[str, Any],
    priority: str = "HIGH",
    farmer_id: str = "FARMER_101",
    farmer_name: str = "Ramesh Patel",
    crop: str = "Wheat",
    crop_stage: str = "Tillering",
    location: str = "Plot A-4, Raipur Zone",
    confidence_score: Optional[float] = None,
    image_url: Optional[str] = None
) -> Dict[str, Any]:
    """Creates a new field agent escalation task in PENDING state."""
    task_id = f"TASK_ESC_{uuid.uuid4().hex[:8].upper()}"
    escalation_id = f"ESC_{uuid.uuid4().hex[:8].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()

    task = {
        "task_id": task_id,
        "escalation_id": escalation_id,
        "farmer_id": str(farmer_id),
        "farmer_name": farmer_name,
        "farm_id": payload.get("farm_id", "FARM_DEFAULT"),
        "field_id": payload.get("field_id", "FIELD_01"),
        "crop": crop,
        "crop_stage": crop_stage,
        "location": location,
        "trigger_type": trigger_type,
        "trigger_reason": reason,
        "signal_details": payload,
        "confidence_score": confidence_score,
        "uploaded_image_url": image_url,
        "priority": priority,
        "status": "PENDING",
        "assigned_agent_id": "AGENT_007",
        "assigned_agent_name": "Rahul Verma",
        "rejection_reason": None,
        "chemical_recommendation_status": "LOCKED" if trigger_type == "LOW_CONFIDENCE_DISEASE_PREDICTION" else "AVAILABLE",
        "created_at": now_iso,
        "updated_at": now_iso
    }

    _TASK_STORE[task_id] = task
    _AUDIT_LOG.append({
        "event": "TASK_CREATED",
        "task_id": task_id,
        "trigger_type": trigger_type,
        "status": "PENDING",
        "timestamp": now_iso
    })

    return task


def get_field_agent_tasks(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lists field agent tasks filtered by status."""
    tasks = list(_TASK_STORE.values())
    if status and status.upper() != "ALL":
        tasks = [t for t in tasks if t.get("status", "").upper() == status.upper()]
    # Sort latest first
    return sorted(tasks, key=lambda x: x.get("created_at", ""), reverse=True)


def get_task_by_id(task_id: str) -> Optional[Dict[str, Any]]:
    return _TASK_STORE.get(task_id)


def accept_field_agent_task(
    task_id: str,
    agent_id: str = "AGENT_007",
    agent_name: str = "Rahul Verma",
    notes: str = ""
) -> Dict[str, Any]:
    """Transitions task from PENDING to ACCEPTED."""
    task = _TASK_STORE.get(task_id)
    if not task:
        raise ValueError(f"Task with ID {task_id} not found.")

    now_iso = datetime.now(timezone.utc).isoformat()
    task["status"] = "ACCEPTED"
    task["assigned_agent_id"] = agent_id
    task["assigned_agent_name"] = agent_name
    task["agent_notes"] = notes
    task["updated_at"] = now_iso

    _AUDIT_LOG.append({
        "event": "TASK_ACCEPTED",
        "task_id": task_id,
        "agent_id": agent_id,
        "agent_name": agent_name,
        "timestamp": now_iso
    })

    return {
        "success": True,
        "task_id": task_id,
        "status": "ACCEPTED",
        "assigned_agent": agent_name,
        "message": "Task accepted. Field inspection authorized."
    }


def reject_field_agent_task(
    task_id: str,
    rejection_reason: str,
    agent_id: str = "AGENT_007",
    agent_name: str = "Rahul Verma"
) -> Dict[str, Any]:
    """Rejects a field agent task. Rejection reason is strictly mandatory."""
    if not rejection_reason or len(rejection_reason.strip()) < 3:
        raise ValueError("Rejection reason is mandatory and must be at least 3 characters.")

    task = _TASK_STORE.get(task_id)
    if not task:
        raise ValueError(f"Task with ID {task_id} not found.")

    now_iso = datetime.now(timezone.utc).isoformat()
    task["status"] = "REJECTED"
    task["rejection_reason"] = rejection_reason.strip()
    task["updated_at"] = now_iso

    _AUDIT_LOG.append({
        "event": "TASK_REJECTED",
        "task_id": task_id,
        "agent_id": agent_id,
        "rejection_reason": rejection_reason.strip(),
        "timestamp": now_iso
    })

    return {
        "success": True,
        "task_id": task_id,
        "status": "REJECTED",
        "rejection_reason": rejection_reason.strip(),
        "message": "Task rejected and archived with audit reason."
    }


def submit_field_verification(
    task_id: str,
    field_observation: str,
    disease_observed: str,
    verification_result: str,
    pathogen_identified: Optional[str] = None,
    notes: str = "",
    agent_id: str = "AGENT_007",
    evidence_photos: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Submits a field visit report and formal verification result.
    If VERIFIED_DISEASE, unlocks verified treatment recommendations.
    """
    valid_results = {"VERIFIED_DISEASE", "NOT_VERIFIED", "INCONCLUSIVE"}
    if verification_result not in valid_results:
        raise ValueError(f"Invalid verification result: {verification_result}. Must be one of {valid_results}")

    task = _TASK_STORE.get(task_id)
    if not task:
        raise ValueError(f"Task with ID {task_id} not found.")

    now_iso = datetime.now(timezone.utc).isoformat()
    report_id = f"RPT_{uuid.uuid4().hex[:8].upper()}"

    is_verified = (verification_result == "VERIFIED_DISEASE")
    new_chem_status = "AVAILABLE" if is_verified else ("UNAVAILABLE" if verification_result == "NOT_VERIFIED" else "LOCKED")
    downstream_action = "UNLOCK_TREATMENT_ADVISORY" if is_verified else ("DISMISS_ALERT" if verification_result == "NOT_VERIFIED" else "ESCALATE_LAB_DIAGNOSIS")

    task["status"] = "VERIFIED" if is_verified else verification_result
    task["chemical_recommendation_status"] = new_chem_status
    task["verification_report"] = {
        "report_id": report_id,
        "field_observation": field_observation,
        "disease_observed": disease_observed,
        "pathogen_identified": pathogen_identified,
        "verification_result": verification_result,
        "notes": notes,
        "evidence_photos": evidence_photos or [],
        "verified_at": now_iso,
        "agent_id": agent_id
    }
    task["updated_at"] = now_iso

    _AUDIT_LOG.append({
        "event": "FIELD_VERIFICATION_SUBMITTED",
        "task_id": task_id,
        "report_id": report_id,
        "verification_result": verification_result,
        "timestamp": now_iso
    })

    return {
        "success": True,
        "task_id": task_id,
        "report_id": report_id,
        "verification_result": verification_result,
        "disease_confirmed": is_verified,
        "downstream_action": downstream_action,
        "chemical_recommendation_new_status": new_chem_status,
        "message": f"Verification submitted: {verification_result}."
    }
