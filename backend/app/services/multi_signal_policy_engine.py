"""
AgriBridge Multi-Signal Policy Engine
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

A pure, deterministic, explainable policy evaluation layer that consumes the
canonical FarmDecisionContext and produces structured MultiSignalDecision findings.

Guarantees:
- Zero database writes
- Zero external network / API calls
- Zero LLM calls
- Deterministic conflict resolution precedence
- Strict preservation of the [30%, 65%) clinical confidence gate
- Strict preservation of SIMULATED and DECLARED provenances
- Complete chronological decision audit trace
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..domain.farm_decision_context import FarmDecisionContext, SignalProvenance, SignalQuality
from .utils import is_signal_trustworthy
from ..domain.multi_signal_decision import (
    DecisionResult,
    DecisionTraceItem,
    DecisionType,
    MultiSignalDecision,
    PolicyDecisionItem,
)


class MultiSignalPolicyEngine:
    """
    Deterministic Multi-Signal Policy Evaluator for AgriBridge.
    Evaluates cross-domain farm signals and produces structured, traceable decisions.
    """

    @staticmethod
    def evaluate(context: FarmDecisionContext) -> MultiSignalDecision:
        """
        Master evaluation method.
        Inspects all 8 sub-states of FarmDecisionContext, applies domain policies,
        resolves multi-signal conflicts, and produces a MultiSignalDecision.
        """
        decision_id = f"DEC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        decisions: List[PolicyDecisionItem] = []
        trace: List[DecisionTraceItem] = []
        constraints: List[str] = []
        blocked_actions: List[str] = []
        recommended_actions: List[str] = []
        signals_inspected = 0

        escalation_required = False
        escalation_reason = None

        # ----------------------------------------------------------------------
        # 1. EVALUATE DISEASE & CLINICAL CONFIDENCE POLICY
        # ----------------------------------------------------------------------
        disease_finding, d_trace, d_signals = MultiSignalPolicyEngine._evaluate_disease_policy(context)
        decisions.append(disease_finding)
        trace.extend(d_trace)
        signals_inspected += d_signals
        constraints.extend(disease_finding.constraints_added)

        if disease_finding.result == DecisionResult.REQUIRES_HUMAN_REVIEW:
            escalation_required = True
            escalation_reason = disease_finding.explanation
            blocked_actions.append(f"Autonomous chemical prescription for {context.disease.pathogen_name.value or 'crop condition'}")
        elif disease_finding.result == DecisionResult.BLOCKED:
            blocked_actions.append("Autonomous diagnosis (rejected for low confidence)")
        elif disease_finding.result == DecisionResult.ALLOWED and context.disease.has_diagnosis:
            pathogen = context.disease.pathogen_name.value or "identified crop condition"
            recommended_actions.append(f"Prepare ICAR standard treatment protocol for {pathogen}")

        # ----------------------------------------------------------------------
        # 2. EVALUATE WEATHER & EXECUTION CONSTRAINTS POLICY
        # ----------------------------------------------------------------------
        weather_finding, w_trace, w_signals = MultiSignalPolicyEngine._evaluate_weather_policy(context)
        decisions.append(weather_finding)
        trace.extend(w_trace)
        signals_inspected += w_signals
        constraints.extend(weather_finding.constraints_added)

        if weather_finding.result == DecisionResult.DEFERRED:
            if "WEATHER_RAIN_BLOCK" in weather_finding.constraints_added:
                blocked_actions.append("Immediate outdoor foliar spraying and irrigation")
            if "WEATHER_WIND_DRIFT_BLOCK" in weather_finding.constraints_added:
                blocked_actions.append("High-wind foliar spraying (drift hazard)")
        elif weather_finding.result == DecisionResult.ALLOWED:
            recommended_actions.append(weather_finding.action)

        # ----------------------------------------------------------------------
        # 3. EVALUATE TELEMETRY & SOIL MOISTURE POLICY
        # ----------------------------------------------------------------------
        telemetry_finding, t_trace, t_signals = MultiSignalPolicyEngine._evaluate_telemetry_policy(context, constraints)
        decisions.append(telemetry_finding)
        trace.extend(t_trace)
        signals_inspected += t_signals
        constraints.extend(telemetry_finding.constraints_added)

        if telemetry_finding.result == DecisionResult.ALLOWED and telemetry_finding.reason_code == "LOW_SOIL_MOISTURE_IRRIGATION_NEEDED":
            recommended_actions.append(telemetry_finding.action)
        elif telemetry_finding.result == DecisionResult.BLOCKED:
            blocked_actions.append("Field irrigation (soil already saturated)")
        elif telemetry_finding.result == DecisionResult.DEFERRED:
            blocked_actions.append("Immediate irrigation (deferred for incoming rainfall)")

        # ----------------------------------------------------------------------
        # 4. EVALUATE SOIL NUTRIENT & NPK POLICY
        # ----------------------------------------------------------------------
        nutrient_finding, n_trace, n_signals = MultiSignalPolicyEngine._evaluate_nutrient_policy(context)
        decisions.append(nutrient_finding)
        trace.extend(n_trace)
        signals_inspected += n_signals
        constraints.extend(nutrient_finding.constraints_added)

        if nutrient_finding.result == DecisionResult.REQUIRES_HUMAN_REVIEW:
            blocked_actions.append("Additional nitrogen fertilizer top-dressing")
        elif nutrient_finding.result == DecisionResult.ALLOWED and nutrient_finding.reason_code == "BALANCED_NITROGEN_LEVELS":
            recommended_actions.append(nutrient_finding.action)

        # ----------------------------------------------------------------------
        # 5. EVALUATE MARKET & COMMERCIAL POLICY
        # ----------------------------------------------------------------------
        market_finding, m_trace, m_signals = MultiSignalPolicyEngine._evaluate_market_policy(context)
        decisions.append(market_finding)
        trace.extend(m_trace)
        signals_inspected += m_signals
        constraints.extend(market_finding.constraints_added)

        if market_finding.result == DecisionResult.ALLOWED and market_finding.reason_code == "MARKET_LISTING_ACTIVE":
            recommended_actions.append(market_finding.action)

        # ----------------------------------------------------------------------
        # 6. MULTI-SIGNAL CONFLICT RESOLUTION & SYNTHESIS
        # ----------------------------------------------------------------------
        overall_risk, priority = MultiSignalPolicyEngine._resolve_risk_and_priority(
            context=context,
            decisions=decisions,
            constraints=constraints,
            escalation_required=escalation_required
        )

        # Precedence Rule: If treatment is indicated BUT Weather blocks execution -> defer treatment
        if context.disease.has_diagnosis and context.disease.confidence_percent.value and context.disease.confidence_percent.value >= 65.0:
            if "WEATHER_RAIN_BLOCK" in constraints or "WEATHER_WIND_DRIFT_BLOCK" in constraints:
                # Remove from immediate recommended actions, replace with deferred execution
                pathogen = context.disease.pathogen_name.value or "identified disease"
                recommended_actions = [a for a in recommended_actions if pathogen not in a]
                fav_win = context.weather.favorable_window.value or "next available dry window"
                deferred_treatment = f"Treatment for {pathogen} authorized but deferred until {fav_win} due to weather constraint"
                recommended_actions.append(deferred_treatment)
                trace.append(
                    DecisionTraceItem(
                        signal="multi_signal.conflict_resolution",
                        value="DISEASE_ACTION_REQUIRED + WEATHER_EXECUTION_BLOCKED",
                        unit="logical_conflict",
                        source="multi_signal_policy_engine",
                        provenance="DERIVED",
                        policy="safety_precedence_rule_2",
                        condition="treatment_indicated=True AND weather_block=True",
                        effect="treatment_deferred_to_favorable_window"
                    )
                )

        # De-duplicate lists preserving order
        unique_constraints = list(dict.fromkeys(constraints))
        unique_blocked = list(dict.fromkeys(blocked_actions))
        unique_recommended = list(dict.fromkeys(recommended_actions))

        # Copy context provenance summary
        prov_summary = context.provenance_summary or context.compile_provenance_summary()

        return MultiSignalDecision(
            decision_id=decision_id,
            context_id=context.context_id,
            overall_risk=overall_risk,
            priority=priority,
            decisions=decisions,
            constraints=unique_constraints,
            blocked_actions=unique_blocked,
            recommended_actions=unique_recommended,
            escalation_required=escalation_required,
            escalation_reason=escalation_reason,
            signals_considered=signals_inspected,
            decision_trace=trace,
            provenance_summary=prov_summary,
            generated_at=datetime.utcnow().isoformat()
        )

    # ==========================================================================
    # SUB-POLICY EVALUATORS (Deterministic Rules)
    # ==========================================================================

    @staticmethod
    def _evaluate_disease_policy(
        context: FarmDecisionContext
    ) -> Tuple[PolicyDecisionItem, List[DecisionTraceItem], int]:
        """
        Evaluates clinical disease detection using the strict 3-tier confidence contract:
          - conf < 30.0%: Reject out-of-domain
          - 30.0% <= conf < 65.0%: Borderline -> Human Expert Review, Prescription Locked
          - conf >= 65.0%: Actionable treatment protocol
        """
        trace: List[DecisionTraceItem] = []
        constraints: List[str] = []

        # Trust check for disease confidence signal
        if not is_signal_trustworthy(context.disease.confidence_percent):
            trace.append(
                DecisionTraceItem(
                    signal="disease.confidence_percent",
                    value=context.disease.confidence_percent.value,
                    unit="%",
                    source=context.disease.confidence_percent.source,
                    provenance=str(context.disease.confidence_percent.provenance),
                    policy="signal_quality_check",
                    condition="confidence signal untrusted",
                    effect="diagnosis_deferred_due_to_untrusted_signal"
                )
            )
            constraints.append("UNTRUSTED_DISEASE_CONFIDENCE")
            return (
                PolicyDecisionItem(
                    decision_type=DecisionType.DISEASE_TREATMENT,
                    result=DecisionResult.DEFERRED,
                    reason_code="UNTRUSTED_DISEASE_CONFIDENCE",
                    signals=["disease.confidence_percent"],
                    policy="signal_quality_check",
                    action="Defer disease evaluation until confidence signal is trustworthy",
                    explanation="Disease confidence signal failed trust validation (quality not VALID or stale timestamp).",
                    constraints_added=constraints
                ),
                trace,
                1
            )
        if not context.disease.has_diagnosis:
            trace.append(
                DecisionTraceItem(
                    signal="disease.has_diagnosis",
                    value=False,
                    unit="boolean",
                    source=context.disease.model_name.source or "ai_engine",
                    provenance=str(context.disease.pathogen_name.provenance),
                    policy="icar_clinical_confidence_gate_v1",
                    condition="has_diagnosis == False",
                    effect="no_active_pathology"
                )
            )
            return (
                PolicyDecisionItem(
                    decision_type=DecisionType.DISEASE_TREATMENT,
                    result=DecisionResult.ALLOWED,
                    reason_code="NO_ACTIVE_PATHOLOGY",
                    signals=["disease.has_diagnosis"],
                    policy="icar_clinical_confidence_gate_v1",
                    action="Continue routine agronomic crop scouting",
                    explanation="No clinical plant disease detected. Maintain standard monitoring.",
                    constraints_added=[]
                ),
                trace,
                1
            )

        conf_pct = context.disease.confidence_percent.value or 0.0
        pathogen = context.disease.pathogen_name.value or "Unspecified Crop Condition"
        source = context.disease.confidence_percent.source or "EfficientNet-B0"
        prov = str(context.disease.confidence_percent.provenance)

        trace.append(
            DecisionTraceItem(
                signal="disease.pathogen_name",
                value=pathogen,
                unit="taxonomy",
                source=context.disease.pathogen_name.source or "pathology_model",
                provenance=str(context.disease.pathogen_name.provenance),
                policy="icar_clinical_confidence_gate_v1",
                condition=f"pathogen = {pathogen}",
                effect="target_disease_identified"
            )
        )
        trace.append(
            DecisionTraceItem(
                signal="disease.confidence_percent",
                value=conf_pct,
                unit="%",
                source=source,
                provenance=prov,
                policy="icar_clinical_confidence_gate_v1",
                condition=f"confidence = {conf_pct:.2f}%",
                effect="confidence_bracket_evaluation"
            )
        )

        if conf_pct < 30.0:
            constraints.append("DIAGNOSIS_UNRELIABLE_REJECTED")
            trace.append(
                DecisionTraceItem(
                    signal="disease.confidence_percent",
                    value=conf_pct,
                    unit="%",
                    source=source,
                    provenance=prov,
                    policy="icar_clinical_confidence_gate_v1",
                    condition="confidence < 30.0%",
                    effect="diagnosis_rejected"
                )
            )
            return (
                PolicyDecisionItem(
                    decision_type=DecisionType.DISEASE_TREATMENT,
                    result=DecisionResult.BLOCKED,
                    reason_code="OUT_OF_DOMAIN_CONFIDENCE",
                    signals=["disease.confidence_percent", "disease.pathogen_name"],
                    policy="icar_clinical_confidence_gate_v1",
                    action="Reject diagnosis; request clearer high-resolution photograph of affected leaf",
                    explanation=f"Diagnostic confidence ({conf_pct:.2f}%) is below the minimum 30.0% validity threshold. Prescription blocked to prevent misapplication.",
                    constraints_added=constraints
                ),
                trace,
                2
            )

        elif conf_pct < 65.0:
            constraints.extend(["PRESCRIPTION_LOCKED", "FIELD_AGENT_ESCALATION_REQUIRED"])
            trace.append(
                DecisionTraceItem(
                    signal="disease.confidence_percent",
                    value=conf_pct,
                    unit="%",
                    source=source,
                    provenance=prov,
                    policy="icar_clinical_confidence_gate_v1",
                    condition="30.0 <= confidence < 65.0%",
                    effect="prescription_locked_expert_review_required"
                )
            )
            return (
                PolicyDecisionItem(
                    decision_type=DecisionType.DISEASE_TREATMENT,
                    result=DecisionResult.REQUIRES_HUMAN_REVIEW,
                    reason_code="BORDERLINE_CONFIDENCE_GATE",
                    signals=["disease.confidence_percent", "disease.pathogen_name"],
                    policy="icar_clinical_confidence_gate_v1",
                    action=f"Lock chemical prescription for {pathogen}; route to certified agricultural field agent for on-site visual confirmation",
                    explanation=f"Diagnostic confidence ({conf_pct:.2f}%) is borderline [30.0%, 65.0%). Chemical dosage recommendations remain locked until human agronomist verification.",
                    constraints_added=constraints
                ),
                trace,
                2
            )

        else:
            trace.append(
                DecisionTraceItem(
                    signal="disease.confidence_percent",
                    value=conf_pct,
                    unit="%",
                    source=source,
                    provenance=prov,
                    policy="icar_clinical_confidence_gate_v1",
                    condition="confidence >= 65.0%",
                    effect="treatment_action_authorized"
                )
            )
            return (
                PolicyDecisionItem(
                    decision_type=DecisionType.DISEASE_TREATMENT,
                    result=DecisionResult.ALLOWED,
                    reason_code="CONFIDENT_DIAGNOSIS_ACTIONABLE",
                    signals=["disease.confidence_percent", "disease.pathogen_name"],
                    policy="icar_clinical_confidence_gate_v1",
                    action=f"Prepare ICAR standard management protocol for {pathogen}",
                    explanation=f"High diagnostic confidence ({conf_pct:.2f}%) confirms {pathogen}. Clinical treatment is authorized subject to environmental safety checks.",
                    constraints_added=constraints
                ),
                trace,
                2
            )

    @staticmethod
    def _evaluate_weather_policy(
        context: FarmDecisionContext
    ) -> Tuple[PolicyDecisionItem, List[DecisionTraceItem], int]:
        trace: List[DecisionTraceItem] = []
        constraints: List[str] = []

        # Trust check for weather signals
        weather_signals = [
            context.weather.rain_probability_percent,
            context.weather.wind_speed_kmh,
            context.weather.humidity_percent,
            context.weather.precipitation_mm,
        ]
        untrusted = [s for s in weather_signals if not is_signal_trustworthy(s)]
        if untrusted:
            # Record each untrusted signal in trace
            for sig in untrusted:
                trace.append(
                    DecisionTraceItem(
                        signal=f"weather.{sig.source}",
                        value=sig.value,
                        unit=sig.unit,
                        source=sig.source,
                        provenance=sig.provenance.value if hasattr(sig.provenance, 'value') else str(sig.provenance),
                        policy="signal_quality_check",
                        condition="signal untrusted",
                        effect="weather_evaluation_deferred"
                    )
                )
            constraints.append("UNTRUSTED_WEATHER")
            return (
                PolicyDecisionItem(
                    decision_type=DecisionType.WEATHER_TIMING,
                    result=DecisionResult.DEFERRED,
                    reason_code="UNTRUSTED_WEATHER",
                    signals=["weather.rain_probability_percent", "weather.wind_speed_kmh", "weather.humidity_percent", "weather.precipitation_mm"],
                    policy="signal_quality_check",
                    action="Defer weather-dependent actions until signals are trustworthy",
                    explanation="One or more weather signals failed trust validation (invalid quality or stale timestamp).",
                    constraints_added=constraints
                ),
                trace,
                len(weather_signals)
            )
        # Existing evaluation continues below
        """
        Evaluates Open-Meteo weather constraints against agricultural execution rules:
          - Rain probability >= 60% OR precip >= 5.0mm -> DEFER (wash-off risk)
          - Wind speed > 20.0 km/h -> DEFER (spray drift hazard)
          - Humidity > 90% -> Monitor fungal microclimate
        """
        trace: List[DecisionTraceItem] = []
        constraints: List[str] = []

        rain_prob = context.weather.rain_probability_percent.value
        precip_mm = context.weather.precipitation_mm.value
        wind_spd = context.weather.wind_speed_kmh.value
        humidity = context.weather.humidity_percent.value
        fav_win = context.weather.favorable_window.value or "next available dry window"

        source = context.weather.rain_probability_percent.source or "Open-Meteo REST API"
        prov = str(context.weather.rain_probability_percent.provenance)

        # Default safe fallbacks if signal values missing
        r_prob_safe = rain_prob if rain_prob is not None else 0
        p_mm_safe = precip_mm if precip_mm is not None else 0.0
        w_spd_safe = wind_spd if wind_spd is not None else 0.0

        trace.append(
            DecisionTraceItem(
                signal="weather.rain_probability_percent",
                value=r_prob_safe,
                unit="%",
                source=source,
                provenance=prov,
                policy="open_meteo_spray_weather_safety_rule",
                condition=f"rain_prob = {r_prob_safe}%",
                effect="rain_probability_checked"
            )
        )
        trace.append(
            DecisionTraceItem(
                signal="weather.wind_speed_kmh",
                value=w_spd_safe,
                unit="km/h",
                source=source,
                provenance=prov,
                policy="open_meteo_spray_weather_safety_rule",
                condition=f"wind_speed = {w_spd_safe} km/h",
                effect="wind_drift_checked"
            )
        )

        # Evaluation
        if r_prob_safe >= 60 or p_mm_safe >= 5.0:
            constraints.append("WEATHER_RAIN_BLOCK")
            if w_spd_safe > 20.0:
                constraints.append("WEATHER_WIND_DRIFT_BLOCK")
            trace.append(
                DecisionTraceItem(
                    signal="weather.precipitation_mm",
                    value=p_mm_safe,
                    unit="mm",
                    source=source,
                    provenance=prov,
                    policy="open_meteo_spray_weather_safety_rule",
                    condition="rain_prob >= 60% OR rainfall >= 5.0mm",
                    effect="spray_and_irrigation_deferred"
                )
            )
            return (
                PolicyDecisionItem(
                    decision_type=DecisionType.WEATHER_TIMING,
                    result=DecisionResult.DEFERRED,
                    reason_code="RAIN_RISK_EXECUTION_BLOCKED",
                    signals=["weather.rain_probability_percent", "weather.precipitation_mm"],
                    policy="open_meteo_spray_weather_safety_rule",
                    action=f"Postpone outdoor spraying and fertilizer top-dressing until {fav_win}",
                    explanation=f"High rain probability ({r_prob_safe}%) or expected rainfall ({p_mm_safe:.1f} mm) threatens to wash off treatments. Execution deferred to protect farmer investment.",
                    constraints_added=constraints
                ),
                trace,
                3
            )

        elif w_spd_safe > 20.0:
            constraints.append("WEATHER_WIND_DRIFT_BLOCK")
            trace.append(
                DecisionTraceItem(
                    signal="weather.wind_speed_kmh",
                    value=w_spd_safe,
                    unit="km/h",
                    source=source,
                    provenance=prov,
                    policy="open_meteo_spray_weather_safety_rule",
                    condition="wind_speed > 20.0 km/h",
                    effect="spray_task_deferred_drift_hazard"
                )
            )
            return (
                PolicyDecisionItem(
                    decision_type=DecisionType.WEATHER_TIMING,
                    result=DecisionResult.DEFERRED,
                    reason_code="HIGH_WIND_SPRAY_DRIFT_BLOCK",
                    signals=["weather.wind_speed_kmh"],
                    policy="open_meteo_spray_weather_safety_rule",
                    action=f"Postpone spraying until wind calms below 20.0 km/h (current: {w_spd_safe:.1f} km/h)",
                    explanation=f"Excessive wind speed ({w_spd_safe:.1f} km/h) creates off-target spray drift hazards. Postpone application to morning or evening calm hours.",
                    constraints_added=constraints
                ),
                trace,
                2
            )

        else:
            return (
                PolicyDecisionItem(
                    decision_type=DecisionType.WEATHER_TIMING,
                    result=DecisionResult.ALLOWED,
                    reason_code="WEATHER_CONDITIONS_FAVORABLE",
                    signals=["weather.rain_probability_percent", "weather.wind_speed_kmh"],
                    policy="open_meteo_spray_weather_safety_rule",
                    action=f"Weather conditions are clear and favorable for field activities ({fav_win})",
                    explanation=f"Low rain risk ({r_prob_safe}%) and calm winds ({w_spd_safe:.1f} km/h) provide a safe window for field management.",
                    constraints_added=[]
                ),
                trace,
                2
            )

    @staticmethod
    def _evaluate_telemetry_policy(
        context: FarmDecisionContext,
        active_constraints: List[str]
    ) -> Tuple[PolicyDecisionItem, List[DecisionTraceItem], int]:
        """
        Evaluates soil moisture telemetry.
        CRITICAL: Preserves provenance as SIMULATED (virtual prototype IoT node).
        Thresholds:
          - VWC < 40.0%: Low moisture -> Irrigate (unless impending rain defert)
          - 40.0% <= VWC < 65.0%: Optimal moisture -> No irrigation needed
          - VWC >= 65.0%: Elevated moisture -> Block irrigation (asphyxiation / rot risk)
        """
        trace: List[DecisionTraceItem] = []
        constraints: List[str] = []

        vwc = context.telemetry.soil_moisture_vwc.value
        source = context.telemetry.soil_moisture_vwc.source or "Virtual IoT Node #SIM-NODE-01"
        p_raw = context.telemetry.soil_moisture_vwc.provenance
        prov = getattr(p_raw, "value", getattr(p_raw, "name", str(p_raw or SignalProvenance.SIMULATED.value)))

        if vwc is None:
            trace.append(
                DecisionTraceItem(
                    signal="telemetry.soil_moisture_vwc",
                    value="None",
                    unit="% VWC",
                    source=source,
                    provenance=prov,
                    policy="virtual_telemetry_vwc_irrigation_rule",
                    condition="soil_moisture_vwc is None",
                    effect="telemetry_unavailable_fallback_to_profile"
                )
            )
            return (
                PolicyDecisionItem(
                    decision_type=DecisionType.IRRIGATION,
                    result=DecisionResult.INSUFFICIENT_DATA,
                    reason_code="TELEMETRY_UNAVAILABLE",
                    signals=["telemetry.soil_moisture_vwc"],
                    policy="virtual_telemetry_vwc_irrigation_rule",
                    action="Telemetry sensor data unavailable; maintain standard calendar irrigation schedule",
                    explanation="No soil volumetric water content reading available. Dynamic water optimization deferred.",
                    constraints_added=[]
                ),
                trace,
                1
            )

        # Trust check for telemetry soil moisture signal
        if not is_signal_trustworthy(context.telemetry.soil_moisture_vwc):
            prov_str = context.telemetry.soil_moisture_vwc.provenance.value if hasattr(context.telemetry.soil_moisture_vwc.provenance, 'value') else str(context.telemetry.soil_moisture_vwc.provenance)
            trace.append(
                DecisionTraceItem(
                    signal="telemetry.soil_moisture_vwc",
                    value=context.telemetry.soil_moisture_vwc.value,
                    unit=context.telemetry.soil_moisture_vwc.unit,
                    source=context.telemetry.soil_moisture_vwc.source,
                    provenance=prov_str,
                    policy="signal_quality_check",
                    condition="signal untrusted",
                    effect="telemetry_evaluation_deferred"
                )
            )
            constraints.append("UNTRUSTED_TELEMETRY")
            return (
                PolicyDecisionItem(
                    decision_type=DecisionType.IRRIGATION,
                    result=DecisionResult.DEFERRED,
                    reason_code="UNTRUSTED_TELEMETRY",
                    signals=["telemetry.soil_moisture_vwc"],
                    policy="signal_quality_check",
                    action="Defer irrigation decision until telemetry signal is trustworthy",
                    explanation="Soil moisture telemetry failed trust validation (quality not VALID or stale timestamp).",
                    constraints_added=constraints
                ),
                trace,
                1
            )

        trace.append(
            DecisionTraceItem(
                signal="telemetry.soil_moisture_vwc",
                value=vwc,
                unit="% VWC",
                source=source,
                provenance=prov,
                policy="virtual_telemetry_vwc_irrigation_rule",
                condition=f"vwc = {vwc:.1f}%",
                effect="root_zone_hydration_evaluated"
            )
        )

        # Conflict check: Low soil moisture BUT impending heavy rain
        if vwc < 40.0:
            if "WEATHER_RAIN_BLOCK" in active_constraints:
                trace.append(
                    DecisionTraceItem(
                        signal="telemetry.soil_moisture_vwc",
                        value=vwc,
                        unit="% VWC",
                        source=source,
                        provenance=prov,
                        policy="virtual_telemetry_vwc_irrigation_rule",
                        condition="vwc < 40.0% AND WEATHER_RAIN_BLOCK active",
                        effect="irrigation_deferred_for_natural_rainfall"
                    )
                )
                return (
                    PolicyDecisionItem(
                        decision_type=DecisionType.IRRIGATION,
                        result=DecisionResult.DEFERRED,
                        reason_code="DEFER_IRRIGATION_FOR_INCOMING_RAIN",
                        signals=["telemetry.soil_moisture_vwc", "weather.rain_probability_percent"],
                        policy="virtual_telemetry_vwc_irrigation_rule",
                        action=f"Defer irrigation despite low moisture ({vwc:.1f}% VWC); anticipated rainfall will recharge root zone naturally",
                        explanation=f"Soil moisture is low ({vwc:.1f}% VWC), but impending precipitation makes immediate artificial irrigation redundant and wasteful.",
                        constraints_added=[]
                    ),
                    trace,
                    2
                )
            else:
                trace.append(
                    DecisionTraceItem(
                        signal="telemetry.soil_moisture_vwc",
                        value=vwc,
                        unit="% VWC",
                        source=source,
                        provenance=prov,
                        policy="virtual_telemetry_vwc_irrigation_rule",
                        condition="vwc < 40.0% AND clear weather",
                        effect="irrigation_scheduled"
                    )
                )
                return (
                    PolicyDecisionItem(
                        decision_type=DecisionType.IRRIGATION,
                        result=DecisionResult.ALLOWED,
                        reason_code="LOW_SOIL_MOISTURE_IRRIGATION_NEEDED",
                        signals=["telemetry.soil_moisture_vwc"],
                        policy="virtual_telemetry_vwc_irrigation_rule",
                        action=f"Schedule field irrigation: root zone moisture is depleted ({vwc:.1f}% VWC < 40% threshold)",
                        explanation=f"Simulated soil moisture ({vwc:.1f}% VWC) indicates moisture deficit in root zone. Prompt irrigation recommended.",
                        constraints_added=[]
                    ),
                    trace,
                    1
                )

        elif vwc >= 65.0:
            constraints.append("IRRIGATION_BLOCKED_HIGH_MOISTURE")
            trace.append(
                DecisionTraceItem(
                    signal="telemetry.soil_moisture_vwc",
                    value=vwc,
                    unit="% VWC",
                    source=source,
                    provenance=prov,
                    policy="virtual_telemetry_vwc_irrigation_rule",
                    condition="vwc >= 65.0%",
                    effect="irrigation_blocked_field_saturated"
                )
            )
            return (
                PolicyDecisionItem(
                    decision_type=DecisionType.IRRIGATION,
                    result=DecisionResult.BLOCKED,
                    reason_code="ELEVATED_SOIL_MOISTURE_IRRIGATION_BLOCKED",
                    signals=["telemetry.soil_moisture_vwc"],
                    policy="virtual_telemetry_vwc_irrigation_rule",
                    action=f"Do not irrigate: root zone moisture is elevated ({vwc:.1f}% VWC)",
                    explanation=f"Root zone volumetric moisture is elevated ({vwc:.1f}% VWC). Over-watering risks root hypoxia and fungal proliferation.",
                    constraints_added=constraints
                ),
                trace,
                1
            )

        else:
            return (
                PolicyDecisionItem(
                    decision_type=DecisionType.IRRIGATION,
                    result=DecisionResult.ALLOWED,
                    reason_code="OPTIMAL_SOIL_MOISTURE_NO_IRRIGATION",
                    signals=["telemetry.soil_moisture_vwc"],
                    policy="virtual_telemetry_vwc_irrigation_rule",
                    action=f"Root zone soil moisture is optimal ({vwc:.1f}% VWC); additional irrigation not required",
                    explanation=f"Soil moisture ({vwc:.1f}% VWC) is within the optimal agronomic bracket (40% - 65% VWC).",
                    constraints_added=[]
                ),
                trace,
                1
            )

    @staticmethod
    def _evaluate_nutrient_policy(
        context: FarmDecisionContext
    ) -> Tuple[PolicyDecisionItem, List[DecisionTraceItem], int]:
        """
        Evaluates soil NPK nutrient data.
        STRICT REQUIREMENT: If NPK is unavailable, returns INSUFFICIENT_DATA.
        Does NOT fabricate a fertilizer prescription from missing laboratory data.
        """
        trace: List[DecisionTraceItem] = []
        constraints: List[str] = []

        n_val = context.soil.nitrogen_kg_ha.value
        p_val = context.soil.phosphorus_kg_ha.value
        k_val = context.soil.potassium_kg_ha.value
        source = context.soil.nitrogen_kg_ha.source or "none"
        prov = str(context.soil.nitrogen_kg_ha.provenance or SignalProvenance.UNAVAILABLE)

        if n_val is None:
            trace.append(
                DecisionTraceItem(
                    signal="soil.nitrogen_kg_ha",
                    value="None",
                    unit="kg/ha",
                    source=source,
                    provenance=prov,
                    policy="soil_health_card_npk_rule",
                    condition="nitrogen_kg_ha is None",
                    effect="nutrient_prescription_deferred_insufficient_data"
                )
            )
            return (
                PolicyDecisionItem(
                    decision_type=DecisionType.NUTRIENT_MANAGEMENT,
                    result=DecisionResult.INSUFFICIENT_DATA,
                    reason_code="MISSING_NPK_DATA",
                    signals=["soil.nitrogen_kg_ha", "soil.phosphorus_kg_ha", "soil.potassium_kg_ha"],
                    policy="soil_health_card_npk_rule",
                    action="Soil laboratory NPK data unavailable. Maintain standard cereal baseline nutrition; avoid uncalibrated chemical top-dressing",
                    explanation="Without measured soil laboratory NPK figures, dynamic nutrient optimization cannot be confidently performed. No fabricated dosage generated.",
                    constraints_added=[]
                ),
                trace,
                3
            )

        # Trust check for nutrient nitrogen signal when present
        if not is_signal_trustworthy(context.soil.nitrogen_kg_ha):
            prov_str = context.soil.nitrogen_kg_ha.provenance.value if hasattr(context.soil.nitrogen_kg_ha.provenance, 'value') else str(context.soil.nitrogen_kg_ha.provenance)
            trace.append(
                DecisionTraceItem(
                    signal="soil.nitrogen_kg_ha",
                    value=context.soil.nitrogen_kg_ha.value,
                    unit="kg/ha",
                    source=context.soil.nitrogen_kg_ha.source or "none",
                    provenance=prov_str,
                    policy="signal_quality_check",
                    condition="signal untrusted",
                    effect="nutrient_evaluation_deferred"
                )
            )
            constraints.append("UNTRUSTED_NUTRIENT_DATA")
            return (
                PolicyDecisionItem(
                    decision_type=DecisionType.NUTRIENT_MANAGEMENT,
                    result=DecisionResult.DEFERRED,
                    reason_code="UNTRUSTED_NUTRIENT_DATA",
                    signals=["soil.nitrogen_kg_ha"],
                    policy="signal_quality_check",
                    action="Defer nutrient management decision until nitrogen signal is trustworthy",
                    explanation="Soil nitrogen data failed trust validation (quality not VALID or stale timestamp).",
                    constraints_added=constraints
                ),
                trace,
                1
            )

        trace.append(
            DecisionTraceItem(
                signal="soil.nitrogen_kg_ha",
                value=n_val,
                unit="kg/ha",
                source=source,
                provenance=prov,
                policy="soil_health_card_npk_rule",
                condition=f"nitrogen = {n_val:.1f} kg/ha",
                effect="soil_nitrogen_fertility_evaluated"
            )
        )

        if n_val > 120.0:
            constraints.append("EXCESSIVE_NITROGEN_ALERT")
            trace.append(
                DecisionTraceItem(
                    signal="soil.nitrogen_kg_ha",
                    value=n_val,
                    unit="kg/ha",
                    source=source,
                    provenance=prov,
                    policy="soil_health_card_npk_rule",
                    condition="nitrogen > 120.0 kg/ha",
                    effect="excessive_nitrogen_rust_risk_flagged"
                )
            )
            return (
                PolicyDecisionItem(
                    decision_type=DecisionType.NUTRIENT_MANAGEMENT,
                    result=DecisionResult.REQUIRES_HUMAN_REVIEW,
                    reason_code="EXCESSIVE_NITROGEN_RUST_RISK",
                    signals=["soil.nitrogen_kg_ha"],
                    policy="soil_health_card_npk_rule",
                    action=f"Excessive soil nitrogen detected ({n_val:.1f} kg/ha > 120 kg/ha ceiling). Withhold nitrogen top-dressing to prevent succulent leaf growth and rust outbreak",
                    explanation=f"High soil nitrogen levels ({n_val:.1f} kg/ha) accelerate vegetative succulence, drastically increasing foliar disease and fungal rust vulnerability.",
                    constraints_added=constraints
                ),
                trace,
                3
            )
        elif n_val < 50.0:
            return (
                PolicyDecisionItem(
                    decision_type=DecisionType.NUTRIENT_MANAGEMENT,
                    result=DecisionResult.ALLOWED,
                    reason_code="NITROGEN_DEFICIT_DETECTED",
                    signals=["soil.nitrogen_kg_ha"],
                    policy="soil_health_card_npk_rule",
                    action=f"Nitrogen deficit ({n_val:.1f} kg/ha). Apply split-dose Urea/NPK per package of practices.",
                    explanation=f"Measured soil nitrogen ({n_val:.1f} kg/ha) is below optimal threshold (50.0 kg/ha). Targeted nutrition recommended.",
                    constraints_added=[]
                ),
                trace,
                3
            )
        else:
            return (
                PolicyDecisionItem(
                    decision_type=DecisionType.NUTRIENT_MANAGEMENT,
                    result=DecisionResult.ALLOWED,
                    reason_code="BALANCED_NITROGEN_LEVELS",
                    signals=["soil.nitrogen_kg_ha"],
                    policy="soil_health_card_npk_rule",
                    action=f"Soil nitrogen ({n_val:.1f} kg/ha) is within normal agronomic parameters for {context.crop.crop_name.value or 'crop'}",
                    explanation=f"Measured soil nitrogen ({n_val:.1f} kg/ha) conforms to recommended baselines.",
                    constraints_added=[]
                ),
                trace,
                3
            )

    @staticmethod
    def _evaluate_market_policy(
        context: FarmDecisionContext
    ) -> Tuple[PolicyDecisionItem, List[DecisionTraceItem], int]:
        """
        Evaluates market and commercial signals.
        STRICT REQUIREMENT: Never claims benchmark pricing is live exchange rates.
        Preserves provenance as DECLARED or CACHED.
        """
        trace: List[DecisionTraceItem] = []
        constraints: List[str] = []

        ref_price = context.market.reference_price_per_kg.value
        # Trust check for market reference price signal when present
        if ref_price is not None and not is_signal_trustworthy(context.market.reference_price_per_kg):
            prov_str = context.market.reference_price_per_kg.provenance.value if hasattr(context.market.reference_price_per_kg.provenance, 'value') else str(context.market.reference_price_per_kg.provenance)
            trace.append(
                DecisionTraceItem(
                    signal="market.reference_price_per_kg",
                    value=ref_price,
                    unit="INR/kg",
                    source=context.market.reference_price_per_kg.source or "AgriBridge Mandi Price Registry",
                    provenance=prov_str,
                    policy="signal_quality_check",
                    condition="signal untrusted",
                    effect="market_evaluation_deferred"
                )
            )
            constraints.append("UNTRUSTED_MARKET_DATA")
            return (
                PolicyDecisionItem(
                    decision_type=DecisionType.MARKET_DISPATCH,
                    result=DecisionResult.DEFERRED,
                    reason_code="UNTRUSTED_MARKET_DATA",
                    signals=["market.reference_price_per_kg"],
                    policy="signal_quality_check",
                    action="Defer market dispatch decision until price signal is trustworthy",
                    explanation="Market reference price signal failed trust validation (quality not VALID or stale timestamp).",
                    constraints_added=constraints
                ),
                trace,
                1
            )
        ref_price = context.market.reference_price_per_kg.value or 0.0
        pricing_type = context.market.pricing_type.value or "BENCHMARK"
        active_listings = context.market.active_market_listings.value or 0
        crop_name = context.crop.crop_name.value or "Crop"
        source = context.market.reference_price_per_kg.source or "AgriBridge Mandi Price Registry"
        prov = getattr(context.market.reference_price_per_kg.provenance, "value", str(context.market.reference_price_per_kg.provenance or SignalProvenance.DECLARED.value))

        trace.append(
            DecisionTraceItem(
                signal="market.reference_price_per_kg",
                value=ref_price,
                unit="INR/kg",
                source=source,
                provenance=prov,
                policy="mandi_registry_timing_rule",
                condition=f"price = ₹{ref_price}/kg ({pricing_type})",
                effect="market_commercial_context_attached"
            )
        )

        if active_listings > 0:
            return (
                PolicyDecisionItem(
                    decision_type=DecisionType.MARKET_DISPATCH,
                    result=DecisionResult.ALLOWED,
                    reason_code="MARKET_LISTING_ACTIVE",
                    signals=["market.reference_price_per_kg", "market.active_market_listings"],
                    policy="mandi_registry_timing_rule",
                    action=f"Active marketplace liquidity: {active_listings} trading lot(s) listed for {crop_name}. Forward contract hedging favorable at ₹{ref_price}/kg benchmark.",
                    explanation=f"Wholesale buyer liquidity detected for {crop_name}. Farmers may pre-commit harvest lots to lock in benchmark returns.",
                    constraints_added=[]
                ),
                trace,
                2
            )
        else:
            return (
                PolicyDecisionItem(
                    decision_type=DecisionType.MARKET_DISPATCH,
                    result=DecisionResult.ALLOWED,
                    reason_code="BENCHMARK_PRICING_ADVISORY_ONLY",
                    signals=["market.reference_price_per_kg"],
                    policy="mandi_registry_timing_rule",
                    action=f"Mandi benchmark rate for {crop_name} is ₹{ref_price}/kg (declared reference price). Commercial dispatch timing advisory only.",
                    explanation=f"Reference price ₹{ref_price}/kg provides financial baseline for treatment viability. Commercial signals remain advisory and do not override agronomic safety.",
                    constraints_added=[]
                ),
                trace,
                1
            )

    @staticmethod
    def _resolve_risk_and_priority(
        context: FarmDecisionContext,
        decisions: List[PolicyDecisionItem],
        constraints: List[str],
        escalation_required: bool
    ) -> Tuple[str, str]:
        """
        Applies deterministic multi-signal precedence to establish overall risk and operational priority.
        Precedence:
          1. Human Review / Locked Clinical Prescription -> URGENT / HIGH
          2. Weather Rain / Wind Block -> ELEVATED
          3. Soil Moisture Deficit -> ELEVATED
          4. Default Routine Operations -> ROUTINE / MODERATE
        """
        # 1. Critical Escalation & Safety Gate
        if escalation_required or "PRESCRIPTION_LOCKED" in constraints:
            return ("high", "urgent")

        # 2. Disease Scan Active & High Confidence
        has_active_disease = (
            context.disease.has_diagnosis and
            (context.disease.confidence_percent.value or 0.0) >= 65.0
        )

        has_weather_block = (
            "WEATHER_RAIN_BLOCK" in constraints or
            "WEATHER_WIND_DRIFT_BLOCK" in constraints
        )

        if has_active_disease and has_weather_block:
            # Confident disease + bad weather = High agronomic pressure under execution block
            return ("critical", "urgent")

        if has_active_disease:
            return ("high", "urgent")

        if has_weather_block:
            return ("moderate", "elevated")

        # Check for soil moisture deficit
        for d in decisions:
            if d.reason_code == "LOW_SOIL_MOISTURE_IRRIGATION_NEEDED":
                return ("moderate", "elevated")
            if d.reason_code == "EXCESSIVE_NITROGEN_RUST_RISK":
                return ("moderate", "elevated")

        # Fallback to weather overall risk or moderate
        base_risk = (context.weather.overall_risk.value or "moderate").lower()
        if base_risk in ["high", "critical"]:
            return (base_risk, "elevated")

        return ("moderate", "routine")
