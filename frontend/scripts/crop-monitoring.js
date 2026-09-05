// ==========================================================================
// AGRIBRIDGE AI — ULTRA CROP MONITORING & IoT TELEMETRY CONTROLLER
// Problem Statement: SH-AGR-001 — Autonomous Farm-to-Field Advisory & Action Orchestration Agents
// Consumes POST /api/v1/monitoring/analyze and POST /api/v1/monitoring/notification/action
// ==========================================================================

console.log("=== ULTRA CROP MONITORING CONTROLLER INITIALIZED ===");

// DOM Elements - Inputs
const stateSelect = document.getElementById("state-select");
const districtSelect = document.getElementById("district-select");
const villageInput = document.getElementById("village-input");
const farmIdInput = document.getElementById("farm-id-input");
const fieldIdInput = document.getElementById("field-id-input");
const cropSelect = document.getElementById("crop-select");
const plantingDateInput = document.getElementById("planting-date");
const stageModeSelect = document.getElementById("stage-mode-select");
const manualStageGroup = document.getElementById("manual-stage-group");
const manualStageSelect = document.getElementById("manual-stage-select");
const cropListedCheckbox = document.getElementById("crop-listed-checkbox");
const toggleTelemetryBtn = document.getElementById("toggle-telemetry-btn");
const telemetryDrawer = document.getElementById("telemetry-drawer");
const monitoringForm = document.getElementById("monitoring-form");
const loadingSpinner = document.getElementById("loading-spinner");
const monitoringResults = document.getElementById("monitoring-results");

// Telemetry Input Elements
const iotMoisture = document.getElementById("iot-moisture");
const iotSoilTemp = document.getElementById("iot-soil-temp");
const iotAirTemp = document.getElementById("iot-air-temp");
const iotHumidity = document.getElementById("iot-humidity");
const iotRainfall = document.getElementById("iot-rainfall");
const iotLeafWetness = document.getElementById("iot-leaf-wetness");
const iotEc = document.getElementById("iot-ec");
const iotPh = document.getElementById("iot-ph");
const iotNitrogen = document.getElementById("iot-nitrogen");
const iotPhosphorus = document.getElementById("iot-phosphorus");
const iotPotassium = document.getElementById("iot-potassium");
const iotOrganicCarbon = document.getElementById("iot-organic-carbon");

// Results Elements
const resCropHeader = document.getElementById("res-crop-header");
const resLocationHeader = document.getElementById("res-location-header");
const resFarmHeader = document.getElementById("res-farm-header");
const dapBadge = document.getElementById("dap-badge");
const activeStageTitle = document.getElementById("active-stage-title");
const stageStatusText = document.getElementById("stage-status-text");
const stageProgressFill = document.getElementById("stage-progress-fill");
const nextStageText = document.getElementById("next-stage-text");
const daysToHarvestText = document.getElementById("days-to-harvest-text");

// Pre-Harvest Marketplace Reminder Banner
const marketplaceReminderBanner = document.getElementById("marketplace-reminder-banner");
const mprTitle = document.getElementById("mpr-title");
const mprBadge = document.getElementById("mpr-badge");
const mprText = document.getElementById("mpr-text");
const mprListBtn = document.getElementById("mpr-list-btn");

// Weather Elements
const weatherSourceBadge = document.getElementById("weather-source-badge");
const weatherTempHeadline = document.getElementById("weather-temp-headline");
const weatherDecisionDetail = document.getElementById("weather-decision-detail");
const wmHumidityVal = document.getElementById("wm-humidity-val");
const wmWindVal = document.getElementById("wm-wind-val");
const wmRainVal = document.getElementById("wm-rain-val");
const dailyPriorityVal = document.getElementById("daily-priority-val");

// IoT Display Elements
const iotValMoisture = document.getElementById("iot-val-moisture");
const iotValSoilTemp = document.getElementById("iot-val-soil-temp");
const iotValAirTemp = document.getElementById("iot-val-air-temp");
const iotValRh = document.getElementById("iot-val-rh");
const iotValWetness = document.getElementById("iot-val-wetness");
const iotValEc = document.getElementById("iot-val-ec");
const iotValPh = document.getElementById("iot-val-ph");
const iotValLight = document.getElementById("iot-val-light");

// Calendar & Fertility Elements
const stageTimelineCards = document.getElementById("stage-timeline-cards");
const calendarEventsList = document.getElementById("calendar-events-list");
const soilFertilityGrid = document.getElementById("soil-fertility-grid");
const fertilityDeficiencyCallout = document.getElementById("fertility-deficiency-callout");
const todayActionsContainer = document.getElementById("today-actions-container");

// Fertilizer Elements
const fertPriorityBadge = document.getElementById("fert-priority-badge");
const fertWhat = document.getElementById("fert-what");
const fertWhy = document.getElementById("fert-why");
const fertHow = document.getElementById("fert-how");
const fertWhen = document.getElementById("fert-when");
const fertWeatherAdjustment = document.getElementById("fert-weather-adjustment");
const fertWeatherAdjustmentText = document.getElementById("fert-weather-adjustment-text");

// Decision Matrix Elements
const decIrrigationStatus = document.getElementById("dec-irrigation-status");
const decIrrigationReason = document.getElementById("dec-irrigation-reason");
const decDiseaseStatus = document.getElementById("dec-disease-status");
const decDiseaseReason = document.getElementById("dec-disease-reason");
const decPestStatus = document.getElementById("dec-pest-status");
const decPestReason = document.getElementById("dec-pest-reason");
const decStressStatus = document.getElementById("dec-stress-status");
const decStressReason = document.getElementById("dec-stress-reason");
const decFertilizerStatus = document.getElementById("dec-fertilizer-status");
const decFertilizerReason = document.getElementById("dec-fertilizer-reason");

// Notifications & Guidance
const notificationsList = document.getElementById("notifications-list");
const geminiGuidanceText = document.getElementById("gemini-guidance-text");

// Tool Buttons
const btnListen = document.getElementById("btn-listen");
const ttsLabel = document.getElementById("tts-label");
const btnPrintPlan = document.getElementById("btn-print-plan");
const btnAskVoice = document.getElementById("btn-ask-voice");

let currentMonitoringData = null;
let isSpeaking = false;

// ==========================================================================
// INITIALIZATION
// ==========================================================================
document.addEventListener("DOMContentLoaded", async function () {
    // Check URL parameters or localStorage
    const urlParams = new URLSearchParams(window.location.search);
    const initialCrop = urlParams.get("crop") || localStorage.getItem("cropMonitoringSelectedCrop") || "Wheat";
    const initialPlantingDate = urlParams.get("planting_date") || localStorage.getItem("cropMonitoringPlantingDate") || null;
    const initialFieldId = urlParams.get("field_id") || localStorage.getItem("cropMonitoringFieldId") || "FIELD_001";

    if (initialPlantingDate) {
        plantingDateInput.value = initialPlantingDate;
    } else {
        // Default planting date: 34 days ago (CRI stage for Wheat)
        const defaultDate = new Date();
        defaultDate.setDate(defaultDate.getDate() - 34);
        plantingDateInput.value = defaultDate.toISOString().split("T")[0];
    }

    if (initialFieldId) {
        fieldIdInput.value = initialFieldId;
    }

    await loadStates();
    await loadCrops(initialCrop);
    setupEventListeners();

    // Auto run analysis on load
    executeMonitoringAnalysis();
});

function setupEventListeners() {
    stateSelect.addEventListener("change", function () {
        if (this.value) {
            loadDistricts(this.value);
        } else {
            districtSelect.disabled = true;
            districtSelect.innerHTML = '<option value="">Select State First</option>';
        }
    });

    cropSelect.addEventListener("change", function () {
        if (this.value) {
            loadCropStages(this.value);
        }
    });

    stageModeSelect.addEventListener("change", function () {
        if (this.value === "MANUAL") {
            manualStageGroup.style.display = "block";
            loadCropStages(cropSelect.value);
        } else {
            manualStageGroup.style.display = "none";
        }
    });

    toggleTelemetryBtn.addEventListener("click", function () {
        if (telemetryDrawer.style.display === "none") {
            telemetryDrawer.style.display = "grid";
            this.textContent = "⚙️ Hide Synthetic IoT Telemetry Parameters ▲";
        } else {
            telemetryDrawer.style.display = "none";
            this.textContent = "⚙️ Customize Synthetic IoT Telemetry Parameters (Optional) ▼";
        }
    });

    monitoringForm.addEventListener("submit", function (e) {
        e.preventDefault();
        executeMonitoringAnalysis();
    });

    btnPrintPlan.addEventListener("click", function () {
        window.print();
    });

    btnAskVoice.addEventListener("click", function () {
        window.location.href = "/frontend/pages/voice-assistant.html";
    });

    btnListen.addEventListener("click", function () {
        toggleSpeechAdvisory();
    });

    mprListBtn.addEventListener("click", function () {
        const crop = cropSelect.value || "Wheat";
        const farm = farmIdInput.value || "FARM_001";
        window.location.href = `/frontend/pages/crop-listings.html?crop=${encodeURIComponent(crop)}&farm_id=${encodeURIComponent(farm)}&action=pre_harvest_list`;
    });
}

// ==========================================================================
// DATA LOADERS
// ==========================================================================
async function loadStates() {
    try {
        const resp = await fetch("/api/weather/states");
        const data = await resp.json();
        if (data.states) {
            stateSelect.innerHTML = '<option value="">Select State</option>';
            data.states.forEach(st => {
                const opt = document.createElement("option");
                opt.value = st;
                opt.textContent = st;
                stateSelect.appendChild(opt);
            });
            stateSelect.value = "Uttar Pradesh";
            await loadDistricts("Uttar Pradesh", "Varanasi");
        }
    } catch (e) {
        console.error("Failed loading states:", e);
    }
}

async function loadDistricts(stateName, defaultDistrict = "Varanasi") {
    if (!stateName) return;
    districtSelect.disabled = true;
    districtSelect.innerHTML = '<option value="">Loading Districts...</option>';

    try {
        let resp = await fetch(`/api/weather/districts/${encodeURIComponent(stateName)}`);
        if (!resp.ok) {
            resp = await fetch(`/api/weather/districts?state=${encodeURIComponent(stateName)}`);
        }
        const data = await resp.json();
        if (data.districts && data.districts.length > 0) {
            districtSelect.innerHTML = '<option value="">Select District</option>';
            data.districts.forEach(d => {
                const dName = (typeof d === "object" && d !== null) ? (d.name || d.district || "") : String(d);
                if (dName) {
                    const opt = document.createElement("option");
                    opt.value = dName;
                    opt.textContent = dName;
                    if (typeof d === "object" && d !== null) {
                        if (d.latitude !== undefined) opt.dataset.lat = d.latitude;
                        if (d.longitude !== undefined) opt.dataset.lon = d.longitude;
                    }
                    districtSelect.appendChild(opt);
                }
            });
            districtSelect.disabled = false;
            
            const names = data.districts.map(d => (typeof d === "object" && d !== null) ? (d.name || d.district || "") : String(d));
            if (defaultDistrict && names.includes(defaultDistrict)) {
                districtSelect.value = defaultDistrict;
            } else if (districtSelect.options.length > 1) {
                districtSelect.selectedIndex = 1;
            }
        } else {
            districtSelect.innerHTML = '<option value="">No Districts Found</option>';
        }
    } catch (e) {
        console.error("Failed loading districts:", e);
        districtSelect.innerHTML = '<option value="">Error Loading Districts</option>';
    }
}

async function loadCrops(preferredCrop = "Wheat") {
    try {
        const resp = await fetch("/api/v1/monitoring/crops");
        const data = await resp.json();
        if (data.crops && data.crops.length > 0) {
            cropSelect.innerHTML = '<option value="">Select Crop</option>';
            let foundPreferred = false;
            data.crops.forEach(c => {
                const cropName = c.crop || c.crop_name;
                const opt = document.createElement("option");
                opt.value = cropName;
                opt.textContent = cropName;
                if (cropName.toLowerCase() === preferredCrop.toLowerCase()) {
                    opt.selected = true;
                    foundPreferred = true;
                }
                cropSelect.appendChild(opt);
            });
            if (!foundPreferred && cropSelect.options.length > 1) {
                cropSelect.selectedIndex = 1;
            }
            await loadCropStages(cropSelect.value);
        }
    } catch (e) {
        console.error("Failed loading crops:", e);
    }
}

async function loadCropStages(cropName, defaultStage = null) {
    if (!cropName) return;
    manualStageSelect.innerHTML = '<option value="">Loading stages...</option>';
    try {
        let resp = await fetch(`/api/v1/monitoring/stages/${encodeURIComponent(cropName)}`);
        if (!resp.ok) {
            resp = await fetch(`/api/crop-monitoring/stages/${encodeURIComponent(cropName)}`);
        }
        const data = await resp.json();
        if (data.stages && data.stages.length > 0) {
            manualStageSelect.innerHTML = '<option value="">Select Crop Stage</option>';
            data.stages.forEach(st => {
                const opt = document.createElement("option");
                opt.value = st;
                opt.textContent = st;
                manualStageSelect.appendChild(opt);
            });
            if (defaultStage && data.stages.includes(defaultStage)) {
                manualStageSelect.value = defaultStage;
            } else if (manualStageSelect.options.length > 1) {
                manualStageSelect.selectedIndex = 1;
            }
        } else {
            manualStageSelect.innerHTML = '<option value="">No predefined stages found</option>';
        }
    } catch (e) {
        console.error("Failed loading crop stages:", e);
        manualStageSelect.innerHTML = '<option value="">Error loading stages</option>';
    }
}

// ==========================================================================
// SCENARIO DEMO PRESETS
// ==========================================================================
window.loadDemoScenario = function (scenarioKey) {
    stateSelect.value = "Uttar Pradesh";
    loadDistricts("Uttar Pradesh", "Varanasi");
    cropSelect.value = "Wheat";
    farmIdInput.value = "FARM_001";
    fieldIdInput.value = "FIELD_001";
    stageModeSelect.value = "AUTO";
    manualStageGroup.style.display = "none";
    cropListedCheckbox.checked = false;

    // Reset baseline telemetry
    iotMoisture.value = "30.5";
    iotSoilTemp.value = "23.6";
    iotAirTemp.value = "25.7";
    iotHumidity.value = "70.0";
    iotRainfall.value = "0.0";
    iotLeafWetness.value = "false";
    iotEc.value = "0.93";
    iotPh.value = "6.49";
    if (iotNitrogen) iotNitrogen.value = "110";
    if (iotPhosphorus) iotPhosphorus.value = "18";
    if (iotPotassium) iotPotassium.value = "210";
    if (iotOrganicCarbon) iotOrganicCarbon.value = "0.42";

    const today = new Date();

    if (scenarioKey === "wheat_cri") {
        const d = new Date(today);
        d.setDate(d.getDate() - 34);
        plantingDateInput.value = d.toISOString().split("T")[0];
    } else if (scenarioKey === "six_days_harvest") {
        const d = new Date(today);
        d.setDate(d.getDate() - 114);
        plantingDateInput.value = d.toISOString().split("T")[0];
    } else if (scenarioKey === "three_days_harvest") {
        const d = new Date(today);
        d.setDate(d.getDate() - 117);
        plantingDateInput.value = d.toISOString().split("T")[0];
    } else if (scenarioKey === "one_day_harvest") {
        const d = new Date(today);
        d.setDate(d.getDate() - 119);
        plantingDateInput.value = d.toISOString().split("T")[0];
    } else if (scenarioKey === "high_disease") {
        const d = new Date(today);
        d.setDate(d.getDate() - 40);
        plantingDateInput.value = d.toISOString().split("T")[0];
        iotHumidity.value = "95.0";
        iotLeafWetness.value = "true";
        iotRainfall.value = "12.0";
    } else if (scenarioKey === "low_moisture") {
        const d = new Date(today);
        d.setDate(d.getDate() - 25);
        plantingDateInput.value = d.toISOString().split("T")[0];
        iotMoisture.value = "14.2";
    }

    executeMonitoringAnalysis();
};

// ==========================================================================
// CORE EXECUTION: POST /api/v1/monitoring/analyze
// ==========================================================================
async function executeMonitoringAnalysis() {
    loadingSpinner.style.display = "block";
    monitoringResults.style.display = "none";

    const selDistrictOpt = districtSelect.options[districtSelect.selectedIndex];
    const distLat = selDistrictOpt && selDistrictOpt.dataset.lat ? parseFloat(selDistrictOpt.dataset.lat) : null;
    const distLon = selDistrictOpt && selDistrictOpt.dataset.lon ? parseFloat(selDistrictOpt.dataset.lon) : null;

    const payload = {
        farm_id: farmIdInput.value.trim() || "FARM_001",
        field_id: fieldIdInput.value.trim() || "FIELD_001",
        telemetry_id: `TEL_${Date.now().toString().slice(-4)}`,
        location: {
            state: stateSelect.value || "Uttar Pradesh",
            district: districtSelect.value || "Varanasi",
            village: villageInput.value.trim() || "Demo Village",
            latitude: distLat,
            longitude: distLon
        },
        crop: {
            crop_name: cropSelect.value || "Wheat",
            planting_date: plantingDateInput.value || null,
            crop_stage_mode: stageModeSelect.value || "AUTO",
            crop_stage: stageModeSelect.value === "MANUAL" ? (manualStageSelect.value.trim() || null) : null
        },
        marketplace: {
            crop_listed: cropListedCheckbox.checked
        },
        telemetry: {
            soil_moisture_percent: parseFloat(iotMoisture.value) || 30.0,
            soil_temperature_c: parseFloat(iotSoilTemp.value) || 23.0,
            air_temperature_c: parseFloat(iotAirTemp.value) || 25.0,
            relative_humidity_percent: parseFloat(iotHumidity.value) || 70.0,
            rainfall_mm: parseFloat(iotRainfall.value) || 0.0,
            leaf_wetness: iotLeafWetness.value === "true",
            soil_ec_ds_m: parseFloat(iotEc.value) || 0.9,
            soil_ph: parseFloat(iotPh.value) || 6.5,
            soil_nitrogen_mg_kg: iotNitrogen ? parseFloat(iotNitrogen.value) || 110.0 : 110.0,
            soil_phosphorus_mg_kg: iotPhosphorus ? parseFloat(iotPhosphorus.value) || 18.0 : 18.0,
            soil_potassium_mg_kg: iotPotassium ? parseFloat(iotPotassium.value) || 210.0 : 210.0,
            soil_organic_carbon_percent: iotOrganicCarbon ? parseFloat(iotOrganicCarbon.value) || 0.42 : 0.42,
            light_hours: 8.0,
            wind_speed_kmh: 10.0
        }
    };

    try {
        const resp = await fetch("/api/v1/monitoring/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!resp.ok) {
            const errData = await resp.json().catch(() => ({}));
            throw new Error(errData.detail || `HTTP Error ${resp.status}`);
        }

        const data = await resp.json();
        currentMonitoringData = data;
        renderMonitoringDashboard(data);

    } catch (err) {
        console.error("MONITORING ANALYSIS ERROR:", err);
        alert(`Monitoring Engine Error: ${err.message}`);
    } finally {
        loadingSpinner.style.display = "none";
    }
}

// ==========================================================================
// RENDER MONITORING DASHBOARD (DYNAMIC & UNHARDCODED)
// ==========================================================================
function renderMonitoringDashboard(data) {
    monitoringResults.style.display = "block";

    const farm = data.farm || {};
    const loc = farm.location || {};
    const crop = data.crop || {};
    const stage = data.stage || {};
    const weather = data.weather || {};
    const iot = data.iot || {};
    const decisions = data.decisions || {};
    const harvest = data.harvest || {};
    const mkt = data.marketplace || {};
    const notifs = data.notifications || [];
    const guidance = data.farmer_guidance || {};
    const calendar = data.calendar || {};
    const fertility = data.soil_fertility || {};
    const todayActions = data.today_actions || [];

    // 1. Top Header Banner
    resCropHeader.textContent = crop.crop_name || "Crop";
    resLocationHeader.textContent = `${loc.village || "Demo Village"}, ${loc.district || "District"}, ${loc.state || "State"}`;
    resFarmHeader.textContent = `${farm.farm_id || "FARM_001"} • Field: ${farm.field_id || "FIELD_001"}`;

    // 2. Crop Lifecycle & Stage (Clean Human Name, zero day ranges)
    const ageDays = stage.crop_age_days !== null && stage.crop_age_days !== undefined ? stage.crop_age_days : 0;
    dapBadge.textContent = `${ageDays} Days After Planting`;
    activeStageTitle.textContent = stage.human_stage_name || stage.current_stage || "Active Stage";
    stageStatusText.textContent = `Planting Date: ${stage.formatted_planting_date || crop.planting_date || "N/A"}`;
    nextStageText.textContent = stage.next_stage || "Maturity / Harvest";

    const dth = harvest.days_to_harvest !== undefined ? harvest.days_to_harvest : 0;
    daysToHarvestText.textContent = dth > 0 ? `${dth} days` : (harvest.status === "HARVEST_WINDOW" ? "Ready for Harvest!" : "Harvest Point Reached");

    const maxDay = harvest.harvest_start_day || 120;
    const pct = Math.min(100, Math.max(5, Math.round((ageDays / maxDay) * 100)));
    stageProgressFill.style.width = `${pct}%`;

    // 3. Pre-Harvest Marketplace Reminder Banner
    const listingDecision = mkt.listing_decision || {};
    if (listingDecision.reminder && !mkt.crop_listed) {
        marketplaceReminderBanner.style.display = "flex";
        mprTitle.textContent = listingDecision.status === "LISTING_URGENT" ? "🚨 Urgent Pre-Harvest Marketplace Reminder" : "🔔 Pre-Harvest Marketplace Listing Reminder";
        mprBadge.textContent = listingDecision.reminder_type || "REMINDER";
        mprBadge.className = `mpr-badge ${listingDecision.priority === "HIGH" ? "mpr-badge-urgent" : "mpr-badge-due"}`;
        mprText.textContent = listingDecision.reason || `Your crop is expected to reach harvest in ${listingDecision.days_to_harvest} days. List it now on AgriBridge Verified Marketplace to connect with buyers before harvest.`;
        mprListBtn.style.display = "inline-block";
    } else if (mkt.crop_listed) {
        marketplaceReminderBanner.style.display = "flex";
        mprTitle.textContent = "✅ Crop Listed on AgriBridge Marketplace";
        mprBadge.textContent = "LISTED";
        mprBadge.className = "mpr-badge mpr-badge-listed";
        mprText.textContent = "Your crop is currently listed in the verified marketplace. Wholesale buyers can view your harvest availability and place commitments.";
        mprListBtn.style.display = "none";
    } else {
        marketplaceReminderBanner.style.display = "none";
    }

    // 4. Live Open-Meteo Weather Card
    weatherSourceBadge.textContent = weather.source || "LIVE_REAL (Open-Meteo)";
    const tempC = weather.temperature_c !== undefined ? weather.temperature_c : "--";
    weatherTempHeadline.textContent = `${tempC}°C • ${weather.forecast_summary || "Real-Time Weather"}`;
    weatherDecisionDetail.textContent = weather.advisory_note || "Atmospheric telemetry dynamically processed via farm location coordinates.";
    wmHumidityVal.textContent = weather.relative_humidity_percent ? `${weather.relative_humidity_percent}%` : "--";
    wmWindVal.textContent = weather.wind_speed_kmh ? `${weather.wind_speed_kmh} km/h` : "--";
    wmRainVal.textContent = weather.rainfall_mm !== undefined ? `${weather.rainfall_mm} mm` : "0.0 mm";
    dailyPriorityVal.textContent = decisions.daily_priority || "NORMAL";
    dailyPriorityVal.className = `mi-val ${decisions.daily_priority === "HIGH" ? "text-danger" : "text-success"}`;

    // 5. Dynamic Date-Aware Calendar
    renderCalendarTimeline(calendar);

    // 6. Today's Actions (Mandatory 4-Question Format)
    renderTodayActions(todayActions);

    // 7. Soil Fertility & Nutrient Status Engine
    renderSoilFertility(fertility);

    // 8. Stage-Specific Fertilizer Prescription
    renderFertilizerPrescription(decisions.fertilizer);

    // 9. Virtual IoT Telemetry Grid
    iotValMoisture.textContent = iot.soil_moisture_percent !== undefined ? `${iot.soil_moisture_percent}%` : "--";
    iotValSoilTemp.textContent = iot.soil_temperature_c !== undefined ? `${iot.soil_temperature_c}°C` : "--";
    iotValAirTemp.textContent = iot.air_temperature_c !== undefined ? `${iot.air_temperature_c}°C` : "--";
    iotValRh.textContent = iot.relative_humidity_percent !== undefined ? `${iot.relative_humidity_percent}%` : "--";
    iotValWetness.textContent = iot.leaf_wetness ? "Wet / Active" : "Dry";
    iotValEc.textContent = iot.soil_ec_ds_m !== undefined ? `${iot.soil_ec_ds_m} dS/m` : "--";
    iotValPh.textContent = iot.soil_ph !== undefined ? `${iot.soil_ph}` : "--";
    iotValLight.textContent = iot.light_hours !== undefined ? `${iot.light_hours} hrs` : "8.0 hrs";

    // 10. Multi-Signal Decision Matrix
    renderDecisionCard(decisions.irrigation, decIrrigationStatus, decIrrigationReason);
    renderDecisionCard(decisions.disease, decDiseaseStatus, decDiseaseReason);
    renderDecisionCard(decisions.pest, decPestStatus, decPestReason);
    renderDecisionCard(decisions.weather_stress, decStressStatus, decStressReason);
    renderDecisionCard(decisions.fertilizer, decFertilizerStatus, decFertilizerReason);

    // 11. Dynamic Notification Center
    renderNotificationsList(notifs);

    // 12. Gemini Farmer Guidance
    geminiGuidanceText.textContent = guidance.advisory_text || guidance.summary || "Follow scheduled monitoring and field scouting activities.";
}

function renderCalendarTimeline(calendar) {
    if (!stageTimelineCards || !calendarEventsList) return;

    const stages = calendar.stages_timeline || [];
    if (stages.length === 0) {
        stageTimelineCards.innerHTML = `<div style="color:#64748B; padding:12px;">Timeline computed dynamically upon registration.</div>`;
    } else {
        stageTimelineCards.innerHTML = "";
        stages.forEach(st => {
            const card = document.createElement("div");
            card.className = `stage-tl-card ${st.is_current ? 'current' : ''} ${st.is_completed ? 'completed' : ''}`;
            
            let badgeClass = "background:#F1F5F9; color:#475569;";
            let badgeText = "Upcoming";
            if (st.is_current) {
                badgeClass = "background:#DCFCE7; color:#166534; font-weight:800;";
                badgeText = "CURRENT ACTIVE";
            } else if (st.is_completed) {
                badgeClass = "background:#E2E8F0; color:#334155;";
                badgeText = "Completed";
            }

            card.innerHTML = `
                <div class="stage-tl-header">
                    <span class="stage-tl-name">${escapeHtml(st.stage_name)}</span>
                    <span class="stage-tl-badge" style="${badgeClass}">${badgeText}</span>
                </div>
                <div class="stage-tl-dates">
                    <span>📅 <strong>${escapeHtml(st.start_date)}</strong> → <strong>${escapeHtml(st.end_date)}</strong></span>
                    <span style="color:#64748B;">Duration: ${st.duration_days} days</span>
                </div>
            `;
            stageTimelineCards.appendChild(card);
        });
    }

    const events = calendar.daily_events || [];
    if (events.length === 0) {
        calendarEventsList.innerHTML = `<div style="color:#64748B; padding:12px;">No active daily events for this cycle.</div>`;
    } else {
        calendarEventsList.innerHTML = "";
        events.forEach(ev => {
            const item = document.createElement("div");
            item.className = `calendar-event-item ${ev.is_today ? 'today-event' : ''}`;
            
            item.innerHTML = `
                <div class="calendar-event-info">
                    <span class="calendar-event-date">${escapeHtml(ev.date)}</span>
                    <span style="font-size: 13.5px; color:#1E293B;">${escapeHtml(ev.title)}</span>
                </div>
                ${ev.is_today ? '<span style="background:#FEF08A; color:#854D0E; font-size:11px; font-weight:800; padding:2px 8px; border-radius:4px;">TODAY</span>' : ''}
            `;
            calendarEventsList.appendChild(item);
        });
    }
}

function renderTodayActions(actions) {
    if (!todayActionsContainer) return;

    if (!actions || actions.length === 0) {
        todayActionsContainer.innerHTML = `
            <div style="background:#F8FAFC; border:1px dashed #CBD5E1; border-radius:10px; padding:16px; text-align:center; color:#64748B;">
                ✅ All systems normal for today. Routine field inspection recommended.
            </div>
        `;
        return;
    }

    todayActionsContainer.innerHTML = "";
    actions.forEach(act => {
        const card = document.createElement("div");
        card.className = "action-4q-card";

        const priorityClass = act.priority === "HIGH" ? "badge-high" : "badge-scheduled";

        card.innerHTML = `
            <div class="action-4q-card-header">
                <h3 class="action-4q-title">${act.icon || '🎯'} ${escapeHtml(act.title)}</h3>
                <span class="dec-badge ${priorityClass}">${act.priority || 'NORMAL'}</span>
            </div>
            <div class="action-4q-grid">
                <div class="action-4q-item">
                    <span class="action-4q-q">1. What to Do</span>
                    <p class="action-4q-a">${escapeHtml(act.what)}</p>
                </div>
                <div class="action-4q-item item-why">
                    <span class="action-4q-q">2. Why to Do It</span>
                    <p class="action-4q-a">${escapeHtml(act.why)}</p>
                </div>
                <div class="action-4q-item item-how">
                    <span class="action-4q-q">3. How to Do It</span>
                    <p class="action-4q-a">${escapeHtml(act.how)}</p>
                </div>
                <div class="action-4q-item item-when">
                    <span class="action-4q-q">4. When to Do It</span>
                    <p class="action-4q-a">${escapeHtml(act.when)}</p>
                </div>
            </div>
        `;
        todayActionsContainer.appendChild(card);
    });
}

function renderSoilFertility(fert) {
    if (!soilFertilityGrid) return;

    const nutrients = [
        { key: "nitrogen", label: "🌿 Nitrogen (N)", unit: "mg/kg", data: fert.nitrogen },
        { key: "phosphorus", label: "💎 Phosphorus (P)", unit: "mg/kg", data: fert.phosphorus },
        { key: "potassium", label: "🥔 Potassium (K)", unit: "mg/kg", data: fert.potassium },
        { key: "organic_carbon", label: "🍂 Organic Carbon (OC)", unit: "%", data: fert.organic_carbon },
        { key: "soil_ph", label: "🧪 Soil pH", unit: "", data: fert.soil_ph },
        { key: "soil_ec", label: "⚡ Soil EC", unit: "dS/m", data: fert.soil_ec }
    ];

    soilFertilityGrid.innerHTML = "";
    nutrients.forEach(n => {
        const d = n.data || {};
        const val = d.value_mg_kg !== undefined ? `${d.value_mg_kg} ${n.unit}` :
                    d.value_percent !== undefined ? `${d.value_percent} ${n.unit}` :
                    d.value_ds_m !== undefined ? `${d.value_ds_m} ${n.unit}` :
                    d.value !== undefined ? `${d.value}` : "--";
        const status = d.status || "ADEQUATE";
        const statusClass = `badge-${status.toLowerCase()}`;

        const card = document.createElement("div");
        card.className = "fertility-metric-card";
        card.innerHTML = `
            <div class="fertility-card-top">
                <span class="fertility-nutrient-title">${n.label}</span>
                <span class="fertility-status-badge ${statusClass}">${status}</span>
            </div>
            <span class="fertility-nutrient-val">${val}</span>
            <span class="fertility-guide-text">${escapeHtml(d.description || '')}</span>
        `;
        soilFertilityGrid.appendChild(card);
    });

    if (fertilityDeficiencyCallout) {
        const defs = fert.deficiencies || [];
        if (defs.length > 0) {
            fertilityDeficiencyCallout.innerHTML = `
                ⚠️ <strong>Soil Nutrient Deficiencies Detected:</strong> ${defs.join(", ")}. 
                Prescription includes targeted basal/top-dress corrections aligned with current crop stage requirements.
            `;
            fertilityDeficiencyCallout.style.background = "#FEF3C7";
            fertilityDeficiencyCallout.style.borderColor = "#FDE68A";
            fertilityDeficiencyCallout.style.color = "#92400E";
        } else {
            fertilityDeficiencyCallout.innerHTML = `
                ✅ <strong>Balanced Soil Fertility:</strong> All primary nutrients (NPK, OC, pH, EC) are within optimal agronomic thresholds for healthy crop growth.
            `;
            fertilityDeficiencyCallout.style.background = "#F0FDF4";
            fertilityDeficiencyCallout.style.borderColor = "#BBF7D0";
            fertilityDeficiencyCallout.style.color = "#166534";
        }
    }
}

function renderFertilizerPrescription(fert) {
    if (!fert) return;

    if (fertPriorityBadge) {
        fertPriorityBadge.textContent = fert.priority || "SCHEDULED";
        fertPriorityBadge.className = `dec-badge badge-${(fert.priority || 'scheduled').toLowerCase()}`;
    }

    if (fertWhat) fertWhat.textContent = fert.what || fert.recommendation || "Follow crop stage nutrition.";
    if (fertWhy) fertWhy.textContent = fert.why || fert.reason || "Maintain soil nutrient availability.";
    if (fertHow) fertHow.textContent = fert.how || "Broadcast evenly or apply via fertigation.";
    if (fertWhen) fertWhen.textContent = fert.when || "Apply during early morning or late afternoon.";

    if (fertWeatherAdjustment && fertWeatherAdjustmentText) {
        if (fert.weather_adjustment && fert.weather_adjustment.includes("DELAY")) {
            fertWeatherAdjustment.style.display = "flex";
            fertWeatherAdjustmentText.textContent = fert.weather_adjustment;
        } else {
            fertWeatherAdjustment.style.display = "none";
        }
    }
}

function renderDecisionCard(decisionObj, statusEl, reasonEl) {
    if (!decisionObj || !statusEl || !reasonEl) return;
    const status = (decisionObj.status || "NORMAL").toUpperCase();
    const priority = (decisionObj.priority || "LOW").toUpperCase();
    statusEl.textContent = status;
    statusEl.className = `dec-badge badge-${priority.toLowerCase()}`;
    reasonEl.textContent = decisionObj.reason || "Operating under standard monitoring conditions.";
}

function renderNotificationsList(notifications) {
    if (!notificationsList) return;
    if (!notifications || notifications.length === 0) {
        notificationsList.innerHTML = `
            <div class="notif-item">
                <div class="notif-content">
                    <strong>✅ All Systems Normal</strong>
                    <p>No urgent action alerts currently required for your farm field.</p>
                </div>
                <span class="notif-tag">OK</span>
            </div>
        `;
        return;
    }

    notificationsList.innerHTML = "";
    notifications.forEach(n => {
        const item = document.createElement("div");
        item.className = "notif-item";
        item.id = `notif-card-${n.notification_id}`;

        const isCompleted = n.action_status === "COMPLETE";
        const pClass = (n.priority || "LOW").toLowerCase();
        const actionBtnText = n.type === "marketplace" ? "📦 List Crop" : (isCompleted ? "✅ Done" : "Mark Done");

        item.innerHTML = `
            <div class="notif-content">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                    <strong>${escapeHtml(n.title || "Notification")}</strong>
                    <span class="notif-p-pill p-${pClass}">${n.priority || "LOW"}</span>
                    ${n.action_status ? `<span class="notif-p-pill" style="background:#C8E6C9; color:#2E7D32;">${n.action_status}</span>` : ""}
                </div>
                <p>${escapeHtml(n.reason || "")}</p>
            </div>
            <div class="notif-actions-col" style="display: flex; gap: 8px; align-items: center;">
                <button type="button" class="notif-action-btn ${isCompleted ? 'btn-done' : ''}" onclick="handleNotifAction('${escapeHtml(n.notification_id)}', 'COMPLETE')">
                    ${actionBtnText}
                </button>
                <button type="button" class="notif-action-btn btn-postpone" onclick="handleNotifAction('${escapeHtml(n.notification_id)}', 'POSTPONE')">
                    Postpone
                </button>
            </div>
        `;
        notificationsList.appendChild(item);
    });
}

// ==========================================================================
// NOTIFICATION INTERACTIVE ACTION: POST /api/v1/monitoring/notification/action
// ==========================================================================
window.handleNotifAction = async function (notificationId, actionType) {
    if (notificationId && notificationId.includes("MARKETPLACE")) {
        const crop = cropSelect.value || "Wheat";
        const farm = farmIdInput.value || "FARM_001";
        window.location.href = `/frontend/pages/crop-listings.html?crop=${encodeURIComponent(crop)}&farm_id=${encodeURIComponent(farm)}&action=pre_harvest_list`;
        return;
    }

    try {
        const resp = await fetch("/api/v1/monitoring/notification/action", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                notification_id: notificationId,
                action: actionType,
                reason: `Action updated by farmer from Crop Monitoring dashboard`
            })
        });

        if (resp.ok) {
            const card = document.getElementById(`notif-card-${notificationId}`);
            if (card) {
                card.style.background = "#E8F5E9";
                card.style.borderColor = "#81C784";
                const btn = card.querySelector(".notif-action-btn");
                if (btn) {
                    btn.textContent = actionType === "COMPLETE" ? "✅ Done" : "⏳ Postponed";
                    btn.disabled = true;
                }
            }
        }
    } catch (e) {
        console.error("Failed to update notification action:", e);
    }
};

// ==========================================================================
// TEXT TO SPEECH (ADVISORY AUDIO)
// ==========================================================================
function toggleSpeechAdvisory() {
    if (!("speechSynthesis" in window)) {
        alert("Speech synthesis is not supported in this browser.");
        return;
    }

    if (isSpeaking) {
        window.speechSynthesis.cancel();
        isSpeaking = false;
        ttsLabel.textContent = "Listen to Plan (आवाज में सुनें)";
        return;
    }

    const textToSpeak = geminiGuidanceText ? geminiGuidanceText.textContent : "Monitoring advisory plan.";
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utterance.lang = "hi-IN";
    utterance.rate = 0.95;

    utterance.onstart = function () {
        isSpeaking = true;
        ttsLabel.textContent = "⏹️ Stop Audio";
    };

    utterance.onend = function () {
        isSpeaking = false;
        ttsLabel.textContent = "Listen to Plan (आवाज में सुनें)";
    };

    utterance.onerror = function () {
        isSpeaking = false;
        ttsLabel.textContent = "Listen to Plan (आवाज में सुनें)";
    };

    window.speechSynthesis.speak(utterance);
}

function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

