import unittest
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.marketplace_quality_service import get_crop_cleaning_protocol, assess_crop_quality
from app.crop_monitoring.marketplace_context import get_marketplace_context


class TestMarketplaceTwoPhaseGuidance(unittest.TestCase):

    def test_crop_cleaning_protocols_available(self):
        crops = ["wheat", "rice", "tomato", "potato", "corn", "soybean"]
        for c in crops:
            proto = get_crop_cleaning_protocol(c)
            self.assertIsNotNone(proto)
            self.assertIn("cleaning_steps", proto)
            self.assertTrue(len(proto["cleaning_steps"]) > 0)
            self.assertIn("quality_parameters", proto)
            self.assertIn("grade_criteria", proto)
            self.assertIn("Grade A", proto["grade_criteria"])

    def test_quality_assessment_grade_a(self):
        result = assess_crop_quality(
            crop_name="wheat",
            target_grade="Grade A",
            moisture_pct=11.5,
            foreign_matter_pct=0.4,
            defects_pct=1.2,
            uniformity_pct=95.0,
            custom_base_price=2275.0
        )
        self.assertEqual(result["target_grade"], "Grade A")
        self.assertEqual(result["achieved_grade"], "Grade A")
        self.assertGreater(result["potential_total_price_per_quintal"], 2275.0)
        self.assertGreaterEqual(result["potential_premium_percentage"], 15.0)

    def test_quality_assessment_target_vs_achieved_separation(self):
        # Farmer targets Grade A, but physical test reveals high moisture and foreign matter
        result = assess_crop_quality(
            crop_name="wheat",
            target_grade="Grade A",
            moisture_pct=13.0,
            foreign_matter_pct=1.1,
            defects_pct=2.8,
            uniformity_pct=85.0,
            custom_base_price=2275.0
        )
        self.assertEqual(result["target_grade"], "Grade A")
        self.assertEqual(result["achieved_grade"], "Grade B")  # Does not auto-grant Grade A!
        self.assertLess(result["potential_premium_percentage"], 15.0)  # Grade B premium, not Grade A

    def test_marketplace_context_two_phase_structure(self):
        ctx = get_marketplace_context(crop_id="wheat", days_to_harvest=20, is_harvested=False)
        
        self.assertIn("pre_harvest_marketplace", ctx)
        self.assertIn("post_harvest_cleaned_crop", ctx)
        
        # Pre-harvest checks
        pre = ctx["pre_harvest_marketplace"]
        self.assertEqual(pre["section_name"], "PRE-HARVEST MARKETPLACE")
        self.assertFalse(pre["premium_pricing_allowed"])
        self.assertEqual(pre["crop_listing_option"]["label"], "CROP LISTING — VALID ONLY FOR PRE-HARVEST MARKETPLACE")
        
        # Post-harvest checks
        post = ctx["post_harvest_cleaned_crop"]
        self.assertEqual(post["section_name"], "POST-HARVEST — CLEANED CROP")
        self.assertIn("If you want to earn more, clean, dry and properly sort", post["farmer_message"])
        self.assertIn("HARVEST", post["workflow"])
        self.assertIn("CLEANING AT HOME", post["workflow"])
        self.assertIn("QUALITY ASSESSMENT", post["workflow"])
        self.assertIn("POTENTIAL PREMIUM PRICE", post["workflow"])


if __name__ == "__main__":
    unittest.main()

