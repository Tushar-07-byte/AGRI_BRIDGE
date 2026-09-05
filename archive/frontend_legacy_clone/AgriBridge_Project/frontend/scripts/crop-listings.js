// ==========================================================================
// AGRIBRIDGE — FARMER CROP LISTINGS
// Multi-Crop Catalog, Original Farm Photos & Real-Time Sync
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
    "use strict";

    const container = document.getElementById("farmer-listings-grid");
    if (!container) return;

    // 1. BASE REGISTERED FARM CROPS CATALOG WITH REAL HIGH-RES FARM PHOTOS
    const FARMER_CROPS = [
        {
            id: 1,
            cropName: "Golden Sharbati Wheat",
            category: "Cereal / Grain",
            quantity: "5,000 kg",
            harvestDate: "15 Oct 2026",
            location: "Raipur, Chhattisgarh",
            price: "₹ 27 / kg",
            status: "committed",
            buyerName: "FreshBazaar Retail Pvt Ltd",
            confidence: "95%",
            image: "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=800&auto=format&fit=crop&q=80",
            certId: "AGB-CERT-2026-081"
        },
        {
            id: 2,
            cropName: "Basmati 1121 Paddy Rice",
            category: "Cereal / Aromatic",
            quantity: "3,500 kg",
            harvestDate: "20 Oct 2026",
            location: "Bathinda, Punjab",
            price: "₹ 75 / kg",
            status: "verified",
            buyerName: null,
            confidence: "96%",
            image: "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=800&auto=format&fit=crop&q=80",
            certId: "AGB-CERT-2026-082"
        },
        {
            id: 3,
            cropName: "Pusa Bold Yellow Mustard",
            category: "Oilseed",
            quantity: "4,000 kg",
            harvestDate: "05 Nov 2026",
            location: "Kota, Rajasthan",
            price: "₹ 58 / kg",
            status: "committed",
            buyerName: "AgriCorp Global Procurement",
            confidence: "94%",
            image: "https://images.unsplash.com/photo-1508747703725-719777637510?w=800&auto=format&fit=crop&q=80",
            certId: "AGB-CERT-2026-083"
        },
        {
            id: 4,
            cropName: "Organic High-Protein Soybean (JS 335)",
            category: "Legume / Pulse",
            quantity: "3,000 kg",
            harvestDate: "18 Oct 2026",
            location: "Rajnandgaon, Chhattisgarh",
            price: "₹ 42 / kg",
            status: "verified",
            buyerName: null,
            confidence: "93%",
            image: "https://images.unsplash.com/photo-1595855759920-86582396756a?w=800&auto=format&fit=crop&q=80",
            certId: "AGB-CERT-2026-084"
        },
        {
            id: 5,
            cropName: "Hybrid Maize & Sweet Corn (HQPM-1)",
            category: "Cereal / Fodder",
            quantity: "4,500 kg",
            harvestDate: "25 Oct 2026",
            location: "Raipur North, Chhattisgarh",
            price: "₹ 22 / kg",
            status: "verified",
            buyerName: null,
            confidence: "91%",
            image: "https://images.unsplash.com/photo-1551754655-cd27e38d2076?w=800&auto=format&fit=crop&q=80",
            certId: "AGB-CERT-2026-085"
        },
        {
            id: 6,
            cropName: "Long-Staple BT Cotton",
            category: "Commercial Fiber",
            quantity: "3,200 kg",
            harvestDate: "12 Nov 2026",
            location: "Nagpur, Maharashtra",
            price: "₹ 68 / kg",
            status: "verified",
            buyerName: null,
            confidence: "95%",
            image: "https://images.unsplash.com/photo-1606041008023-472dfb5e530f?w=800&auto=format&fit=crop&q=80",
            certId: "AGB-CERT-2026-086"
        },
        {
            id: 7,
            cropName: "High Brix Sugarcane (Co 0238)",
            category: "Cash Crop",
            quantity: "8,000 kg",
            harvestDate: "28 Nov 2026",
            location: "Karnal, Haryana",
            price: "₹ 34 / kg",
            status: "verified",
            buyerName: null,
            confidence: "96%",
            image: "https://images.unsplash.com/photo-1605000797499-95a51c5269ae?w=800&auto=format&fit=crop&q=80",
            certId: "AGB-CERT-2026-087"
        },
        {
            id: 8,
            cropName: "Kufri Jyoti Table & Processing Potato",
            category: "Tuber / Vegetable",
            quantity: "3,800 kg",
            harvestDate: "30 Oct 2026",
            location: "Varanasi, Uttar Pradesh",
            price: "₹ 16 / kg",
            status: "verified",
            buyerName: null,
            confidence: "92%",
            image: "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=800&auto=format&fit=crop&q=80",
            certId: "AGB-CERT-2026-088"
        },
        {
            id: 9,
            cropName: "Vine-Ripened Himsona Tomato",
            category: "Horticulture",
            quantity: "1,800 kg",
            harvestDate: "10 Oct 2026",
            location: "Bilaspur, Chhattisgarh",
            price: "₹ 18 / kg",
            status: "verified",
            buyerName: null,
            confidence: "96%",
            image: "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=800&auto=format&fit=crop&q=80",
            certId: "AGB-CERT-2026-089"
        },
        {
            id: 10,
            cropName: "Red Nasik Onion (Pre-Harvest)",
            category: "Bulb Vegetable",
            quantity: "4,200 kg",
            harvestDate: "15 Nov 2026",
            location: "Nashik, Maharashtra",
            price: "₹ 24 / kg",
            status: "verified",
            buyerName: null,
            confidence: "95%",
            image: "https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=800&auto=format&fit=crop&q=80",
            certId: "AGB-CERT-2026-090"
        },
        {
            id: 11,
            cropName: "Durum Malwa Gold Amber Wheat",
            category: "Cereal / Grain",
            quantity: "6,000 kg",
            harvestDate: "28 Oct 2026",
            location: "Indore, Madhya Pradesh",
            price: "₹ 29 / kg",
            status: "verified",
            buyerName: null,
            confidence: "96%",
            image: "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?w=800&auto=format&fit=crop&q=80",
            certId: "AGB-CERT-2026-091"
        },
        {
            id: 12,
            cropName: "Guntur Sannam Red Chilli",
            category: "Commercial Spice",
            quantity: "2,500 kg",
            harvestDate: "08 Nov 2026",
            location: "Guntur, Andhra Pradesh",
            price: "₹ 32 / kg",
            status: "verified",
            buyerName: null,
            confidence: "94%",
            image: "https://images.unsplash.com/photo-1588252303782-cb80119abd6d?w=800&auto=format&fit=crop&q=80",
            certId: "AGB-CERT-2026-092"
        }
    ];

    // 2. CHECK IF USER UPLOADED A CUSTOM CROP VIA UPLOAD PAGE
    try {
        const savedCropData = localStorage.getItem("cropData");
        const savedCropImage = localStorage.getItem("cropImage");
        if (savedCropData) {
            const parsed = JSON.parse(savedCropData);
            if (parsed && parsed.cropName) {
                FARMER_CROPS.unshift({
                    id: 100,
                    cropName: parsed.cropName,
                    category: parsed.category || "Custom Farm Lot",
                    quantity: `${parsed.quantity || 2000} kg`,
                    harvestDate: parsed.harvestDate || "30 Oct 2026",
                    location: parsed.location || "Raipur, Chhattisgarh",
                    price: `₹ ${parsed.price || 28} / kg`,
                    status: parsed.status || "verified",
                    buyerName: null,
                    confidence: `${parsed.confidence || 94}%`,
                    image: savedCropImage || "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=800&auto=format&fit=crop&q=80",
                    certId: "AGB-CERT-2026-099"
                });
            }
        }
    } catch (e) {
        console.warn("Custom crop load error:", e);
    }

    // 3. RENDER ALL CROPS INTO MODERN SHOWCASE CARDS
    container.innerHTML = FARMER_CROPS.map(c => {
        const isCommitted = c.status === "committed";
        const statusBadge = isCommitted
            ? `<span class="ab-badge ab-badge-gold">🤝 Committed (${c.buyerName || 'Verified Buyer'})</span>`
            : `<span class="ab-badge ab-badge-verified">✓ Field Agent Verified</span>`;

        return `
            <section class="listing-showcase-card" style="margin-bottom: 24px;">
                <div class="listing-image-container">
                    <img src="${c.image}" alt="${c.cropName}" class="crop-img-view" onerror="this.src='https://images.unsplash.com/photo-1500937386664-56d1dfef3854?w=800&auto=format&fit=crop&q=80'">
                    <div class="listing-badge-overlay">
                        <span class="ab-badge ab-badge-verified">🧠 AI Conf: ${c.confidence}</span>
                    </div>
                </div>

                <div class="listing-details-col">
                    <div class="listing-title-row">
                        <h2 class="crop-title">${c.cropName}</h2>
                        <span class="crop-category-tag">${c.category}</span>
                    </div>

                    <div class="details-grid-box">
                        <div class="detail-stat-item">
                            <span>Estimated Quantity</span>
                            <strong>${c.quantity}</strong>
                        </div>
                        <div class="detail-stat-item">
                            <span>Target Harvest Date</span>
                            <strong>${c.harvestDate}</strong>
                        </div>
                        <div class="detail-stat-item">
                            <span>Pre-Harvest Rate</span>
                            <strong style="color: var(--ab-primary-green);">${c.price}</strong>
                        </div>
                        <div class="detail-stat-item">
                            <span>Farm Location</span>
                            <strong>${c.location}</strong>
                        </div>
                    </div>

                    <div class="status-badges-row">
                        <div class="status-box">
                            <span class="status-box-label">Certificate ID:</span>
                            <code style="background: #EBF3E7; color: #315C2A; padding: 3px 8px; border-radius: 4px; font-weight: 700;">${c.certId}</code>
                        </div>
                        <div class="status-box">
                            <span class="status-box-label">Marketplace Status:</span>
                            ${statusBadge}
                        </div>
                    </div>

                    <div class="listing-actions-row">
                        <button class="stylish-btn ab-btn-secondary" onclick="window.location.href='/frontend/pages/ai-result.html'">
                            🩺 View AI Diagnostics
                        </button>
                        <button class="stylish-btn ab-btn-primary" onclick="window.location.href='/frontend/pages/orders.html'">
                            📦 View Commitments
                        </button>
                    </div>
                </div>
            </section>
        `;
    }).join("");
});