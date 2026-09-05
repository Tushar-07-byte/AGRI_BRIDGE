"""
AgriBridge Marketplace Quality & Post-Harvest Cleaned Crop Service
Handles post-harvest home cleaning protocols, quality assessment,
independent achieved grade evaluation, and potential premium price calculations.
"""

from typing import Any, Dict, List, Optional
from datetime import date


# ==============================================================================
# 1. CROP-SPECIFIC POST-HARVEST CLEANING, DRYING & SORTING PROTOCOLS
# ==============================================================================

CROP_CLEANING_PROTOCOLS: Dict[str, Dict[str, Any]] = {
    "wheat": {
        "crop_name": "Wheat",
        "category": "Cereal / Grain",
        "base_mandi_price_per_quintal": 2275.0,  # MSP benchmark / mandi rate
        "cleaning_steps": [
            {
                "step": 1,
                "title": "Threshing & Coarse Sieving",
                "description": "Use a 2.5mm wire mesh sieve to remove straw, chaff, soil clods, and stones immediately after threshing."
            },
            {
                "step": 2,
                "title": "Sun Drying on Tarpaulin",
                "description": "Spread cleaned wheat grains on clean HDPE tarpaulins under direct sunlight for 2 to 3 days (6-8 hours daily). Avoid drying directly on bare soil to prevent silica contamination."
            },
            {
                "step": 3,
                "title": "Moisture Conditioning",
                "description": "Ensure moisture content drops below 12.0% for safe storage and Grade A premium eligibility (check via moisture meter or grain-crack test)."
            },
            {
                "step": 4,
                "title": "Winnowing & Fine Sorting",
                "description": "Perform mechanical or wind winnowing to blow away shriveled, insect-damaged, and broken grains (target < 0.5% foreign matter)."
            },
            {
                "step": 5,
                "title": "Bagging & Hermetic Storage",
                "description": "Pack in new, dry jute or multi-layer hermetic bags. Label with lot date and store in a ventilated, rodent-free area raised 15cm off the floor on pallets."
            }
        ],
        "quality_parameters": {
            "moisture_target_pct": 12.0,
            "foreign_matter_max_pct": 0.5,
            "damaged_grains_max_pct": 1.5,
            "shriveled_grains_max_pct": 2.0
        },
        "grade_criteria": {
            "Grade A": {
                "max_moisture": 12.0,
                "max_foreign_matter": 0.5,
                "max_defects": 1.5,
                "potential_premium_pct": 18.0,
                "description": "Superior Milling Quality — Low moisture, zero stone/chaff, bold uniform grains."
            },
            "Grade B": {
                "max_moisture": 13.5,
                "max_foreign_matter": 1.2,
                "max_defects": 3.0,
                "potential_premium_pct": 8.0,
                "description": "Standard Commercial Grade — Well-cleaned, suitable for regional flour mills."
            },
            "Grade C": {
                "max_moisture": 15.0,
                "max_foreign_matter": 2.5,
                "max_defects": 6.0,
                "potential_premium_pct": 0.0,
                "description": "Basic Mandi Grade — Standard un-graded lot, baseline market price without premium."
            }
        }
    },
    "rice": {
        "crop_name": "Rice (Paddy)",
        "category": "Cereal / Grain",
        "base_mandi_price_per_quintal": 2183.0,
        "cleaning_steps": [
            {
                "step": 1,
                "title": "Pre-Cleaning & Scalping",
                "description": "Pass harvested paddy through a rotary scalper or handheld wire screen to remove panicle stems, weed seeds, and mud balls."
            },
            {
                "step": 2,
                "title": "Shade & Low-Intensity Sun Drying",
                "description": "Dry paddy gradually to prevent grain fissuring and chalky kernels. Stir grains every 30 minutes during drying."
            },
            {
                "step": 3,
                "title": "Moisture Stabilization",
                "description": "Target 13.0% - 14.0% moisture content. Excess moisture causes fungal yellowing; under-drying (<12%) increases milling breakage."
            },
            {
                "step": 4,
                "title": "De-stoning & Immature Grain Sorting",
                "description": "Separate green/immature grains and hollow chaff using air-screen cleaner or gravity separator."
            },
            {
                "step": 5,
                "title": "Moisture-Proof Bagging",
                "description": "Bag in dry bags with inner lining to prevent re-absorption of atmospheric humidity."
            }
        ],
        "quality_parameters": {
            "moisture_target_pct": 13.5,
            "foreign_matter_max_pct": 0.7,
            "damaged_grains_max_pct": 1.0,
            "immature_grains_max_pct": 2.0
        },
        "grade_criteria": {
            "Grade A": {
                "max_moisture": 13.5,
                "max_foreign_matter": 0.5,
                "max_defects": 1.0,
                "potential_premium_pct": 20.0,
                "description": "Export & Modern Mill Quality — High head-rice recovery, low chalkiness."
            },
            "Grade B": {
                "max_moisture": 14.5,
                "max_foreign_matter": 1.5,
                "max_defects": 3.0,
                "potential_premium_pct": 7.0,
                "description": "Fair Average Quality (FAQ) — Suitable for domestic procurement and standard milling."
            },
            "Grade C": {
                "max_moisture": 16.0,
                "max_foreign_matter": 3.0,
                "max_defects": 6.0,
                "potential_premium_pct": 0.0,
                "description": "Raw Field Lot — Base mandi rate without quality premium."
            }
        }
    },
    "tomato": {
        "crop_name": "Tomato",
        "category": "Horticulture / Vegetable",
        "base_mandi_price_per_quintal": 1850.0,
        "cleaning_steps": [
            {
                "step": 1,
                "title": "Harvest-Hour Field Sorting",
                "description": "Harvest in early morning or late afternoon with calyx intact. Discard fruit with blossom end rot, sunscald, or borer holes."
            },
            {
                "step": 2,
                "title": "Dry Wipe / Cloth Cleaning",
                "description": "Wipe tomatoes gently with clean, dry cotton cloth to remove dust. Avoid cold water washing unless chlorine sanitized, to prevent stem-end decay."
            },
            {
                "step": 3,
                "title": "Ripeness & Color Grading",
                "description": "Segregate by maturity: Breaker / Turning Stage (for long-distance transit) vs Pink / Light Red Stage (for local wholesale market within 24 hours)."
            },
            {
                "step": 4,
                "title": "Size & Firmness Sorting",
                "description": "Sort into uniform size groups (Medium 55-65mm, Large 65-75mm). Separate soft or overripe tomatoes."
            },
            {
                "step": 5,
                "title": "Crate Packaging & Cushioning",
                "description": "Pack in ventilated plastic crates (20-25 kg max) lined with paper. Never use gunny sacks which crush lower layers."
            }
        ],
        "quality_parameters": {
            "foreign_matter_max_pct": 0.2,
            "damaged_fruit_max_pct": 2.0,
            "uniformity_pct": 95.0
        },
        "grade_criteria": {
            "Grade A": {
                "max_foreign_matter": 0.2,
                "max_defects": 2.0,
                "min_uniformity": 95.0,
                "potential_premium_pct": 25.0,
                "description": "Premium Retail / Supermarket Lot — Firm, uniform color, blemish-free, intact calyx."
            },
            "Grade B": {
                "max_foreign_matter": 1.0,
                "max_defects": 5.0,
                "min_uniformity": 85.0,
                "potential_premium_pct": 10.0,
                "description": "Standard Mandi Lot — Sound fruit with minor surface marks, good firmness."
            },
            "Grade C": {
                "max_foreign_matter": 3.0,
                "max_defects": 12.0,
                "min_uniformity": 70.0,
                "potential_premium_pct": 0.0,
                "description": "Processing / Local Lot — Mixed sizes, higher defect tolerance, base market rate."
            }
        }
    },
    "potato": {
        "crop_name": "Potato",
        "category": "Tuber / Vegetable",
        "base_mandi_price_per_quintal": 1400.0,
        "cleaning_steps": [
            {
                "step": 1,
                "title": "Field Curing & Skin Hardening",
                "description": "Cut haulms 10-12 days before harvesting. After digging, cure tubers in heaps under dry straw for 10-15 days at 15-20°C to thicken skin and heal surface cuts."
            },
            {
                "step": 2,
                "title": "Dry Brushing / De-soiling",
                "description": "Gently remove dry surface soil using soft brushes or cotton gloves. Do not wash with water before cold storage."
            },
            {
                "step": 3,
                "title": "Green Tuber & Sprout Removal",
                "description": "Strictly discard greenish tubers (solanine accumulation) and rotten/soft tubers."
            },
            {
                "step": 4,
                "title": "Size Caliber Sorting",
                "description": "Grade into Extra Large (>55mm for chips/french fries), Table Ware (45-55mm), and Seed Size (30-45mm)."
            },
            {
                "step": 5,
                "title": "Mesh Bag Packaging",
                "description": "Pack in ventilated Leno mesh bags (50kg) and store in dark, cool, dry sheds to prevent greening."
            }
        ],
        "quality_parameters": {
            "foreign_matter_max_pct": 0.5,
            "damaged_tubers_max_pct": 2.5,
            "green_tubers_max_pct": 0.0
        },
        "grade_criteria": {
            "Grade A": {
                "max_foreign_matter": 0.5,
                "max_defects": 2.0,
                "min_uniformity": 92.0,
                "potential_premium_pct": 20.0,
                "description": "Processing & Export Grade — Thick cured skin, zero greening, uniform shape (>50mm)."
            },
            "Grade B": {
                "max_foreign_matter": 1.5,
                "max_defects": 6.0,
                "min_uniformity": 80.0,
                "potential_premium_pct": 8.0,
                "description": "Standard Table Potato — Cleaned, sound tubers suitable for wholesale and retail mandis."
            },
            "Grade C": {
                "max_foreign_matter": 4.0,
                "max_defects": 12.0,
                "min_uniformity": 65.0,
                "potential_premium_pct": 0.0,
                "description": "Ungraded Field Lot — Mixed caliber, base mandi market rate."
            }
        }
    },
    "corn": {
        "crop_name": "Corn (Maize)",
        "category": "Cereal / Grain",
        "base_mandi_price_per_quintal": 2090.0,
        "cleaning_steps": [
            {
                "step": 1,
                "title": "Shelling & De-cobbing",
                "description": "Shell cobs only when grain moisture is below 16% to avoid cracked seeds and pericarp damage."
            },
            {
                "step": 2,
                "title": "Sun Drying to Safe Moisture",
                "description": "Dry shelled grain evenly on tarpaulins until moisture reaches 13.0% to prevent Aspergillus/Aflatoxin contamination."
            },
            {
                "step": 3,
                "title": "Rotary Sieving & Cob Chaff Removal",
                "description": "Pass through double screens to remove cob debris, husk particles, and broken tips."
            },
            {
                "step": 4,
                "title": "Aspirated Winnowing",
                "description": "Blow off insect-bored, discolored, and light grains."
            },
            {
                "step": 5,
                "title": "Air-tight Bagging",
                "description": "Bag in dry gunny or HDPE bags treated against storage weevils."
            }
        ],
        "quality_parameters": {
            "moisture_target_pct": 13.0,
            "foreign_matter_max_pct": 0.8,
            "damaged_grains_max_pct": 2.0
        },
        "grade_criteria": {
            "Grade A": {
                "max_moisture": 13.0,
                "max_foreign_matter": 0.5,
                "max_defects": 1.5,
                "potential_premium_pct": 16.0,
                "description": "Feed & Starch Industrial Grade — Yellow bold grain, <13% moisture, low aflatoxin risk."
            },
            "Grade B": {
                "max_moisture": 14.5,
                "max_foreign_matter": 1.5,
                "max_defects": 4.0,
                "potential_premium_pct": 6.0,
                "description": "Commercial Feed Quality — Cleaned lot for domestic poultry and feed manufacturers."
            },
            "Grade C": {
                "max_moisture": 16.5,
                "max_foreign_matter": 3.5,
                "max_defects": 8.0,
                "potential_premium_pct": 0.0,
                "description": "Standard Raw Lot — Base market rate without quality premium."
            }
        }
    },
    "soybean": {
        "crop_name": "Soybean",
        "category": "Oilseed / Legume",
        "base_mandi_price_per_quintal": 4600.0,
        "cleaning_steps": [
            {
                "step": 1,
                "title": "Gentle Threshing & Pod Separation",
                "description": "Thresh at low cylinder speed (400-500 rpm) to avoid split cotyledons and seed coat rupture."
            },
            {
                "step": 2,
                "title": "Slow Sun Drying",
                "description": "Dry under mild morning sun. Avoid hot midday direct heat which splits the seed coat."
            },
            {
                "step": 3,
                "title": "Moisture Standardization",
                "description": "Bring moisture to 10.0% - 11.0% (maximum 12.0% for oil extraction contracts)."
            },
            {
                "step": 4,
                "title": "Sieving for Foreign Matter & Stones",
                "description": "Screen out pod shells, weed seeds, and soil particles (target < 1.0% foreign matter)."
            },
            {
                "step": 5,
                "title": "Cool Bagging in New Sacks",
                "description": "Allow grain to cool to ambient temperature before packing to prevent moisture condensation."
            }
        ],
        "quality_parameters": {
            "moisture_target_pct": 11.0,
            "foreign_matter_max_pct": 1.0,
            "damaged_grains_max_pct": 2.0
        },
        "grade_criteria": {
            "Grade A": {
                "max_moisture": 11.0,
                "max_foreign_matter": 0.8,
                "max_defects": 2.0,
                "potential_premium_pct": 15.0,
                "description": "Oil Extraction & Seed Quality — Low moisture, intact seed coat, yellow uniform seed."
            },
            "Grade B": {
                "max_moisture": 12.5,
                "max_foreign_matter": 2.0,
                "max_defects": 4.5,
                "potential_premium_pct": 6.0,
                "description": "Commercial Oil Mill Grade — Standard cleaned lot."
            },
            "Grade C": {
                "max_moisture": 14.0,
                "max_foreign_matter": 4.0,
                "max_defects": 8.0,
                "potential_premium_pct": 0.0,
                "description": "Raw Mandi Lot — Base market rate without premium."
            }
        }
    }
}


def get_crop_cleaning_protocol(crop_name: str) -> Dict[str, Any]:
    """Retrieves post-harvest cleaning, drying, and sorting guidelines for a crop."""
    norm = crop_name.strip().lower() if crop_name else "wheat"
    if norm in CROP_CLEANING_PROTOCOLS:
        return CROP_CLEANING_PROTOCOLS[norm]

    # Default fallback for unlisted crops
    return {
        "crop_name": crop_name.capitalize() if crop_name else "Crop",
        "category": "Agricultural Produce",
        "base_mandi_price_per_quintal": 2000.0,
        "cleaning_steps": [
            {
                "step": 1,
                "title": "De-trashing & Coarse Cleaning",
                "description": "Remove plant debris, leaves, and large soil stones immediately after harvest."
            },
            {
                "step": 2,
                "title": "Sun Drying on Tarpaulin",
                "description": "Spread produce on clean tarpaulins in sunlight until safe storage moisture is achieved."
            },
            {
                "step": 3,
                "title": "Sorting Defective Material",
                "description": "Manually sort out discolored, shriveled, bruised, or damaged material."
            },
            {
                "step": 4,
                "title": "Grading by Size and Uniformity",
                "description": "Group produce by uniform size, color, and maturity."
            },
            {
                "step": 5,
                "title": "Clean Aerated Packaging",
                "description": "Pack in clean, dry bags or crates labeled with lot details."
            }
        ],
        "quality_parameters": {
            "moisture_target_pct": 12.0,
            "foreign_matter_max_pct": 1.0,
            "damaged_grains_max_pct": 2.5
        },
        "grade_criteria": {
            "Grade A": {
                "max_moisture": 12.0,
                "max_foreign_matter": 0.8,
                "max_defects": 2.0,
                "potential_premium_pct": 15.0,
                "description": "Top Quality — Cleaned, dried, uniform lot with minimum foreign matter."
            },
            "Grade B": {
                "max_moisture": 14.0,
                "max_foreign_matter": 2.0,
                "max_defects": 5.0,
                "potential_premium_pct": 6.0,
                "description": "Commercial Grade — Fair Average Quality."
            },
            "Grade C": {
                "max_moisture": 16.0,
                "max_foreign_matter": 4.0,
                "max_defects": 10.0,
                "potential_premium_pct": 0.0,
                "description": "Standard Raw Lot — Base mandi rate."
            }
        }
    }


# ==============================================================================
# 2. QUALITY ASSESSMENT & INDEPENDENT ACHIEVED GRADE ENGINE
# ==============================================================================

def assess_crop_quality(
    crop_name: str,
    target_grade: Optional[str] = "Grade A",
    moisture_pct: Optional[float] = None,
    foreign_matter_pct: Optional[float] = None,
    defects_pct: Optional[float] = None,
    uniformity_pct: Optional[float] = None,
    custom_base_price: Optional[float] = None
) -> Dict[str, Any]:
    """
    Evaluates farmer's home quality measurements against scientific standards.
    
    STRICT RULES:
    1. Target Grade (farmer's wish) is kept separate from Achieved Grade.
    2. Achieved Grade is calculated strictly from measured values (Moisture, Foreign Matter, Defects).
    3. Never automatically grants Grade A or premium just because farmer selected Target Grade A.
    4. Premium price is presented as a potential configured estimate, NOT a guaranteed payout.
    """
    proto = get_crop_cleaning_protocol(crop_name)
    crop_display = proto["crop_name"]
    base_price = float(custom_base_price) if custom_base_price else float(proto.get("base_mandi_price_per_quintal", 2000.0))
    grades = proto["grade_criteria"]

    # Normalize inputs
    m_val = float(moisture_pct) if moisture_pct is not None else None
    fm_val = float(foreign_matter_pct) if foreign_matter_pct is not None else None
    def_val = float(defects_pct) if defects_pct is not None else None
    unif_val = float(uniformity_pct) if uniformity_pct is not None else None

    # Determine Achieved Grade strictly from physical measurements
    achieved_grade = "Grade C"
    reasons_for_grade = []
    reasons_for_downgrade = []

    # Check Grade A criteria
    grade_a_spec = grades.get("Grade A", {})
    grade_b_spec = grades.get("Grade B", {})

    meets_a = True

    if m_val is not None and "max_moisture" in grade_a_spec:
        if m_val > grade_a_spec["max_moisture"]:
            meets_a = False
            reasons_for_downgrade.append(f"Moisture content ({m_val:.1f}%) exceeds Grade A limit ({grade_a_spec['max_moisture']}%)")
        else:
            reasons_for_grade.append(f"Moisture ({m_val:.1f}%) satisfies Grade A standard (≤ {grade_a_spec['max_moisture']}%)")

    if fm_val is not None and "max_foreign_matter" in grade_a_spec:
        if fm_val > grade_a_spec["max_foreign_matter"]:
            meets_a = False
            reasons_for_downgrade.append(f"Foreign matter ({fm_val:.1f}%) exceeds Grade A limit ({grade_a_spec['max_foreign_matter']}%)")
        else:
            reasons_for_grade.append(f"Foreign matter ({fm_val:.1f}%) satisfies Grade A standard (≤ {grade_a_spec['max_foreign_matter']}%)")

    if def_val is not None and "max_defects" in grade_a_spec:
        if def_val > grade_a_spec["max_defects"]:
            meets_a = False
            reasons_for_downgrade.append(f"Defective/damaged content ({def_val:.1f}%) exceeds Grade A limit ({grade_a_spec['max_defects']}%)")
        else:
            reasons_for_grade.append(f"Defect rate ({def_val:.1f}%) satisfies Grade A standard (≤ {grade_a_spec['max_defects']}%)")

    if unif_val is not None and "min_uniformity" in grade_a_spec:
        if unif_val < grade_a_spec["min_uniformity"]:
            meets_a = False
            reasons_for_downgrade.append(f"Uniformity ({unif_val:.1f}%) is below Grade A limit (≥ {grade_a_spec['min_uniformity']}%)")

    if meets_a and (m_val is not None or fm_val is not None or def_val is not None):
        achieved_grade = "Grade A"
    else:
        # Check Grade B criteria
        meets_b = True
        if m_val is not None and "max_moisture" in grade_b_spec:
            if m_val > grade_b_spec["max_moisture"]:
                meets_b = False
                reasons_for_downgrade.append(f"Moisture ({m_val:.1f}%) exceeds Grade B limit ({grade_b_spec['max_moisture']}%)")
        if fm_val is not None and "max_foreign_matter" in grade_b_spec:
            if fm_val > grade_b_spec["max_foreign_matter"]:
                meets_b = False
                reasons_for_downgrade.append(f"Foreign matter ({fm_val:.1f}%) exceeds Grade B limit ({grade_b_spec['max_foreign_matter']}%)")
        if def_val is not None and "max_defects" in grade_b_spec:
            if def_val > grade_b_spec["max_defects"]:
                meets_b = False
                reasons_for_downgrade.append(f"Defect rate ({def_val:.1f}%) exceeds Grade B limit ({grade_b_spec['max_defects']}%)")

        if meets_b and (m_val is not None or fm_val is not None or def_val is not None):
            achieved_grade = "Grade B"
        else:
            achieved_grade = "Grade C"

    # Calculate potential premium for the achieved grade
    achieved_spec = grades.get(achieved_grade, {})
    premium_pct = achieved_spec.get("potential_premium_pct", 0.0)
    potential_premium_amount_per_quintal = round(base_price * (premium_pct / 100.0), 2)
    potential_total_price_per_quintal = round(base_price + potential_premium_amount_per_quintal, 2)

    # Comparison with farmer's target grade
    target_norm = (target_grade or "Grade A").strip()
    target_matched = (target_norm == achieved_grade)

    target_advice = ""
    if not target_matched:
        target_spec = grades.get(target_norm, {})
        target_prem = target_spec.get("potential_premium_pct", 0.0)
        target_advice = (
            f"You selected Target {target_norm} (potential +{target_prem}% premium), but current home measurements "
            f"qualify for {achieved_grade}. Further cleaning or drying can help achieve {target_norm}."
        )
    else:
        target_advice = f"Your cleaned crop meets your Target {target_norm} standard perfectly!"

    return {
        "success": True,
        "crop": crop_display,
        "base_market_price_per_quintal": base_price,
        "currency": "INR",
        "measurements_evaluated": {
            "moisture_percent": m_val,
            "foreign_matter_percent": fm_val,
            "defects_percent": def_val,
            "uniformity_percent": unif_val
        },
        "target_grade": target_norm,
        "achieved_grade": achieved_grade,
        "target_and_achieved_matched": target_matched,
        "target_grade_advice": target_advice,
        "potential_premium_percentage": premium_pct,
        "potential_premium_amount_per_quintal": potential_premium_amount_per_quintal,
        "potential_total_price_per_quintal": potential_total_price_per_quintal,
        "premium_status": "POTENTIAL_CONFIGURED_PREMIUM",
        "guarantee_disclaimer": (
            "Premium price is an estimated potential configured benchmark based on quality grades. "
            "It is NOT a guaranteed price; final realized price is determined during buyer trade."
        ),
        "achieved_grade_description": achieved_spec.get("description", ""),
        "evaluation_notes": {
            "positive_factors": reasons_for_grade,
            "areas_for_improvement": reasons_for_downgrade
        },
        "cleaning_protocol_summary": proto["cleaning_steps"],
        "recommended_next_action": (
            "Proceed to List Cleaned Crop on AgriBridge Post-Harvest Marketplace"
            if achieved_grade in ["Grade A", "Grade B"]
            else "Perform further winnowing/drying or list at standard mandi market rate"
        )
    }

