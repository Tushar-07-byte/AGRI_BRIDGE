// ==============================================================================
// AGRIBRIDGE — MASTER FARMER DASHBOARD CONTROLLER (farmer-dashboard.js)
// Real-time Precision Operations, Live Weather, AI Diagnostics & Orders
// ==============================================================================

(function () {
    "use strict";

    console.log("FARMER DASHBOARD CONTROLLER INITIALIZED");

    // Route Protection: Farmer Only
    if (window.AgriBridgeAuth && typeof window.AgriBridgeAuth.requireAuth === "function") {
        window.AgriBridgeAuth.requireAuth(["farmer"]);
    }

    // State Variables
    let currentTimingAlertData = null;
    let currentFarmerLocation = null;
    let currentFarmerCrop = "Wheat";
    let currentNotifFilter = "ALL";
    let allLoadedNotifications = [];

    // 36 Comprehensive Indian States & UTs Fallback
    const INDIAN_STATES = [
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
        "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
        "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
        "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
        "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
        "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
        "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
    ];

    // ==========================================================================
    // 1. INITIALIZATION ON DOM READY
    // ==========================================================================

    document.addEventListener("DOMContentLoaded", () => {
        initFarmerProfile();
        initLocationModal();
        initNavbarHandlers();
        initNotificationCenter();
        initRescheduleModal();
        initAutonomousLoopController();
        loadMiniWeather();
        loadTimingAlert();
        loadAutonomousLoopData();
        loadActiveCrops();
        loadFarmerNotifications();
        loadKpiMetrics();
        loadFieldActionPlans();
        loadBuyerOrders();
        loadActivityFeed();
    });

    // Re-render when language is switched
    window.addEventListener("languageChanged", () => {
        initFarmerProfile();
        if (currentTimingAlertData) {
            renderTimingAlert(currentTimingAlertData);
        }
        loadAutonomousLoopData();
        loadActiveCrops();
        loadFarmerNotifications();
        loadFieldActionPlans();
        loadBuyerOrders();
        loadActivityFeed();
    });

    // ==========================================================================
    // 2. PROFILE & LOCATION MANAGEMENT
    // ==========================================================================

    function getSavedFarmerLocation() {
        // 1. Direct key
        const directLoc = localStorage.getItem("farmer_location");
        if (directLoc && directLoc.trim() && directLoc !== "--") {
            return directLoc.trim();
        }

        // 2. State & District separate keys
        const dist = localStorage.getItem("farmer_district");
        const st = localStorage.getItem("farmer_state");
        if (dist && st) {
            return `${dist.trim()}, ${st.trim()}`;
        }

        // 3. User profile JSON
        const currentUser = window.AgriBridgeAuth ? window.AgriBridgeAuth.getCurrentUser() : null;
        const userId = currentUser ? currentUser.id : "default";
        const rawProfile = localStorage.getItem(`farmer_profile_${userId}`) || localStorage.getItem("farmerProfile");
        if (rawProfile) {
            try {
                const profile = JSON.parse(rawProfile);
                if (profile.location && profile.location.trim() && profile.location !== "--") {
                    return profile.location.trim();
                }
                if (profile.district && profile.state) {
                    return `${profile.district.trim()}, ${profile.state.trim()}`;
                }
            } catch (e) {}
        }

        return null;
    }

    function initFarmerProfile() {
        const currentUser = window.AgriBridgeAuth ? window.AgriBridgeAuth.getCurrentUser() : null;
        const farmerNameEl = document.getElementById("farmer-name");
        const navbarUserNameEl = document.getElementById("navbarUserName");
        const mobileNavbarUserNameEl = document.getElementById("mobileNavbarUserName");
        const userAvatarEl = document.getElementById("userAvatar");
        const mobileUserAvatarEl = document.getElementById("mobileUserAvatar");

        let displayName = "Farmer";

        if (currentUser && currentUser.name) {
            displayName = currentUser.name.trim();
        } else {
            const rawUser = localStorage.getItem("agribridge_user") || localStorage.getItem("user");
            if (rawUser) {
                try {
                    const u = JSON.parse(rawUser);
                    if (u.name) displayName = u.name.trim();
                } catch (e) {}
            }
        }

        if (farmerNameEl) farmerNameEl.textContent = displayName;
        if (navbarUserNameEl) navbarUserNameEl.textContent = displayName;
        if (mobileNavbarUserNameEl) mobileNavbarUserNameEl.textContent = displayName;

        const initial = displayName.charAt(0).toUpperCase() || "F";
        if (userAvatarEl) userAvatarEl.textContent = initial;
        if (mobileUserAvatarEl) mobileUserAvatarEl.textContent = initial;

        // Load farm details
        const userId = currentUser ? currentUser.id : "default";
        const rawProfile = localStorage.getItem(`farmer_profile_${userId}`) || localStorage.getItem("farmerProfile");

        const farmAreaEl = document.getElementById("farm-area");
        const farmLocationEl = document.getElementById("farm-location");

        if (rawProfile) {
            try {
                const profile = JSON.parse(rawProfile);
                if (farmAreaEl && profile.farmArea) {
                    farmAreaEl.textContent = `${profile.farmArea} ${profile.farmAreaUnit || "acres"}`;
                } else if (farmAreaEl && profile.land_size) {
                    farmAreaEl.textContent = `${profile.land_size} acres`;
                }

                if (profile.crop || profile.crop_type) {
                    currentFarmerCrop = profile.crop || profile.crop_type;
                }
            } catch (e) {}
        }

        if (farmAreaEl && farmAreaEl.textContent === "--") {
            farmAreaEl.textContent = "5.0 acres";
        }

        // Location Resolution: Check saved 1-time selection
        const savedLoc = getSavedFarmerLocation();
        if (savedLoc) {
            currentFarmerLocation = savedLoc;
            if (farmLocationEl) {
                farmLocationEl.textContent = savedLoc;
            }
        } else {
            currentFarmerLocation = null;
            if (farmLocationEl) {
                farmLocationEl.innerHTML = '<span style="color: #059669; font-weight: 700; text-decoration: underline;">Select Location</span>';
            }
            // Automatically prompt the user to select their location once
            setTimeout(() => {
                openLocationModal();
            }, 400);
        }
    }

    // ==========================================================================
    // 2.1 LOCATION MODAL LOGIC (1-TIME SELECTION & DEFAULT PERSISTENCE)
    // ==========================================================================

    function initLocationModal() {
        const modal = document.getElementById("farmLocationModal");
        const openChip = document.getElementById("farmLocationChip");
        const closeBtn = document.getElementById("closeLocationModalBtn");
        const overlay = document.getElementById("closeLocationOverlay");
        const stateSelect = document.getElementById("modalStateSelect");
        const districtSelect = document.getElementById("modalDistrictSelect");
        const gpsBtn = document.getElementById("modalGpsBtn");
        const gpsStatus = document.getElementById("modalGpsStatus");
        const saveBtn = document.getElementById("saveLocationBtn");

        if (!modal) return;

        // Open modal on chip click
        if (openChip) {
            openChip.addEventListener("click", () => {
                openLocationModal();
            });
        }

        // Close handlers
        const closeModal = () => {
            modal.style.display = "none";
        };

        if (closeBtn) closeBtn.addEventListener("click", closeModal);
        if (overlay) overlay.addEventListener("click", closeModal);

        // Load Indian States into dropdown
        loadModalStates();

        // State Change -> Fetch Districts
        if (stateSelect && districtSelect) {
            stateSelect.addEventListener("change", async () => {
                const selectedState = stateSelect.value;
                districtSelect.innerHTML = '<option value="">-- Loading Districts... --</option>';
                districtSelect.disabled = true;
                if (saveBtn) saveBtn.disabled = true;

                if (!selectedState) {
                    districtSelect.innerHTML = '<option value="">-- Choose District --</option>';
                    return;
                }

                try {
                    const res = await fetch(`/api/weather/districts/${encodeURIComponent(selectedState)}`);
                    if (res.ok) {
                        const data = await res.json();
                        if (data.success && Array.isArray(data.districts) && data.districts.length > 0) {
                            districtSelect.innerHTML = '<option value="">-- Choose District --</option>';
                            data.districts.forEach(d => {
                                const dName = typeof d === "object" ? (d.name || d.district) : d;
                                const opt = document.createElement("option");
                                opt.value = dName;
                                opt.textContent = dName;
                                districtSelect.appendChild(opt);
                            });
                            districtSelect.disabled = false;
                            return;
                        }
                    }
                } catch (e) {
                    console.warn("Districts API fetch error:", e);
                }

                // Fallback default district option if network fails
                districtSelect.innerHTML = `
                    <option value="">-- Choose District --</option>
                    <option value="${selectedState} Central">${selectedState} Central</option>
                    <option value="${selectedState} North">${selectedState} North</option>
                    <option value="${selectedState} South">${selectedState} South</option>
                `;
                districtSelect.disabled = false;
            });

            districtSelect.addEventListener("change", () => {
                if (saveBtn) {
                    saveBtn.disabled = !districtSelect.value;
                }
            });
        }

        // GPS Auto Detect
        if (gpsBtn) {
            gpsBtn.addEventListener("click", () => {
                if (!navigator.geolocation) {
                    showGpsStatus("Geolocation is not supported by your browser.", "error");
                    return;
                }

                showGpsStatus("🛰️ Locating your farm coordinates...", "info");
                gpsBtn.disabled = true;

                navigator.geolocation.getCurrentPosition(
                    async (position) => {
                        const lat = position.coords.latitude;
                        const lon = position.coords.longitude;
                        showGpsStatus("🛰️ Coordinates detected! Matching State and District...", "info");

                        try {
                            // Reverse geocode via OpenStreetMap Nominatim
                            const geoRes = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`);
                            if (geoRes.ok) {
                                const geoData = await geoRes.json();
                                const addr = geoData.address || {};
                                const state = addr.state || "";
                                const district = addr.state_district || addr.county || addr.district || addr.city || "";

                                if (state) {
                                    // Match state in dropdown
                                    const stateOptions = Array.from(stateSelect.options);
                                    const matchedState = stateOptions.find(opt => opt.value.toLowerCase() === state.toLowerCase() || state.toLowerCase().includes(opt.value.toLowerCase()));

                                    if (matchedState) {
                                        stateSelect.value = matchedState.value;
                                        stateSelect.dispatchEvent(new Event("change"));

                                        setTimeout(() => {
                                            if (district && districtSelect) {
                                                const dOptions = Array.from(districtSelect.options);
                                                const matchedD = dOptions.find(opt => opt.value.toLowerCase() === district.toLowerCase() || district.toLowerCase().includes(opt.value.toLowerCase()));
                                                if (matchedD) {
                                                    districtSelect.value = matchedD.value;
                                                }
                                            }
                                            if (saveBtn) saveBtn.disabled = false;
                                        }, 600);

                                        showGpsStatus(`✓ Detected: ${district ? district + ', ' : ''}${state}`, "success");
                                        gpsBtn.disabled = false;
                                        return;
                                    }
                                }
                            }
                        } catch (err) {
                            console.warn("Reverse geocode notice:", err);
                        }

                        showGpsStatus("Coordinates found! Please confirm State and District below.", "info");
                        gpsBtn.disabled = false;
                    },
                    (error) => {
                        showGpsStatus("Could not retrieve GPS location. Please choose from dropdowns.", "error");
                        gpsBtn.disabled = false;
                    },
                    { timeout: 10000, enableHighAccuracy: true }
                );
            });
        }

        // Save Farm Location Button
        if (saveBtn) {
            saveBtn.addEventListener("click", () => {
                const state = stateSelect.value.trim();
                const district = districtSelect.value.trim();

                if (!state || !district) return;

                const fullLocation = `${district}, ${state}`;

                // 1. Persist in localStorage across entire application
                localStorage.setItem("farmer_location", fullLocation);
                localStorage.setItem("farmer_state", state);
                localStorage.setItem("farmer_district", district);

                // 2. Sync farmerProfile in localStorage
                try {
                    let profile = JSON.parse(localStorage.getItem("farmerProfile") || "{}");
                    profile.location = fullLocation;
                    profile.state = state;
                    profile.district = district;
                    localStorage.setItem("farmerProfile", JSON.stringify(profile));

                    const currentUser = window.AgriBridgeAuth ? window.AgriBridgeAuth.getCurrentUser() : null;
                    const userId = currentUser ? currentUser.id : "default";
                    let userProfile = JSON.parse(localStorage.getItem(`farmer_profile_${userId}`) || "{}");
                    userProfile.location = fullLocation;
                    userProfile.state = state;
                    userProfile.district = district;
                    localStorage.setItem(`farmer_profile_${userId}`, JSON.stringify(userProfile));
                } catch (e) {}

                // 3. Update application state
                currentFarmerLocation = fullLocation;
                const farmLocationEl = document.getElementById("farm-location");
                if (farmLocationEl) {
                    farmLocationEl.textContent = fullLocation;
                }

                // 4. Close Modal
                closeModal();

                // 5. Instantly fetch real-time weather & timing alerts for this chosen location
                loadMiniWeather();
                loadTimingAlert();
                loadFieldActionPlans();
            });
        }
    }

    async function loadModalStates() {
        const stateSelect = document.getElementById("modalStateSelect");
        if (!stateSelect) return;

        try {
            const res = await fetch("/api/weather/states");
            if (res.ok) {
                const data = await res.json();
                if (data.success && Array.isArray(data.states) && data.states.length > 0) {
                    stateSelect.innerHTML = '<option value="">-- Choose State / UT --</option>';
                    data.states.forEach(st => {
                        const sName = typeof st === "object" ? (st.name || st.state) : st;
                        const opt = document.createElement("option");
                        opt.value = sName;
                        opt.textContent = sName;
                        stateSelect.appendChild(opt);
                    });
                    return;
                }
            }
        } catch (e) {
            console.warn("States API fetch error:", e);
        }

        // Fallback comprehensive state list
        stateSelect.innerHTML = '<option value="">-- Choose State / UT --</option>';
        INDIAN_STATES.forEach(st => {
            const opt = document.createElement("option");
            opt.value = st;
            opt.textContent = st;
            stateSelect.appendChild(opt);
        });
    }

    function openLocationModal() {
        const modal = document.getElementById("farmLocationModal");
        const stateSelect = document.getElementById("modalStateSelect");
        const districtSelect = document.getElementById("modalDistrictSelect");
        const saveBtn = document.getElementById("saveLocationBtn");
        if (!modal) return;

        modal.style.display = "flex";

        // Preselect current values if available
        const savedState = localStorage.getItem("farmer_state");
        const savedDistrict = localStorage.getItem("farmer_district");

        if (savedState && stateSelect) {
            stateSelect.value = savedState;
            stateSelect.dispatchEvent(new Event("change"));
            setTimeout(() => {
                if (savedDistrict && districtSelect) {
                    districtSelect.value = savedDistrict;
                    if (saveBtn) saveBtn.disabled = false;
                }
            }, 400);
        }
    }

    function showGpsStatus(msg, type = "info") {
        const el = document.getElementById("modalGpsStatus");
        if (!el) return;
        el.className = `ab-gps-status ${type}`;
        el.textContent = msg;
        el.style.display = "block";
    }

    // ==========================================================================
    // 3. NAVBAR INTERACTIVITY & LOGOUT
    // ==========================================================================

    function initNavbarHandlers() {
        // Mobile menu toggle
        const menuBtn = document.getElementById("abMobileMenu");
        const mobilePanel = document.getElementById("abMobilePanel");

        if (menuBtn && mobilePanel) {
            menuBtn.addEventListener("click", () => {
                const isOpen = mobilePanel.classList.toggle("open");
                menuBtn.setAttribute("aria-expanded", String(isOpen));
                mobilePanel.setAttribute("aria-hidden", String(!isOpen));
            });

            mobilePanel.querySelectorAll("a").forEach(link => {
                link.addEventListener("click", () => {
                    mobilePanel.classList.remove("open");
                    menuBtn.setAttribute("aria-expanded", "false");
                    mobilePanel.setAttribute("aria-hidden", "true");
                });
            });
        }

        // Language selector button
        const langBtn = document.getElementById("languageButton");
        const selectedLangLabel = document.getElementById("selectedLanguage");

        if (selectedLangLabel && typeof getCurrentLanguage === "function") {
            const code = getCurrentLanguage();
            const names = {
                "en": "English", "hi": "हिंदी (Hindi)", "pa": "ਪੰਜਾਬੀ (Punjabi)",
                "mr": "मराठी (Marathi)", "bn": "বাংলা (Bengali)", "gu": "ગુજરાતી (Gujarati)",
                "ta": "தமிழ் (Tamil)", "te": "తెలుగు (Telugu)", "kn": "ಕನ್ನಡ (Kannada)",
                "ml": "മലയാളം (Malayalam)", "or": "ଓଡ଼ିଆ (Odia)", "as": "অসমীয়া (Assamese)", "ur": "اردو (Urdu)"
            };
            selectedLangLabel.textContent = names[code] || "English";
        }

        if (langBtn) {
            langBtn.addEventListener("click", () => {
                // Focus or trigger select if present
                const langSelect = document.querySelector(".lang-select");
                if (langSelect) {
                    langSelect.focus();
                    try { langSelect.showPicker(); } catch (e) {}
                }
            });
        }

        // Logout buttons
        const desktopLogout = document.getElementById("logoutButton");
        const mobileLogout = document.getElementById("mobileLogoutButton");

        function handleLogout() {
            if (window.AgriBridgeAuth && typeof window.AgriBridgeAuth.logout === "function") {
                window.AgriBridgeAuth.logout();
            } else {
                localStorage.removeItem("agribridge_token");
                localStorage.removeItem("agribridge_user");
                window.location.href = "/frontend/pages/login.html";
            }
        }

        if (desktopLogout) desktopLogout.addEventListener("click", handleLogout);
        if (mobileLogout) mobileLogout.addEventListener("click", handleLogout);
    }

    // ==========================================================================
    // 4. LIVE MINI-WEATHER CARD
    // ==========================================================================

    async function loadMiniWeather() {
        const tempEl = document.getElementById("miniWeatherTemp");
        const descEl = document.getElementById("miniWeatherDesc");
        const detailsEl = document.getElementById("miniWeatherDetails");
        const advisoryEl = document.getElementById("miniWeatherAdvisory");
        const kpiRainEl = document.getElementById("kpi-rain-prob");

        if (!currentFarmerLocation) {
            if (tempEl) tempEl.textContent = "--°C";
            if (descEl) descEl.textContent = "Location Needed";
            if (detailsEl) detailsEl.textContent = "Select farm location to activate live weather";
            if (advisoryEl) {
                advisoryEl.textContent = "📍 Select your State & District to load hyper-local weather alerts";
                advisoryEl.style.background = "rgba(16, 185, 129, 0.15)";
                advisoryEl.style.color = "#065F46";
            }
            if (kpiRainEl) kpiRainEl.textContent = "--%";
            return;
        }

        try {
            const resp = await fetch(`/api/weather/timing-alert?region=${encodeURIComponent(currentFarmerLocation)}&crop=${encodeURIComponent(currentFarmerCrop)}`);
            if (resp.ok) {
                const data = await resp.json();
                if (data.success && data.alert) {
                    const prob = data.alert.rain_probability || 0;
                    if (kpiRainEl) {
                        kpiRainEl.textContent = `${prob}%`;
                        kpiRainEl.style.color = prob >= 60 ? "#C2410C" : "#15803D";
                    }

                    if (descEl) {
                        descEl.textContent = prob >= 60 ? "Rain Expected Soon" : "Favorable & Dry";
                    }

                    if (advisoryEl) {
                        if (prob >= 60) {
                            advisoryEl.textContent = "⚠️ Rain risk high — delay chemical spraying and harvesting";
                            advisoryEl.style.background = "rgba(234, 88, 12, 0.2)";
                            advisoryEl.style.color = "#FED7AA";
                        } else {
                            advisoryEl.textContent = "🌱 Good conditions for fertilizer and foliar spray";
                            advisoryEl.style.background = "rgba(255, 255, 255, 0.08)";
                            advisoryEl.style.color = "#C2D6BA";
                        }
                    }
                }
            }
        } catch (e) {
            console.warn("Weather fetch notice:", e);
        }
    }

    // ==========================================================================
    // 5. LIVE TIMING ADVICE ALERT BANNER
    // ==========================================================================

    async function loadTimingAlert() {
        const banner = document.getElementById("timing-alert-banner");
        const messageEl = document.getElementById("timing-alert-message");
        if (!banner || !messageEl) return;

        if (!currentFarmerLocation) {
            banner.style.display = "none";
            return;
        }

        try {
            const response = await fetch(
                `/api/weather/timing-alert?region=${encodeURIComponent(currentFarmerLocation)}&crop=${encodeURIComponent(currentFarmerCrop)}`
            );

            if (!response.ok) return;
            const data = await response.json();
            if (!data.success || !data.alert) return;

            currentTimingAlertData = data.alert;
            renderTimingAlert(currentTimingAlertData);
        } catch (err) {
            console.warn("Failed to load timing advice alert:", err);
        }
    }

    function renderTimingAlert(alert) {
        const banner = document.getElementById("timing-alert-banner");
        const iconEl = document.getElementById("timing-alert-icon");
        const badgeEl = document.getElementById("timing-alert-badge");
        const messageEl = document.getElementById("timing-alert-message");

        if (!banner || !alert) return;

        const isWarning = alert.status === "delayed" || alert.rain_risk === true;
        banner.className = `timing-alert-banner ${isWarning ? "alert-warning" : "alert-favorable"}`;

        if (iconEl) iconEl.textContent = isWarning ? "⚠️" : "🌱";
        if (badgeEl) {
            badgeEl.textContent = isWarning ? "SPRAY DELAY ADVISORY" : "CONDITIONS FAVORABLE";
        }
        if (messageEl) {
            messageEl.textContent = alert.summary || alert.advice;
        }

        banner.style.display = "flex";
    }

    // ==========================================================================
    // 6. KPI METRICS COUNTER
    // ==========================================================================

    function loadKpiMetrics() {
        const activeListingsEl = document.getElementById("kpi-active-listings");
        const buyerOrdersEl = document.getElementById("kpi-buyer-orders");
        const healthScoreEl = document.getElementById("kpi-health-score");

        // 1. Active Listings Count
        try {
            const savedListings = localStorage.getItem("cropListings");
            if (savedListings) {
                const list = JSON.parse(savedListings);
                if (activeListingsEl) activeListingsEl.textContent = Array.isArray(list) ? list.length : 1;
            } else if (localStorage.getItem("cropData")) {
                if (activeListingsEl) activeListingsEl.textContent = "1";
            } else {
                if (activeListingsEl) activeListingsEl.textContent = "1";
            }
        } catch (e) {}

        // 2. Buyer Commitments Count
        try {
            const currentUser = (window.AgriBridgeAuth && window.AgriBridgeAuth.getCurrentUser) ? window.AgriBridgeAuth.getCurrentUser() : null;
            const farmerId = (currentUser && currentUser.id) ? currentUser.id : null;
            const ordersUrl = farmerId ? `/api/orders/?farmer_id=${farmerId}` : "/api/orders/";
            
            fetch(ordersUrl)
                .then(res => res.ok ? res.json() : null)
                .then(data => {
                    const dbCount = (data && data.orders) ? data.orders.length : 0;
                    const localCount = (localStorage.getItem("buyerCommitment") === "true") ? 1 : 0;
                    const totalCount = dbCount > 0 ? dbCount : localCount;
                    if (buyerOrdersEl) buyerOrdersEl.textContent = totalCount.toString();
                })
                .catch(() => {
                    const localCount = (localStorage.getItem("buyerCommitment") === "true") ? 1 : 0;
                    if (buyerOrdersEl) buyerOrdersEl.textContent = localCount.toString();
                });
        } catch (e) {}

        // 3. AI Health Score from recent scan
        try {
            const rawAi = localStorage.getItem("ai_prediction_result") || localStorage.getItem("aiResult");
            if (rawAi) {
                const aiData = JSON.parse(rawAi);
                const conf = Math.round(aiData.confidence_score || aiData.confidence || 92);
                const isHealthy = (aiData.predicted_disease || "").toLowerCase().includes("healthy");
                if (healthScoreEl) {
                    healthScoreEl.textContent = isHealthy ? `Healthy (${conf}%)` : `Detected (${conf}%)`;
                    healthScoreEl.style.color = isHealthy ? "#15803D" : "#C2410C";
                }
            } else {
                if (healthScoreEl) healthScoreEl.textContent = "94% (Good)";
            }
        } catch (e) {}
    }

    // ==========================================================================
    // 7. INCOMING BUYER ORDERS & COMMITMENTS (Live DB + Storage)
    // ==========================================================================

    async function loadBuyerOrders() {
        const container = document.getElementById("orders-container");
        const buyerOrdersEl = document.getElementById("kpi-buyer-orders");
        if (!container) return;

        container.innerHTML = `<div style="padding: 24px; text-align: center; color: #64748B;">Loading incoming buyer commitments...</div>`;

        let orders = [];

        // 1. Attempt fetching live orders from backend database
        try {
            const currentUser = (window.AgriBridgeAuth && window.AgriBridgeAuth.getCurrentUser) ? window.AgriBridgeAuth.getCurrentUser() : null;
            const farmerId = (currentUser && currentUser.id) ? currentUser.id : null;
            const url = farmerId ? `/api/orders/?farmer_id=${farmerId}` : "/api/orders/";

            const res = await fetch(url);
            if (res.ok) {
                const data = await res.json();
                const dbList = Array.isArray(data.orders) ? data.orders : [];
                dbList.forEach(dbOrder => {
                    orders.push({
                        id: dbOrder.id,
                        title: "🤝 Verified Buyer Commitment",
                        buyer: dbOrder.buyer_name || `Wholesale Buyer #${dbOrder.buyer_id}`,
                        cropName: dbOrder.crop_type || "Agricultural Lot",
                        quantity: typeof dbOrder.quantity === "number" ? `${dbOrder.quantity} Quintals` : `${dbOrder.quantity || 50}`,
                        price: dbOrder.price || "₹2,520 / Quintal",
                        location: currentFarmerLocation,
                        harvestDate: dbOrder.harvest_date || "Expected: Next Month",
                        status: dbOrder.status || "Buyer Committed",
                        isReal: true,
                        orderId: dbOrder.id
                    });
                });
            }
        } catch (err) {
            console.warn("Could not load backend orders for farmer:", err);
        }

        // 2. Check localStorage for local demo/client commitments
        const savedCropData = localStorage.getItem("cropData");
        const buyerCommitment = localStorage.getItem("buyerCommitment");

        if (savedCropData && buyerCommitment === "true") {
            try {
                const crop = JSON.parse(savedCropData);
                orders.push({
                    title: "🎉 New Buyer Commitment",
                    buyer: "AgroCorp Processing Ltd",
                    cropName: crop.cropName || crop.crop || "Wheat",
                    quantity: `${crop.quantity || "100"} Quintals`,
                    price: "₹2,450 / Quintal",
                    location: crop.location || currentFarmerLocation,
                    harvestDate: crop.harvestDate || "2026-10-15",
                    status: "Verified & Committed",
                    isReal: true,
                    orderId: "LOCAL"
                });
            } catch (e) {}
        }

        // Update KPI counter
        if (buyerOrdersEl) {
            buyerOrdersEl.textContent = orders.length.toString();
        }

        // 3. Render orders or empty state
        if (orders.length === 0) {
            renderEmptyOrdersState(container);
            return;
        }

        container.innerHTML = "";
        orders.forEach(order => renderOrderCard(container, order));
    }

    function renderEmptyOrdersState(container) {
        container.innerHTML = `
            <div class="no-orders-box">
                <span class="no-orders-icon">📦</span>
                <p class="no-orders-title">No incoming buyer commitments yet.</p>
                <p class="no-orders-sub">When certified wholesale buyers commit forward purchases for your verified crops, your order contracts will appear here in real time.</p>
                <div style="display: flex; gap: 12px; justify-content: center; align-items: center; margin-top: 14px; flex-wrap: wrap;">
                    <a href="/frontend/pages/upload-crop.html" class="stylish-btn ab-btn-primary">
                        + Upload & List Crop
                    </a>
                    <button type="button" id="btn-toggle-demo-order" class="stylish-btn" style="background: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; font-size: 13px; padding: 7px 16px;">
                        👁️ Show Demo Preview
                    </button>
                </div>
            </div>
        `;

        const btnDemo = document.getElementById("btn-toggle-demo-order");
        if (btnDemo) {
            btnDemo.addEventListener("click", function () {
                container.innerHTML = "";
                renderOrderCard(container, {
                    title: "🤝 Buyer Pre-Harvest Commitment",
                    buyer: "Kisan Mandi Direct",
                    cropName: "Sharbati Wheat",
                    quantity: "50 Quintals",
                    price: "₹2,520 / Quintal",
                    location: currentFarmerLocation,
                    harvestDate: "Expected: Next Month",
                    status: "Demo Preview",
                    isDemo: true
                });
            });
        }
    }

    function renderOrderCard(container, order) {
        const card = document.createElement("div");
        card.className = "order-card";
        const statusBadge = order.isDemo ? "ℹ️ Demo Preview" : `✓ ${order.status}`;
        const detailLink = order.orderId && order.orderId !== "LOCAL"
            ? `/frontend/pages/orders.html?order_id=${order.orderId}`
            : "/frontend/pages/orders.html";

        card.innerHTML = `
            <div class="order-card-header">
                <span class="order-buyer-name">${order.buyer}</span>
                <span class="order-status-pill ${order.isDemo ? 'pill-demo' : ''}">${statusBadge}</span>
            </div>
            <h3 class="order-crop-title">${order.cropName}</h3>
            <div class="order-specs-grid">
                <div class="order-spec-item">
                    <span class="spec-label">Quantity</span>
                    <strong class="spec-val">${order.quantity}</strong>
                </div>
                <div class="order-spec-item">
                    <span class="spec-label">Agreed Rate</span>
                    <strong class="spec-val">${order.price}</strong>
                </div>
                <div class="order-spec-item">
                    <span class="spec-label">Harvest Window</span>
                    <strong class="spec-val">${order.harvestDate}</strong>
                </div>
            </div>
            <div class="order-actions-row">
                <a href="${detailLink}" class="btn-subtle green-cta">View Order Details →</a>
            </div>
        `;
        container.appendChild(card);
    }

    // ==========================================================================
    // 8. RECENT FARM ACTIVITY FEED
    // ==========================================================================

    async function loadActivityFeed() {
        const container = document.getElementById("activity-container");
        if (!container) return;

        let farmerId = null;
        if (window.AgriBridgeAuth && window.AgriBridgeAuth.getCurrentUser()) {
            farmerId = window.AgriBridgeAuth.getCurrentUser().id || null;
        }

        const url = farmerId ? `/api/farmers/${farmerId}/activity` : "/api/farmers/activity";

        try {
            const res = await fetch(url);
            if (res.ok) {
                const data = await res.json();
                const activities = Array.isArray(data.activities) ? data.activities : [];

                if (activities.length > 0) {
                    container.innerHTML = "";
                    activities.forEach(item => {
                        const div = document.createElement("div");
                        div.className = "activity-item";
                        div.innerHTML = `
                            <div class="activity-icon ${item.bg}">${item.icon}</div>
                            <div class="activity-content">
                                <h3>${item.title}</h3>
                                <p>${item.desc}</p>
                                <span class="activity-time">${item.time}</span>
                            </div>
                        `;
                        container.appendChild(div);
                    });
                    return;
                }
            }
        } catch (e) {
            console.warn("Could not fetch backend activity feed:", e);
        }

        // Clean fallback
        container.innerHTML = `
            <div class="activity-item">
                <div class="activity-icon bg-green">🌱</div>
                <div class="activity-content">
                    <h3>Farm Health Monitoring Active</h3>
                    <p>AgriBridge is monitoring your active plots. Scan a leaf or upload harvest lots to view real-time log entries.</p>
                    <span class="activity-time">Live</span>
                </div>
            </div>
        `;
    }

    // ==========================================================================
    // 9. AUTONOMOUS FIELD ACTION PLANS & TRACE (PROMPT 6)
    // ==========================================================================

    async function loadFieldActionPlans() {
        const container = document.getElementById("action-plans-container");
        if (!container) return;

        let farmerId = 1;
        if (window.AgriBridgeAuth && window.AgriBridgeAuth.getCurrentUser()) {
            farmerId = window.AgriBridgeAuth.getCurrentUser().id || 1;
        }

        try {
            const res = await fetch(`/api/action-plans/${farmerId}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            container.innerHTML = "";

            const plans = data.action_plans || [];
            if (plans.length === 0) {
                container.innerHTML = `
                    <div style="background: white; border: 1px dashed #CBD5E1; border-radius: 12px; padding: 24px; text-align: center; color: #64748B; grid-column: 1 / -1;">
                        No active field action plans yet. Upload a crop photo to generate autonomous diagnostic tasks.
                    </div>
                `;
                return;
            }

            plans.slice(0, 3).forEach(plan => {
                const latestTask = (plan.tasks && plan.tasks.length > 0) ? plan.tasks[plan.tasks.length - 1] : null;
                const totalTasks = plan.tasks ? plan.tasks.length : 0;
                const isReplanned = totalTasks > 1;

                let statusBadge = `<span style="background: #DCFCE7; color: #166534; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 4px; text-transform: uppercase;">Active</span>`;
                if (plan.status === "needs_expert_review") {
                    statusBadge = `<span style="background: #FEF3C7; color: #92400E; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 4px; text-transform: uppercase;">⚠️ Expert Review</span>`;
                } else if (plan.status === "completed") {
                    statusBadge = `<span style="background: #E2E8F0; color: #334155; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 4px; text-transform: uppercase;">Completed</span>`;
                }

                const card = document.createElement("div");
                card.style.cssText = "background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 20px; box-shadow: 0 4px 12px rgba(15,23,42,0.05); display: flex; flex-direction: column; justify-content: space-between; transition: all 0.2s ease;";
                
                card.innerHTML = `
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                            <span style="font-family: monospace; font-size: 12px; font-weight: 700; color: #64748B;">PLAN #${plan.id}</span>
                            <div style="display: flex; gap: 6px; align-items: center;">
                                ${isReplanned ? '<span style="background: #FEE2E2; color: #991B1B; font-size: 10px; font-weight: 800; padding: 2px 6px; border-radius: 4px;">🔄 REPLANNED</span>' : ''}
                                ${statusBadge}
                            </div>
                        </div>
                        <h3 style="font-size: 16px; font-weight: 700; color: #0F172A; margin: 0 0 6px 0;">
                            ${latestTask ? escapeHtml(latestTask.title) : 'Treatment Protocol'}
                        </h3>
                        <p style="font-size: 13px; color: #475569; margin: 0 0 12px 0; line-height: 1.4;">
                            ${latestTask && latestTask.reasoning ? escapeHtml(latestTask.reasoning.substring(0, 110)) + '...' : 'Optimized for current meteorological conditions.'}
                        </p>
                        <div style="font-size: 12px; color: #64748B; margin-bottom: 16px; display: flex; gap: 12px;">
                            <span>⏱️ ${plan.created_at ? new Date(plan.created_at).toLocaleDateString() : 'Recent'}</span>
                            <span>📋 ${totalTasks} Milestone${totalTasks === 1 ? '' : 's'}</span>
                        </div>
                    </div>
                    <a href="/frontend/pages/action-plan-trace.html?id=${plan.id}" 
                       style="display: flex; align-items: center; justify-content: center; gap: 6px; background: #0F5132; color: #FFFFFF; text-decoration: none; font-size: 13px; font-weight: 600; padding: 10px 14px; border-radius: 8px; transition: background 0.2s ease;">
                        <span>🔍 View Autonomous Reasoning Trace →</span>
                    </a>
                `;

                container.appendChild(card);
            });
        } catch (err) {
            console.error("Failed to load action plans:", err);
            container.innerHTML = `
                <div style="background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; color: #64748B; text-align: center; grid-column: 1 / -1;">
                    ⚠️ Unable to connect to database — please verify your connection and try again.
                </div>
            `;
        }
    }

    // ==========================================================================
    // 7. ACTIVE CROPS & FIELD LIFECYCLE LOADER
    // ==========================================================================

    async function loadActiveCrops() {
        const grid = document.getElementById("activeCropsGrid");
        if (!grid) return;

        try {
            const res = await fetch("/api/v1/monitoring/active-crops");
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            const crops = data.active_crops || [];
            if (crops.length === 0) {
                grid.innerHTML = `
                    <div style="background: white; border: 1px dashed #CBD5E1; border-radius: 12px; padding: 24px; text-align: center; color: #64748B; grid-column: 1 / -1;">
                        No active crops found. Select a crop in Crop Monitoring or register a farm plot to begin date-aware lifecycle tracking.
                    </div>
                `;
                return;
            }

            grid.innerHTML = "";
            crops.forEach(crop => {
                const cropCard = document.createElement("div");
                cropCard.className = "active-crop-card";

                const cropEmoji = crop.crop_name.toLowerCase().includes("wheat") ? "🌾" :
                                 crop.crop_name.toLowerCase().includes("paddy") || crop.crop_name.toLowerCase().includes("rice") ? "🍚" :
                                 crop.crop_name.toLowerCase().includes("mustard") ? "🌼" :
                                 crop.crop_name.toLowerCase().includes("cotton") ? "🌱" : "🌿";

                cropCard.innerHTML = `
                    <div>
                        <div class="active-crop-header">
                            <div class="active-crop-title-wrap">
                                <span class="active-crop-field-id">${escapeHtml(crop.field_id)}</span>
                                <h3 class="active-crop-name">${cropEmoji} ${escapeHtml(crop.crop_name)}</h3>
                            </div>
                            <span class="active-crop-stage-badge">🌱 ${escapeHtml(crop.human_stage_name || crop.current_stage)}</span>
                        </div>
                        <div class="active-crop-meta-grid" style="margin-top: 14px;">
                            <div class="active-crop-meta-item">
                                <span class="active-crop-meta-label">Crop Age</span>
                                <span class="active-crop-meta-val">⏱️ ${crop.days_after_planting} Days After Planting</span>
                            </div>
                            <div class="active-crop-meta-item">
                                <span class="active-crop-meta-label">Planting Date</span>
                                <span class="active-crop-meta-val">📅 ${escapeHtml(crop.formatted_planting_date || crop.planting_date)}</span>
                            </div>
                        </div>
                    </div>
                    <button type="button" class="active-crop-action-btn" data-crop="${escapeHtml(crop.crop_name)}" data-pdate="${escapeHtml(crop.planting_date)}" data-field="${escapeHtml(crop.field_id)}">
                        <span>📊 OPEN CROP MONITORING</span>
                        <span>→</span>
                    </button>
                `;

                // Add button click listener
                const btn = cropCard.querySelector(".active-crop-action-btn");
                if (btn) {
                    btn.addEventListener("click", () => {
                        localStorage.setItem("cropMonitoringSelectedCrop", crop.crop_name);
                        localStorage.setItem("cropMonitoringPlantingDate", crop.planting_date);
                        localStorage.setItem("cropMonitoringFieldId", crop.field_id);
                        window.location.href = `/frontend/pages/crop-monitoring.html?crop=${encodeURIComponent(crop.crop_name)}&planting_date=${encodeURIComponent(crop.planting_date)}&field_id=${encodeURIComponent(crop.field_id)}`;
                    });
                }

                grid.appendChild(cropCard);
            });
        } catch (err) {
            console.warn("Failed to load active crops:", err);
            grid.innerHTML = `
                <div class="active-crop-card">
                    <div>
                        <div class="active-crop-header">
                            <div class="active-crop-title-wrap">
                                <span class="active-crop-field-id">FIELD_WHT_001</span>
                                <h3 class="active-crop-name">🌾 Wheat</h3>
                            </div>
                            <span class="active-crop-stage-badge">🌱 Crown Root Initiation (CRI)</span>
                        </div>
                        <div class="active-crop-meta-grid" style="margin-top: 14px;">
                            <div class="active-crop-meta-item">
                                <span class="active-crop-meta-label">Crop Age</span>
                                <span class="active-crop-meta-val">⏱️ 43 Days After Planting</span>
                            </div>
                            <div class="active-crop-meta-item">
                                <span class="active-crop-meta-label">Planting Date</span>
                                <span class="active-crop-meta-val">📅 01 Aug 2026</span>
                            </div>
                        </div>
                    </div>
                    <button type="button" class="active-crop-action-btn" onclick="window.location.href='/frontend/pages/crop-monitoring.html?crop=Wheat&planting_date=2026-08-01'">
                        <span>📊 OPEN CROP MONITORING</span>
                        <span>→</span>
                    </button>
                </div>
            `;
        }
    }

    // ==========================================================================
    // 8. FARMER NOTIFICATION DASHBOARD & COMMAND CENTER
    // ==========================================================================

    function initNotificationCenter() {
        const filterTabs = document.querySelectorAll("#notifFilterTabs .notif-tab-btn");
        filterTabs.forEach(tab => {
            tab.addEventListener("click", () => {
                filterTabs.forEach(t => t.classList.remove("active"));
                tab.classList.add("active");
                currentNotifFilter = tab.getAttribute("data-filter") || "ALL";
                loadFarmerNotifications();
            });
        });

        const btnMarkAll = document.getElementById("btnMarkAllNotifsRead");
        if (btnMarkAll) {
            btnMarkAll.addEventListener("click", async () => {
                try {
                    const currentUser = window.AgriBridgeAuth ? window.AgriBridgeAuth.getCurrentUser() : null;
                    const farmerId = currentUser ? currentUser.id : null;
                    const url = farmerId ? `/api/farmers/notifications/read-all?farmer_id=${farmerId}` : "/api/farmers/notifications/read-all";
                    await fetch(url, { method: "POST" });
                    await loadFarmerNotifications();
                } catch (e) {
                    console.warn("Mark all read failed:", e);
                }
            });
        }
    }

    async function loadFarmerNotifications() {
        const container = document.getElementById("farmer-notifications-container");
        const unreadBadge = document.getElementById("notif-unread-count");
        const navNotifCount = document.getElementById("navNotifCount");

        if (!container) return;

        let farmerId = null;
        if (window.AgriBridgeAuth && window.AgriBridgeAuth.getCurrentUser()) {
            farmerId = window.AgriBridgeAuth.getCurrentUser().id || null;
        }

        const url = farmerId 
            ? `/api/farmers/${farmerId}/notifications?filter_type=${encodeURIComponent(currentNotifFilter)}` 
            : `/api/farmers/notifications?filter_type=${encodeURIComponent(currentNotifFilter)}`;

        try {
            const res = await fetch(url);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            allLoadedNotifications = data.notifications || [];
            const unreadCount = data.unread_count || 0;

            if (unreadBadge) unreadBadge.textContent = unreadCount.toString();
            if (navNotifCount) navNotifCount.textContent = unreadCount.toString();

            // Update tab counts if on ALL filter
            if (currentNotifFilter === "ALL") {
                updateTabCounters(allLoadedNotifications);
            }

            if (allLoadedNotifications.length === 0) {
                container.innerHTML = `
                    <div class="notif-empty-state">
                        <span style="font-size: 28px; display: block; margin-bottom: 8px;">🌱</span>
                        <strong style="color: #1E293B;">No notifications in this category.</strong>
                        <p style="margin: 4px 0 0 0; font-size: 13px;">Diagnostic approvals, chemical prescriptions, and inspection alerts will appear here in real time.</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = "";
            allLoadedNotifications.forEach(notif => {
                const card = renderNotificationCard(notif);
                container.appendChild(card);
            });

        } catch (err) {
            console.warn("Failed to load notifications from backend:", err);
            // Graceful demo fallback
            renderFallbackNotifications(container);
        }
    }

    function updateTabCounters(notifs) {
        const countAll = notifs.length;
        const countTx = notifs.filter(n => n.notification_type === "TREATMENT_APPROVED" || n.notification_type === "TREATMENT").length;
        const countInsp = notifs.filter(n => n.notification_type === "INSPECTION_DISPATCHED" || n.notification_type === "INSPECTION" || n.notification_type === "NEEDS_PHYSICAL_VISIT").length;
        const countWeather = notifs.filter(n => n.notification_type === "WEATHER_ALERT" || n.notification_type === "WEATHER").length;
        const countOrders = notifs.filter(n => n.notification_type === "ORDER" || n.notification_type === "BUYER_ORDER" || n.notification_type === "LISTING_VERIFIED" || n.notification_type === "LISTING_REJECTED").length;

        const elAll = document.getElementById("tab-count-all");
        const elTx = document.getElementById("tab-count-treatments");
        const elInsp = document.getElementById("tab-count-inspections");
        const elWeather = document.getElementById("tab-count-weather");
        const elOrders = document.getElementById("tab-count-orders");

        if (elAll) elAll.textContent = countAll.toString();
        if (elTx) elTx.textContent = countTx.toString();
        if (elInsp) elInsp.textContent = countInsp.toString();
        if (elWeather) elWeather.textContent = countWeather.toString();
        if (elOrders) elOrders.textContent = countOrders.toString();
    }

    function renderNotificationCard(notif) {
        const card = document.createElement("div");
        const nType = notif.notification_type || "SYSTEM";
        const meta = notif.meta_data || {};
        const diseaseScan = notif.disease_scan || {};

        let typeClass = "system";
        let typeTag = "Notification";
        let typeIcon = "🔔";

        if (nType === "TREATMENT_APPROVED" || nType === "TREATMENT") {
            typeClass = "treatment";
            typeTag = "ICAR Verified Rx";
            typeIcon = "🩺";
        } else if (nType === "INSPECTION_DISPATCHED" || nType === "INSPECTION" || nType === "NEEDS_PHYSICAL_VISIT") {
            typeClass = "inspection";
            typeTag = "On-Site Visit";
            typeIcon = "🚨";
        } else if (nType === "WEATHER_ALERT" || nType === "WEATHER") {
            typeClass = "weather";
            typeTag = "Spray Advisory";
            typeIcon = "🌦️";
        } else if (nType === "ORDER" || nType === "BUYER_ORDER" || nType === "LISTING_VERIFIED" || nType === "LISTING_REJECTED") {
            typeClass = "order";
            typeTag = nType === "LISTING_VERIFIED" ? "Listing Verified" : (nType === "LISTING_REJECTED" ? "Listing Update" : "Buyer Order");
            typeIcon = nType === "LISTING_VERIFIED" ? "📋" : "🤝";
        }

        card.className = `notif-card ${typeClass} ${notif.is_unread ? 'unread' : ''}`;

        // Header
        let headerHtml = `
            <div class="notif-card-header">
                <div class="notif-card-title-wrap">
                    <span class="notif-icon-box">${typeIcon}</span>
                    <h3 class="notif-card-title">${escapeHtml(notif.title)}</h3>
                    <span class="notif-type-tag tag-${typeClass}">${typeTag}</span>
                </div>
                <span class="notif-time-badge">${escapeHtml(notif.time_ago || "Recent")}</span>
            </div>
        `;

        // Body message
        let bodyHtml = `
            <div class="notif-card-body">
                <p class="notif-msg-text">${escapeHtml(notif.message)}</p>
            </div>
        `;

        // Meta box for treatment prescription or inspection details
        let metaHtml = "";
        let actionsHtml = "";

        if (nType === "TREATMENT_APPROVED") {
            const chem = meta.chemical_name || diseaseScan.chemical || "Mancozeb 75% WP";
            const dose = meta.exact_dosage || diseaseScan.dosage || "2.0 g/L water";
            const phi = meta.pre_harvest_interval || diseaseScan.phi || "7-10 Days PHI";
            const agent = meta.agent_name || diseaseScan.agent_name || "Field Agent Rahul";
            const targetUrl = notif.action_url || (notif.related_id ? `/frontend/pages/ai-result.html?record_id=${notif.related_id}` : '/frontend/pages/ai-result.html');

            metaHtml = `
                <div class="notif-meta-box">
                    <div class="notif-meta-item">
                        <span class="notif-meta-lbl">Approved ICAR Chemical</span>
                        <span class="notif-meta-val" style="color: #065F46;">${escapeHtml(chem)}</span>
                    </div>
                    <div class="notif-meta-item">
                        <span class="notif-meta-lbl">Exact Knapsack Dosage</span>
                        <span class="notif-meta-val">${escapeHtml(dose)}</span>
                    </div>
                    <div class="notif-meta-item">
                        <span class="notif-meta-lbl">Pre-Harvest Safety Interval</span>
                        <span class="notif-meta-val" style="color: #DC2626;">${escapeHtml(phi)}</span>
                    </div>
                    <div class="notif-meta-item">
                        <span class="notif-meta-lbl">Authorizing Agronomist</span>
                        <span class="notif-meta-val">${escapeHtml(agent)}</span>
                    </div>
                </div>
            `;

            actionsHtml = `
                <div class="notif-actions-row">
                    <a href="${targetUrl}" class="btn-notif-action btn-view-rx">
                        🩺 View Accepted Treatment & Rx →
                    </a>
                </div>
            `;

        } else if (nType === "INSPECTION_DISPATCHED") {
            const inspStatus = diseaseScan.inspection_status || meta.inspection_status || "SCHEDULED";
            const inspDate = meta.scheduled_date_formatted || (diseaseScan.inspection_date ? new Date(diseaseScan.inspection_date).toLocaleDateString() : "Tomorrow 10:00 AM");
            const agent = meta.agent_name || diseaseScan.agent_name || "Field Agent Rahul (Agri-Student)";
            const recordId = notif.related_id || meta.record_id || (diseaseScan ? diseaseScan.id : null);
            const cropName = meta.crop_type || diseaseScan.crop_type || "Crop";

            metaHtml = `
                <div class="notif-meta-box">
                    <div class="notif-meta-item">
                        <span class="notif-meta-lbl">Assigned Field Agent</span>
                        <span class="notif-meta-val">${escapeHtml(agent)}</span>
                    </div>
                    <div class="notif-meta-item">
                        <span class="notif-meta-lbl">Scheduled Visit Date</span>
                        <span class="notif-meta-val" style="color: #92400E;">📅 ${escapeHtml(inspDate)}</span>
                    </div>
                    <div class="notif-meta-item">
                        <span class="notif-meta-lbl">Visit Purpose</span>
                        <span class="notif-meta-val">On-Site Leaf Lesion Verification</span>
                    </div>
                    <div class="notif-meta-item">
                        <span class="notif-meta-lbl">Current Schedule Status</span>
                        <span class="notif-meta-val">
                            ${inspStatus === 'CONFIRMED' ? '<span class="inspection-status-pill pill-confirmed">✓ Confirmed</span>' :
                              inspStatus === 'RESCHEDULED' ? '<span class="inspection-status-pill pill-rescheduled">📅 Rescheduled</span>' :
                              inspStatus === 'REJECTED' ? '<span class="inspection-status-pill pill-rejected">❌ Declined</span>' :
                              '<span class="inspection-status-pill pill-scheduled">⏳ Awaiting Confirmation</span>'}
                        </span>
                    </div>
                </div>
            `;

            if (inspStatus === "CONFIRMED") {
                actionsHtml = `
                    <div class="notif-actions-row">
                        <span class="inspection-status-pill pill-confirmed">✅ Visit Confirmed by You</span>
                        <button type="button" class="btn-notif-action btn-reschedule-visit" onclick="openRescheduleModal(${recordId}, '${escapeHtml(cropName)}', '${escapeHtml(inspDate)}')">
                            📅 Reschedule Visit
                        </button>
                    </div>
                `;
            } else if (inspStatus === "RESCHEDULED") {
                actionsHtml = `
                    <div class="notif-actions-row">
                        <span class="inspection-status-pill pill-rescheduled">📅 Rescheduled to ${escapeHtml(inspDate)}</span>
                        <button type="button" class="btn-notif-action btn-confirm-visit" onclick="confirmInspection(${recordId}, ${notif.id})">
                            ✅ Confirm This Date
                        </button>
                    </div>
                `;
            } else if (inspStatus === "REJECTED") {
                actionsHtml = `
                    <div class="notif-actions-row">
                        <span class="inspection-status-pill pill-rejected">❌ You declined this field visit</span>
                        <button type="button" class="btn-notif-action btn-reschedule-visit" onclick="openRescheduleModal(${recordId}, '${escapeHtml(cropName)}', '${escapeHtml(inspDate)}')">
                            📅 Request Inspection for Later
                        </button>
                    </div>
                `;
            } else {
                // SCHEDULED (Pending farmer confirmation or rejection or reschedule)
                actionsHtml = `
                    <div class="notif-actions-row">
                        <button type="button" class="btn-notif-action btn-confirm-visit" onclick="confirmInspection(${recordId}, ${notif.id})">
                            ✅ Confirm Visit
                        </button>
                        <button type="button" class="btn-notif-action btn-reject-visit" onclick="rejectInspection(${recordId}, ${notif.id})">
                            ❌ Reject / Decline Visit
                        </button>
                        <button type="button" class="btn-notif-action btn-reschedule-visit" onclick="openRescheduleModal(${recordId}, '${escapeHtml(cropName)}', '${escapeHtml(inspDate)}')">
                            📅 Schedule for Later
                        </button>
                    </div>
                `;
            }
        } else if (nType === "ORDER" || nType === "BUYER_ORDER" || nType === "LISTING_VERIFIED" || nType === "LISTING_REJECTED") {
            const targetUrl = notif.action_url || (nType.startsWith("LISTING") ? "/frontend/pages/crop-listings.html" : "/frontend/pages/orders.html");
            const btnLabel = nType.startsWith("LISTING") ? "📋 View Marketplace Listings →" : "🤝 View Orders →";
            actionsHtml = `
                <div class="notif-actions-row">
                    <a href="${targetUrl}" class="btn-notif-action btn-view-rx">
                        ${btnLabel}
                    </a>
                </div>
            `;
        }

        card.innerHTML = headerHtml + bodyHtml + metaHtml + actionsHtml;
        return card;
    }

    function renderFallbackNotifications(container) {
        container.innerHTML = `
            <div class="notif-card treatment">
                <div class="notif-card-header">
                    <div class="notif-card-title-wrap">
                        <span class="notif-icon-box">🩺</span>
                        <h3 class="notif-card-title">ICAR Prescription Approved: Tomato — Early Blight</h3>
                        <span class="notif-type-tag tag-treatment">ICAR Verified Rx</span>
                    </div>
                    <span class="notif-time-badge">Just now</span>
                </div>
                <div class="notif-card-body">
                    <p class="notif-msg-text">Field Agent Rahul verified your leaf diagnostic scan. Approved Agronomic Prescription: Apply Mancozeb 75% WP @ 2.0 g / L water. Strictly observe 7-10 Days PHI.</p>
                </div>
                <div class="notif-meta-box">
                    <div class="notif-meta-item">
                        <span class="notif-meta-lbl">Approved Chemical</span>
                        <span class="notif-meta-val" style="color: #065F46;">Mancozeb 75% WP</span>
                    </div>
                    <div class="notif-meta-item">
                        <span class="notif-meta-lbl">Dosage</span>
                        <span class="notif-meta-val">2.0 g / L water</span>
                    </div>
                    <div class="notif-meta-item">
                        <span class="notif-meta-lbl">Pre-Harvest Interval</span>
                        <span class="notif-meta-val" style="color: #DC2626;">7-10 Days PHI</span>
                    </div>
                </div>
                <div class="notif-actions-row">
                    <a href="/frontend/pages/ai-result.html" class="btn-notif-action btn-view-rx">
                        🩺 View Accepted Treatment & Rx →
                    </a>
                </div>
            </div>
        `;
    }

    // ==========================================================================
    // 9. FARMER INSPECTION ACTIONS (CONFIRM, REJECT, RESCHEDULE)
    // ==========================================================================

    window.confirmInspection = async function(recordId, notifId) {
        if (!recordId) return;
        try {
            const res = await fetch(`/api/verifications/disease-scans/${recordId}/inspection-response`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: "CONFIRM", notes: "Farmer confirmed inspection date." })
            });
            const data = await res.json();
            if (!res.ok || !data.success) throw new Error(data.detail || "Confirmation failed");

            alert("✅ Inspection Confirmed! The Agri-Student Field Agent has been notified of your confirmation.");
            await loadFarmerNotifications();
        } catch (err) {
            console.error("Confirm inspection error:", err);
            alert(`⚠️ Error confirming inspection: ${err.message}`);
        }
    };

    window.rejectInspection = async function(recordId, notifId) {
        if (!recordId) return;
        const reason = prompt("Enter reason for declining the field inspection:", "I will manage using organic cultural methods / Not required at this time.");
        if (reason === null) return;

        try {
            const res = await fetch(`/api/verifications/disease-scans/${recordId}/inspection-response`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: "REJECT", notes: reason })
            });
            const data = await res.json();
            if (!res.ok || !data.success) throw new Error(data.detail || "Rejection failed");

            alert("❌ Inspection Cancelled. Your preference has been recorded.");
            await loadFarmerNotifications();
        } catch (err) {
            console.error("Reject inspection error:", err);
            alert(`⚠️ Error declining inspection: ${err.message}`);
        }
    };

    window.openRescheduleModal = function(recordId, cropName, currentDate) {
        const modal = document.getElementById("rescheduleInspectionModal");
        const cropInfoEl = document.getElementById("rescheduleCropInfo");
        const recIdInput = document.getElementById("rescheduleRecordId");
        const customDateInput = document.getElementById("rescheduleCustomDate");

        if (!modal) return;

        if (recIdInput) recIdInput.value = recordId || "";
        if (cropInfoEl) {
            cropInfoEl.innerHTML = `
                <strong>Field Audit for:</strong> ${escapeHtml(cropName || 'Crop')}<br>
                <strong>Current Proposed Date:</strong> ${escapeHtml(currentDate || 'Tomorrow 10:00 AM')}
            `;
        }

        // Set min date to tomorrow
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        const minStr = tomorrow.toISOString().split("T")[0];
        if (customDateInput) {
            customDateInput.min = minStr;
            customDateInput.value = minStr;
        }

        modal.style.display = "flex";
    };

    function initRescheduleModal() {
        const modal = document.getElementById("rescheduleInspectionModal");
        const closeBtn = document.getElementById("closeRescheduleModalBtn");
        const cancelBtn = document.getElementById("btnCancelReschedule");
        const overlay = document.getElementById("closeRescheduleOverlay");
        const submitBtn = document.getElementById("btnSubmitReschedule");
        const quickChips = document.querySelectorAll(".quick-date-chip");
        const customDateInput = document.getElementById("rescheduleCustomDate");
        const notesInput = document.getElementById("rescheduleNotes");
        const recIdInput = document.getElementById("rescheduleRecordId");

        function closeModal() {
            if (modal) modal.style.display = "none";
        }

        if (closeBtn) closeBtn.addEventListener("click", closeModal);
        if (cancelBtn) cancelBtn.addEventListener("click", closeModal);
        if (overlay) overlay.addEventListener("click", closeModal);

        quickChips.forEach(chip => {
            chip.addEventListener("click", () => {
                quickChips.forEach(c => c.classList.remove("active"));
                chip.classList.add("active");
                const days = parseInt(chip.getAttribute("data-days") || "1", 10);
                const target = new Date();
                target.setDate(target.getDate() + days);
                if (customDateInput) {
                    customDateInput.value = target.toISOString().split("T")[0];
                }
            });
        });

        if (submitBtn) {
            submitBtn.addEventListener("click", async () => {
                const recordId = recIdInput ? recIdInput.value : null;
                const newDate = customDateInput ? customDateInput.value : "";
                const notes = notesInput ? notesInput.value.trim() : "";

                if (!recordId) {
                    alert("Error: Disease scan ID missing.");
                    return;
                }
                if (!newDate) {
                    alert("Please select a valid date for the rescheduled visit.");
                    return;
                }

                try {
                    submitBtn.disabled = true;
                    submitBtn.textContent = "Updating Schedule...";

                    const res = await fetch(`/api/verifications/disease-scans/${recordId}/inspection-response`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            action: "RESCHEDULE",
                            reschedule_date: newDate,
                            notes: notes
                        })
                    });

                    const data = await res.json();
                    if (!res.ok || !data.success) throw new Error(data.detail || "Rescheduling failed");

                    closeModal();
                    alert(`📅 Success! Field inspection rescheduled to ${newDate}. Field agent schedule has been updated.`);
                    await loadFarmerNotifications();

                } catch (err) {
                    console.error("Reschedule submit error:", err);
                    alert(`⚠️ Error rescheduling: ${err.message}`);
                } finally {
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.textContent = "📅 Confirm New Inspection Date";
                    }
                }
            });
        }
    }

    // ==========================================================================
    // PHASE 5: AUTONOMOUS FARM-TO-FIELD LOOP CONTROLLER
    // ==========================================================================

    let currentActiveTaskId = null;
    let currentActiveTaskStatus = "pending";
    let currentActivePlanId = null;
    let activeScenarioMode = "LIVE";

    function initAutonomousLoopController() {
        const refreshBtn = document.getElementById("btnRefreshAutonomousLoop");
        if (refreshBtn) {
            refreshBtn.addEventListener("click", () => {
                loadAutonomousLoopData(activeScenarioMode);
            });
        }

        const scenarioBtns = document.querySelectorAll("#demoScenarioBar .scenario-btn");
        scenarioBtns.forEach(btn => {
            btn.addEventListener("click", () => {
                scenarioBtns.forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                activeScenarioMode = btn.getAttribute("data-scenario") || "LIVE";
                loadAutonomousLoopData(activeScenarioMode);
            });
        });

        const advanceBtn = document.getElementById("btnAdvanceTask");
        if (advanceBtn) {
            advanceBtn.addEventListener("click", async () => {
                await advanceActiveTaskLifecycle();
            });
        }
    }

    async function loadAutonomousLoopData(scenario) {
        scenario = scenario || activeScenarioMode || "LIVE";
        const simPill = document.getElementById("demoSimPill");
        const provBadge = document.getElementById("provenance-badge");

        // 1. Scenario Handler (uses backend deterministic evaluation)
        if (scenario && scenario !== "LIVE") {
            if (simPill) simPill.style.display = "inline-block";
            if (provBadge) {
                provBadge.textContent = "SOURCE: SIMULATED DEMO SIGNAL";
                provBadge.className = "ab-badge ab-badge-gold";
            }

            let payload = {
                farmer_id: 1,
                crop: currentFarmerCrop || "wheat",
                state: "Punjab",
                district: "Ludhiana",
                village: "Samrala"
            };

            if (scenario === "SCENARIO_A") {
                payload.disease_name = "Yellow Rust";
                payload.confidence = 88.5;
                payload.rain_probability = 15;
                payload.wind_speed = 8.0;
            } else if (scenario === "SCENARIO_B") {
                payload.disease_name = "Yellow Rust";
                payload.confidence = 88.5;
                payload.rain_probability = 85;
                payload.wind_speed = 12.0;
            } else if (scenario === "SCENARIO_C") {
                payload.disease_name = "Leaf Blight (Suspected)";
                payload.confidence = 52.0;
                payload.rain_probability = 15;
            } else if (scenario === "SCENARIO_D") {
                payload.disease_name = "Yellow Rust (ICAR Verified)";
                payload.confidence = 98.0;
                payload.rain_probability = 20;
            } else if (scenario === "SCENARIO_F") {
                payload.disease_name = "Yellow Rust";
                payload.confidence = 90.0;
                payload.soil_moisture_vwc = 16.5;
                payload.rain_probability = 10;
            }

            try {
                const res = await fetch("/api/orchestration/evaluate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const data = await res.json();
                renderAutonomousDecision(data, payload, true);
                return;
            } catch (err) {
                console.error("Scenario evaluation failed:", err);
            }
        }

        // 2. Live Farm Mode: Fetch canonical context & action plans from backend
        if (simPill) simPill.style.display = "none";
        if (provBadge) {
            provBadge.textContent = "SOURCE: LIVE SIGNALS";
            provBadge.className = "ab-badge ab-badge-gray";
        }

        let farmerId = 1;
        if (window.AgriBridgeAuth && window.AgriBridgeAuth.getCurrentUser()) {
            farmerId = window.AgriBridgeAuth.getCurrentUser().id || 1;
        }

        try {
            // Parallel fetch of canonical context & action plans
            const [ctxRes, plansRes] = await Promise.all([
                fetch(`/api/orchestration/context/${farmerId}?crop=${encodeURIComponent(currentFarmerCrop || 'wheat')}`),
                fetch(`/api/action-plans/${farmerId}`)
            ]);

            const ctxData = ctxRes.ok ? await ctxRes.json() : null;
            const plansData = plansRes.ok ? await plansRes.json() : null;

            renderLiveFarmContext(ctxData, plansData);
        } catch (err) {
            console.error("Failed to load live autonomous loop data:", err);
            renderUnavailableState();
        }
    }

    function renderAutonomousDecision(data, reqPayload, isDemo) {
        // Card 1: Crop Health
        const pathogenEl = document.getElementById("autoPathogenName");
        const sciEl = document.getElementById("autoScientificName");
        const confEl = document.getElementById("autoConfidenceVal");
        const rxEl = document.getElementById("autoPrescriptionLock");
        const qualEl = document.getElementById("autoSignalQuality");
        const healthPill = document.getElementById("healthStatusPill");
        const sourceEl = document.getElementById("healthSignalSource");

        const primaryDecision = (data.decisions && data.decisions.length > 0) ? data.decisions[0] : null;
        const overallResult = primaryDecision ? (primaryDecision.result || "").toUpperCase() : "ALLOWED";

        if (pathogenEl) pathogenEl.textContent = reqPayload.disease_name || "Wheat Stand";
        if (sciEl) sciEl.textContent = "Puccinia striiformis f. sp. tritici";
        if (confEl) confEl.textContent = `${reqPayload.confidence || 90}%`;
        if (sourceEl) sourceEl.textContent = isDemo ? "Source: Simulated Inference (Demo)" : "Source: EfficientNet-B0";

        const isLocked = (data.constraints || []).includes("PRESCRIPTION_LOCKED") || (reqPayload.confidence >= 30 && reqPayload.confidence < 65);
        if (rxEl) {
            rxEl.textContent = isLocked ? "🔒 LOCKED (Review Req.)" : "✓ UNLOCKED (Authorized)";
            rxEl.style.color = isLocked ? "#C2410C" : "#15803D";
        }
        if (qualEl) qualEl.textContent = isDemo ? "SIMULATED" : "VALID (High Trust)";

        if (healthPill) {
            if (overallResult === "ALLOWED") {
                healthPill.className = "status-pill pill-allowed";
                healthPill.textContent = "ALLOWED";
            } else if (overallResult === "DEFERRED") {
                healthPill.className = "status-pill pill-deferred";
                healthPill.textContent = "DEFERRED";
            } else if (overallResult === "REQUIRES_HUMAN_REVIEW") {
                healthPill.className = "status-pill pill-review";
                healthPill.textContent = "REVIEW REQ.";
            } else {
                healthPill.className = "status-pill pill-blocked";
                healthPill.textContent = "BLOCKED";
            }
        }

        // Card 2: "Why This Decision?"
        const bulletsList = document.getElementById("decisionBulletsList");
        const riskEl = document.getElementById("autoRiskLevel");
        const escEl = document.getElementById("autoEscalationStatus");
        const decPill = document.getElementById("decisionResultPill");

        if (riskEl) riskEl.textContent = (data.overall_risk || "moderate").toUpperCase();
        if (escEl) {
            escEl.textContent = data.escalation_required ? "🚨 Expert Escalation Active" : "✓ Not Required";
            escEl.style.color = data.escalation_required ? "#C2410C" : "#15803D";
        }

        if (decPill) {
            decPill.className = `status-pill pill-${overallResult.toLowerCase().replace(/_/g, '-')}`;
            decPill.textContent = overallResult;
        }

        if (bulletsList) {
            bulletsList.innerHTML = "";
            if (primaryDecision && primaryDecision.explanation) {
                const li = document.createElement("li");
                li.innerHTML = `<strong>Policy Finding:</strong> ${escapeHtml(primaryDecision.explanation)}`;
                bulletsList.appendChild(li);
            }
            if (data.constraints && data.constraints.length > 0) {
                const li = document.createElement("li");
                li.innerHTML = `<strong>Enforced Constraints:</strong> ${escapeHtml(data.constraints.join(", "))}`;
                bulletsList.appendChild(li);
            }
            if (data.recommended_actions && data.recommended_actions.length > 0) {
                const li = document.createElement("li");
                li.innerHTML = `<strong>Authorized Action:</strong> ${escapeHtml(data.recommended_actions[0])}`;
                bulletsList.appendChild(li);
            }
            if (bulletsList.children.length === 0) {
                bulletsList.innerHTML = "<li>Decision trace details currently unavailable.</li>";
            }
        }

        // Card 3: Weather Constraints
        const rainProbEl = document.getElementById("autoRainProbVal");
        const windEl = document.getElementById("autoWindVal");
        const weatherPill = document.getElementById("weatherConstraintPill");
        const sprayEl = document.getElementById("autoSprayAdvisory");
        const winEl = document.getElementById("weatherWindowVal");
        const condEl = document.getElementById("weatherConditionSummary");

        const rainP = reqPayload.rain_probability !== undefined ? reqPayload.rain_probability : 20;
        const windS = reqPayload.wind_speed !== undefined ? reqPayload.wind_speed : 8;

        if (rainProbEl) rainProbEl.textContent = `${rainP}%`;
        if (windEl) windEl.textContent = `${windS} km/h`;

        const isWeatherHold = rainP >= 60 || windS >= 25;
        if (weatherPill) {
            weatherPill.className = isWeatherHold ? "status-pill pill-hold" : "status-pill pill-safe";
            weatherPill.textContent = isWeatherHold ? "WEATHER HOLD" : "SAFE WINDOW";
        }
        if (winEl) winEl.textContent = isWeatherHold ? "Next dry window in 48-72h" : "Tomorrow Morning (6:00 - 9:00 AM)";
        if (condEl) condEl.textContent = isWeatherHold ? "High precipitation / wash-off risk" : "Optimal foliar spray conditions";
        if (sprayEl) {
            sprayEl.textContent = isWeatherHold ? "🚫 Delay foliar chemical application" : "✓ Suitable for precision application";
            sprayEl.style.color = isWeatherHold ? "#991B1B" : "#15803D";
        }

        // Card 4: Field Execution Task
        const taskTitleEl = document.getElementById("autoTaskTitle");
        const taskTimingEl = document.getElementById("autoTaskTiming");
        const taskPlanIdEl = document.getElementById("taskPlanId");
        const taskLifecyclePill = document.getElementById("taskLifecyclePill");
        const advanceBtn = document.getElementById("btnAdvanceTask");

        if (taskPlanIdEl) taskPlanIdEl.textContent = isDemo ? "Plan: #DEMO" : "Plan: #--";

        if (overallResult === "ALLOWED" && !isWeatherHold) {
            if (taskTitleEl) taskTitleEl.textContent = `Apply Propiconazole 25% EC for ${reqPayload.disease_name || 'Wheat'}`;
            if (taskTimingEl) taskTimingEl.textContent = "Target Window: Tomorrow 06:00 AM";
            if (taskLifecyclePill) {
                taskLifecyclePill.className = "status-pill pill-pending";
                taskLifecyclePill.textContent = "PENDING";
            }
            updateStepperUI("pending");
            if (advanceBtn) {
                advanceBtn.disabled = isDemo;
                advanceBtn.textContent = isDemo ? "🔒 Live Database Mode Required to Mutate" : "▶ Acknowledge Task";
            }
        } else if (isWeatherHold) {
            if (taskTitleEl) taskTitleEl.textContent = `Rescheduled: Delay treatment until rain clears`;
            if (taskTimingEl) taskTimingEl.textContent = "Next Window: Post-Rain (48-72h)";
            if (taskLifecyclePill) {
                taskLifecyclePill.className = "status-pill pill-deferred";
                taskLifecyclePill.textContent = "WEATHER HOLD";
            }
            updateStepperUI("pending");
            if (advanceBtn) {
                advanceBtn.disabled = true;
                advanceBtn.textContent = "🌧️ Execution Held for Weather";
            }
        } else {
            if (taskTitleEl) taskTitleEl.textContent = "0 Executable Tasks (Human Verification Required)";
            if (taskTimingEl) taskTimingEl.textContent = "Awaiting ICAR certified agronomist inspection";
            if (taskLifecyclePill) {
                taskLifecyclePill.className = "status-pill pill-review";
                taskLifecyclePill.textContent = "LOCKED";
            }
            updateStepperUI(null);
            if (advanceBtn) {
                advanceBtn.disabled = true;
                advanceBtn.textContent = "🔒 Prescription Locked";
            }
        }
    }

    function renderLiveFarmContext(ctxData, plansData) {
        const ctx = (ctxData && ctxData.context) ? ctxData.context : null;
        const plans = (plansData && plansData.action_plans) ? plansData.action_plans : [];
        const latestPlan = plans.length > 0 ? plans[0] : null;

        // Card 1: Crop Health
        const pathogenEl = document.getElementById("autoPathogenName");
        const sciEl = document.getElementById("autoScientificName");
        const confEl = document.getElementById("autoConfidenceVal");
        const rxEl = document.getElementById("autoPrescriptionLock");
        const qualEl = document.getElementById("autoSignalQuality");
        const healthPill = document.getElementById("healthStatusPill");
        const sourceEl = document.getElementById("healthSignalSource");

        if (ctx && ctx.disease) {
            const d = ctx.disease;
            const pName = (d.pathogen_name && d.pathogen_name.value) ? d.pathogen_name.value : "Healthy Stand";
            const sName = (d.scientific_name && d.scientific_name.value) ? d.scientific_name.value : "None";
            const conf = (d.confidence_percent && d.confidence_percent.value !== null) ? d.confidence_percent.value : 96.5;
            const src = (d.confidence_percent && d.confidence_percent.source) ? d.confidence_percent.source : "EfficientNet-B0";
            const qual = (d.confidence_percent && d.confidence_percent.quality) ? d.confidence_percent.quality : "VALID";

            if (pathogenEl) pathogenEl.textContent = pName;
            if (sciEl) sciEl.textContent = sName;
            if (confEl) confEl.textContent = `${Math.round(conf * 10) / 10}%`;
            if (sourceEl) sourceEl.textContent = `Source: ${src}`;
            if (qualEl) qualEl.textContent = `${qual} (Trust Gate)`;

            const isLocked = d.prescription_locked || (conf >= 30.0 && conf < 65.0);
            if (rxEl) {
                rxEl.textContent = isLocked ? "🔒 LOCKED (Review Req.)" : "✓ UNLOCKED (Authorized)";
                rxEl.style.color = isLocked ? "#C2410C" : "#15803D";
            }

            if (healthPill) {
                if (isLocked) {
                    healthPill.className = "status-pill pill-review";
                    healthPill.textContent = "REVIEW REQ.";
                } else if (!d.has_diagnosis || pName.toLowerCase().includes("healthy")) {
                    healthPill.className = "status-pill pill-allowed";
                    healthPill.textContent = "HEALTHY";
                } else {
                    healthPill.className = "status-pill pill-allowed";
                    healthPill.textContent = "DIAGNOSED";
                }
            }
        } else {
            if (pathogenEl) pathogenEl.textContent = "Live Stand Scouting";
            if (confEl) confEl.textContent = "95.0%";
            if (rxEl) rxEl.textContent = "✓ UNLOCKED";
            if (healthPill) {
                healthPill.className = "status-pill pill-allowed";
                healthPill.textContent = "ACTIVE";
            }
        }

        // Card 2: "Why This Decision?"
        const bulletsList = document.getElementById("decisionBulletsList");
        const riskEl = document.getElementById("autoRiskLevel");
        const escEl = document.getElementById("autoEscalationStatus");
        const decPill = document.getElementById("decisionResultPill");

        if (latestPlan) {
            currentActivePlanId = latestPlan.id;
            if (riskEl) riskEl.textContent = (latestPlan.risk_level || latestPlan.risk_type || "moderate").toUpperCase();
            if (escEl) {
                escEl.textContent = latestPlan.escalation_required ? "🚨 Field Agent Escalated" : "✓ Autonomous Execution";
                escEl.style.color = latestPlan.escalation_required ? "#C2410C" : "#15803D";
            }

            const planStatus = (latestPlan.status || "active").toUpperCase();
            if (decPill) {
                if (planStatus.includes("DEFERRED")) {
                    decPill.className = "status-pill pill-deferred";
                    decPill.textContent = "DEFERRED";
                } else if (planStatus.includes("REVIEW") || planStatus.includes("ESCALAT")) {
                    decPill.className = "status-pill pill-review";
                    decPill.textContent = "REQUIRES REVIEW";
                } else if (planStatus.includes("COMPLETED")) {
                    decPill.className = "status-pill pill-safe";
                    decPill.textContent = "COMPLETED";
                } else {
                    decPill.className = "status-pill pill-allowed";
                    decPill.textContent = "ALLOWED";
                }
            }

            if (bulletsList) {
                bulletsList.innerHTML = "";
                const tasks = latestPlan.tasks || [];
                const activeT = tasks.length > 0 ? tasks[tasks.length - 1] : null;

                if (activeT && activeT.reasoning) {
                    const li = document.createElement("li");
                    li.innerHTML = `<strong>Autonomous Reasoning:</strong> ${escapeHtml(activeT.reasoning)}`;
                    bulletsList.appendChild(li);
                }
                if (latestPlan.constraints && latestPlan.constraints.length > 0) {
                    const li = document.createElement("li");
                    li.innerHTML = `<strong>Enforced Constraints:</strong> ${escapeHtml(latestPlan.constraints.join(", "))}`;
                    bulletsList.appendChild(li);
                }
                if (latestPlan.recommended_actions && latestPlan.recommended_actions.length > 0) {
                    const li = document.createElement("li");
                    li.innerHTML = `<strong>Recommended Protocol:</strong> ${escapeHtml(latestPlan.recommended_actions[0])}`;
                    bulletsList.appendChild(li);
                }
                if (bulletsList.children.length === 0) {
                    bulletsList.innerHTML = `
                        <li>Autonomous plan #${latestPlan.id} active for ${escapeHtml(latestPlan.crop_id || 'Wheat')}.</li>
                        <li>Policy evaluated: MultiSignalPolicyEngine (Deterministic).</li>
                    `;
                }
            }
        } else {
            if (bulletsList) {
                bulletsList.innerHTML = "<li>No active action plan found. Scan a leaf or initialize monitoring.</li>";
            }
            if (decPill) {
                decPill.className = "status-pill pill-pending";
                decPill.textContent = "READY";
            }
        }

        // Card 3: Weather Constraints
        const rainProbEl = document.getElementById("autoRainProbVal");
        const windEl = document.getElementById("autoWindVal");
        const weatherPill = document.getElementById("weatherConstraintPill");
        const sprayEl = document.getElementById("autoSprayAdvisory");
        const winEl = document.getElementById("weatherWindowVal");
        const condEl = document.getElementById("weatherConditionSummary");

        if (ctx && ctx.weather) {
            const w = ctx.weather;
            const rProb = (w.rain_probability_percent && w.rain_probability_percent.value !== null) ? w.rain_probability_percent.value : 10;
            const wSpeed = (w.wind_speed_kmh && w.wind_speed_kmh.value !== null) ? w.wind_speed_kmh.value : 6.5;
            const favWin = (w.favorable_window && w.favorable_window.value) ? w.favorable_window.value : "Tomorrow Morning (6:00 - 9:00 AM)";
            const riskCat = (w.risk_category && w.risk_category.value) ? w.risk_category.value : "low";

            if (rainProbEl) rainProbEl.textContent = `${rProb}%`;
            if (windEl) windEl.textContent = `${wSpeed} km/h`;

            const isHold = rProb >= 60 || wSpeed >= 25 || riskCat === "high";
            if (weatherPill) {
                weatherPill.className = isHold ? "status-pill pill-hold" : "status-pill pill-safe";
                weatherPill.textContent = isHold ? "WEATHER HOLD" : "SAFE WINDOW";
            }
            if (winEl) winEl.textContent = favWin;
            if (condEl) condEl.textContent = isHold ? "High wash-off or drift risk" : "Clear and favorable atmospheric conditions";
            if (sprayEl) {
                sprayEl.textContent = isHold ? "🚫 Delay foliar chemical application" : "✓ Safe for precision application";
                sprayEl.style.color = isHold ? "#991B1B" : "#15803D";
            }
        }

        // Card 4: Field Execution Task
        const taskTitleEl = document.getElementById("autoTaskTitle");
        const taskTimingEl = document.getElementById("autoTaskTiming");
        const taskPlanIdEl = document.getElementById("taskPlanId");
        const taskLifecyclePill = document.getElementById("taskLifecyclePill");
        const advanceBtn = document.getElementById("btnAdvanceTask");

        if (latestPlan && latestPlan.tasks && latestPlan.tasks.length > 0) {
            const activeTask = latestPlan.tasks[latestPlan.tasks.length - 1];
            currentActiveTaskId = activeTask.id;
            currentActiveTaskStatus = (activeTask.status || "pending").toLowerCase();

            if (taskPlanIdEl) taskPlanIdEl.textContent = `Plan: #${latestPlan.id}`;
            if (taskTitleEl) taskTitleEl.textContent = activeTask.title || "Treatment Task";
            if (taskTimingEl) {
                const sched = activeTask.scheduled_for ? new Date(activeTask.scheduled_for).toLocaleString() : (activeTask.execution_window || "Immediate");
                taskTimingEl.textContent = `Scheduled: ${sched}`;
            }

            if (taskLifecyclePill) {
                taskLifecyclePill.className = `status-pill pill-${currentActiveTaskStatus === 'done' || currentActiveTaskStatus === 'completed' ? 'safe' : 'pending'}`;
                taskLifecyclePill.textContent = currentActiveTaskStatus.toUpperCase();
            }

            updateStepperUI(currentActiveTaskStatus);

            if (advanceBtn) {
                if (currentActiveTaskStatus === "pending") {
                    advanceBtn.disabled = false;
                    advanceBtn.textContent = "▶ Acknowledge Task";
                } else if (currentActiveTaskStatus === "acknowledged") {
                    advanceBtn.disabled = false;
                    advanceBtn.textContent = "🚜 Begin Field Work";
                } else if (currentActiveTaskStatus === "in_progress") {
                    advanceBtn.disabled = false;
                    advanceBtn.textContent = "✓ Mark Completed & Re-check Weather";
                } else {
                    advanceBtn.disabled = true;
                    advanceBtn.textContent = "✓ Task Completed & Verified";
                }
            }
        } else {
            currentActiveTaskId = null;
            if (taskTitleEl) taskTitleEl.textContent = "No pending execution task";
            if (taskTimingEl) taskTimingEl.textContent = "Upload a crop photo to generate plan";
            updateStepperUI(null);
            if (advanceBtn) {
                advanceBtn.disabled = true;
                advanceBtn.textContent = "🔒 No Action Available";
            }
        }
    }

    function updateStepperUI(status) {
        const st = (status || "").toLowerCase();
        const steps = ["pending", "acknowledged", "in_progress", "completed"];
        const stepIdx = st === "done" ? 3 : steps.indexOf(st);

        steps.forEach((name, idx) => {
            const el = document.getElementById(`step-${name}`);
            if (!el) return;
            el.className = "stepper-step";
            if (stepIdx !== -1) {
                if (idx < stepIdx) {
                    el.classList.add("completed");
                } else if (idx === stepIdx) {
                    el.classList.add("active");
                }
            }
        });
    }

    async function advanceActiveTaskLifecycle() {
        if (!currentActiveTaskId) return;

        const advanceBtn = document.getElementById("btnAdvanceTask");
        let nextStatus = "acknowledged";
        if (currentActiveTaskStatus === "pending") {
            nextStatus = "ACKNOWLEDGED";
        } else if (currentActiveTaskStatus === "acknowledged") {
            nextStatus = "IN_PROGRESS";
        } else if (currentActiveTaskStatus === "in_progress") {
            nextStatus = "COMPLETED";
        } else {
            return;
        }

        try {
            if (advanceBtn) {
                advanceBtn.disabled = true;
                advanceBtn.textContent = "Updating task on server...";
            }

            const res = await fetch(`/api/orchestration/tasks/${currentActiveTaskId}/status`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status: nextStatus })
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Task update failed");

            // Refresh autonomous loop and action plans
            await loadAutonomousLoopData("LIVE");
            await loadFieldActionPlans();
            await loadFarmerNotifications();
        } catch (err) {
            console.error("Failed to advance task lifecycle:", err);
            alert(`⚠️ Task transition failed: ${err.message}`);
        } finally {
            if (advanceBtn) advanceBtn.disabled = false;
        }
    }

    function renderUnavailableState() {
        const pathogenEl = document.getElementById("autoPathogenName");
        const bulletsList = document.getElementById("decisionBulletsList");
        const winEl = document.getElementById("weatherWindowVal");
        const taskTitleEl = document.getElementById("autoTaskTitle");

        if (pathogenEl) pathogenEl.textContent = "Data unavailable";
        if (bulletsList) bulletsList.innerHTML = "<li>Decision details currently unavailable from server.</li>";
        if (winEl) winEl.textContent = "Data unavailable";
        if (taskTitleEl) taskTitleEl.textContent = "Data unavailable";
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

})();


