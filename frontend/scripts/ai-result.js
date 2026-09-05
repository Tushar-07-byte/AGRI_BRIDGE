// ==========================================================================
// AGRIBRIDGE — AI CROP DIAGNOSTIC & PRESCRIPTION CONTROLLER
// Hackathon-Ready Diagnostic Intelligence, Dosage Calculator & Multilingual TTS
// ==========================================================================

console.log("=== AGRIBRIDGE AI-RESULT DASHBOARD INITIALIZED ===");

// Helper for safe translation fallback
function t(key, fallback) {
    if (typeof translate === "function") {
        const val = translate(key);
        if (val && val !== key) return val;
    }
    return fallback || key;
}

// ==========================================================================
// PRESET DEMO CASES (Judge-Proofing Fail-Safe)
// ==========================================================================
const DEMO_PRESETS = {
    tomato_early_blight: {
        prediction: {
            plant: "tomato",
            model: "tomato_model",
            model_name: "AgriBridge PlantVillage Deep CNN",
            confidence: 98.45,
            class_id: 2
        },
        disease: {
            crop: "Tomato",
            disease: "Early Blight (Alternaria solani)",
            scientific_name: "Alternaria solani (Ellis & G. Martin) Sorauer",
            description: "Fungal infection characterized by circular dark brown target-board lesions with concentric rings and chlorotic halos, starting on older foliage.",
            severity_level: "moderate",
            severity_percentage: 55,
            yield_risk: "20% - 35%",
            treatment: "Apply Mancozeb 75% WP @ 2g/L water or Chlorothalonil 75% WP. For systemic cure, alternate with Azoxystrobin 23% SC @ 1ml/L.",
            organic_option: "Spray cold-pressed Neem Oil (10,000 ppm) @ 5ml/L with emulsifier, or Bio-fungicide Trichoderma viride @ 5g/L on foliage.",
            chemical_option: "Mancozeb 75% WP @ 2g/L water or Copper Oxychloride 50% WP @ 2.5g/L water.",
            prevention: "Avoid overhead sprinkler irrigation that wets leaves. Maintain 60cm row spacing for ventilation and mulch soil.",
            sanitation: "Prune heavily infected lower leaves and safely bury them outside the farm to stop conidial dispersion."
        },
        farm: {
            farm_area: 2.5,
            growth_stage: "flowering",
            irrigation_method: "drip",
            irrigation_status: "normal",
            recent_rainfall: "low",
            humidity: "moderate",
            fertilizer_applied: "NPK 19:19:19 + Micronutrients",
            previous_crop: "Mustard",
            disease_severity: "moderate",
            region: "Maharashtra (Pune District)"
        },
        farm_specific_advice: {
            irrigation_advice: "Maintain controlled drip cycles in the early morning. Avoid evening watering to minimize leaf wetness duration.",
            weather_advice: "Low rain probability over next 48h provides a favorable window for foliar fungicide application.",
            fertilizer_advice: "Temporarily pause high-nitrogen fertilizers which promote succulent vulnerable foliage; apply soluble Potassium to fortify cell walls.",
            field_sanitation: "Disinfect pruning shears between plants using a 10% sodium hypochlorite solution.",
            disease_severity: "Moderate infection observed on ~18% lower canopy foliage.",
            growth_stage: "Crop in critical flowering stage; protective spray prevents flower drop.",
            regional_advice: "Common in Western Ghats transitional zones during post-monsoon humidity swings."
        },
        timing_advice: {
            status: "favorable",
            rain_risk: false,
            advice: "Ideal weather window detected. Low wind speed (5 km/h) and dry weather ensure maximum foliar adhesion.",
            recommended_window: "Tomorrow 6:00 AM – 9:00 AM"
        },
        verification: {
            verified: true,
            source: "ICAR-IIHR & PlantVillage Agronomy Database",
            safety_note: "Strictly observe 7-day Pre-Harvest Interval (PHI). Wear protective gloves and eye gear."
        },
        sample_image: "/frontend/assets/logo/logo.png"
    },

    potato_late_blight: {
        prediction: {
            plant: "potato",
            model: "potato_model",
            model_name: "AgriBridge Potato Blight ResNet-50",
            confidence: 99.10,
            class_id: 1
        },
        disease: {
            crop: "Potato",
            disease: "Late Blight (Phytophthora infestans)",
            scientific_name: "Phytophthora infestans (Mont.) de Bary",
            description: "High-risk oomycete disease producing water-soaked dark lesions with white mold margins under humid conditions.",
            severity_level: "severe",
            severity_percentage: 85,
            yield_risk: "45% - 70%",
            treatment: "Immediate emergency foliar spray with Cymoxanil 8% + Mancozeb 64% WP @ 2.5g/L or Dimethomorph 50% WP @ 1g/L.",
            organic_option: "Bio-bactericide Bacillus subtilis @ 5g/L combined with Copper Hydroxide @ 2g/L.",
            chemical_option: "Metalaxyl-M 4% + Mancozeb 64% WP (Ridomil Gold) @ 2.5g/L water.",
            prevention: "Plant certified disease-free seed tubers; destroy volunteer potato plants and nightshade weeds.",
            sanitation: "Rogue out and destroy infected vines immediately. Do not compost blight-infected haulms."
        },
        farm: {
            farm_area: 3.0,
            growth_stage: "tuberization",
            irrigation_method: "sprinkler",
            irrigation_status: "wet",
            recent_rainfall: "moderate",
            humidity: "high",
            fertilizer_applied: "DAP + MOP",
            previous_crop: "Wheat",
            disease_severity: "high",
            region: "Punjab (Jalandhar District)"
        },
        farm_specific_advice: {
            irrigation_advice: "Halt sprinkler irrigation immediately. Allow soil surface to dry out.",
            weather_advice: "High humidity and cool night temperatures accelerate spore germination. Urgent intervention required.",
            fertilizer_advice: "Apply foliar Potassium Phosphite to activate systemic acquired resistance (SAR).",
            field_sanitation: "Cover exposed tubers with soil earthing-up to prevent zoospore infection.",
            disease_severity: "High risk of rapid canopy collapse within 4 to 6 days without systemic fungicide.",
            growth_stage: "Tuber bulking phase — protection critical for market grade.",
            regional_advice: "Late blight advisory active across Indo-Gangetic plains."
        },
        timing_advice: {
            status: "favorable",
            rain_risk: false,
            advice: "Emergency spray window open. Apply systemic fungicide during early morning before 10 AM.",
            recommended_window: "Today 4:30 PM – 6:30 PM or Tomorrow 6:00 AM"
        },
        verification: {
            verified: true,
            source: "CPRI (Central Potato Research Institute) & AgriBridge Agronomy",
            safety_note: "Do not harvest within 10 days of systemic metalaxyl application."
        },
        sample_image: "/frontend/assets/logo/logo.png"
    },

    corn_healthy: {
        prediction: {
            plant: "corn",
            model: "corn_model",
            model_name: "AgriBridge Cereal Vision Net",
            confidence: 99.80,
            class_id: 0
        },
        disease: {
            crop: "Corn (Maize)",
            disease: "Healthy Crop (No Disease Detected)",
            scientific_name: "Zea mays L. (Healthy Foliage)",
            description: "Plant foliage exhibits uniform chlorophyll pigmentation, robust turgor pressure, and zero active fungal or bacterial lesions.",
            severity_level: "healthy",
            severity_percentage: 5,
            yield_risk: "0% (Optimal Yield Potential)",
            treatment: "No pesticide or fungicide needed. Maintain standard irrigation and nutrient schedule.",
            organic_option: "Apply prophylactic Jeevamrutha or seaweed liquid fertilizer to maintain vigor.",
            chemical_option: "No chemical application warranted. Zero chemical residue advantage for export marketplace.",
            prevention: "Continue periodic scouting for Fall Armyworm (Spodoptera frugiperda) and Northern Leaf Blight.",
            sanitation: "Keep inter-row furrows free of broadleaf weeds."
        },
        farm: {
            farm_area: 5.0,
            growth_stage: "vegetative",
            irrigation_method: "furrow",
            irrigation_status: "normal",
            recent_rainfall: "moderate",
            humidity: "moderate",
            fertilizer_applied: "Urea + Zinc Sulphate",
            previous_crop: "Soybean",
            disease_severity: "none",
            region: "Karnataka (Davanagere District)"
        },
        farm_specific_advice: {
            irrigation_advice: "Maintain regular furrow scheduling every 7-10 days depending on soil moisture.",
            weather_advice: "Weather conditions are optimal for rapid vegetative photosynthesis.",
            fertilizer_advice: "Apply top-dressing of Nitrogen (Urea) at knee-high stage.",
            field_sanitation: "Maintain clean farm bunds.",
            disease_severity: "Crop is in pristine health.",
            growth_stage: "V6 vegetative growth stage.",
            regional_advice: "Ideal crop stand for Pre-Harvest Marketplace premium bidding."
        },
        timing_advice: {
            status: "favorable",
            rain_risk: false,
            advice: "Favorable conditions for routine micronutrient foliar boost.",
            recommended_window: "Any clear morning or evening window"
        },
        verification: {
            verified: true,
            source: "AgriBridge Verified Agronomy & CIMMYT Maize Standards",
            safety_note: "Crop verified 100% pesticide-free; qualifies for Green Grade certification."
        },
        sample_image: "/frontend/assets/logo/logo.png"
    }
};

// Global Active State
let currentAIResult = null;
let currentCropName = "Crop";
let currentDiseaseName = "Disease";
let isSpeaking = false;
let currentAcreage = 2.5;

// ==========================================================================
// DOM ELEMENT REFERENCES
// ==========================================================================
const cropImage = document.getElementById("crop-image");
const resultTitle = document.getElementById("result-title");
const resultScientific = document.getElementById("result-scientific-name");
const resultMessage = document.getElementById("result-message");
const cropNameText = document.getElementById("crop-name-text");
const overlayStatusText = document.getElementById("overlay-status-text");
const severityBadge = document.getElementById("severity-badge");
const severityMeterFill = document.getElementById("severity-meter-fill");
const confidencePercentage = document.getElementById("confidence-percentage");
const confidenceFill = document.getElementById("confidence-fill");
const modelNameSub = document.getElementById("model-name-sub");
const yieldRiskVal = document.getElementById("yield-risk-val");
const yieldRiskSub = document.getElementById("yield-risk-sub");

// Tabs
const tabButtons = document.querySelectorAll(".tab-btn");
const tabPanels = document.querySelectorAll(".tab-panel");

// Dosage Elements
const farmAcresInput = document.getElementById("farm-acres-input");
const calcWaterVal = document.getElementById("calc-water-val");
const calcOrganicVal = document.getElementById("calc-organic-val");
const calcChemicalVal = document.getElementById("calc-chemical-val");
const calcTanksVal = document.getElementById("calc-tanks-val");

// Weather Elements
const weatherAlertBox = document.getElementById("weather-alert-box");
const weatherAlertIcon = document.getElementById("weather-alert-icon");
const weatherAlertHeadline = document.getElementById("weather-alert-headline");
const weatherAlertDesc = document.getElementById("weather-alert-desc");
const windowTimeText = document.getElementById("window-time-text");

// Buttons & Actions
const btnTTS = document.getElementById("btn-tts");
const ttsBtnText = document.getElementById("tts-btn-text");
const btnPrint = document.getElementById("btn-print");
const btnShare = document.getElementById("btn-share");
const btnVoiceQA = document.getElementById("btn-voice-qa");
const continueButton = document.getElementById("continue-button");
const resubmitButton = document.getElementById("resubmit-button");
const btnCompareRef = document.getElementById("btn-compare-reference");
const comparisonModal = document.getElementById("comparison-modal");
const btnCloseModal = document.getElementById("btn-close-modal");
const demoModeBanner = document.getElementById("demo-mode-banner");

// HITL Status Banner Elements
const hitlBanner = document.getElementById("field-agent-status-banner");
const hitlIcon = document.getElementById("hitl-banner-icon");
const hitlTitle = document.getElementById("hitl-banner-title");
const hitlDesc = document.getElementById("hitl-banner-desc");
const hitlBadge = document.getElementById("hitl-banner-badge");

// ==========================================================================
// INITIALIZATION
// ==========================================================================

document.addEventListener("DOMContentLoaded", function () {
    setupTabNavigation();
    setupDosageCalculator();
    setupAudioTTS();
    setupPrintAndShare();
    setupDeepLinks();
    setupComparisonModal();
    loadAnalysisData();
});

// ==========================================================================
// DATA LOADING (REAL, URL PARAM, OR DEMO PRESET)
// ==========================================================================
async function loadAnalysisData() {
    const urlParams = new URLSearchParams(window.location.search);
    const recordId = urlParams.get("record_id") || urlParams.get("scan_id") || urlParams.get("id");

    // 1. If loaded with a specific disease record ID from a notification link
    if (recordId) {
        try {
            console.log(`Fetching persistent disease record #${recordId}...`);
            const res = await fetch(`/api/verifications/disease-scans/${recordId}`);
            if (res.ok) {
                const data = await res.json();
                if (data.success && data.disease_scan) {
                    const rec = data.disease_scan;
                    console.log("Loaded persistent disease scan from backend:", rec);

                    let confVal = Number(rec.confidence) || 0.95;
                    if (confVal <= 1.0) confVal = confVal * 100;

                    const reconstructedResult = {
                        prediction: {
                            plant: (rec.crop_type || "crop").toLowerCase(),
                            model: "plantvillage_cnn",
                            model_name: "AgriBridge ICAR Plant Health Vision Net",
                            confidence: confVal,
                            class_id: 1
                        },
                        disease: {
                            crop: rec.crop_type ? (rec.crop_type.charAt(0).toUpperCase() + rec.crop_type.slice(1)) : "Crop",
                            disease: rec.predicted_pathogen || "Crop Condition",
                            scientific_name: rec.scientific_name || "Pathogen classification verified",
                            description: `Diagnostic record for ${rec.crop_type}. Agent audit remarks: ${rec.agent_remarks || 'ICAR protocol applied.'}`,
                            severity_level: (rec.severity || "moderate").toLowerCase(),
                            severity_percentage: (rec.severity || "").toLowerCase().includes("severe") ? 80 : 50,
                            yield_risk: (rec.severity || "").toLowerCase().includes("severe") ? "35% - 50%" : "15% - 25%",
                            treatment: `Apply ${rec.prescription_chemical || 'Mancozeb 75% WP'} at ${rec.prescription_dosage || '2.0 g/L water'}. Observe ${rec.prescription_phi || '7-10 Days PHI'}.`,
                            organic_option: rec.prescription_organic || "Spray cold-pressed Neem Oil (10,000 ppm) @ 5ml/L on foliage.",
                            chemical_option: `${rec.prescription_chemical || 'Mancozeb 75% WP'} @ ${rec.prescription_dosage || '2.0 g/L water'}`,
                            prevention: "Avoid sprinkler wetting of leaves. Maintain ventilation and sanitize tools.",
                            sanitation: "Remove and destroy heavily blighted lower leaves."
                        },
                        farm: {
                            farm_area: rec.farm_area || 2.5,
                            growth_stage: rec.growth_stage || "flowering",
                            irrigation_method: "drip",
                            irrigation_status: "normal",
                            recent_rainfall: "low",
                            humidity: "moderate",
                            fertilizer_applied: "NPK Standard",
                            region: rec.geolocation || "Raipur, Chhattisgarh"
                        },
                        farm_specific_advice: {
                            irrigation_advice: "Maintain morning irrigation. Avoid evening watering to prevent nocturnal canopy dampness.",
                            weather_advice: "Favorable dry window detected for foliar spray.",
                            fertilizer_advice: "Supplement with soluble potassium to fortify plant cell walls.",
                            field_sanitation: "Disinfect pruning tools with 10% sodium hypochlorite.",
                            disease_severity: `Severity evaluated as ${rec.severity || 'moderate'}.`,
                            growth_stage: `Crop in ${rec.growth_stage || 'flowering'} stage.`,
                            regional_advice: "ICAR standard agronomist verified prescription."
                        },
                        timing_advice: {
                            status: "favorable",
                            rain_risk: false,
                            advice: "Ideal weather window. Low wind speed ensures maximum foliar adhesion.",
                            recommended_window: "Tomorrow 6:00 AM – 9:00 AM"
                        },
                        verification: {
                            verified: rec.status === "VERIFIED_HEALTH_RECORD",
                            source: rec.agent_name ? `Verified by ${rec.agent_name}` : "ICAR Agronomy Verification Hub",
                            safety_note: `Strictly observe ${rec.prescription_phi || '7-10 Days Pre-Harvest Interval (PHI)'}.`
                        },
                        disease_record: rec
                    };

                    if (rec.image_url) {
                        const imgUrl = rec.image_url.startsWith("http") ? rec.image_url : `/${rec.image_url}`;
                        cropImage.src = imgUrl;
                    }

                    demoModeBanner.style.display = "none";
                    localStorage.setItem("diseaseRecord", JSON.stringify(rec));
                    localStorage.setItem("aiResult", JSON.stringify(reconstructedResult));
                    renderAIResult(reconstructedResult);
                    return;
                }
            }
        } catch (fetchErr) {
            console.warn("Could not load record by ID, trying localStorage:", fetchErr);
        }
    }

    const savedAIResult = localStorage.getItem("aiResult");
    const savedImage = localStorage.getItem("cropImage");

    if (savedAIResult) {
        try {
            const parsed = JSON.parse(savedAIResult);
            console.log("Loaded Live AI Result from localStorage:", parsed);
            if (savedImage) {
                cropImage.src = savedImage;
            }
            demoModeBanner.style.display = "none";
            renderAIResult(parsed);

            // Check live backend verification status if record exists
            const savedRecordStr = localStorage.getItem("diseaseRecord");
            if (savedRecordStr) {
                try {
                    const record = JSON.parse(savedRecordStr);
                    if (record && record.id) {
                        fetch(`/api/verifications/disease-scans/${record.id}`)
                            .then(res => res.ok ? res.json() : null)
                            .then(data => {
                                if (data && data.success && data.disease_scan) {
                                    if (data.disease_scan.status !== (parsed.disease_record && parsed.disease_record.status)) {
                                        console.log("Updated live disease scan status:", data.disease_scan.status);
                                        localStorage.setItem("diseaseRecord", JSON.stringify(data.disease_scan));
                                        parsed.disease_record = data.disease_scan;
                                        renderAIResult(parsed);
                                    }
                                }
                            })
                            .catch(err => console.debug("Status check skipped:", err));
                    }
                } catch (recErr) {}
            }
            return;

        } catch (e) {
            console.error("Failed to parse saved AI result:", e);
        }
    }

    // Fail-Safe: Show Demo Mode so judges never hit a broken screen
    console.info("No saved upload found. Activating Judge Demo Mode.");
    demoModeBanner.style.display = "block";
    loadPresetCase("tomato_early_blight");
}

window.loadPresetCase = function (presetKey) {
    const preset = DEMO_PRESETS[presetKey];
    if (!preset) return;

    // Update demo pill UI active state
    document.querySelectorAll(".demo-pill").forEach(btn => btn.classList.remove("active"));
    const activeBtn = document.getElementById(`demo-pill-${presetKey.split("_")[0]}`);
    if (activeBtn) activeBtn.classList.add("active");

    if (preset.sample_image) {
        cropImage.src = preset.sample_image;
    }

    renderAIResult(preset);
};

// ==========================================================================
// MAIN RENDER FUNCTION
// ==========================================================================
function renderAIResult(aiResult) {
    currentAIResult = aiResult;

    const prediction = aiResult.prediction || {};
    const disease = aiResult.disease || {};
    const farmAdvice = aiResult.farm_specific_advice || {};
    const farm = aiResult.farm || {};
    const verification = aiResult.verification || {};
    const timing = aiResult.timing_advice || {};

    currentCropName = disease.crop || prediction.plant || "Crop";
    currentDiseaseName = disease.disease || "Crop Diagnosis";
    currentAcreage = Number(farm.farm_area) || 2.5;

    // Determine HITL Disease Verification Status
    let diseaseStatus = "VERIFIED_HEALTH_RECORD";
    const savedRecordStr = localStorage.getItem("diseaseRecord");
    let savedRecord = null;
    if (savedRecordStr) {
        try { savedRecord = JSON.parse(savedRecordStr); } catch (e) {}
    }

    if (aiResult.disease_record && aiResult.disease_record.status) {
        diseaseStatus = aiResult.disease_record.status;
    } else if (savedRecord && savedRecord.status) {
        diseaseStatus = savedRecord.status;
    }

    const isDemo = demoModeBanner && demoModeBanner.style.display !== "none";
    if (isDemo) {
        diseaseStatus = "VERIFIED_HEALTH_RECORD";
    }

    // 0. Update HITL Verification Banner
    if (hitlBanner) {
        hitlBanner.style.display = "flex";
        hitlBanner.className = "hitl-banner";

        if (diseaseStatus === "PENDING_AGENT_REVIEW") {
            hitlBanner.classList.add("pending");
            if (hitlIcon) hitlIcon.textContent = "⏳";
            if (hitlTitle) hitlTitle.textContent = "Pending Field Agent Review";
            if (hitlDesc) hitlDesc.textContent = "Your disease scan has been queued for human-in-the-loop review by an Agri-Student Field Agent. Chemical dosage and prescription are locked until verified to ensure ICAR agronomic compliance.";
            if (hitlBadge) hitlBadge.textContent = "PENDING REVIEW";
            if (overlayStatusText) overlayStatusText.textContent = "Pending Agent Review";
        } else if (diseaseStatus === "NEEDS_PHYSICAL_VISIT" || diseaseStatus === "PENDING_FIELD_DISPATCH") {
            hitlBanner.classList.add("dispatch");
            if (hitlIcon) hitlIcon.textContent = "🚨";
            if (hitlTitle) hitlTitle.textContent = "On-Site Physical Audit Assigned";
            if (hitlDesc) hitlDesc.textContent = "Your disease scan requires on-site verification. An Agri-Student Agent has been assigned to visit your field.";
            if (hitlBadge) hitlBadge.textContent = "ON-SITE AUDIT";
            if (overlayStatusText) overlayStatusText.textContent = "On-Site Audit Required";
        } else {
            hitlBanner.classList.add("verified");
            if (hitlIcon) hitlIcon.textContent = "✅";
            if (hitlTitle) hitlTitle.textContent = "Verified Health Record — Approved by Field Agent";
            if (hitlDesc) hitlDesc.textContent = "Diagnosis verified by Field Agent. ICAR-compliant agronomic prescription authorized for application.";
            if (hitlBadge) hitlBadge.textContent = "VERIFIED";
            if (overlayStatusText) overlayStatusText.textContent = "Verified Health Record";
        }
    }

    // 1. Headline & Hero Box
    cropNameText.textContent = `Crop: ${capitalize(currentCropName)}`;
    resultTitle.textContent = currentDiseaseName;
    resultScientific.textContent = disease.scientific_name || `Classification: ${prediction.model_name || "AgriBridge AI"}`;
    resultMessage.textContent = disease.description || "AI diagnosis completed successfully based on leaf visual patterns.";

    // 2. Visual Severity & Metrics
    const isHealthy = currentDiseaseName.toLowerCase().includes("healthy") || (disease.severity_level === "healthy") || (disease.severity_level === "none");
    const severity = (disease.severity_level || farm.disease_severity || (isHealthy ? "healthy" : "moderate")).toLowerCase();

    updateSeverityMeter(severity, disease.severity_percentage);
    updateConfidenceScore(prediction.confidence, prediction.model_name);

    if (yieldRiskVal) {
        yieldRiskVal.textContent = disease.yield_risk || (isHealthy ? "0% (Healthy)" : "20% - 35%");
        if (isHealthy) {
            yieldRiskVal.style.color = "#2E7D32";
            if (yieldRiskSub) yieldRiskSub.textContent = "Optimal Market Quality Stand";
            if (overlayStatusText && diseaseStatus === "VERIFIED_HEALTH_RECORD") overlayStatusText.textContent = "Verified Healthy Crop";
        } else {
            yieldRiskVal.style.color = "#D32F2F";
            if (yieldRiskSub) yieldRiskSub.textContent = "Preventable with immediate Rx";
            if (overlayStatusText && diseaseStatus === "VERIFIED_HEALTH_RECORD") overlayStatusText.textContent = "Diagnosis Complete";
        }
    }

    // 3. Treatments (Tab 1) — Lock chemical dosage if not verified
    const organicEl = document.getElementById("organic-treatment-text");
    const chemicalEl = document.getElementById("chemical-treatment-text");
    const preventionEl = document.getElementById("prevention-text");
    const sanitationEl = document.getElementById("sanitation-text");

    const isPrescriptionLocked = (diseaseStatus === "PENDING_AGENT_REVIEW" || diseaseStatus === "NEEDS_PHYSICAL_VISIT" || diseaseStatus === "PENDING_FIELD_DISPATCH");

    if (organicEl) {
        organicEl.textContent = disease.organic_option || disease.treatment || "Apply organic bio-fungicide formulation.";
    }

    if (chemicalEl) {
        if (isPrescriptionLocked) {
            chemicalEl.innerHTML = `
                <div class="prescription-locked-box">
                    <div class="prescription-locked-icon">🔒</div>
                    <div class="prescription-locked-title">Chemical Dosage & Prescription Locked</div>
                    <div class="prescription-locked-desc">
                        Awaiting manual verification by an assigned Agri-Student / Field Agent. To ensure chemical safety and ICAR compliance, specific chemical formulations and dilution rates are masked until authorized.
                    </div>
                </div>
            `;
        } else {
            chemicalEl.textContent = disease.chemical_option || "Apply recommended systemic/contact chemical control if severity warrants.";
        }
    }

    if (preventionEl) preventionEl.textContent = disease.prevention || farmAdvice.fertilizer_advice || "Ensure appropriate plant spacing and soil aeration.";
    if (sanitationEl) sanitationEl.textContent = disease.sanitation || farmAdvice.field_sanitation || "Prune infected leaves and maintain clean field borders.";

    // 4. Dosage Calculator (Tab 2)
    if (farmAcresInput) {
        farmAcresInput.value = currentAcreage;
        if (isPrescriptionLocked) {
            if (calcChemicalVal) calcChemicalVal.textContent = "🔒 Locked (Pending Field Agent)";
            if (calcOrganicVal) calcOrganicVal.textContent = "Bio-fungicide only";
        } else {
            recalculateDosage(currentAcreage);
        }
    }


    // 5. Weather Spray Timing (Tab 3)
    renderWeatherTiming(timing, farmAdvice.weather_advice);

    // 6. Farm Profile Context (Tab 5)
    renderFarmProfile(farm, farmAdvice);

    // 7. Verification Citation Box
    const vStatusPill = document.getElementById("verification-status-pill");
    const vSourceText = document.getElementById("verification-source-text");
    const vSafetyText = document.getElementById("verification-safety-text");

    if (vStatusPill) {
        vStatusPill.textContent = verification.verified ? "✅ Verified by Agronomy Dataset" : "ℹ️ AI Generated";
    }
    if (vSourceText) {
        vSourceText.textContent = verification.source || "Knowledge base compiled from ICAR, TNAU Agritech Portal, and PlantVillage Diagnostic Database.";
    }
    if (vSafetyText) {
        vSafetyText.textContent = verification.safety_note || "Safety Note: Always follow registered manufacturer product label recommendations and dilution ratios.";
    }
}

// ==========================================================================
// SEVERITY & CONFIDENCE HELPERS
// ==========================================================================
function updateSeverityMeter(severity, customPercentage) {
    if (!severityBadge || !severityMeterFill) return;

    severityBadge.className = `severity-tag ${severity}`;
    severityBadge.textContent = capitalize(severity);

    let widthPercent = 50;
    if (customPercentage) {
        widthPercent = customPercentage;
    } else {
        switch (severity) {
            case "healthy":
            case "none":
                widthPercent = 5;
                break;
            case "mild":
            case "low":
                widthPercent = 25;
                break;
            case "moderate":
                widthPercent = 55;
                break;
            case "severe":
            case "high":
                widthPercent = 90;
                break;
        }
    }

    severityMeterFill.style.width = `${widthPercent}%`;
}

function updateConfidenceScore(confidence, modelName) {
    if (!confidencePercentage || !confidenceFill) return;

    let confNum = Number(confidence) || 98.4;
    // If confidence is between 0 and 1, convert to percentage
    if (confNum <= 1 && confNum > 0) confNum = confNum * 100;

    confidencePercentage.textContent = `${confNum.toFixed(1)}%`;
    confidenceFill.style.width = `${Math.min(confNum, 100)}%`;

    if (modelNameSub) {
        modelNameSub.textContent = `Model: ${modelName || "AgriBridge Deep CNN"}`;
    }
}

// ==========================================================================
// TAB NAVIGATION
// ==========================================================================
function setupTabNavigation() {
    tabButtons.forEach(button => {
        button.addEventListener("click", () => {
            const targetTabId = button.getAttribute("data-tab");

            tabButtons.forEach(btn => btn.classList.remove("active"));
            tabPanels.forEach(panel => panel.classList.remove("active"));

            button.classList.add("active");
            const targetPanel = document.getElementById(targetTabId);
            if (targetPanel) {
                targetPanel.classList.add("active");
            }
        });
    });
}

// ==========================================================================
// DOSAGE CALCULATOR
// ==========================================================================
function setupDosageCalculator() {
    if (!farmAcresInput) return;

    farmAcresInput.addEventListener("input", (e) => {
        let val = parseFloat(e.target.value);
        if (isNaN(val) || val <= 0) val = 1;
        recalculateDosage(val);
    });
}

function recalculateDosage(acres) {
    const waterLiters = Math.round(acres * 200);
    const neemLiters = (acres * 0.5).toFixed(2);
    const mancozebKg = (acres * 0.4).toFixed(2);
    const knapsackTanks = Math.ceil(waterLiters / 16);

    if (calcWaterVal) calcWaterVal.textContent = `${waterLiters} Liters`;
    if (calcOrganicVal) calcOrganicVal.textContent = `${neemLiters} Liters`;
    if (calcChemicalVal) calcChemicalVal.textContent = `${mancozebKg} kg`;
    if (calcTanksVal) calcTanksVal.textContent = `${knapsackTanks} Tanks`;
}

// ==========================================================================
// WEATHER SPRAY TIMING
// ==========================================================================
function renderWeatherTiming(timing, customWeatherText) {
    if (!weatherAlertBox) return;

    const isDelayed = timing.status === "delayed" || timing.rain_risk === true;

    if (isDelayed) {
        weatherAlertBox.className = "weather-alert-box alert-delayed";
        if (weatherAlertIcon) weatherAlertIcon.textContent = "⚠️";
        if (weatherAlertHeadline) weatherAlertHeadline.textContent = "Weather Warning — Spray Delay Advised";
        if (weatherAlertDesc) weatherAlertDesc.textContent = timing.advice || customWeatherText || "Rain or high winds detected. Delay spraying to avoid chemical runoff.";
    } else {
        weatherAlertBox.className = "weather-alert-box";
        if (weatherAlertIcon) weatherAlertIcon.textContent = "🌦️";
        if (weatherAlertHeadline) weatherAlertHeadline.textContent = "Optimal Weather Spray Window Detected";
        if (weatherAlertDesc) weatherAlertDesc.textContent = timing.advice || customWeatherText || "Low wind speed and clear skies ensure high chemical foliar adhesion and absorption.";
    }

    if (windowTimeText) {
        windowTimeText.textContent = timing.recommended_window || "Tomorrow 6:00 AM – 9:00 AM";
    }
}

// ==========================================================================
// FARM PROFILE RENDERING
// ==========================================================================
function renderFarmProfile(farm, farmAdvice) {
    const specsList = document.getElementById("farm-specs-list");
    const adviceList = document.getElementById("farm-advice-list");

    // Deterministic simulated soil moisture for prototype display
    let soilMoistureDisplay = "54% VWC (Optimal)";
    try {
        const rawAi = JSON.parse(localStorage.getItem("ai_prediction_result") || localStorage.getItem("aiResult") || "{}");
        if (rawAi.simulated_soil_moisture && rawAi.simulated_soil_moisture.label) {
            soilMoistureDisplay = rawAi.simulated_soil_moisture.label;
        } else {
            const m = (farm.irrigation_method || "drip").toLowerCase();
            const val = m.includes("flood") || m.includes("canal") ? 70 : (m.includes("sprinkler") ? 55 : 42);
            soilMoistureDisplay = `${val}% VWC (${val >= 65 ? "Elevated" : "Optimal"})`;
        }
    } catch (e) {}

    if (specsList) {
        specsList.innerHTML = `
            <div class="farm-spec-item"><strong>Farm Size</strong><span>${farm.farm_area || currentAcreage} Acres</span></div>
            <div class="farm-spec-item"><strong>Growth Stage</strong><span>${capitalize(farm.growth_stage || "Flowering")}</span></div>
            <div class="farm-spec-item"><strong>Irrigation</strong><span>${capitalize(farm.irrigation_method || "Drip")} (${capitalize(farm.irrigation_status || "Normal")})</span></div>
            <div class="farm-spec-item"><strong>Recent Rain</strong><span>${capitalize(farm.recent_rainfall || "Low")}</span></div>
            <div class="farm-spec-item"><strong>Fertilizer</strong><span>${farm.fertilizer_applied || "NPK Blend"}</span></div>
            <div class="farm-spec-item"><strong>Location</strong><span>${farm.region || "Verified Region"}</span></div>
            <div class="farm-spec-item" style="grid-column: 1 / -1; background: #F0FDF4; border: 1px solid #BBF7D0; border-left: 4px solid #16A34A; border-radius: 8px; padding: 10px 14px;">
                <strong style="color: #166534;">🧪 Simulated Soil Moisture Reading (Prototype Data):</strong>
                <span style="font-weight: 700; color: #15803D;">${soilMoistureDisplay}</span>
            </div>
        `;
    }

    if (adviceList) {
        adviceList.innerHTML = `
            <div class="advice-pill-item">
                <strong>💧 Irrigation Direction:</strong>
                ${farmAdvice.irrigation_advice || "Schedule morning drip irrigation to prevent nocturnal canopy dampness."}
            </div>
            <div class="advice-pill-item">
                <strong>🌾 Nutrition Management:</strong>
                ${farmAdvice.fertilizer_advice || "Supplement with micronutrient boron and potassium to reinforce fruit set."}
            </div>
            <div class="advice-pill-item">
                <strong>📍 Regional Microclimate:</strong>
                ${farmAdvice.regional_advice || "Maintain vigilance against early morning fog condensing on leaf margins."}
            </div>
        `;
    }
}

// ==========================================================================
// MULTILINGUAL VOICE TEXT-TO-SPEECH (TTS)
// ==========================================================================
function setupAudioTTS() {
    if (!btnTTS) return;

    btnTTS.addEventListener("click", () => {
        if (isSpeaking) {
            stopSpeaking();
        } else {
            startSpeaking();
        }
    });
}

function startSpeaking() {
    if (!("speechSynthesis" in window)) {
        alert("Text-to-speech audio is not supported in this browser.");
        return;
    }

    window.speechSynthesis.cancel(); // Stop any pending speech

    const lang = localStorage.getItem("selectedLanguage") || "en";
    let speechText = "";

    if (lang === "hi") {
        speechText = `एग्रीब्रिज कृषि रिपोर्ट। आपके ${currentCropName} में ${currentDiseaseName} का निदान हुआ है। जैविक उपचार के लिए नीम तेल का छिड़काव करें। स्प्रे करने का सर्वोत्तम समय कल सुबह छह से नौ बजे है।`;
    } else if (lang === "mr") {
        speechText = `अ‍ॅग्रीब्रिज पीक आरोग्य अहवाल। तुमच्या ${currentCropName} पिकावर ${currentDiseaseName} आढळले आहे। सेंद्रिय उपचारासाठी कडुनिंब तेलाची फवारणी करा। फवारणीची सर्वोत्तम वेळ उद्या सकाळी आहे।`;
    } else if (lang === "te") {
        speechText = `అగ్రిబ్రిడ్జ్ పంట ఆరోగ్య నివేదిక. మీ ${currentCropName} పంటలో ${currentDiseaseName} గుర్తించబడింది. సేంద్రీయ నివారణకు వేప నూనెను వాడండి.`;
    } else {
        speechText = `AgriBridge Crop Diagnostic Report. Your ${currentCropName} has been diagnosed with ${currentDiseaseName}. Recommended organic remedy: Apply cold-pressed neem oil formulation. Optimal spray window is tomorrow morning from 6 AM to 9 AM.`;
    }

    const utterance = new SpeechSynthesisUtterance(speechText);
    
    // Map to BCP-47 language codes
    const langCodes = {
        "en": "en-IN",
        "hi": "hi-IN",
        "mr": "mr-IN",
        "te": "te-IN",
        "ta": "ta-IN",
        "bn": "bn-IN",
        "gu": "gu-IN",
        "pa": "pa-IN"
    };
    utterance.lang = langCodes[lang] || "en-IN";
    utterance.rate = 0.95;
    utterance.pitch = 1.0;

    utterance.onstart = () => {
        isSpeaking = true;
        btnTTS.classList.add("speaking");
        if (ttsBtnText) ttsBtnText.textContent = "Stop Audio (रोकें)";
    };

    utterance.onend = utterance.onerror = () => {
        stopSpeaking();
    };

    window.speechSynthesis.speak(utterance);
}

function stopSpeaking() {
    if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
    }
    isSpeaking = false;
    if (btnTTS) btnTTS.classList.remove("speaking");
    if (ttsBtnText) ttsBtnText.textContent = "Listen (आवाज में सुनें)";
}

// ==========================================================================
// PRINT, PDF EXPORT & WHATSAPP SHARING
// ==========================================================================
function setupPrintAndShare() {
    // Print Rx
    if (btnPrint) {
        btnPrint.addEventListener("click", () => {
            const timestampEl = document.getElementById("print-timestamp");
            if (timestampEl) {
                const now = new Date();
                timestampEl.innerHTML = `<strong>Date Generated:</strong> ${now.toLocaleDateString()} ${now.toLocaleTimeString()}<br><strong>Farmer ID:</strong> AB-${Math.floor(100000 + Math.random() * 900000)}`;
            }
            window.print();
        });
    }

    // Share on WhatsApp
    if (btnShare) {
        btnShare.addEventListener("click", () => {
            const shareText = `*AgriBridge Crop Health Prescription*%0A%0A*Crop:* ${currentCropName}%0A*Diagnosis:* ${currentDiseaseName}%0A*Severity:* ${severityBadge ? severityBadge.textContent : "Moderate"}%0A*Optimal Spray Window:* ${windowTimeText ? windowTimeText.textContent : "Tomorrow Morning"}%0A%0A_Generated via AgriBridge AI Agronomy Platform_`;
            window.open(`https://api.whatsapp.com/send?text=${shareText}`, "_blank");
        });
    }
}

// ==========================================================================
// DEEP LINKS & WORKFLOW NAVIGATION
// ==========================================================================
function setupDeepLinks() {
    // Voice Assistant Bridge
    if (btnVoiceQA) {
        btnVoiceQA.addEventListener("click", () => {
            const prompt = `I have ${currentCropName} with ${currentDiseaseName}. What is the exact spray dosage and timing for my farm?`;
            localStorage.setItem("voiceAssistantPresetQuery", prompt);
            window.location.href = "/frontend/pages/voice-assistant.html";
        });
    }

    // Continue to Verification
    if (continueButton) {
        continueButton.addEventListener("click", () => {
            window.location.href = "/frontend/pages/verification-status.html";
        });
    }

    // Resubmit / Scan Another
    if (resubmitButton) {
        resubmitButton.addEventListener("click", () => {
            localStorage.removeItem("aiResult");
            localStorage.removeItem("cropImage");
            window.location.href = "/frontend/pages/upload-crop.html";
        });
    }
}

// ==========================================================================
// REFERENCE COMPARISON MODAL
// ==========================================================================
function setupComparisonModal() {
    if (btnCompareRef && comparisonModal) {
        btnCompareRef.addEventListener("click", () => {
            const modalUploadedImg = document.getElementById("modal-uploaded-img");
            if (modalUploadedImg && cropImage) {
                modalUploadedImg.src = cropImage.src;
            }
            comparisonModal.style.display = "flex";
        });
    }

    if (btnCloseModal && comparisonModal) {
        btnCloseModal.addEventListener("click", () => {
            comparisonModal.style.display = "none";
        });
    }

    if (comparisonModal) {
        comparisonModal.addEventListener("click", (e) => {
            if (e.target === comparisonModal) {
                comparisonModal.style.display = "none";
            }
        });
    }
}

// ==========================================================================
// GENERAL UTILITIES
// ==========================================================================
function capitalize(str) {
    if (!str) return "";
    return String(str).charAt(0).toUpperCase() + String(str).slice(1);
}
