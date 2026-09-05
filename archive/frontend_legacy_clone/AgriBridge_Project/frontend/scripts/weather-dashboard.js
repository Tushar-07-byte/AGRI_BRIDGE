// =========================================
// AGRIBRIDGE WEATHER DASHBOARD
// =========================================


// =========================================
// API BASE
// =========================================

const WD_API = "http://127.0.0.1:8000";


// =========================================
// SUPPORTED CROPS (matches ai.py)
// =========================================

const WD_CROPS = [
    "Apple", "Blueberry", "Cherry", "Corn", "Grape",
    "Orange", "Peach", "Pepper", "Potato", "Raspberry",
    "Rice", "Soybean", "Squash", "Strawberry", "Tomato",
    "Wheat"
];


// =========================================
// GROWTH STAGES (matches ai.py)
// =========================================

const WD_GROWTH_STAGES = [
    "Seedling", "Vegetative", "Flowering",
    "Fruiting", "Maturity"
];


// =========================================
// ELEMENTS
// =========================================

const weatherForm =
    document.getElementById("weather-form");

const stateSelect =
    document.getElementById("weather-state");

const districtSelect =
    document.getElementById("weather-district");

const cropSelect =
    document.getElementById("weather-crop");

const growthStageSelect =
    document.getElementById("weather-growth-stage");

const weatherMessage =
    document.getElementById("weather-message");

const getWeatherBtn =
    document.getElementById("get-weather-btn");

const currentWeatherSection =
    document.getElementById("current-weather-section");

const forecastSection =
    document.getElementById("forecast-section");

const advisorySection =
    document.getElementById("advisory-section");


// =========================================
// INITIALIZE
// =========================================

initializeWeatherDashboard();


async function initializeWeatherDashboard() {

    // Load states
    await loadStates();

    // Populate crop dropdown
    populateCrops();

    // Populate growth stage dropdown
    populateGrowthStages();

    // Pre-fill from farmer profile if available
    prefillFromProfile();
}


// =========================================
// LOAD STATES
// =========================================

async function loadStates() {

    try {
        const response =
            await fetch(`${WD_API}/api/weather/states`);

        const data =
            await response.json();

        if (!data.success || !data.states) {
            throw new Error("Failed to load states.");
        }

        stateSelect.innerHTML =
            '<option value="" data-i18n="weatherDashboard.selectState">Select State</option>';

        data.states.forEach(function (state) {
            const option =
                document.createElement("option");
            option.value = state;
            option.textContent = state;
            stateSelect.appendChild(option);
        });

    } catch (error) {
        console.error("Error loading states:", error);
        stateSelect.innerHTML =
            '<option value="">Failed to load states</option>';
    }

}


// =========================================
// STATE → DISTRICT DROPDOWN
// =========================================

async function loadDistrictsForState(state, preselectedDistrict = "") {

    districtSelect.innerHTML =
        '<option value="" data-i18n="weatherDashboard.selectDistrict">Select District</option>';
    districtSelect.disabled = true;

    if (!state) {
        return;
    }

    try {
        const response =
            await fetch(
                `${WD_API}/api/weather/districts/${encodeURIComponent(state)}`
            );

        const data =
            await response.json();

        if (!data.success || !data.districts) {
            throw new Error(data.error || "Failed to load districts.");
        }

        data.districts.forEach(function (d) {
            const option =
                document.createElement("option");
            option.value = d.name;
            option.textContent = d.name;
            districtSelect.appendChild(option);
        });

        districtSelect.disabled = false;

        if (preselectedDistrict) {
            const options = Array.from(districtSelect.options);
            const dMatch = options.find(
                opt => opt.value.toLowerCase() === preselectedDistrict.toLowerCase()
            );
            if (dMatch) {
                districtSelect.value = dMatch.value;
            }
        }

    } catch (error) {
        console.error("Error loading districts:", error);
        districtSelect.innerHTML =
            '<option value="">Failed to load districts</option>';
    }

}

stateSelect.addEventListener("change", function () {
    loadDistrictsForState(stateSelect.value);
});


// =========================================
// POPULATE CROPS
// =========================================

function populateCrops() {

    WD_CROPS.forEach(function (crop) {
        const option =
            document.createElement("option");
        option.value = crop;
        option.textContent = crop;
        cropSelect.appendChild(option);
    });

}


// =========================================
// POPULATE GROWTH STAGES
// =========================================

function populateGrowthStages() {

    WD_GROWTH_STAGES.forEach(function (stage) {
        const option =
            document.createElement("option");
        option.value = stage;
        option.textContent = stage;
        growthStageSelect.appendChild(option);
    });

}


// =========================================
// PREFILL FROM FARMER PROFILE
// =========================================

async function prefillFromProfile() {

    const saved =
        localStorage.getItem("farmerProfile");

    if (!saved) {
        return;
    }

    try {
        const profile = JSON.parse(saved);

        if (profile.state) {
            const options =
                Array.from(stateSelect.options);
            const match = options.find(
                function (opt) {
                    return opt.value.toLowerCase() === profile.state.toLowerCase();
                }
            );

            if (match) {
                stateSelect.value = match.value;
                await loadDistrictsForState(match.value, profile.district || "");
            }
        }

    } catch (e) {
        // Ignore parse errors
    }

}


// =========================================
// FORM SUBMISSION — GET WEATHER
// =========================================

weatherForm.addEventListener(
    "submit",
    handleGetWeather
);


async function handleGetWeather(event) {

    event.preventDefault();

    // Validate form
    if (!weatherForm.checkValidity()) {
        weatherForm.reportValidity();
        return;
    }

    const state = stateSelect.value;
    const district = districtSelect.value;
    const crop = cropSelect.value;
    const growthStage = growthStageSelect.value;

    if (!state || !district || !crop || !growthStage) {
        showMessage(
            typeof translate === "function"
                ? translate("weatherDashboard.fillAll")
                : "Please fill in all fields."
        );
        return;
    }

    // Disable button
    const originalText = getWeatherBtn.textContent;
    getWeatherBtn.disabled = true;
    getWeatherBtn.textContent =
        typeof translate === "function"
            ? translate("weatherDashboard.loading")
            : "Loading...";

    showMessage("");

    // Hide previous results
    currentWeatherSection.style.display = "none";
    forecastSection.style.display = "none";
    advisorySection.style.display = "none";

    try {

        // =====================================
        // FETCH ADVISORY (includes everything)
        // =====================================

        const response =
            await fetch(
                `${WD_API}/api/weather/advisory`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body: JSON.stringify({
                        state: state,
                        district: district,
                        crop: crop,
                        growth_stage: growthStage
                    })
                }
            );

        const data =
            await response.json();

        console.log(
            "Weather advisory response:",
            data
        );

        if (!data.success) {
            throw new Error(
                data.error || "Failed to get weather."
            );
        }

        // =====================================
        // DISPLAY CURRENT WEATHER
        // =====================================

        displayCurrentWeather(
            data.location,
            data.current_weather
        );

        // =====================================
        // DISPLAY FORECAST
        // =====================================

        displayForecast(data.forecast);

        // =====================================
        // DISPLAY ADVISORY
        // =====================================

        displayAdvisory(
            data.crop,
            data.growth_stage,
            data.agricultural_advisory
        );

    } catch (error) {

        console.error(
            "Weather dashboard error:",
            error
        );

        showMessage(
            `${typeof translate === "function"
                ? (translate("weatherDashboard.error") || translate("common.error") || "Error")
                : "Error"}: ${error.message}`
        );

    } finally {

        getWeatherBtn.disabled = false;
        getWeatherBtn.textContent = originalText;

    }

}


// =========================================
// DISPLAY CURRENT WEATHER
// =========================================

function displayCurrentWeather(
    location,
    weather
) {

    document.getElementById(
        "current-weather-location"
    ).textContent =
        `📍 ${location.district}, ${location.state}`;

    document.getElementById("wd-temperature")
        .textContent =
        `${weather.temperature}°C`;

    document.getElementById("wd-humidity")
        .textContent =
        `${weather.humidity}%`;

    document.getElementById("wd-rainfall")
        .textContent =
        `${weather.rainfall} mm`;

    document.getElementById("wd-wind-speed")
        .textContent =
        `${weather.wind_speed} km/h`;

    document.getElementById("wd-condition")
        .textContent =
        weather.weather_condition;

    currentWeatherSection.style.display = "block";

}


// =========================================
// DISPLAY 15-DAY FORECAST
// =========================================

function displayForecast(forecast) {

    const container =
        document.getElementById(
            "forecast-container"
        );

    container.innerHTML = "";

    forecast.forEach(function (day, index) {

        const card =
            document.createElement("div");

        card.classList.add("forecast-day-card");

        const dateObj =
            new Date(day.date);

        const dayName =
            index === 0
                ? (typeof translate === "function"
                    ? (translate("weatherDashboard.today") || translate("common.today") || "Today")
                    : "Today")
                : dateObj.toLocaleDateString(
                    undefined,
                    { weekday: "short" }
                );

        const dateStr =
            dateObj.toLocaleDateString(
                "en-IN",
                { month: "short", day: "numeric" }
            );

        card.innerHTML = `
            <div class="forecast-day-name">
                ${dayName}
            </div>
            <div class="forecast-date">
                ${dateStr}
            </div>
            <div class="forecast-condition">
                ${day.weather_condition}
            </div>
            <div class="forecast-temps">
                <span class="temp-high">
                    ${day.temperature_max}°
                </span>
                <span class="temp-sep">/</span>
                <span class="temp-low">
                    ${day.temperature_min}°
                </span>
            </div>
            <div class="forecast-rain">
                🌧️ ${day.rain_probability}% · ${day.rainfall}mm
            </div>
        `;

        container.appendChild(card);

    });

    forecastSection.style.display = "block";

}


// =========================================
// DISPLAY AGRICULTURAL ADVISORY
// =========================================

function displayAdvisory(
    crop,
    growthStage,
    advisory
) {

    const container =
        document.getElementById(
            "advisory-content"
        );

    // Convert markdown-like headings to HTML
    let html = advisory;

    // Bold headings
    html = html.replace(
        /\*\*(.+?)\*\*/g,
        "<strong>$1</strong>"
    );

    // Line breaks
    html = html.replace(
        /\n/g,
        "<br>"
    );

    container.innerHTML = `
        <div class="advisory-header">
            <span class="advisory-crop">
                🌱 ${crop} — ${growthStage}
            </span>
        </div>
        <div class="advisory-body">
            ${html}
        </div>
    `;

    advisorySection.style.display = "block";

}


// =========================================
// SHOW MESSAGE
// =========================================

function showMessage(msg) {
    weatherMessage.textContent = msg;
}
