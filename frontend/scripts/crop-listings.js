// =============================================================================
// AGRIBRIDGE — TWO-PHASE MARKETPLACE GUIDANCE & LISTINGS JS
// 1. PRE-HARVEST MARKETPLACE (Market intel, benchmark rates, pre-harvest listing)
// 2. POST-HARVEST — CLEANED CROP (Cleaning protocols, quality grading, potential premium)
// =============================================================================

// Cleaning Protocols Reference Data
const CROP_PROTOCOLS = {
    wheat: {
        name: "Wheat (गेहूं)",
        base_price: 2275,
        cleaning_steps: [
            "Sieve harvested grain with standard 2mm mesh to remove chaff, weed seeds, and small stones.",
            "Use winnowing fan or gentle wind to blow away light husk and dust."
        ],
        drying_steps: "Sun dry grain on clean tarpaulin for 1-2 days until moisture drops below 12%. Avoid drying directly on bare soil.",
        sorting_steps: "Remove broken grains, shriveled kernels, and discolored seeds manually or using grading screens.",
        grade_a_hint: "Moisture ≤ 12%, Foreign Matter ≤ 1.0%, Defects ≤ 2.0%"
    },
    rice: {
        name: "Rice / Paddy (धान)",
        base_price: 2183,
        cleaning_steps: [
            "Pass paddy through scalper / sieve cleaner to remove straw, mud balls, and stones.",
            "Aspirate chaff and immature unfilled grains using winnowing airflow."
        ],
        drying_steps: "Gradual shade/sun drying with frequent turning until grain moisture reaches 13-14% to prevent kernel cracking.",
        sorting_steps: "Separate immature greenish grains, chalky grains, and foreign paddy seeds.",
        grade_a_hint: "Moisture ≤ 14%, Foreign Matter ≤ 1.0%, Defects ≤ 3.0%"
    },
    tomato: {
        name: "Tomato (टमाटर)",
        base_price: 1850,
        cleaning_steps: [
            "Gently wipe fruit with clean dry cotton cloth or wash with clean potable water to remove field dirt.",
            "Air dry in shaded, well-ventilated area before packing."
        ],
        drying_steps: "Do not sun dry fresh market tomatoes. Surface dry only in shade for 1 hour to prevent surface mold.",
        sorting_steps: "Sort by uniform size and color (breaker/turning/red). Eliminate cracked, bruised, punctured, or pest-blemished fruit.",
        grade_a_hint: "Foreign Matter = 0%, Defects ≤ 3.0%, Uniformity ≥ 90%"
    },
    potato: {
        name: "Potato (आलू)",
        base_price: 1400,
        cleaning_steps: [
            "Cure tubers in cool shaded dry area for 7-10 days to toughen skin.",
            "Gently brush off dry soil without skinning or damaging the tuber surface."
        ],
        drying_steps: "Cure and dry in dark, dry room (15-20°C). Never expose to direct sunlight to prevent greening (solanine).",
        sorting_steps: "Remove green-tinted, cut, diseased, or rotten tubers. Grade by size: Large (>60mm), Medium (45-60mm), Small (<45mm).",
        grade_a_hint: "Moisture ≤ 80%, Foreign Matter ≤ 1.0%, Defects ≤ 3.0%"
    },
    corn: {
        name: "Corn / Maize (मक्का)",
        base_price: 2090,
        cleaning_steps: [
            "De-husk ears and shell kernels carefully to minimize mechanical embryo damage.",
            "Screen through dual sieve to eliminate cob fragments, dust, and weed seeds."
        ],
        drying_steps: "Dry kernels on clean surface under sun until moisture reaches 12-13.5%.",
        sorting_steps: "Pick out moldy, discolored, weevil-bored, and broken kernels.",
        grade_a_hint: "Moisture ≤ 13.5%, Foreign Matter ≤ 1.5%, Defects ≤ 2.5%"
    },
    soybean: {
        name: "Soybean (सोयाबीन)",
        base_price: 4600,
        cleaning_steps: [
            "Aspirate and screen to eliminate pods, stalks, soil lumps, and split seed coats.",
            "Run through spiral separator if available for uniform round seed sorting."
        ],
        drying_steps: "Sun dry on tarpaulin, turning every 2 hours until moisture stabilizes at 10-12%.",
        sorting_steps: "Remove split, shriveled, green, and diseased seeds.",
        grade_a_hint: "Moisture ≤ 11%, Foreign Matter ≤ 1.0%, Defects ≤ 2.0%"
    }
};

// =============================================================================
// PHASE SWITCHER LOGIC
// =============================================================================

function switchMarketplacePhase(phase) {
    const tabPre = document.getElementById("tab-btn-pre-harvest");
    const tabPost = document.getElementById("tab-btn-post-harvest");
    const panelPre = document.getElementById("panel-pre-harvest");
    const panelPost = document.getElementById("panel-post-harvest");

    if (phase === "pre-harvest") {
        tabPre.classList.add("active");
        tabPost.classList.remove("active");
        panelPre.classList.add("active");
        panelPost.classList.remove("active");
    } else {
        tabPost.classList.add("active");
        tabPre.classList.remove("active");
        panelPost.classList.add("active");
        panelPre.classList.remove("active");
    }
}

// =============================================================================
// INITIALIZE PRE-HARVEST DATA & LISTING
// =============================================================================

document.addEventListener("DOMContentLoaded", () => {
    loadPreHarvestData();
    updateCropCleaningProtocol();
});

function loadPreHarvestData() {
    const savedCropData = localStorage.getItem("cropData");
    const savedCropImage = localStorage.getItem("cropImage");

    const cropNameEl = document.getElementById("crop-name");
    const cropQuantityEl = document.getElementById("crop-quantity");
    const harvestDateEl = document.getElementById("harvest-date");
    const cropLocationEl = document.getElementById("crop-location");
    const cropImageEl = document.getElementById("crop-image");
    const verificationStatusEl = document.getElementById("verification-status");
    const buyerStatusEl = document.getElementById("buyer-status");

    let cropName = "Wheat";

    if (savedCropData) {
        try {
            const cropData = JSON.parse(savedCropData);
            cropName = cropData.cropName || cropData.crop_type || "Wheat";
            if (cropNameEl) cropNameEl.textContent = cropName;
            if (cropQuantityEl) cropQuantityEl.textContent = (cropData.quantity || cropData.quantity_est || "1200") + " kg";
            if (harvestDateEl) harvestDateEl.textContent = cropData.harvestDate || cropData.harvest_date || "28 Mar 2026";
            if (cropLocationEl) cropLocationEl.textContent = cropData.location || "Plot A-4, North Field";

            const status = cropData.status || "pending";
            if (verificationStatusEl) {
                if (status === "verified" || status === "active") {
                    verificationStatusEl.textContent = "✓ Verified";
                    verificationStatusEl.className = "status-chip-view verified";
                } else {
                    verificationStatusEl.textContent = "Pending";
                    verificationStatusEl.className = "status-chip-view pending";
                }
            }

            if (buyerStatusEl) {
                if (status === "committed") {
                    buyerStatusEl.textContent = "🤝 Buyer Committed";
                    buyerStatusEl.className = "status-chip-view committed";
                } else {
                    buyerStatusEl.textContent = "No Buyer Yet";
                    buyerStatusEl.className = "status-chip-view pending";
                }
            }
        } catch (e) {
            console.warn("Could not parse savedCropData", e);
        }
    }

    if (savedCropImage && cropImageEl) {
        cropImageEl.src = savedCropImage;
    }

    // Attempt to fetch fresh guidance from backend
    fetch(`/api/marketplace/guidance/${encodeURIComponent(cropName.toLowerCase())}`)
        .then(res => res.json())
        .then(data => {
            if (data.success && data.data && data.data.pre_harvest_marketplace) {
                const pre = data.data.pre_harvest_marketplace;
                const mandiPriceEl = document.getElementById("intel-mandi-price");
                const mandiLocEl = document.getElementById("intel-market-loc");
                const trendEl = document.getElementById("intel-trend");
                const guidanceTextEl = document.getElementById("preharvest-selling-guidance-text");

                if (mandiPriceEl) mandiPriceEl.textContent = `₹${pre.mandi_price_per_quintal.toLocaleString()} / qtl`;
                if (mandiLocEl) mandiLocEl.textContent = pre.local_market_info;
                if (trendEl) trendEl.textContent = `📈 ${pre.market_trend} (${pre.price_change_trend})`;
                if (guidanceTextEl && pre.selling_time_guidance) {
                    guidanceTextEl.textContent = pre.selling_time_guidance;
                }
            }
        })
        .catch(err => {
            console.log("Using default pre-harvest guidance intelligence", err);
        });
}

// =============================================================================
// CROP CLEANING PROTOCOL UPDATER
// =============================================================================

function updateCropCleaningProtocol() {
    const select = document.getElementById("protocol-crop-select");
    const cropKey = select ? select.value : "wheat";
    const proto = CROP_PROTOCOLS[cropKey] || CROP_PROTOCOLS.wheat;

    const cleaningList = document.getElementById("proto-cleaning-steps");
    const dryingText = document.getElementById("proto-drying-steps");
    const sortingText = document.getElementById("proto-sorting-steps");
    const basePriceInput = document.getElementById("calc-base-price");

    if (cleaningList) {
        cleaningList.innerHTML = proto.cleaning_steps.map(s => `<li>${s}</li>`).join("");
    }
    if (dryingText) {
        dryingText.textContent = proto.drying_steps;
    }
    if (sortingText) {
        sortingText.textContent = proto.sorting_steps;
    }
    if (basePriceInput && proto.base_price) {
        basePriceInput.value = proto.base_price;
    }
}

// =============================================================================
// QUALITY ASSESSMENT & POTENTIAL PREMIUM CALCULATOR
// =============================================================================

async function calculateQualityAssessment(event) {
    if (event) event.preventDefault();

    const cropSelect = document.getElementById("protocol-crop-select");
    const cropName = cropSelect ? cropSelect.value : "wheat";
    const targetGrade = document.getElementById("calc-target-grade").value;
    const basePrice = parseFloat(document.getElementById("calc-base-price").value) || 2275.0;
    const moisture = parseFloat(document.getElementById("calc-moisture").value) || 12.0;
    const foreignMatter = parseFloat(document.getElementById("calc-foreign-matter").value) || 1.0;
    const defects = parseFloat(document.getElementById("calc-defects").value) || 2.0;
    const uniformity = parseFloat(document.getElementById("calc-uniformity").value) || 90.0;

    const btn = document.getElementById("btn-assess-quality");
    if (btn) {
        btn.disabled = true;
        btn.textContent = "⏳ Assessing Quality Parameters...";
    }

    try {
        const response = await fetch("/api/marketplace/quality-assessment", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                crop_name: cropName,
                target_grade: targetGrade,
                base_price: basePrice,
                moisture_pct: moisture,
                foreign_matter_pct: foreignMatter,
                defects_pct: defects,
                uniformity_pct: uniformity
            })
        });

        const resData = await response.json();
        if (resData.success && resData.data) {
            displayAssessmentResult(resData.data);
        } else {
            fallbackLocalAssessment(targetGrade, basePrice, moisture, foreignMatter, defects);
        }
    } catch (e) {
        console.warn("Backend assessment API unreachable, using local evaluation", e);
        fallbackLocalAssessment(targetGrade, basePrice, moisture, foreignMatter, defects);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = "🔬 Calculate Quality Grade & Potential Premium";
        }
    }
}

function displayAssessmentResult(data) {
    const resultBox = document.getElementById("quality-result-box");
    const targetGradeEl = document.getElementById("res-target-grade");
    const achievedGradeEl = document.getElementById("res-achieved-grade");
    const basePriceEl = document.getElementById("res-base-price");
    const premiumPriceEl = document.getElementById("res-premium-price");
    const premiumPctEl = document.getElementById("res-premium-pct");
    const explanationEl = document.getElementById("res-explanation");

    if (targetGradeEl) targetGradeEl.textContent = data.target_grade;
    if (achievedGradeEl) {
        achievedGradeEl.textContent = data.achieved_grade;
        achievedGradeEl.className = data.achieved_grade === "Grade A" ? "grade-highlight text-success" : "grade-highlight";
    }
    if (basePriceEl) basePriceEl.textContent = `₹${data.base_mandi_price.toLocaleString()} / qtl`;
    if (premiumPriceEl) {
        premiumPriceEl.textContent = `₹${data.potential_premium_price.toLocaleString()} / qtl`;
    }
    if (premiumPctEl) {
        const pct = data.premium_multiplier_pct;
        premiumPctEl.textContent = pct > 0 ? `+${pct}% Potential Upside` : "Base Mandi Benchmark";
    }
    if (explanationEl) {
        explanationEl.textContent = data.explanation;
    }

    if (resultBox) {
        resultBox.style.display = "flex";
        resultBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
}

function fallbackLocalAssessment(targetGrade, basePrice, moisture, foreignMatter, defects) {
    let achieved = "Grade C";
    let premiumMult = 0;
    let explanation = "Lot meets Grade C basic commercial standard.";

    if (moisture <= 12.0 && foreignMatter <= 1.0 && defects <= 2.0) {
        achieved = "Grade A";
        premiumMult = 20;
        explanation = "Cleaned lot satisfies all Grade A criteria (Moisture ≤ 12%, Foreign Matter ≤ 1.0%, Defects ≤ 2.0%).";
    } else if (moisture <= 14.0 && foreignMatter <= 2.5 && defects <= 5.0) {
        achieved = "Grade B";
        premiumMult = 8;
        explanation = "Cleaned lot satisfies Grade B criteria with moderate cleaning and sorting.";
    }

    const premiumPrice = Math.round(basePrice * (1 + premiumMult / 100));

    displayAssessmentResult({
        target_grade: targetGrade,
        achieved_grade: achieved,
        base_mandi_price: basePrice,
        potential_premium_price: premiumPrice,
        premium_multiplier_pct: premiumMult,
        explanation: explanation
    });
}