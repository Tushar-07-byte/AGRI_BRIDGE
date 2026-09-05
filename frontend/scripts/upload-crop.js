// =========================================
// AGRIBRIDGE UPLOAD + AI + LISTING FLOW
// =========================================

console.log(
    "=== AGRIBRIDGE UPLOAD SCRIPT START ===",
    location.href
);


// =========================================
// ELEMENTS
// =========================================

const cropForm = document.getElementById("crop-form");
const cropName = document.getElementById("crop-name");
const quantity = document.getElementById("quantity");
const harvestDate = document.getElementById("harvest-date");
const locationInput = document.getElementById("location");
const farmArea = document.getElementById("farm-area");
const growthStage = document.getElementById("growth-stage");
const irrigationMethod = document.getElementById("irrigation-method");
const irrigationStatus = document.getElementById("irrigation-status");
const recentRainfall = document.getElementById("recent-rainfall");
const humidity = document.getElementById("humidity");
const fertilizerApplied = document.getElementById("fertilizer-applied");
const previousCrop = document.getElementById("previous-crop");
const diseaseSeverity = document.getElementById("disease-severity");
const cropImage = document.getElementById("crop-image");
const imagePreview = document.getElementById("image-preview");
const analyzeButton = document.getElementById("analyze-button");
const message = document.getElementById("message");


// =========================================
// API URLs
// =========================================

const API_BASE = "http://127.0.0.1:8000";

const AI_API_URL =
    `${API_BASE}/api/ai/predict`;

const LISTING_API_URL =
    `${API_BASE}/api/listings/`;

const RESULT_URL =
    "/frontend/pages/ai-result.html";


// =========================================
// CHECK ELEMENTS
// =========================================

console.log("Analyze button:", analyzeButton);
console.log("Crop image:", cropImage);
console.log("AI API:", AI_API_URL);
console.log("Listing API:", LISTING_API_URL);


// =========================================
// BLOCK FORM SUBMISSION
// =========================================

if (cropForm) {

    cropForm.addEventListener("submit", function (event) {

        event.preventDefault();

        console.log(
            "Blocked unexpected form submission."
        );

    });

}


// =========================================
// IMAGE PREVIEW
// =========================================

if (cropImage) {

    cropImage.addEventListener("change", function () {

        const file = cropImage.files[0];

        if (!file) {

            imagePreview.removeAttribute("src");
            imagePreview.style.display = "none";

            return;
        }

        if (
            ![
                "image/jpeg",
                "image/jpg",
                "image/png"
            ].includes(file.type)
        ) {

            cropImage.value = "";

            imagePreview.style.display = "none";

            message.textContent =
                typeof translate === "function"
                    ? translate("crop.upload.invalidImageType")
                    : "Please select a JPG, JPEG, or PNG image.";

            return;
        }

        imagePreview.src =
            URL.createObjectURL(file);

        imagePreview.style.display = "block";

        message.textContent = "";

    });

}


// =========================================
// FILE → BASE64
// =========================================

function readAsDataUrl(file) {

    return new Promise((resolve, reject) => {

        const reader = new FileReader();

        reader.onload = () =>
            resolve(reader.result);

        reader.onerror = () =>
            reject(
                new Error(
                    "Unable to convert crop image."
                )
            );

        reader.readAsDataURL(file);

    });

}


// =========================================
// CREATE LISTING
// =========================================

async function createListing(
    crop,
    amount,
    date,
    farmLocation,
    aiResult,
    image
) {

    console.log(
        "Creating listing..."
    );


    // -----------------------------------------
    // Extract AI information
    // -----------------------------------------

    const prediction =
        aiResult.prediction || {};

    const disease =
        aiResult.disease || {};


    const plant =
        prediction.plant || crop;

    const confidence =
        prediction.confidence != null
            ? Number(prediction.confidence) / 100
            : null;

    const healthStatus =
        disease.disease ||
        "Unknown";


    // -----------------------------------------
    // Listing data
    // -----------------------------------------

    const listingData = {

        farmer_id: 1,

        crop_type: plant,

        photo_path:
            aiResult.uploaded_image_path || image.name,

        health_status:
            healthStatus,

        confidence:
            confidence,

        harvest_date:
            date,

        quantity_est:
            Number(amount),

        // The database makes this crop available only after the field-agent
        // verification changes from pending to verified.
        status:
            "pending"

    };


    console.log(
        "Listing data:",
        listingData
    );


    // -----------------------------------------
    // Send to FastAPI
    // -----------------------------------------

    const response =
        await fetch(
            LISTING_API_URL,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body:
                    JSON.stringify(
                        listingData
                    )
            }
        );


    const payload =
        await response.json();


    console.log(
        "Listing API response:",
        payload
    );


    if (
        !response.ok ||
        !payload.success ||
        !payload.listing
    ) {

        throw new Error(
            payload.detail ||
            "Failed to create listing."
        );

    }


    return payload.listing;

}


// =========================================
// ANALYZE CROP
// =========================================

async function analyzeCrop(event) {

    event.preventDefault();

    console.log(
        "=== ANALYZE FUNCTION STARTED ==="
    );


    // -----------------------------------------
    // Validate form
    // -----------------------------------------

    if (!cropForm.checkValidity()) {

        cropForm.reportValidity();

        return;
    }


    const crop =
        cropName.value.trim();

    const amount =
        quantity ? quantity.value : (farmArea && farmArea.value ? parseFloat(farmArea.value) * 1000 : 1000);

    const date =
        harvestDate.value;

    const farmLocation =
        locationInput.value.trim();

    const image =
        cropImage.files[0];


    console.log("Crop:", crop);
    console.log("Quantity:", amount);
    console.log("Harvest date:", date);
    console.log("Location:", farmLocation);
    console.log("Image:", image);    if (!image) {

        message.textContent =
            typeof translate === "function"
                ? translate("crop.upload.selectImageError")
                : "Please select a crop image.";

        return;

    }


    // -----------------------------------------
    // Disable button
    // -----------------------------------------

    const originalText =
        analyzeButton.textContent;

    analyzeButton.disabled = true;

    analyzeButton.textContent =
        typeof translate === "function"
            ? translate("crop.upload.analyzing")
            : "Analyzing...";


    message.textContent =
        typeof translate === "function"
            ? translate("crop.upload.sendingRequest")
            : "Sending request to FastAPI...";


    try {

        // =====================================
        // FARM DATA
        // =====================================

        const farm = {

            farm_area: Number(farmArea.value),

            growth_stage: growthStage.value,

            irrigation_method: irrigationMethod.value,

            irrigation_status: irrigationStatus.value,

            recent_rainfall: recentRainfall.value,

            humidity: humidity.value,

            fertilizer_applied: fertilizerApplied.value.trim(),

            previous_crop: previousCrop.value.trim(),

            disease_severity: diseaseSeverity.value,

            region: farmLocation

        };


        // =====================================
        // AI REQUEST
        // =====================================

        const formData =
            new FormData();

        formData.append(
            "plant",
            crop
        );

        formData.append(
            "farm",
            JSON.stringify(farm)
        );

        formData.append(
            "image",
            image
        );


        console.log(
            "AI request starting:",
            AI_API_URL
        );


        const aiResponse =
            await fetch(
                AI_API_URL,
                {
                    method: "POST",
                    body: formData
                }
            );


        const aiPayload =
            await aiResponse.json();


        console.log(
            "AI response:",
            aiPayload
        );


        if (
            !aiResponse.ok ||
            !aiPayload.success ||
            !aiPayload.result
        ) {

            throw new Error(
                aiPayload.detail ||
                `AI request failed with status ${aiResponse.status}.`
            );

        }


        // =====================================
        // AI RESULT & DIAGNOSTIC RECORD
        // =====================================

        const aiResult =
            aiPayload.result;

        const diseaseRecord =
            aiResult.disease_record || {
                status: "PENDING_AGENT_REVIEW",
                locked_prescription: true
            };

        message.textContent =
            typeof translate === "function"
                ? translate("crop.upload.analysisComplete")
                : "AI analysis complete. Dispatched to Field Agent Hub for review...";

        // =====================================
        // IMAGE BASE64
        // =====================================

        const imageDataUrl =
            await readAsDataUrl(image);

        // =====================================
        // SAVE AI RESULT & DIAGNOSTIC STATE
        // =====================================

        localStorage.setItem(
            "aiResult",
            JSON.stringify(aiResult)
        );

        localStorage.setItem(
            "diseaseRecord",
            JSON.stringify(diseaseRecord)
        );

        // =====================================
        // SAVE CROP DIAGNOSTIC DATA (Decoupled from Marketplace)
        // =====================================

        const cropData = {
            cropName: crop,
            quantity: Number(amount),
            harvestDate: date,
            location: farmLocation,
            status: diseaseRecord.status || "PENDING_AGENT_REVIEW",
            diseaseRecordId: diseaseRecord.id
        };

        localStorage.setItem(
            "cropData",
            JSON.stringify(cropData)
        );


        // =====================================
        // SAVE LISTING ID (separate key)
        //
        // verification-status.js reads this
        // key directly. It must be set here
        // =====================================
        // SAVE IMAGE
        // =====================================

        localStorage.setItem(
            "cropImage",
            imageDataUrl
        );

        console.log(
            "CROP DIAGNOSTIC DATA SAVED:",
            cropData
        );

        // =====================================
        // NAVIGATE TO AI RESULT
        // =====================================

        message.textContent =
            typeof translate === "function"
                ? translate("crop.upload.listingCreated")
                : "Diagnosis queued for field verification. Opening AI result...";



        const resultUrl =
            new URL(
                RESULT_URL,
                location.origin
            ).href;


        console.log(
            "Navigating to:",
            resultUrl
        );


        window.location.assign(
            resultUrl
        );

    }

    catch (error) {

        console.error(
            "AI/listing flow failed:",
            error
        );

        let userFriendlyMsg = error.message || "An unexpected error occurred.";
        if (userFriendlyMsg.includes("Failed to fetch") || userFriendlyMsg.includes("NetworkError") || userFriendlyMsg.includes("Network request failed")) {
            userFriendlyMsg = "Unable to connect to server — please check your connection and try again.";
        } else if (userFriendlyMsg.includes("500") || userFriendlyMsg.includes("Internal Server Error")) {
            userFriendlyMsg = "Service temporarily unavailable — please try again in a few moments.";
        }

        message.textContent = `⚠️ ${userFriendlyMsg}`;

        analyzeButton.disabled =
            false;

        analyzeButton.textContent =
            originalText;

    }

}


// =========================================
// SINGLE CLICK LISTENER
// =========================================

analyzeButton.addEventListener(
    "click",
    analyzeCrop
);


console.log(
    "One click listener attached to #analyze-button."
);
