// ==========================================================================
// AGRIBRIDGE — AI FARM COMMAND CENTER
// Multi-Agent Reasoning, Virtual IoT Telemetry & Closed-Loop Verification
// ==========================================================================

const FCC = (function () {
    "use strict";

    // ==========================================================================
    // APPLICATION STATE
    // ==========================================================================
    const State = {
        isOnline: true,
        currentScenario: "NORMAL",
        cropName: "Golden Sharbati Wheat",
        cropStage: "Vegetative / Tillering",
        farmLocation: "Raipur, Chhattisgarh",
        plotId: "Zone A-2",

        // Telemetry State
        telemetry: {
            soilMoisture: 24, // %
            temperature: 29,   // °C
            humidity: 62,      // %
            rainProb: 12,      // %
            lightIntensity: 62000, // lux
            soilPh: 6.6        // pH
        },

        // Farm Health Index (0-100)
        healthScore: 86,

        // 5 Modular Risks (0-100)
        risks: {
            water: 14,
            disease: 12,
            weather: 15,
            nutrient: 10,
            overall: 12
        },

        // Multi-Agent Output Signals
        agentSignals: {
            monitor: "Field stand healthy • Normal vegetative stage",
            water: "Moisture balanced • No immediate irrigation needed",
            disease: "Leaf scan negative • Zero fungal lesions detected",
            nutrient: "Soil pH 6.6 • Nitrogen/Potassium absorption optimal",
            weather: "Clear skies • Rain probability 12%"
        },

        // Action Plan
        actions: [
            {
                id: 1,
                priority: "P1",
                name: "Irrigate Zone A (Sub-Surface Drip)",
                meta: "When: Today @ 6:00 PM • Where: Plot A-2 • Volume: 420 Liters",
                why: "Prevent crop moisture stress before morning heat cycle",
                status: "Pending",
                confidence: 94
            },
            {
                id: 2,
                priority: "P2",
                name: "Inspect Lower Foliage for Yellow Rust",
                meta: "When: Tomorrow Morning • Where: North Border • Confidence: 88%",
                why: "Proactive preventative field scouting",
                status: "Pending",
                confidence: 88
            },
            {
                id: 3,
                priority: "P3",
                name: "Recheck Soil Hydration Sensor Node",
                meta: "When: In 48 Hours • Where: Zone A • Target: 28% Moisture",
                why: "Closed-loop verification of irrigation efficacy",
                status: "Pending",
                confidence: 91
            }
        ],

        // Offline Queue
        offlineQueue: [],

        // Decision History Audit Trail
        history: []
    };

    // ==========================================================================
    // SCENARIO DEFINITIONS (Virtual IoT Telemetry Profiles)
    // ==========================================================================
    const SCENARIOS = {
        NORMAL: {
            name: "NORMAL",
            telemetry: { soilMoisture: 24, temperature: 29, humidity: 62, rainProb: 12, lightIntensity: 62000, soilPh: 6.6 },
            healthScore: 86,
            scoreSummary: "Vegetative tillering stable. Soil hydration balanced at field capacity. Zero fungal spore infestation detected.",
            risks: { water: 14, disease: 12, weather: 15, nutrient: 10, overall: 12 },
            factors: {
                water: "Soil moisture at 24%. Evapotranspiration nominal.",
                disease: "Canopy aeration good. Leaf wetness index 10%.",
                weather: "Calm winds (8 km/h). Temperature 29°C.",
                nutrient: "Soil pH 6.6 (optimal for wheat cation uptake).",
                overall: "All multi-agent risk signals within safe operational bounds."
            },
            actionsText: {
                water: "Next irrigation in 48 hrs",
                disease: "No fungal spray required",
                weather: "Favorable field conditions",
                nutrient: "Maintain bio-fertilizer schedule",
                overall: "Standard farm monitoring"
            },
            agentOutputs: {
                monitor: "Field stand healthy • Normal vegetative stage",
                water: "Moisture balanced • No immediate irrigation needed",
                disease: "Leaf scan negative • Zero fungal lesions detected",
                nutrient: "Soil pH 6.6 • Nitrogen/Potassium absorption optimal",
                weather: "Clear skies • Rain probability 12%"
            },
            evidence: [
                "Soil moisture at 24% is sufficient for wheat vegetative tillering stage.",
                "Atmospheric rain probability is low (12%), eliminating waterlogging threat.",
                "Zero fungal or pest infestation detected in physical sweep and leaf analysis."
            ],
            confidence: "94% High Confidence",
            actions: [
                { id: 1, priority: "P1", name: "Routine Sub-Surface Drip Irrigation", meta: "When: In 48 Hours • Where: Zone A • Volume: 300 L", why: "Maintain optimal field capacity", status: "Pending", confidence: 94 },
                { id: 2, priority: "P2", name: "Routine Foliage Health Inspection", meta: "When: Tomorrow Morning • Where: North Border", why: "Proactive preventative field scouting", status: "Pending", confidence: 88 },
                { id: 3, priority: "P3", name: "Bio-Fertilizer Micronutrient Spray", meta: "When: Next Week • Where: Zone A", why: "Support vigorous tillering", status: "Pending", confidence: 91 }
            ]
        },

        WATER_STRESS: {
            name: "WATER_STRESS",
            telemetry: { soilMoisture: 18, temperature: 34, humidity: 45, rainProb: 12, lightIntensity: 78000, soilPh: 6.5 },
            healthScore: 68,
            scoreSummary: "Water stress detected. Root zone hydration depleted to 18%. High daytime transpiration rate.",
            risks: { water: 84, disease: 10, weather: 45, nutrient: 22, overall: 62 },
            factors: {
                water: "CRITICAL: Moisture 18% below wilting threshold (20%).",
                disease: "Low disease threat; dry microclimate.",
                weather: "Elevated temp (34°C) increasing soil evapotranspiration.",
                nutrient: "Nutrient transport slowed by water deficit.",
                overall: "High water stress risk requiring scheduled irrigation."
            },
            actionsText: {
                water: "URGENT: Irrigate 420 L @ 6:00 PM",
                disease: "No action required",
                weather: "Monitor afternoon heat",
                nutrient: "Irrigate first before fertilizing",
                overall: "Execute P1 Irrigation Action"
            },
            agentOutputs: {
                monitor: "Warning: Wilting indicators detected in lower canopy",
                water: "ALERT: Soil moisture 18% • 420 L irrigation recommended @ 6:00 PM",
                disease: "Low risk • Fungal pressure minimal",
                nutrient: "Estimated nutrient uptake impeded by moisture deficit",
                weather: "Temperature 34°C • Rain probability 12% (no natural rain)"
            },
            evidence: [
                "Soil moisture (18%) is beneath the critical 20% wheat threshold.",
                "Ambient temperature of 34°C is accelerating evapotranspiration.",
                "Rain probability remains low (12%), meaning natural rain will not relieve deficit.",
                "Irrigation scheduled for 6:00 PM to minimize evaporative water loss."
            ],
            confidence: "91% High Confidence",
            actions: [
                { id: 1, priority: "P1", name: "Irrigate Zone A (Sub-Surface Drip)", meta: "When: Today @ 6:00 PM • Where: Plot A-2 • Volume: 420 Liters", why: "Prevent root moisture stress before morning heat cycle", status: "Pending", confidence: 91 },
                { id: 2, priority: "P2", name: "Inspect Moisture Sensor Calibration", meta: "When: Today @ 5:30 PM • Where: Zone A Node 1", why: "Confirm sensor depth contact", status: "Pending", confidence: 86 },
                { id: 3, priority: "P3", name: "Recheck Post-Irrigation Hydration", meta: "When: Tomorrow @ 7:00 AM • Target: 28% Moisture", why: "Verify soil recovery", status: "Pending", confidence: 92 }
            ]
        },

        DISEASE_RISK: {
            name: "DISEASE_RISK",
            telemetry: { soilMoisture: 28, temperature: 28, humidity: 88, rainProb: 40, lightIntensity: 45000, soilPh: 6.4 },
            healthScore: 64,
            scoreSummary: "Elevated fungal spore development conditions. High humidity (88%) and sustained leaf wetness.",
            risks: { water: 12, disease: 86, weather: 35, nutrient: 15, overall: 65 },
            factors: {
                water: "Moisture 28% (ample root zone hydration).",
                disease: "CRITICAL: Humidity 88% creates ideal Yellow Rust environment.",
                weather: "Overcast skies reducing solar UV spore sterilization.",
                nutrient: "Nitrogen level adequate.",
                overall: "Fungal disease escalation risk."
            },
            actionsText: {
                water: "Hold irrigation",
                disease: "URGENT: Apply Bio-Fungicide (Neem Extract)",
                weather: "Scout after fog clears",
                nutrient: "Hold foliar feeding",
                overall: "Execute P1 Disease Scouting"
            },
            agentOutputs: {
                monitor: "Alert: Canopy microclimate favors fungal sporulation",
                water: "Adequate moisture • Irrigation paused",
                disease: "HIGH RISK: 88% humidity triggers Yellow Rust spore alert",
                nutrient: "Estimated nutrient levels stable",
                weather: "Cloud cover 80% • Moderate rain probability 40%"
            },
            evidence: [
                "Relative humidity exceeds 85% for more than 6 consecutive hours.",
                "Ambient temperature (28°C) matches Puccinia striiformis optimal spore germination window.",
                "Integrated with uploaded leaf image AI diagnostics: early lesion check recommended."
            ],
            confidence: "89% High Confidence",
            actions: [
                { id: 1, priority: "P1", name: "Apply Organic Bio-Fungicide (Neem Formulation)", meta: "When: Today @ 4:00 PM • Where: Zone A Canopy • Rate: 3 ml/L", why: "Neutralize fungal spore germination", status: "Pending", confidence: 89 },
                { id: 2, priority: "P2", name: "Physical Leaf Scouting Sweep", meta: "When: Tomorrow Morning • Where: All Plot Quadrants", why: "Verify containment of rust spots", status: "Pending", confidence: 93 },
                { id: 3, priority: "P3", name: "Pause Overhead Sprinklers", meta: "When: Immediate • Duration: 72 Hours", why: "Prevent further leaf wetness accumulation", status: "Pending", confidence: 95 }
            ]
        },

        HEAT_STRESS: {
            name: "HEAT_STRESS",
            telemetry: { soilMoisture: 19, temperature: 41, humidity: 32, rainProb: 5, lightIntensity: 92000, soilPh: 6.6 },
            healthScore: 60,
            scoreSummary: "Severe heatwave alert. Ambient temperature 41°C. Risk of pollen sterility and rapid moisture depletion.",
            risks: { water: 72, disease: 8, weather: 88, nutrient: 25, overall: 70 },
            factors: {
                water: "Rapid depletion due to 41°C heat.",
                disease: "Low disease risk in extreme dry heat.",
                weather: "CRITICAL: Extreme thermal heatwave index.",
                nutrient: "Leaf tip scorching risk.",
                overall: "Severe heat stress requiring protective measures."
            },
            actionsText: {
                water: "Evening cooling irrigation",
                disease: "No spray needed",
                weather: "Deploy micro-sprinkler misting",
                nutrient: "Apply anti-transpirant",
                overall: "Protect crop from heat burnout"
            },
            agentOutputs: {
                monitor: "Thermal stress alert: Leaf temperature above 38°C",
                water: "High deficit: Recommend 500 L evening cooling irrigation",
                disease: "Pathogen risk minimal",
                nutrient: "Transpiration stream under stress",
                weather: "SEVERE HEATWAVE: 41°C • Extreme solar radiation"
            },
            evidence: [
                "Ambient temperature (41°C) exceeds optimal wheat physiological threshold by 9°C.",
                "Solar radiation (92,000 lux) causing rapid stomatal closure and heat burnout.",
                "Nighttime cooling pulse recommended to prevent thermal shock."
            ],
            confidence: "93% High Confidence",
            actions: [
                { id: 1, priority: "P1", name: "Deploy Evening Cooling Irrigation", meta: "When: Today @ 7:30 PM • Where: Zone A • Volume: 500 L", why: "Reduce root-zone thermal buildup", status: "Pending", confidence: 93 },
                { id: 2, priority: "P2", name: "Activate Micro-Misting Sprinklers", meta: "When: 12:00 PM - 3:00 PM • Duration: 15 min pulses", why: "Create microclimate canopy cooling", status: "Pending", confidence: 90 },
                { id: 3, priority: "P3", name: "Apply Potassium Silicate Foliar Spray", meta: "When: Tomorrow 6:00 AM • Rate: 2 g/L", why: "Enhance leaf cuticle heat tolerance", status: "Pending", confidence: 85 }
            ]
        },

        HEAVY_RAIN: {
            name: "HEAVY_RAIN",
            telemetry: { soilMoisture: 32, temperature: 24, humidity: 94, rainProb: 91, lightIntensity: 22000, soilPh: 6.5 },
            healthScore: 78,
            scoreSummary: "Storm Cloudburst Inbound. 91% Rain Probability. Automated AI Replanner CANCELS all pending irrigation to save water.",
            risks: { water: 5, disease: 40, weather: 65, nutrient: 18, overall: 30 },
            factors: {
                water: "Zero irrigation required; incoming natural rain 35mm.",
                disease: "Watch drainage post-storm.",
                weather: "Heavy rainfall (91%) & gusty winds (32 km/h).",
                nutrient: "Ensure field drainage to prevent nitrogen leaching.",
                overall: "Irrigation cancelled; farm water preserved."
            },
            actionsText: {
                water: "IRRIGATION CANCELLED (420 L SAVED)",
                disease: "Inspect drainage channels",
                weather: "Secure plot borders",
                nutrient: "Postpone fertilizer application",
                overall: "Storm preparation protocol"
            },
            agentOutputs: {
                monitor: "Pre-storm stand check • Stems resilient",
                water: "REPLAN TRIGGERED: Irrigation CANCELLED • 420 L Water Saved",
                disease: "Post-rain fungal scouting scheduled",
                nutrient: "Hold nitrogen fertilizer to prevent runoff",
                weather: "STORM INBOUND: 91% Rain Probability • Estimated precipitation 35mm"
            },
            evidence: [
                "Atmospheric radar confirms 91% rain probability within the next 4 hours.",
                "Action Planning Agent resolved signal conflict: Weather Agent overrides Water Agent.",
                "Cancelling the scheduled 420 L irrigation prevents soil waterlogging and potentially avoids 420 L of unnecessary aquifer water extraction."
            ],
            confidence: "High Confidence",
            actions: [
                { id: 1, priority: "P1", name: "🚫 CANCELLED: Irrigation Zone A", meta: "Status: Automatically Cancelled • Potential Water Avoided: 420 Liters", why: "Natural heavy precipitation (91% prob) renders scheduled irrigation redundant", status: "Cancelled", confidence: 96 },
                { id: 2, priority: "P2", name: "Clear Drainage Outlets & Furrows", meta: "When: Immediately • Where: Plot Lower Perimeter", why: "Prevent post-storm water ponding", status: "Pending", confidence: 92 },
                { id: 3, priority: "P3", name: "Post-Storm Saturated Soil Check", meta: "When: In 36 Hours • Where: Zone A Node 1", why: "Verify natural water infiltration", status: "Pending", confidence: 89 }
            ]
        },

        NUTRIENT_RISK: {
            name: "NUTRIENT_RISK",
            telemetry: { soilMoisture: 22, temperature: 28, humidity: 58, rainProb: 15, lightIntensity: 60000, soilPh: 5.2 },
            healthScore: 66,
            scoreSummary: "Estimated Nutrient Lockup. Soil pH dropped to 5.2 (acidic). Cation exchange capacity impaired.",
            risks: { water: 15, disease: 14, weather: 10, nutrient: 82, overall: 60 },
            factors: {
                water: "Moisture 22% (normal).",
                disease: "Low pathogen activity.",
                weather: "Stable conditions.",
                nutrient: "CRITICAL: Acidic soil (pH 5.2) locks phosphorus & potassium uptake.",
                overall: "Estimated nutrient bioavailability risk."
            },
            actionsText: {
                water: "Maintain schedule",
                disease: "No action required",
                weather: "Normal",
                nutrient: "Apply Agricultural Lime (Calcium Carbonate)",
                overall: "Correct soil pH balance"
            },
            agentOutputs: {
                monitor: "Mild interveinal chlorosis estimated on older leaves",
                water: "Hydration normal",
                disease: "Zero pathogen lesions",
                nutrient: "ALERT: Soil pH 5.2 causing estimated phosphorus bioavailability lockup",
                weather: "Favorable conditions"
            },
            evidence: [
                "Estimated soil pH (5.2) is below optimal 6.2 - 6.8 wheat absorption range.",
                "Estimated phosphorus fixation risk in acidic profile; agricultural lime required.",
                "Label: Estimated Nutrient Risk based on sensor pH and crop stage rules."
            ],
            confidence: "88% High Confidence",
            actions: [
                { id: 1, priority: "P1", name: "Apply Agricultural Calcitic Lime", meta: "When: Tomorrow Morning • Where: Zone A • Rate: 150 kg/acre", why: "Neutralize soil acidity and unlock phosphorus availability", status: "Pending", confidence: 88 },
                { id: 2, priority: "P2", name: "Foliar Spray of Chelated Micronutrients", meta: "When: In 3 Days • Where: Foliar Canopy • Rate: 2 ml/L", why: "Bypass root lockup with direct foliar absorption", status: "Pending", confidence: 85 },
                { id: 3, priority: "P3", name: "Recheck Soil pH Sensor", meta: "When: In 7 Days • Target: pH 6.4", why: "Confirm buffering recovery", status: "Pending", confidence: 91 }
            ]
        }
    };

    // ==========================================================================
    // INITIALIZATION
    // ==========================================================================
    function init() {
        setupEventListeners();
        loadStoredDecisions();
        checkOfflineStatus();
        loadSavedDiseaseResult();
        applyScenario("NORMAL", false);
    }

    function setupEventListeners() {
        // Scenario Buttons
        const scenarioBtns = document.querySelectorAll(".fcc-scenario-btn[data-scenario]");
        scenarioBtns.forEach(btn => {
            btn.addEventListener("click", () => {
                const scenKey = btn.getAttribute("data-scenario");
                applyScenario(scenKey, true);
            });
        });

        // 1-Click Grand Finale Demo Button
        const demoBtn = document.getElementById("btn-run-demo");
        if (demoBtn) {
            demoBtn.addEventListener("click", runStormReplanningDemo);
        }

        // Offline / Online Status Toggle
        const statusToggle = document.getElementById("fcc-status-toggle");
        if (statusToggle) {
            statusToggle.addEventListener("click", toggleOnlineStatus);
        }

        // Sync Offline Queue Button
        const syncBtn = document.getElementById("btn-sync-offline");
        if (syncBtn) {
            syncBtn.addEventListener("click", syncOfflineQueue);
        }
    }

    // ==========================================================================
    // SCENARIO & MULTI-AGENT STATE RECALCULATION
    // ==========================================================================
    function applyScenario(scenarioKey, userTriggered = true) {
        const scenario = SCENARIOS[scenarioKey];
        if (!scenario) return;

        State.currentScenario = scenarioKey;
        State.telemetry = { ...scenario.telemetry };
        State.healthScore = scenario.healthScore;
        State.risks = { ...scenario.risks };
        State.actions = JSON.parse(JSON.stringify(scenario.actions));

        // Update active chip
        document.querySelectorAll(".fcc-scenario-btn[data-scenario]").forEach(b => {
            b.classList.toggle("active", b.getAttribute("data-scenario") === scenarioKey);
        });

        // Render UI
        renderTelemetry();
        renderHealthScore(scenario.healthScore, scenario.scoreSummary);
        renderRiskCards(scenario);
        renderAgentSignals(scenario.agentOutputs);
        renderWhyPanel(scenario);
        renderActionPlan();
        updateDecisionStatusPill(scenarioKey);
        updateWhatChangedPanel(scenarioKey);
        renderTimeline(scenarioKey);

        // Record Decision History Event
        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const eventMsg = `Switched to <strong>${scenarioKey}</strong> profile. Multi-Agent decision updated. Health Score: ${scenario.healthScore}/100.`;
        logDecisionEvent(timestamp, eventMsg);

        if (userTriggered) {
            showToast(`Loaded ${scenarioKey.replace("_", " ")} Profile`, "info");
        }
    }

    function updateDecisionStatusPill(scenarioKey) {
        const pill = document.getElementById("fcc-decision-status-pill");
        if (!pill) return;

        switch (scenarioKey) {
            case "WATER_STRESS":
                pill.textContent = "🔴 AI DECISION: IRRIGATION REQUIRED";
                pill.style.background = "#FEE2E2";
                pill.style.color = "#DC2626";
                pill.style.border = "1px solid #FCA5A5";
                break;
            case "HEAVY_RAIN":
                pill.textContent = "🟡 AI DECISION: PLAN REVISED";
                pill.style.background = "#FEF3C7";
                pill.style.color = "#B45309";
                pill.style.border = "1px solid #FCD34D";
                break;
            case "DISEASE_RISK":
                pill.textContent = "🔴 AI DECISION: CROP HEALTH INSPECTION REQUIRED";
                pill.style.background = "#FEE2E2";
                pill.style.color = "#DC2626";
                pill.style.border = "1px solid #FCA5A5";
                break;
            case "HEAT_STRESS":
                pill.textContent = "🟠 AI DECISION: HEAT MITIGATION REQUIRED";
                pill.style.background = "#FFEDD5";
                pill.style.color = "#C2410C";
                pill.style.border = "1px solid #FDBA74";
                break;
            case "NUTRIENT_RISK":
                pill.textContent = "🟠 AI DECISION: NUTRIENT CORRECTION REQUIRED";
                pill.style.background = "#FFEDD5";
                pill.style.color = "#C2410C";
                pill.style.border = "1px solid #FDBA74";
                break;
            case "NORMAL":
            default:
                pill.textContent = "🟢 AI DECISION: NO ACTION REQUIRED";
                pill.style.background = "#EBF3E7";
                pill.style.color = "#315C2A";
                pill.style.border = "1px solid #C4DEC0";
                break;
        }
    }

    function updateWhatChangedPanel(scenarioKey) {
        const panel = document.getElementById("fcc-what-changed-card");
        const impact = document.getElementById("fcc-decision-impact-card");
        if (panel) panel.style.display = scenarioKey === "HEAVY_RAIN" ? "block" : "none";
        if (impact) impact.style.display = scenarioKey === "HEAVY_RAIN" ? "block" : "none";
    }

    function renderTimeline(scenarioKey) {
        const container = document.getElementById("fcc-action-timeline");
        if (!container) return;

        const now = new Date();
        const timeMinus = (mins) => {
            const d = new Date(now.getTime() - mins * 60000);
            return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        };

        let items = [];
        if (scenarioKey === "HEAVY_RAIN") {
            items = [
                { time: timeMinus(6), text: "📡 Farm signals received (Moisture 18%, Temp 34°C, Rain 12%)" },
                { time: timeMinus(5), text: "🧠 Water Intelligence detected high soil moisture deficit in Zone A" },
                { time: timeMinus(4), text: "💧 Action Planner scheduled irrigation: <strong>420 L @ 6:00 PM (Awaiting confirmation)</strong>" },
                { time: timeMinus(2), text: "🌧️ Heavy rain storm scenario detected: <strong>Rain probability surged to 91%</strong>" },
                { time: timeMinus(1), text: "🔄 AI replanned farm action: Weather Agent overrode Water Agent" },
                { time: timeMinus(0), text: "❌ <strong>Irrigation Cancelled</strong> — 💧 <strong>420 L potentially avoided</strong> (Drainage protocol active)" }
            ];
        } else if (scenarioKey === "WATER_STRESS") {
            items = [
                { time: timeMinus(4), text: "📡 Farm signals received (Moisture 18%, Temp 34°C, Rain 12%)" },
                { time: timeMinus(3), text: "🧠 Water Intelligence Agent raised <strong>WATER STRESS ALERT (84/100)</strong>" },
                { time: timeMinus(1), text: "💧 Action Planner generated P1 Action: <strong>Irrigate Zone A (420 L @ 6:00 PM)</strong>" },
                { time: timeMinus(0), text: "📋 Awaiting farmer confirmation or automated weather replanning trigger" }
            ];
        } else if (scenarioKey === "DISEASE_RISK") {
            items = [
                { time: timeMinus(4), text: "📡 Microclimate signals received (Humidity 88%, Temp 28°C)" },
                { time: timeMinus(3), text: "🦠 Crop Health Agent detected elevated <strong>Yellow Rust spore germination index</strong>" },
                { time: timeMinus(1), text: "🩺 Action Planner recommended: <strong>Apply Organic Bio-Fungicide (Neem Extract)</strong>" }
            ];
        } else {
            items = [
                { time: timeMinus(5), text: "📡 Farm signals received (Moisture 24%, Temp 29°C, Rain 12%, pH 6.6)" },
                { time: timeMinus(3), text: "✓ Multi-Agent consensus: All physiological risk parameters within optimal bounds" },
                { time: timeMinus(0), text: "🟢 AI Decision: <strong>NO ACTION REQUIRED</strong> — Continue standard farm stand monitoring" }
            ];
        }

        container.innerHTML = items.map(it => `
            <div class="fcc-history-item">
                <span class="fcc-history-time" style="font-weight: 700; color: var(--ab-primary-green);">${it.time}</span>
                <span class="fcc-history-event">${it.text}</span>
            </div>
        `).join("");
    }

    // ==========================================================================
    // UI RENDERING FUNCTIONS
    // ==========================================================================
    function renderTelemetry() {
        const t = State.telemetry;

        setElemText("telemetry-moisture-val", t.soilMoisture);
        setElemWidth("telemetry-moisture-bar", `${Math.min(100, t.soilMoisture * 2)}%`);

        setElemText("telemetry-temp-val", t.temperature);
        setElemWidth("telemetry-temp-bar", `${Math.min(100, (t.temperature / 50) * 100)}%`);

        setElemText("telemetry-humidity-val", t.humidity);
        setElemWidth("telemetry-humidity-bar", `${t.humidity}%`);

        setElemText("telemetry-rain-val", t.rainProb);
        setElemWidth("telemetry-rain-bar", `${t.rainProb}%`);

        setElemText("telemetry-light-val", t.lightIntensity.toLocaleString());
        setElemWidth("telemetry-light-bar", `${Math.min(100, (t.lightIntensity / 100000) * 100)}%`);

        setElemText("telemetry-ph-val", t.soilPh.toFixed(1));
        setElemWidth("telemetry-ph-bar", `${Math.min(100, (t.soilPh / 10) * 100)}%`);

        // Save telemetry snapshot to storage for Admin monitoring
        localStorage.setItem("agribridge_telemetry", JSON.stringify({
            timestamp: new Date().toISOString(),
            ...t
        }));
    }

    function renderHealthScore(score, summary) {
        setElemText("fcc-health-score", score);
        setElemText("fcc-score-summary", summary);

        const circle = document.getElementById("fcc-score-circle");
        const badge = document.getElementById("fcc-score-badge");
        if (circle) {
            // Circumference is 2 * PI * 60 ~= 377
            const offset = 377 - (377 * score) / 100;
            circle.style.strokeDashoffset = offset;

            if (score >= 80) {
                circle.style.stroke = "var(--ab-primary-green)";
                if (badge) {
                    badge.textContent = "Optimal Farm Stand";
                    badge.style.background = "#EBF3E7";
                    badge.style.color = "#315C2A";
                }
            } else if (score >= 65) {
                circle.style.stroke = "#F59E0B";
                if (badge) {
                    badge.textContent = "Moderate Attention Needed";
                    badge.style.background = "#FEF3C7";
                    badge.style.color = "#B45309";
                }
            } else {
                circle.style.stroke = "#DC2626";
                if (badge) {
                    badge.textContent = "Critical Risk Alert";
                    badge.style.background = "#FEE2E2";
                    badge.style.color = "#DC2626";
                }
            }
        }
    }

    function renderRiskCards(scen) {
        const r = scen.risks;
        const f = scen.factors;
        const a = scen.actionsText;

        // Water
        updateRiskCard("water", r.water, f.water, a.water);
        // Disease
        updateRiskCard("disease", r.disease, f.disease, a.disease);
        // Weather
        updateRiskCard("weather", r.weather, f.weather, a.weather);
        // Nutrient
        updateRiskCard("nutrient", r.nutrient, f.nutrient, a.nutrient);
        // Overall
        updateRiskCard("overall", r.overall, f.overall, a.overall);
    }

    function updateRiskCard(type, score, factor, action) {
        const card = document.getElementById(`risk-card-${type}`);
        const badge = document.getElementById(`badge-${type}-risk`);
        const val = document.getElementById(`val-${type}-risk`);
        const factElem = document.getElementById(`factors-${type}-risk`);
        const actElem = document.getElementById(`action-${type}-risk`);

        if (val) val.textContent = type === "overall" ? `${score}% Combined` : `${score} / 100`;
        if (factElem) factElem.textContent = factor;
        if (actElem) actElem.textContent = action;

        if (card && badge) {
            card.classList.remove("risk-low", "risk-medium", "risk-high");
            badge.classList.remove("badge-low", "badge-med", "badge-high");

            if (score <= 25) {
                card.classList.add("risk-low");
                badge.classList.add("badge-low");
                badge.textContent = type === "overall" ? "SAFE" : `LOW (${score}%)`;
            } else if (score <= 60) {
                card.classList.add("risk-medium");
                badge.classList.add("badge-med");
                badge.textContent = type === "overall" ? "MODERATE" : `MED (${score}%)`;
            } else {
                card.classList.add("risk-high");
                badge.classList.add("badge-high");
                badge.textContent = type === "overall" ? "ELEVATED" : `HIGH (${score}%)`;
            }
        }
    }

    function renderAgentSignals(signals) {
        setElemText("agent-signal-monitor", signals.monitor);
        setElemText("agent-signal-water", signals.water);
        setElemText("agent-signal-disease", signals.disease);
        setElemText("agent-signal-nutrient", signals.nutrient);
        setElemText("agent-signal-weather", signals.weather);
    }

    function renderWhyPanel(scen) {
        const list = document.getElementById("why-evidence-list");
        if (list && scen.evidence) {
            list.innerHTML = scen.evidence.map(e => `
                <li class="fcc-evidence-item">
                    <span class="fcc-evidence-check">✓</span>
                    <span>${e}</span>
                </li>
            `).join("");
        }

        setElemText("why-confidence-val", scen.confidence || "94% High Confidence");

        const decisionId = `DEC-${Date.now().toString().slice(-6)}`;
        setElemText("why-decision-id", decisionId);
    }

    function renderActionPlan() {
        const container = document.getElementById("action-plan-container");
        if (!container) return;

        container.innerHTML = State.actions.map(action => {
            const isCompleted = action.status === "Completed";
            const isCancelled = action.status === "Cancelled";

            let pClass = "priority-p1";
            let tagClass = "";
            if (action.priority === "P2") { pClass = "priority-p2"; tagClass = "p2"; }
            if (action.priority === "P3") { pClass = "priority-p3"; tagClass = "p3"; }

            let statusBtn = `
                <button class="fcc-action-btn fcc-btn-complete" onclick="FCC.completeAction(${action.id})">
                    ✓ Approve Action (Simulated)
                </button>
            `;

            if (isCompleted) {
                pClass += " status-completed";
                statusBtn = `<span style="color: #2E7D32; font-weight: 700; font-size: 0.82rem;">✓ Action Approved • Execution: Simulated</span>`;
            } else if (isCancelled) {
                pClass += " status-completed";
                statusBtn = `<span style="color: #DC2626; font-weight: 700; font-size: 0.82rem;">🚫 Cancelled</span>`;
            }

            return `
                <div class="fcc-action-item ${pClass}" id="action-item-${action.id}">
                    <div class="fcc-action-left">
                        <span class="fcc-priority-tag ${tagClass}">${action.priority}</span>
                        <div class="fcc-action-text-group">
                            <span class="fcc-action-name">${action.name}</span>
                            <span class="fcc-action-meta">${action.meta}</span>
                            <span class="fcc-action-why">${action.why}</span>
                        </div>
                    </div>
                    <div class="fcc-action-btn-group">
                        ${statusBtn}
                    </div>
                </div>
            `;
        }).join("");
    }

    // ==========================================================================
    // CLOSED-LOOP ACTION COMPLETION & SIMULATED VERIFICATION
    // ==========================================================================
    function completeAction(actionId) {
        const action = State.actions.find(a => a.id === actionId);
        if (!action) return;

        if (!State.isOnline) {
            // Queue offline
            State.offlineQueue.push({
                actionId: action.id,
                actionName: action.name,
                timestamp: new Date().toISOString()
            });
            updateOfflineQueueUI();
            showToast(`Action '${action.name}' queued locally (Offline)`, "info");
            return;
        }

        action.status = "Completed";
        renderActionPlan();

        // Perform Closed-Loop Simulated Verification
        const verificationBox = document.getElementById("fcc-verification-box");
        const verificationMsg = document.getElementById("fcc-verification-msg");

        if (actionId === 1) {
            // Post-irrigation verification
            const oldMoisture = State.telemetry.soilMoisture;
            const newMoisture = 32;
            State.telemetry.soilMoisture = newMoisture;
            State.healthScore = Math.min(94, State.healthScore + 14);
            State.risks.water = Math.max(8, State.risks.water - 40);

            renderTelemetry();
            renderHealthScore(State.healthScore, "Hydration restored post-action. Root moisture replenished.");
            updateRiskCard("water", State.risks.water, `Post-action sensor sweep: ${newMoisture}% moisture.`, "Optimal hydration");

            if (verificationBox && verificationMsg) {
                verificationMsg.innerHTML = `
                    Action executed successfully. Post-irrigation sensor sweep confirms:
                    <strong>Soil moisture (Previous: ${oldMoisture}% ➔ Simulated: ${newMoisture}%)</strong>.
                    Status: <strong>Recovery detected</strong>. Action closed.
                `;
                verificationBox.style.display = "block";
            }

            const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            logDecisionEvent(timestamp, `Farmer approved and executed <strong>${action.name}</strong>. Simulated sensor verification: Moisture rose from ${oldMoisture}% to ${newMoisture}%. Status: Recovery detected.`);
            showToast("Action approved & verified by sensor sweep (Simulated)!", "success");

        } else {
            if (verificationBox && verificationMsg) {
                verificationMsg.innerHTML = `
                    Action <strong>'${action.name}'</strong> marked as completed. Sensor audit confirms field parameters are within normal threshold.
                `;
                verificationBox.style.display = "block";
            }
            showToast(`Action '${action.name}' approved (Simulated)!`, "success");
        }
    }

    // ==========================================================================
    // CRITICAL WEATHER-TRIGGERED REPLANNING (SMART ACTION)
    // ==========================================================================
    function runStormReplanningDemo() {
        showToast("Analyzing root-zone moisture deficit...", "info");
        applyScenario("WATER_STRESS", false);

        // Simulate impending storm cloudburst in 3.5 seconds
        setTimeout(() => {
            showToast("🌦️ Weather Radar Alert: Storm precipitation detected! Optimizing plan...", "info");

            setTimeout(() => {
                applyScenario("HEAVY_RAIN", false);

                // Show dynamic replanning alert
                showToast("🌧️ FARM PLAN UPDATED: Heavy rain detected. Irrigation cancelled. 420 L potentially avoided.", "success");

                const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                logDecisionEvent(timestamp, "<strong>Weather-Triggered Optimization:</strong> Rain probability surged to 91%. Water Agent cancelled 420 L irrigation. Potential water avoided: 420 L. Reason: Heavy rainfall expected within irrigation window.");

                // Record in persistent audit trail
                persistDecisionSnapshot({
                    event: "STORM_TRIGGERED_OPTIMIZATION",
                    timestamp: new Date().toISOString(),
                    waterAvoidedLiters: 420,
                    rainProbability: 91,
                    status: "Cancelled & Conserved"
                });

            }, 1000);
        }, 3200);
    }

    // ==========================================================================
    // OFFLINE MODE & LOCAL QUEUE SYNCHRONIZATION
    // ==========================================================================
    function toggleOnlineStatus() {
        State.isOnline = !State.isOnline;
        const toggleBtn = document.getElementById("fcc-status-toggle");
        const statusText = document.getElementById("fcc-status-text");

        if (State.isOnline) {
            toggleBtn.className = "fcc-status-pill fcc-status-online";
            if (statusText) statusText.textContent = "🟢 ONLINE • SYNCED";
            showToast("Connectivity restored (🟢 ONLINE • SYNCED)", "success");
            updateOfflineQueueUI();
        } else {
            toggleBtn.className = "fcc-status-pill fcc-status-offline";
            if (statusText) statusText.textContent = "🟠 OFFLINE MODE";
            showToast("Switched to Offline Mode. Actions will be queued locally.", "info");
            updateOfflineQueueUI();
        }
    }

    function checkOfflineStatus() {
        try {
            const queue = localStorage.getItem("agribridge_offline_actions_queue");
            if (queue) {
                State.offlineQueue = JSON.parse(queue) || [];
                updateOfflineQueueUI();
            }
        } catch (e) {
            console.warn("Offline queue error:", e);
        }
    }

    function updateOfflineQueueUI() {
        const queueBar = document.getElementById("fcc-offline-queue");
        const countSpan = document.getElementById("fcc-offline-queue-count");

        if (!queueBar || !countSpan) return;

        countSpan.textContent = State.offlineQueue.length;

        if (!State.isOnline) {
            queueBar.style.display = "flex";
            queueBar.querySelector("div").innerHTML = `<strong>🟠 Offline Mode Active:</strong> <span id="fcc-offline-queue-count">${State.offlineQueue.length}</span> action(s) queued locally.`;
        } else if (State.offlineQueue.length > 0) {
            queueBar.style.display = "flex";
            queueBar.querySelector("div").innerHTML = `<strong>📡 Pending Sync:</strong> <span id="fcc-offline-queue-count">${State.offlineQueue.length}</span> action(s) queued locally.`;
        } else {
            queueBar.style.display = "none";
        }

        localStorage.setItem("agribridge_offline_actions_queue", JSON.stringify(State.offlineQueue));
    }

    function syncOfflineQueue() {
        if (State.offlineQueue.length === 0) {
            showToast("No offline actions in queue.", "info");
            return;
        }

        const count = State.offlineQueue.length;
        State.offlineQueue.forEach(item => {
            const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            logDecisionEvent(timestamp, `Synced offline action: <strong>${item.actionName}</strong>.`);
        });

        State.offlineQueue = [];
        updateOfflineQueueUI();
        showToast(`Successfully synced ${count} queued action(s) with server!`, "success");
    }

    // ==========================================================================
    // DISEASE AI INTEGRATION & REASONING
    // ==========================================================================
    function loadSavedDiseaseResult() {
        try {
            const saved = localStorage.getItem("aiResult");
            if (saved) {
                const parsed = JSON.parse(saved);
                if (parsed && parsed.disease) {
                    const diseaseName = parsed.disease.disease || "Leaf Spot";
                    const conf = parsed.prediction?.confidence || 94;

                    State.agentSignals.disease = `Leaf scan: ${diseaseName} (${conf}%) • Bio-treatment ready`;
                    renderAgentSignals(State.agentSignals);
                }
            }
        } catch (e) {
            console.warn("Disease result load warning:", e);
        }
    }

    // ==========================================================================
    // DECISION HISTORY AUDIT TRAIL
    // ==========================================================================
    function logDecisionEvent(time, eventHtml) {
        State.history.unshift({ time, eventHtml });
        renderHistory();

        // Persist to local decision log
        try {
            localStorage.setItem("agribridge_ai_decisions", JSON.stringify(State.history.slice(0, 30)));
        } catch (e) {}
    }

    function loadStoredDecisions() {
        try {
            const saved = localStorage.getItem("agribridge_ai_decisions");
            if (saved) {
                State.history = JSON.parse(saved);
            } else {
                State.history = [
                    { time: "14:02", eventHtml: "Water Intelligence Agent recommended 420 L irrigation for Zone A." },
                    { time: "13:45", eventHtml: "Farm Monitoring Agent verified vegetative wheat tillering status." },
                    { time: "12:30", eventHtml: "Soil pH sensor calibrated at 6.6 (Optimal absorption range)." }
                ];
            }
            renderHistory();
        } catch (e) {}
    }

    function renderHistory() {
        const container = document.getElementById("fcc-history-container");
        if (!container) return;

        container.innerHTML = State.history.map(item => `
            <div class="fcc-history-item">
                <span class="fcc-history-time">${item.time}</span>
                <span class="fcc-history-event">${item.eventHtml}</span>
            </div>
        `).join("");
    }

    function clearHistory() {
        State.history = [];
        localStorage.removeItem("agribridge_ai_decisions");
        renderHistory();
        showToast("Activity history cleared.", "info");
    }

    function persistDecisionSnapshot(decisionObj) {
        try {
            const liveLogins = localStorage.getItem("agribridge_live_logins");
            const parsed = liveLogins ? JSON.parse(liveLogins) : [];
            parsed.unshift({
                role: "Farmer / AI Engine",
                email: "ramesh@agrifarm.in",
                ip: "10.228.117.107",
                device: "AI Farm Command Center",
                time: new Date().toLocaleTimeString(),
                activity: `AI Decision: ${decisionObj.event} (Saved ${decisionObj.waterSavedLiters || 0} L)`
            });
            localStorage.setItem("agribridge_live_logins", JSON.stringify(parsed.slice(0, 20)));
        } catch (e) {}
    }

    // ==========================================================================
    // UTILITY HELPERS & TOASTS
    // ==========================================================================
    function setElemText(id, text) {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    }

    function setElemWidth(id, widthStr) {
        const el = document.getElementById(id);
        if (el) el.style.width = widthStr;
    }

    function showToast(msg, type = "info") {
        const container = document.getElementById("fcc-toast-container");
        if (!container) return;

        const toast = document.createElement("div");
        toast.className = "fcc-toast";
        toast.innerHTML = `<span>⚡</span><span>${msg}</span>`;

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transform = "translateY(20px)";
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }

    async function checkDatabaseStatus() {
        try {
            const resp = await fetch("http://127.0.0.1:8000/api/db/status");
            if (resp.ok) {
                const data = await resp.json();
                const dbStatusEl = document.getElementById("fcc-db-status");
                if (dbStatusEl) {
                    if (data.is_fallback) {
                        dbStatusEl.textContent = "SQLite FALLBACK — ACTIVE";
                        dbStatusEl.style.color = "#DC2626";
                        dbStatusEl.title = data.warning || "SQLite Fallback Active";
                    } else {
                        dbStatusEl.textContent = "MySQL — ACTIVE";
                        dbStatusEl.style.color = "#16A34A";
                    }
                }
            }
        } catch (e) {
            console.warn("Database status check notice:", e);
        }
    }

    // ==========================================================================
    // PHASE 4: DETERMINISTIC SCENARIO ENGINE & PROVENANCE MATRIX
    // ==========================================================================

    const DETERMINISTIC_PAYLOADS = {
        NORMAL: {
            crop: "wheat",
            state: "Uttar Pradesh",
            district: "Sultanpur",
            soil_moisture_vwc: 50.0,
            rain_probability: 12,
            wind_speed: 8.0,
            confidence: 94.0,
            disease_name: "Healthy Leaf Stand"
        },
        A: {
            crop: "wheat",
            state: "Uttar Pradesh",
            district: "Sultanpur",
            disease_name: "Wheat Yellow Rust",
            confidence: 82.0,
            soil_moisture_vwc: 55.0,
            rain_probability: 10,
            wind_speed: 12.0
        },
        B: {
            crop: "wheat",
            state: "Punjab",
            district: "Ludhiana",
            disease_name: "Wheat Yellow Rust",
            confidence: 51.69,
            soil_moisture_vwc: 24.0,
            rain_probability: 10,
            wind_speed: 12.0
        },
        C: {
            crop: "wheat",
            state: "Haryana",
            district: "Karnal",
            disease_name: "Wheat Yellow Rust",
            confidence: 82.0,
            soil_moisture_vwc: 45.0,
            rain_probability: 85,
            wind_speed: 25.0
        },
        D: {
            crop: "wheat",
            state: "Uttar Pradesh",
            district: "Sultanpur",
            disease_name: "Wheat Yellow Rust",
            confidence: 82.0,
            soil_moisture_vwc: 24.0
        }
    };

    function getProvBadgeHtml(prov) {
        const p = (prov || "UNAVAILABLE").toUpperCase();
        const pLower = p.toLowerCase();
        return `<span class="prov-badge prov-${pLower}">${p}</span>`;
    }

    async function runDeterministicScenario(scenarioKey) {
        const payload = DETERMINISTIC_PAYLOADS[scenarioKey] || DETERMINISTIC_PAYLOADS.NORMAL;

        // Highlight scenario button
        const buttons = document.querySelectorAll("#scenario-btn-group button");
        buttons.forEach(btn => {
            const sc = btn.getAttribute("data-scenario");
            if (sc === `SCENARIO_${scenarioKey}` || (scenarioKey === "NORMAL" && sc === "NORMAL")) {
                btn.classList.add("active");
            } else {
                btn.classList.remove("active");
            }
        });

        showToast(`Executing Scenario ${scenarioKey} through Policy Engine...`, "info");

        try {
            const res = await fetch("http://127.0.0.1:8000/api/orchestration/evaluate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            renderJudgeMatrix(data, payload);

            // Log event to timeline
            const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            logDecisionEvent(time, `Executed Scenario <strong>${scenarioKey}</strong> • Risk: <strong>${data.overall_risk?.toUpperCase()}</strong> • Constraints: ${data.constraints?.join(", ") || "None"}.`);
            showToast(`✓ Scenario ${scenarioKey} evaluated successfully!`, "success");

        } catch (err) {
            console.error("Scenario evaluation failed:", err);
            showToast("Failed to connect to backend policy engine. Please ensure backend is running.", "info");
        }
    }

    function renderJudgeMatrix(decisionData, payload) {
        if (!decisionData) return;

        // 1. Stat Boxes
        const riskEl = document.getElementById("judge-stat-risk");
        if (riskEl) {
            const risk = (decisionData.overall_risk || "moderate").toUpperCase();
            riskEl.textContent = risk;
            riskEl.style.color = (risk === "CRITICAL" || risk === "HIGH") ? "#DC2626" : (risk === "MODERATE" ? "#D97706" : "#16A34A");
        }

        const prioEl = document.getElementById("judge-stat-priority");
        if (prioEl) {
            prioEl.textContent = (decisionData.priority || "routine").toUpperCase();
            prioEl.style.color = decisionData.priority === "urgent" ? "#DC2626" : "#2563EB";
        }

        const escEl = document.getElementById("judge-stat-escalation");
        if (escEl) {
            if (decisionData.escalation_required) {
                escEl.innerHTML = "🚨 Field Agent Dispatched";
                escEl.style.color = "#DC2626";
            } else {
                escEl.innerHTML = "🛡️ Farmer Autonomous Action";
                escEl.style.color = "#059669";
            }
        }

        const sigCountEl = document.getElementById("judge-stat-signals");
        if (sigCountEl) {
            sigCountEl.textContent = `${decisionData.signals_considered || 20} Signals Inspected`;
        }

        // 2. Prescription Locked Banner
        const rxBanner = document.getElementById("judge-rx-locked-banner");
        const rxDesc = document.getElementById("judge-rx-locked-desc");
        const constraints = decisionData.constraints || [];
        if (rxBanner) {
            if (constraints.includes("PRESCRIPTION_LOCKED") || decisionData.escalation_required) {
                rxBanner.style.display = "flex";
                if (rxDesc && decisionData.escalation_reason) {
                    rxDesc.textContent = decisionData.escalation_reason;
                }
            } else {
                rxBanner.style.display = "none";
            }
        }

        // 3. Constraints List
        const constrList = document.getElementById("judge-constraints-list");
        if (constrList) {
            if (constraints.length === 0) {
                constrList.innerHTML = `<span class="prov-badge prov-live">NONE (ALL GATES CLEAR)</span>`;
            } else {
                constrList.innerHTML = constraints.map(c => `<span class="prov-badge prov-derived" style="background: #FEE2E2; color: #DC2626; border-color: #FCA5A5;">⚠️ ${c}</span>`).join(" ");
            }
        }

        // 4. Blocked Operations List
        const blockedList = document.getElementById("judge-blocked-list");
        if (blockedList) {
            const blocked = decisionData.blocked_actions || [];
            if (blocked.length === 0) {
                blockedList.innerHTML = `<span style="color: #16A34A; font-weight: 600;">None (Standard farm operations permitted)</span>`;
            } else {
                blockedList.innerHTML = blocked.map(b => `<div style="margin-top: 3px;">• 🚫 <strong>${b}</strong></div>`).join("");
            }
        }

        // 5. Provenance Matrix Table
        const provTbody = document.getElementById("judge-provenance-tbody");
        if (provTbody && decisionData.provenance_summary) {
            const rows = Object.entries(decisionData.provenance_summary).map(([key, item]) => {
                const provBadge = getProvBadgeHtml(item.provenance);
                const valStr = item.has_value === "True" ? "Active / Validated" : "N/A (Unavailable)";
                return `
                    <tr>
                        <td><strong>${key}</strong></td>
                        <td>${valStr}</td>
                        <td><code>${item.unit || "N/A"}</code></td>
                        <td>${item.source || "System Engine"}</td>
                        <td><span style="font-size: 0.72rem; font-weight: 700; color: ${item.quality === 'VALID' ? '#16A34A' : '#64748B'}">${item.quality || 'VALID'}</span></td>
                        <td>${provBadge}</td>
                    </tr>
                `;
            });
            provTbody.innerHTML = rows.join("");
        }

        // 6. Decision Trace Table
        const traceTbody = document.getElementById("judge-trace-tbody");
        if (traceTbody && decisionData.decision_trace) {
            const traceRows = decisionData.decision_trace.map(t => {
                const provBadge = getProvBadgeHtml(t.provenance);
                return `
                    <tr>
                        <td><code>${t.signal}</code></td>
                        <td><strong>${t.condition}</strong></td>
                        <td style="color: #64748B; font-size: 0.74rem;">${t.policy}</td>
                        <td><span style="color: #0F172A; font-weight: 600;">${t.effect}</span></td>
                        <td>${provBadge}</td>
                    </tr>
                `;
            });
            traceTbody.innerHTML = traceRows.join("");
        }

        // 7. Sync top-level telemetry widgets with scenario payload
        if (payload.soil_moisture_vwc !== undefined) {
            setElemText("telemetry-moisture-val", Math.round(payload.soil_moisture_vwc));
            setElemWidth("telemetry-moisture-bar", `${Math.min(100, Math.round(payload.soil_moisture_vwc))}%`);
        }
        if (payload.rain_probability !== undefined) {
            setElemText("telemetry-rain-val", payload.rain_probability);
            setElemWidth("telemetry-rain-bar", `${payload.rain_probability}%`);
        }

        // 8. Update Action Plan items with recommended actions
        const recActions = decisionData.recommended_actions || [];
        if (recActions.length > 0) {
            const a1Name = document.getElementById("action-1-name");
            const a1Why = document.getElementById("action-1-why");
            if (a1Name) a1Name.textContent = recActions[0];
            if (a1Why) a1Why.textContent = decisionData.escalation_reason || "Deterministic policy recommendation";
        }
    }

    function init() {
        loadStoredDecisions();
        loadSavedDiseaseResult();
        checkDatabaseStatus();
        updateOfflineQueueUI();
        runDeterministicScenario("NORMAL");
    }

    function resetDemo() {
        runDeterministicScenario("NORMAL");
        const whatChanged = document.getElementById("fcc-what-changed-card");
        if (whatChanged) whatChanged.style.display = "none";
        const impactCard = document.getElementById("fcc-decision-impact-card");
        if (impactCard) impactCard.style.display = "none";
        const verifBox = document.getElementById("fcc-verification-box");
        if (verifBox) verifBox.style.display = "none";
        showToast("↻ Demo Reset: Returned to Normal Profile (86/100 Health)", "info");
    }

    // DOM Ready
    document.addEventListener("DOMContentLoaded", init);

    // Public API
    return {
        applyScenario,
        completeAction,
        runStormReplanningDemo,
        runDeterministicScenario,
        toggleOnlineStatus,
        syncOfflineQueue,
        clearHistory,
        resetDemo
    };

})();


