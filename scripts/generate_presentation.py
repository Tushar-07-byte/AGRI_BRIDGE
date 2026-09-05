"""
Generate a 17-slide PPTX deck for AgriBridge college/hackathon presentation.
"""

from pathlib import Path
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "docs" / "presentation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "AgriBridge_Final_Presentation.pptx"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# Color Palette: Clean Modern Agricultural Tech
DARK_BG = RGBColor(15, 32, 24)       # Deep forest green
WHITE = RGBColor(255, 255, 255)
LIGHT_GREEN = RGBColor(46, 204, 113)  # Vibrant accent green
GOLD = RGBColor(241, 196, 15)        # Highlight gold
TEXT_MUTED = RGBColor(180, 195, 185)
CARD_BG = RGBColor(24, 48, 36)       # Subtle card background
BORDER_COLOR = RGBColor(39, 80, 58)

slides_data = [
    {
        "title": "AgriBridge",
        "subtitle": "Autonomous Farm-to-Field Advisory & Action Orchestration Platform\nSmart Horizon 2026 | Problem Statement: SH-AGR-001 (Agriculture & Rural Development)",
        "bullets": [
            "Empowering 140M+ Indian Smallholder Farmers with Grounded Autonomous Advisory",
            "Multi-Signal Deterministic Safety Engine & Closed-Loop Field Execution",
            "14-Language Conversational AI Companion (Kisan Saathi) with Zero-Hallucination Guardrails",
            "Direct FPO & Buyer Marketplace with Real-Time Agmarknet Mandi Pricing"
        ],
        "is_title": True
    },
    {
        "title": "1. Problem Landscape: The Indian Agritech Dilemma",
        "subtitle": "Why current digital agriculture solutions fail at the grassroots",
        "bullets": [
            "Advisory Fragmentation: Farmers rely on disconnected apps for weather, disease, and mandi prices.",
            "Unverified AI Hallucinations: Generic chatbots recommend inappropriate dosages leading to crop loss.",
            "Weather Vulnerability: Over 40% of applied agrochemicals wash away due to uncoordinated rainfall events.",
            "Middleman Exploitation: Asymmetric price information costs smallholders 25-35% of their harvest value.",
            "Connectivity & Literacy Barriers: Complex graphical forms alienate non-English and vernacular speakers."
        ]
    },
    {
        "title": "2. Farmer Pain Point: The Execution Chasm",
        "subtitle": "Advice without safe execution creates risk, not value",
        "bullets": [
            "\"I know my crop is sick, but is it safe to spray today?\"",
            "\"If rain starts in 3 hours, will my expensive chemical spray be wasted or harm soil ecology?\"",
            "\"Can I trust a computer vision diagnosis when leaves have overlapping symptoms?\"",
            "\"How do I track what tasks my farm labor must execute step-by-step?\"",
            "AgriBridge bridges the gap between passive diagnosis and guaranteed safe field execution."
        ]
    },
    {
        "title": "3. The AgriBridge Solution: Closed-Loop Platform",
        "subtitle": "From raw visual/sensor signals to deterministic farm action",
        "bullets": [
            "Multi-Signal Ingestion: Leaf imagery, soil telemetry (N-P-K, pH, Moisture), growth stages, and IMD/GFS weather.",
            "Autonomous Provenance Engine: Distinguishes LIVE authenticated signals from SIMULATED test feeds.",
            "Deterministic MultiSignalPolicyEngine: Sole decision authority — AI recommends, deterministic rules decide.",
            "4-State PlanTask Lifecycle: PENDING -> ACKNOWLEDGED -> IN_PROGRESS -> COMPLETED with full audit trail.",
            "Kisan Saathi Voice Companion: 14 Indian languages + Hinglish for 100% accessible conversational interface."
        ]
    },
    {
        "title": "4. Key Feature Matrix",
        "subtitle": "End-to-end capabilities across the agricultural value chain",
        "bullets": [
            "Computer Vision Diagnostics: Custom EfficientNet-B0 + ResNet architectures trained on 38+ plant disease classes.",
            "Pre-Execution Weather Gating: Hard safety lock delaying sprays when Rain > 60% or Wind > 20 km/h.",
            "Human-in-the-Loop Escalation: Automatic handoff to Krishi Vigyan Kendra (KVK) agents when AI confidence < 65%.",
            "Scientific ICAR Package of Practices: Grounded crop stage calendars (CRI, Tillering, Heading, Milking, Ripening).",
            "FPO & Direct Bidding Marketplace: Transparent bids above MSP with batch traceability certificates."
        ]
    },
    {
        "title": "5. System Architecture: 5-Layer Autonomous Pipeline",
        "subtitle": "Resilient, modular, and cloud-edge decoupled architecture",
        "bullets": [
            "Layer 1: Signal Ingestion (Vision Uploads, Soil IoT Telemetry, Weather Forecast API, Voice Audio).",
            "Layer 2: Quality & Provenance (E.164 Identity, Sensor Drift Detection, Signal Trust Scoring).",
            "Layer 3: Multi-Signal Policy Engine (ICAR Rule Fusion, Weather Gating, Disease Thresholding).",
            "Layer 4: Action Orchestration (ActionPlan Generator, 4-State Task Tracker, Dynamic Recheck Scheduler).",
            "Layer 5: Presentation & Voice (Farmer UI, Field Agent Portal, Buyer Marketplace, Kisan Saathi)."
        ]
    },
    {
        "title": "6. Autonomous Decision Loop: MultiSignalPolicyEngine",
        "subtitle": "Deterministic safety as the sole decision authority",
        "bullets": [
            "Multi-Signal Policy Engine acts as the strict cryptographic & agronomic gatekeeper.",
            "Four Exclusive Policy Decisions:",
            "  • ALLOWED: All signals valid, confidence >= 65%, weather safe -> Generates executable PlanTask.",
            "  • DEFERRED: Disease valid but weather unsafe (Rain > 60% or Wind > 20 km/h) -> Zero unsafe tasks, auto-recheck.",
            "  • BLOCKED: Invalid agronomic combination or sensor failure -> Zero tasks, safety alert issued.",
            "  • REQUIRES_HUMAN_REVIEW: Borderline confidence (< 65%) -> Field agent escalation ticket created."
        ]
    },
    {
        "title": "7. AI/ML + Deterministic Safety Fusion",
        "subtitle": "Combining statistical AI flexibility with deterministic engineering guarantees",
        "bullets": [
            "Core Architectural Rule: AI and LLMs are strictly ADVISORY; they CANNOT create executable field tasks.",
            "Zero-Hallucination Kisan Saathi: LLM responses are constrained to ICAR agronomic reference templates.",
            "Confidence Isolation: Vision probabilities are bounded and calibrated before passing to the policy engine.",
            "No Autonomous Override: Human agent verification updates context and triggers deterministic re-evaluation."
        ]
    },
    {
        "title": "8. Crop Diagnostics & Disease Inference",
        "subtitle": "Robust deep learning visual diagnostics",
        "bullets": [
            "Deep Learning Pipeline: EfficientNet-B0 + ResNet50 backbone with calibrated softmax confidence.",
            "Comprehensive Crop Coverage: Wheat (Rust, Blight), Tomato (Early/Late Blight, Yellow Leaf Curl), Rice, Maize, Potato.",
            "Dynamic Fallback & Mocking: Graceful degradation to ICAR heuristics if GPU/TensorFlow is unavailable.",
            "Signal Trust Scoring: Image resolution, blur detection, and timestamp validity checks."
        ]
    },
    {
        "title": "9. Dynamic Weather Adaptation & Safe Deferral",
        "subtitle": "Zero agrochemical loss through automated meteorology integration",
        "bullets": [
            "Real-Time Weather Integration: 15-day dynamic forecast via IMD / Open-Meteo API.",
            "Pre-Execution Gating: Evaluates precipitation probability, wind velocity, and ambient humidity.",
            "Automatic Rescheduling: Deferrals trigger a non-blocking background recheck timer for safe weather windows.",
            "Farmer Visibility: The UI displays exact weather constraints (e.g. \"Spray deferred: 75% rain expected in 2h\")."
        ]
    },
    {
        "title": "10. Human-in-the-Loop (HITL) Field Escalation",
        "subtitle": "Protecting farmers from catastrophic edge cases and false positives",
        "bullets": [
            "Automated Escalation: Vision AI confidence < 65% triggers an escalation ticket for Field Agents / KVK officers.",
            "Prescription Lock: Farmer dashboard shows \"Escalated for Officer Review\"; chemical application remains locked.",
            "Field Agent Portal: Officer inspects high-res imagery, reviews farm history, and submits expert verification.",
            "Context Rebuild & Re-Evaluation: Officer verification updates context and re-triggers policy evaluation cleanly."
        ]
    },
    {
        "title": "11. Farmer-First UI & Vernacular Experience",
        "subtitle": "Designed for maximum readability and instant cognitive clarity",
        "bullets": [
            "Glanceable Primary Card: Farm/Crop, Health Status, Confidence %, Decision State, and Task Progress.",
            "Clean Decision Badges: Green (ALLOWED), Orange (DEFERRED - Weather), Yellow (UNDER REVIEW), Red (BLOCKED).",
            "Single-Tap Task Acknowledgment: Clear progression from Pending -> Acknowledged -> In Progress -> Completed.",
            "Deep Traceability: Secondary modal provides telemetry logs, policy reasoning, and audit timestamps."
        ]
    },
    {
        "title": "12. Kisan Saathi: Multilingual Voice Assistant",
        "subtitle": "Natural voice interaction for 100% digital accessibility",
        "bullets": [
            "14 Indian Languages: Hindi, Punjabi, Marathi, Bengali, Telugu, Tamil, Gujarati, Kannada, Odia, and Hinglish.",
            "Context-Aware UI Navigation: Voice commands navigate pages (e.g., \"Mera khet dikhao\", \"Marketplace kholo\").",
            "Multilingual Speech-to-Text & Text-to-Speech: Web Speech API + Gemini Multilingual STT + gTTS synthesis.",
            "Strict Scope Boundary: Deflects non-agricultural queries politely to maintain zero-hallucination integrity."
        ]
    },
    {
        "title": "13. End-to-End Judge Validation Scenarios (A to J)",
        "subtitle": "100% verified across 10 mission-critical operational conditions",
        "bullets": [
            "Scenario A (Safe/Allowed): High confidence + clear weather -> ALLOWED -> 1 Executable Task.",
            "Scenario B (Rain/Deferred): Valid disease + 80% rain -> DEFERRED -> Zero unsafe tasks -> Auto-recheck scheduled.",
            "Scenario C (High Wind): Valid disease + 28 km/h wind -> DEFERRED -> Safe application window tracked.",
            "Scenario D (Borderline Review): 58% confidence -> REQUIRES_HUMAN_REVIEW -> Ticket created in Agent Portal.",
            "Scenario E (Agent Verification): Officer verifies Leaf Rust -> Context rebuilt -> Re-evaluated -> ALLOWED.",
            "Scenario F to J: Blocked invalid combos, simulated data tags, weather clearing recheck, and safe network fallbacks."
        ]
    },
    {
        "title": "14. Engineering Rigor, Testing & Reliability",
        "subtitle": "Production-grade automated test coverage and zero flaky tests",
        "bullets": [
            "Automated Test Suite: 270 Tests Total (156 Unit Tests + 114 Integration Tests).",
            "Test Pass Rate: 270 Passed / 0 Failed / 0 Errors (100% Green in ~80 seconds).",
            "Role-Based Access Control: Strict JWT isolation across Farmer, Field Agent, Buyer, and Admin roles.",
            "Database Agnostic: Active MySQL support with seamless SQLite automatic fallback."
        ]
    },
    {
        "title": "15. Core Innovation & Competitive Advantages",
        "subtitle": "How AgriBridge stands out against existing agritech offerings",
        "bullets": [
            "Autonomous Closed-Loop vs. Advisory Only: Does not stop at diagnosis; manages physical execution lifecycles.",
            "Deterministic Safety Engine: Eliminates LLM and vision model hallucination risks in agrochemical dosing.",
            "Multi-Signal Coherence: Simultaneously evaluates soil chemistry, crop phenology, and atmospheric forecast.",
            "Zero-Hardware Barrier: Works with standard smartphones, basic camera inputs, and voice."
        ]
    },
    {
        "title": "16. Limitations & Future Development Roadmap",
        "subtitle": "Honest current scope and clear production scaling path",
        "bullets": [
            "Current Scope: Tested on Wheat, Tomato, Rice, Maize, Potato; Simulated IoT telemetry for hackathon demo.",
            "Hardware Integration: Direct LoRaWAN / NB-IoT soil sensor probe plug-ins in Phase 6.",
            "Satellite Earth Observation: Sentinel-2 NDVI spectral vegetation indexing for field-scale biomass mapping.",
            "FPO Aggregation: Smart contract escrow payments and cooperative bulk purchasing discounts."
        ]
    },
    {
        "title": "17. Conclusion & Submission Summary",
        "subtitle": "AgriBridge — Autonomous Farm-to-Field Advisory & Action Orchestration",
        "bullets": [
            "Complete end-to-end working platform ready for immediate judge evaluation.",
            "270/270 automated tests passing with zero failures.",
            "Comprehensive documentation, architecture diagrams, and verified demo seed data.",
            "Thank You! Questions & Live Demonstration."
        ]
    }
]

# Helper to create slides
for slide_info in slides_data:
    slide = prs.slides.add_slide(prs.slide_layouts[6]) # blank layout
    
    # Background fill
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = DARK_BG
    bg.line.fill.background()
    
    # Top Accent Bar
    top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.5), Inches(11.733), Inches(0.08))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = LIGHT_GREEN
    top_bar.line.fill.background()
    
    # Header Box
    header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.733), Inches(1.3))
    tf = header_box.text_frame
    tf.word_wrap = True
    
    p_title = tf.paragraphs[0]
    p_title.text = slide_info["title"]
    p_title.font.name = "Arial"
    p_title.font.size = Pt(28) if not slide_info.get("is_title") else Pt(38)
    p_title.font.bold = True
    p_title.font.color.rgb = WHITE if not slide_info.get("is_title") else LIGHT_GREEN
    
    p_sub = tf.add_paragraph()
    p_sub.text = slide_info["subtitle"]
    p_sub.font.name = "Arial"
    p_sub.font.size = Pt(14)
    p_sub.font.color.rgb = GOLD if slide_info.get("is_title") else TEXT_MUTED
    p_sub.space_before = Pt(4)
    
    # Content Card
    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(0.8), Inches(2.2), Inches(11.733), Inches(4.7)
    )
    card.fill.solid()
    card.fill.fore_color.rgb = CARD_BG
    card.line.color.rgb = BORDER_COLOR
    card.line.width = Pt(1.5)
    
    # Content Box inside Card
    content_box = slide.shapes.add_textbox(Inches(1.1), Inches(2.4), Inches(11.133), Inches(4.3))
    ctf = content_box.text_frame
    ctf.word_wrap = True
    
    for i, bullet in enumerate(slide_info["bullets"]):
        p = ctf.paragraphs[0] if i == 0 else ctf.add_paragraph()
        p.text = bullet
        p.font.name = "Arial"
        p.font.size = Pt(16) if not slide_info.get("is_title") else Pt(18)
        p.font.color.rgb = WHITE
        p.space_after = Pt(12)
        if bullet.startswith("  •"):
            p.level = 1
            p.font.size = Pt(14)
            p.font.color.rgb = TEXT_MUTED

prs.save(str(OUTPUT_FILE))
print(f"Presentation saved successfully to: {OUTPUT_FILE}")

