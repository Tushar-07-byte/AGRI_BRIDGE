"""
AgriBridge Multi-Signal Decision Domain Model
Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents

Defines the output contract for the deterministic Multi-Signal Policy Evaluator.
Captures individual policy findings, operational constraints, blocked actions,
recommended actions, human escalation flags, and a fully explainable decision trace.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DecisionResult(str, Enum):
    """Operational state of a policy decision."""
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    DEFERRED = "deferred"
    REQUIRES_HUMAN_REVIEW = "requires_human_review"
    INSUFFICIENT_DATA = "insufficient_data"


class DecisionType(str, Enum):
    """Agricultural domain of the policy evaluation."""
    DISEASE_TREATMENT = "disease_treatment"
    WEATHER_TIMING = "weather_timing"
    IRRIGATION = "irrigation"
    NUTRIENT_MANAGEMENT = "nutrient_management"
    MARKET_DISPATCH = "market_dispatch"
    GENERAL_OPERATION = "general_operation"


class DecisionTraceItem(BaseModel):
    """
    Explainable machine-reasoning trace item for an individual evaluated signal.
    Guarantees deterministic, transparent auditability without opaque LLM hallucination.
    """
    signal: str = Field(..., description="Canonical signal name (e.g. disease.confidence_percent)")
    value: Any = Field(..., description="Observed measurement or state value")
    unit: str = Field("N/A", description="Measurement unit (e.g. %, mm, km/h, % VWC, kg/ha)")
    source: str = Field("unknown", description="Originating sensor, API, database, or model")
    provenance: str = Field("UNAVAILABLE", description="LIVE | SIMULATED | DECLARED | CACHED | DERIVED")
    policy: str = Field(..., description="Name of the authoritative project rule/policy applied")
    condition: str = Field(..., description="Logical condition evaluated (e.g. '30.0 <= confidence < 65.0')")
    effect: str = Field(..., description="Direct decision impact (e.g. 'prescription_locked', 'spray_task_deferred')")


class PolicyDecisionItem(BaseModel):
    """
    Structured finding produced by an individual domain policy evaluator.
    """
    decision_type: DecisionType = Field(..., description="Domain category of decision")
    result: DecisionResult = Field(..., description="allowed | blocked | deferred | requires_human_review | insufficient_data")
    reason_code: str = Field(..., description="Machine-readable decision constant (e.g. BORDERLINE_CONFIDENCE_GATE)")
    signals: List[str] = Field(default_factory=list, description="Canonical signal names that influenced this decision")
    policy: str = Field(..., description="Authoritative rule or protocol name")
    action: str = Field(..., description="Recommended operational action string")
    explanation: str = Field(..., description="Clear plain-language agronomic explanation")
    constraints_added: List[str] = Field(default_factory=list, description="Operational constraints imposed by this decision")

    class Config:
        use_enum_values = True


class MultiSignalDecision(BaseModel):
    """
    Canonical Multi-Signal Decision Contract for AgriBridge (SH-AGR-001).
    Produced by MultiSignalPolicyEngine and consumed by OrchestrationService.
    """
    decision_id: str = Field(..., description="Unique deterministic decision identifier")
    context_id: str = Field(..., description="Linked FarmDecisionContext identifier")
    overall_risk: str = Field("moderate", description="low | moderate | high | critical")
    priority: str = Field("routine", description="routine | elevated | urgent | emergency")
    
    # Policy findings
    decisions: List[PolicyDecisionItem] = Field(
        default_factory=list,
        description="Structured findings from each evaluated domain policy"
    )
    
    # Aggregated execution constraints
    constraints: List[str] = Field(
        default_factory=list,
        description="Active constraints (e.g. WEATHER_RAIN_BLOCK, PRESCRIPTION_LOCKED)"
    )
    blocked_actions: List[str] = Field(
        default_factory=list,
        description="Actions currently forbidden from execution due to safety or weather"
    )
    recommended_actions: List[str] = Field(
        default_factory=list,
        description="Approved, safe actions ready for autonomous or farmer execution"
    )
    
    # Human-in-the-loop Escalation
    escalation_required: bool = Field(False, description="True if on-site agronomist intervention is mandatory")
    escalation_reason: Optional[str] = Field(None, description="Detailed explanation of escalation trigger")
    
    # Traceability & Explainability
    signals_considered: int = Field(0, description="Total count of input signals inspected")
    decision_trace: List[DecisionTraceItem] = Field(
        default_factory=list,
        description="Deterministic trace mapping every signal to its evaluated rule and effect"
    )
    provenance_summary: Dict[str, Dict[str, str]] = Field(
        default_factory=dict,
        description="Index of input signal provenances and data qualities"
    )
    
    generated_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO-8601 UTC timestamp of decision synthesis"
    )

    class Config:
        use_enum_values = True
