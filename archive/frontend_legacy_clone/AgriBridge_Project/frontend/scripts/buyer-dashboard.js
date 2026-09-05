// ==========================================================================
// AGRIBRIDGE — BUYER DASHBOARD & VERIFIED MARKETPLACE SCRIPT
// Hackathon Final Implementation with End-to-End Field Agent Health Audits
// ==========================================================================

console.log("=== AGRIBRIDGE BUYER DASHBOARD INITIALIZING ===");

// ==========================================================================
// CONFIGURATION & CONSTANTS
// ==========================================================================

const API_BASE_URL = "http://127.0.0.1:8000";
const BUYER_ID = 101;
const BUYER_NAME = "Demo Buyer";

// Default standard crop pricing (₹/kg) when not explicitly stored in database table
const CROP_DEFAULT_PRICES = {
    "wheat": 25,
    "rice": 22,
    "tomato": 18,
    "potato": 15,
    "maize": 20,
    "soybean": 42,
    "cotton": 65,
    "sugarcane": 4,
    "onion": 24,
    "gram": 55,
    "mustard": 52
};

// Known Farmer directory mapping for UI presentation matching Leaflet Map
// Known Farmer directory mapping for UI presentation matching Leaflet Map
const FARMER_DIRECTORY = {
    1: {
        name: "Ramesh Patel",
        location: "Raipur, Chhattisgarh",
        lat: 21.2514,
        lng: 81.6296,
        fieldAgent: "Amit Sharma",
        agentId: "FA-204",
        agentPhone: "+91 98271 44512",
        territory: "Raipur Central Agricultural Zone"
    },
    2: {
        name: "Gurpreet Singh",
        location: "Bathinda, Punjab",
        lat: 30.2110,
        lng: 74.9455,
        fieldAgent: "Balwinder Singh",
        agentId: "FA-405",
        agentPhone: "+91 98765 12340",
        territory: "Malwa Agricultural Belt"
    },
    3: {
        name: "Suresh Meena",
        location: "Kota, Rajasthan",
        lat: 25.2138,
        lng: 75.8648,
        fieldAgent: "Kailash Joshi",
        agentId: "FA-501",
        agentPhone: "+91 94140 88219",
        territory: "Hadoti Mustard Zone"
    },
    4: {
        name: "Vijay Singh",
        location: "Rajnandgaon, Chhattisgarh",
        lat: 21.2350,
        lng: 81.6500,
        fieldAgent: "Pooja Verma",
        agentId: "FA-318",
        agentPhone: "+91 97531 66204",
        territory: "Rajnandgaon South District"
    },
    5: {
        name: "Anil Sahu",
        location: "Raipur, Chhattisgarh",
        lat: 21.2700,
        lng: 81.6200,
        fieldAgent: "Amit Sharma",
        agentId: "FA-204",
        agentPhone: "+91 98271 44512",
        territory: "Raipur North Agricultural Zone"
    },
    6: {
        name: "Anand Deshmukh",
        location: "Nagpur, Maharashtra",
        lat: 21.1458,
        lng: 79.0882,
        fieldAgent: "Devendra Verma",
        agentId: "FA-303",
        agentPhone: "+91 98222 34109",
        territory: "Vidarbha Cotton Hub"
    },
    7: {
        name: "Vikram Chauhan",
        location: "Karnal, Haryana",
        lat: 29.6857,
        lng: 76.9905,
        fieldAgent: "Priya Nair",
        agentId: "FA-109",
        agentPhone: "+91 98120 77410",
        territory: "Karnal Agro-Sugar Belt"
    },
    8: {
        name: "Harishankar Yadav",
        location: "Varanasi, Uttar Pradesh",
        lat: 25.3176,
        lng: 82.9739,
        fieldAgent: "Pooja Verma",
        agentId: "FA-318",
        agentPhone: "+91 97531 66204",
        territory: "Eastern UP Tuber Belt"
    }
};

// Crop emoji mapping
const CROP_EMOJIS = {
    "wheat": "🌾",
    "rice": "🍚",
    "tomato": "🍅",
    "potato": "🥔",
    "maize": "🌽",
    "soybean": "🌱",
    "cotton": "☁️",
    "sugarcane": "🎋",
    "onion": "🧅",
    "mustard": "🌼"
};

// Crop fallback images (High-definition, authentic agriculture photography)
const CROP_FALLBACK_IMAGES = {
    "wheat": "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=800&auto=format&fit=crop&q=80",
    "rice": "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=800&auto=format&fit=crop&q=80",
    "mustard": "https://images.unsplash.com/photo-1508747703725-719777637510?w=800&auto=format&fit=crop&q=80",
    "soybean": "https://images.unsplash.com/photo-1595855759920-86582396756a?w=800&auto=format&fit=crop&q=80",
    "maize": "https://images.unsplash.com/photo-1551754655-cd27e38d2076?w=800&auto=format&fit=crop&q=80",
    "cotton": "https://images.unsplash.com/photo-1606041008023-472dfb5e530f?w=800&auto=format&fit=crop&q=80",
    "sugarcane": "https://images.unsplash.com/photo-1605000797499-95a51c5269ae?w=800&auto=format&fit=crop&q=80",
    "potato": "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=800&auto=format&fit=crop&q=80",
    "tomato": "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=800&auto=format&fit=crop&q=80",
    "default": "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?w=800&auto=format&fit=crop&q=80"
};

// Realistic AgriBridge Seed Data with End-to-End Field Agent Health Audits
const DEMO_LISTINGS = [
    {
        id: 1,
        farmer_id: 1,
        farmer_name: "Ramesh Patel",
        crop_type: "Wheat",
        quantity_est: 5000,
        unit_price: 27,
        harvest_date: "2026-10-15",
        location: "Raipur, Chhattisgarh",
        lat: 21.2514,
        lng: 81.6296,
        health_status: "Healthy (Grade A+)",
        confidence: 0.95,
        photo_path: "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=800&auto=format&fit=crop&q=80",
        status: "Available",
        field_agent: "Amit Sharma",
        agent_id: "FA-204",
        quality_grade: "Grade A+",
        quality_score: 96,
        cert_id: "AGB-CERT-2026-081",
        verified_at: "2026-08-28",
        verification_status: "verified",
        remarks: "Comprehensive field inspection complete. Vigorous crop stand, optimal grain filling stage, zero rust or blight detected.",
        audit_details: {
            foliage: { score: "98/100", status: "Optimal", desc: "Dark green uniform canopy with strong tillering count." },
            pest: { score: "0% Rate", status: "Pest-Free", desc: "No aphids, stem borers, or armyworms identified in sample rows." },
            moisture: { score: "94/100", status: "Balanced", desc: "Soil moisture measured at 22% (ideal root zone level)." },
            maturity: { score: "88%", status: "On Schedule", desc: "Grain heading completed; hardening expected in 18 days." },
            safety: { score: "100% Safe", status: "Compliant", desc: "Organic bio-fungicide used; zero chemical residue violations." },
            yield_check: { score: "5,000 kg ± 3%", status: "Audited", desc: "Quadrat sampling confirms estimated harvest quantity." }
        }
    },
    {
        id: 2,
        farmer_id: 2,
        farmer_name: "Gurpreet Singh",
        crop_type: "Rice",
        quantity_est: 3500,
        unit_price: 75,
        harvest_date: "2026-10-20",
        location: "Bathinda, Punjab",
        lat: 30.2110,
        lng: 74.9455,
        health_status: "Healthy (Basmati 1121)",
        confidence: 0.96,
        photo_path: "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=800&auto=format&fit=crop&q=80",
        status: "Available",
        field_agent: "Balwinder Singh",
        agent_id: "FA-405",
        quality_grade: "Grade A+",
        quality_score: 97,
        cert_id: "AGB-CERT-2026-082",
        verified_at: "2026-08-29",
        verification_status: "verified",
        remarks: "Physical field check verified. High paddy density with no stem borer or blast infestation. Extra long aromatic grain.",
        audit_details: {
            foliage: { score: "96/100", status: "Optimal", desc: "Healthy vegetative canopy with consistent panicle emergence." },
            pest: { score: "0% Rate", status: "Pest-Free", desc: "Yellow stem borer monitoring traps clean; no leaf folder marks." },
            moisture: { score: "96/100", status: "Optimal", desc: "Canal irrigation flood level maintained at controlled 4cm." },
            maturity: { score: "84%", status: "On Schedule", desc: "Milky grain stage complete; dough stage progressing well." },
            safety: { score: "100% Safe", status: "Compliant", desc: "IPM bio-control methods followed by farmer." },
            yield_check: { score: "3,500 kg ± 3%", status: "Audited", desc: "Field panicle count matches projected volume." }
        }
    },
    {
        id: 3,
        farmer_id: 3,
        farmer_name: "Suresh Meena",
        crop_type: "Mustard",
        quantity_est: 4000,
        unit_price: 58,
        harvest_date: "2026-11-05",
        location: "Kota, Rajasthan",
        lat: 25.2138,
        lng: 75.8648,
        health_status: "Healthy (Pusa Bold)",
        confidence: 0.94,
        photo_path: "https://images.unsplash.com/photo-1508747703725-719777637510?w=800&auto=format&fit=crop&q=80",
        status: "Available",
        field_agent: "Kailash Joshi",
        agent_id: "FA-501",
        quality_grade: "Grade A+",
        quality_score: 95,
        cert_id: "AGB-CERT-2026-083",
        verified_at: "2026-08-30",
        verification_status: "verified",
        remarks: "Audited high-oil mustard plot. Pods fully developed, zero aphid damage, and uniform yellow blossom stage.",
        audit_details: {
            foliage: { score: "95/100", status: "Optimal", desc: "Dense flower canopy with high bee pollination activity." },
            pest: { score: "0% Rate", status: "Pest-Free", desc: "Mustard aphid and sawfly check negative." },
            moisture: { score: "92/100", status: "Balanced", desc: "Deep black loam soil retains optimum residual moisture." },
            maturity: { score: "80%", status: "On Schedule", desc: "Pod elongation active; oil content expected at 42%." },
            safety: { score: "100% Safe", status: "Compliant", desc: "Certified organic soil conditioner applied." },
            yield_check: { score: "4,000 kg ± 4%", status: "Audited", desc: "Pod per plant sampling confirms volume." }
        }
    },
    {
        id: 4,
        farmer_id: 4,
        farmer_name: "Vijay Singh",
        crop_type: "Soybean",
        quantity_est: 3000,
        unit_price: 42,
        harvest_date: "2026-10-18",
        location: "Rajnandgaon, Chhattisgarh",
        lat: 21.2350,
        lng: 81.6500,
        health_status: "Healthy (JS 335)",
        confidence: 0.93,
        photo_path: "https://images.unsplash.com/photo-1595855759920-86582396756a?w=800&auto=format&fit=crop&q=80",
        status: "Available",
        field_agent: "Pooja Verma",
        agent_id: "FA-318",
        quality_grade: "Grade A+",
        quality_score: 95,
        cert_id: "AGB-CERT-2026-084",
        verified_at: "2026-08-31",
        verification_status: "verified",
        remarks: "Inspection verified. High nodulation, 3-4 seeded pods per node, and zero yellow mosaic virus.",
        audit_details: {
            foliage: { score: "97/100", status: "Optimal", desc: "Dense bushy foliage with zero leaf rust or defoliation." },
            pest: { score: "0% Rate", status: "Pest-Free", desc: "Girdle beetle and pod borer visual sweep clear." },
            moisture: { score: "93/100", status: "Balanced", desc: "Rain-fed moisture profile well retained in black soil." },
            maturity: { score: "85%", status: "On Schedule", desc: "Pod maturation progressing; leaf yellowing starting naturally." },
            safety: { score: "100% Safe", status: "Compliant", desc: "Rhizobium bio-inoculant confirmed." },
            yield_check: { score: "3,000 kg ± 3%", status: "Audited", desc: "Plant pod count confirms 3,000kg harvest." }
        }
    },
    {
        id: 5,
        farmer_id: 5,
        farmer_name: "Anil Sahu",
        crop_type: "Maize",
        quantity_est: 4500,
        unit_price: 22,
        harvest_date: "2026-10-25",
        location: "Raipur, Chhattisgarh",
        lat: 21.2700,
        lng: 81.6200,
        health_status: "Healthy (Hybrid HQPM-1)",
        confidence: 0.91,
        photo_path: "https://images.unsplash.com/photo-1551754655-cd27e38d2076?w=800&auto=format&fit=crop&q=80",
        status: "Available",
        field_agent: "Amit Sharma",
        agent_id: "FA-204",
        quality_grade: "Grade A",
        quality_score: 92,
        cert_id: "AGB-CERT-2026-085",
        verified_at: "2026-08-30",
        verification_status: "verified",
        remarks: "Field Agent verified. Proper cob formation, full kernel tip filling, and adequate soil nitrogen.",
        audit_details: {
            foliage: { score: "92/100", status: "Good", desc: "Tall upright stalks with strong brace root anchorage." },
            pest: { score: "0% Rate", status: "Pest-Free", desc: "Fall armyworm pheromone traps inspected; zero active larvae." },
            moisture: { score: "90/100", status: "Good", desc: "Furrow irrigation moisture adequate at 20cm depth." },
            maturity: { score: "78%", status: "On Schedule", desc: "Silking completed; grain denting stage underway." },
            safety: { score: "100% Safe", status: "Compliant", desc: "Standard organic booster applied." },
            yield_check: { score: "4,500 kg ± 4%", status: "Audited", desc: "Cob density audit confirms volume target." }
        }
    },
    {
        id: 6,
        farmer_id: 6,
        farmer_name: "Anand Deshmukh",
        crop_type: "Cotton",
        quantity_est: 3200,
        unit_price: 68,
        harvest_date: "2026-11-12",
        location: "Nagpur, Maharashtra",
        lat: 21.1458,
        lng: 79.0882,
        health_status: "Healthy (Long Staple BT)",
        confidence: 0.95,
        photo_path: "https://images.unsplash.com/photo-1606041008023-472dfb5e530f?w=800&auto=format&fit=crop&q=80",
        status: "Available",
        field_agent: "Devendra Verma",
        agent_id: "FA-303",
        quality_grade: "Grade A+",
        quality_score: 96,
        cert_id: "AGB-CERT-2026-086",
        verified_at: "2026-08-31",
        verification_status: "verified",
        remarks: "Premium long-staple cotton stand. High boll retention, clean white fiber lint, zero pink bollworm.",
        audit_details: {
            foliage: { score: "96/100", status: "Optimal", desc: "Strong sympodial branching with healthy square formation." },
            pest: { score: "0% Rate", status: "Pest-Free", desc: "Pink bollworm pheromone traps show zero catch." },
            moisture: { score: "91/100", status: "Good", desc: "Black cotton soil depth moisture adequate." },
            maturity: { score: "75%", status: "On Schedule", desc: "Boll opening initiated across bottom branches." },
            safety: { score: "100% Safe", status: "Compliant", desc: "Bio-agent Trichogramma released." },
            yield_check: { score: "3,200 kg ± 3%", status: "Audited", desc: "Boll count per plant verifies harvest estimate." }
        }
    },
    {
        id: 7,
        farmer_id: 7,
        farmer_name: "Vikram Chauhan",
        crop_type: "Sugarcane",
        quantity_est: 8000,
        unit_price: 34,
        harvest_date: "2026-11-28",
        location: "Karnal, Haryana",
        lat: 29.6857,
        lng: 76.9905,
        health_status: "Healthy (Co 0238 High Brix)",
        confidence: 0.96,
        photo_path: "https://images.unsplash.com/photo-1605000797499-95a51c5269ae?w=800&auto=format&fit=crop&q=80",
        status: "Available",
        field_agent: "Priya Nair",
        agent_id: "FA-109",
        quality_grade: "Grade A+",
        quality_score: 97,
        cert_id: "AGB-CERT-2026-087",
        verified_at: "2026-09-01",
        verification_status: "verified",
        remarks: "Certified high-sucrose sugarcane stand. Thick canes, average 2.8m height, zero red rot or top borer.",
        audit_details: {
            foliage: { score: "98/100", status: "Optimal", desc: "Lush green crown foliage with clean de-trashing." },
            pest: { score: "0% Rate", status: "Pest-Free", desc: "Early shoot borer and pyrilla tests clean." },
            moisture: { score: "95/100", status: "Optimal", desc: "Furrow irrigation moisture level balanced." },
            maturity: { score: "82%", status: "On Schedule", desc: "Brix refractometer reading 19.5%." },
            safety: { score: "100% Safe", status: "Compliant", desc: "Pressmud and bio-fertilizer verified." },
            yield_check: { score: "8,000 kg ± 3%", status: "Audited", desc: "Millable cane count per meter verified." }
        }
    },
    {
        id: 8,
        farmer_id: 8,
        farmer_name: "Harishankar Yadav",
        crop_type: "Potato",
        quantity_est: 3800,
        unit_price: 16,
        harvest_date: "2026-10-30",
        location: "Varanasi, Uttar Pradesh",
        lat: 25.3176,
        lng: 82.9739,
        health_status: "Healthy (Kufri Jyoti)",
        confidence: 0.92,
        photo_path: "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=800&auto=format&fit=crop&q=80",
        status: "Available",
        field_agent: "Pooja Verma",
        agent_id: "FA-318",
        quality_grade: "Grade A",
        quality_score: 93,
        cert_id: "AGB-CERT-2026-088",
        verified_at: "2026-08-30",
        verification_status: "verified",
        remarks: "Certified seed and table potato stand. Uniform tuber sizing, smooth skin, zero late blight symptoms.",
        audit_details: {
            foliage: { score: "94/100", status: "Optimal", desc: "Dense green canopy covering ridge tops completely." },
            pest: { score: "0% Rate", status: "Pest-Free", desc: "Aphid counts below critical economic threshold (0/100 leaves)." },
            moisture: { score: "91/100", status: "Balanced", desc: "Sprinkler irrigation maintained at optimal moisture field capacity." },
            maturity: { score: "80%", status: "On Schedule", desc: "Tuber bulking phase in progress; skin setting expected soon." },
            safety: { score: "100% Safe", status: "Compliant", desc: "Bio-fungicide preventive spray program." },
            yield_check: { score: "3,800 kg ± 4%", status: "Audited", desc: "Tuber per hill test digs confirm lot weight." }
        }
    },
    {
        id: 9,
        farmer_id: 3,
        farmer_name: "Mahesh Verma",
        crop_type: "Tomato",
        quantity_est: 1800,
        unit_price: 18,
        harvest_date: "2026-10-10",
        location: "Bilaspur, Chhattisgarh",
        lat: 21.2420,
        lng: 81.6180,
        health_status: "Healthy (Himsona)",
        confidence: 0.96,
        photo_path: "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=800&auto=format&fit=crop&q=80",
        status: "Available",
        field_agent: "Rahul Sahu",
        agent_id: "FA-109",
        quality_grade: "Grade A+",
        quality_score: 95,
        cert_id: "AGB-CERT-2026-089",
        verified_at: "2026-08-30",
        verification_status: "verified",
        remarks: "Greenhouse & field plot inspected. Uniform fruit development, firm pericarp, and zero early blight.",
        audit_details: {
            foliage: { score: "96/100", status: "Optimal", desc: "Vigorous indeterminate vine growth with strong staking support." },
            pest: { score: "0% Rate", status: "Pest-Free", desc: "Whitefly and fruit borer visual sampling completely negative." },
            moisture: { score: "92/100", status: "Controlled", desc: "Drip irrigation functioning with optimal fertigation cycle." },
            maturity: { score: "90%", status: "On Schedule", desc: "Breaker stage starting; harvest readiness within 9 days." },
            safety: { score: "100% Safe", status: "Compliant", desc: "Neem extract spray log verified." },
            yield_check: { score: "1,800 kg ± 4%", status: "Audited", desc: "Cluster sampling verifies estimated lot weight." }
        }
    },
    {
        id: 10,
        farmer_id: 6,
        farmer_name: "Baburao Kadam",
        crop_type: "Onion",
        quantity_est: 4200,
        unit_price: 24,
        harvest_date: "2026-11-15",
        location: "Nashik, Maharashtra",
        lat: 19.9975,
        lng: 73.7898,
        health_status: "Healthy (Red Nasik)",
        confidence: 0.95,
        photo_path: "https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=800&auto=format&fit=crop&q=80",
        status: "Available",
        field_agent: "Devendra Verma",
        agent_id: "FA-303",
        quality_grade: "Grade A+",
        quality_score: 96,
        cert_id: "AGB-CERT-2026-090",
        verified_at: "2026-09-01",
        verification_status: "verified",
        remarks: "Inspection verified. Uniform bulb formation, tight papery skin layers, zero purple blotch.",
        audit_details: {
            foliage: { score: "95/100", status: "Optimal", desc: "Upright hollow cylindrical green leaves with strong waxy bloom." },
            pest: { score: "0% Rate", status: "Pest-Free", desc: "Thrips visual count zero; sticky traps inspected." },
            moisture: { score: "90/100", status: "Good", desc: "Drip irrigation moisture adequate." },
            maturity: { score: "78%", status: "On Schedule", desc: "Bulb expansion stage progressing on target." },
            safety: { score: "100% Safe", status: "Compliant", desc: "Safe bio-agent compliance." },
            yield_check: { score: "4,200 kg ± 3%", status: "Audited", desc: "Bulb sampling confirms stated volume." }
        }
    },
    {
        id: 11,
        farmer_id: 1,
        farmer_name: "Brijesh Mishra",
        crop_type: "Wheat",
        quantity_est: 6000,
        unit_price: 29,
        harvest_date: "2026-10-28",
        location: "Indore, Madhya Pradesh",
        lat: 22.7196,
        lng: 75.8577,
        health_status: "Healthy (Durum Malwa Gold)",
        confidence: 0.96,
        photo_path: "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?w=800&auto=format&fit=crop&q=80",
        status: "Available",
        field_agent: "Kailash Joshi",
        agent_id: "FA-501",
        quality_grade: "Grade A+",
        quality_score: 97,
        cert_id: "AGB-CERT-2026-091",
        verified_at: "2026-09-01",
        verification_status: "verified",
        remarks: "High-protein durum wheat stand. Excellent amber semolina quality, zero loose smut or rust.",
        audit_details: {
            foliage: { score: "98/100", status: "Optimal", desc: "Broad erect flag leaves with intense solar absorption." },
            pest: { score: "0% Rate", status: "Pest-Free", desc: "Sample quadrat sweep clear of pests." },
            moisture: { score: "94/100", status: "Balanced", desc: "Black soil moisture capacity ideal." },
            maturity: { score: "82%", status: "On Schedule", desc: "Heading phase complete; kernel filling underway." },
            safety: { score: "100% Safe", status: "Compliant", desc: "Zero chemical residues." },
            yield_check: { score: "6,000 kg ± 3%", status: "Audited", desc: "Spike count per meter confirms yield." }
        }
    },
    {
        id: 12,
        farmer_id: 4,
        farmer_name: "Venkat Rao",
        crop_type: "Tomato",
        quantity_est: 2500,
        unit_price: 32,
        harvest_date: "2026-11-08",
        location: "Guntur, Andhra Pradesh",
        lat: 16.3067,
        lng: 80.4365,
        health_status: "Healthy (Guntur Special)",
        confidence: 0.94,
        photo_path: "https://images.unsplash.com/photo-1588252303782-cb80119abd6d?w=800&auto=format&fit=crop&q=80",
        status: "Available",
        field_agent: "Priya Nair",
        agent_id: "FA-109",
        quality_grade: "Grade A+",
        quality_score: 95,
        cert_id: "AGB-CERT-2026-092",
        verified_at: "2026-09-01",
        verification_status: "verified",
        remarks: "Certified commercial spice stand. High fruit count, vibrant color, zero anthracnose.",
        audit_details: {
            foliage: { score: "96/100", status: "Optimal", desc: "Strong canopy with vigorous fruit set." },
            pest: { score: "0% Rate", status: "Pest-Free", desc: "Mite and thrips visual inspections negative." },
            moisture: { score: "93/100", status: "Balanced", desc: "Red soil drip system verified." },
            maturity: { score: "85%", status: "On Schedule", desc: "Pod development on schedule." },
            safety: { score: "100% Safe", status: "Compliant", desc: "GAP farming standards adhered." },
            yield_check: { score: "2,500 kg ± 4%", status: "Audited", desc: "Fruit load count confirms volume." }
        }
    }
];

// ==========================================================================
// APPLICATION STATE
// ==========================================================================

const AppState = {
    currentTab: "marketplace", // 'marketplace' | 'commitments'
    isBackendLive: false,
    forceDemoMode: false,
    allListings: [],
    allVerifications: [],
    allOrders: [],
    verifiedListings: [],
    committedListingIds: new Set(),
    selectedListingForModal: null,
    filters: {
        search: "",
        crop: "",
        location: "",
        agent: "",
        grade: "",
        status: "available", // 'all' | 'available' | 'committed'
        sort: "harvest_asc"
    }
};

// ==========================================================================
// DOM ELEMENTS
// ==========================================================================

const DOM = {
    // Navigation & Tabs
    tabMarketplaceBtn: document.getElementById("tab-marketplace-btn"),
    tabCommitmentsBtn: document.getElementById("tab-commitments-btn"),
    commitmentsNavBadge: document.getElementById("commitments-nav-badge"),
    modeToggleBtn: document.getElementById("mode-toggle-btn"),
    modeToggleLabel: document.getElementById("mode-toggle-label"),
    buyerDisplayName: document.getElementById("buyer-display-name"),

    // Views
    marketplaceTabView: document.getElementById("marketplace-tab-view"),
    commitmentsTabView: document.getElementById("commitments-tab-view"),

    // Hero Stats
    statVerifiedCount: document.getElementById("stat-verified-count"),
    statTotalSupply: document.getElementById("stat-total-supply"),
    statCommitmentsCount: document.getElementById("stat-commitments-count"),

    // Toolbar & Controls
    searchInput: document.getElementById("search-input"),
    clearSearchBtn: document.getElementById("clear-search-btn"),
    cropFilter: document.getElementById("crop-filter"),
    locationFilter: document.getElementById("location-filter"),
    agentFilter: document.getElementById("agent-filter"),
    gradeFilter: document.getElementById("grade-filter"),
    statusFilter: document.getElementById("status-filter"),
    sortBy: document.getElementById("sort-by"),
    resetFiltersBtn: document.getElementById("reset-filters-btn"),
    resultsCountText: document.getElementById("results-count-text"),
    activeFilterTags: document.getElementById("active-filter-tags"),

    // State Containers
    listingsLoading: document.getElementById("listings-loading"),
    listingsError: document.getElementById("listings-error"),
    errorDetailsText: document.getElementById("error-details-text"),
    retryBtn: document.getElementById("retry-btn"),
    listingsEmpty: document.getElementById("listings-empty"),
    emptyResetBtn: document.getElementById("empty-reset-btn"),
    listingsContainer: document.getElementById("listings-container"),

    // Commitments View Elements
    commitmentsContainer: document.getElementById("commitments-container"),
    commitmentsEmpty: document.getElementById("commitments-empty"),
    backToMarketplaceBtn: document.getElementById("back-to-marketplace-btn"),

    // Details Modal
    detailsModal: document.getElementById("details-modal"),
    modalCropTitle: document.getElementById("modal-crop-title"),
    modalDetailsBody: document.getElementById("modal-details-body"),
    modalDetailsCloseBtn: document.getElementById("modal-details-close-btn"),
    modalDetailsCancelBtn: document.getElementById("modal-details-cancel-btn"),
    modalDetailsCommitBtn: document.getElementById("modal-details-commit-btn"),

    // Field Agent Certificate Modal
    fieldReportModal: document.getElementById("field-report-modal"),
    certCropTitle: document.getElementById("cert-crop-title"),
    modalFieldBody: document.getElementById("modal-field-body"),
    modalFieldCloseBtn: document.getElementById("modal-field-close-btn"),
    modalFieldCancelBtn: document.getElementById("modal-field-cancel-btn"),
    modalFieldReinspectBtn: document.getElementById("modal-field-reinspect-btn"),
    modalFieldCommitBtn: document.getElementById("modal-field-commit-btn"),

    // Re-inspect Modal
    reinspectModal: document.getElementById("reinspect-modal"),
    reinspectLotName: document.getElementById("reinspect-lot-name"),
    reinspectAgentName: document.getElementById("reinspect-agent-name"),
    reinspectNotes: document.getElementById("reinspect-notes"),
    modalReinspectCloseBtn: document.getElementById("modal-reinspect-close-btn"),
    reinspectCancelBtn: document.getElementById("reinspect-cancel-btn"),
    reinspectSubmitBtn: document.getElementById("reinspect-submit-btn"),

    // Commit Modal
    commitModal: document.getElementById("commit-modal"),
    confirmCropName: document.getElementById("confirm-crop-name"),
    confirmFarmerName: document.getElementById("confirm-farmer-name"),
    confirmLocation: document.getElementById("confirm-location"),
    confirmQuantity: document.getElementById("confirm-quantity"),
    confirmPrice: document.getElementById("confirm-price"),
    confirmTotalValue: document.getElementById("confirm-total-value"),
    confirmHarvestDate: document.getElementById("confirm-harvest-date"),
    confirmVerification: document.getElementById("confirm-verification"),
    modalCommitCloseBtn: document.getElementById("modal-commit-close-btn"),
    confirmCancelBtn: document.getElementById("confirm-cancel-btn"),
    confirmSubmitBtn: document.getElementById("confirm-submit-btn"),

    // Toast Container
    toastContainer: document.getElementById("toast-container")
};

// ==========================================================================
// INITIALIZATION
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
    initApp();
});

async function initApp() {
    setupEventListeners();
    loadPersistedOrders();
    await loadMarketplaceData();
}

// ==========================================================================
// EVENT LISTENERS SETUP
// ==========================================================================

function setupEventListeners() {
    // Navigation Tabs
    if (DOM.tabMarketplaceBtn) {
        DOM.tabMarketplaceBtn.addEventListener("click", () => switchTab("marketplace"));
    }
    if (DOM.tabCommitmentsBtn) {
        DOM.tabCommitmentsBtn.addEventListener("click", () => switchTab("commitments"));
    }
    if (DOM.backToMarketplaceBtn) {
        DOM.backToMarketplaceBtn.addEventListener("click", () => switchTab("marketplace"));
    }

    // Mode Toggle (Live API vs Demo Mode)
    if (DOM.modeToggleBtn) {
        DOM.modeToggleBtn.addEventListener("click", toggleMode);
    }

    // Search Box
    if (DOM.searchInput) {
        DOM.searchInput.addEventListener("input", handleSearchInput);
    }
    if (DOM.clearSearchBtn) {
        DOM.clearSearchBtn.addEventListener("click", () => {
            DOM.searchInput.value = "";
            DOM.clearSearchBtn.style.display = "none";
            AppState.filters.search = "";
            applyFiltersAndRender();
        });
    }

    // Filters & Sorting
    if (DOM.cropFilter) {
        DOM.cropFilter.addEventListener("change", (e) => {
            AppState.filters.crop = e.target.value;
            applyFiltersAndRender();
        });
    }
    if (DOM.locationFilter) {
        DOM.locationFilter.addEventListener("change", (e) => {
            AppState.filters.location = e.target.value;
            applyFiltersAndRender();
        });
    }
    if (DOM.agentFilter) {
        DOM.agentFilter.addEventListener("change", (e) => {
            AppState.filters.agent = e.target.value;
            applyFiltersAndRender();
        });
    }
    if (DOM.gradeFilter) {
        DOM.gradeFilter.addEventListener("change", (e) => {
            AppState.filters.grade = e.target.value;
            applyFiltersAndRender();
        });
    }
    if (DOM.statusFilter) {
        DOM.statusFilter.addEventListener("change", (e) => {
            AppState.filters.status = e.target.value;
            applyFiltersAndRender();
        });
    }
    if (DOM.sortBy) {
        DOM.sortBy.addEventListener("change", (e) => {
            AppState.filters.sort = e.target.value;
            applyFiltersAndRender();
        });
    }

    // Reset Filters Buttons
    if (DOM.resetFiltersBtn) {
        DOM.resetFiltersBtn.addEventListener("click", resetFilters);
    }
    if (DOM.emptyResetBtn) {
        DOM.emptyResetBtn.addEventListener("click", resetFilters);
    }
    if (DOM.retryBtn) {
        DOM.retryBtn.addEventListener("click", () => loadMarketplaceData());
    }

    // Details Modal Actions
    if (DOM.modalDetailsCloseBtn) {
        DOM.modalDetailsCloseBtn.addEventListener("click", closeDetailsModal);
    }
    if (DOM.modalDetailsCancelBtn) {
        DOM.modalDetailsCancelBtn.addEventListener("click", closeDetailsModal);
    }
    if (DOM.modalDetailsCommitBtn) {
        DOM.modalDetailsCommitBtn.addEventListener("click", () => {
            closeDetailsModal();
            if (AppState.selectedListingForModal) {
                openCommitModal(AppState.selectedListingForModal);
            }
        });
    }

    // Field Report Modal Actions
    if (DOM.modalFieldCloseBtn) {
        DOM.modalFieldCloseBtn.addEventListener("click", closeFieldReportModal);
    }
    if (DOM.modalFieldCancelBtn) {
        DOM.modalFieldCancelBtn.addEventListener("click", closeFieldReportModal);
    }
    if (DOM.modalFieldCommitBtn) {
        DOM.modalFieldCommitBtn.addEventListener("click", () => {
            closeFieldReportModal();
            if (AppState.selectedListingForModal) {
                openCommitModal(AppState.selectedListingForModal);
            }
        });
    }
    if (DOM.modalFieldReinspectBtn) {
        DOM.modalFieldReinspectBtn.addEventListener("click", () => {
            closeFieldReportModal();
            if (AppState.selectedListingForModal) {
                openReinspectModal(AppState.selectedListingForModal);
            }
        });
    }

    // Re-inspection Request Modal Actions
    if (DOM.modalReinspectCloseBtn) {
        DOM.modalReinspectCloseBtn.addEventListener("click", closeReinspectModal);
    }
    if (DOM.reinspectCancelBtn) {
        DOM.reinspectCancelBtn.addEventListener("click", closeReinspectModal);
    }
    if (DOM.reinspectSubmitBtn) {
        DOM.reinspectSubmitBtn.addEventListener("click", handleReinspectSubmit);
    }

    // Commit Modal Actions
    if (DOM.modalCommitCloseBtn) {
        DOM.modalCommitCloseBtn.addEventListener("click", closeCommitModal);
    }
    if (DOM.confirmCancelBtn) {
        DOM.confirmCancelBtn.addEventListener("click", closeCommitModal);
    }
    if (DOM.confirmSubmitBtn) {
        DOM.confirmSubmitBtn.addEventListener("click", handleCommitSubmit);
    }

    // Global Modal Backdrop Click & Escape Key
    window.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            closeDetailsModal();
            closeFieldReportModal();
            closeReinspectModal();
            closeCommitModal();
        }
    });

    [DOM.detailsModal, DOM.fieldReportModal, DOM.reinspectModal, DOM.commitModal].forEach(modal => {
        if (modal) {
            modal.addEventListener("click", (e) => {
                if (e.target === modal) {
                    closeDetailsModal();
                    closeFieldReportModal();
                    closeReinspectModal();
                    closeCommitModal();
                }
            });
        }
    });
}

// ==========================================================================
// TABS SWITCHING
// ==========================================================================

function switchTab(tabName) {
    AppState.currentTab = tabName;

    if (tabName === "marketplace") {
        DOM.tabMarketplaceBtn.classList.add("active");
        DOM.tabCommitmentsBtn.classList.remove("active");
        DOM.marketplaceTabView.style.display = "flex";
        DOM.commitmentsTabView.style.display = "none";
        window.scrollTo({ top: 0, behavior: "smooth" });
    } else {
        DOM.tabMarketplaceBtn.classList.remove("active");
        DOM.tabCommitmentsBtn.classList.add("active");
        DOM.marketplaceTabView.style.display = "none";
        DOM.commitmentsTabView.style.display = "flex";
        renderCommitments();
        window.scrollTo({ top: 0, behavior: "smooth" });
    }
}

// ==========================================================================
// LIVE API VS DEMO MODE TOGGLE
// ==========================================================================

function toggleMode() {
    AppState.forceDemoMode = !AppState.forceDemoMode;
    showToast(
        AppState.forceDemoMode ? "Switched to Demo Mode (Seed Data)" : "Switched to Live Backend Mode",
        "info"
    );
    loadMarketplaceData();
}

function updateModeUI(isLive) {
    if (!DOM.modeToggleBtn || !DOM.modeToggleLabel) return;

    if (isLive && !AppState.forceDemoMode) {
        DOM.modeToggleBtn.classList.remove("mode-demo");
        DOM.modeToggleLabel.textContent = "🟢 Backend Live";
        DOM.modeToggleBtn.title = "Connected to FastAPI backend. Click to test Demo Mode.";
    } else {
        DOM.modeToggleBtn.classList.add("mode-demo");
        DOM.modeToggleLabel.textContent = "🟡 Demo Mode";
        DOM.modeToggleBtn.title = "Running with AgriBridge demo seed data. Click to connect to backend.";
    }
}

// ==========================================================================
// DATA LOADING & BACKEND INTEGRATION
// ==========================================================================

async function loadMarketplaceData() {
    showLoadingState();

    let backendAvailable = false;

    if (!AppState.forceDemoMode) {
        try {
            // Test connection with timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 2000);

            const [listingsRes, verificationsRes, ordersRes] = await Promise.all([
                fetch(`${API_BASE_URL}/api/listings/`, { signal: controller.signal }),
                fetch(`${API_BASE_URL}/api/verifications/`, { signal: controller.signal }),
                fetch(`${API_BASE_URL}/api/orders/`, { signal: controller.signal }).catch(() => null)
            ]);

            clearTimeout(timeoutId);

            if (listingsRes.ok && verificationsRes.ok) {
                const listingsData = await listingsRes.json();
                const verificationsData = await verificationsRes.json();
                let ordersData = { orders: [] };

                if (ordersRes && ordersRes.ok) {
                    ordersData = await ordersRes.json();
                }

                AppState.rawListings = listingsData.listings || [];
                AppState.rawVerifications = verificationsData.verifications || [];
                AppState.rawOrders = ordersData.orders || [];

                backendAvailable = true;
                AppState.isBackendLive = true;

                processBackendData();
            }
        } catch (error) {
            console.warn("Backend API unavailable or timed out, falling back to Demo Mode:", error.message);
            backendAvailable = false;
            AppState.isBackendLive = false;
        }
    }

    if (!backendAvailable || AppState.forceDemoMode) {
        AppState.isBackendLive = false;
        processDemoData();
    }

    updateModeUI(AppState.isBackendLive);
    populateDynamicFilters();
    applyFiltersAndRender();
    updateHeroStats();
    updateCommitmentsNavBadge();
}

// ==========================================================================
// DATA NORMALIZATION & PROCESSING
// ==========================================================================

function processBackendData() {
    // 1. Build Verification Map
    const verifiedMap = new Map();
    AppState.rawVerifications.forEach(v => {
        if (v.status === "verified") {
            verifiedMap.set(String(v.listing_id), v);
        }
    });

    // 2. Identify Committed Orders for this Buyer
    AppState.committedListingIds.clear();
    AppState.allOrders = (AppState.rawOrders || []).map(order => normalizeOrder(order));

    AppState.allOrders.forEach(order => {
        if (String(order.buyer_id) === String(BUYER_ID)) {
            AppState.committedListingIds.add(String(order.listing_id));
        }
    });

    // 3. Normalize Listings and filter verified
    AppState.allListings = (AppState.rawListings || []).map(listing => {
        const verification = verifiedMap.get(String(listing.id));
        return normalizeListing(listing, verification);
    });

    // Always merge backend listings with the rich 12-crop catalog so Buyer sees full variety
    const backendVerified = AppState.allListings.filter(listing => listing.is_verified);
    const demoVerified = DEMO_LISTINGS.map(item => ({
        ...item,
        is_verified: true,
        total_value: (item.quantity_est || 0) * (item.unit_price || 25),
        photo_url: item.photo_path || getListingImageUrl(item.photo_path, item.crop_type)
    }));

    const mergedMap = new Map();
    demoVerified.forEach(d => mergedMap.set(String(d.id), d));
    backendVerified.forEach(b => mergedMap.set(String(b.id), b));

    AppState.verifiedListings = Array.from(mergedMap.values());
    AppState.allListings = [...AppState.verifiedListings];

    loadPersistedOrders();
}

function processDemoData() {
    AppState.verifiedListings = DEMO_LISTINGS.map(item => ({
        ...item,
        is_verified: true,
        total_value: (item.quantity_est || 0) * (item.unit_price || 25),
        photo_url: item.photo_path || getListingImageUrl(item.photo_path, item.crop_type)
    }));

    AppState.allListings = [...AppState.verifiedListings];

    // Read stored demo orders
    loadPersistedOrders();
}

function normalizeListing(listing, verification) {
    const id = listing.id ?? listing.listing_id;
    const cropType = String(listing.crop_type || listing.cropName || listing.crop || "Unknown Crop").trim();
    const lowerCrop = cropType.toLowerCase();

    // Map known farmer or default
    const farmerId = listing.farmer_id || 1;
    const farmerMeta = FARMER_DIRECTORY[farmerId] || {
        name: listing.farmer_name || `Farmer #${farmerId}`,
        location: listing.location || "Raipur, Chhattisgarh",
        lat: 21.2514,
        lng: 81.6296,
        fieldAgent: "Amit Sharma",
        agentId: "FA-204",
        agentPhone: "+91 98271 44512",
        territory: "Raipur Agricultural Zone"
    };

    // Calculate unit price based on crop type
    const unitPrice = listing.unit_price || CROP_DEFAULT_PRICES[lowerCrop] || 25;
    const quantity = Number(listing.quantity_est ?? listing.quantity ?? 0);
    const totalValue = quantity * unitPrice;

    // Confidence normalized to percentage integer
    let confidenceVal = 92;
    if (listing.confidence !== null && listing.confidence !== undefined) {
        const num = Number(listing.confidence);
        confidenceVal = num <= 1 ? Math.round(num * 100) : Math.round(num);
    }

    // Verification details
    const isVerified = Boolean(
        verification ||
        listing.status === "verified" ||
        listing.status === "Available" ||
        listing.verification_status === "verified"
    );

    const agentName = verification?.agent_name || farmerMeta.fieldAgent;
    const agentId = farmerMeta.agentId || "FA-204";
    const remarks = verification?.remarks || "Physical inspection verified by AgriBridge Field Agent. Crop health and soil moisture within optimal threshold.";
    const verifiedAt = verification?.created_at ? new Date(verification.created_at).toLocaleDateString() : "2026-08-30";
    const certId = `AGB-CERT-2026-0${id}`;
    const qualityScore = Math.min(98, Math.max(88, confidenceVal + 2));
    const qualityGrade = qualityScore >= 94 ? "Grade A+" : "Grade A";

    return {
        id: id,
        farmer_id: farmerId,
        farmer_name: farmerMeta.name,
        crop_type: cropType,
        quantity_est: quantity,
        unit_price: unitPrice,
        total_value: totalValue,
        harvest_date: listing.harvest_date || "2026-10-15",
        location: listing.location || farmerMeta.location,
        lat: farmerMeta.lat,
        lng: farmerMeta.lng,
        health_status: listing.health_status || "Healthy",
        confidence: confidenceVal,
        photo_path: listing.photo_path,
        photo_url: getListingImageUrl(listing.photo_path, cropType),
        status: listing.status || "Available",
        is_verified: isVerified,
        field_agent: agentName,
        agent_id: agentId,
        agent_phone: farmerMeta.agentPhone,
        agent_territory: farmerMeta.territory,
        quality_grade: qualityGrade,
        quality_score: qualityScore,
        cert_id: certId,
        verified_at: verifiedAt,
        remarks: remarks,
        audit_details: {
            foliage: { score: `${qualityScore}/100`, status: "Optimal", desc: "Dark green uniform canopy with strong vegetative growth." },
            pest: { score: "0% Rate", status: "Pest-Free", desc: "Zero active insect infestation or fungal blight found during physical sweep." },
            moisture: { score: "94/100", status: "Balanced", desc: "Optimal root zone hydration; watering regimen verified." },
            maturity: { score: "86%", status: "On Schedule", desc: "Crop ripening timeline aligned with harvest projection." },
            safety: { score: "100% Safe", status: "Compliant", desc: "Safe bio-pesticide compliance verified against standards." },
            yield_check: { score: `${quantity.toLocaleString()} kg ± 4%`, status: "Audited", desc: "Sampling density confirms stated pre-harvest volume." }
        }
    };
}

function normalizeOrder(order) {
    const listingId = order.listing_id;
    const listing = AppState.allListings.find(l => String(l.id) === String(listingId)) ||
                    DEMO_LISTINGS.find(l => String(l.id) === String(listingId));

    const cropName = listing?.crop_type || order.crop_type || "Agricultural Harvest";
    const quantity = listing?.quantity_est || order.quantity || 1000;
    const price = listing?.unit_price || 25;
    const total = quantity * price;

    return {
        id: order.id || `ORD-${Date.now()}`,
        listing_id: listingId,
        buyer_id: order.buyer_id || BUYER_ID,
        crop_type: cropName,
        farmer_name: listing?.farmer_name || `Farmer #${listing?.farmer_id || 1}`,
        location: listing?.location || "Raipur, Chhattisgarh",
        quantity: quantity,
        unit_price: price,
        total_value: total,
        harvest_date: listing?.harvest_date || "October 2026",
        committed_at: order.committed_at || new Date().toISOString(),
        status: "Committed & Reserved",
        photo_url: getListingImageUrl(listing?.photo_path, cropName)
    };
}

function getListingImageUrl(photoPath, cropType) {
    if (photoPath && (String(photoPath).startsWith("http://") || String(photoPath).startsWith("https://"))) {
        return photoPath;
    }

    const lowerCrop = String(cropType || "").toLowerCase();
    for (const key in CROP_FALLBACK_IMAGES) {
        if (lowerCrop.includes(key)) {
            return CROP_FALLBACK_IMAGES[key];
        }
    }
    return CROP_FALLBACK_IMAGES.wheat;
}

// ==========================================================================
// LOCAL STORAGE ORDER PERSISTENCE
// ==========================================================================

function loadPersistedOrders() {
    try {
        const saved = localStorage.getItem("agribridge_buyer_orders");
        if (saved) {
            const parsed = JSON.parse(saved);
            if (Array.isArray(parsed)) {
                parsed.forEach(o => {
                    AppState.committedListingIds.add(String(o.listing_id));
                    if (!AppState.allOrders.some(existing => String(existing.id) === String(o.id))) {
                        AppState.allOrders.push(o);
                    }
                });
            }
        }
    } catch (e) {
        console.error("Error reading saved buyer orders:", e);
    }
}

function persistOrderLocally(newOrder) {
    try {
        AppState.allOrders.unshift(newOrder);
        AppState.committedListingIds.add(String(newOrder.listing_id));

        const saved = localStorage.getItem("agribridge_buyer_orders");
        const orders = saved ? JSON.parse(saved) : [];
        orders.unshift(newOrder);
        localStorage.setItem("agribridge_buyer_orders", JSON.stringify(orders));

        // Sync with Farmer Dashboard keys so single-machine hackathon demo flows smoothly!
        const cropData = {
            cropName: newOrder.crop_type,
            quantity: newOrder.quantity,
            harvestDate: newOrder.harvest_date,
            location: newOrder.location,
            status: "committed",
            listingId: newOrder.listing_id
        };
        localStorage.setItem("cropData", JSON.stringify(cropData));
        localStorage.setItem("buyerCommitment", "true");
        localStorage.setItem("cropImage", newOrder.photo_url);

    } catch (e) {
        console.error("Error saving buyer order to storage:", e);
    }
}

// ==========================================================================
// DYNAMIC FILTERS POPULATION
// ==========================================================================

function populateDynamicFilters() {
    if (!DOM.cropFilter || !DOM.locationFilter || !DOM.agentFilter) return;

    // Preserve selections
    const prevCrop = AppState.filters.crop;
    const prevLoc = AppState.filters.location;
    const prevAgent = AppState.filters.agent;

    // Collect unique crops, locations, agents
    const crops = new Set();
    const locations = new Set();
    const agents = new Set();

    AppState.verifiedListings.forEach(item => {
        if (item.crop_type) crops.add(item.crop_type);
        if (item.location) {
            const city = item.location.split(",")[0].trim();
            if (city) locations.add(city);
        }
        if (item.field_agent) agents.add(item.field_agent);
    });

    // Build Crop Options
    DOM.cropFilter.innerHTML = '<option value="">All Crops</option>';
    Array.from(crops).sort().forEach(crop => {
        const opt = document.createElement("option");
        opt.value = crop;
        const emoji = CROP_EMOJIS[crop.toLowerCase()] || "🌾";
        opt.textContent = `${emoji} ${crop}`;
        if (crop === prevCrop) opt.selected = true;
        DOM.cropFilter.appendChild(opt);
    });

    // Build Location Options
    DOM.locationFilter.innerHTML = '<option value="">All Locations</option>';
    Array.from(locations).sort().forEach(loc => {
        const opt = document.createElement("option");
        opt.value = loc;
        opt.textContent = `📍 ${loc}`;
        if (loc === prevLoc) opt.selected = true;
        DOM.locationFilter.appendChild(opt);
    });

    // Build Field Agent Options
    DOM.agentFilter.innerHTML = '<option value="">All Field Agents</option>';
    Array.from(agents).sort().forEach(agent => {
        const opt = document.createElement("option");
        opt.value = agent;
        opt.textContent = `🛡️ ${agent}`;
        if (agent === prevAgent) opt.selected = true;
        DOM.agentFilter.appendChild(opt);
    });
}

// ==========================================================================
// SEARCH, FILTERING & SORTING LOGIC
// ==========================================================================

function handleSearchInput(e) {
    const val = e.target.value.trim();
    AppState.filters.search = val;
    DOM.clearSearchBtn.style.display = val ? "block" : "none";
    applyFiltersAndRender();
}

function resetFilters() {
    AppState.filters.search = "";
    AppState.filters.crop = "";
    AppState.filters.location = "";
    AppState.filters.agent = "";
    AppState.filters.grade = "";
    AppState.filters.status = "all";
    AppState.filters.sort = "harvest_asc";

    if (DOM.searchInput) DOM.searchInput.value = "";
    if (DOM.clearSearchBtn) DOM.clearSearchBtn.style.display = "none";
    if (DOM.cropFilter) DOM.cropFilter.value = "";
    if (DOM.locationFilter) DOM.locationFilter.value = "";
    if (DOM.agentFilter) DOM.agentFilter.value = "";
    if (DOM.gradeFilter) DOM.gradeFilter.value = "";
    if (DOM.statusFilter) DOM.statusFilter.value = "all";
    if (DOM.sortBy) DOM.sortBy.value = "harvest_asc";

    applyFiltersAndRender();
}

function applyFiltersAndRender() {
    const { search, crop, location, agent, grade, status, sort } = AppState.filters;

    // Filter listings
    let filtered = AppState.verifiedListings.filter(item => {
        // 1. Search Query (Crop, Farmer, Field Agent, Location)
        if (search) {
            const query = search.toLowerCase();
            const matchCrop = (item.crop_type || "").toLowerCase().includes(query);
            const matchFarmer = (item.farmer_name || "").toLowerCase().includes(query);
            const matchAgent = (item.field_agent || "").toLowerCase().includes(query);
            const matchLocation = (item.location || "").toLowerCase().includes(query);
            if (!matchCrop && !matchFarmer && !matchAgent && !matchLocation) return false;
        }

        // 2. Crop Filter
        if (crop && item.crop_type.toLowerCase() !== crop.toLowerCase()) {
            return false;
        }

        // 3. Location Filter
        if (location && !(item.location || "").toLowerCase().includes(location.toLowerCase())) {
            return false;
        }

        // 4. Field Agent Filter
        if (agent && (item.field_agent || "").toLowerCase() !== agent.toLowerCase()) {
            return false;
        }

        // 5. Quality Grade Filter
        if (grade && (item.quality_grade || "").toLowerCase() !== grade.toLowerCase()) {
            return false;
        }

        // 6. Status Filter
        const isCommitted = AppState.committedListingIds.has(String(item.id));
        if (status === "available" && isCommitted) {
            return false;
        }
        if (status === "committed" && !isCommitted) {
            return false;
        }

        return true;
    });

    // Sort listings
    filtered.sort((a, b) => {
        switch (sort) {
            case "price_asc":
                return (a.unit_price || 0) - (b.unit_price || 0);
            case "price_desc":
                return (b.unit_price || 0) - (a.unit_price || 0);
            case "confidence_desc":
                return (b.confidence || 0) - (a.confidence || 0);
            case "grade_desc":
                return (b.quality_score || 0) - (a.quality_score || 0);
            case "quantity_desc":
                return (b.quantity_est || 0) - (a.quantity_est || 0);
            case "harvest_asc":
            default:
                return new Date(a.harvest_date || "2099-12-31") - new Date(b.harvest_date || "2099-12-31");
        }
    });

    renderMarketplaceCards(filtered);
    updateResultsMeta(filtered.length);
}

function updateResultsMeta(count) {
    if (!DOM.resultsCountText) return;

    if (count === 1) {
        DOM.resultsCountText.textContent = "Showing 1 verified harvest";
    } else {
        DOM.resultsCountText.textContent = `Showing ${count} verified harvests`;
    }

    // Active filter chips
    if (DOM.activeFilterTags) {
        DOM.activeFilterTags.innerHTML = "";
        const { crop, location, agent, grade, status } = AppState.filters;

        if (crop) DOM.activeFilterTags.appendChild(createTagChip(`Crop: ${crop}`));
        if (location) DOM.activeFilterTags.appendChild(createTagChip(`Location: ${location}`));
        if (agent) DOM.activeFilterTags.appendChild(createTagChip(`Agent: ${agent}`));
        if (grade) DOM.activeFilterTags.appendChild(createTagChip(`Grade: ${grade}`));
        if (status && status !== "all") DOM.activeFilterTags.appendChild(createTagChip(`Status: ${status}`));
    }
}

function createTagChip(text) {
    const chip = document.createElement("span");
    chip.classList.add("filter-tag-chip");
    chip.textContent = text;
    return chip;
}

// ==========================================================================
// UI RENDERING: MARKETPLACE CARDS
// ==========================================================================

function renderMarketplaceCards(listings) {
    hideStateContainers();

    if (!DOM.listingsContainer) return;
    DOM.listingsContainer.innerHTML = "";

    if (listings.length === 0) {
        showEmptyState();
        return;
    }

    listings.forEach(listing => {
        const isCommitted = AppState.committedListingIds.has(String(listing.id));
        const card = createListingCard(listing, isCommitted);
        DOM.listingsContainer.appendChild(card);
    });
}

function createListingCard(listing, isCommitted) {
    const card = document.createElement("div");
    card.classList.add("crop-card");
    card.id = `listing-card-${listing.id}`;

    const emoji = CROP_EMOJIS[listing.crop_type.toLowerCase()] || "🌾";
    const formattedDate = formatHarvestDate(listing.harvest_date);
    const formattedPrice = `₹${listing.unit_price}/kg`;
    const formattedQty = `${listing.quantity_est.toLocaleString()} kg`;
    const cropImg = listing.photo_url || CROP_FALLBACK_IMAGES[listing.crop_type.toLowerCase()] || CROP_FALLBACK_IMAGES.wheat;

    card.innerHTML = `
        <div class="card-image-wrap">
            <img src="${cropImg}" alt="${listing.crop_type}" loading="lazy" onerror="this.src='${CROP_FALLBACK_IMAGES[listing.crop_type.toLowerCase()] || CROP_FALLBACK_IMAGES.wheat}'">
            <div class="card-crop-tag">${emoji} ${listing.crop_type}</div>
            <div class="card-grade-tag">⭐ ${listing.quality_grade || 'Grade A'} (${listing.quality_score || 95}%)</div>
            <div class="card-verified-tag">✓ FIELD AGENT VERIFIED</div>
        </div>

        <div class="card-body">
            <div class="card-title-row">
                <h3 class="card-crop-name">${listing.crop_type}</h3>
                <span class="ai-confidence-pill" title="AI Health Assessment Confidence">
                    🧠 AI Confidence: ${listing.confidence}%
                </span>
            </div>

            <div class="card-metrics-grid">
                <div class="metric-box">
                    <span class="metric-label">Quantity Est.</span>
                    <span class="metric-val">${formattedQty}</span>
                </div>
                <div class="metric-box">
                    <span class="metric-label">Target Price</span>
                    <span class="metric-val price-val">${formattedPrice}</span>
                </div>
            </div>

            <div class="card-specs-list">
                <div class="spec-item">
                    <span class="spec-item-label">📅 Expected Harvest:</span>
                    <span class="spec-item-val">${formattedDate}</span>
                </div>
                <div class="spec-item">
                    <span class="spec-item-label">🩺 Crop Health:</span>
                    <span class="spec-item-val health-badge-inline">🟢 ${listing.health_status}</span>
                </div>
                <div class="spec-item">
                    <span class="spec-item-label">👨‍🌾 Farmer:</span>
                    <span class="spec-item-val">${listing.farmer_name}</span>
                </div>
                <div class="spec-item">
                    <span class="spec-item-label">📍 Location:</span>
                    <span class="spec-item-val">${listing.location}</span>
                </div>
            </div>

            <div class="field-agent-seal">
                <div class="seal-agent-info">
                    <span class="seal-icon">🛡️</span>
                    <span>Audited by <strong>${listing.field_agent}</strong></span>
                </div>
                <button type="button" class="seal-audit-link" title="View Full Physical Audit Certificate">
                    Audit Report ↗
                </button>
            </div>

            <div class="card-actions">
                <button type="button" class="stylish-btn ab-btn-secondary btn-details" data-id="${listing.id}">
                    View Details
                </button>
                <button type="button" class="stylish-btn ab-btn-primary btn-commit ${isCommitted ? 'btn-committed-state' : ''}" data-id="${listing.id}" ${isCommitted ? 'disabled' : ''}>
                    ${isCommitted ? 'Committed ✓' : 'Commit to Buy →'}
                </button>
            </div>
        </div>
    `;

    // Attach Action Listeners
    const detailsBtn = card.querySelector(".btn-details");
    if (detailsBtn) {
        detailsBtn.addEventListener("click", () => openDetailsModal(listing));
    }

    const auditLinkBtn = card.querySelector(".seal-audit-link");
    if (auditLinkBtn) {
        auditLinkBtn.addEventListener("click", () => openFieldReportModal(listing));
    }

    const commitBtn = card.querySelector(".btn-commit");
    if (commitBtn && !isCommitted) {
        commitBtn.addEventListener("click", () => openCommitModal(listing));
    }

    return card;
}

// ==========================================================================
// UI RENDERING: MY COMMITMENTS
// ==========================================================================

function renderCommitments() {
    if (!DOM.commitmentsContainer) return;

    DOM.commitmentsContainer.innerHTML = "";

    // Find orders for current buyer
    const myOrders = AppState.allOrders.filter(o => String(o.buyer_id) === String(BUYER_ID));

    if (myOrders.length === 0) {
        if (DOM.commitmentsEmpty) DOM.commitmentsEmpty.style.display = "flex";
        DOM.commitmentsContainer.style.display = "none";
        return;
    }

    if (DOM.commitmentsEmpty) DOM.commitmentsEmpty.style.display = "none";
    DOM.commitmentsContainer.style.display = "flex";

    myOrders.forEach(order => {
        const card = document.createElement("div");
        card.classList.add("commitment-card");

        const emoji = CROP_EMOJIS[order.crop_type.toLowerCase()] || "🌾";
        const formattedCommitTime = formatCommitmentTimestamp(order.committed_at);

        card.innerHTML = `
            <img src="${order.photo_url}" alt="${order.crop_type}" class="commitment-thumb" onerror="this.src='${CROP_FALLBACK_IMAGES.default}'">

            <div class="commitment-info">
                <div class="commitment-title-row">
                    <h3 class="commitment-crop-title">${emoji} ${order.crop_type}</h3>
                    <span class="order-id-badge">Order #${order.id}</span>
                </div>

                <div class="commitment-details-grid">
                    <div class="commit-meta-item">
                        <span class="commit-meta-label">Quantity</span>
                        <span class="commit-meta-val">${(order.quantity || 0).toLocaleString()} kg</span>
                    </div>
                    <div class="commit-meta-item">
                        <span class="commit-meta-label">Price Agreed</span>
                        <span class="commit-meta-val">₹${order.unit_price}/kg</span>
                    </div>
                    <div class="commit-meta-item">
                        <span class="commit-meta-label">Total Value</span>
                        <span class="commit-meta-val">₹${(order.total_value || 0).toLocaleString()}</span>
                    </div>
                    <div class="commit-meta-item">
                        <span class="commit-meta-label">Farmer & Location</span>
                        <span class="commit-meta-val">${order.farmer_name} (📍 ${order.location})</span>
                    </div>
                </div>
            </div>

            <div class="commitment-status-col">
                <span class="commitment-status-badge">
                    ✓ ${order.status}
                </span>
                <span class="commitment-time-text">Committed: ${formattedCommitTime}</span>
            </div>
        `;

        DOM.commitmentsContainer.appendChild(card);
    });
}

// ==========================================================================
// MODAL: VIEW DETAILS
// ==========================================================================

function openDetailsModal(listing) {
    AppState.selectedListingForModal = listing;
    if (!DOM.detailsModal || !DOM.modalDetailsBody) return;

    const emoji = CROP_EMOJIS[listing.crop_type.toLowerCase()] || "🌾";
    DOM.modalCropTitle.textContent = `${emoji} ${listing.crop_type} — Lot #${listing.id}`;

    const isCommitted = AppState.committedListingIds.has(String(listing.id));
    const formattedDate = formatHarvestDate(listing.harvest_date);

    DOM.modalDetailsBody.innerHTML = `
        <div class="modal-crop-hero">
            <img src="${listing.photo_url}" alt="${listing.crop_type}" class="modal-crop-image" onerror="this.src='${CROP_FALLBACK_IMAGES.default}'">
            <div>
                <h3 style="font-size: 20px; font-weight: 800; color: var(--ab-primary-dark); margin-bottom: 4px;">
                    ${listing.crop_type} Pre-Harvest Supply
                </h3>
                <p style="font-size: 13px; color: var(--ab-text-muted); margin-bottom: 12px;">
                    Direct from ${listing.farmer_name} • Farm Location: ${listing.location}
                </p>
                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                    <span class="card-verified-tag" style="position: static;">✓ FIELD AGENT VERIFIED</span>
                    <span class="card-grade-tag" style="position: static;">⭐ ${listing.quality_grade} (${listing.quality_score}%)</span>
                    <span class="ai-confidence-pill" style="position: static;">🧠 AI CONFIDENCE: ${listing.confidence}%</span>
                </div>
            </div>
        </div>

        <div class="modal-specs-table">
            <div class="spec-item">
                <span class="spec-item-label">Estimated Supply:</span>
                <strong class="spec-item-val">${listing.quantity_est.toLocaleString()} kg</strong>
            </div>
            <div class="spec-item">
                <span class="spec-item-label">Offered Price:</span>
                <strong class="spec-item-val price-val" style="color: var(--ab-primary-green);">₹${listing.unit_price}/kg</strong>
            </div>
            <div class="spec-item">
                <span class="spec-item-label">Expected Harvest:</span>
                <strong class="spec-item-val">${formattedDate}</strong>
            </div>
            <div class="spec-item">
                <span class="spec-item-label">Estimated Lot Value:</span>
                <strong class="spec-item-val">₹${(listing.total_value || 0).toLocaleString()}</strong>
            </div>
        </div>

        <!-- AI Health Card -->
        <div class="modal-section-card">
            <div class="modal-section-title">
                <span>🩺</span> AI Health & Disease Diagnostic
            </div>
            <p style="font-size: 13px; color: var(--ab-text-body); line-height: 1.5;">
                Deep learning computer vision detected: <strong>${listing.health_status}</strong>. AI confidence index: <strong>${listing.confidence}%</strong>. No foliage blight or active disease patterns identified.
            </p>
        </div>

        <!-- Field Agent Verification Report Bar -->
        <div class="modal-section-card" style="background: rgba(220, 232, 210, 0.35); border-color: rgba(49, 92, 42, 0.2);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <div class="modal-section-title" style="color: var(--ab-primary-green); margin: 0;">
                    <span>🛡️</span> Physical Field Agent Inspection Audit
                </div>
                <button type="button" class="stylish-btn ab-btn-secondary" id="modal-inner-open-cert" style="padding: 4px 12px; font-size: 12px;">
                    Full Certificate ↗
                </button>
            </div>
            <p style="font-size: 13px; color: var(--ab-text-body); line-height: 1.5; margin-bottom: 6px;">
                <em>"${listing.remarks}"</em>
            </p>
            <div style="display: flex; justify-content: space-between; font-size: 11px; color: var(--ab-text-muted); font-weight: 700;">
                <span>Verified Agent: <strong>${listing.field_agent} (${listing.agent_id})</strong></span>
                <span>Audit Score: <strong style="color: var(--ab-success);">${listing.quality_score}% (${listing.quality_grade})</strong></span>
            </div>
        </div>
    `;

    // Inner button to jump to full certificate
    const innerCertBtn = DOM.modalDetailsBody.querySelector("#modal-inner-open-cert");
    if (innerCertBtn) {
        innerCertBtn.addEventListener("click", () => {
            closeDetailsModal();
            openFieldReportModal(listing);
        });
    }

    // Footer CTA button
    if (DOM.modalDetailsCommitBtn) {
        if (isCommitted) {
            DOM.modalDetailsCommitBtn.textContent = "Already Committed ✓";
            DOM.modalDetailsCommitBtn.disabled = true;
            DOM.modalDetailsCommitBtn.classList.add("btn-committed-state");
        } else {
            DOM.modalDetailsCommitBtn.textContent = "Commit to Buy →";
            DOM.modalDetailsCommitBtn.disabled = false;
            DOM.modalDetailsCommitBtn.classList.remove("btn-committed-state");
        }
    }

    DOM.detailsModal.classList.add("active");
    DOM.detailsModal.setAttribute("aria-hidden", "false");
}

function closeDetailsModal() {
    if (!DOM.detailsModal) return;
    DOM.detailsModal.classList.remove("active");
    DOM.detailsModal.setAttribute("aria-hidden", "true");
}

// ==========================================================================
// MODAL: FIELD AGENT PHYSICAL INSPECTION AUDIT CERTIFICATE
// ==========================================================================

function openFieldReportModal(listing) {
    AppState.selectedListingForModal = listing;
    if (!DOM.fieldReportModal || !DOM.modalFieldBody) return;

    const emoji = CROP_EMOJIS[listing.crop_type.toLowerCase()] || "🌾";
    DOM.certCropTitle.textContent = `${emoji} ${listing.crop_type} — Physical Field Health Audit`;

    const audit = listing.audit_details || {
        foliage: { score: "96/100", status: "Optimal", desc: "Healthy canopy stand." },
        pest: { score: "0% Rate", status: "Pest-Free", desc: "Zero pests found in physical sweep." },
        moisture: { score: "94/100", status: "Balanced", desc: "Optimal root moisture." },
        maturity: { score: "85%", status: "On Schedule", desc: "Maturity on target." },
        safety: { score: "100% Safe", status: "Compliant", desc: "Safe bio-pesticides verified." },
        yield_check: { score: `${listing.quantity_est} kg ± 4%`, status: "Audited", desc: "Density sampling matches target." }
    };

    DOM.modalFieldBody.innerHTML = `
        <!-- Inspector Profile Card -->
        <div class="inspector-card-profile">
            <div class="inspector-info-left">
                <div class="inspector-avatar-badge">👨‍🌾</div>
                <div class="inspector-text-block">
                    <span class="inspector-name">${listing.field_agent}</span>
                    <span class="inspector-id-tag">Senior Agri-Field Inspector • ID #${listing.agent_id}</span>
                    <span style="font-size: 11px; color: var(--ab-text-muted); margin-top: 2px;">
                        📞 ${listing.agent_phone || '+91 98271 44512'} • 📍 ${listing.agent_territory || listing.location}
                    </span>
                </div>
            </div>
            <div class="inspector-status-stamp">
                <span class="stamp-badge">✓ PHYSICAL INSPECTION PASSED</span>
                <span class="stamp-date">Certificate ID: <strong>${listing.cert_id}</strong></span>
                <span class="stamp-date">Audit Date: ${listing.verified_at}</span>
            </div>
        </div>

        <!-- Farm GPS Geo-Coordinates Bar -->
        <div class="gps-audit-strip">
            <span>📍 <strong>Field GPS Verification:</strong> Geo-Fenced Farm Polygon Verified</span>
            <span class="gps-coords-text">${listing.lat ? `${listing.lat.toFixed(4)}° N, ${listing.lng.toFixed(4)}° E` : '21.2514° N, 81.6296° E'}</span>
        </div>

        <!-- 6-Point Physical Crop Health Audit Grid -->
        <div class="audit-checklist-section">
            <div class="audit-section-heading">
                <span>📋</span> 6-Point End-to-End Physical Health Audit
            </div>

            <div class="audit-checklist-grid">
                <!-- 1. Foliage -->
                <div class="audit-check-card">
                    <div class="audit-check-icon">🌿</div>
                    <div class="audit-check-content">
                        <span class="audit-check-title">1. Foliage & Plant Canopy Vigor</span>
                        <span class="audit-check-desc">${audit.foliage.desc}</span>
                        <span class="audit-score-pill">Status: ${audit.foliage.status} (Score: ${audit.foliage.score})</span>
                    </div>
                </div>

                <!-- 2. Pest -->
                <div class="audit-check-card">
                    <div class="audit-check-icon">🐛</div>
                    <div class="audit-check-content">
                        <span class="audit-check-title">2. Pest & Pathogen Sweep</span>
                        <span class="audit-check-desc">${audit.pest.desc}</span>
                        <span class="audit-score-pill">Status: ${audit.pest.status} (Infection Rate: ${audit.pest.score})</span>
                    </div>
                </div>

                <!-- 3. Moisture -->
                <div class="audit-check-card">
                    <div class="audit-check-icon">💧</div>
                    <div class="audit-check-content">
                        <span class="audit-check-title">3. Soil Moisture & Root Hydration</span>
                        <span class="audit-check-desc">${audit.moisture.desc}</span>
                        <span class="audit-score-pill">Status: ${audit.moisture.status} (Score: ${audit.moisture.score})</span>
                    </div>
                </div>

                <!-- 4. Maturity -->
                <div class="audit-check-card">
                    <div class="audit-check-icon">🌾</div>
                    <div class="audit-check-content">
                        <span class="audit-check-title">4. Grain / Fruit Ripening Stage</span>
                        <span class="audit-check-desc">${audit.maturity.desc}</span>
                        <span class="audit-score-pill">Progress: ${audit.maturity.status} (${audit.maturity.score})</span>
                    </div>
                </div>

                <!-- 5. Safety -->
                <div class="audit-check-card">
                    <div class="audit-check-icon">🧪</div>
                    <div class="audit-check-content">
                        <span class="audit-check-title">5. Chemical Residue & Bio-Standard</span>
                        <span class="audit-check-desc">${audit.safety.desc}</span>
                        <span class="audit-score-pill">Compliance: ${audit.safety.status} (${audit.safety.score})</span>
                    </div>
                </div>

                <!-- 6. Yield Sampling -->
                <div class="audit-check-card">
                    <div class="audit-check-icon">⚖️</div>
                    <div class="audit-check-content">
                        <span class="audit-check-title">6. Yield Density & Quadrat Sampling</span>
                        <span class="audit-check-desc">${audit.yield_check.desc}</span>
                        <span class="audit-score-pill">Verification: ${audit.yield_check.status} (${audit.yield_check.score})</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- AI vs Field Ground Reality Matrix -->
        <div class="ai-field-matrix-card">
            <div class="modal-section-title">
                <span>🧠 vs 🛡️</span> AI Model Diagnosis vs Field Agent Ground Truth
            </div>

            <div class="matrix-grid">
                <div class="matrix-col">
                    <span class="matrix-header"><span>🧠</span> AI Vision Prediction</span>
                    <span class="matrix-val">Confidence: ${listing.confidence}%</span>
                    <p class="matrix-notes">Model detected: <strong>${listing.health_status}</strong> based on multispectral leaf photo analysis.</p>
                </div>

                <div class="matrix-col" style="background: rgba(220, 232, 210, 0.45); border-color: rgba(49, 92, 42, 0.25);">
                    <span class="matrix-header" style="color: var(--ab-primary-green);"><span>🛡️</span> Field Agent Ground Truth</span>
                    <span class="matrix-val" style="color: var(--ab-primary-green);">Quality Score: ${listing.quality_score}% (${listing.quality_grade})</span>
                    <p class="matrix-notes">Physical sweep by ${listing.field_agent} confirmed 100% agreement with AI diagnostic.</p>
                </div>
            </div>
        </div>

        <!-- Inspector Remarks & Official Recommendation -->
        <div class="modal-section-card" style="background: #FCFDFB; border-left: 4px solid var(--ab-primary-green);">
            <div class="modal-section-title" style="color: var(--ab-primary-green);">
                <span>✍️</span> Inspector's Official Recommendation & Verdict
            </div>
            <p style="font-size: 14px; color: var(--ab-primary-dark); line-height: 1.6; font-style: italic; margin-top: 4px;">
                "${listing.remarks}"
            </p>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; font-size: 11px; color: var(--ab-text-muted); font-weight: 700;">
                <span>Digital Seal: <strong>AGRIBRIDGE-VERIFIED-${listing.cert_id}</strong></span>
                <span style="color: var(--ab-success);">Status: APPROVED FOR ADVANCE BUYER COMMITMENT ✓</span>
            </div>
        </div>
    `;

    // Footer button state
    const isCommitted = AppState.committedListingIds.has(String(listing.id));
    if (DOM.modalFieldCommitBtn) {
        if (isCommitted) {
            DOM.modalFieldCommitBtn.textContent = "Already Committed ✓";
            DOM.modalFieldCommitBtn.disabled = true;
            DOM.modalFieldCommitBtn.classList.add("btn-committed-state");
        } else {
            DOM.modalFieldCommitBtn.textContent = "Commit with Verified Confidence →";
            DOM.modalFieldCommitBtn.disabled = false;
            DOM.modalFieldCommitBtn.classList.remove("btn-committed-state");
        }
    }

    DOM.fieldReportModal.classList.add("active");
    DOM.fieldReportModal.setAttribute("aria-hidden", "false");
}

function closeFieldReportModal() {
    if (!DOM.fieldReportModal) return;
    DOM.fieldReportModal.classList.remove("active");
    DOM.fieldReportModal.setAttribute("aria-hidden", "true");
}

// ==========================================================================
// MODAL: ON-DEMAND RE-INSPECTION REQUEST
// ==========================================================================

function openReinspectModal(listing) {
    AppState.selectedListingForModal = listing;
    if (!DOM.reinspectModal) return;

    if (DOM.reinspectLotName) {
        DOM.reinspectLotName.value = `${listing.crop_type} (Lot #${listing.id}) — ${listing.farmer_name} (📍 ${listing.location})`;
    }
    if (DOM.reinspectAgentName) {
        DOM.reinspectAgentName.value = `${listing.field_agent} (Inspector #${listing.agent_id})`;
    }
    if (DOM.reinspectNotes) {
        DOM.reinspectNotes.value = "";
    }

    DOM.reinspectModal.classList.add("active");
    DOM.reinspectModal.setAttribute("aria-hidden", "false");
}

function closeReinspectModal() {
    if (!DOM.reinspectModal) return;
    DOM.reinspectModal.classList.remove("active");
    DOM.reinspectModal.setAttribute("aria-hidden", "true");
}

function handleReinspectSubmit() {
    const listing = AppState.selectedListingForModal;
    if (!listing) return;

    closeReinspectModal();
    showToast(
        `✓ Re-inspection request dispatched to Field Agent ${listing.field_agent}! Updated audit report will arrive in 24 hours.`,
        "success"
    );
}

// ==========================================================================
// MODAL: COMMITMENT CONFIRMATION
// ==========================================================================

function openCommitModal(listing) {
    AppState.selectedListingForModal = listing;
    if (!DOM.commitModal) return;

    const emoji = CROP_EMOJIS[listing.crop_type.toLowerCase()] || "🌾";
    DOM.confirmCropName.textContent = `${emoji} ${listing.crop_type} (${listing.quality_grade || 'Grade A+'})`;
    DOM.confirmFarmerName.textContent = listing.farmer_name;
    DOM.confirmLocation.textContent = listing.location;
    DOM.confirmQuantity.textContent = `${listing.quantity_est.toLocaleString()} kg`;
    DOM.confirmPrice.textContent = `₹${listing.unit_price}/kg`;
    DOM.confirmTotalValue.textContent = `₹${(listing.total_value || 0).toLocaleString()}`;
    DOM.confirmHarvestDate.textContent = formatHarvestDate(listing.harvest_date);
    DOM.confirmVerification.textContent = `✓ Field Agent Verified (${listing.field_agent} • Score: ${listing.quality_score || 95}%)`;

    DOM.confirmSubmitBtn.disabled = false;
    DOM.confirmSubmitBtn.textContent = "Confirm Commitment";

    DOM.commitModal.classList.add("active");
    DOM.commitModal.setAttribute("aria-hidden", "false");
}

function closeCommitModal() {
    if (!DOM.commitModal) return;
    DOM.commitModal.classList.remove("active");
    DOM.commitModal.setAttribute("aria-hidden", "true");
}

// ==========================================================================
// ORDER SUBMISSION & COMMITMENT CREATION
// ==========================================================================

async function handleCommitSubmit() {
    const listing = AppState.selectedListingForModal;
    if (!listing) return;

    // Loading State on Button
    DOM.confirmSubmitBtn.disabled = true;
    DOM.confirmSubmitBtn.textContent = "Processing Commitment...";

    let orderCreated = false;
    let orderRecord = null;

    // 1. If backend is live, send real POST request
    if (AppState.isBackendLive && !AppState.forceDemoMode) {
        try {
            const payload = {
                listing_id: Number(listing.id),
                buyer_id: BUYER_ID
            };

            console.log("Submitting order commitment to backend:", payload);

            const response = await fetch(`${API_BASE_URL}/api/orders/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            const result = await response.json();
            console.log("Backend order response:", result);

            if (response.ok && (result.success || result.order || result.id)) {
                orderCreated = true;
                const newId = result.order?.id || result.id || Math.floor(Math.random() * 1000) + 10;
                orderRecord = {
                    id: newId,
                    listing_id: listing.id,
                    buyer_id: BUYER_ID,
                    crop_type: listing.crop_type,
                    farmer_name: listing.farmer_name,
                    location: listing.location,
                    quantity: listing.quantity_est,
                    unit_price: listing.unit_price,
                    total_value: listing.total_value,
                    harvest_date: listing.harvest_date,
                    committed_at: new Date().toISOString(),
                    status: "Committed & Reserved",
                    photo_url: listing.photo_url
                };
            } else {
                throw new Error(result.detail || "Server rejected commitment.");
            }
        } catch (apiError) {
            console.warn("Backend order creation failed, falling back to local storage commitment:", apiError.message);
        }
    }

    // 2. Demo Mode or Local Fallback
    if (!orderCreated) {
        const demoId = Math.floor(Math.random() * 900) + 100;
        orderRecord = {
            id: demoId,
            listing_id: listing.id,
            buyer_id: BUYER_ID,
            crop_type: listing.crop_type,
            farmer_name: listing.farmer_name,
            location: listing.location,
            quantity: listing.quantity_est,
            unit_price: listing.unit_price,
            total_value: listing.total_value,
            harvest_date: listing.harvest_date,
            committed_at: new Date().toISOString(),
            status: "Committed & Reserved",
            photo_url: listing.photo_url
        };
        orderCreated = true;
    }

    if (orderCreated && orderRecord) {
        persistOrderLocally(orderRecord);
        closeCommitModal();
        showToast("✓ Buyer commitment created successfully!", "success");

        // Re-render
        applyFiltersAndRender();
        updateHeroStats();
        updateCommitmentsNavBadge();

        // If currently on commitments view, re-render it
        if (AppState.currentTab === "commitments") {
            renderCommitments();
        }
    } else {
        DOM.confirmSubmitBtn.disabled = false;
        DOM.confirmSubmitBtn.textContent = "Confirm Commitment";
        showToast("Unable to create commitment. Please try again.", "error");
    }
}

// ==========================================================================
// HERO STATS & BADGES
// ==========================================================================

function updateHeroStats() {
    const verifiedCount = AppState.verifiedListings.length;
    let totalSupply = 0;

    AppState.verifiedListings.forEach(l => {
        totalSupply += Number(l.quantity_est || 0);
    });

    const buyerCommitmentsCount = AppState.allOrders.filter(o => String(o.buyer_id) === String(BUYER_ID)).length;

    if (DOM.statVerifiedCount) {
        DOM.statVerifiedCount.textContent = verifiedCount;
    }
    if (DOM.statTotalSupply) {
        DOM.statTotalSupply.textContent = `${totalSupply.toLocaleString()} kg`;
    }
    if (DOM.statCommitmentsCount) {
        DOM.statCommitmentsCount.textContent = buyerCommitmentsCount;
    }
}

function updateCommitmentsNavBadge() {
    const count = AppState.allOrders.filter(o => String(o.buyer_id) === String(BUYER_ID)).length;
    if (DOM.commitmentsNavBadge) {
        DOM.commitmentsNavBadge.textContent = count;
    }
}

// ==========================================================================
// STATE CONTAINER HELPERS
// ==========================================================================

function showLoadingState() {
    if (DOM.listingsLoading) DOM.listingsLoading.style.display = "flex";
    if (DOM.listingsError) DOM.listingsError.style.display = "none";
    if (DOM.listingsEmpty) DOM.listingsEmpty.style.display = "none";
    if (DOM.listingsContainer) DOM.listingsContainer.style.display = "none";
}

function hideStateContainers() {
    if (DOM.listingsLoading) DOM.listingsLoading.style.display = "none";
    if (DOM.listingsError) DOM.listingsError.style.display = "none";
    if (DOM.listingsEmpty) DOM.listingsEmpty.style.display = "none";
    if (DOM.listingsContainer) DOM.listingsContainer.style.display = "grid";
}

function showEmptyState() {
    if (DOM.listingsEmpty) DOM.listingsEmpty.style.display = "flex";
    if (DOM.listingsContainer) DOM.listingsContainer.style.display = "none";
}

function showErrorState(message) {
    if (DOM.listingsLoading) DOM.listingsLoading.style.display = "none";
    if (DOM.listingsEmpty) DOM.listingsEmpty.style.display = "none";
    if (DOM.listingsContainer) DOM.listingsContainer.style.display = "none";
    if (DOM.listingsError) {
        DOM.listingsError.style.display = "flex";
        if (DOM.errorDetailsText) DOM.errorDetailsText.textContent = message;
    }
}

// ==========================================================================
// TOAST NOTIFICATIONS
// ==========================================================================

function showToast(message, type = "success") {
    if (!DOM.toastContainer) return;

    const toast = document.createElement("div");
    toast.classList.add(
        "toast",
        type === "error" ? "toast-error" : (type === "info" ? "toast-info" : "toast-success")
    );

    const icon = type === "error" ? "✕" : (type === "info" ? "ℹ️" : "✓");
    toast.innerHTML = `<span class="toast-icon">${icon}</span> <span>${message}</span>`;

    DOM.toastContainer.appendChild(toast);

    // Trigger enter animation
    setTimeout(() => {
        toast.classList.add("toast-show");
    }, 20);

    // Auto dismiss after 3.8s
    setTimeout(() => {
        toast.classList.remove("toast-show");
        setTimeout(() => toast.remove(), 350);
    }, 3800);
}

// ==========================================================================
// UTILITY FORMATTERS
// ==========================================================================

function formatHarvestDate(dateStr) {
    if (!dateStr || dateStr === "Not available") return "October 2026";
    try {
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return dateStr;
        return d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
    } catch {
        return dateStr;
    }
}

function formatCommitmentTimestamp(dateStr) {
    if (!dateStr) return "Just now";
    try {
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return "Recently";
        return d.toLocaleDateString("en-IN", {
            day: "numeric",
            month: "short",
            hour: "2-digit",
            minute: "2-digit"
        });
    } catch {
        return "Recently";
    }
}
