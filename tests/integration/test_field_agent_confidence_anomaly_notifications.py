import unittest
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.field_agent_engine import (
    evaluate_disease_confidence,
    evaluate_sensor_telemetry,
    create_field_agent_task,
    accept_field_agent_task,
    reject_field_agent_task,
    submit_field_verification,
    get_field_agent_tasks,
    get_confidence_config
)
from app.services.notification_delivery_service import (
    create_notification,
    enqueue_and_deliver,
    retry_failed_notification,
    mark_notification_read,
    get_farmer_notifications
)
from app.crop_monitoring.safety_validator import enforce_disease_safety_policy
from app.crop_monitoring.lifecycle_engine import calculate_crop_lifecycle


class TestFieldAgentConfidenceAnomalyNotificationSystem(unittest.TestCase):

    # 1. High-confidence disease does NOT escalate
    def test_high_confidence_disease_no_escalation(self):
        res = evaluate_disease_confidence(
            confidence=0.91,
            disease_name="Wheat Yellow Rust",
            crop_name="Wheat",
            verified_treatment_exists=True,
            treatment_details={"chemical": "Propiconazole 25% EC"}
        )
        self.assertEqual(res["confidence_status"], "ACCEPTABLE")
        self.assertFalse(res["field_agent_escalation"])
        self.assertEqual(res["chemical_recommendation"]["status"], "AVAILABLE")

    # 2. Low-confidence disease DOES escalate
    def test_low_confidence_disease_escalates(self):
        res = evaluate_disease_confidence(
            confidence=0.54,
            disease_name="Wheat Yellow Rust",
            crop_name="Wheat",
            verified_treatment_exists=True
        )
        self.assertEqual(res["confidence_status"], "LOW")
        self.assertTrue(res["field_agent_escalation"])
        self.assertEqual(res["escalation_reason"], "LOW_CONFIDENCE_DISEASE_PREDICTION")

    # 3. Low-confidence disease locks chemical recommendation
    def test_low_confidence_disease_locks_chemical(self):
        res = evaluate_disease_confidence(
            confidence=0.48,
            disease_name="Tomato Early Blight",
            crop_name="Tomato"
        )
        self.assertEqual(res["chemical_recommendation"]["status"], "LOCKED")
        self.assertEqual(res["chemical_recommendation"]["reason"], "LOW_DISEASE_CONFIDENCE")
        self.assertIsNone(res["chemical_recommendation"]["pesticide_name"])
        self.assertIn("Field Agent verification is required", res["farmer_message"])

    # 4. High-confidence disease unlocks valid treatment guidance
    def test_high_confidence_disease_unlocks_valid_treatment(self):
        res = evaluate_disease_confidence(
            confidence=0.85,
            disease_name="Rice Blast",
            crop_name="Rice",
            verified_treatment_exists=True,
            treatment_details={"chemical": "Tricyclazole 75% WP @ 0.6g/L"}
        )
        self.assertEqual(res["confidence_status"], "ACCEPTABLE")
        self.assertEqual(res["chemical_recommendation"]["status"], "AVAILABLE")
        self.assertIsNotNone(res["chemical_recommendation"]["treatment_details"])

    # 5. Missing treatment knowledge keeps recommendation unavailable
    def test_missing_treatment_knowledge_unavailable(self):
        res = evaluate_disease_confidence(
            confidence=0.92,
            disease_name="Rare Pathogen Condition",
            crop_name="Wheat",
            verified_treatment_exists=False
        )
        self.assertEqual(res["confidence_status"], "ACCEPTABLE")
        self.assertEqual(res["chemical_recommendation"]["status"], "UNAVAILABLE")
        self.assertEqual(res["chemical_recommendation"]["reason"], "NO_VERIFIED_TREATMENT_IN_KB")

    # 6. Gemini cannot bypass chemical lock
    def test_gemini_cannot_bypass_chemical_lock(self):
        mock_payload = {
            "crop_protection_guidance": "I diagnose confirmed disease. Spray Mancozeb 75% WP 3g/L immediately.",
            "safety_information": ""
        }
        sanitized = enforce_disease_safety_policy(mock_payload, chemical_locked=True)
        self.assertIn("Chemical treatment guidance is locked", sanitized["crop_protection_guidance"])
        self.assertNotIn("Mancozeb", sanitized["crop_protection_guidance"])
        self.assertNotIn("I diagnose", sanitized["crop_protection_guidance"])

    # 7. Unusual sensor reading escalates
    def test_unusual_sensor_reading_escalates(self):
        # Soil moisture 0% in irrigated field
        res = evaluate_sensor_telemetry(
            sensor_id="SN_SOIL_99",
            sensor_type="soil_moisture",
            value=0.0,
            crop_name="Wheat"
        )
        self.assertTrue(res["anomaly_detected"])
        self.assertTrue(res["field_agent_escalation"])
        self.assertEqual(res["escalation_reason"], "UNUSUAL_SENSOR_READING")

    # 8. Normal sensor reading does not escalate
    def test_normal_sensor_reading_no_escalation(self):
        res = evaluate_sensor_telemetry(
            sensor_id="SN_SOIL_01",
            sensor_type="soil_moisture",
            value=45.0,
            crop_name="Wheat"
        )
        self.assertFalse(res["anomaly_detected"])
        self.assertFalse(res["field_agent_escalation"])
        self.assertEqual(res["priority"], "LOW")

    # 9. Field Agent can ACCEPT
    def test_field_agent_accept(self):
        task = create_field_agent_task(
            trigger_type="LOW_CONFIDENCE_DISEASE_PREDICTION",
            reason="Confidence 0.52 below threshold",
            payload={"confidence": 0.52}
        )
        task_id = task["task_id"]
        accept_res = accept_field_agent_task(task_id, agent_id="AGENT_007", agent_name="Rahul Verma")
        self.assertTrue(accept_res["success"])
        self.assertEqual(accept_res["status"], "ACCEPTED")

    # 10. Field Agent can REJECT
    def test_field_agent_reject(self):
        task = create_field_agent_task(
            trigger_type="UNUSUAL_SENSOR_READING",
            reason="Zero reading",
            payload={"value": 0.0}
        )
        task_id = task["task_id"]
        reject_res = reject_field_agent_task(task_id, rejection_reason="Out of operational jurisdiction")
        self.assertTrue(reject_res["success"])
        self.assertEqual(reject_res["status"], "REJECTED")

    # 11. Reject requires a reason
    def test_reject_requires_reason(self):
        task = create_field_agent_task(
            trigger_type="UNUSUAL_SENSOR_READING",
            reason="Zero reading",
            payload={"value": 0.0}
        )
        task_id = task["task_id"]
        with self.assertRaises(ValueError):
            reject_field_agent_task(task_id, rejection_reason="")

    # 12. Verification updates escalation state
    def test_verification_updates_escalation_state(self):
        task = create_field_agent_task(
            trigger_type="LOW_CONFIDENCE_DISEASE_PREDICTION",
            reason="Confidence 0.49",
            payload={"confidence": 0.49}
        )
        task_id = task["task_id"]
        accept_field_agent_task(task_id)
        
        verif_res = submit_field_verification(
            task_id=task_id,
            field_observation="Visible orange pustules confirmed on leaves",
            disease_observed="YES",
            verification_result="VERIFIED_DISEASE",
            pathogen_identified="Wheat Yellow Rust"
        )
        self.assertTrue(verif_res["success"])
        self.assertEqual(verif_res["verification_result"], "VERIFIED_DISEASE")
        self.assertEqual(verif_res["downstream_action"], "UNLOCK_TREATMENT_ADVISORY")
        self.assertEqual(verif_res["chemical_recommendation_new_status"], "AVAILABLE")

    # 13. Notification is not marked delivered merely when created
    def test_notification_creation_not_delivered_immediately(self):
        notif = create_notification(
            farmer_id="FARMER_201",
            title="Advisory Created",
            message="Advisory in buffer",
            auto_deliver=False
        )
        self.assertEqual(notif["delivery_status"], "CREATED")
        self.assertIsNone(notif["delivered_at"])

    # 14. Notification delivery status is tracked
    def test_notification_delivery_status_tracking(self):
        notif = create_notification(
            farmer_id="FARMER_202",
            title="Weather Alert",
            message="Rain expected",
            auto_deliver=False
        )
        self.assertEqual(notif["delivery_status"], "CREATED")
        
        # Dispatch
        delivered = enqueue_and_deliver(notif["notification_id"])
        self.assertEqual(delivered["delivery_status"], "DELIVERED")
        self.assertIsNotNone(delivered["delivered_at"])
        
        # Read
        read_notif = mark_notification_read(notif["notification_id"])
        self.assertEqual(read_notif["delivery_status"], "READ")
        self.assertIsNotNone(read_notif["read_at"])

    # 15. Failed notification can retry
    def test_failed_notification_retry(self):
        notif = create_notification(
            farmer_id="FARMER_203",
            title="Urgent Alert",
            message="Check field",
            auto_deliver=False
        )
        failed = enqueue_and_deliver(notif["notification_id"], simulate_failure=True)
        self.assertEqual(failed["delivery_status"], "FAILED")
        
        retried = retry_failed_notification(notif["notification_id"], use_fallback=True)
        self.assertEqual(retried["delivery_status"], "DELIVERED")
        self.assertEqual(retried["channel"], "SMS_GATEWAY")
        self.assertGreaterEqual(retried["retry_count"], 1)

    # 16. Existing monitoring system continues to work
    def test_crop_stage_engine_preserved(self):
        lifecycle = calculate_crop_lifecycle(crop_id="wheat", planting_date="2026-01-01", current_stage=None)
        self.assertIn("current_stage", lifecycle)
        self.assertIn("days_after_planting", lifecycle)
        self.assertIsNotNone(lifecycle["current_stage"])


if __name__ == "__main__":
    unittest.main()

