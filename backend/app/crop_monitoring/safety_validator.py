"""
AgriBridge Safety Validation & Disease Policy Engine
Enforces structured schema compliance and strict inspection-only disease safety guidelines.
"""

from typing import Any, Dict, List, Tuple

REQUIRED_SCHEMA_FIELDS = [
    "current_stage",
    "stage_status",
    "next_stage",
    "weather_summary",
    "weather_risk",
    "weather_decision",
    "recommended_action",
    "irrigation_guidance",
    "fertilizer_guidance",
    "crop_protection_guidance",
    "monitoring_guidance",
    "marketplace_guidance",
    "safety_information",
    "important_note",
    "sources"
]

PROHIBITED_DIAGNOSTIC_PHRASES = [
    "i diagnose",
    "diagnosed as",
    "i have confirmed that your crop has",
    "gemini confirmed disease",
    "model confirmed disease",
    "disease confirmed:",
    "definitely infected with"
]


import re

def enforce_disease_safety_policy(data: Dict[str, Any], chemical_locked: bool = False) -> Dict[str, Any]:
    """
    Ensures that disease handling is strictly inspection-only and adheres
    to non-diagnostic safety standards. If chemical recommendations are locked,
    guarantees no pesticide/chemical dosing is prescribed.
    """
    sanitized = dict(data)

    # Sanitize protection guidance to remove any prohibited confirmation claims
    prot = str(sanitized.get("crop_protection_guidance", ""))
    for phrase in PROHIBITED_DIAGNOSTIC_PHRASES:
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        prot = pattern.sub("Inspect for potential symptoms of", prot)

    if chemical_locked:
        prot = (
            "Chemical treatment guidance is locked because AI disease confidence is below the verification threshold. "
            "Field Agent verification is required before chemical treatment guidance can be provided. "
            "Inspect affected foliage manually and avoid overhead irrigation."
        )

    # Ensure inspection instruction is clearly stated
    if not chemical_locked and "inspection only" not in prot.lower() and "disease detection" not in prot.lower():
        prot += " Note: Disease handling is inspection-only. If leaf spots or discoloration appear, photograph the leaf and submit to AgriBridge AI Disease Scan."

    sanitized["crop_protection_guidance"] = prot

    # Ensure safety information has proper label & PPE guidance
    safe_info = str(sanitized.get("safety_information", ""))
    standard_safety = (
        "Disease handling is inspection-only. No disease diagnosis or model inference is performed by LLM. "
        "Always follow registered product labels, recommended dilution ratios, pre-harvest intervals (PHI), "
        "and wear protective gear during any chemical application."
    )
    if len(safe_info.strip()) < 10:
        sanitized["safety_information"] = standard_safety
    elif "label" not in safe_info.lower() and "inspection" not in safe_info.lower():
        sanitized["safety_information"] = f"{safe_info} {standard_safety}"

    return sanitized



def validate_gemini_response(data: Any) -> Tuple[bool, Dict[str, Any], List[str]]:
    """
    Validates a dictionary against schemas/gemini_response_schema.json.
    Fills safe defaults for any missing fields to prevent downstream application crashes.
    """
    if not isinstance(data, dict):
        return False, {}, ["Response is not a valid JSON object"]

    missing_fields = []
    validated: Dict[str, Any] = {}

    for field in REQUIRED_SCHEMA_FIELDS:
        val = data.get(field)
        if val is None and field != "next_stage":
            missing_fields.append(field)

        if field == "sources":
            validated[field] = val if isinstance(val, list) else [str(val)] if val else ["AgriBridge Knowledge Base"]
        elif field == "next_stage":
            validated[field] = str(val) if val is not None else None
        else:
            validated[field] = str(val) if val is not None else "Information unavailable in current context"

    # Enforce disease safety policy
    validated = enforce_disease_safety_policy(validated)

    is_valid = len(missing_fields) == 0
    return is_valid, validated, missing_fields
