// ==========================================================================
// AGRIBRIDGE — COMPLETE ADMIN CONTROL CENTER JAVASCRIPT ENGINE
// Enterprise Operations, Multi-Entity Governance & Live Data Bus
// ==========================================================================

(function () {
    "use strict";

    console.log("=== AGRIBRIDGE ADMIN CONTROL CENTER INITIALIZING ===");

    const API_BASE_URL = "http://127.0.0.1:8000";

    // ======================================================================
    // 1. COMPREHENSIVE PLATFORM DATA STORE
    // ======================================================================
    const DB = {
        users: [
            { id: "USR-101", name: "Ramesh Patel", email: "ramesh.patel@agrifarm.in", role: "farmer", location: "Raipur, Chhattisgarh", status: "active", createdAt: "2026-02-10", lastActive: "10 mins ago" },
            { id: "USR-102", name: "Suresh Meena", email: "suresh.meena@rajasthanfarm.org", role: "farmer", location: "Kota, Rajasthan", status: "active", createdAt: "2026-02-12", lastActive: "1 hour ago" },
            { id: "USR-103", name: "Gurpreet Singh", email: "gurpreet.singh@punjabkisan.in", role: "farmer", location: "Bathinda, Punjab", status: "active", createdAt: "2026-02-15", lastActive: "35 mins ago" },
            { id: "USR-104", name: "Anand Deshmukh", email: "anand.deshmukh@mahagri.com", role: "farmer", location: "Nagpur, Maharashtra", status: "active", createdAt: "2026-02-18", lastActive: "2 hours ago" },
            { id: "USR-105", name: "Vikram Chauhan", email: "vikram.chauhan@haryanafarm.in", role: "farmer", location: "Karnal, Haryana", status: "active", createdAt: "2026-02-20", lastActive: "15 mins ago" },
            { id: "USR-106", name: "Rajesh Kumar", email: "rajesh.kumar@jharkhandagri.in", role: "farmer", location: "Ranchi, Jharkhand", status: "active", createdAt: "2026-02-22", lastActive: "5 mins ago" },
            { id: "USR-107", name: "Harishankar Yadav", email: "harishankar.y@upkisan.in", role: "farmer", location: "Varanasi, Uttar Pradesh", status: "pending", createdAt: "2026-02-28", lastActive: "1 day ago" },
            { id: "USR-108", name: "Pooja Verma", email: "pooja.verma@biharfarm.in", role: "farmer", location: "Patna, Bihar", status: "active", createdAt: "2026-02-25", lastActive: "4 hours ago" },
            { id: "USR-109", name: "Brijesh Mishra", email: "brijesh.mishra@mpagri.org", role: "farmer", location: "Indore, Madhya Pradesh", status: "active", createdAt: "2026-02-26", lastActive: "3 hours ago" },
            { id: "USR-110", name: "Manoj Choudhary", email: "manoj.c@gujaratkisan.in", role: "farmer", location: "Surat, Gujarat", status: "active", createdAt: "2026-02-27", lastActive: "6 hours ago" },
            
            { id: "USR-201", name: "FreshBazaar Retail Pvt Ltd", email: "procurement@freshbazaar.in", role: "buyer", location: "Mumbai, Maharashtra", status: "active", createdAt: "2026-02-05", lastActive: "8 mins ago" },
            { id: "USR-202", name: "AgriCorp Global Procurement", email: "orders@agricorp.com", role: "buyer", location: "New Delhi, Delhi", status: "active", createdAt: "2026-02-08", lastActive: "25 mins ago" },
            { id: "USR-203", name: "GrainHub Wholesale Traders", email: "sourcing@grainhub.org", role: "buyer", location: "Bengaluru, Karnataka", status: "active", createdAt: "2026-02-14", lastActive: "1 hour ago" },
            { id: "USR-204", name: "NatureBounty Organic Foods", email: "contact@naturebounty.in", role: "buyer", location: "Pune, Maharashtra", status: "active", createdAt: "2026-02-19", lastActive: "45 mins ago" },
            { id: "USR-205", name: "MahaSpices & Grains Ltd", email: "supply@mahaspices.com", role: "buyer", location: "Hyderabad, Telangana", status: "active", createdAt: "2026-02-21", lastActive: "2 hours ago" },
            { id: "USR-206", name: "Apex Agro Exports Ltd", email: "export@apexagro.in", role: "buyer", location: "Chennai, Tamil Nadu", status: "suspended", createdAt: "2026-01-20", lastActive: "5 days ago" },
            
            { id: "USR-301", name: "Amit Sharma", email: "amit.sharma@agribridge.org", role: "field-agent", location: "Raipur & Durg, Chhattisgarh", status: "active", createdAt: "2026-02-01", lastActive: "Just now" },
            { id: "USR-302", name: "Priya Nair", email: "priya.nair@agribridge.org", role: "field-agent", location: "Karnal, Haryana", status: "active", createdAt: "2026-02-01", lastActive: "12 mins ago" },
            { id: "USR-303", name: "Devendra Verma", email: "devendra.v@agribridge.org", role: "field-agent", location: "Nagpur, Maharashtra", status: "active", createdAt: "2026-02-03", lastActive: "30 mins ago" },
            { id: "USR-304", name: "Balwinder Singh", email: "balwinder.s@agribridge.org", role: "field-agent", location: "Bathinda, Punjab", status: "active", createdAt: "2026-02-04", lastActive: "1 hour ago" },
            { id: "USR-305", name: "Kailash Joshi", email: "kailash.j@agribridge.org", role: "field-agent", location: "Kota, Rajasthan", status: "active", createdAt: "2026-02-05", lastActive: "2 hours ago" },
            { id: "USR-306", name: "Sunil Soren", email: "sunil.soren@agribridge.org", role: "field-agent", location: "Ranchi, Jharkhand", status: "active", createdAt: "2026-02-06", lastActive: "40 mins ago" },

            { id: "USR-001", name: "Operations SuperAdmin", email: "ops@agribridge.org", role: "admin", location: "Headquarters (Cloud Node 01)", status: "active", createdAt: "2026-01-01", lastActive: "Active Session" },
            { id: "USR-002", name: "Security & Trust Officer", email: "trust@agribridge.org", role: "admin", location: "Headquarters (Cloud Node 02)", status: "active", createdAt: "2026-01-05", lastActive: "3 hours ago" }
        ],

        farmers: [
            { id: "FARMER-101", name: "Ramesh Patel", location: "Raipur, Chhattisgarh", crop: "Wheat (Sharbati A+)", area: "8.5 Acres", aiHealth: "94% (Grade A+)", verified: true, commitments: "₹ 1,35,000", phone: "+91 98271 44520" },
            { id: "FARMER-102", name: "Suresh Meena", location: "Kota, Rajasthan", crop: "Mustard (Pusa Bold)", area: "6.0 Acres", aiHealth: "91% (Grade A)", verified: true, commitments: "₹ 2,90,000", phone: "+91 94140 88210" },
            { id: "FARMER-103", name: "Gurpreet Singh", location: "Bathinda, Punjab", crop: "Rice (Basmati 1121)", area: "14.2 Acres", aiHealth: "96% (Grade A+)", verified: true, commitments: "₹ 2,25,000", phone: "+91 98150 33490" },
            { id: "FARMER-104", name: "Anand Deshmukh", location: "Nagpur, Maharashtra", crop: "Soybean (JS 335)", area: "10.0 Acres", aiHealth: "93% (Grade A)", verified: true, commitments: "₹ 1,68,000", phone: "+91 98220 55180" },
            { id: "FARMER-105", name: "Vikram Chauhan", location: "Karnal, Haryana", crop: "Wheat (HD-2967)", area: "12.0 Acres", aiHealth: "95% (Grade A+)", verified: true, commitments: "₹ 1,20,000", phone: "+91 94660 77310" },
            { id: "FARMER-106", name: "Rajesh Kumar", location: "Ranchi, Jharkhand", crop: "Maize (Hybrid HQPM-1)", area: "5.5 Acres", aiHealth: "89% (Pending)", verified: false, commitments: "₹ 0 (In Review)", phone: "+91 94311 22980" },
            { id: "FARMER-107", name: "Harishankar Yadav", location: "Varanasi, UP", crop: "Mustard", area: "4.2 Acres", aiHealth: "86% (Pending)", verified: false, commitments: "₹ 0 (In Review)", phone: "+91 94500 11840" },
            { id: "FARMER-108", name: "Brijesh Mishra", location: "Indore, MP", crop: "Soybean", area: "9.0 Acres", aiHealth: "92% (Grade A)", verified: true, commitments: "₹ 1,44,000", phone: "+91 98260 44290" }
        ],

        buyers: [
            { id: "BUYER-201", name: "FreshBazaar Retail Pvt Ltd", contact: "procurement@freshbazaar.in", type: "Supermarket Chain", totalOrders: 3, committedVal: "₹ 4,25,000", status: "active" },
            { id: "BUYER-202", name: "AgriCorp Global Procurement", contact: "orders@agricorp.com", type: "Wholesale Aggregator", totalOrders: 2, committedVal: "₹ 5,15,000", status: "active" },
            { id: "BUYER-203", name: "GrainHub Wholesale Traders", contact: "sourcing@grainhub.org", type: "Milling Enterprise", totalOrders: 2, committedVal: "₹ 2,89,000", status: "active" },
            { id: "BUYER-204", name: "NatureBounty Organic Foods", contact: "contact@naturebounty.in", type: "Direct-to-Consumer Brand", totalOrders: 1, committedVal: "₹ 1,35,000", status: "active" },
            { id: "BUYER-205", name: "MahaSpices & Grains Ltd", contact: "supply@mahaspices.com", type: "Commodity Exporter", totalOrders: 1, committedVal: "₹ 1,21,000", status: "active" }
        ],

        agents: [
            { id: "FA-204", name: "Amit Sharma", territory: "Raipur & Durg, CG", contact: "+91 98271 44520", assignedFarms: 5, pendingAudits: 1, completedAudits: 14, score: "98.4%" },
            { id: "FA-109", name: "Priya Nair", territory: "Karnal, Haryana", contact: "+91 98765 43210", assignedFarms: 4, pendingAudits: 0, completedAudits: 11, score: "97.2%" },
            { id: "FA-303", name: "Devendra Verma", territory: "Nagpur, Maharashtra", contact: "+91 94221 88900", assignedFarms: 3, pendingAudits: 1, completedAudits: 9, score: "96.5%" },
            { id: "FA-405", name: "Balwinder Singh", territory: "Bathinda, Punjab", contact: "+91 98140 77620", assignedFarms: 4, pendingAudits: 0, completedAudits: 16, score: "99.1%" },
            { id: "FA-501", name: "Sunil Soren", territory: "Ranchi, Jharkhand", contact: "+91 94311 66540", assignedFarms: 2, pendingAudits: 1, completedAudits: 6, score: "95.0%" }
        ],

        farms: [
            { id: "POLY-001", farmer: "Ramesh Patel", location: "Raipur, CG", coords: "21.2514° N, 81.6296° E", area: 8.5, crop: "Wheat", vigor: "94% (High)", geoFenced: true },
            { id: "POLY-002", farmer: "Suresh Meena", location: "Kota, RJ", coords: "25.2138° N, 75.8648° E", area: 6.0, crop: "Mustard", vigor: "91% (High)", geoFenced: true },
            { id: "POLY-003", farmer: "Gurpreet Singh", location: "Bathinda, PB", coords: "30.2110° N, 74.9455° E", area: 14.2, crop: "Basmati Rice", vigor: "96% (High)", geoFenced: true },
            { id: "POLY-004", farmer: "Anand Deshmukh", location: "Nagpur, MH", coords: "21.1458° N, 79.0882° E", area: 10.0, crop: "Soybean", vigor: "93% (High)", geoFenced: true },
            { id: "POLY-005", farmer: "Vikram Chauhan", location: "Karnal, HR", coords: "29.6857° N, 76.9905° E", area: 12.0, crop: "Wheat", vigor: "95% (High)", geoFenced: true },
            { id: "POLY-006", farmer: "Rajesh Kumar", location: "Ranchi, JH", coords: "23.3441° N, 85.3096° E", area: 5.5, crop: "Maize", vigor: "89% (Pending Audit)", geoFenced: true }
        ],

        listings: [
            { id: "LIST-001", crop: "Wheat (Sharbati A+)", farmer: "Ramesh Patel", location: "Raipur, CG", qty: "5,000 kg", price: "₹ 27 / kg", harvestDate: "2026-10-15", aiConfidence: "95%", agent: "Amit Sharma #FA-204", status: "Committed" },
            { id: "LIST-002", crop: "Rice (Basmati 1121)", farmer: "Gurpreet Singh", location: "Bathinda, PB", qty: "3,500 kg", price: "₹ 75 / kg", harvestDate: "2026-10-20", aiConfidence: "96%", agent: "Balwinder Singh #FA-405", status: "Verified" },
            { id: "LIST-003", crop: "Mustard (Pusa Bold)", farmer: "Suresh Meena", location: "Kota, RJ", qty: "4,000 kg", price: "₹ 58 / kg", harvestDate: "2026-11-05", aiConfidence: "94%", agent: "Kailash Joshi #FA-501", status: "Committed" },
            { id: "LIST-004", crop: "Soybean (JS 335)", farmer: "Vijay Singh", location: "Rajnandgaon, CG", qty: "3,000 kg", price: "₹ 42 / kg", harvestDate: "2026-10-18", aiConfidence: "93%", agent: "Pooja Verma #FA-318", status: "Verified" },
            { id: "LIST-005", crop: "Maize (Hybrid HQPM-1)", farmer: "Anil Sahu", location: "Raipur, CG", qty: "4,500 kg", price: "₹ 22 / kg", harvestDate: "2026-10-25", aiConfidence: "91%", agent: "Amit Sharma #FA-204", status: "Verified" },
            { id: "LIST-006", crop: "Cotton (Long Staple BT)", farmer: "Anand Deshmukh", location: "Nagpur, MH", qty: "3,200 kg", price: "₹ 68 / kg", harvestDate: "2026-11-12", aiConfidence: "95%", agent: "Devendra Verma #FA-303", status: "Verified" },
            { id: "LIST-007", crop: "Sugarcane (Co 0238)", farmer: "Vikram Chauhan", location: "Karnal, HR", qty: "8,000 kg", price: "₹ 34 / kg", harvestDate: "2026-11-28", aiConfidence: "96%", agent: "Priya Nair #FA-109", status: "Verified" },
            { id: "LIST-008", crop: "Potato (Kufri Jyoti)", farmer: "Harishankar Yadav", location: "Varanasi, UP", qty: "3,800 kg", price: "₹ 16 / kg", harvestDate: "2026-10-30", aiConfidence: "92%", agent: "Pooja Verma #FA-318", status: "Verified" },
            { id: "LIST-009", crop: "Tomato (Himsona)", farmer: "Mahesh Verma", location: "Bilaspur, CG", qty: "1,800 kg", price: "₹ 18 / kg", harvestDate: "2026-10-10", aiConfidence: "96%", agent: "Rahul Sahu #FA-109", status: "Verified" }
        ],

        verifications: [
            { id: "VERIF-101", listingId: "LIST-001", farmer: "Ramesh Patel", crop: "Wheat (Sharbati A+)", location: "Raipur, CG", agent: "Amit Sharma #FA-204", aiConf: "94%", grade: "Grade A+ (96%)", date: "2026-02-28", status: "Verified", notes: "Foliage vigor optimal, 0% pathogen infection, quadrat yield sampling passed." },
            { id: "VERIF-102", listingId: "LIST-002", farmer: "Suresh Meena", crop: "Mustard (Pusa Bold)", location: "Kota, RJ", agent: "Kailash Joshi #FA-501", aiConf: "91%", grade: "Grade A (94%)", date: "2026-02-27", status: "Verified", notes: "Siliqua pod formation complete, zero aphid infestation." },
            { id: "VERIF-103", listingId: "LIST-003", farmer: "Gurpreet Singh", crop: "Rice (Basmati 1121)", location: "Bathinda, PB", agent: "Balwinder Singh #FA-405", aiConf: "96%", grade: "Grade A+ (97%)", date: "2026-02-28", status: "Verified", notes: "Panicle density excellent, zero stem borer activity." },
            { id: "VERIF-104", listingId: "LIST-006", farmer: "Rajesh Kumar", crop: "Maize (Hybrid HQPM-1)", location: "Ranchi, JH", agent: "Sunil Soren #FA-501", aiConf: "89%", grade: "Pending Audit", date: "2026-03-01", status: "Pending", notes: "Field visit scheduled for tomorrow morning." },
            { id: "VERIF-105", listingId: "LIST-007", farmer: "Harishankar Yadav", crop: "Mustard", location: "Varanasi, UP", agent: "Unassigned", aiConf: "86%", grade: "Pending Audit", date: "2026-03-01", status: "Pending", notes: "Awaiting local agent dispatch." }
        ],

        orders: [
            { id: "ORD-8821", buyer: "FreshBazaar Retail Pvt Ltd", farmer: "Ramesh Patel", crop: "Wheat (Sharbati A+)", qty: "5,000 kg", amount: "₹ 1,35,000", date: "2026-03-01 10:15 AM", status: "Committed" },
            { id: "ORD-8822", buyer: "AgriCorp Global Procurement", farmer: "Suresh Meena", crop: "Mustard (Pusa Bold)", qty: "5,000 kg", amount: "₹ 2,90,000", date: "2026-03-01 09:40 AM", status: "Committed" },
            { id: "ORD-8823", buyer: "NatureBounty Organic Foods", farmer: "Vikram Chauhan", crop: "Wheat (HD-2967)", qty: "4,000 kg", amount: "₹ 1,20,000", date: "2026-02-28 04:30 PM", status: "Committed" },
            { id: "ORD-8824", buyer: "GrainHub Wholesale Traders", farmer: "Gurpreet Singh", crop: "Rice (Basmati 1121)", qty: "3,000 kg", amount: "₹ 2,25,000", date: "2026-02-28 02:15 PM", status: "Confirmed" },
            { id: "ORD-8825", buyer: "FreshBazaar Retail Pvt Ltd", farmer: "Anand Deshmukh", crop: "Soybean (JS 335)", qty: "4,000 kg", amount: "₹ 1,68,000", date: "2026-02-27 11:20 AM", status: "Confirmed" }
        ],

        notifications: [
            { id: "NOTIF-901", recipient: "Ramesh Patel (Farmer)", role: "Farmer", category: "Order", text: "FreshBazaar locked ₹1,35,000 pre-harvest commitment for 5,000 kg Wheat.", time: "10:15 AM", status: "Delivered (SMS)" },
            { id: "NOTIF-902", recipient: "Amit Sharma (Inspector)", role: "Field Agent", category: "Verification", text: "Quality certificate AGB-CERT-2026-081 signed for Farm POLY-001.", time: "09:30 AM", status: "Delivered (In-App)" },
            { id: "NOTIF-903", recipient: "Rajesh Kumar (Farmer)", role: "Farmer", category: "Weather", text: "Light rain forecast in Ranchi window. Delay pesticide application.", time: "08:45 AM", status: "Delivered (WhatsApp)" }
        ],

        aiDiagnostics: [
            { id: "AI-SCAN-01", farm: "Farm #1 — Ramesh Patel", crop: "Wheat", health: "94% (Healthy)", diseaseRisk: "Low (1.2%)", weatherRisk: "Low (15% Rain)", conf: "94.8%", priority: "Normal", rec: "Proceed with pre-harvest listing and field seal." },
            { id: "AI-SCAN-02", farm: "Farm #2 — Suresh Meena", crop: "Mustard", health: "91% (Healthy)", diseaseRisk: "Low (2.4%)", weatherRisk: "Moderate (Wind 18km/h)", conf: "91.2%", priority: "Normal", rec: "Maintain soil moisture level." },
            { id: "AI-SCAN-03", farm: "Farm #6 — Rajesh Kumar", crop: "Maize", health: "89% (Mild Stress)", diseaseRisk: "Moderate (Yellow Rust 4%)", weatherRisk: "High (65% Rain Prob)", conf: "89.4%", priority: "High Priority", rec: "Schedule Field Agent inspection and foliar spray." }
        ],

        weatherRegions: [
            { name: "Raipur, Chhattisgarh", temp: "28°C", rain: "20%", humidity: "72%", wind: "12 km/h", risk: "LOW", advisory: "Safe 48h spraying window. Optimum harvest conditions." },
            { name: "Kota, Rajasthan", temp: "31°C", rain: "5%", humidity: "45%", wind: "14 km/h", risk: "LOW", advisory: "Dry weather favorable for mustard pod maturation." },
            { name: "Bathinda, Punjab", temp: "24°C", rain: "10%", humidity: "62%", wind: "10 km/h", risk: "LOW", advisory: "Favorable conditions for panicle filling in wheat/rice." },
            { name: "Nagpur, Maharashtra", temp: "32°C", rain: "15%", humidity: "50%", wind: "15 km/h", risk: "LOW", advisory: "Optimal soil temperature for legume stands." },
            { name: "Ranchi, Jharkhand", temp: "27°C", rain: "45%", humidity: "78%", wind: "16 km/h", risk: "MODERATE", advisory: "Scattered precipitation expected Thursday. Complete spraying before noon." }
        ],

        securityEvents: [
            { id: "SEC-101", type: "Authentication", severity: "Low", source: "103.21.14.82", desc: "Admin login successful with encrypted session cookie.", time: "Today 10:45 AM", status: "Authorized" },
            { id: "SEC-102", type: "Rate Limiter", severity: "Medium", source: "49.36.120.14", desc: "2 failed password attempts on buyer@agricorp.com. Blocked by rate limiter.", time: "Today 09:12 AM", status: "Resolved" },
            { id: "SEC-103", type: "Session Audit", severity: "Low", source: "Internal Bus", desc: "JWT token renewed for Field Inspector #FA-204.", time: "Today 08:30 AM", status: "Valid" }
        ],

        loginHistory: [
            { id: "LOG-551", user: "Operations SuperAdmin", role: "admin", ip: "103.21.14.82", device: "Chrome 122 / Windows 11", time: "Today 10:45 AM", status: "Successful" },
            { id: "LOG-552", user: "procurement@freshbazaar.in", role: "buyer", ip: "115.112.44.10", device: "Chrome 122 / macOS", time: "Today 10:12 AM", status: "Successful" },
            { id: "LOG-553", user: "amit.sharma@agribridge.org", role: "field-agent", ip: "106.51.88.20", device: "Mobile Safari / iOS", time: "Today 09:30 AM", status: "Successful" },
            { id: "LOG-554", user: "ramesh.patel@agrifarm.in", role: "farmer", ip: "49.36.120.14", device: "Chrome Mobile / Android", time: "Today 09:05 AM", status: "Successful" },
            { id: "LOG-555", user: "buyer@agricorp.com", role: "buyer", ip: "49.36.120.14", device: "Firefox / Windows", time: "Today 09:12 AM", status: "Failed (Invalid Pass)" }
        ],

        auditLogs: [
            { id: "AUD-701", time: "Today 10:45 AM", actor: "Operations SuperAdmin", action: "Admin Session Login", entity: "Admin Portal", entityId: "USR-001", status: "Success", details: "Control Center accessed from local IP." },
            { id: "AUD-702", time: "Today 10:15 AM", actor: "FreshBazaar Retail", action: "Placed Pre-Harvest Order", entity: "Order", entityId: "ORD-8821", status: "Success", details: "Committed ₹1,35,000 for 5,000 kg Wheat." },
            { id: "AUD-703", time: "Today 09:30 AM", actor: "Amit Sharma #FA-204", action: "Issued Quality Certificate", entity: "Verification", entityId: "VERIF-101", status: "Success", details: "Certified Farm POLY-001 with Grade A+." },
            { id: "AUD-704", time: "Today 09:05 AM", actor: "Ramesh Patel", action: "Uploaded Crop Photo for Scan", entity: "Listing", entityId: "LIST-001", status: "Success", details: "AI Neural scan executed with 94% confidence." }
        ]
    };

    // ======================================================================
    // 2. LIVE LOCAL STORAGE & BACKEND SYNC
    // ======================================================================
    function syncLocalData() {
        try {
            // Merge buyer orders from localStorage if present
            const savedBuyerOrders = localStorage.getItem("agribridge_buyer_orders");
            if (savedBuyerOrders) {
                const parsed = JSON.parse(savedBuyerOrders);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    parsed.forEach((order, idx) => {
                        const exists = DB.orders.some(o => o.id === order.order_id);
                        if (!exists) {
                            DB.orders.unshift({
                                id: order.order_id || `ORD-L${idx + 1}`,
                                buyer: order.buyer_name || "Enterprise Buyer",
                                farmer: order.farmer_name || "Ramesh Patel",
                                crop: order.crop_name || "Wheat",
                                qty: `${order.quantity || 5000} kg`,
                                amount: `₹ ${(order.total_amount || 135000).toLocaleString("en-IN")}`,
                                date: order.created_at || "Just now",
                                status: order.status || "Committed"
                            });
                        }
                    });
                }
            }

            // Sync crop data if uploaded via farmer dashboard
            const cropData = localStorage.getItem("cropData");
            if (cropData) {
                const parsedCrop = JSON.parse(cropData);
                if (parsedCrop && parsedCrop.crop_type) {
                    const exists = DB.listings.some(l => l.crop === parsedCrop.crop_type);
                    if (!exists) {
                        DB.listings.unshift({
                            id: `LIST-${parsedCrop.id || "901"}`,
                            crop: parsedCrop.crop_type,
                            farmer: parsedCrop.farmer_name || "Local Farmer",
                            location: parsedCrop.location || "Ranchi, Jharkhand",
                            qty: `${parsedCrop.quantity || 3500} kg`,
                            price: `₹ ${parsedCrop.price_per_kg || 28} / kg`,
                            harvestDate: parsedCrop.expected_harvest || "2026-04-10",
                            aiConfidence: `${parsedCrop.ai_confidence || 92}%`,
                            agent: "Amit Sharma #FA-204",
                            status: parsedCrop.verification_status || "Verified"
                        });
                    }
                }
            }

            // Sync live logins from teammates
            const liveLogins = localStorage.getItem("agribridge_live_logins");
            if (liveLogins) {
                const parsedLogs = JSON.parse(liveLogins);
                if (Array.isArray(parsedLogs) && parsedLogs.length > 0) {
                    parsedLogs.forEach(log => {
                        const exists = DB.loginHistory.some(l => l.id === log.id);
                        if (!exists) {
                            DB.loginHistory.unshift(log);
                        }
                    });
                }
            }
        } catch (e) {
            console.warn("Storage sync completed with defaults:", e.message);
        }
    }

    // ======================================================================
    // 3. CORE DOM & VIEW ROUTER
    // ======================================================================
    const AdminApp = {
        currentView: "overview",

        init: function () {
            syncLocalData();
            this.setupAuthGuard();
            this.setupClock();
            this.setupNavigation();
            this.setupSearch();
            this.setupModals();
            this.setupSettingsForm();
            this.renderAllViews();
            this.checkBackendHealth();
            console.log("✓ AgriBridge Admin Control Center Ready.");
        },

        setupAuthGuard: function () {
            const guardEl = document.getElementById("admin-auth-guard");
            const mainLayout = document.getElementById("admin-main-layout");
            const form = document.getElementById("admin-pin-form");
            const pinInput = document.getElementById("admin-pin-input");
            const errorMsg = document.getElementById("pin-error-msg");
            const togglePin = document.getElementById("pin-toggle-btn");
            const logoutBtn = document.getElementById("admin-logout-btn");

            if (!guardEl || !form || !pinInput) return;

            // Always enforce passcode prompt on every visit and every refresh
            sessionStorage.removeItem("agribridge_admin_authenticated");
            guardEl.style.display = "flex";
            if (mainLayout) mainLayout.style.display = "none";
            pinInput.value = "";
            if (errorMsg) errorMsg.style.display = "none";
            setTimeout(() => pinInput.focus(), 250);

            // Show/Hide passcode toggle
            if (togglePin) {
                togglePin.addEventListener("click", () => {
                    if (pinInput.type === "password") {
                        pinInput.type = "text";
                        togglePin.textContent = "🙈";
                    } else {
                        pinInput.type = "password";
                        togglePin.textContent = "👁️";
                    }
                });
            }

            let failedAttempts = 0;

            form.addEventListener("submit", (e) => {
                e.preventDefault();
                const entered = pinInput.value.trim();

                // Valid passcodes: admin123, agri2026, agribridge
                if (entered === "admin123" || entered === "agri2026" || entered === "agribridge") {
                    sessionStorage.setItem("agribridge_admin_authenticated", "true");
                    guardEl.style.display = "none";
                    if (mainLayout) mainLayout.style.display = "flex";
                    if (errorMsg) errorMsg.style.display = "none";
                    this.logAudit("Admin Security Passcode Authorized", "Security Gate", "SESSION", "Success", "Authorized Admin session granted.");
                } else {
                    failedAttempts++;
                    pinInput.value = "";
                    if (errorMsg) {
                        errorMsg.textContent = `❌ Invalid security passcode (Attempt ${failedAttempts}). Passcode is 'admin123'.`;
                        errorMsg.style.display = "block";
                    }
                    this.logAudit("Failed Passcode Attempt", "Security Gate", "ACCESS-DENIED", "Blocked", `Invalid passcode attempt #${failedAttempts}.`);
                    
                    if (failedAttempts >= 3) {
                        const submitBtn = document.getElementById("btn-submit-pin");
                        if (submitBtn) {
                            submitBtn.disabled = true;
                            submitBtn.textContent = "Rate Limited (Wait 5s)...";
                            setTimeout(() => {
                                submitBtn.disabled = false;
                                submitBtn.textContent = "Unlock Control Center";
                            }, 5000);
                        }
                    }
                }
            });

            // Logout handler
            if (logoutBtn) {
                logoutBtn.addEventListener("click", (e) => {
                    e.preventDefault();
                    sessionStorage.removeItem("agribridge_admin_authenticated");
                    guardEl.style.display = "flex";
                    if (mainLayout) mainLayout.style.display = "none";
                    pinInput.value = "";
                    if (errorMsg) errorMsg.style.display = "none";
                    this.logAudit("Admin Logged Out", "Security Gate", "SESSION", "Success", "Session invalidated.");
                    setTimeout(() => pinInput.focus(), 250);
                });
            }
        },

        setupClock: function () {
            const clockEl = document.getElementById("live-clock");
            if (!clockEl) return;
            const updateTime = () => {
                const now = new Date();
                clockEl.textContent = now.toLocaleTimeString("en-IN", { hour12: false }) + " IST";
            };
            updateTime();
            setInterval(updateTime, 1000);
        },

        setupNavigation: function () {
            const navItems = document.querySelectorAll(".nav-item[data-view]");
            const panels = document.querySelectorAll(".admin-view-panel");
            const viewTitle = document.getElementById("current-view-title");
            const sidebar = document.getElementById("admin-sidebar");
            const toggleBtn = document.getElementById("sidebar-toggle");

            // Sidebar toggle for mobile
            if (toggleBtn && sidebar) {
                toggleBtn.addEventListener("click", () => {
                    sidebar.classList.toggle("open");
                });
            }

            // View switching handler
            navItems.forEach(item => {
                item.addEventListener("click", () => {
                    const targetView = item.getAttribute("data-view");
                    if (!targetView) return;

                    navItems.forEach(n => n.classList.remove("active"));
                    item.classList.add("active");

                    panels.forEach(panel => {
                        panel.classList.remove("active");
                        if (panel.id === `view-${targetView}`) {
                            panel.classList.add("active");
                        }
                    });

                    // Update Title
                    const text = item.querySelector(".nav-text")?.textContent || "Control Center";
                    if (viewTitle) viewTitle.textContent = text;
                    this.currentView = targetView;

                    // Close mobile sidebar
                    if (sidebar) sidebar.classList.remove("open");
                    window.scrollTo({ top: 0, behavior: "smooth" });
                });
            });

            // Quick Jump triggers
            document.querySelectorAll("[data-jump]").forEach(btn => {
                btn.addEventListener("click", () => {
                    const jumpTarget = btn.getAttribute("data-jump");
                    const targetNav = document.querySelector(`.nav-item[data-view="${jumpTarget}"]`);
                    if (targetNav) targetNav.click();
                });
            });

            // Refresh Button
            const refreshBtn = document.getElementById("admin-refresh-btn");
            if (refreshBtn) {
                refreshBtn.addEventListener("click", () => {
                    refreshBtn.style.transform = "rotate(360deg)";
                    refreshBtn.style.transition = "transform 0.5s ease";
                    setTimeout(() => {
                        refreshBtn.style.transform = "none";
                        refreshBtn.style.transition = "none";
                    }, 500);
                    syncLocalData();
                    this.renderAllViews();
                    this.logAudit("Admin Data Refresh", "System Bus", "ALL", "Success", "Refreshed operational views.");
                });
            }
        },

        // ==================================================================
        // 4. GLOBAL OMNI-SEARCH ENGINE
        // ==================================================================
        setupSearch: function () {
            const searchInput = document.getElementById("global-admin-search");
            const dropdown = document.getElementById("omni-search-dropdown");
            const resultsList = document.getElementById("omni-search-list");
            const closeBtn = document.getElementById("search-close-btn");
            const clearBtn = document.getElementById("search-clear-btn");

            if (!searchInput || !dropdown || !resultsList) return;

            const handleSearch = () => {
                const query = searchInput.value.trim().toLowerCase();
                if (query.length < 2) {
                    dropdown.style.display = "none";
                    if (clearBtn) clearBtn.style.display = "none";
                    return;
                }

                if (clearBtn) clearBtn.style.display = "block";
                resultsList.innerHTML = "";

                let matches = 0;

                // Search Users
                DB.users.forEach(u => {
                    if (u.name.toLowerCase().includes(query) || u.email.toLowerCase().includes(query) || u.id.toLowerCase().includes(query)) {
                        matches++;
                        this.appendSearchResult(resultsList, "USER", u.name, `${u.role.toUpperCase()} · ${u.location}`, () => {
                            this.jumpToView("users");
                            this.inspectItem("user", u.id);
                        });
                    }
                });

                // Search Listings
                DB.listings.forEach(l => {
                    if (l.crop.toLowerCase().includes(query) || l.farmer.toLowerCase().includes(query) || l.id.toLowerCase().includes(query)) {
                        matches++;
                        this.appendSearchResult(resultsList, "LISTING", l.crop, `${l.farmer} · ${l.qty} · ${l.status}`, () => {
                            this.jumpToView("listings");
                            this.inspectItem("listing", l.id);
                        });
                    }
                });

                // Search Orders
                DB.orders.forEach(o => {
                    if (o.id.toLowerCase().includes(query) || o.buyer.toLowerCase().includes(query) || o.crop.toLowerCase().includes(query)) {
                        matches++;
                        this.appendSearchResult(resultsList, "ORDER", o.id, `${o.buyer} · ${o.amount} · ${o.status}`, () => {
                            this.jumpToView("orders");
                            this.inspectItem("order", o.id);
                        });
                    }
                });

                if (matches === 0) {
                    resultsList.innerHTML = `<div style="padding: 16px; text-align: center; color: var(--adm-text-muted); font-size: 12px;">No matching records found for "${query}".</div>`;
                }

                dropdown.style.display = "block";
            };

            searchInput.addEventListener("input", handleSearch);

            if (clearBtn) {
                clearBtn.addEventListener("click", () => {
                    searchInput.value = "";
                    dropdown.style.display = "none";
                    clearBtn.style.display = "none";
                });
            }

            if (closeBtn) {
                closeBtn.addEventListener("click", () => {
                    dropdown.style.display = "none";
                });
            }

            document.addEventListener("click", (e) => {
                if (!dropdown.contains(e.target) && e.target !== searchInput) {
                    dropdown.style.display = "none";
                }
            });
        },

        appendSearchResult: function (container, tag, title, sub, onClick) {
            const div = document.createElement("div");
            div.className = "search-result-row";
            div.innerHTML = `
                <div>
                    <span class="status-chip pending" style="margin-bottom: 3px; font-size: 8px;">${tag}</span>
                    <div class="search-result-title">${title}</div>
                    <div class="search-result-sub">${sub}</div>
                </div>
                <button type="button" class="action-sm-btn">View →</button>
            `;
            div.addEventListener("click", () => {
                document.getElementById("omni-search-dropdown").style.display = "none";
                onClick();
            });
            container.appendChild(div);
        },

        jumpToView: function (viewKey) {
            const nav = document.querySelector(`.nav-item[data-view="${viewKey}"]`);
            if (nav) nav.click();
        },

        // ==================================================================
        // 5. RENDER ALL APPLICATION VIEWS
        // ==================================================================
        renderAllViews: function () {
            this.renderOverview();
            this.renderUsers();
            this.renderFarmers();
            this.renderBuyers();
            this.renderAgents();
            this.renderFarms();
            this.renderListings();
            this.renderVerifications();
            this.renderOrders();
            this.renderCommitments();
            this.renderNotifications();
            this.renderAIDiagnostics();
            this.renderWeatherRegions();
            this.renderAnalytics();
            this.renderSecurity();
            this.renderLoginHistory();
            this.renderAuditLogs();
        },

        // 5.1 OVERVIEW
        renderOverview: function () {
            // Update KPI counts
            const totalUsersEl = document.getElementById("kpi-total-users");
            const totalListingsEl = document.getElementById("kpi-total-listings");
            const pendingCountEl = document.getElementById("kpi-pending-count");
            const verifiedCountEl = document.getElementById("kpi-verified-count");

            if (totalUsersEl) totalUsersEl.textContent = DB.users.length;
            if (totalListingsEl) totalListingsEl.textContent = DB.listings.length;
            if (pendingCountEl) pendingCountEl.textContent = DB.listings.filter(l => l.status.includes("Pending")).length;
            if (verifiedCountEl) verifiedCountEl.textContent = DB.listings.filter(l => l.status === "Verified" || l.status === "Committed").length;

            // Render Chart 1: Verified Listings vs Commitments
            const chartContainer = document.getElementById("chart-commitments");
            if (chartContainer) {
                chartContainer.innerHTML = `
                    <div style="display: flex; align-items: flex-end; gap: 16px; height: 160px; padding-top: 20px; border-bottom: 2px solid #E1E7DB;">
                        <div style="flex: 1; display: flex; flex-direction: column; align-items: center; gap: 6px;">
                            <div style="width: 100%; height: 120px; background: linear-gradient(180deg, #527A45 0%, #315C2A 100%); border-radius: 6px 6px 0 0; box-shadow: 0 4px 10px rgba(49, 92, 42, 0.2);"></div>
                            <span style="font-size: 11px; font-weight: 700; color: var(--adm-text-dark);">Wheat (5T)</span>
                        </div>
                        <div style="flex: 1; display: flex; flex-direction: column; align-items: center; gap: 6px;">
                            <div style="width: 100%; height: 105px; background: linear-gradient(180deg, #E6C566 0%, #D8B84C 100%); border-radius: 6px 6px 0 0; box-shadow: 0 4px 10px rgba(216, 184, 76, 0.25);"></div>
                            <span style="font-size: 11px; font-weight: 700; color: var(--adm-text-dark);">Mustard (5T)</span>
                        </div>
                        <div style="flex: 1; display: flex; flex-direction: column; align-items: center; gap: 6px;">
                            <div style="width: 100%; height: 80px; background: linear-gradient(180deg, #42A5F5 0%, #1E88E5 100%); border-radius: 6px 6px 0 0; box-shadow: 0 4px 10px rgba(30, 136, 229, 0.25);"></div>
                            <span style="font-size: 11px; font-weight: 700; color: var(--adm-text-dark);">Basmati (3T)</span>
                        </div>
                        <div style="flex: 1; display: flex; flex-direction: column; align-items: center; gap: 6px;">
                            <div style="width: 100%; height: 95px; background: linear-gradient(180deg, #AB47BC 0%, #7B1FA2 100%); border-radius: 6px 6px 0 0; box-shadow: 0 4px 10px rgba(123, 31, 162, 0.25);"></div>
                            <span style="font-size: 11px; font-weight: 700; color: var(--adm-text-dark);">Soybean (4T)</span>
                        </div>
                    </div>
                `;
            }

            // Render Recent Activity Feed
            const activityFeed = document.getElementById("overview-recent-activity");
            if (activityFeed) {
                activityFeed.innerHTML = DB.auditLogs.slice(0, 4).map(log => `
                    <div class="activity-item">
                        <span class="activity-icon">⚡</span>
                        <div class="activity-content">
                            <div class="activity-title">${log.action} · <code>${log.entityId}</code></div>
                            <div class="activity-desc">${log.details}</div>
                        </div>
                        <span class="activity-time">${log.time}</span>
                    </div>
                `).join("");
            }
        },

        // 5.2 USERS
        renderUsers: function () {
            const tbody = document.getElementById("tbody-users");
            if (!tbody) return;

            const roleFilter = document.getElementById("filter-user-role")?.value || "all";
            const statusFilter = document.getElementById("filter-user-status")?.value || "all";
            const searchVal = document.getElementById("filter-user-search")?.value.trim().toLowerCase() || "";

            const filtered = DB.users.filter(u => {
                if (roleFilter !== "all" && u.role !== roleFilter) return false;
                if (statusFilter !== "all" && u.status !== statusFilter) return false;
                if (searchVal && !u.name.toLowerCase().includes(searchVal) && !u.email.toLowerCase().includes(searchVal) && !u.id.toLowerCase().includes(searchVal)) return false;
                return true;
            });

            const countLabel = document.getElementById("label-users-count");
            if (countLabel) countLabel.textContent = `Showing ${filtered.length} of ${DB.users.length} users`;

            tbody.innerHTML = filtered.map(u => `
                <tr>
                    <td><code>${u.id}</code></td>
                    <td><strong>${u.name}</strong></td>
                    <td style="color: var(--adm-text-muted);">${u.email}</td>
                    <td><span class="status-chip ${u.role === 'admin' ? 'suspended' : u.role === 'farmer' ? 'verified' : 'committed'}">${u.role.toUpperCase()}</span></td>
                    <td>${u.location}</td>
                    <td><span class="status-chip ${u.status === 'active' ? 'active' : 'suspended'}">${u.status.toUpperCase()}</span></td>
                    <td>${u.createdAt}</td>
                    <td>
                        <div class="action-btn-group">
                            <button type="button" class="action-sm-btn" onclick="window.AdminApp.inspectItem('user', '${u.id}')">Inspect</button>
                            <button type="button" class="action-sm-btn ${u.status === 'active' ? '' : 'success'}" onclick="window.AdminApp.toggleUserStatus('${u.id}')">${u.status === 'active' ? 'Suspend' : 'Activate'}</button>
                        </div>
                    </td>
                </tr>
            `).join("");

            // Attach filter listeners once
            this.attachFilterListener("filter-user-role", () => this.renderUsers());
            this.attachFilterListener("filter-user-status", () => this.renderUsers());
            this.attachInputListener("filter-user-search", () => this.renderUsers());
        },

        // 5.3 FARMERS
        renderFarmers: function () {
            const tbody = document.getElementById("tbody-farmers");
            if (!tbody) return;
            tbody.innerHTML = DB.farmers.map(f => `
                <tr>
                    <td><code>${f.id}</code></td>
                    <td><strong>${f.name}</strong></td>
                    <td>${f.location}</td>
                    <td>${f.crop}</td>
                    <td>${f.area}</td>
                    <td><strong style="color: var(--adm-green-light);">${f.aiHealth}</strong></td>
                    <td><span class="status-chip ${f.verified ? 'verified' : 'pending'}">${f.verified ? '✓ Certified' : 'Pending Audit'}</span></td>
                    <td><strong style="color: var(--adm-gold-light);">${f.commitments}</strong></td>
                    <td>
                        <button type="button" class="action-sm-btn" onclick="window.AdminApp.inspectItem('farmer', '${f.id}')">View Farm →</button>
                    </td>
                </tr>
            `).join("");
        },

        // 5.4 BUYERS
        renderBuyers: function () {
            const tbody = document.getElementById("tbody-buyers");
            if (!tbody) return;
            tbody.innerHTML = DB.buyers.map(b => `
                <tr>
                    <td><code>${b.id}</code></td>
                    <td><strong>${b.name}</strong></td>
                    <td style="color: var(--adm-text-muted);">${b.contact}</td>
                    <td>${b.type}</td>
                    <td><strong>${b.totalOrders} Orders</strong></td>
                    <td><strong style="color: var(--adm-gold-light);">${b.committedVal}</strong></td>
                    <td><span class="status-chip ${b.status === 'active' ? 'active' : 'suspended'}">${b.status.toUpperCase()}</span></td>
                    <td>
                        <button type="button" class="action-sm-btn" onclick="window.AdminApp.inspectItem('buyer', '${b.id}')">Orders Profile</button>
                    </td>
                </tr>
            `).join("");
        },

        // 5.5 AGENTS
        renderAgents: function () {
            const tbody = document.getElementById("tbody-agents");
            if (!tbody) return;
            tbody.innerHTML = DB.agents.map(a => `
                <tr>
                    <td><code>${a.id}</code></td>
                    <td><strong>${a.name}</strong></td>
                    <td>${a.territory}</td>
                    <td style="color: var(--adm-text-muted);">${a.contact}</td>
                    <td><strong>${a.assignedFarms} Plots</strong></td>
                    <td><span class="status-chip ${a.pendingAudits > 0 ? 'pending' : 'verified'}">${a.pendingAudits} Pending</span></td>
                    <td><strong>${a.completedAudits} Checks</strong></td>
                    <td><strong style="color: var(--adm-green-light);">${a.score}</strong></td>
                    <td>
                        <button type="button" class="action-sm-btn" onclick="window.AdminApp.inspectItem('agent', '${a.id}')">Territory Map</button>
                    </td>
                </tr>
            `).join("");
        },

        // 5.6 FARMS
        renderFarms: function () {
            const tbody = document.getElementById("tbody-farms");
            if (!tbody) return;
            tbody.innerHTML = DB.farms.map(f => `
                <tr>
                    <td><code>${f.id}</code></td>
                    <td><strong>${f.farmer}</strong></td>
                    <td>${f.location}</td>
                    <td class="mono-text">${f.coords}</td>
                    <td>${f.area} Acres</td>
                    <td>${f.crop}</td>
                    <td><strong style="color: var(--adm-green-light);">${f.vigor}</strong></td>
                    <td><span class="status-chip verified">✓ Geo-Fenced</span></td>
                    <td>
                        <button type="button" class="action-sm-btn" onclick="window.AdminApp.inspectItem('farm', '${f.id}')">GPS View</button>
                    </td>
                </tr>
            `).join("");
        },

        // 5.7 LISTINGS
        renderListings: function () {
            const tbody = document.getElementById("tbody-listings");
            if (!tbody) return;

            const statusFilter = document.getElementById("filter-listing-status")?.value || "all";
            const searchVal = document.getElementById("filter-listing-search")?.value.trim().toLowerCase() || "";

            const filtered = DB.listings.filter(l => {
                if (statusFilter !== "all" && l.status !== statusFilter) return false;
                if (searchVal && !l.crop.toLowerCase().includes(searchVal) && !l.farmer.toLowerCase().includes(searchVal) && !l.id.toLowerCase().includes(searchVal)) return false;
                return true;
            });

            tbody.innerHTML = filtered.map(l => `
                <tr>
                    <td><code>${l.id}</code></td>
                    <td><strong>${l.crop}</strong></td>
                    <td>${l.farmer}</td>
                    <td>${l.location}</td>
                    <td>${l.qty}</td>
                    <td><strong>${l.price}</strong></td>
                    <td>${l.harvestDate}</td>
                    <td><strong style="color: var(--adm-green-light);">${l.aiConfidence}</strong></td>
                    <td>${l.agent}</td>
                    <td><span class="status-chip ${l.status === 'Verified' ? 'verified' : l.status === 'Committed' ? 'committed' : 'pending'}">${l.status}</span></td>
                    <td>
                        <button type="button" class="action-sm-btn" onclick="window.AdminApp.inspectItem('listing', '${l.id}')">Inspect</button>
                    </td>
                </tr>
            `).join("");

            this.attachFilterListener("filter-listing-status", () => this.renderListings());
            this.attachInputListener("filter-listing-search", () => this.renderListings());
        },

        // 5.8 VERIFICATION COMMAND CENTER
        renderVerifications: function () {
            const tbody = document.getElementById("tbody-verifications");
            if (!tbody) return;

            tbody.innerHTML = DB.verifications.map(v => `
                <tr>
                    <td><code>${v.id}</code></td>
                    <td><code>${v.listingId}</code></td>
                    <td><strong>${v.farmer}</strong></td>
                    <td>${v.crop} · ${v.location}</td>
                    <td>${v.agent}</td>
                    <td><strong style="color: var(--adm-green-light);">${v.aiConf}</strong></td>
                    <td><strong>${v.grade}</strong></td>
                    <td>${v.date}</td>
                    <td><span class="status-chip ${v.status === 'Verified' ? 'verified' : 'pending'}">${v.status}</span></td>
                    <td>
                        <div class="action-btn-group">
                            <button type="button" class="action-sm-btn" onclick="window.AdminApp.inspectItem('verification', '${v.id}')">Details</button>
                            ${v.status === 'Pending' ? `<button type="button" class="action-sm-btn success" onclick="window.AdminApp.openDecisionModal('${v.id}')">Certify Seal</button>` : ''}
                        </div>
                    </td>
                </tr>
            `).join("");
        },

        // 5.9 ORDERS
        renderOrders: function () {
            const tbody = document.getElementById("tbody-orders");
            if (!tbody) return;
            tbody.innerHTML = DB.orders.map(o => `
                <tr>
                    <td><code>${o.id}</code></td>
                    <td><strong>${o.buyer}</strong></td>
                    <td>${o.farmer}</td>
                    <td>${o.crop}</td>
                    <td>${o.qty}</td>
                    <td><strong style="color: var(--adm-gold-light);">${o.amount}</strong></td>
                    <td>${o.date}</td>
                    <td><span class="status-chip ${o.status === 'Committed' || o.status === 'Confirmed' ? 'committed' : 'pending'}">${o.status}</span></td>
                    <td>
                        <button type="button" class="action-sm-btn" onclick="window.AdminApp.inspectItem('order', '${o.id}')">Inspect</button>
                    </td>
                </tr>
            `).join("");
        },

        // 5.10 COMMITMENTS
        renderCommitments: function () {
            const tbody = document.getElementById("tbody-forward-commitments");
            if (!tbody) return;
            tbody.innerHTML = DB.orders.map(o => `
                <tr>
                    <td><code>FWD-${o.id}</code></td>
                    <td><strong>${o.buyer}</strong></td>
                    <td>${o.farmer}</td>
                    <td>${o.crop}</td>
                    <td>${o.qty}</td>
                    <td>₹ 27 - ₹ 58 / kg</td>
                    <td><strong style="color: var(--adm-gold-light);">${o.amount}</strong></td>
                    <td>March 2026</td>
                    <td><span class="status-chip verified">✓ Guaranteed Lock</span></td>
                </tr>
            `).join("");
        },

        // 5.11 NOTIFICATIONS
        renderNotifications: function () {
            const tbody = document.getElementById("tbody-notifications");
            if (!tbody) return;
            tbody.innerHTML = DB.notifications.map(n => `
                <tr>
                    <td><code>${n.id}</code></td>
                    <td><strong>${n.recipient}</strong></td>
                    <td><span class="status-chip committed">${n.role}</span></td>
                    <td><span class="status-chip pending">${n.category}</span></td>
                    <td>${n.text}</td>
                    <td class="mono-text">${n.time}</td>
                    <td><span class="status-chip verified">${n.status}</span></td>
                </tr>
            `).join("");
        },

        // 5.12 AI DIAGNOSTICS
        renderAIDiagnostics: function () {
            const tbody = document.getElementById("tbody-ai-diagnostics");
            if (!tbody) return;
            tbody.innerHTML = DB.aiDiagnostics.map(a => `
                <tr>
                    <td><code>${a.id}</code></td>
                    <td><strong>${a.farm}</strong></td>
                    <td>${a.crop}</td>
                    <td><strong style="color: var(--adm-green-light);">${a.health}</strong></td>
                    <td>${a.diseaseRisk}</td>
                    <td>${a.weatherRisk}</td>
                    <td><strong>${a.conf}</strong></td>
                    <td><span class="status-chip ${a.priority === 'Normal' ? 'verified' : 'high-risk'}">${a.priority}</span></td>
                    <td>${a.rec}</td>
                </tr>
            `).join("");
        },

        // 5.13 WEATHER REGIONS
        renderWeatherRegions: function () {
            const container = document.getElementById("weather-regions-container");
            if (!container) return;
            container.innerHTML = DB.weatherRegions.map(w => `
                <div class="weather-region-card">
                    <div class="region-header">
                        <span class="region-name">${w.name}</span>
                        <span class="region-temp">${w.temp}</span>
                    </div>
                    <div class="region-metrics">
                        <div class="region-metric-item">
                            <span>Rain Prob.</span>
                            <strong>${w.rain}</strong>
                        </div>
                        <div class="region-metric-item">
                            <span>Humidity</span>
                            <strong>${w.humidity}</strong>
                        </div>
                        <div class="region-metric-item">
                            <span>Wind Speed</span>
                            <strong>${w.wind}</strong>
                        </div>
                    </div>
                    <div class="region-advisory">
                        <strong>Advisory:</strong> ${w.advisory}
                    </div>
                </div>
            `).join("");
        },

        // 5.14 ANALYTICS CHARTS
        renderAnalytics: function () {
            const cropDist = document.getElementById("chart-crop-dist");
            if (cropDist) {
                cropDist.innerHTML = `
                    <div style="display:flex; flex-direction:column; gap:12px;">
                        <div>
                            <div style="display:flex; justify-content:space-between; font-size:12.5px; margin-bottom:5px; font-weight:600;">
                                <span style="color: var(--adm-text-dark);">Wheat (Sharbati & HD-2967)</span>
                                <strong style="color: var(--adm-primary);">9,000 kg (41%)</strong>
                            </div>
                            <div style="height:10px; background:#EDF1E8; border-radius:6px; overflow:hidden;">
                                <div style="width:41%; height:100%; background:var(--adm-primary); border-radius:6px;"></div>
                            </div>
                        </div>
                        <div>
                            <div style="display:flex; justify-content:space-between; font-size:12.5px; margin-bottom:5px; font-weight:600;">
                                <span style="color: var(--adm-text-dark);">Mustard (Pusa Bold & Varuna)</span>
                                <strong style="color: var(--adm-gold-dark);">7,800 kg (35%)</strong>
                            </div>
                            <div style="height:10px; background:#EDF1E8; border-radius:6px; overflow:hidden;">
                                <div style="width:35%; height:100%; background:var(--adm-gold); border-radius:6px;"></div>
                            </div>
                        </div>
                        <div>
                            <div style="display:flex; justify-content:space-between; font-size:12.5px; margin-bottom:5px; font-weight:600;">
                                <span style="color: var(--adm-text-dark);">Basmati Rice 1121</span>
                                <strong style="color: var(--adm-info);">3,000 kg (14%)</strong>
                            </div>
                            <div style="height:10px; background:#EDF1E8; border-radius:6px; overflow:hidden;">
                                <div style="width:14%; height:100%; background:var(--adm-info); border-radius:6px;"></div>
                            </div>
                        </div>
                    </div>
                `;
            }
        },

        // 5.15 SECURITY EVENTS
        renderSecurity: function () {
            const tbody = document.getElementById("tbody-security-events");
            if (!tbody) return;
            tbody.innerHTML = DB.securityEvents.map(s => `
                <tr>
                    <td><code>${s.id}</code></td>
                    <td><strong>${s.type}</strong></td>
                    <td><span class="status-chip ${s.severity === 'Low' ? 'verified' : 'pending'}">${s.severity}</span></td>
                    <td class="mono-text">${s.source}</td>
                    <td>${s.desc}</td>
                    <td>${s.time}</td>
                    <td><span class="status-chip verified">${s.status}</span></td>
                </tr>
            `).join("");
        },

        // 5.16 LOGIN HISTORY
        renderLoginHistory: function () {
            const tbody = document.getElementById("tbody-logins");
            if (!tbody) return;

            // Merge any live logins from login.js / command center
            let list = [...DB.loginHistory];
            try {
                const live = localStorage.getItem("agribridge_live_logins");
                if (live) {
                    const parsed = JSON.parse(live);
                    if (Array.isArray(parsed)) {
                        parsed.forEach(p => {
                            list.unshift({
                                id: `LOG-${Math.floor(1000 + Math.random() * 9000)}`,
                                user: p.email || "Farmer",
                                role: p.role || "farmer",
                                ip: p.ip || "10.228.117.107",
                                device: p.device || "Chrome / Web",
                                time: `Today ${p.time || '12:00 PM'}`,
                                status: "Successful (Auth)"
                            });
                        });
                    }
                }
            } catch (e) {}

            tbody.innerHTML = list.slice(0, 20).map(l => `
                <tr>
                    <td><code>${l.id}</code></td>
                    <td><strong>${l.user}</strong></td>
                    <td><span class="status-chip committed">${l.role.toUpperCase()}</span></td>
                    <td class="mono-text">${l.ip}</td>
                    <td style="color: var(--adm-text-muted);">${l.device}</td>
                    <td>${l.time}</td>
                    <td><span class="status-chip ${l.status.includes('Successful') ? 'verified' : 'high-risk'}">${l.status}</span></td>
                </tr>
            `).join("");
        },

        // 5.17 AUDIT LOGS
        renderAuditLogs: function () {
            const tbody = document.getElementById("tbody-audit-logs");
            if (!tbody) return;

            let list = [...DB.auditLogs];
            try {
                const decisions = localStorage.getItem("agribridge_ai_decisions");
                if (decisions) {
                    const parsed = JSON.parse(decisions);
                    if (Array.isArray(parsed)) {
                        parsed.forEach(d => {
                            list.unshift({
                                id: `DEC-${Math.floor(100 + Math.random() * 900)}`,
                                time: `Today ${d.time || 'Now'}`,
                                actor: "AI Farm Command Center",
                                action: "Multi-Agent Replan",
                                entity: "Farm Telemetry",
                                entityId: "ZONE-A",
                                status: "Executed",
                                details: d.eventHtml ? d.eventHtml.replace(/<[^>]*>?/gm, '') : "Decision recorded."
                            });
                        });
                    }
                }
            } catch (e) {}

            tbody.innerHTML = list.slice(0, 30).map(a => `
                <tr>
                    <td><code>${a.id}</code></td>
                    <td class="mono-text">${a.time}</td>
                    <td><strong>${a.actor}</strong></td>
                    <td><span class="status-chip committed">${a.action}</span></td>
                    <td>${a.entity}</td>
                    <td><code>${a.entityId}</code></td>
                    <td><span class="status-chip verified">${a.status}</span></td>
                    <td>${a.details}</td>
                </tr>
            `).join("");
        },

        // ==================================================================
        // 6. ACTION HANDLERS & MODALS
        // ==================================================================
        setupModals: function () {
            const inspectModal = document.getElementById("admin-inspect-modal");
            const inspectClose = document.getElementById("modal-inspect-close");
            const closeAction = document.getElementById("modal-close-action");

            const decisionModal = document.getElementById("admin-decision-modal");
            const decisionClose = document.getElementById("decision-modal-close");
            const decisionCancel = document.getElementById("decision-cancel-btn");

            [inspectClose, closeAction].forEach(btn => {
                if (btn && inspectModal) {
                    btn.addEventListener("click", () => inspectModal.style.display = "none");
                }
            });

            [decisionClose, decisionCancel].forEach(btn => {
                if (btn && decisionModal) {
                    btn.addEventListener("click", () => decisionModal.style.display = "none");
                }
            });
        },

        inspectItem: function (type, id) {
            const modal = document.getElementById("admin-inspect-modal");
            const catEl = document.getElementById("modal-item-category");
            const titleEl = document.getElementById("modal-item-title");
            const contentEl = document.getElementById("modal-item-content");

            if (!modal || !contentEl) return;

            let html = "";
            catEl.textContent = type.toUpperCase() + " AUDIT VIEW";
            titleEl.textContent = `Record Identifier: ${id}`;

            if (type === "user") {
                const item = DB.users.find(u => u.id === id);
                if (item) {
                    html = `
                        <div class="modal-kv-grid">
                            <div class="modal-kv-item"><div class="modal-kv-label">User ID</div><div class="modal-kv-val">${item.id}</div></div>
                            <div class="modal-kv-item"><div class="modal-kv-label">Full Name</div><div class="modal-kv-val">${item.name}</div></div>
                            <div class="modal-kv-item"><div class="modal-kv-label">Email Address</div><div class="modal-kv-val">${item.email}</div></div>
                            <div class="modal-kv-item"><div class="modal-kv-label">Assigned Role</div><div class="modal-kv-val">${item.role.toUpperCase()}</div></div>
                            <div class="modal-kv-item"><div class="modal-kv-label">Location Territory</div><div class="modal-kv-val">${item.location}</div></div>
                            <div class="modal-kv-item"><div class="modal-kv-label">Account Status</div><div class="modal-kv-val">${item.status.toUpperCase()}</div></div>
                        </div>
                        <p style="color: var(--adm-text-muted); font-size: 12px;">Registered on <strong>${item.createdAt}</strong> · Last activity recorded <strong>${item.lastActive}</strong>.</p>
                    `;
                }
            } else if (type === "listing") {
                const item = DB.listings.find(l => l.id === id);
                if (item) {
                    html = `
                        <div class="modal-kv-grid">
                            <div class="modal-kv-item"><div class="modal-kv-label">Listing ID</div><div class="modal-kv-val">${item.id}</div></div>
                            <div class="modal-kv-item"><div class="modal-kv-label">Crop Name</div><div class="modal-kv-val">${item.crop}</div></div>
                            <div class="modal-kv-item"><div class="modal-kv-label">Farmer</div><div class="modal-kv-val">${item.farmer}</div></div>
                            <div class="modal-kv-item"><div class="modal-kv-label">Location</div><div class="modal-kv-val">${item.location}</div></div>
                            <div class="modal-kv-item"><div class="modal-kv-label">Quantity</div><div class="modal-kv-val">${item.qty}</div></div>
                            <div class="modal-kv-item"><div class="modal-kv-label">Agreed Rate</div><div class="modal-kv-val">${item.price}</div></div>
                            <div class="modal-kv-item"><div class="modal-kv-label">Expected Harvest</div><div class="modal-kv-val">${item.harvestDate}</div></div>
                            <div class="modal-kv-item"><div class="modal-kv-label">AI Confidence</div><div class="modal-kv-val">${item.aiConfidence}</div></div>
                        </div>
                        <div style="background: rgba(46, 125, 50, 0.15); border: 1px solid rgba(46, 125, 50, 0.3); border-radius: 8px; padding: 12px; margin-top: 10px;">
                            <strong>Physical Audit Status:</strong> Verified by ${item.agent}.
                        </div>
                    `;
                }
            } else if (type === "order") {
                const item = DB.orders.find(o => o.id === id);
                if (item) {
                    html = `
                        <div class="modal-kv-grid">
                            <div class="modal-kv-item"><div class="modal-kv-label">Order ID</div><div class="modal-kv-val">${item.id}</div></div>
                            <div class="modal-kv-item"><div class="modal-kv-label">Procuring Buyer</div><div class="modal-kv-val">${item.buyer}</div></div>
                            <div class="modal-kv-item"><div class="modal-kv-label">Farmer Producer</div><div class="modal-kv-val">${item.farmer}</div></div>
                            <div class="modal-kv-item"><div class="modal-kv-label">Crop & Stand</div><div class="modal-kv-val">${item.crop}</div></div>
                            <div class="modal-kv-item"><div class="modal-kv-label">Volume Locked</div><div class="modal-kv-val">${item.qty}</div></div>
                            <div class="modal-kv-item"><div class="modal-kv-label">Total Contract Value</div><div class="modal-kv-val" style="color: var(--adm-gold-light);">${item.amount}</div></div>
                        </div>
                        <p style="color: var(--adm-text-muted); font-size: 12px;">Committed on <strong>${item.date}</strong> · Status: <strong>${item.status}</strong>.</p>
                    `;
                }
            } else if (type === "verification") {
                const item = DB.verifications.find(v => v.id === id);
                if (item) {
                    html = `
                        <div class="modal-kv-grid">
                            <div class="modal-kv-item"><div class="modal-kv-label">Verification ID</div><div class="modal-kv-val">${item.id}</div></div>
                            <div class="modal-kv-item"><div class="modal-kv-label">Farmer</div><div class="modal-kv-val">${item.farmer}</div></div>
                            <div class="modal-kv-item"><div class="modal-kv-label">Crop & Stand</div><div class="modal-kv-val">${item.crop}</div></div>
                            <div class="modal-kv-item"><div class="modal-kv-label">Field Inspector</div><div class="modal-kv-val">${item.agent}</div></div>
                            <div class="modal-kv-item"><div class="modal-kv-label">AI Neural Score</div><div class="modal-kv-val">${item.aiConf}</div></div>
                            <div class="modal-kv-item"><div class="modal-kv-label">Physical Grade</div><div class="modal-kv-val">${item.grade}</div></div>
                        </div>
                        <div style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px; font-size: 12px; margin-top: 10px;">
                            <strong>Auditor Notes:</strong> ${item.notes}
                        </div>
                    `;
                }
            } else {
                html = `<p style="padding: 20px;">Record details loaded for ${id}.</p>`;
            }

            contentEl.innerHTML = html;
            modal.style.display = "flex";
            this.logAudit("Inspected Record", type.toUpperCase(), id, "Success", `Viewed full audit detail of ${id}.`);
        },

        openDecisionModal: function (verifId) {
            const modal = document.getElementById("admin-decision-modal");
            const bodyEl = document.getElementById("decision-modal-body");
            const confirmBtn = document.getElementById("decision-confirm-btn");

            if (!modal || !bodyEl || !confirmBtn) return;

            const item = DB.verifications.find(v => v.id === verifId);
            if (!item) return;

            bodyEl.innerHTML = `
                <p style="margin-bottom: 12px;">You are issuing an official <strong>AgriBridge Digital Quality Verification Seal</strong> for:</p>
                <div class="modal-kv-grid">
                    <div class="modal-kv-item"><div class="modal-kv-label">Verification ID</div><div class="modal-kv-val">${item.id}</div></div>
                    <div class="modal-kv-item"><div class="modal-kv-label">Farmer & Crop</div><div class="modal-kv-val">${item.farmer} · ${item.crop}</div></div>
                    <div class="modal-kv-item"><div class="modal-kv-label">AI Confidence</div><div class="modal-kv-val">${item.aiConf}</div></div>
                    <div class="modal-kv-item"><div class="modal-kv-label">Assigned Inspector</div><div class="modal-kv-val">${item.agent}</div></div>
                </div>
            `;

            confirmBtn.onclick = () => {
                item.status = "Verified";
                item.grade = "Grade A+ (96%)";
                modal.style.display = "none";
                this.renderVerifications();
                this.renderOverview();
                this.logAudit("Approved Verification", "Verification", item.id, "Success", `Issued quality certificate for ${item.crop}.`);
                alert(`✓ Digital Certificate Issued successfully for ${item.crop} (${item.farmer})!`);
            };

            modal.style.display = "flex";
        },

        toggleUserStatus: function (userId) {
            const user = DB.users.find(u => u.id === userId);
            if (!user) return;
            user.status = user.status === "active" ? "suspended" : "active";
            this.renderUsers();
            this.logAudit("Updated User Status", "User", user.id, "Success", `Status toggled to ${user.status}.`);
        },

        logAudit: function (action, entity, entityId, status, details) {
            const now = new Date();
            const timeStr = now.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
            DB.auditLogs.unshift({
                id: `AUD-${Math.floor(100 + Math.random() * 900)}`,
                time: `Today ${timeStr}`,
                actor: "Operations SuperAdmin",
                action: action,
                entity: entity,
                entityId: entityId,
                status: status,
                details: details
            });
            this.renderAuditLogs();
        },

        // ==================================================================
        // 7. CSV REPORT EXPORTER (RFC-4180 ENGINE)
        // ==================================================================
        exportReport: function (type) {
            let filename = `agribridge_${type}_report_${new Date().toISOString().slice(0, 10)}.csv`;
            let csvContent = "";

            if (type === "listings") {
                csvContent = "Listing ID,Crop,Farmer,Location,Quantity,Price,Expected Harvest,AI Confidence,Status\n" +
                    DB.listings.map(l => `"${l.id}","${l.crop}","${l.farmer}","${l.location}","${l.qty}","${l.price}","${l.harvestDate}","${l.aiConfidence}","${l.status}"`).join("\n");
            } else if (type === "orders") {
                csvContent = "Order ID,Buyer,Farmer,Crop,Quantity,Amount,Date,Status\n" +
                    DB.orders.map(o => `"${o.id}","${o.buyer}","${o.farmer}","${o.crop}","${o.qty}","${o.amount}","${o.date}","${o.status}"`).join("\n");
            } else if (type === "verifications") {
                csvContent = "Verification ID,Listing ID,Farmer,Crop,Location,Inspector,AI Confidence,Grade,Status\n" +
                    DB.verifications.map(v => `"${v.id}","${v.listingId}","${v.farmer}","${v.crop}","${v.location}","${v.agent}","${v.aiConf}","${v.grade}","${v.status}"`).join("\n");
            } else if (type === "users") {
                csvContent = "User ID,Name,Email,Role,Location,Status,Created Date\n" +
                    DB.users.map(u => `"${u.id}","${u.name}","${u.email}","${u.role}","${u.location}","${u.status}","${u.createdAt}"`).join("\n");
            } else if (type === "ai") {
                csvContent = "Scan ID,Farm,Crop,Health,Disease Risk,Weather Risk,Confidence,Priority\n" +
                    DB.aiDiagnostics.map(a => `"${a.id}","${a.farm}","${a.crop}","${a.health}","${a.diseaseRisk}","${a.weatherRisk}","${a.conf}","${a.priority}"`).join("\n");
            } else {
                csvContent = "Audit ID,Timestamp,Actor,Action,Entity,Entity ID,Status,Details\n" +
                    DB.auditLogs.map(a => `"${a.id}","${a.time}","${a.actor}","${a.action}","${a.entity}","${a.entityId}","${a.status}","${a.details}"`).join("\n");
            }

            const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
            const link = document.createElement("a");
            const url = URL.createObjectURL(blob);
            link.setAttribute("href", url);
            link.setAttribute("download", filename);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            this.logAudit("Exported CSV Dataset", "Reports", type.toUpperCase(), "Success", `Downloaded ${filename}`);
            alert(`✓ ${filename} generated and downloaded successfully!`);
        },

        setupSettingsForm: function () {
            const form = document.getElementById("admin-settings-form");
            if (!form) return;
            form.addEventListener("submit", (e) => {
                e.preventDefault();
                this.logAudit("Updated Platform Settings", "Settings", "PLATFORM-CONFIG", "Success", "Saved operational thresholds.");
                alert("✓ Platform Operational Settings saved successfully!");
            });

            // Connect individual export buttons
            document.getElementById("btn-export-users")?.addEventListener("click", () => this.exportReport("users"));
            document.getElementById("btn-export-farmers")?.addEventListener("click", () => this.exportReport("users"));
            document.getElementById("btn-export-buyers")?.addEventListener("click", () => this.exportReport("users"));
            document.getElementById("btn-export-agents")?.addEventListener("click", () => this.exportReport("users"));
            document.getElementById("btn-export-listings")?.addEventListener("click", () => this.exportReport("listings"));
            document.getElementById("btn-export-verifications")?.addEventListener("click", () => this.exportReport("verifications"));
            document.getElementById("btn-export-orders")?.addEventListener("click", () => this.exportReport("orders"));
            document.getElementById("btn-export-logins")?.addEventListener("click", () => this.exportReport("audits"));
            document.getElementById("btn-export-audits")?.addEventListener("click", () => this.exportReport("audits"));
        },

        checkBackendHealth: function () {
            const badge = document.getElementById("health-api-badge");
            const statusText = document.getElementById("health-api-status");
            if (!badge || !statusText) return;

            fetch(`${API_BASE_URL}/api/listings/`, { method: "GET" })
                .then(res => {
                    if (res.ok) {
                        badge.className = "health-badge online";
                        badge.textContent = "● Connected (Live)";
                        statusText.textContent = "FastAPI Gateway Online (Port 8000)";
                    } else {
                        badge.className = "health-badge";
                        badge.textContent = "● Standalone Web Bus";
                    }
                })
                .catch(() => {
                    badge.className = "health-badge";
                    badge.textContent = "● Local Web Bus (Active)";
                });
        },

        attachFilterListener: function (id, callback) {
            const el = document.getElementById(id);
            if (el && !el._attached) {
                el.addEventListener("change", callback);
                el._attached = true;
            }
        },

        attachInputListener: function (id, callback) {
            const el = document.getElementById(id);
            if (el && !el._attached) {
                el.addEventListener("input", callback);
                el._attached = true;
            }
        }
    };

    // Expose to window for inline onclick handlers
    window.AdminApp = AdminApp;

    document.addEventListener("DOMContentLoaded", () => {
        AdminApp.init();
    });

})();

