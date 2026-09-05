// =========================================
// AGRIBRIDGE — AI RESULT PAGE
// =========================================

console.log("AI-RESULT.JS LOADED");


// Helper for safe translation fallback
function t(key, fallback) {
    if (typeof translate === "function") {
        return translate(key) || fallback || key;
    }
    return fallback || key;
}


// =========================================
// GET HTML ELEMENTS
// =========================================

const cropImage =
    document.getElementById("crop-image");

const resultIcon =
    document.getElementById("result-icon");

const resultTitle =
    document.getElementById("result-title");

const resultMessage =
    document.getElementById("result-message");

const guidanceSection =
    document.getElementById("guidance-section");

const continueButton =
    document.getElementById("continue-button");

const resubmitButton =
    document.getElementById("resubmit-button");


// =========================================
// LOAD SAVED IMAGE
// =========================================

const savedImage =
    localStorage.getItem("cropImage");


if (savedImage) {

    cropImage.src = savedImage;

} else {

    cropImage.style.display = "none";

}


// =========================================
// LOAD AI RESULT
// =========================================

const savedAIResult =
    localStorage.getItem("aiResult");


console.log(
    "Saved AI result:",
    savedAIResult
);


// =========================================
// RESULT NOT FOUND
// =========================================

if (!savedAIResult) {

    showError(
        t("aiResult.resultNotFound", "AI Result Not Found"),
        t("aiResult.resultNotFoundDesc", "No AI analysis result was found. Please analyze the crop again.")
    );

} else {

    try {

        const aiResult =
            JSON.parse(savedAIResult);


        console.log(
            "Loaded AI Result:",
            aiResult
        );


        displayAIResult(aiResult);


    } catch (error) {

        console.error(
            "AI Result Parsing Error:",
            error
        );

        showError(
            t("aiResult.unableToDisplay", "Unable to Display Result"),
            t("aiResult.unableToDisplayDesc", "The AI response could not be displayed correctly.")
        );

    }

}


// =========================================
// DISPLAY AI RESULT
// =========================================

function displayAIResult(aiResult) {

    const prediction =
        aiResult.prediction || {};

    const disease =
        aiResult.disease || {};

    const farmAdvice =
        aiResult.farm_specific_advice || {};

    const farm =
        aiResult.farm || {};

    const verification =
        aiResult.verification || {};


    // =====================================
    // DISEASE RESULT
    // =====================================

    resultIcon.textContent = "🌱";

    resultTitle.textContent =
        disease.disease ||
        "Disease information unavailable";

    resultMessage.textContent =
        disease.description ||
        "The AI completed the analysis, but no disease description was provided.";


    // =====================================
    // BUILD RESULT HTML
    // =====================================

    let html = "";


    // =====================================
    // BASIC AI INFORMATION
    // =====================================

    html += `

        <div class="ai-detail">

            <strong>${t("aiResult.fields.crop", "Crop:")}</strong>

            <span>
                ${safeText(
                    disease.crop ||
                    prediction.plant ||
                    t("common.noDataAvailable", "Not specified")
                )}
            </span>

        </div>


        <div class="ai-detail">

            <strong>${t("aiResult.fields.aiModel", "AI Model:")}</strong>

            <span>
                ${safeText(
                    prediction.model_name ||
                    prediction.model ||
                    t("common.noDataAvailable", "Not specified")
                )}
            </span>

        </div>


        <div class="ai-detail">

            <strong>${t("aiResult.fields.confidence", "AI Confidence:")}</strong>

            <span>
                ${formatConfidence(
                    prediction.confidence
                )}
            </span>

        </div>


        <div class="ai-detail">

            <strong>${t("aiResult.fields.classId", "Prediction Class ID:")}</strong>

            <span>
                ${safeText(
                    prediction.class_id ??
                    t("common.noDataAvailable", "Not specified")
                )}
            </span>

        </div>

    `;


    // =====================================
    // TREATMENT
    // =====================================

    if (disease.treatment) {

        html += `

            <div class="ai-detail">

                <strong>${t("aiResult.fields.treatment", "Treatment:")}</strong>

                <span>
                    ${safeText(disease.treatment)}
                </span>

            </div>

        `;

    }


    // =====================================
    // PREVENTION
    // =====================================

    if (disease.prevention) {

        html += `

            <div class="ai-detail">

                <strong>${t("aiResult.fields.prevention", "Prevention:")}</strong>

                <span>
                    ${safeText(disease.prevention)}
                </span>

            </div>

        `;

    }


    // =====================================
    // ORGANIC OPTION
    // =====================================

    if (disease.organic_option) {

        html += `

            <div class="ai-detail">

                <strong>${t("aiResult.fields.organicOption", "Organic / Biological Option:")}</strong>

                <span>
                    ${safeText(disease.organic_option)}
                </span>

            </div>

        `;

    }


    // =====================================
    // CHEMICAL OPTION
    // =====================================

    if (disease.chemical_option) {

        html += `

            <div class="ai-detail">

                <strong>${t("aiResult.fields.chemicalOption", "Chemical Option:")}</strong>

                <span>
                    ${safeText(disease.chemical_option)}
                </span>

            </div>

        `;

    }


    // =====================================
    // FARM PROFILE
    // =====================================

    if (Object.keys(farm).length > 0) {

        html += `

            <hr>

            <h3>${t("aiResult.farmProfile.title", "Farm Profile Used for Advice")}</h3>

            <div class="farm-profile">

                ${createFarmDetail(
                    t("aiResult.farmProfile.farmArea", "Farm Area (acres)"),
                    farm.farm_area
                )}

                ${createFarmDetail(
                    t("aiResult.farmProfile.irrigationMethod", "Irrigation Method"),
                    farm.irrigation_method
                )}

                ${createFarmDetail(
                    t("aiResult.farmProfile.irrigationStatus", "Irrigation Status"),
                    farm.irrigation_status
                )}

                ${createFarmDetail(
                    t("aiResult.farmProfile.recentRainfall", "Recent Rainfall"),
                    farm.recent_rainfall
                )}

                ${createFarmDetail(
                    t("aiResult.farmProfile.humidity", "Humidity"),
                    farm.humidity
                )}

                ${createFarmDetail(
                    t("aiResult.farmProfile.fertilizerApplied", "Fertilizer Applied"),
                    farm.fertilizer_applied
                )}

                ${createFarmDetail(
                    t("aiResult.farmProfile.previousCrop", "Previous Crop"),
                    farm.previous_crop
                )}

                ${createFarmDetail(
                    t("aiResult.farmProfile.diseaseSeverity", "Disease Severity"),
                    farm.disease_severity
                )}

                ${createFarmDetail(
                    t("aiResult.farmProfile.growthStage", "Growth Stage"),
                    farm.growth_stage
                )}

                ${createFarmDetail(
                    t("aiResult.farmProfile.region", "Region"),
                    farm.region
                )}

            </div>

        `;

    }


    // =====================================
    // FARM-SPECIFIC ADVICE
    // =====================================

    html += `

        <hr>

        <h3>${t("aiResult.advice.title", "Farm-Specific Advice")}</h3>

    `;


    html += createAdviceSection(
        t("aiResult.advice.irrigation", "💧 Irrigation Advice"),
        farmAdvice.irrigation_advice
    );


    html += createAdviceSection(
        t("aiResult.advice.weather", "🌦️ Weather Advice"),
        farmAdvice.weather_advice
    );


    html += createAdviceSection(
        t("aiResult.advice.fertilizer", "🌾 Fertilizer Advice"),
        farmAdvice.fertilizer_advice
    );


    html += createAdviceSection(
        t("aiResult.advice.sanitation", "🧹 Field Sanitation"),
        farmAdvice.field_sanitation
    );


    html += createAdviceSection(
        t("aiResult.advice.diseaseSeverity", "⚠️ Disease Severity"),
        farmAdvice.disease_severity
    );


    html += createAdviceSection(
        t("aiResult.advice.growthStage", "🌱 Growth Stage"),
        farmAdvice.growth_stage
    );


    html += createAdviceSection(
        t("aiResult.advice.regional", "📍 Regional Advice"),
        farmAdvice.regional_advice
    );


    // =====================================
    // VERIFICATION
    // =====================================

    html += `

        <hr>

        <h3>${t("aiResult.verification.title", "✅ Recommendation Verification")}</h3>

        <div class="verification-box">

            <p>

                <strong>${t("aiResult.verification.verified", "Verified:")}</strong>

                ${verification.verified === true
                    ? t("aiResult.verification.yes", "Yes")
                    : t("aiResult.verification.notVerified", "Not verified")}

            </p>

            <p>

                <strong>${t("aiResult.verification.source", "Source:")}</strong>

                ${safeText(
                    verification.source ||
                    t("common.noDataAvailable", "Not specified")
                )}

            </p>

            <p>

                <strong>${t("aiResult.verification.safetyNote", "Safety Note:")}</strong>

                ${safeText(
                    verification.safety_note ||
                    t("aiResult.verification.safetyDefault", "Follow registered product labels and local agricultural guidance.")
                )}

            </p>

        </div>

    `;


    // =====================================
    // DISPLAY
    // =====================================

    guidanceSection.innerHTML = html;

    guidanceSection.style.display = "block";

    continueButton.style.display = "block";

    resubmitButton.style.display = "block";

}


// =========================================
// CREATE ADVICE SECTION
// =========================================

function createAdviceSection(
    title,
    advice
) {

    if (!advice) {
        return "";
    }


    // -------------------------------------
    // ARRAY
    // -------------------------------------

    if (Array.isArray(advice)) {

        if (advice.length === 0) {
            return "";
        }


        return `

            <div class="advice-block">

                <h4>
                    ${safeText(title)}
                </h4>

                <ul>

                    ${advice.map(
                        item => `
                            <li>
                                ${safeText(item)}
                            </li>
                        `
                    ).join("")}

                </ul>

            </div>

        `;

    }


    // -------------------------------------
    // STRING
    // -------------------------------------

    if (typeof advice === "string") {

        return `

            <div class="advice-block">

                <h4>
                    ${safeText(title)}
                </h4>

                <p>
                    ${safeText(advice)}
                </p>

            </div>

        `;

    }


    return "";

}


// =========================================
// FARM DETAIL
// =========================================

function createFarmDetail(
    title,
    value
) {

    if (
        value === undefined ||
        value === null ||
        value === ""
    ) {

        return "";

    }


    return `

        <div class="farm-detail">

            <strong>
                ${safeText(title)}:
            </strong>

            <span>
                ${safeText(value)}
            </span>

        </div>

    `;

}


// =========================================
// CONFIDENCE FORMAT
// =========================================

function formatConfidence(confidence) {

    if (
        confidence === undefined ||
        confidence === null ||
        confidence === ""
    ) {

        return t("common.noDataAvailable", "Not available");

    }


    const number =
        Number(confidence);


    if (Number.isNaN(number)) {

        return safeText(confidence);

    }


    return `${number.toFixed(2)}%`;

}


// =========================================
// SAFE TEXT
// =========================================

function safeText(value) {

    if (
        value === undefined ||
        value === null
    ) {

        return "";

    }


    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

}


// =========================================
// ERROR DISPLAY
// =========================================

function showError(
    title,
    message
) {

    resultIcon.textContent = "⚠️";

    resultTitle.textContent = title;

    resultMessage.textContent = message;

    guidanceSection.innerHTML = `

        <h3>${t("aiResult.whatYouShouldDo", "What you should do")}</h3>

        <ul>

            <li>
                ${t("aiResult.returnToUpload", "Return to the crop upload page.")}
            </li>

            <li>
                ${t("aiResult.uploadClearImage", "Upload a clear crop image.")}
            </li>

            <li>
                ${t("aiResult.makeSureCropName", "Make sure the crop name is correct.")}
            </li>

        </ul>

    `;

    guidanceSection.style.display = "block";

    continueButton.style.display = "none";

    resubmitButton.style.display = "block";

}


// =========================================
// CONTINUE
// =========================================

continueButton.addEventListener(
    "click",
    function () {

        const savedCropData =
            localStorage.getItem("cropData");

        let cropStatus = "unknown";

        if (savedCropData) {

            const parsed =
                JSON.parse(savedCropData);

            cropStatus =
                parsed.status || "unknown";

        }

        console.log(
            "CONTINUE CLICKED - NEW CROP STATUS:",
            cropStatus
        );

        console.log(
            "LISTING ID:",
            localStorage.getItem("listingId")
        );

        window.location.href =
            "/frontend/pages/verification-status.html";

    }
);


// =========================================
// RESUBMIT
// =========================================

resubmitButton.addEventListener(
    "click",
    function () {

        localStorage.removeItem(
            "aiResult"
        );

        localStorage.removeItem(
            "cropImage"
        );

        window.location.href =
            "/frontend/pages/upload-crop.html";

    }
);
