from datetime import datetime, timedelta
from pathlib import Path
import json
import re
import shutil
import uuid

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
    Depends
)
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.farmer import Farmer
from app.models.action_plan import ActionPlan, PlanTask, FieldAgentEscalation
from app.models.disease_record import DiseaseRecord
from app.services.ai_service import analyze_crop, get_timing_advice_for_prediction


router = APIRouter(
    prefix="/api/ai",
    tags=["AI"]
)


# ============================================================
# TEMP UPLOAD DIRECTORY
# ============================================================

UPLOAD_DIR = (
    Path(__file__).resolve().parents[2]
    / "ai_uploads"
)

UPLOAD_DIR.mkdir(
    exist_ok=True
)

# The permanent copy is served by FastAPI's project-level /uploads/ mount.
LISTING_UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads"
LISTING_UPLOAD_DIR.mkdir(exist_ok=True)

SUPPORTED_PLANTS = {
    "apple", "blueberry", "cherry", "corn", "grape", "orange", "peach",
    "pepper", "potato", "raspberry", "rice", "soybean", "squash",
    "strawberry", "tomato", "wheat"
}

FARM_OPTIONS = {
    "growth_stage": {"seedling", "vegetative", "flowering", "fruiting", "maturity"},
    "irrigation_method": {"drip", "sprinkler", "flood", "furrow", "rainfed"},
    "irrigation_status": {"dry", "normal", "wet", "waterlogged"},
    "recent_rainfall": {"none", "low", "moderate", "heavy"},
    "humidity": {"low", "moderate", "high"},
    "disease_severity": {"low", "moderate", "high"},
}

REQUIRED_FARM_FIELDS = {
    "farm_area", "growth_stage", "irrigation_method", "irrigation_status",
    "recent_rainfall", "humidity", "fertilizer_applied", "previous_crop",
    "disease_severity", "region"
}


def validate_farm_profile(farm_data: dict) -> dict:

    if not isinstance(farm_data, dict):
        raise HTTPException(status_code=400, detail="farm must be a JSON object")

    missing = [field for field in REQUIRED_FARM_FIELDS if farm_data.get(field) in (None, "")]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required farm fields: {', '.join(sorted(missing))}"
        )

    try:
        farm_area = float(farm_data["farm_area"])
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="farm_area must be a positive number")

    if farm_area <= 0:
        raise HTTPException(status_code=400, detail="farm_area must be a positive number")

    validated = {
        field: str(farm_data[field]).strip()
        for field in REQUIRED_FARM_FIELDS
        if field != "farm_area"
    }
    validated["farm_area"] = farm_area


    if "farmer_id" in farm_data and farm_data["farmer_id"] not in (None, ""):
        try:
            validated["farmer_id"] = int(farm_data["farmer_id"])
        except (ValueError, TypeError):
            pass

    for field in {"fertilizer_applied", "previous_crop", "region"}:
        if not validated[field]:
            raise HTTPException(status_code=400, detail=f"{field} is required")

    for field, options in FARM_OPTIONS.items():
        value = validated[field].lower()
        if value not in options:
            raise HTTPException(status_code=400, detail=f"Invalid {field}: {validated[field]}")
        validated[field] = value

    return validated


# ============================================================
# AI HEALTH
# ============================================================

@router.get("/health")
def ai_health():

    return {
        "success": True,
        "service": "AgriBridge AI",
        "status": "available"
    }


# ============================================================
# AI MODEL READINESS
# ============================================================

@router.get("/readiness")
def ai_readiness():
    """
    Returns real-time readiness status of the AI inference engine:
    READY, WARMING, or FAILED.
    """
    from app.services.ai_service import get_ai_readiness
    readiness_data = get_ai_readiness()
    return {
        "success": True,
        **readiness_data
    }


# ============================================================
# CROP DISEASE ANALYSIS
# ============================================================

@router.post("/predict")
async def predict_crop_disease(
    plant: str = Form(...),
    farm: str = Form("{}"),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    image_path = None
    permanent_image_path = None

    try:

        # ----------------------------------------------------
        # Validate image
        # ----------------------------------------------------

        if not image.filename:

            raise HTTPException(
                status_code=400,
                detail="Image file is required."
            )

        plant = plant.strip().lower()
        if plant not in SUPPORTED_PLANTS:
            raise HTTPException(status_code=400, detail=f"Unsupported plant: {plant}")

        # ----------------------------------------------------
        # Parse farm JSON
        # ----------------------------------------------------

        try:
            farm_data = json.loads(farm)

        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail="Invalid farm JSON."
            )

        farm_data = validate_farm_profile(farm_data)

        # ----------------------------------------------------
        # Save uploaded image
        # ----------------------------------------------------

        extension = Path(
            image.filename
        ).suffix.lower()

        allowed_extensions = {
            ".jpg",
            ".jpeg",
            ".png"
        }

        if extension not in allowed_extensions:

            raise HTTPException(
                status_code=400,
                detail="Only JPG, JPEG and PNG images are supported."
            )

        orig_stem = Path(image.filename).stem if image.filename else "crop_image"
        clean_stem = re.sub(r'[^a-zA-Z0-9_\-]', '_', orig_stem)
        filename = f"{clean_stem}_{uuid.uuid4().hex[:8]}{extension}"

        image_path = (
            UPLOAD_DIR
            / filename
        )

        with open(
            image_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                image.file,
                buffer
            )

        permanent_image_path = LISTING_UPLOAD_DIR / filename
        shutil.copy2(image_path, permanent_image_path)


        # ----------------------------------------------------
        # Run AI
        # ----------------------------------------------------

        result = analyze_crop(
            image_path,
            plant,
            farm_data
        )

        # ----------------------------------------------------
        # Weather-Aware Spray Timing Evaluation
        # ----------------------------------------------------
        timing_advice = await get_timing_advice_for_prediction(
            farm_info=farm_data,
            disease_data=result.get("disease", {})
        )
        result["timing_advice"] = timing_advice

        result["uploaded_image_path"] = f"uploads/{filename}"

        # ----------------------------------------------------
        # Automatically Generate Action Plan & Trackable Plan Task
        # ----------------------------------------------------
        try:
            # Determine farmer ID
            farmer_id = farm_data.get("farmer_id")
            if not farmer_id:
                farmer = db.query(Farmer).first()
                if not farmer:
                    farmer = Farmer(
                        name="AgriBridge Farmer"
                    )
                    db.add(farmer)
                    db.flush()
                farmer_id = farmer.id

            disease_obj = result.get("disease", {})
            pred_obj = result.get("prediction", {})
            disease_name = disease_obj.get("disease", disease_obj.get("name", "Crop Condition"))
            chem_opt = disease_obj.get("chemical_option", [])
            org_opt = disease_obj.get("organic_option", [])
            treatment_list = result.get("treatment", [])

            # Extract title
            if chem_opt and isinstance(chem_opt, list) and len(chem_opt) > 0:
                task_title = f"Apply {chem_opt[0][:80]}"
            elif org_opt and isinstance(org_opt, list) and len(org_opt) > 0:
                task_title = f"Apply {org_opt[0][:80]}"
            elif treatment_list and isinstance(treatment_list, list) and len(treatment_list) > 0:
                task_title = f"Apply {treatment_list[0][:80]}"
            else:
                task_title = f"Execute treatment plan for {disease_name}"

            # ----------------------------------------------------
            # Compute Deterministic Simulated Soil Moisture (Prototype Data)
            # ----------------------------------------------------
            irrig_method = str(farm_data.get("irrigation_method") or "drip").lower()
            irrig_status = str(farm_data.get("irrigation_status") or "normal").lower()
            recent_rain = str(farm_data.get("recent_rainfall") or "low").lower()

            base_moisture = 45
            if "flood" in irrig_method or "canal" in irrig_method or "furrow" in irrig_method:
                base_moisture = 70
            elif "sprinkler" in irrig_method:
                base_moisture = 55
            elif "drip" in irrig_method:
                base_moisture = 42
            elif "rainfed" in irrig_method:
                base_moisture = 38

            if "high" in recent_rain:
                base_moisture += 12
            elif "medium" in recent_rain or "moderate" in recent_rain:
                base_moisture += 5

            if "excess" in irrig_status or "high" in irrig_status:
                base_moisture += 8
            elif "deficit" in irrig_status or "dry" in irrig_status:
                base_moisture -= 10

            soil_moisture_val = max(18, min(88, base_moisture))
            moisture_label = "Elevated" if soil_moisture_val >= 65 else ("Optimal" if soil_moisture_val >= 40 else "Low")

            simulated_soil = {
                "value_percent": soil_moisture_val,
                "unit": "% VWC",
                "label": f"{soil_moisture_val}% VWC ({moisture_label})",
                "status": moisture_label,
                "is_prototype": True,
                "note": "Simulated Soil Moisture Reading (Prototype Data)"
            }
            result["simulated_soil_moisture"] = simulated_soil

            # Extract reasoning from timing advice, confidence & simulated soil moisture
            timing_text = timing_advice.get("advice", "") if isinstance(timing_advice, dict) else str(timing_advice)
            timing_window = timing_advice.get("recommended_window", "") if isinstance(timing_advice, dict) else ""
            rain_risk = timing_advice.get("rain_risk", False) if isinstance(timing_advice, dict) else False

            confidence_val = pred_obj.get("confidence", 0)
            reasoning_parts = []
            if confidence_val:
                reasoning_parts.append(f"Disease {disease_name} detected with {confidence_val}% confidence.")
            if timing_text:
                reasoning_parts.append(timing_text)
            if timing_window:
                reasoning_parts.append(f"Optimal Window: {timing_window}.")
            reasoning_parts.append(f"Combined with {moisture_label.lower()} simulated soil moisture ({soil_moisture_val}% VWC), treatment is recommended within 48 hours.")

            reasoning_text = " ".join(reasoning_parts) if reasoning_parts else f"Automated treatment task for {disease_name}."

            risk_type = "weather_delay" if rain_risk else "disease_treatment"
            is_borderline = (confidence_val >= 30.0 and confidence_val < 65.0)
            plan_status = "needs_expert_review" if is_borderline else "active"
            esc_reason = "Inspection uncertainty: Confidence in 30-65% range requires on-site expert review." if is_borderline else None

            # Create Action Plan
            action_plan = ActionPlan(
                farmer_id=int(farmer_id),
                listing_id=None,
                risk_type=risk_type,
                status=plan_status,
                escalation_required=True if is_borderline else False,
                escalation_reason=esc_reason,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(action_plan)
            db.flush()

            if is_borderline:
                escalation_entry = FieldAgentEscalation(
                    action_plan_id=action_plan.id,
                    farmer_id=int(farmer_id),
                    risk_level="high",
                    reason=esc_reason,
                    status="escalated",
                    created_at=datetime.utcnow()
                )
                db.add(escalation_entry)

            # Create Plan Task
            plan_task = PlanTask(
                action_plan_id=action_plan.id,
                title=task_title,
                scheduled_for=datetime.utcnow() + timedelta(days=1),
                status="pending",
                reasoning=reasoning_text,
                completed_at=None
            )
            db.add(plan_task)
            db.commit()
            db.refresh(action_plan)
            db.refresh(plan_task)

            result["action_plan"] = {
                "id": action_plan.id,
                "farmer_id": action_plan.farmer_id,
                "risk_type": action_plan.risk_type,
                "status": action_plan.status,
                "created_at": action_plan.created_at.isoformat(),
                "tasks": [
                    {
                        "id": plan_task.id,
                        "title": plan_task.title,
                        "status": plan_task.status,
                        "reasoning": plan_task.reasoning,
                        "scheduled_for": plan_task.scheduled_for.isoformat() if plan_task.scheduled_for else None
                    }
                ]
            }
        except Exception as plan_err:
            db.rollback()
            print(f"Warning: Failed to create automated action plan: {plan_err}")

        # ----------------------------------------------------
        # Persist Clinical Disease Record (Status: PENDING_AGENT_REVIEW)
        # Human-in-the-Loop verification queue (strictly decoupled from Marketplace)
        # ----------------------------------------------------
        try:
            disease_obj = result.get("disease", {})
            pred_obj = result.get("prediction", {})
            disease_name = disease_obj.get("disease", disease_obj.get("name", "Crop Condition"))
            chem_opt = disease_obj.get("chemical_option", [])
            org_opt = disease_obj.get("organic_option", [])
            confidence_val = pred_obj.get("confidence", 0)

            chem_val = chem_opt[0] if (chem_opt and isinstance(chem_opt, list)) else (str(chem_opt) if chem_opt else "Mancozeb 75% WP @ 2.0g/L")
            org_val = org_opt[0] if (org_opt and isinstance(org_opt, list)) else (str(org_opt) if org_opt else "Neem Oil 10,000 ppm @ 5ml/L")

            disease_record = DiseaseRecord(
                farmer_id=int(farmer_id) if 'farmer_id' in locals() and farmer_id else 1,
                crop_type=plant,
                image_url=f"uploads/{filename}",
                confidence=float(confidence_val) if confidence_val else None,
                predicted_pathogen=str(disease_name),
                scientific_name=str(disease_obj.get("scientific_name") or ""),
                severity=str(disease_obj.get("severity_level") or farm_data.get("disease_severity") or "moderate"),
                status="PENDING_AGENT_REVIEW",
                prescription_chemical=str(chem_val),
                prescription_dosage="2.0 g / L water (Standard ICAR Knapsack Dilution)",
                prescription_phi="7-10 Days Pre-Harvest Interval (PHI)",
                prescription_organic=str(org_val),
                farm_area=float(farm_data.get("farm_area", 2.5)),
                growth_stage=str(farm_data.get("growth_stage", "flowering")),
                geolocation=str(farm_data.get("region", "Raipur, Chhattisgarh")),
                action_plan_id=action_plan.id if 'action_plan' in locals() and action_plan else None,
                created_at=datetime.utcnow()
            )
            db.add(disease_record)
            db.commit()
            db.refresh(disease_record)

            result["disease_record"] = {
                "id": disease_record.id,
                "status": disease_record.status,
                "crop_type": disease_record.crop_type,
                "predicted_pathogen": disease_record.predicted_pathogen,
                "scientific_name": disease_record.scientific_name,
                "confidence": disease_record.confidence,
                "image_url": disease_record.image_url,
                "geolocation": disease_record.geolocation,
                "locked_prescription": True,
                "notice": "Diagnostic record is PENDING_AGENT_REVIEW. Chemical dosage and prescription are locked until verified by an Agri-Student / Field Agent."
            }
        except Exception as rec_err:
            db.rollback()
            print(f"Warning: Failed to create disease record: {rec_err}")

        # ----------------------------------------------------
        # Delete only the temporary analysis copy. The permanent image remains
        # under project /uploads/ so it can be displayed from FastAPI.

        try:
            image_path.unlink()
        except Exception:
            pass

        return {
            "success": True,
            "result": result
        }

    except HTTPException:
        raise

    except ValueError as ve:
        # Clean up temporary images
        try:
            if image_path and image_path.exists():
                image_path.unlink()
        except Exception:
            pass

        try:
            if permanent_image_path and permanent_image_path.exists():
                permanent_image_path.unlink()
        except Exception:
            pass

        raise HTTPException(
            status_code=400,
            detail=str(ve)
        )

    except Exception as e:

        # Clean up image if something fails
        try:
            if image_path and image_path.exists():
                image_path.unlink()
        except Exception:
            pass

        try:
            if permanent_image_path and permanent_image_path.exists():
                permanent_image_path.unlink()
        except Exception:
            pass

        raise HTTPException(
            status_code=500,
            detail=f"Unable to analyze the crop image: {str(e)}"
        )
