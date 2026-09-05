// =========================================
// CROP RECOMMENDATION
// =========================================

const API_BASE = "http://127.0.0.1:8000";

const RECOMMENDATION_API = `${API_BASE}/recommend-crop`;
const STATES_API = `${API_BASE}/recommend-crop/states`;
const DISTRICTS_API = `${API_BASE}/recommend-crop/districts`;
const SEASONS_API = `${API_BASE}/recommend-crop/seasons`;
const SOIL_TYPE_API = `${API_BASE}/recommend-crop/soil-type`;


// =========================================
// DOM ELEMENTS
// =========================================

const recForm =
    document.getElementById("recommendation-form");

const stateSelect =
    document.getElementById("rec-state");

const districtSelect =
    document.getElementById("rec-district");

const seasonSelect =
    document.getElementById("rec-season");

const soilTypeSelect =
    document.getElementById("rec-soil-type");

const phInput =
    document.getElementById("rec-ph");

const formMessage =
    document.getElementById("rec-message");

const recommendButton =
    document.getElementById("rec-submit-btn");

const resultsSection =
    document.getElementById("rec-results-section");

const newRecommendationButton =
    document.getElementById("new-recommendation-button");


// =========================================
// HELPER: SHOW MESSAGE
// =========================================

function showMessage(text, color) {
    formMessage.textContent = text;
    formMessage.style.color = color || "#c62828";
}


// =========================================
// HELPER: FETCH JSON
// =========================================

async function fetchJson(url) {
    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(
            `Request failed with status ${response.status}`
        );
    }

    return await response.json();
}


// =========================================
// LOAD STATES ON PAGE LOAD
// =========================================

async function loadStates() {

    try {

        const data = await fetchJson(STATES_API);

        stateSelect.innerHTML =
            '<option value="">Select State</option>';

        data.states.forEach(function (state) {
            const option =
                document.createElement("option");
            option.value = state;
            option.textContent = state;
            stateSelect.appendChild(option);
        });

    } catch (error) {

        console.error("Failed to load states:", error);
        showMessage(
            typeof translate === "function" ? translate("recommendation.errors.loadStatesFailed") : "Failed to load states. Please refresh the page.",
            "#c62828"
        );

    }

}

loadStates();


// =========================================
// STATE → DISTRICTS
// =========================================

stateSelect.addEventListener(
    "change",
    async function () {

        const state = stateSelect.value;

        // Reset downstream
        districtSelect.innerHTML =
            '<option value="">Select District</option>';
        districtSelect.disabled = true;

        seasonSelect.innerHTML =
            '<option value="">Select Season</option>';
        seasonSelect.disabled = true;

        soilTypeSelect.innerHTML =
            '<option value="">Select Soil Type</option>';
        soilTypeSelect.disabled = true;

        if (!state) return;

        try {

            const data = await fetchJson(
                `${DISTRICTS_API}/${encodeURIComponent(state)}`
            );

            data.districts.forEach(function (district) {
                const option =
                    document.createElement("option");
                option.value = district;
                option.textContent = district;
                districtSelect.appendChild(option);
            });

            districtSelect.disabled = false;

        } catch (error) {

            console.error(
                "Failed to load districts:", error
            );
            showMessage(
                typeof translate === "function" ? translate("recommendation.errors.loadDistrictsFailed") : "Failed to load districts.",
                "#c62828"
            );

        }

    }
);


// =========================================
// DISTRICT → SEASONS
// =========================================

districtSelect.addEventListener(
    "change",
    async function () {

        const state = stateSelect.value;
        const district = districtSelect.value;

        // Reset downstream
        seasonSelect.innerHTML =
            '<option value="">Select Season</option>';
        seasonSelect.disabled = true;

        soilTypeSelect.innerHTML =
            '<option value="">Select Soil Type</option>';
        soilTypeSelect.disabled = true;

        if (!district) return;

        try {

            const data = await fetchJson(
                `${SEASONS_API}/${encodeURIComponent(state)}/${encodeURIComponent(district)}`
            );

            data.seasons.forEach(function (season) {
                const option =
                    document.createElement("option");
                option.value = season;
                option.textContent = season;
                seasonSelect.appendChild(option);
            });

            seasonSelect.disabled = false;

        } catch (error) {

            console.error(
                "Failed to load seasons:", error
            );
            showMessage(
                "Failed to load seasons.",
                "#c62828"
            );

        }

    }
);


// =========================================
// SEASON → SOIL TYPE (Auto-select)
// =========================================

seasonSelect.addEventListener(
    "change",
    async function () {

        const state = stateSelect.value;
        const district = districtSelect.value;
        const season = seasonSelect.value;

        // Reset soil type
        soilTypeSelect.innerHTML =
            '<option value="">Select Soil Type</option>';
        soilTypeSelect.disabled = true;

        if (!season) return;

        try {

            const data = await fetchJson(
                `${SOIL_TYPE_API}/${encodeURIComponent(state)}/${encodeURIComponent(district)}/${encodeURIComponent(season)}`
            );

            if (data.soil_type) {

                const option =
                    document.createElement("option");
                option.value = data.soil_type;
                option.textContent = data.soil_type;
                soilTypeSelect.appendChild(option);

                soilTypeSelect.value = data.soil_type;
                soilTypeSelect.disabled = true;

            } else {

                soilTypeSelect.innerHTML =
                    '<option value="">No soil type available</option>';

            }

        } catch (error) {

            console.error(
                "Failed to load soil type:", error
            );
            showMessage(
                typeof translate === "function" ? translate("recommendation.errors.loadSoilFailed") : "Failed to load soil type.",
                "#c62828"
            );

        }

    }
);


// =========================================
// FORM SUBMISSION
// =========================================

recForm.addEventListener(
    "submit",
    async function (event) {

        event.preventDefault();

        // ------------------------------------
        // Get values
        // ------------------------------------

        const state = stateSelect.value.trim();
        const district = districtSelect.value.trim();
        const season = seasonSelect.value.trim();
        const soilType = soilTypeSelect.value.trim();
        const phValue = phInput.value.trim();

        // ------------------------------------
        // Validate required fields
        // ------------------------------------

        if (!state || !district || !season || !soilType) {
        showMessage(
            typeof translate === "function" ? translate("recommendation.errors.fillRequired") : "Please fill in all required fields.",
            "#c62828"
        );
            return;
        }

        // ------------------------------------
        // Validate pH range
        // ------------------------------------

        let ph = null;

        if (phValue !== "") {

            ph = parseFloat(phValue);

            if (isNaN(ph) || ph < 0 || ph > 14) {
                showMessage(
                    typeof translate === "function" ? translate("recommendation.errors.invalidPh") : "Soil pH must be between 0 and 14.",
                    "#c62828"
                );
                return;
            }

        }

        // ------------------------------------
        // Disable button & show loading
        // ------------------------------------

        const originalText =
            recommendButton.textContent;

        recommendButton.disabled = true;
        recommendButton.textContent =
            "Getting recommendations...";

        showMessage(
            typeof translate === "function" ? translate("recommendation.gettingRecommendations") : "Getting recommendations...",
            "#1565C0"
        );

        // ------------------------------------
        // Build request payload
        // ------------------------------------

        const payload = {
            state: state,
            district: district,
            season: season,
            soil_type: soilType,
            ph: ph
        };

        console.log(
            "Recommendation request:", payload
        );

        // ------------------------------------
        // Send request
        // ------------------------------------

        try {

            const response = await fetch(
                RECOMMENDATION_API,
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body: JSON.stringify(payload)
                }
            );

            const data = await response.json();

            console.log(
                "Recommendation response:", data
            );

            // --------------------------------
            // Handle error response
            // --------------------------------

            if (!response.ok) {

                const errorMessage =
                    data.detail ||
                    data.message ||
                    "Failed to get recommendation.";

                showMessage(errorMessage, "#c62828");

                return;

            }

            // --------------------------------
            // Handle engine error status
            // --------------------------------

            if (data.status === "error") {

                showMessage(
                    data.message,
                    "#c62828"
                );

                return;

            }

            // --------------------------------
            // Display results
            // --------------------------------

            displayResults(data);

            // --------------------------------
            // Save to localStorage
            // --------------------------------

            localStorage.setItem(
                "cropRecommendation",
                JSON.stringify(data)
            );

        } catch (error) {

            console.error(
                "Recommendation request failed:",
                error
            );

            showMessage(
                typeof translate === "function" ? translate("recommendation.errors.networkError") : "Network error. Please check your connection and try again.",
                "#c62828"
            );

        } finally {

            // --------------------------------
            // Re-enable button
            // --------------------------------

            recommendButton.disabled = false;
            recommendButton.textContent =
                originalText;

        }

    }
);


// =========================================
// DISPLAY RESULTS
// =========================================

function displayResults(data) {

    // ------------------------------------
    // Hide form, show results
    // ------------------------------------

    recForm.closest(".rec-form-card")
        .style.display = "none";

    resultsSection.style.display = "block";

    // ------------------------------------
    // Summary Bar
    // ------------------------------------

    const summaryBar =
        document.getElementById("rec-summary-bar");

    const phStatusLabel =
        data.soil.ph_status === "Suitable"
            ? "✅"
            : data.soil.ph_status === "Outside recommended range"
                ? "⚠️"
                : "ℹ️";

    summaryBar.innerHTML = `
        <div class="rec-summary-item">
            <span class="rec-summary-label">Location</span>
            <span class="rec-summary-value">${data.location.state}, ${data.location.district}</span>
        </div>
        <div class="rec-summary-item">
            <span class="rec-summary-label">Season</span>
            <span class="rec-summary-value">${data.season}</span>
        </div>
        <div class="rec-summary-item">
            <span class="rec-summary-label">Soil Type</span>
            <span class="rec-summary-value">${data.soil.type}</span>
        </div>
        <div class="rec-summary-item">
            <span class="rec-summary-label">pH Range</span>
            <span class="rec-summary-value">${data.soil.recommended_ph} ${phStatusLabel} ${data.soil.ph_status}</span>
        </div>
    `;

    // ------------------------------------
    // Crops Metadata & Rendering
    // ------------------------------------

    const CROP_META = {
        "wheat": { emoji: "🌾", category: "Cereal / Grain", water: "💧 Medium", duration: "⏱️ 110-130 Days" },
        "rice": { emoji: "🍚", category: "Cereal / Staple", water: "💧 High", duration: "⏱️ 120-150 Days" },
        "maize": { emoji: "🌽", category: "Coarse Grain", water: "💧 Medium", duration: "⏱️ 90-110 Days" },
        "cotton": { emoji: "☁️", category: "Commercial Cash Crop", water: "💧 Medium-High", duration: "⏱️ 150-180 Days" },
        "sugarcane": { emoji: "🎋", category: "Commercial Cash Crop", water: "💧 High", duration: "⏱️ 10-12 Months" },
        "potato": { emoji: "🥔", category: "Horticulture / Tuber", water: "💧 Medium", duration: "⏱️ 80-100 Days" },
        "tomato": { emoji: "🍅", category: "Horticulture / Vegetable", water: "💧 Medium", duration: "⏱️ 90-120 Days" },
        "onion": { emoji: "🧅", category: "Horticulture / Bulb", water: "💧 Medium", duration: "⏱️ 110-140 Days" },
        "chilli": { emoji: "🌶️", category: "Spice / Cash Crop", water: "💧 Low-Medium", duration: "⏱️ 120-150 Days" },
        "mustard": { emoji: "🌼", category: "Oilseed", water: "💧 Low-Medium", duration: "⏱️ 90-110 Days" },
        "soybean": { emoji: "🌿", category: "Legume / Oilseed", water: "💧 Medium", duration: "⏱️ 95-105 Days" },
        "groundnut": { emoji: "🥜", category: "Oilseed", water: "💧 Medium", duration: "⏱️ 100-120 Days" },
        "gram": { emoji: "🌱", category: "Pulse / Legume", water: "💧 Low", duration: "⏱️ 90-110 Days" },
        "tur": { emoji: "🌱", category: "Pulse / Legume", water: "💧 Low-Medium", duration: "⏱️ 150-180 Days" },
        "moong": { emoji: "🌱", category: "Pulse / Short Duration", water: "💧 Low", duration: "⏱️ 60-70 Days" },
        "urad": { emoji: "🌱", category: "Pulse / Legume", water: "💧 Low", duration: "⏱️ 70-80 Days" },
        "barley": { emoji: "🌾", category: "Cereal / Fodder", water: "💧 Low-Medium", duration: "⏱️ 100-120 Days" },
        "jowar": { emoji: "🌾", category: "Millets / Nutri-Cereal", water: "💧 Low", duration: "⏱️ 100-115 Days" },
        "bajra": { emoji: "🌾", category: "Millets / Drought-Hardy", water: "💧 Low", duration: "⏱️ 80-90 Days" },
        "ragi": { emoji: "🌾", category: "Finger Millet", water: "💧 Low-Medium", duration: "⏱️ 105-120 Days" },
        "sunflower": { emoji: "🌻", category: "Oilseed", water: "💧 Medium", duration: "⏱️ 85-95 Days" },
        "jute": { emoji: "🧶", category: "Fibre Crop", water: "💧 High", duration: "⏱️ 120-140 Days" }
    };

    const cropsContainer =
        document.getElementById("rec-crops-container");

    cropsContainer.innerHTML = "";

    data.recommended_crops.forEach(function (crop, index) {
        const cropKey = crop.toLowerCase().trim();
        const meta = CROP_META[cropKey] || { emoji: "🌱", category: "Agricultural Crop", water: "💧 Medium", duration: "⏱️ Seasonal" };
        
        let matchBadgeClass = "badge-standard-match";
        let matchBadgeText = "✓ Suitable";
        if (index === 0) {
            matchBadgeClass = "badge-top-match";
            matchBadgeText = "⭐ Top Match";
        } else if (index === 1) {
            matchBadgeClass = "badge-high-match";
            matchBadgeText = "🌱 High Match";
        }

        const cropCard = document.createElement("div");
        cropCard.classList.add("rec-crop-card");

        cropCard.innerHTML = `
            <div class="rec-crop-card-top">
                <div class="rec-crop-icon-wrap">${meta.emoji}</div>
                <span class="rec-crop-badge ${matchBadgeClass}">${matchBadgeText}</span>
            </div>
            <div class="rec-crop-body">
                <h3 class="rec-crop-name">${crop}</h3>
                <span class="rec-crop-category">${meta.category}</span>
                <div class="rec-crop-meta-chips">
                    <span class="meta-chip">${meta.water}</span>
                    <span class="meta-chip">${meta.duration}</span>
                </div>
            </div>
            <div class="rec-crop-actions">
                <a href="/frontend/pages/farmer-dashboard.html" class="crop-action-btn btn-plan">🌱 Plan Sowing</a>
                <a href="/frontend/pages/crop-listings.html" class="crop-action-btn btn-mandi">📈 Mandi Rates</a>
            </div>
        `;

        cropsContainer.appendChild(cropCard);
    });

}


// =========================================
// NEW RECOMMENDATION BUTTON
// =========================================

if (newRecommendationButton) {
    newRecommendationButton.addEventListener(
        "click",
        function () {

            // Hide results, show form
            resultsSection.style.display = "none";

            recForm.closest(".rec-form-card")
                .style.display = "block";

            // Reset message
            formMessage.textContent = "";

        }
    );
}


// =========================================
// LOAD SAVED RECOMMENDATION
// =========================================

(function loadSavedRecommendation() {

    const saved =
        localStorage.getItem("cropRecommendation");

    if (saved) {

        try {

            const data = JSON.parse(saved);

            if (
                data &&
                data.status === "success" &&
                data.recommended_crops
            ) {

                displayResults(data);

            }

        } catch (error) {

            console.error(
                "Failed to load saved recommendation:",
                error
            );

        }

    }

})();

// =========================================
// SYNC NAVBAR USER NAME
// =========================================

(function syncNavbarUser() {
    try {
        const user = window.AgriBridgeAuth ? window.AgriBridgeAuth.getUser() : JSON.parse(localStorage.getItem("agribridge_user") || "{}");
        const userNameEl = document.getElementById("navbarUserName");
        if (userNameEl && user && user.name) {
            userNameEl.textContent = user.name;
        }
    } catch (e) {}
})();

