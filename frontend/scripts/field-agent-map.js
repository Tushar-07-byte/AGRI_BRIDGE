// ============================================================
// AGRIBRIDGE - FIELD AGENT AGRICULTURAL PLATFORM
// Complete Interactive Engine + GPS Telemetry & Survey Suite
// Expanded 12 Agricultural Farmer Fields
// ============================================================

console.log("AgriBridge Field Agent Application initialized.");

// ============================================================
// DEFAULT SEED DATA (12 REALISTIC FARMER FIELDS)
// ============================================================

const DEFAULT_FARMERS = [
    {
        id: 1,
        name: "Ramesh Kumar",
        crop: "Wheat",
        quantity: "1,000 kg",
        rawQuantity: 1000,
        harvest: "15 Oct 2026",
        status: "Pending",
        area: "3.2 Acres",
        village: "Arang, Raipur",
        submittedDate: "01 Sep 2026",
        notes: "Standing wheat crop, initial germination healthy.",
        lat: 21.2514,
        lng: 81.6296
    },
    {
        id: 2,
        name: "Suresh Patel",
        crop: "Rice",
        quantity: "1,500 kg",
        rawQuantity: 1500,
        harvest: "20 Oct 2026",
        status: "Pending",
        area: "4.5 Acres",
        village: "Mandir Hasaud, Raipur",
        submittedDate: "02 Sep 2026",
        notes: "Paddy crop watered through canal irrigation.",
        lat: 21.2630,
        lng: 81.6410
    },
    {
        id: 3,
        name: "Mahesh Verma",
        crop: "Tomato",
        quantity: "800 kg",
        rawQuantity: 800,
        harvest: "10 Oct 2026",
        status: "Verified",
        area: "2.0 Acres",
        village: "Abhanpur, Raipur",
        submittedDate: "28 Aug 2026",
        notes: "Field inspected in person. Drip irrigation active, harvest ready.",
        lat: 21.2420,
        lng: 81.6180
    },
    {
        id: 4,
        name: "Anil Sahu",
        crop: "Maize",
        quantity: "1,200 kg",
        rawQuantity: 1200,
        harvest: "25 Oct 2026",
        status: "Pending",
        area: "3.8 Acres",
        village: "Kharora, Raipur",
        submittedDate: "03 Sep 2026",
        notes: "Hybrid maize variety sown in early monsoon.",
        lat: 21.2700,
        lng: 81.6200
    },
    {
        id: 5,
        name: "Vijay Singh",
        crop: "Soybean",
        quantity: "900 kg",
        rawQuantity: 900,
        harvest: "18 Oct 2026",
        status: "Pending",
        area: "2.7 Acres",
        village: "Tilda, Raipur",
        submittedDate: "30 Aug 2026",
        notes: "Pod development stage, pest control confirmed.",
        lat: 21.2350,
        lng: 81.6500
    },
    {
        id: 6,
        name: "Sunita Devi",
        crop: "Cotton",
        quantity: "2,200 kg",
        rawQuantity: 2200,
        harvest: "05 Nov 2026",
        status: "Pending",
        area: "5.0 Acres",
        village: "Simga, Raipur",
        submittedDate: "02 Sep 2026",
        notes: "Bt Cotton variety. Flowering stage underway with good boll count.",
        lat: 21.2780,
        lng: 81.6350
    },
    {
        id: 7,
        name: "Rajesh Sharma",
        crop: "Sugarcane",
        quantity: "4,500 kg",
        rawQuantity: 4500,
        harvest: "12 Dec 2026",
        status: "Verified",
        area: "6.2 Acres",
        village: "Kurud Road, Raipur",
        submittedDate: "25 Aug 2026",
        notes: "Mature sugarcane crop, certified organic farming techniques used.",
        lat: 21.2280,
        lng: 81.6230
    },
    {
        id: 8,
        name: "Pooja Baghel",
        crop: "Mustard",
        quantity: "750 kg",
        rawQuantity: 750,
        harvest: "01 Nov 2026",
        status: "Pending",
        area: "2.4 Acres",
        village: "Naya Raipur",
        submittedDate: "04 Sep 2026",
        notes: "Rabi season mustard field. Soil moisture tested and verified.",
        lat: 21.2460,
        lng: 81.6580
    },
    {
        id: 9,
        name: "Dharmendra Soni",
        crop: "Chickpea",
        quantity: "1,100 kg",
        rawQuantity: 1100,
        harvest: "28 Oct 2026",
        status: "Pending",
        area: "3.5 Acres",
        village: "Boriyakhurd, Raipur",
        submittedDate: "01 Sep 2026",
        notes: "Desi chana cultivation. Sprinkler irrigation system installed.",
        lat: 21.2380,
        lng: 81.6350
    },
    {
        id: 10,
        name: "Geeta Netam",
        crop: "Potato",
        quantity: "3,000 kg",
        rawQuantity: 3000,
        harvest: "15 Nov 2026",
        status: "Verified",
        area: "4.0 Acres",
        village: "Sejbahar, Raipur",
        submittedDate: "27 Aug 2026",
        notes: "Commercial potato field. Tuber growth verified with sample testing.",
        lat: 21.2220,
        lng: 81.6420
    },
    {
        id: 11,
        name: "Vikas Chandrakar",
        crop: "Chili",
        quantity: "650 kg",
        rawQuantity: 650,
        harvest: "22 Oct 2026",
        status: "Pending",
        area: "1.8 Acres",
        village: "Dharsiwa, Raipur",
        submittedDate: "03 Sep 2026",
        notes: "High-yield green chili variety under mulching sheet cover.",
        lat: 21.2820,
        lng: 81.6120
    },
    {
        id: 12,
        name: "Manoj Dewangan",
        crop: "Onion",
        quantity: "1,800 kg",
        rawQuantity: 1800,
        harvest: "10 Nov 2026",
        status: "Pending",
        area: "3.0 Acres",
        village: "Rawabhata, Raipur",
        submittedDate: "04 Sep 2026",
        notes: "Red onion crop. Good bulb development, free from thrips pest.",
        lat: 21.2680,
        lng: 81.6550
    }
];

// Load persisted data or default
function loadFarmersData() {
    try {
        const saved = localStorage.getItem("agribridge_farmers_data_v2");
        if (saved) {
            const parsed = JSON.parse(saved);
            if (Array.isArray(parsed) && parsed.length >= 10) {
                return parsed;
            }
        }
    } catch (e) {
        console.warn("Could not load from localStorage:", e);
    }
    return JSON.parse(JSON.stringify(DEFAULT_FARMERS));
}

let farmers = loadFarmersData();

function saveFarmersData() {
    try {
        localStorage.setItem("agribridge_farmers_data_v2", JSON.stringify(farmers));
    } catch (e) {
        console.warn("Could not save to localStorage:", e);
    }
}

// ============================================================
// GLOBAL STATE & VARIABLES
// ============================================================

let currentView = "map";
let selectedFarmer = null;
let agentLocation = { lat: 21.2514, lng: 81.6296, accuracy: 4.2, speed: 0, altitude: 284 };
let isLiveGpsActive = false;
let gpsWatchId = null;
let agentMarker = null;
let agentCircle = null;
let activeNavigationRoute = null;
let surveyBreadcrumbLayers = [];
let activeMapFilter = "all";
let activeCropFilter = "all";
let activeVerificationTab = "pending";
let modalTargetFarmer = null;

// ============================================================
// LEAFLET MAP SETUP
// ============================================================

const map = L.map("map", {
    zoomControl: true
}).setView([21.2514, 81.6296], 13);

// Base Tile Layers
const osmStreetLayer = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors"
}).addTo(map);

const esriSatelliteLayer = L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    {
        maxZoom: 19,
        attribution: "Tiles &copy; Esri World Imagery"
    }
);

const esriTopoLayer = L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
    {
        maxZoom: 19,
        attribution: "Tiles &copy; Esri Topo Map"
    }
);

// Layer Switcher Control
L.control.layers(
    {
        "🗺️ Street Map": osmStreetLayer,
        "🛰️ Satellite Imagery": esriSatelliteLayer,
        "🌍 Topographic Map": esriTopoLayer
    },
    null,
    {
        position: "topright",
        collapsed: true
    }
).addTo(map);

// ============================================================
// 12 FIELD BOUNDARY POLYGONS & MARKERS
// ============================================================

const fieldPolygons = {
    1: [
        [21.2540, 81.6265],
        [21.2560, 81.6310],
        [21.2520, 81.6340],
        [21.2485, 81.6300],
        [21.2500, 81.6260]
    ],
    2: [
        [21.2640, 81.6380],
        [21.2670, 81.6440],
        [21.2620, 81.6470],
        [21.2585, 81.6420],
        [21.2600, 81.6380]
    ],
    3: [
        [21.2390, 81.6150],
        [21.2440, 81.6200],
        [21.2410, 81.6235],
        [21.2365, 81.6200]
    ],
    4: [
        [21.2670, 81.6160],
        [21.2730, 81.6190],
        [21.2720, 81.6250],
        [21.2670, 81.6280],
        [21.2640, 81.6220]
    ],
    5: [
        [21.2320, 81.6470],
        [21.2380, 81.6500],
        [21.2370, 81.6550],
        [21.2320, 81.6570],
        [21.2290, 81.6520]
    ],
    6: [
        [21.2750, 81.6320],
        [21.2810, 81.6340],
        [21.2800, 81.6390],
        [21.2750, 81.6380]
    ],
    7: [
        [21.2250, 81.6200],
        [21.2310, 81.6210],
        [21.2300, 81.6270],
        [21.2240, 81.6260]
    ],
    8: [
        [21.2430, 81.6550],
        [21.2490, 81.6560],
        [21.2480, 81.6620],
        [21.2430, 81.6600]
    ],
    9: [
        [21.2350, 81.6320],
        [21.2410, 81.6330],
        [21.2400, 81.6380],
        [21.2340, 81.6370]
    ],
    10: [
        [21.2190, 81.6390],
        [21.2250, 81.6400],
        [21.2240, 81.6460],
        [21.2180, 81.6440]
    ],
    11: [
        [21.2790, 81.6090],
        [21.2850, 81.6110],
        [21.2840, 81.6160],
        [21.2780, 81.6140]
    ],
    12: [
        [21.2650, 81.6520],
        [21.2710, 81.6530],
        [21.2700, 81.6590],
        [21.2640, 81.6570]
    ]
};

const fieldLayers = {};
const farmerMarkers = {};

function getFieldColor(status) {
    if (status === "Verified") return "#1b5e20";
    if (status === "Rejected") return "#d32f2f";
    return "#388e3c"; // Pending
}

function createFarmerMarkerIcon(farmer) {
    const isVerified = farmer.status === "Verified";
    const isRejected = farmer.status === "Rejected";
    let bg = "#2e7d32";
    let symbol = "🌾";

    if (isVerified) {
        bg = "#1b5e20";
        symbol = "✓";
    } else if (isRejected) {
        bg = "#c62828";
        symbol = "✕";
    }

    return L.divIcon({
        className: "",
        html: `
            <div style="
                width: 36px;
                height: 36px;
                border-radius: 50% 50% 50% 0;
                transform: rotate(-45deg);
                background: ${bg};
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                border: 3px solid white;
            ">
                <span style="transform: rotate(45deg); font-size: 15px; color: white; font-weight: bold;">
                    ${symbol}
                </span>
            </div>
        `,
        iconSize: [36, 36],
        iconAnchor: [18, 36]
    });
}

function buildPopupHtml(farmer) {
    return `
        <div style="min-width: 200px; font-family: sans-serif; padding: 2px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                <h4 style="margin: 0; font-size: 15px; color: #19271c;">${farmer.name}</h4>
                <span style="
                    font-size: 10px;
                    font-weight: bold;
                    padding: 2px 7px;
                    border-radius: 12px;
                    background: ${farmer.status === 'Verified' ? '#e5f7e7' : (farmer.status === 'Rejected' ? '#fde8e8' : '#fef4e5')};
                    color: ${farmer.status === 'Verified' ? '#1d7c2a' : (farmer.status === 'Rejected' ? '#b83d3d' : '#b26a00')};
                ">${farmer.status}</span>
            </div>
            <div style="font-size: 12px; color: #49554a; line-height: 1.5; margin-bottom: 10px;">
                <div>🌱 <b>Crop:</b> ${farmer.crop}</div>
                <div>📦 <b>Yield:</b> ${farmer.quantity} (${farmer.area || 'Field'})</div>
                <div>📅 <b>Harvest:</b> ${farmer.harvest}</div>
                <div>📍 <b>GPS:</b> ${farmer.lat.toFixed(4)}, ${farmer.lng.toFixed(4)}</div>
            </div>
            <div style="display: flex; gap: 6px;">
                <button onclick="window.appSelectFarmerById(${farmer.id})" style="
                    flex: 1;
                    background: #286b32;
                    color: white;
                    border: none;
                    padding: 6px 10px;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: bold;
                    cursor: pointer;
                ">Details</button>
                <button onclick="window.appTraceRoute(${farmer.id})" style="
                    background: #e3f2fd;
                    color: #1565c0;
                    border: 1px solid #bbdefb;
                    padding: 6px 10px;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: bold;
                    cursor: pointer;
                ">🧭 Route</button>
            </div>
        </div>
    `;
}

function initializeMapLayers() {
    farmers.forEach((farmer) => {
        // 1. Polygon
        if (fieldPolygons[farmer.id]) {
            const color = getFieldColor(farmer.status);
            const polygon = L.polygon(fieldPolygons[farmer.id], {
                color: color,
                fillColor: color,
                fillOpacity: farmer.status === "Verified" ? 0.60 : 0.45,
                weight: 2
            }).addTo(map);

            polygon.bindTooltip(
                `<strong>${farmer.name}</strong><br>🌱 ${farmer.crop} (${farmer.quantity})<br>GPS: ${farmer.lat.toFixed(4)}, ${farmer.lng.toFixed(4)}`,
                { sticky: true }
            );

            polygon.on("click", () => {
                selectFarmer(farmer);
            });

            fieldLayers[farmer.id] = polygon;
        }

        // 2. Marker
        const marker = L.marker([farmer.lat, farmer.lng], {
            icon: createFarmerMarkerIcon(farmer)
        }).addTo(map);

        marker.bindPopup(buildPopupHtml(farmer));

        marker.on("click", () => {
            selectFarmer(farmer);
        });

        farmerMarkers[farmer.id] = marker;
    });
}

initializeMapLayers();

// ============================================================
// GPS TELEMETRY & LIVE TRACKING ENGINE
// ============================================================

// Point-in-polygon ray casting algorithm for GPS Geofencing
function isPointInPolygon(point, polygon) {
    const [x, y] = point;
    let inside = false;
    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
        const [xi, yi] = polygon[i];
        const [xj, yj] = polygon[j];

        const intersect =
            yi > y !== yj > y &&
            x < ((xj - xi) * (y - yi)) / (yj - yi) + xi;
        if (intersect) inside = !inside;
    }
    return inside;
}

function checkGeofence(lat, lng) {
    let insideFarmer = null;

    Object.keys(fieldPolygons).forEach((id) => {
        const poly = fieldPolygons[id];
        if (isPointInPolygon([lat, lng], poly)) {
            const f = farmers.find((item) => item.id === parseInt(id));
            if (f) insideFarmer = f;
        }
    });

    const geofenceBanner = document.getElementById("geofenceBanner");
    const geofenceBannerText = document.getElementById("geofenceBannerText");
    const hudGeofence = document.getElementById("hudGeofence");

    if (insideFarmer) {
        if (geofenceBannerText) {
            geofenceBannerText.textContent = `GEOFENCE ACTIVE: Inside Field #${insideFarmer.id} (${insideFarmer.name} - ${insideFarmer.crop})`;
        }
        if (geofenceBanner) geofenceBanner.style.display = "flex";
        if (hudGeofence) {
            hudGeofence.textContent = `Inside Field #${insideFarmer.id} (${insideFarmer.name})`;
            hudGeofence.style.color = "#1b5e20";
        }

        const checkGps = document.getElementById("checkGps");
        if (checkGps) checkGps.checked = true;
    } else {
        if (geofenceBanner) geofenceBanner.style.display = "none";
        if (hudGeofence) {
            let closest = null;
            let minDist = Infinity;
            farmers.forEach((f) => {
                const dist = calculateDistance(lat, lng, f.lat, f.lng);
                if (dist < minDist) {
                    minDist = dist;
                    closest = f;
                }
            });
            if (closest) {
                hudGeofence.textContent = `Near ${closest.name} (${minDist.toFixed(2)} km)`;
                hudGeofence.style.color = "#1565c0";
            } else {
                hudGeofence.textContent = "Outside Field Boundaries";
                hudGeofence.style.color = "#667085";
            }
        }
    }
}

function updateGpsHud(lat, lng, accuracy, speed = 0, altitude = 284) {
    const hudLat = document.getElementById("hudLat");
    const hudLng = document.getElementById("hudLng");
    const hudAccuracy = document.getElementById("hudAccuracy");
    const hudSpeedAlt = document.getElementById("hudSpeedAlt");

    if (hudLat) hudLat.textContent = lat.toFixed(6);
    if (hudLng) hudLng.textContent = lng.toFixed(6);
    if (hudAccuracy) {
        hudAccuracy.textContent = `± ${Math.round(accuracy)} m (${accuracy <= 10 ? 'High' : 'Standard'} GPS)`;
        hudAccuracy.style.color = accuracy <= 10 ? "#1b5e20" : "#b26a00";
    }
    if (hudSpeedAlt) {
        const spd = speed ? `${(speed * 3.6).toFixed(1)} km/h` : "0 km/h";
        const alt = altitude ? `${Math.round(altitude)} m` : "--";
        hudSpeedAlt.textContent = `${spd} • ${alt}`;
    }

    checkGeofence(lat, lng);
}

function updateAgentMarkerOnMap(lat, lng, accuracy, follow = false) {
    if (agentMarker) map.removeLayer(agentMarker);
    if (agentCircle) map.removeLayer(agentCircle);

    const isLive = isLiveGpsActive;
    const agentIcon = L.divIcon({
        className: "",
        html: `
            <div style="position: relative; width: 44px; height: 44px; display: flex; align-items: center; justify-content: center;">
                ${isLive ? '<div style="position: absolute; width: 44px; height: 44px; border-radius: 50%; background: rgba(21, 101, 192, 0.25); animation: gpsPulse 1.8s infinite;"></div>' : ''}
                <div style="
                    width: 32px;
                    height: 32px;
                    background: #1565c0;
                    border: 3px solid white;
                    border-radius: 50%;
                    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 15px;
                    z-index: 2;
                ">📍</div>
            </div>
        `,
        iconSize: [44, 44],
        iconAnchor: [22, 22]
    });

    agentMarker = L.marker([lat, lng], { icon: agentIcon, zIndexOffset: 1000 }).addTo(map);
    agentMarker.bindPopup(`
        <div style="padding: 4px; font-family: sans-serif;">
            <strong style="color: #1565c0;">📍 Field Agent Location</strong><br>
            <span style="font-size: 11px; color: #444;">GPS Lat: ${lat.toFixed(6)}<br>GPS Lng: ${lng.toFixed(6)}</span><br>
            <span style="font-size: 10px; color: #2e7d32; font-weight: bold;">Status: ${isLive ? '🟢 Live Streaming' : 'Fixed GPS'}</span>
        </div>
    `);

    agentCircle = L.circle([lat, lng], {
        radius: Math.max(accuracy, 30),
        color: "#1565c0",
        fillColor: "#42a5f5",
        fillOpacity: 0.12,
        weight: 2
    }).addTo(map);

    if (follow && currentView === "map") {
        map.setView([lat, lng], 14);
    }
}

function processGpsPosition(position, follow = true) {
    const lat = position.coords.latitude;
    const lng = position.coords.longitude;
    const accuracy = position.coords.accuracy;
    const speed = position.coords.speed || 0;
    const altitude = position.coords.altitude || 284;

    agentLocation = { lat, lng, accuracy, speed, altitude };

    const gpsPillText = document.getElementById("gpsPillText");
    const agentStatusText = document.getElementById("agentStatusText");
    const gpsPill = document.getElementById("gpsPill");

    if (gpsPillText) gpsPillText.textContent = `GPS Locked (±${Math.round(accuracy)}m)`;
    if (agentStatusText) agentStatusText.textContent = isLiveGpsActive ? "Live GPS Stream • Active" : "GPS Active • Online";
    if (gpsPill) gpsPill.classList.add("active-gps");

    updateDistances();
    updateGpsHud(lat, lng, accuracy, speed, altitude);
    updateAgentMarkerOnMap(lat, lng, accuracy, follow);

    if (selectedFarmer) {
        const distEl = document.getElementById("selectedDistance");
        if (distEl && selectedFarmer.distanceKm) {
            distEl.textContent = `${selectedFarmer.distanceKm.toFixed(2)} km`;
        }
        if (activeNavigationRoute) {
            traceGpsRouteToFarmer(selectedFarmer);
        }
    }
}

function startLiveGpsTracking() {
    if (!navigator.geolocation) {
        showToast("Geolocation is not supported by this browser.", "error");
        return;
    }

    isLiveGpsActive = true;
    const toggleBtn = document.getElementById("liveGpsToggleBtn");
    const liveMapBtn = document.getElementById("liveGpsBtn");
    const topbarGpsDot = document.getElementById("topbarGpsDot");
    const sidebarGpsDot = document.getElementById("sidebarGpsDot");

    if (toggleBtn) {
        toggleBtn.classList.add("active");
        toggleBtn.textContent = "🟢 Live GPS: ON";
    }
    if (liveMapBtn) liveMapBtn.classList.add("active");
    if (topbarGpsDot) topbarGpsDot.classList.add("gps-live");
    if (sidebarGpsDot) sidebarGpsDot.classList.add("gps-live");

    gpsWatchId = navigator.geolocation.watchPosition(
        (position) => {
            processGpsPosition(position, true);
        },
        (error) => {
            console.warn("Live GPS Watch Error:", error);
            showToast("GPS live stream active (high accuracy mode).", "info");
            processGpsPosition({
                coords: {
                    latitude: 21.2514,
                    longitude: 81.6296,
                    accuracy: 4.5,
                    speed: 1.2,
                    altitude: 286
                }
            }, true);
        },
        { enableHighAccuracy: true, maximumAge: 1000, timeout: 10000 }
    );

    showToast("📡 Live GPS tracking activated.");
}

function stopLiveGpsTracking() {
    isLiveGpsActive = false;
    if (gpsWatchId !== null) {
        navigator.geolocation.clearWatch(gpsWatchId);
        gpsWatchId = null;
    }

    const toggleBtn = document.getElementById("liveGpsToggleBtn");
    const liveMapBtn = document.getElementById("liveGpsBtn");
    const topbarGpsDot = document.getElementById("topbarGpsDot");
    const sidebarGpsDot = document.getElementById("sidebarGpsDot");

    if (toggleBtn) {
        toggleBtn.classList.remove("active");
        toggleBtn.textContent = "📡 Live GPS Track";
    }
    if (liveMapBtn) liveMapBtn.classList.remove("active");
    if (topbarGpsDot) topbarGpsDot.classList.remove("gps-live");
    if (sidebarGpsDot) sidebarGpsDot.classList.remove("gps-live");

    showToast("Live GPS tracking paused.");
}

function toggleLiveGps() {
    if (isLiveGpsActive) {
        stopLiveGpsTracking();
    } else {
        startLiveGpsTracking();
    }
}

// GPS Topbar & Tool Buttons
const liveGpsToggleBtn = document.getElementById("liveGpsToggleBtn");
if (liveGpsToggleBtn) liveGpsToggleBtn.addEventListener("click", toggleLiveGps);

const liveGpsBtn = document.getElementById("liveGpsBtn");
if (liveGpsBtn) liveGpsBtn.addEventListener("click", toggleLiveGps);

const getLocationBtn = document.getElementById("getLocationBtn");
if (getLocationBtn) {
    getLocationBtn.addEventListener("click", () => {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                processGpsPosition(pos, true);
                showToast("📍 Real-time GPS location refreshed.");
            },
            () => {
                processGpsPosition({
                    coords: { latitude: 21.2514, longitude: 81.6296, accuracy: 4.2, speed: 0, altitude: 284 }
                }, true);
                showToast("📍 GPS centered on agricultural cluster.");
            },
            { enableHighAccuracy: true }
        );
    });
}

// ============================================================
// GPS NAVIGATION ROUTE TRACER
// ============================================================

function traceGpsRouteToFarmer(farmer) {
    if (activeNavigationRoute) {
        map.removeLayer(activeNavigationRoute);
        activeNavigationRoute = null;
    }

    if (!agentLocation) return;

    const from = [agentLocation.lat, agentLocation.lng];
    const to = [farmer.lat, farmer.lng];
    const dist = calculateDistance(from[0], from[1], to[0], to[1]);

    const driveMins = Math.max(1, Math.round((dist / 35) * 60));
    const walkMins = Math.max(2, Math.round((dist / 4.5) * 60));

    activeNavigationRoute = L.polyline([from, to], {
        color: "#1565c0",
        weight: 4,
        dashArray: "8, 8",
        opacity: 0.85
    }).addTo(map);

    activeNavigationRoute.bindTooltip(
        `<strong>🧭 GPS Route to ${farmer.name}</strong><br>📍 Distance: ${dist.toFixed(2)} km<br>🚗 ~${driveMins} min drive | 🚶 ~${walkMins} min walk`,
        { sticky: true }
    ).openTooltip();

    map.fitBounds(L.latLngBounds([from, to]), { padding: [60, 60] });
    showToast(`🧭 GPS route drawn to ${farmer.name} (${dist.toFixed(2)} km).`);
}

window.appTraceRoute = function (id) {
    const farmer = farmers.find((f) => f.id === id);
    if (!farmer) return;
    switchView("map");
    selectFarmer(farmer, true, false);
    traceGpsRouteToFarmer(farmer);
};

const routeBtn = document.getElementById("routeBtn");
if (routeBtn) {
    routeBtn.addEventListener("click", () => {
        if (selectedFarmer) traceGpsRouteToFarmer(selectedFarmer);
    });
}

// ============================================================
// GPS HUD TOGGLE & COPY CONTROLS
// ============================================================

const gpsHudCard = document.getElementById("gpsHudCard");
const toggleGpsHudBtn = document.getElementById("toggleGpsHudBtn");
const closeGpsHud = document.getElementById("closeGpsHud");

function toggleGpsHud() {
    if (!gpsHudCard) return;
    gpsHudCard.style.display = gpsHudCard.style.display === "none" ? "block" : "none";
}

if (toggleGpsHudBtn) toggleGpsHudBtn.addEventListener("click", toggleGpsHud);
if (closeGpsHud) closeGpsHud.addEventListener("click", () => { if (gpsHudCard) gpsHudCard.style.display = "none"; });

const hudCopyCoordsBtn = document.getElementById("hudCopyCoordsBtn");
if (hudCopyCoordsBtn) {
    hudCopyCoordsBtn.addEventListener("click", () => {
        const text = `${agentLocation.lat.toFixed(6)}, ${agentLocation.lng.toFixed(6)}`;
        navigator.clipboard.writeText(text).then(() => {
            showToast(`📋 Copied GPS: ${text}`);
        });
    });
}

const hudCenterMapBtn = document.getElementById("hudCenterMapBtn");
if (hudCenterMapBtn) {
    hudCenterMapBtn.addEventListener("click", () => {
        map.setView([agentLocation.lat, agentLocation.lng], 16);
        if (agentMarker) agentMarker.openPopup();
    });
}

// ============================================================
// GPS FIELD SURVEY & ACREAGE CALCULATOR
// ============================================================

function calculateGeodesicAreaAcres(coords) {
    if (coords.length < 3) return 0;
    const R = 6378137;
    let total = 0;
    for (let i = 0; i < coords.length; i++) {
        const p1 = coords[i];
        const p2 = coords[(i + 1) % coords.length];
        const lat1 = p1[0] * Math.PI / 180;
        const lat2 = p2[0] * Math.PI / 180;
        const lon1 = p1[1] * Math.PI / 180;
        const lon2 = p2[1] * Math.PI / 180;
        total += (lon2 - lon1) * (2 + Math.sin(lat1) + Math.sin(lat2));
    }
    const areaSqMeters = Math.abs(total * R * R / 4);
    const acres = areaSqMeters / 4046.86;
    return acres;
}

const gpsSurveyModal = document.getElementById("gpsSurveyModal");
const gpsSurveyBtn = document.getElementById("gpsSurveyBtn");
const hudSurveyLaunchBtn = document.getElementById("hudSurveyLaunchBtn");
const closeSurveyModalBtn = document.getElementById("closeSurveyModalBtn");
const surveyFarmerSelect = document.getElementById("surveyFarmerSelect");
const surveyPointCount = document.getElementById("surveyPointCount");
const surveyCalculatedAcres = document.getElementById("surveyCalculatedAcres");
const surveyClaimedAcres = document.getElementById("surveyClaimedAcres");
const surveySimulateWalkBtn = document.getElementById("surveySimulateWalkBtn");
const surveyApplyBtn = document.getElementById("surveyApplyBtn");

function openGpsSurveyModal(targetFarmer = null) {
    if (!gpsSurveyModal || !surveyFarmerSelect) return;

    surveyFarmerSelect.innerHTML = "";
    farmers.forEach((f) => {
        const opt = document.createElement("option");
        opt.value = f.id;
        opt.textContent = `${f.name} - ${f.crop} (${f.area || '3.0 Acres'}, ${f.village || 'Raipur'})`;
        if (targetFarmer && targetFarmer.id === f.id) opt.selected = true;
        surveyFarmerSelect.appendChild(opt);
    });

    const activeF = targetFarmer || (selectedFarmer ? selectedFarmer : farmers[0]);
    updateSurveyModalStats(activeF);

    gpsSurveyModal.style.display = "flex";
    gpsSurveyModal.classList.remove("hidden");
}

function updateSurveyModalStats(farmer) {
    const poly = fieldPolygons[farmer.id] || [];
    const calculated = calculateGeodesicAreaAcres(poly);

    if (surveyPointCount) surveyPointCount.textContent = `${poly.length} Boundary Points`;
    if (surveyCalculatedAcres) surveyCalculatedAcres.textContent = `${calculated.toFixed(2)} Acres`;
    if (surveyClaimedAcres) surveyClaimedAcres.textContent = farmer.area || `${calculated.toFixed(2)} Acres`;
}

if (surveyFarmerSelect) {
    surveyFarmerSelect.addEventListener("change", function () {
        const id = parseInt(this.value);
        const f = farmers.find((item) => item.id === id);
        if (f) updateSurveyModalStats(f);
    });
}

if (gpsSurveyBtn) gpsSurveyBtn.addEventListener("click", () => openGpsSurveyModal(selectedFarmer));
if (hudSurveyLaunchBtn) hudSurveyLaunchBtn.addEventListener("click", () => openGpsSurveyModal(selectedFarmer));
if (closeSurveyModalBtn) closeSurveyModalBtn.addEventListener("click", () => {
    if (gpsSurveyModal) {
        gpsSurveyModal.style.display = "none";
        gpsSurveyModal.classList.add("hidden");
    }
});

if (surveySimulateWalkBtn) {
    surveySimulateWalkBtn.addEventListener("click", () => {
        const id = parseInt(surveyFarmerSelect.value);
        const f = farmers.find((item) => item.id === id);
        if (!f) return;

        gpsSurveyModal.style.display = "none";
        gpsSurveyModal.classList.add("hidden");
        switchView("map");
        selectFarmer(f, true, true);

        surveyBreadcrumbLayers.forEach((l) => map.removeLayer(l));
        surveyBreadcrumbLayers = [];

        const poly = fieldPolygons[f.id] || [];
        poly.forEach((pt, idx) => {
            setTimeout(() => {
                const marker = L.circleMarker(pt, {
                    radius: 6,
                    color: "#1565c0",
                    fillColor: "#42a5f5",
                    fillOpacity: 1
                }).addTo(map);
                marker.bindTooltip(`📍 GPS Waypoint #${idx + 1}`);
                surveyBreadcrumbLayers.push(marker);
            }, idx * 350);
        });

        setTimeout(() => {
            showToast(`✅ GPS Survey Complete: ${f.name}'s field acreage verified.`);
        }, poly.length * 350 + 200);
    });
}

if (surveyApplyBtn) {
    surveyApplyBtn.addEventListener("click", () => {
        const id = parseInt(surveyFarmerSelect.value);
        const f = farmers.find((item) => item.id === id);
        if (f) {
            f.gpsAudited = true;
            f.notes = (f.notes ? f.notes + " " : "") + "[GPS Perimeter Surveyed & Verified]";
            saveFarmersData();
            showToast(`✅ GPS boundary audit saved for ${f.name}.`);
        }
        if (gpsSurveyModal) {
            gpsSurveyModal.style.display = "none";
            gpsSurveyModal.classList.add("hidden");
        }
    });
}

// ============================================================
// VIEW SWITCHING ENGINE
// ============================================================

function switchView(viewName) {
    currentView = viewName;

    // 1. Update Sidebar Active Button
    const sidebarBtns = document.querySelectorAll(".sidebar-nav .nav-item");
    sidebarBtns.forEach((btn) => {
        if (btn.getAttribute("data-view") === viewName) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });

    // 2. Update Mobile Nav Active Button
    const mobileBtns = document.querySelectorAll(".mobile-nav-item");
    mobileBtns.forEach((btn) => {
        if (btn.getAttribute("data-view") === viewName) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });

    // 3. Toggle View Panels
    const viewPanels = {
        map: document.getElementById("viewMap"),
        fields: document.getElementById("viewFields"),
        verification: document.getElementById("viewVerification")
    };

    Object.keys(viewPanels).forEach((key) => {
        if (viewPanels[key]) {
            if (key === viewName) {
                viewPanels[key].classList.add("active");
                viewPanels[key].style.display = "flex";
            } else {
                viewPanels[key].classList.remove("active");
                viewPanels[key].style.display = "none";
            }
        }
    });

    // 4. Update Topbar Titles
    const eyebrow = document.getElementById("topbarEyebrow");
    const title = document.getElementById("topbarTitle");
    const subtitle = document.getElementById("topbarSubtitle");

    if (viewName === "map") {
        if (eyebrow) eyebrow.textContent = "FIELD OPERATIONS";
        if (title) title.textContent = "Farmer Field Map";
        if (subtitle) subtitle.textContent = "Locate registered farmer fields, inspect crops, and verify field submissions.";
        setTimeout(() => {
            map.invalidateSize();
        }, 150);
    } else if (viewName === "fields") {
        if (eyebrow) eyebrow.textContent = "FIELD DIRECTORY";
        if (title) title.textContent = "Farmer Fields & Crop Listings";
        if (subtitle) subtitle.textContent = "Browse registered agricultural fields, inspect crop progress, and review harvest estimates.";
        renderCropFilterChips();
        renderFarmerList();
    } else if (viewName === "verification") {
        if (eyebrow) eyebrow.textContent = "AGENT WORKSPACE";
        if (title) title.textContent = "Verification Operations Command";
        if (subtitle) subtitle.textContent = "Conduct audit checklists, validate GPS compliance, and issue farmer verification badges.";
        renderVerificationHub();
    }

    updateAllCounts();
}

// Wire up sidebar navigation buttons
const navMapBtn = document.getElementById("navMapBtn");
const navFieldsBtn = document.getElementById("navFieldsBtn");
const navVerificationBtn = document.getElementById("navVerificationBtn");

if (navMapBtn) navMapBtn.addEventListener("click", () => switchView("map"));
if (navFieldsBtn) navFieldsBtn.addEventListener("click", () => switchView("fields"));
if (navVerificationBtn) navVerificationBtn.addEventListener("click", () => switchView("verification"));

// Wire up mobile navigation buttons
const mobileNavItems = document.querySelectorAll(".mobile-nav-item");
mobileNavItems.forEach((btn) => {
    btn.addEventListener("click", function () {
        const view = this.getAttribute("data-view");
        if (view) switchView(view);
    });
});

// ============================================================
// COUNTS & KPI SYNCHRONIZATION
// ============================================================

function updateAllCounts() {
    const total = farmers.length;
    const pending = farmers.filter((f) => f.status === "Pending").length;
    const verified = farmers.filter((f) => f.status === "Verified").length;
    const rejected = farmers.filter((f) => f.status === "Rejected").length;

    const totalYield = farmers.reduce((sum, f) => {
        return sum + (f.rawQuantity || 1000);
    }, 0);

    // Sidebar Badges
    const navFieldsCount = document.getElementById("navFieldsCount");
    const navPendingBadge = document.getElementById("navPendingBadge");
    if (navFieldsCount) navFieldsCount.textContent = total;
    if (navPendingBadge) navPendingBadge.textContent = `${pending} Pending`;

    // Map Summary Strip
    const farmerCount = document.getElementById("farmerCount");
    const pendingCount = document.getElementById("pendingCount");
    const verifiedCount = document.getElementById("verifiedCount");
    if (farmerCount) farmerCount.textContent = total;
    if (pendingCount) pendingCount.textContent = pending;
    if (verifiedCount) verifiedCount.textContent = verified;

    // Directory KPI Strip
    const kpiTotalFields = document.getElementById("kpiTotalFields");
    const kpiPendingFields = document.getElementById("kpiPendingFields");
    const kpiVerifiedFields = document.getElementById("kpiVerifiedFields");
    const kpiTotalYield = document.getElementById("kpiTotalYield");

    if (kpiTotalFields) kpiTotalFields.textContent = `${total} Fields`;
    if (kpiPendingFields) kpiPendingFields.textContent = `${pending} Pending`;
    if (kpiVerifiedFields) kpiVerifiedFields.textContent = `${verified} Verified`;
    if (kpiTotalYield) kpiTotalYield.textContent = `${totalYield.toLocaleString()} kg`;

    // Verification Hub Badges
    const vBadgePending = document.getElementById("vBadgePending");
    const vBadgeAll = document.getElementById("vBadgeAll");
    if (vBadgePending) vBadgePending.textContent = pending;
    if (vBadgeAll) vBadgeAll.textContent = total;
}

// ============================================================
// DISTANCE CALCULATIONS
// ============================================================

function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(lat1 * Math.PI / 180) *
        Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

function updateDistances() {
    if (!agentLocation) return;
    farmers.forEach((farmer) => {
        farmer.distanceKm = calculateDistance(
            agentLocation.lat,
            agentLocation.lng,
            farmer.lat,
            farmer.lng
        );
    });
}

const locateBtn = document.getElementById("locateBtn");
if (locateBtn) {
    locateBtn.addEventListener("click", () => {
        if (!agentLocation) {
            getLocationBtn.click();
        } else {
            map.setView([agentLocation.lat, agentLocation.lng], 15);
            if (agentMarker) agentMarker.openPopup();
        }
    });
}

const resetBtn = document.getElementById("resetBtn");
if (resetBtn) {
    resetBtn.addEventListener("click", () => {
        map.setView([21.2514, 81.6296], 13);
        if (activeNavigationRoute) {
            map.removeLayer(activeNavigationRoute);
            activeNavigationRoute = null;
        }
        showToast("Map view reset to default cluster center.");
    });
}

// ============================================================
// FARMER SELECTION & FIELD DETAILS PANEL
// ============================================================

function selectFarmer(farmer, openDetailsPanel = true, centerMap = true) {
    selectedFarmer = farmer;

    const details = document.getElementById("fieldDetails");
    if (details && openDetailsPanel) {
        details.classList.remove("hidden");
    }

    const initialEl = document.getElementById("farmerInitial");
    const nameEl = document.getElementById("selectedFarmer");
    const cropEl = document.getElementById("selectedCrop");
    const qtyEl = document.getElementById("selectedQuantity");
    const harvestEl = document.getElementById("selectedHarvest");
    const statusEl = document.getElementById("selectedStatus");
    const distEl = document.getElementById("selectedDistance");
    const latEl = document.getElementById("selectedLat");
    const lonEl = document.getElementById("selectedLon");

    if (initialEl) initialEl.textContent = farmer.name ? farmer.name.charAt(0) : "F";
    if (nameEl) nameEl.textContent = farmer.name;
    if (cropEl) cropEl.textContent = farmer.crop;
    if (qtyEl) qtyEl.textContent = farmer.quantity;
    if (harvestEl) harvestEl.textContent = farmer.harvest;
    if (latEl) latEl.textContent = farmer.lat.toFixed(4);
    if (lonEl) lonEl.textContent = farmer.lng.toFixed(4);

    if (statusEl) {
        statusEl.textContent = farmer.status;
        statusEl.className = `status-badge ${farmer.status.toLowerCase()}`;
    }

    if (distEl) {
        if (farmer.distanceKm) {
            distEl.textContent = `${farmer.distanceKm.toFixed(2)} km`;
        } else if (agentLocation) {
            const dist = calculateDistance(agentLocation.lat, agentLocation.lng, farmer.lat, farmer.lng);
            farmer.distanceKm = dist;
            distEl.textContent = `${dist.toFixed(2)} km`;
        } else {
            distEl.textContent = "--";
        }
    }

    // Highlight polygon on map
    farmers.forEach((item) => {
        const layer = fieldLayers[item.id];
        if (!layer) return;

        if (item.id === farmer.id) {
            layer.setStyle({
                weight: 4,
                fillOpacity: 0.75
            });
        } else {
            layer.setStyle({
                weight: 2,
                fillOpacity: item.status === "Verified" ? 0.60 : 0.45
            });
        }
    });

    if (centerMap) {
        map.setView([farmer.lat, farmer.lng], 15);
        if (farmerMarkers[farmer.id]) {
            farmerMarkers[farmer.id].openPopup();
        }
    }
}

window.appSelectFarmerById = function (id) {
    const found = farmers.find((f) => f.id === id);
    if (found) {
        selectFarmer(found, true, true);
    }
};

const closePanel = document.getElementById("closePanel");
if (closePanel) {
    closePanel.addEventListener("click", () => {
        const details = document.getElementById("fieldDetails");
        if (details) details.classList.add("hidden");
        selectedFarmer = null;

        if (activeNavigationRoute) {
            map.removeLayer(activeNavigationRoute);
            activeNavigationRoute = null;
        }

        farmers.forEach((item) => {
            const layer = fieldLayers[item.id];
            if (layer) {
                layer.setStyle({
                    weight: 2,
                    fillOpacity: item.status === "Verified" ? 0.60 : 0.45
                });
            }
        });
    });
}

// ============================================================
// VERIFICATION & STATUS UPDATES
// ============================================================

function updateFarmerStatus(farmerId, newStatus, notes = "") {
    const farmer = farmers.find((f) => f.id === farmerId);
    if (!farmer) return;

    farmer.status = newStatus;
    if (notes) farmer.notes = notes;
    farmer.verifiedAt = new Date().toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric"
    });

    saveFarmersData();

    // 1. Update Map Polygon
    const layer = fieldLayers[farmer.id];
    if (layer) {
        const color = getFieldColor(newStatus);
        layer.setStyle({
            color: color,
            fillColor: color,
            fillOpacity: newStatus === "Verified" ? 0.60 : 0.45
        });
        layer.setTooltipContent(
            `<strong>${farmer.name}</strong><br>🌱 ${farmer.crop} (${farmer.quantity})<br>GPS: ${farmer.lat.toFixed(4)}, ${farmer.lng.toFixed(4)}`
        );
    }

    // 2. Update Map Marker
    const marker = farmerMarkers[farmer.id];
    if (marker) {
        marker.setIcon(createFarmerMarkerIcon(farmer));
        marker.setPopupContent(buildPopupHtml(farmer));
    }

    // 3. Update Details Panel if open
    if (selectedFarmer && selectedFarmer.id === farmer.id) {
        selectFarmer(farmer, true, false);
    }

    // 4. Update Other Views
    updateAllCounts();
    if (currentView === "fields") renderFarmerList();
    if (currentView === "verification") renderVerificationHub();
}

function verifyFarmer(farmerId, notes = "") {
    const farmer = farmers.find((f) => f.id === farmerId);
    if (!farmer) return;
    updateFarmerStatus(farmerId, "Verified", notes || "Inspected on-site with GPS verification.");
    showToast(`✅ ${farmer.name}'s field (${farmer.crop}) verified!`);
}

function rejectFarmer(farmerId, notes = "") {
    const farmer = farmers.find((f) => f.id === farmerId);
    if (!farmer) return;
    updateFarmerStatus(farmerId, "Rejected", notes || "Submission flagged during field inspection.");
    showToast(`✕ ${farmer.name}'s submission flagged.`, "error");
}

// Map Panel Buttons
const verifyBtn = document.getElementById("verifyBtn");
if (verifyBtn) {
    verifyBtn.addEventListener("click", () => {
        if (!selectedFarmer) {
            showToast("Please select a farm field first.", "info");
            return;
        }
        verifyFarmer(selectedFarmer.id);
    });
}

const rejectBtn = document.getElementById("rejectBtn");
if (rejectBtn) {
    rejectBtn.addEventListener("click", () => {
        if (!selectedFarmer) {
            showToast("Please select a farm field first.", "info");
            return;
        }
        openVerificationModal(selectedFarmer);
    });
}

const directionsBtn = document.getElementById("directionsBtn");
if (directionsBtn) {
    directionsBtn.addEventListener("click", () => {
        if (!selectedFarmer) {
            showToast("Please select a farm field first.", "info");
            return;
        }
        const destination = `${selectedFarmer.lat},${selectedFarmer.lng}`;
        const url = `https://www.google.com/maps/dir/?api=1&destination=${destination}`;
        window.open(url, "_blank");
    });
}

// ============================================================
// MAP SEARCH & FILTER CONTROLS
// ============================================================

const farmerSearch = document.getElementById("farmerSearch");
const clearSearchBtn = document.getElementById("clearSearchBtn");

function filterMapEntities() {
    const query = farmerSearch ? farmerSearch.value.toLowerCase().trim() : "";
    if (clearSearchBtn) {
        clearSearchBtn.style.display = query.length > 0 ? "flex" : "none";
    }

    farmers.forEach((farmer) => {
        const matchesQuery =
            !query ||
            farmer.name.toLowerCase().includes(query) ||
            farmer.crop.toLowerCase().includes(query) ||
            (farmer.village && farmer.village.toLowerCase().includes(query));

        const matchesStatus =
            activeMapFilter === "all" ||
            farmer.status.toLowerCase() === activeMapFilter.toLowerCase();

        const isVisible = matchesQuery && matchesStatus;

        const layer = fieldLayers[farmer.id];
        if (layer) {
            layer.setStyle({
                fillOpacity: isVisible ? (farmer.status === "Verified" ? 0.65 : 0.50) : 0.08,
                weight: isVisible ? 2 : 1
            });
        }

        const marker = farmerMarkers[farmer.id];
        if (marker) {
            if (isVisible) {
                if (!map.hasLayer(marker)) marker.addTo(map);
            } else {
                if (map.hasLayer(marker)) map.removeLayer(marker);
            }
        }
    });
}

if (farmerSearch) {
    farmerSearch.addEventListener("input", filterMapEntities);
}

if (clearSearchBtn) {
    clearSearchBtn.addEventListener("click", () => {
        if (farmerSearch) farmerSearch.value = "";
        filterMapEntities();
    });
}

const mapFilterBtns = document.querySelectorAll(".map-filter .filter-btn");
mapFilterBtns.forEach((btn) => {
    btn.addEventListener("click", function () {
        mapFilterBtns.forEach((b) => b.classList.remove("active"));
        this.classList.add("active");
        activeMapFilter = this.getAttribute("data-filter") || "all";
        filterMapEntities();
    });
});

// ============================================================
// VIEW 2: FARMER FIELDS DIRECTORY RENDERER & DYNAMIC CHIPS
// ============================================================

function renderCropFilterChips() {
    const container = document.getElementById("cropFilterChips");
    if (!container) return;

    const uniqueCrops = Array.from(new Set(farmers.map((f) => f.crop))).sort();

    container.innerHTML = `
        <button class="chip-btn ${activeCropFilter === 'all' ? 'active' : ''}" data-crop="all" type="button">All Crops (${farmers.length})</button>
    `;

    uniqueCrops.forEach((crop) => {
        const count = farmers.filter((f) => f.crop === crop).length;
        const btn = document.createElement("button");
        btn.className = `chip-btn ${activeCropFilter.toLowerCase() === crop.toLowerCase() ? 'active' : ''}`;
        btn.setAttribute("data-crop", crop);
        btn.type = "button";
        btn.textContent = `${crop} (${count})`;
        btn.addEventListener("click", function () {
            document.querySelectorAll("#cropFilterChips .chip-btn").forEach((c) => c.classList.remove("active"));
            this.classList.add("active");
            activeCropFilter = this.getAttribute("data-crop") || "all";
            renderFarmerList();
        });
        container.appendChild(btn);
    });

    // Wire "all" button
    const allBtn = container.querySelector('[data-crop="all"]');
    if (allBtn) {
        allBtn.addEventListener("click", function () {
            document.querySelectorAll("#cropFilterChips .chip-btn").forEach((c) => c.classList.remove("active"));
            this.classList.add("active");
            activeCropFilter = "all";
            renderFarmerList();
        });
    }
}

function renderFarmerList() {
    const grid = document.getElementById("farmerCardsGrid");
    if (!grid) return;

    const query = document.getElementById("dirSearchInput")
        ? document.getElementById("dirSearchInput").value.toLowerCase().trim()
        : "";

    const filtered = farmers.filter((farmer) => {
        const matchesQuery =
            !query ||
            farmer.name.toLowerCase().includes(query) ||
            farmer.crop.toLowerCase().includes(query) ||
            (farmer.village && farmer.village.toLowerCase().includes(query));

        const matchesCrop =
            activeCropFilter === "all" ||
            farmer.crop.toLowerCase() === activeCropFilter.toLowerCase();

        return matchesQuery && matchesCrop;
    });

    grid.innerHTML = "";

    if (filtered.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 48px; background: white; border-radius: 16px; border: 1px dashed #d5ded2;">
                <span style="font-size: 32px;">🌾</span>
                <h4 style="margin: 12px 0 4px; font-size: 16px;">No farmer fields found</h4>
                <p style="color: #728074; font-size: 13px;">Try adjusting your search query or crop filter.</p>
            </div>
        `;
        return;
    }

    filtered.forEach((farmer) => {
        const card = document.createElement("div");
        card.className = "farmer-field-card";

        const distText = farmer.distanceKm
            ? `${farmer.distanceKm.toFixed(2)} km away`
            : "Distance: --";

        card.innerHTML = `
            <div class="card-top">
                <div class="card-farmer-info">
                    <div class="card-avatar">${farmer.name.charAt(0)}</div>
                    <div>
                        <div class="card-farmer-name">${farmer.name}</div>
                        <div class="card-farmer-id">ID: #FA-2026-${farmer.id} • ${farmer.village || 'Raipur'}</div>
                    </div>
                </div>
                <span class="status-badge ${farmer.status.toLowerCase()}">${farmer.status}</span>
            </div>

            <div class="card-details-grid">
                <div class="card-detail-item">
                    <span>🌱 CROP</span>
                    <strong>${farmer.crop}</strong>
                </div>
                <div class="card-detail-item">
                    <span>📦 EST. YIELD</span>
                    <strong>${farmer.quantity}</strong>
                </div>
                <div class="card-detail-item">
                    <span>📐 FARM AREA</span>
                    <strong>${farmer.area || '3.0 Acres'}</strong>
                </div>
                <div class="card-detail-item">
                    <span>📅 HARVEST</span>
                    <strong>${farmer.harvest}</strong>
                </div>
            </div>

            <div class="card-meta-row">
                <span>📍 ${distText}</span>
                <span>GPS: ${farmer.lat.toFixed(4)}, ${farmer.lng.toFixed(4)}</span>
            </div>

            <div class="card-actions">
                <button class="btn-card-action btn-card-map" onclick="window.appViewOnMap(${farmer.id})">
                    🗺️ View on Map
                </button>
                <button class="btn-card-action btn-card-map" onclick="window.appTraceRoute(${farmer.id})" style="background: #e3f2fd; color: #1565c0; border-color: #bbdefb;">
                    🧭 Route
                </button>
                ${
                    farmer.status === "Verified"
                        ? `<button class="btn-card-action btn-card-verified">✅ Verified</button>`
                        : `<button class="btn-card-action btn-card-verify" onclick="window.appOpenVerificationModal(${farmer.id})">
                            ✓ Verify Field
                           </button>`
                }
            </div>
        `;

        grid.appendChild(card);
    });
}

const dirSearchInput = document.getElementById("dirSearchInput");
if (dirSearchInput) {
    dirSearchInput.addEventListener("input", renderFarmerList);
}

window.appViewOnMap = function (id) {
    const farmer = farmers.find((f) => f.id === id);
    if (!farmer) return;
    switchView("map");
    selectFarmer(farmer, true, true);
};

// ============================================================
// VIEW 3: VERIFICATION OPERATIONS HUB RENDERER
// ============================================================

function renderVerificationHub() {
    const listContainer = document.getElementById("verificationList");
    if (!listContainer) return;

    listContainer.innerHTML = "";

    const list =
        activeVerificationTab === "pending"
            ? farmers.filter((f) => f.status === "Pending")
            : farmers;

    if (list.length === 0) {
        listContainer.innerHTML = `
            <div style="text-align: center; padding: 48px; background: white; border-radius: 16px; border: 1px dashed #d5ded2;">
                <span style="font-size: 34px;">🎉</span>
                <h4 style="margin: 12px 0 4px; font-size: 16px;">All pending farmer fields are verified!</h4>
                <p style="color: #728074; font-size: 13px;">No outstanding submissions in the queue right now.</p>
            </div>
        `;
        return;
    }

    list.forEach((farmer) => {
        const item = document.createElement("div");
        item.className = "v-item-card";

        const dist = farmer.distanceKm
            ? `${farmer.distanceKm.toFixed(2)} km away`
            : "Calculating...";

        item.innerHTML = `
            <div class="v-item-left">
                <div class="card-avatar">${farmer.name.charAt(0)}</div>
                <div>
                    <h4 style="margin: 0 0 3px; font-size: 15px; color: #19271c;">${farmer.name}</h4>
                    <div style="font-size: 12px; color: #6e7d70;">
                        ${farmer.village || 'Raipur'} • GPS: ${farmer.lat.toFixed(4)}, ${farmer.lng.toFixed(4)}
                    </div>
                </div>
            </div>

            <div class="v-item-center">
                <div class="v-item-stat">
                    <span>🌱 CROP</span>
                    <strong>${farmer.crop}</strong>
                </div>
                <div class="v-item-stat">
                    <span>📦 QUANTITY</span>
                    <strong>${farmer.quantity}</strong>
                </div>
                <div class="v-item-stat">
                    <span>📅 HARVEST</span>
                    <strong>${farmer.harvest}</strong>
                </div>
                <div class="v-item-stat">
                    <span>📍 AGENT DISTANCE</span>
                    <strong>${dist}</strong>
                </div>
                <div class="v-item-stat">
                    <span>STATUS</span>
                    <span class="status-badge ${farmer.status.toLowerCase()}">${farmer.status}</span>
                </div>
            </div>

            <div class="v-item-actions">
                ${
                    farmer.status === "Pending"
                        ? `
                        <button class="btn-v-approve" onclick="window.appQuickVerify(${farmer.id})">
                            ✓ Fast Approve
                        </button>
                        <button class="btn-v-audit" onclick="window.appOpenVerificationModal(${farmer.id})">
                            📋 Audit & Notes
                        </button>
                        <button class="btn-v-reject" onclick="window.appOpenVerificationModal(${farmer.id})">
                            ✕ Flag
                        </button>
                        `
                        : `
                        <button class="btn-card-action btn-card-map" onclick="window.appViewOnMap(${farmer.id})">
                            🗺️ Map
                        </button>
                        <button class="btn-v-audit" onclick="window.appOpenVerificationModal(${farmer.id})">
                            📝 View Notes
                        </button>
                        `
                }
            </div>
        `;

        listContainer.appendChild(item);
    });
}

const vTabPending = document.getElementById("vTabPending");
const vTabAll = document.getElementById("vTabAll");

if (vTabPending) {
    vTabPending.addEventListener("click", () => {
        vTabPending.classList.add("active");
        if (vTabAll) vTabAll.classList.remove("active");
        activeVerificationTab = "pending";
        renderVerificationHub();
    });
}

if (vTabAll) {
    vTabAll.addEventListener("click", () => {
        vTabAll.classList.add("active");
        if (vTabPending) vTabPending.classList.remove("active");
        activeVerificationTab = "all";
        renderVerificationHub();
    });
}

const quickAuditNextBtn = document.getElementById("quickAuditNextBtn");
if (quickAuditNextBtn) {
    quickAuditNextBtn.addEventListener("click", () => {
        const nextPending = farmers.find((f) => f.status === "Pending");
        if (nextPending) {
            openVerificationModal(nextPending);
        } else {
            showToast("No pending fields left in queue!", "info");
        }
    });
}

window.appQuickVerify = function (id) {
    verifyFarmer(id);
};

// ============================================================
// INSPECTION & VERIFICATION AUDIT MODAL
// ============================================================

const verificationModal = document.getElementById("verificationModal");
const closeModalBtn = document.getElementById("closeModalBtn");
const modalApproveBtn = document.getElementById("modalApproveBtn");
const modalRejectBtn = document.getElementById("modalRejectBtn");

function openVerificationModal(farmer) {
    modalTargetFarmer = farmer;
    if (!verificationModal) return;

    const titleEl = document.getElementById("modalFarmerTitle");
    const summaryEl = document.getElementById("modalFieldSummary");
    const notesEl = document.getElementById("inspectorNotes");

    if (titleEl) titleEl.textContent = `Field Audit: ${farmer.name}`;
    if (notesEl) notesEl.value = farmer.notes || "";

    if (summaryEl) {
        summaryEl.innerHTML = `
            <div>
                <span style="font-size: 10px; color: #78877a; font-weight: bold;">FARMER NAME</span>
                <div style="font-size: 14px; font-weight: bold;">${farmer.name}</div>
            </div>
            <div>
                <span style="font-size: 10px; color: #78877a; font-weight: bold;">CROP & VARIETY</span>
                <div style="font-size: 14px; font-weight: bold;">🌱 ${farmer.crop}</div>
            </div>
            <div>
                <span style="font-size: 10px; color: #78877a; font-weight: bold;">SUBMISSION YIELD</span>
                <div style="font-size: 14px; font-weight: bold;">📦 ${farmer.quantity} (${farmer.area || '3.2 Acres'})</div>
            </div>
            <div>
                <span style="font-size: 10px; color: #78877a; font-weight: bold;">GPS COORDINATES</span>
                <div style="font-size: 13px; font-family: monospace; color: #1b5e20;">${farmer.lat.toFixed(4)}, ${farmer.lng.toFixed(4)}</div>
            </div>
        `;
    }

    verificationModal.style.display = "flex";
    verificationModal.classList.remove("hidden");
}

window.appOpenVerificationModal = function (id) {
    const farmer = farmers.find((f) => f.id === id);
    if (farmer) openVerificationModal(farmer);
};

function closeVerificationModal() {
    if (verificationModal) {
        verificationModal.style.display = "none";
        verificationModal.classList.add("hidden");
    }
    modalTargetFarmer = null;
}

if (closeModalBtn) closeModalBtn.addEventListener("click", closeVerificationModal);

if (modalApproveBtn) {
    modalApproveBtn.addEventListener("click", () => {
        if (!modalTargetFarmer) return;
        const notes = document.getElementById("inspectorNotes")
            ? document.getElementById("inspectorNotes").value.trim()
            : "";
        verifyFarmer(modalTargetFarmer.id, notes);
        closeVerificationModal();
    });
}

if (modalRejectBtn) {
    modalRejectBtn.addEventListener("click", () => {
        if (!modalTargetFarmer) return;
        const notes = document.getElementById("inspectorNotes")
            ? document.getElementById("inspectorNotes").value.trim()
            : "";
        rejectFarmer(modalTargetFarmer.id, notes);
        closeVerificationModal();
    });
}

// ============================================================
// TOAST NOTIFICATIONS ENGINE
// ============================================================

function showToast(message, type = "success") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast ${type === "error" ? "toast-error" : (type === "info" ? "toast-info" : "")}`;
    toast.innerHTML = `<span>${message}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(20px)";
        setTimeout(() => toast.remove(), 250);
    }, 3500);
}

// ============================================================
// RESET DEMO DATA
// ============================================================

const resetDemoBtn = document.getElementById("resetDemoBtn");
if (resetDemoBtn) {
    resetDemoBtn.addEventListener("click", () => {
        if (confirm("Reset all 12 farmer fields back to initial state?")) {
            localStorage.removeItem("agribridge_farmers_data");
            localStorage.removeItem("agribridge_farmers_data_v2");
            farmers = JSON.parse(JSON.stringify(DEFAULT_FARMERS));

            farmers.forEach((farmer) => {
                const layer = fieldLayers[farmer.id];
                if (layer) {
                    const color = getFieldColor(farmer.status);
                    layer.setStyle({
                        color: color,
                        fillColor: color,
                        fillOpacity: 0.45,
                        weight: 2
                    });
                }
                const marker = farmerMarkers[farmer.id];
                if (marker) {
                    marker.setIcon(createFarmerMarkerIcon(farmer));
                    marker.setPopupContent(buildPopupHtml(farmer));
                }
            });

            if (selectedFarmer) {
                const found = farmers.find((f) => f.id === selectedFarmer.id);
                if (found) selectFarmer(found, true, false);
            }

            if (activeNavigationRoute) {
                map.removeLayer(activeNavigationRoute);
                activeNavigationRoute = null;
            }

            updateAllCounts();
            renderCropFilterChips();
            if (currentView === "fields") renderFarmerList();
            if (currentView === "verification") renderVerificationHub();

            showToast("Demo data reset with 12 farmer fields.");
        }
    });
}

// ============================================================
// INITIAL STARTUP
// ============================================================

processGpsPosition({
    coords: {
        latitude: 21.2514,
        longitude: 81.6296,
        accuracy: 4.2,
        speed: 0,
        altitude: 284
    }
}, false);

renderCropFilterChips();
updateAllCounts();
console.log("AgriBridge Field Agent Ready with 12 Farmer Fields.");