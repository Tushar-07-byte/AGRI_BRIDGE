"""
AgriBridge Master Orchestration Service
Integration Layer between AI/ML Intelligence, Backend Persistence, Calendar Scheduling,
Notification Delivery, Weather Re-check, Rescheduling, and Field Agent Escalation.
"""

import os
import json
from ..domain.multi_signal_decision import DecisionResult
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from ..models.action_plan import ActionPlan, PlanTask, CalendarEvent, NotificationEvent, FieldAgentEscalation
from ..models.farmer import Farmer
from ..models.user import User
from ..crop_monitoring.lifecycle_engine import calculate_crop_lifecycle
from ..crop_monitoring.weather_context import get_monitoring_weather_context
from ..crop_monitoring.calendar_engine import generate_calendar_events
from ..crop_monitoring.notification_engine import generate_farmer_notifications
from ..crop_monitoring.gemini_engine import generate_crop_recommendation
from ..services.timing_advice_service import calculate_timing_advice
from ..domain.farm_decision_context import FarmDecisionContext
from ..services.farm_decision_context_service import FarmDecisionContextService
from ..services.multi_signal_policy_engine import MultiSignalPolicyEngine

logger = logging.getLogger("agribridge.orchestration")


class OrchestrationService:

    @staticmethod
    def evaluate_escalation_policy(
        overall_risk: str,
        weather_decision: str,
        has_inspection_uncertainty: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Implements the strict AgriBridge escalation policy:
          - LOW: Routine monitoring (Escalation = False)
          - MODERATE: Farmer action + monitoring (Escalation = False)
          - HIGH: Field agent routing (Escalation = True)
          - CRITICAL: Field agent routing (Escalation = True)
          - HIGH/CRITICAL disease inspection uncertainty: Field agent routing (Escalation = True)
        """
        norm_risk = (overall_risk or "moderate").strip().lower()

        if has_inspection_uncertainty:
            return True, "High inspection uncertainty in crop diagnosis requires on-site field agent verification."

        if norm_risk in ["critical", "severe"]:
            return True, "Critical agronomic risk detected. Field agent on-site intervention dispatched."
        elif norm_risk in ["high"]:
            return True, "High weather and pest/disease pressure detected. Routing to local agricultural field agent."
        elif norm_risk in ["moderate", "medium"]:
            return False, "Moderate risk: Recommended for farmer action and routine monitoring."
        else: # low
            return False, "Low risk: Continue standard routine monitoring protocol."

    @staticmethod
    async def orchestrate_farm_plan(
        state: str,
        district: str,
        village: Optional[str] = None,
        crop_id: str = "rice",
        planting_date: Optional[str] = None,
        current_stage: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        farmer_id: Optional[int] = None,
        current_user: Optional[User] = None,
        db: Session = None,
        decision_context: Optional[FarmDecisionContext] = None,
        soil_moisture_vwc: Optional[float] = None,
        rain_probability: Optional[int] = None,
    ) -> Dict[str, Any]:
        "Master orchestration pipeline: Resolve & Authenticate Farmer; Bind FarmDecisionContext; Execute AI/ML; Evaluate escalation; Persist plan; Deliver notifications."
        logger.info(f"[Orchestration] Starting orchestration for crop={crop_id}, location={district}, {state}")

        # ----------------------------------------------------
        # 1. Resolve Farmer Identity
        # ----------------------------------------------------
        resolved_farmer_id = farmer_id
        if current_user and current_user.role == "farmer":
            # Link to existing farmer record or create matching farmer record
            farmer_rec = db.query(Farmer).filter(Farmer.name == current_user.name).first() if db else None
            if not farmer_rec and db:
                farmer_rec = Farmer(
                    name=current_user.name,
                )
                db.add(farmer_rec)
                db.flush()
            if farmer_rec:
                resolved_farmer_id = farmer_rec.id

        if not resolved_farmer_id and db:
            first_farmer = db.query(Farmer).first()
            if not first_farmer:
                first_farmer = Farmer(name="Demo Farmer")
                db.add(first_farmer)
                db.flush()
            resolved_farmer_id = first_farmer.id

        crop_norm = (crop_id or "rice").strip().lower()
        s_clean = (state or "Uttar Pradesh").strip()
        d_clean = (district or "Sultanpur").strip()
        v_clean = (village or "Dhanpatganj").strip() if village else "Dhanpatganj"

        # ----------------------------------------------------
        # 2. Canonical FarmDecisionContext Binding (Phase 2)
        # ----------------------------------------------------
        if decision_context is None:
            from ..services.farm_decision_context_service import FarmDecisionContextService
            telemetry_payload = {"soil_moisture_vwc": soil_moisture_vwc} if soil_moisture_vwc is not None else None
            weather_payload = {"rain_probability_percent": rain_probability} if rain_probability is not None else None
            decision_context = await FarmDecisionContextService.build_context(
                farmer_id=resolved_farmer_id,
                db=db,
                state=s_clean,
                district=d_clean,
                village=v_clean,
                crop_id=crop_norm,
                planting_date=planting_date,
                current_stage=current_stage,
                latitude=latitude,
                longitude=longitude,
                telemetry_data=telemetry_payload,
                weather_override=weather_payload
            )

        # ----------------------------------------------------
        # 2. AI/ML Intelligence Pipeline
        # ----------------------------------------------------
        # A. Lifecycle
        lifecycle = calculate_crop_lifecycle(crop_norm, planting_date, current_stage)
        stage_resolved = current_stage or lifecycle.get("current_stage", "Active Growth")

        # B. Open-Meteo Weather
        weather_context = await get_monitoring_weather_context(
            state=s_clean,
            district=d_clean,
            village=v_clean,
            latitude=latitude,
            longitude=longitude
        )

        risks = weather_context.get("risks", {})
        overall_risk = risks.get("overall_risk", "moderate").lower()
        weather_decision = weather_context.get("decision", "Keep")

        # C. Gemini / Scientific Action Recommendation
        recommendation = await generate_crop_recommendation(
            state=s_clean,
            district=d_clean,
            village=v_clean,
            crop_id=crop_norm,
            planting_date=planting_date,
            current_stage=stage_resolved,
            latitude=latitude,
            longitude=longitude,
            farmer_id=str(resolved_farmer_id),
            db_session=db
        )

        # D. Dynamic Calendar Events
        calendar_events = generate_calendar_events(
            crop_id=crop_norm,
            planting_date=planting_date,
            farmer_id=str(resolved_farmer_id),
            weather_context=weather_context
        )

        # ----------------------------------------------------
        # 2E. Farmer Notification Events
        # ----------------------------------------------------
        notification_events = generate_farmer_notifications(
            crop_id=crop_norm,
            planting_date=planting_date,
            current_stage=stage_resolved,
            farmer_id=str(resolved_farmer_id),
            weather_context=weather_context
        )

        # ----------------------------------------------------
        # 3. Deterministic Multi-Signal Policy Evaluation (Phase 3)
        # ----------------------------------------------------
        from ..services.multi_signal_policy_engine import MultiSignalPolicyEngine
        multi_signal_decision = MultiSignalPolicyEngine.evaluate(decision_context) if decision_context else None

        # ----------------------------------------------------
        # 4. Escalation Policy Evaluation
        # ----------------------------------------------------
        if multi_signal_decision:
            if "WEATHER_RAIN_BLOCK" in multi_signal_decision.constraints or "WEATHER_WIND_DRIFT_BLOCK" in multi_signal_decision.constraints:
                weather_decision = "Postpone"
            overall_risk = multi_signal_decision.overall_risk

        escalation_required, escalation_reason = OrchestrationService.evaluate_escalation_policy(
            overall_risk=overall_risk,
            weather_decision=weather_decision
        )

        if multi_signal_decision and multi_signal_decision.escalation_required:
            escalation_required = True
            escalation_reason = multi_signal_decision.escalation_reason or escalation_reason

        # ----------------------------------------------------
        # 5. Database Persistence & Idempotency
        # ----------------------------------------------------
        action_plan = None
        if db:
            # Check for existing active plan for same farmer + crop + stage created today (Idempotency)
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            existing_plan = (
                db.query(ActionPlan)
                .filter(
                    ActionPlan.farmer_id == resolved_farmer_id,
                    ActionPlan.crop_id == crop_norm,
                    ActionPlan.crop_stage == stage_resolved,
                    ActionPlan.status == "active",
                    ActionPlan.created_at >= today_start
                )
                .order_by(ActionPlan.id.desc())
                .first()
            )

            if existing_plan:
                logger.info(f"[Orchestration] Reusing existing active ActionPlan #{existing_plan.id} (Idempotent)")
                action_plan = existing_plan
                action_plan.risk_level = overall_risk
                action_plan.escalation_required = escalation_required
                action_plan.escalation_reason = escalation_reason
                action_plan.recommendation_json = json.dumps(recommendation)
                action_plan.updated_at = datetime.utcnow()
            else:
                action_plan = ActionPlan(
                    farmer_id=resolved_farmer_id,
                    crop_id=crop_norm,
                    state=s_clean,
                    district=d_clean,
                    village=v_clean,
                    planting_date=planting_date,
                    crop_stage=stage_resolved,
                    risk_type="weather_delay" if weather_decision == "Postpone" else "disease_treatment",
                    risk_level=overall_risk,
                    status="active",
                    escalation_required=escalation_required,
                    escalation_reason=escalation_reason,
                    recommendation_json=json.dumps(recommendation),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(action_plan)
                db.flush()

            # Task Information (WHAT, WHEN, WHERE, WHY)
            rec_action = recommendation.get("recommended_action", f"Execute {crop_norm.capitalize()} {stage_resolved} management protocol")
            task_title = f"{crop_norm.capitalize()}: {rec_action[:80]}"
            task_description = (
                f"WHAT: {rec_action}\n"
                f"WHEN: {weather_decision} window ({recommendation.get('weather_summary', 'Clear window')})\n"
                f"WHERE: {v_clean}, {d_clean}, {s_clean}\n"
                f"WHY: Stage {stage_resolved} agronomic optimization. Environmental risk: {overall_risk.upper()}."
            )
            task_reasoning = (
                f"WHAT: {rec_action}. "
                f"WHEN: {weather_decision} window. "
                f"WHY: {recommendation.get('important_note', 'Targeted crop protection and nutrition schedule')}. "
                f"Risk Level: {overall_risk.upper()}."
            )
            # Persist deterministic decision payloads
            if multi_signal_decision:
                action_plan.decision_json = multi_signal_decision.json()
                action_plan.constraints_json = json.dumps(multi_signal_decision.constraints)
                action_plan.recommended_actions_json = json.dumps(multi_signal_decision.recommended_actions)
            else:
                action_plan.decision_json = None
                action_plan.constraints_json = None
                action_plan.recommended_actions_json = None

            # Check if active task already exists under this plan
            existing_task = (
                db.query(PlanTask)
                .filter(PlanTask.action_plan_id == action_plan.id, PlanTask.status == "pending")
                .first()
            )
            # Create PlanTask for each ALLOWED decision
            allowed_decisions = []
            if multi_signal_decision:
                allowed_decisions = [d for d in multi_signal_decision.decisions if d.result == DecisionResult.ALLOWED]

            # Determine scheduled window (used for all tasks)

            # Create the primary PlanTask (recommendation) if none exists
            if not existing_task:
                scheduled_window = datetime.utcnow() + timedelta(days=2 if weather_decision == "Postpone" else 1)
                plan_task = PlanTask(
                    action_plan_id=action_plan.id,
                    title=task_title,
                    description=task_description,
                    location=f"{v_clean}, {d_clean}, {s_clean}",
                    execution_window=recommendation.get("weather_summary", "Immediate favorable window"),
                    scheduled_for=scheduled_window,
                    status="pending",
                    reasoning=task_reasoning,
                    completed_at=None,
                )
                db.add(plan_task)
                db.flush()


            # Persist Calendar Events if not already saved
            existing_cal_count = db.query(CalendarEvent).filter(CalendarEvent.action_plan_id == action_plan.id).count()
            if existing_cal_count == 0:
                for idx, ev in enumerate(calendar_events[:8]):
                    act_obj = ev.get("activity", {})
                    if isinstance(act_obj, dict):
                        title_str = (
                            act_obj.get("crop_protection")
                            or act_obj.get("fertilizer")
                            or act_obj.get("irrigation")
                            or ev.get("crop_stage", "Crop Management Activity")
                        )
                        desc_str = f"Irrigation: {act_obj.get('irrigation', 'N/A')} | Fertilizer: {act_obj.get('fertilizer', 'N/A')} | Protection: {act_obj.get('crop_protection', 'N/A')}"
                    else:
                        title_str = str(act_obj)
                        desc_str = ev.get("description", "")

                    cal_record = CalendarEvent(
                        action_plan_id=action_plan.id,
                        farmer_id=resolved_farmer_id,
                        event_id=ev.get("event_id", f"{crop_norm.upper()}_EV_{idx+1}"),
                        crop_id=crop_norm,
                        stage_name=ev.get("crop_stage") or ev.get("stage_name", stage_resolved),
                        activity_type=ev.get("activity_type", "management"),
                        title=str(title_str)[:255],
                        description=desc_str,
                        scheduled_date=datetime.utcnow() + timedelta(days=idx * 7),
                        status="scheduled",
                        created_at=datetime.utcnow()
                    )
                    db.add(cal_record)

            # Persist & Deliver Notifications
            existing_notif_count = db.query(NotificationEvent).filter(NotificationEvent.action_plan_id == action_plan.id).count()
            if existing_notif_count == 0:
                for idx, n in enumerate(notification_events[:5]):
                    notif_record = NotificationEvent(
                        action_plan_id=action_plan.id,
                        farmer_id=resolved_farmer_id,
                        notification_id=n.get("notification_id", f"NOTIF_{crop_norm.upper()}_{idx+1}"),
                        title=n.get("title", "Crop Advisory Notification")[:255],
                        message=n.get("message", "Scheduled agricultural reminder."),
                        channel=n.get("channel", "sms_voice_app"),
                        priority=n.get("priority", "medium"),
                        status="NOTIFIED",  # Immediate backend delivery
                        scheduled_at=datetime.utcnow(),
                        delivered_at=datetime.utcnow(),
                        created_at=datetime.utcnow()
                    )
                    db.add(notif_record)

            # Persist Field Agent Escalation if required
            if escalation_required:
                existing_esc = (
                    db.query(FieldAgentEscalation)
                    .filter(FieldAgentEscalation.action_plan_id == action_plan.id)
                    .first()
                )
                if not existing_esc:
                    field_agent = db.query(User).filter(User.role.in_(["field-agent", "field_agent", "professional"])).first()
                    esc_record = FieldAgentEscalation(
                        action_plan_id=action_plan.id,
                        farmer_id=resolved_farmer_id,
                        field_agent_id=field_agent.id if field_agent else None,
                        risk_level=overall_risk,
                        reason=escalation_reason,
                        status="escalated",
                        created_at=datetime.utcnow()
                    )
                    db.add(esc_record)

            db.commit()
            db.refresh(action_plan)

        # ----------------------------------------------------
        # 5. Build Response Object
        # ----------------------------------------------------
        tasks_out = []
        if action_plan:
            for t in action_plan.tasks:
                tasks_out.append({
                    "id": t.id,
                    "title": t.title,
                    "status": t.status,
                    "scheduled_for": t.scheduled_for.isoformat() if t.scheduled_for else None,
                    "reasoning": t.reasoning
                })

        return {
            "success": True,
            "action_plan_id": action_plan.id if action_plan else 1,
            "action_plan": {"id": action_plan.id, "status": action_plan.status} if action_plan else None,
            "farmer_id": resolved_farmer_id,
            "crop": crop_norm,
            "crop_stage": stage_resolved,
            "overall_risk": overall_risk,
            "weather_decision": weather_decision,
            "escalation_required": escalation_required,
            "escalation_reason": escalation_reason,
            "recommendation": recommendation,
            "lifecycle": lifecycle,
            "weather_context": weather_context,
            "calendar_events": calendar_events,
            "notifications": notification_events,
            "tasks": tasks_out,
            "farm_decision_context_id": decision_context.context_id if decision_context else None,
            "decision_context": decision_context.dict() if decision_context else None,
            "signals_considered_count": len(decision_context.provenance_summary) if decision_context else 0,
            "multi_signal_decision": multi_signal_decision.dict() if multi_signal_decision else None
        }

    @staticmethod
    async def recheck_weather_and_reschedule(
        plan_id: int,
        simulated_rain: Optional[int] = None,
        simulated_condition: Optional[str] = None,
        recommended_window: Optional[str] = None,
        force_change: Optional[bool] = False,
        db: Session = None
    ) -> Dict[str, Any]:
        "Performs execution-time weather re-check and updates."
        """Performs execution-time weather re-check and updates using deterministic policy engine."""
        from ..domain.farm_decision_context import SignalProvenance, SignalQuality
        from ..domain.multi_signal_decision import DecisionType

        plan = db.query(ActionPlan).filter(ActionPlan.id == plan_id).first()
        if not plan:
            return {"success": False, "error": f"Action plan #{plan_id} not found."}

        # Find current active/pending task
        active_task = (
            db.query(PlanTask)
            .filter(PlanTask.action_plan_id == plan_id, PlanTask.status == "pending")
            .order_by(PlanTask.id.desc())
            .first()
        )
        if not active_task:
            active_task = db.query(PlanTask).filter(PlanTask.action_plan_id == plan_id).order_by(PlanTask.id.desc()).first()

        if not active_task:
            return {"success": False, "error": "No tasks found under action plan."}

        # Determine weather parameters
        if simulated_rain is not None:
            new_rain = simulated_rain
            new_risk = new_rain >= 60
            new_cond = simulated_condition or ("Heavy convective rain" if new_rain >= 60 else "Clear and dry skies")
            new_win = recommended_window or ("2026-09-08 (Dry Window)" if new_rain >= 60 else "Tomorrow Morning (6:00 AM - 9:00 AM)")
            weather_override = {
                "rain_probability_percent": new_rain,
                "condition": new_cond,
                "provenance": SignalProvenance.SIMULATED,
                "quality": SignalQuality.SIMULATED
            }
        else:
            loc = f"{plan.district or 'Sultanpur'}, {plan.state or 'Uttar Pradesh'}"
            live = await calculate_timing_advice(region_str=loc)
            new_rain = live.get("rain_probability", 0)
            new_risk = live.get("rain_risk", False)
            new_cond = live.get("advice", "Weather forecast updated.")
            new_win = live.get("recommended_window", "Next available dry window")
            weather_override = {
                "rain_probability_percent": new_rain,
                "condition": new_cond,
                "provenance": SignalProvenance.LIVE,
                "quality": SignalQuality.LIVE
            }

        was_weather_delay = (plan.risk_type == "weather_delay")
        new_risk = (new_rain >= 60)

        # Build fresh decision context for deterministic re-check
        context = await FarmDecisionContextService.build_context(
            farmer_id=plan.farmer_id,
            db=db,
            state=plan.state,
            district=plan.district,
            village=plan.village,
            crop_id=plan.crop_id,
            crop_name=None,
            variety=None,
            planting_date=plan.planting_date,
            current_stage=plan.crop_stage,
            season=None,
            farm_area=None,
            irrigation_method=None,
            irrigation_status=None,
            soil_type=None,
            soil_ph=None,
            nitrogen=None,
            phosphorus=None,
            potassium=None,
            latitude=None,
            longitude=None,
            disease_record_id=None,
            disease_scan_data=None,
            telemetry_data=None,
            weather_override=weather_override,
        )

        decision = MultiSignalPolicyEngine.evaluate(context)

        # Evaluate weather outcome from deterministic policy
        weather_item = next((d for d in decision.decisions if d.decision_type == DecisionType.WEATHER_TIMING), None)
        is_weather_blocked = (
            "WEATHER_RAIN_BLOCK" in decision.constraints
            or "WEATHER_WIND_DRIFT_BLOCK" in decision.constraints
            or (weather_item is not None and weather_item.result == DecisionResult.DEFERRED)
            or new_risk
        )

        change_type = "WEATHER_STABLE"
        clean_title = active_task.title.replace("Rescheduled: ", "").replace("Expedited: ", "").replace("Adapted: ", "")

        if is_weather_blocked:
            plan.risk_type = "weather_delay"
            if not was_weather_delay:
                change_type = "WEATHER_WORSENED_RAIN_SURGE"
            else:
                change_type = "WEATHER_UNSAFE_DEFERRED"

            # Reschedule pending task to favorable safe window
            fav_win = (context.weather.favorable_window.value if context.weather and context.weather.favorable_window else None) or new_win
            active_task.title = f"Rescheduled: {clean_title}"
            active_task.execution_window = fav_win
            active_task.scheduled_for = datetime.utcnow() + timedelta(days=3)
            active_task.reasoning = (
                f"Weather constraint detected: {weather_item.explanation if weather_item else 'Postponed due to precipitation'}. "
                f"Application postponed to safe window: {fav_win}."
            )

        else:
            # Weather is safe / ALLOWED
            if was_weather_delay:
                change_type = "WEATHER_CLEARED_SAFE_WINDOW"
                plan.risk_type = "disease_treatment"
                fav_win = (context.weather.favorable_window.value if context.weather and context.weather.favorable_window else None) or "Tomorrow Morning (6:00 AM - 9:00 AM)"
                active_task.title = f"Expedited: {clean_title}"
                active_task.execution_window = fav_win
                active_task.scheduled_for = datetime.utcnow() + timedelta(hours=18)
                active_task.reasoning = (
                    f"Weather cleared ({new_rain}% rain probability). "
                    f"Safe window available ({fav_win}). Execution authorized."
                )
            elif force_change:
                change_type = "WEATHER_STABLE_CONFIRMED"

        change_triggered = (change_type != "WEATHER_STABLE") or force_change

        # Persist updated decision on ActionPlan
        plan.decision_json = decision.json() if hasattr(decision, "json") else json.dumps(decision.dict() if hasattr(decision, "dict") else decision.__dict__)
        plan.constraints_json = json.dumps(decision.constraints if hasattr(decision, "constraints") else [])
        plan.recommended_actions_json = json.dumps(decision.recommended_actions if hasattr(decision, "recommended_actions") else [])
        plan.updated_at = datetime.utcnow()
        db.add(plan)
        db.add(active_task)

        if change_triggered:
            # Update Calendar event if present
            cal_event = db.query(CalendarEvent).filter(CalendarEvent.action_plan_id == plan.id).first()
            if cal_event:
                cal_event.scheduled_date = active_task.scheduled_for
                cal_event.status = "rescheduled"

            # Emit notification event
            notif = NotificationEvent(
                action_plan_id=plan.id,
                farmer_id=plan.farmer_id,
                notification_id=f"REPLAN_{plan.id}_{active_task.id}",
                title=f"Schedule Adapted: {active_task.title[:60]}",
                message=active_task.reasoning,
                channel="sms_voice_app",
                priority="high",
                status="NOTIFIED",
                scheduled_at=datetime.utcnow(),
                delivered_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            db.add(notif)

        db.commit()
        db.refresh(plan)
        db.refresh(active_task)

        # Build unified response
        task_info = {
            "id": active_task.id,
            "title": active_task.title,
            "status": active_task.status,
            "scheduled_for": active_task.scheduled_for.isoformat() if active_task.scheduled_for else None,
            "execution_window": active_task.execution_window,
            "reasoning": active_task.reasoning,
        }
        response = {
            "success": True,
            "action_plan_id": plan.id,
            "change_detected": change_triggered,
            "change_type": change_type if change_triggered else "WEATHER_STABLE",
            "message": (
                "Weather shift detected. Schedule adapted based on deterministic policy."
                if change_triggered
                else f"Weather rechecked ({new_rain}% rain probability). Current execution window remains optimal."
            ),
            "decision": decision.dict() if hasattr(decision, "dict") else decision.__dict__,
            "current_task": task_info,
            "new_task": task_info,
            "superseded_task_id": active_task.id,
        }
        return response

    @staticmethod
    def update_notification_lifecycle(
        notification_id: int,
        status: str,
        db: Session
    ) -> Dict[str, Any]:
        "Updates notification status through: PENDING -> NOTIFIED -> ACKNOWLEDGED -> IN_PROGRESS -> COMPLETED (or SKIPPED / ESCALATED)."
        notif = db.query(NotificationEvent).filter(NotificationEvent.id == notification_id).first()
        if not notif:
            return {"success": False, "error": f"Notification #{notification_id} not found."}

        norm_status = status.strip().upper()
        valid_states = {"PENDING", "NOTIFIED", "ACKNOWLEDGED", "IN_PROGRESS", "COMPLETED", "SKIPPED", "ESCALATED"}
        if norm_status not in valid_states:
            return {"success": False, "error": f"Invalid notification status. Must be one of: {list(valid_states)}"}

        notif.status = norm_status
        now = datetime.utcnow()
        if norm_status == "NOTIFIED" and not notif.delivered_at:
            notif.delivered_at = now
        elif norm_status == "ACKNOWLEDGED":
            notif.acknowledged_at = now
        elif norm_status in ["COMPLETED", "SKIPPED"]:
            notif.completed_at = now

        db.commit()
        db.refresh(notif)
        return {
            "success": True,
            "notification": {
                "id": notif.id,
                "notification_id": notif.notification_id,
                "status": notif.status,
                "delivered_at": notif.delivered_at.isoformat() if notif.delivered_at else None,
                "acknowledged_at": notif.acknowledged_at.isoformat() if notif.acknowledged_at else None,
                "completed_at": notif.completed_at.isoformat() if notif.completed_at else None,
            }
        }

    @staticmethod
    def update_task_status(
        task_id: int,
        status: str,
        db: Session
    ) -> Dict[str, Any]:
        """Update PlanTask status with minimal lifecycle validation.

        Valid transitions (minimal):
        PENDING -> ACKNOWLEDGED -> IN_PROGRESS -> COMPLETED
        Other states are allowed but must be one of the defined enum strings.
        """
        task = db.query(PlanTask).filter(PlanTask.id == task_id).first()
        if not task:
            return {"success": False, "error": f"PlanTask #{task_id} not found."}
        norm_status = status.strip().upper()
        valid_states = {"PENDING", "ACKNOWLEDGED", "IN_PROGRESS", "COMPLETED", "SKIPPED", "ESCALATED"}
        if norm_status not in valid_states:
            return {"success": False, "error": f"Invalid task status. Must be one of: {list(valid_states)}"}
        # Simple transition validation
        current = task.status.upper()
        allowed = {
            "PENDING": {"ACKNOWLEDGED", "SKIPPED", "ESCALATED"},
            "ACKNOWLEDGED": {"IN_PROGRESS", "SKIPPED", "ESCALATED"},
            "IN_PROGRESS": {"COMPLETED", "SKIPPED", "ESCALATED"},
        }
        if norm_status != current and norm_status not in allowed.get(current, set()):
            return {"success": False, "error": f"Invalid transition from {current} to {norm_status}."}
        task.status = norm_status.lower() if norm_status != "COMPLETED" else "completed"
        if norm_status == "COMPLETED":
            task.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
        return {"success": True, "task": {"id": task.id, "status": task.status, "completed_at": task.completed_at.isoformat() if task.completed_at else None}}

