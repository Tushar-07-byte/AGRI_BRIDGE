// ==============================================================================
// AGRIBRIDGE — ACTION PLAN TRACE & OBSERVABILITY CONTROLLER (action-plan-trace.js)
// ==============================================================================

const API_BASE = (window.location.origin && window.location.origin !== "null" && !window.location.origin.startsWith("file:"))
    ? window.location.origin
    : "http://127.0.0.1:8000";

let currentPlanId = null;
let currentActiveTaskId = null;

document.addEventListener("DOMContentLoaded", () => {
    // 1. Resolve Plan ID from URL or farmer's latest plan
    const urlParams = new URLSearchParams(window.location.search);
    const planIdParam = urlParams.get("id");

    if (planIdParam) {
        currentPlanId = parseInt(planIdParam);
        loadActionPlanTrace(currentPlanId);
    } else {
        fetchLatestFarmerPlan();
    }
});

async function fetchLatestFarmerPlan() {
    try {
        let farmerId = 1;
        if (window.AgriBridgeAuth && window.AgriBridgeAuth.getCurrentUser()) {
            farmerId = window.AgriBridgeAuth.getCurrentUser().id || 1;
        }

        const res = await fetch(`${API_BASE}/api/action-plans/${farmerId}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        if (data.action_plans && data.action_plans.length > 0) {
            currentPlanId = data.action_plans[0].id;
            loadActionPlanTrace(currentPlanId);
        } else {
            showEmptyTimeline("No action plans found for this account. Create a crop prediction to view its trace.");
        }
    } catch (err) {
        console.error("Failed to fetch farmer plans:", err);
        showEmptyTimeline("⚠️ Unable to connect to database — please verify your connection and try again.");
    }
}

async function loadActionPlanTrace(planId) {
    const streamContainer = document.getElementById("timeline-stream");
    if (!streamContainer) return;

    try {
        const res = await fetch(`${API_BASE}/api/action-plans/${planId}/trace`);
        if (!res.ok) {
            if (res.status === 404) {
                showEmptyTimeline(`Action Plan #${planId} does not exist.`);
                return;
            }
            throw new Error(`Server returned ${res.status}`);
        }

        const data = await res.json();
        renderTraceUI(data);

    } catch (err) {
        console.error("Failed to load trace:", err);
        showEmptyTimeline("⚠️ Unable to reach action plan service — please check your connection and try again.");
    }
}

function renderTraceUI(traceData) {
    // Update Header Metadata
    document.getElementById("plan-id-label").textContent = `#${traceData.action_plan_id}`;
    document.getElementById("plan-risk-badge").textContent = `Risk: ${traceData.current_risk_type || "N/A"}`;
    document.getElementById("plan-status-badge").textContent = `Status: ${traceData.current_status || "Active"}`;

    document.getElementById("meta-farmer-id").textContent = traceData.farmer_id || "1";
    document.getElementById("meta-created-at").textContent = traceData.created_at ? new Date(traceData.created_at).toLocaleString() : "--";
    document.getElementById("meta-updated-at").textContent = traceData.updated_at ? new Date(traceData.updated_at).toLocaleString() : "--";
    document.getElementById("meta-total-tasks").textContent = traceData.total_tasks_recorded || traceData.trace.length;

    const stream = document.getElementById("timeline-stream");
    stream.innerHTML = "";

    const events = traceData.trace || [];
    if (events.length === 0) {
        showEmptyTimeline("No timeline events recorded yet for this plan.");
        return;
    }

    events.forEach(evt => {
        const node = createTimelineNode(evt);
        stream.appendChild(node);
    });

    // Load and render multi-signal policy decision trace
    loadMultiSignalTrace(traceData.farmer_id || 1, traceData.crop_id || "wheat");
}

async function loadMultiSignalTrace(farmerId, cropId) {
    try {
        const res = await fetch(`${API_BASE}/api/orchestration/evaluate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ farmer_id: farmerId, crop: cropId })
        });
        if (!res.ok) return;
        const data = await res.json();

        // 1. Overview cards
        const riskEl = document.getElementById("trace-eval-risk");
        if (riskEl) {
            const risk = (data.overall_risk || "moderate").toUpperCase();
            riskEl.textContent = risk;
            riskEl.style.color = (risk === "CRITICAL" || risk === "HIGH") ? "#DC2626" : (risk === "MODERATE" ? "#D97706" : "#16A34A");
        }

        const constrEl = document.getElementById("trace-eval-constraints");
        if (constrEl) {
            const cList = data.constraints || [];
            constrEl.textContent = cList.length > 0 ? cList.join(", ") : "None (All Gates Clear)";
            constrEl.style.color = cList.length > 0 ? "#DC2626" : "#16A34A";
        }

        const escEl = document.getElementById("trace-eval-escalation");
        if (escEl) {
            escEl.textContent = data.escalation_required ? "🚨 Field Agent Review Required" : "🛡️ Farmer Autonomous Action";
            escEl.style.color = data.escalation_required ? "#DC2626" : "#059669";
        }

        // 2. Rules trace table
        const tbody = document.getElementById("trace-eval-rules-tbody");
        if (tbody && data.decision_trace) {
            tbody.innerHTML = data.decision_trace.map(t => `
                <tr>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #F1F5F9;"><code>${escapeHtml(t.signal)}</code></td>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #F1F5F9; font-weight: 600;">${escapeHtml(t.condition)}</td>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #F1F5F9; color: #64748B;">${escapeHtml(t.policy)}</td>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #F1F5F9; font-weight: 600; color: #0F172A;">${escapeHtml(t.effect)}</td>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #F1F5F9;"><span class="trace-chip-badge" style="font-size: 11px;">${escapeHtml(t.provenance)}</span></td>
                </tr>
            `).join("");
        }
    } catch (err) {
        console.warn("Could not load multi-signal trace:", err);
    }
}

function createTimelineNode(evt) {
    const node = document.createElement("div");
    node.className = "timeline-node";

    let markerClass = "marker-init";
    let markerIcon = "🌿";
    let cardClass = "";
    let badgeClass = "badge-init";
    let badgeLabel = evt.event_type;
    let title = evt.summary || "System Event";
    let contentHtml = "";

    if (evt.event_type === "PLAN_INITIALIZED") {
        markerIcon = "🌱";
        markerClass = "marker-init";
        badgeClass = "badge-init";
        badgeLabel = "Plan Initialized";
        title = "Diagnostic Assessment & Initial Baseline";
        contentHtml = `
            <p style="margin: 0; color: #334155; font-size: 14px;">
                ${escapeHtml(evt.summary)}
            </p>
        `;
    } else if (evt.event_type === "CALENDAR_SCHEDULED") {
        markerIcon = "🗓️";
        markerClass = "marker-init";
        badgeClass = "badge-init";
        badgeLabel = "Calendar Scheduled";
        title = "Dynamic Crop Journey Milestones";
        contentHtml = `
            <p style="margin: 0; color: #334155; font-size: 14px;">
                ${escapeHtml(evt.summary)}
            </p>
        `;
    } else if (evt.event_type === "NOTIFICATIONS_STAGED") {
        markerIcon = "🔔";
        markerClass = "marker-init";
        badgeClass = "badge-init";
        badgeLabel = "Notifications Staged";
        title = "Multichannel Reminders";
        contentHtml = `
            <p style="margin: 0; color: #334155; font-size: 14px;">
                ${escapeHtml(evt.summary)}
            </p>
        `;
    } else if (evt.event_type === "ESCALATION_EVALUATED") {
        markerIcon = evt.status === "ESCALATED" ? "🚨" : "🛡️";
        markerClass = evt.status === "ESCALATED" ? "marker-superseded" : "marker-done";
        badgeClass = evt.status === "ESCALATED" ? "badge-superseded" : "badge-done";
        badgeLabel = evt.status === "ESCALATED" ? "Field Agent Dispatched" : "Routine Monitoring";
        title = "Agronomic Risk & Escalation Policy";
        contentHtml = `
            <p style="margin: 0; color: #334155; font-size: 14px; font-weight: 600;">
                ${escapeHtml(evt.summary)}
            </p>
        `;
    } else if (evt.event_type === "ACTIVE_TASK_SCHEDULED") {
        markerIcon = "🎯";
        markerClass = "marker-active";
        cardClass = "card-active";
        badgeClass = "badge-active";
        badgeLabel = evt.task_status === "in_progress" ? "In Progress" : "Active Target Task";
        currentActiveTaskId = evt.task_id;
        title = `Task #${evt.task_id}: ${evt.task_title}`;
        contentHtml = `
            <div style="font-size: 13.5px; color: #1E293B; margin-bottom: 6px;">
                📅 <strong>Target Application Window:</strong> <span style="color: #15803D; font-weight: 700;">${evt.scheduled_for ? new Date(evt.scheduled_for).toLocaleString() : 'Immediate'}</span>
            </div>
            <div class="reasoning-box">
                <div class="reasoning-label">🧠 Autonomous Decision Reasoning:</div>
                <p class="reasoning-text">${escapeHtml(evt.reasoning || "Optimized for weather and disease characteristics.")}</p>
            </div>
            <div class="task-lifecycle-control" style="margin-top: 12px; display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px;">
                <span style="font-size: 12.5px; font-weight: 700; color: #334155;">
                    🎯 Task Lifecycle Status:
                </span>
                <select class="task-status-dropdown" onchange="window.updateTaskStatusManual(${evt.task_id}, this.value)" style="font-size: 12px; font-weight: 700; padding: 5px 10px; border-radius: 6px; border: 1.5px solid #0F5132; background: white; cursor: pointer; color: #0F5132;">
                    <option value="pending" ${(evt.task_status === "pending" || !evt.task_status) ? "selected" : ""}>⏳ Pending</option>
                    <option value="in_progress" ${evt.task_status === "in_progress" ? "selected" : ""}>⚡ In Progress</option>
                    <option value="done" ${evt.task_status === "done" ? "selected" : ""}>✅ Completed</option>
                </select>
            </div>
        `;
    } else if (evt.event_type === "TASK_SUPERSEDED") {
        markerIcon = "⚠️";
        markerClass = "marker-superseded";
        cardClass = "card-superseded";
        badgeClass = "badge-superseded";
        badgeLabel = "Invalidated / Superseded";
        title = `Task #${evt.task_id} (Superseded): ${evt.task_title}`;
        contentHtml = `
            <div style="font-size: 13px; color: #78350F; margin-bottom: 6px;">
                Previous Target: <span style="text-decoration: line-through;">${evt.scheduled_for ? new Date(evt.scheduled_for).toLocaleString() : 'N/A'}</span>
            </div>
            <div class="reasoning-box reasoning-amber">
                <div class="reasoning-label">⚡ Reason For Schedule Invalidation:</div>
                <p class="reasoning-text">${escapeHtml(evt.reasoning || "Forecast shifted significantly after formulation.")}</p>
            </div>
        `;
    } else if (evt.event_type === "REPLANNING_TRIGGERED") {
        markerIcon = "🔄";
        markerClass = "marker-replan";
        cardClass = "card-trigger";
        badgeClass = "badge-replan";
        badgeLabel = "Autonomous Replan";
        title = "Dynamic Orchestrator Adaptation";
        contentHtml = `
            <p style="margin: 0; color: #991B1B; font-size: 14px; font-weight: 600;">
                ${escapeHtml(evt.summary)}
            </p>
        `;
    } else if (evt.event_type === "TASK_COMPLETED") {
        markerIcon = "✅";
        markerClass = "marker-done";
        badgeClass = "badge-done";
        badgeLabel = "Completed";
        title = `Task #${evt.task_id} Completed`;
        contentHtml = `
            <p style="margin: 0 0 8px 0; color: #166534; font-size: 14px;">
                ${escapeHtml(evt.summary)} (Verified at: ${evt.completed_at ? new Date(evt.completed_at).toLocaleString() : 'Just now'})
            </p>
            <div class="task-lifecycle-control" style="margin-top: 8px; display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px;">
                <span style="font-size: 12.5px; font-weight: 700; color: #166534;">
                    🎯 Task Lifecycle Status:
                </span>
                <select class="task-status-dropdown" onchange="window.updateTaskStatusManual(${evt.task_id}, this.value)" style="font-size: 12px; font-weight: 700; padding: 5px 10px; border-radius: 6px; border: 1.5px solid #166534; background: white; cursor: pointer; color: #166534;">
                    <option value="pending" ${evt.task_status === "pending" ? "selected" : ""}>⏳ Pending</option>
                    <option value="in_progress" ${evt.task_status === "in_progress" ? "selected" : ""}>⚡ In Progress</option>
                    <option value="done" ${(evt.task_status === "done" || !evt.task_status) ? "selected" : ""}>✅ Completed</option>
                </select>
            </div>
        `;
    }

    node.innerHTML = `
        <div class="node-marker ${markerClass}">
            ${markerIcon}
        </div>
        <div class="node-card ${cardClass}">
            <div class="node-header">
                <div class="node-title-group">
                    <h3>${escapeHtml(title)}</h3>
                    <span class="node-timestamp">⏱️ ${evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : ''}</span>
                </div>
                <span class="node-badge ${badgeClass}">${badgeLabel}</span>
            </div>
            ${contentHtml}
        </div>
    `;

    return node;
}

function showEmptyTimeline(msg) {
    const stream = document.getElementById("timeline-stream");
    if (stream) {
        stream.innerHTML = `
            <div style="background: white; border: 1px dashed #CBD5E1; border-radius: 12px; padding: 30px; text-align: center; color: #64748B;">
                ${escapeHtml(msg)}
            </div>
        `;
    }
}

// ==============================================================================
// DEMO SIMULATION HANDLERS (FOR LIVE DEMOS & JUDGES)
// ==============================================================================

async function simulateWeatherShift(rainProb, conditionText, windowText) {
    if (!currentPlanId) {
        alert("No active plan selected.");
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/api/action-plans/${currentPlanId}/recheck`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                simulated_rain_probability: rainProb,
                simulated_weather_condition: conditionText,
                recommended_window: windowText,
                force_change: true
            })
        });

        const result = await res.json();
        if (result.success) {
            alert(`Autonomous Replanning Triggered!\n${result.message}`);
            loadActionPlanTrace(currentPlanId);
        } else {
            alert("Recheck returned: " + (result.message || "No change"));
        }
    } catch (e) {
        console.error("Simulation error:", e);
        alert("Failed to execute weather recheck.");
    }
}

async function markActiveTaskDone() {
    if (!currentActiveTaskId) {
        alert("No pending task found to mark as completed.");
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/api/plan-tasks/${currentActiveTaskId}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: "done" })
        });

        if (res.ok) {
            alert(`Task #${currentActiveTaskId} marked as completed!`);
            loadActionPlanTrace(currentPlanId);
        }
    } catch (e) {
        console.error("Error marking task done:", e);
    }
}

function triggerRecheckDemo() {
    simulateWeatherShift(85, "Heavy convective thunderstorm expected", "2026-09-08 (Sunny & Dry Window)");
}

// ==============================================================================
// MANUAL TASK LIFECYCLE CONTROLLER (PROMPT -1b)
// ==============================================================================

window.updateTaskStatusManual = async function (taskId, newStatus) {
    if (!taskId) return;
    try {
        const res = await fetch(`${API_BASE}/api/plan-tasks/${taskId}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: newStatus })
        });

        if (res.ok) {
            const data = await res.json();
            console.log(`Task #${taskId} successfully updated:`, data);
            // Re-render the trace immediately so changes reflect in UI
            if (currentPlanId) {
                loadActionPlanTrace(currentPlanId);
            }
        } else {
            alert(`Failed to update Task #${taskId} status.`);
        }
    } catch (err) {
        console.error("Task status update error:", err);
        alert("Unable to reach server to update task status.");
    }
};

function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

