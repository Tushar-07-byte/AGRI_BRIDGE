"""
AgriBridge Marketplace Context Adapter (Two-Phase Architecture)
Strictly separates:
1. PRE-HARVEST MARKETPLACE: Market intelligence, mandi benchmark price, market trend,
   selling-time guidance, and pre-harvest crop listing ("CROP LISTING — VALID ONLY FOR PRE-HARVEST MARKETPLACE").
   NO cleaning/drying/sorting or premium pricing in pre-harvest.
2. POST-HARVEST — CLEANED CROP: Shown only after harvest. Farmer message:
   "If you want to earn more, clean, dry and properly sort your harvested crop at home.
   After quality assessment, you may become eligible for a potential premium price."
   Contains crop-specific cleaning, drying, sorting, quality assessment criteria (Grade A/B/C),
   and potential configured premium calculations.
"""

from typing import Any, Dict, Optional
from datetime import date, timedelta
from ..services.marketplace_quality_service import get_crop_cleaning_protocol, assess_crop_quality


# Mandi Reference Benchmark Rates (₹/quintal)
MANDI_BENCHMARK_RATES: Dict[str, Dict[str, Any]] = {
    "wheat": {"price_per_quintal": 2275.0, "trend": "Bullish", "change_pct": "+2.4%", "local_market": "Khanna / Varanasi Mandi"},
    "rice": {"price_per_quintal": 2183.0, "trend": "Stable", "change_pct": "+0.5%", "local_market": "Karnal / Burdwan Mandi"},
    "tomato": {"price_per_quintal": 1850.0, "trend": "Bullish", "change_pct": "+4.1%", "local_market": "Kolar / Nashik Mandi"},
    "potato": {"price_per_quintal": 1400.0, "trend": "Stable", "change_pct": "-0.8%", "local_market": "Agra / Hooghly Mandi"},
    "corn": {"price_per_quintal": 2090.0, "trend": "Bullish", "change_pct": "+1.8%", "local_market": "Davangere / Chhindwara Mandi"},
    "soybean": {"price_per_quintal": 4600.0, "trend": "Bullish", "change_pct": "+3.2%", "local_market": "Indore / Latur Mandi"},
    "cotton": {"price_per_quintal": 6620.0, "trend": "Stable", "change_pct": "+0.2%", "local_market": "Rajkot / Warangal Mandi"},
    "sugarcane": {"price_per_quintal": 315.0, "trend": "Stable", "change_pct": "0.0%", "local_market": "Kolhapur / Meerut Mill Gate"}
}


def get_marketplace_context(
    crop_id: str,
    db_session=None,
    days_to_harvest: Optional[int] = None,
    is_harvested: bool = False
) -> Dict[str, Any]:
    """
    Safely compiles two-phase marketplace context for a crop.
    
    1. PRE-HARVEST MARKETPLACE: Market intelligence, mandi rates, harvest countdown,
       and pre-harvest listing reminders. No cleaning or premium prices here.
    2. POST-HARVEST — CLEANED CROP: Post-harvest flow guiding home cleaning, drying,
       sorting, quality assessment, and potential premium eligibility.
    """
    crop_norm = crop_id.strip().lower() if crop_id else "wheat"
    crop_display = crop_norm.capitalize()

    # Active DB listings count
    active_listings_count = 0
    if db_session:
        try:
            from ..models.listing import Listing
            active_listings_count = db_session.query(Listing).filter(
                Listing.crop_type.ilike(f"%{crop_norm}%"),
                Listing.status == "active"
            ).count()
        except Exception:
            active_listings_count = 0

    # Market rate intelligence
    bench = MANDI_BENCHMARK_RATES.get(crop_norm, {
        "price_per_quintal": 2000.0,
        "trend": "Stable",
        "change_pct": "0.0%",
        "local_market": "Regional APMC Mandi"
    })

    # Expected harvest date calculation
    harvest_dt_str = None
    if days_to_harvest is not None:
        harvest_dt = date.today() + timedelta(days=max(0, days_to_harvest))
        harvest_dt_str = harvest_dt.isoformat()

    # -------------------------------------------------------------------------
    # 1. PRE-HARVEST MARKETPLACE STRUCTURE
    # -------------------------------------------------------------------------
    selling_guidance = (
        f"Mandi price for {crop_display} is currently {bench['trend']} at ₹{bench['price_per_quintal']}/quintal "
        f"({bench['change_pct']} in {bench['local_market']}). "
        + (f"Harvest is estimated in {days_to_harvest} days. " if days_to_harvest is not None else "")
        + "You can list your upcoming croplot in the Pre-Harvest Marketplace to connect with advance wholesale buyers."
    )

    pre_harvest_marketplace = {
        "section_name": "PRE-HARVEST MARKETPLACE",
        "description": "Market intelligence and selling preparation while the crop is actively growing.",
        "mandi_price_per_quintal": bench["price_per_quintal"],
        "market_trend": bench["trend"],
        "price_change_trend": bench["change_pct"],
        "local_market_info": bench["local_market"],
        "expected_harvest_date": harvest_dt_str,
        "days_remaining_to_harvest": days_to_harvest,
        "selling_time_guidance": selling_guidance,
        "market_preparation_reminders": [
            "Monitor local APMC mandi price arrivals 7-10 days before harvest",
            "Engage verified buyers via advance forward crop listings",
            "Prepare transport crates or bags before harvest week"
        ],
        "crop_listing_option": {
            "label": "CROP LISTING — VALID ONLY FOR PRE-HARVEST MARKETPLACE",
            "intent": "Upcoming croplot, expected harvest date, and advance buyer interest discovery",
            "status": "AVAILABLE_FOR_PRE_HARVEST",
            "active_listings_count": active_listings_count
        },
        "premium_pricing_allowed": False,
        "quality_grading_included": False,
        "cleaning_guidance_included": False
    }

    # -------------------------------------------------------------------------
    # 2. POST-HARVEST — CLEANED CROP STRUCTURE
    # -------------------------------------------------------------------------
    cleaning_proto = get_crop_cleaning_protocol(crop_norm)
    farmer_post_harvest_message = (
        "If you want to earn more, clean, dry and properly sort your harvested crop at home. "
        "After quality assessment, you may become eligible for a potential premium price."
    )

    post_harvest_flow = [
        "HARVEST",
        "CLEANING AT HOME",
        "DRYING",
        "SORTING",
        "QUALITY ASSESSMENT",
        "QUALITY GRADE",
        "POTENTIAL PREMIUM PRICE",
        "OPTIONAL LISTING"
    ]

    post_harvest_cleaned_crop = {
        "section_name": "POST-HARVEST — CLEANED CROP",
        "farmer_message": farmer_post_harvest_message,
        "availability": "POST_HARVEST_ONLY" if not is_harvested else "ACTIVE_NOW",
        "workflow": post_harvest_flow,
        "cleaning_guidance": {
            "crop": crop_display,
            "steps": cleaning_proto["cleaning_steps"],
            "quality_parameters": cleaning_proto["quality_parameters"],
        },
        "quality_grading_system": {
            "grades_available": ["Grade A", "Grade B", "Grade C"],
            "grade_criteria": cleaning_proto["grade_criteria"],
            "target_vs_achieved_rule": (
                "Farmer may select a Target Grade. Achieved Grade is calculated strictly from physical "
                "quality assessment measurements (Moisture %, Foreign Matter %, Defects %). "
                "Target Grade does not guarantee Achieved Grade or premium price."
            ),
            "premium_pricing_nature": "POTENTIAL_CONFIGURED_PREMIUM_NOT_GUARANTEED"
        },
        "optional_cleaned_crop_listing": {
            "status": "OPTIONAL_AFTER_QUALITY_ASSESSMENT",
            "description": "List verified cleaned lot with achieved grade and potential premium pricing."
        }
    }

    return {
        "marketplace_available": True,
        "crop": crop_display,
        "is_harvested": is_harvested,
        "active_market_listings": active_listings_count if active_listings_count > 0 else None,
        "marketplace_guidance": selling_guidance,
        "pre_harvest_marketplace": pre_harvest_marketplace,
        "post_harvest_cleaned_crop": post_harvest_cleaned_crop
    }
