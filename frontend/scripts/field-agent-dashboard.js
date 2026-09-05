// ==========================================================================
// AGRIBRIDGE — FIELD AGENT OPERATIONS HUB JAVASCRIPT
// ==========================================================================

// Guard page for field-agent role
if (window.AgriBridgeAuth) {
    window.AgriBridgeAuth.requireAuth(["field-agent"]);
}

console.log("=== FIELD AGENT OPERATIONS HUB INITIALIZING ===");

// Global state for filtering
let allPendingListings = [];
let allVerifiedListings = [];
let allVerifications = [];
let allEscalations = [];

// ==========================================================================
// 1. API CONFIGURATION
// ==========================================================================
const API_BASE_URL = window.location.origin;
const API_LISTINGS = `${API_BASE_URL}/api/listings/`;
const API_VERIFICATIONS = `${API_BASE_URL}/api/verifications/`;
const API_ESCALATIONS = `${API_BASE_URL}/api/action-plans/escalations/queue`;
const API_DISEASE_SCANS = `${API_BASE_URL}/api/verifications/disease-scans`;

// ==========================================================================
// 2. DASHBOARD INITIALIZATION
// ==========================================================================
async function loadDashboard() {
    await Promise.all([
        loadListingsAndVerifications(),
        loadEscalationsQueue(),
        loadDiseaseScansQueue(),
        loadFieldVisitsQueue()
    ]);
}


// ==========================================================================
// 3. LOAD LISTINGS & VERIFICATIONS
// ==========================================================================
async function loadListingsAndVerifications() {
    const pendingContainer = document.getElementById("pending-container");
    const verifiedContainer = document.getElementById("verified-container");

    try {
        const [listingsRes, verificationsRes] = await Promise.all([
            fetch(API_LISTINGS),
            fetch(API_VERIFICATIONS)
        ]);

        if (!listingsRes.ok) throw new Error(`Listings API error: ${listingsRes.status}`);
        if (!verificationsRes.ok) throw new Error(`Verifications API error: ${verificationsRes.status}`);

        const listingsData = await listingsRes.json();
        const verificationsData = await verificationsRes.json();

        const listings = Array.isArray(listingsData.listings) ? listingsData.listings : [];
        allVerifications = Array.isArray(verificationsData.verifications) ? verificationsData.verifications : [];

        // Partition listings into Pending, Verified, and Rejected
        allPendingListings = listings.filter(l => {
            const v = allVerifications.find(ver => String(ver.listing_id) === String(l.id));
            if (v) return v.status === "pending";
            return l.status === "pending";
        });

        allVerifiedListings = listings.filter(l => {
            const v = allVerifications.find(ver => String(ver.listing_id) === String(l.id));
            if (v) return v.status === "verified";
            return l.status === "verified";
        });

        const rejectedListings = listings.filter(l => {
            const v = allVerifications.find(ver => String(ver.listing_id) === String(l.id));
            if (v) return v.status === "rejected";
            return l.status === "rejected";
        });

        // Update KPI Counters
        const kpiPending = document.getElementById("kpi-pending");
        const kpiVerified = document.getElementById("kpi-verified");
        const kpiRejected = document.getElementById("kpi-rejected");

        if (kpiPending) kpiPending.textContent = allPendingListings.length;
        if (kpiVerified) kpiVerified.textContent = allVerifiedListings.length;
        if (kpiRejected) kpiRejected.textContent = rejectedListings.length;

        // Render Pending Crops
        renderPendingCrops(allPendingListings);

        // Render Verified Archive
        renderVerifiedArchive(allVerifiedListings);

    } catch (err) {
        console.error("Failed to load listings/verifications:", err);
        if (pendingContainer) {
            pendingContainer.innerHTML = `
                <div class="empty-state">
                    <p style="color: #EF4444; font-weight: 600;">⚠️ Unable to load crop submissions. Ensure the backend server is running.</p>
                </div>
            `;
        }
    }
}

// ==========================================================================
// 4. RENDER PENDING CROPS
// ==========================================================================
function renderPendingCrops(listings) {
    const container = document.getElementById("pending-container");
    if (!container) return;

    container.innerHTML = "";

    if (listings.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>🌱 No crop submissions currently awaiting verification.</p>
            </div>
        `;
        return;
    }

    listings.forEach(listing => {
        const verification = allVerifications.find(v => String(v.listing_id) === String(listing.id)) || { id: listing.id };
        const card = createPendingCard(listing, verification);
        container.appendChild(card);
    });
}

function createPendingCard(listing, verification) {
    const card = document.createElement("div");
    card.className = "pending-card";
    card.setAttribute("data-crop-name", (listing.crop_type || "").toLowerCase());

    const imageUrl = typeof getImageUrl === "function" 
        ? getImageUrl(listing.image_url || listing.photo_path) 
        : (listing.image_url ? `/${listing.image_url}` : "/frontend/assets/logo/logo.png");

    let confidenceVal = listing.confidence;
    let confidenceBadge = "";
    if (confidenceVal !== null && confidenceVal !== undefined) {
        let numericConf = Number(confidenceVal);
        if (numericConf <= 1.0) numericConf = numericConf * 100;
        const isHigh = numericConf >= 65.0;
        confidenceBadge = `<span class="confidence-chip ${isHigh ? 'high' : 'borderline'}">${numericConf.toFixed(1)}% ${isHigh ? 'High' : 'Review'}</span>`;
    } else {
        confidenceBadge = `<span class="confidence-chip borderline">N/A</span>`;
    }

    const harvestDate = listing.harvest_date ? String(listing.harvest_date).substring(0, 10) : "Not specified";
    const quantity = listing.quantity_est ? `${listing.quantity_est} kg` : "TBD";
    const price = listing.price_expected ? `₹${listing.price_expected}` : "Market Rate";

    card.innerHTML = `
        <img class="pending-image" src="${imageUrl}" alt="${listing.crop_type || 'Crop'}" onerror="this.src='/frontend/assets/logo/logo.png';">
        <div class="crop-card-header">
            <h3 class="crop-name">${listing.crop_type || "Crop Submission"}</h3>
            <span class="status-pill-pending">⏳ Pending</span>
        </div>
        <div class="crop-meta-list">
            <div class="meta-row">
                <span>Quantity:</span>
                <strong>${quantity}</strong>
            </div>
            <div class="meta-row">
                <span>Expected Harvest:</span>
                <strong>${harvestDate}</strong>
            </div>
            <div class="meta-row">
                <span>Expected Price:</span>
                <strong>${price}</strong>
            </div>
            <div class="meta-row">
                <span>AI Confidence:</span>
                <div>${confidenceBadge}</div>
            </div>
        </div>
        <button class="review-button" onclick="startCropReview(${listing.id}, ${verification.id || listing.id})">
            🔍 Review & Verify Crop
        </button>
    `;

    return card;
}

function startCropReview(listingId, verificationId) {
    const listing = allPendingListings.find(l => l.id === listingId);
    if (listing) {
        localStorage.setItem("listingId", String(listingId));
        localStorage.setItem("agentListing", JSON.stringify(listing));
    }
    window.location.href = `/frontend/pages/verification-review.html?listing_id=${listingId}&verification_id=${verificationId}`;
}

// ==========================================================================
// 5. RENDER VERIFIED ARCHIVE
// ==========================================================================
function renderVerifiedArchive(listings) {
    const container = document.getElementById("verified-container");
    if (!container) return;

    container.innerHTML = "";

    if (listings.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>No verified crops published yet.</p>
            </div>
        `;
        return;
    }

    listings.slice(0, 6).forEach(listing => {
        const card = document.createElement("div");
        card.className = "verified-card";

        const imageUrl = typeof getImageUrl === "function" 
            ? getImageUrl(listing.image_url || listing.photo_path) 
            : (listing.image_url ? `/${listing.image_url}` : "/frontend/assets/logo/logo.png");

        const harvestDate = listing.harvest_date ? String(listing.harvest_date).substring(0, 10) : "Verified";
        const quantity = listing.quantity_est ? `${listing.quantity_est} kg` : "--";

        card.innerHTML = `
            <img class="verified-image" src="${imageUrl}" alt="${listing.crop_type || 'Crop'}" onerror="this.src='/frontend/assets/logo/logo.png';">
            <div class="crop-card-header">
                <h3 class="crop-name">${listing.crop_type || "Verified Crop"}</h3>
                <span class="status-pill-verified">✓ Verified</span>
            </div>
            <div class="crop-meta-list">
                <div class="meta-row">
                    <span>Est. Quantity:</span>
                    <strong>${quantity}</strong>
                </div>
                <div class="meta-row">
                    <span>Harvest Date:</span>
                    <strong>${harvestDate}</strong>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

// ==========================================================================
// 6. LOAD AI ESCALATIONS QUEUE
// ==========================================================================
async function loadEscalationsQueue() {
    const container = document.getElementById("escalations-container");
    const kpiElem = document.getElementById("kpi-escalations");

    try {
        const res = await fetch(API_ESCALATIONS);
        if (!res.ok) throw new Error(`Escalations API error: ${res.status}`);

        const data = await res.json();
        allEscalations = Array.isArray(data.escalations) ? data.escalations : [];

        if (kpiElem) {
            kpiElem.textContent = allEscalations.length;
        }

        if (!container) return;
        container.innerHTML = "";

        if (allEscalations.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p style="color: #059669;">✅ No borderline AI escalations pending! All crop scans are within high confidence bounds.</p>
                </div>
            `;
            return;
        }

        allEscalations.forEach(esc => {
            const card = document.createElement("div");
            card.className = "escalation-card";

            const tasksCount = Array.isArray(esc.tasks) ? esc.tasks.length : 0;
            const reason = esc.escalation_reason || "Borderline AI confidence requires on-site agronomist review.";
            const dateStr = esc.created_at ? new Date(esc.created_at).toLocaleDateString() : "Recent";

            card.innerHTML = `
                <div class="esc-header">
                    <span class="esc-plan-id">Plan #${esc.id} • Farmer ID: ${esc.farmer_id}</span>
                    <span class="esc-badge">⚠️ ${esc.risk_type || "Borderline AI"}</span>
                </div>
                <h4 class="esc-title">Action Plan Escalation</h4>
                <p class="esc-reason">${reason}</p>
                <div class="esc-footer">
                    <span class="esc-time">📅 ${dateStr} • ${tasksCount} Pending Task(s)</span>
                    <a href="/frontend/pages/action-plan-trace.html" class="btn-inspect-esc">
                        ⚡ Inspect Plan
                    </a>
                </div>
            `;
            container.appendChild(card);
        });

    } catch (err) {
        console.error("Failed to load escalations queue:", err);
        if (kpiElem) kpiElem.textContent = "0";
        if (container) {
            container.innerHTML = `
                <div class="empty-state">
                    <p style="color: #64748B;">No escalations currently in queue.</p>
                </div>
            `;
        }
    }
}

// ==========================================================================
// 7. LOAD DISEASE DIAGNOSTIC SCANS (HITL)
// ==========================================================================
async function loadDiseaseScansQueue() {
    const container = document.getElementById("disease-container");
    const kpiElem = document.getElementById("kpi-disease-scans");

    try {
        const res = await fetch(`${API_DISEASE_SCANS}?status=PENDING_AGENT_REVIEW`);
        if (!res.ok) throw new Error(`Disease scans API error: ${res.status}`);

        const data = await res.json();
        const scans = Array.isArray(data.disease_scans) ? data.disease_scans : [];

        if (kpiElem) kpiElem.textContent = scans.length;
        if (!container) return;
        container.innerHTML = "";

        if (scans.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p style="color: #059669;">✅ No disease scans awaiting review! All diagnostic records are up to date.</p>
                </div>
            `;
            return;
        }

        scans.forEach(scan => {
            const card = document.createElement("div");
            card.className = "disease-card";

            let confNum = Number(scan.confidence) || 95.0;
            if (confNum <= 1.0) confNum = confNum * 100;

            const imgSrc = scan.image_url ? (scan.image_url.startsWith("http") ? scan.image_url : `/${scan.image_url}`) : "/frontend/assets/logo/logo.png";
            const dateStr = scan.created_at ? new Date(scan.created_at).toLocaleDateString() : "Today";

            card.innerHTML = `
                <img class="disease-card-img" src="${imgSrc}" alt="${scan.predicted_pathogen}" onerror="this.src='/frontend/assets/logo/logo.png';">
                <div class="crop-card-header">
                    <div>
                        <h3 class="crop-name" style="color:#065F46;">${scan.crop_type ? scan.crop_type.toUpperCase() : 'CROP'} — ${scan.predicted_pathogen}</h3>
                        <small style="color:#64748B;">Farmer ID: #${scan.farmer_id} • 📍 ${scan.geolocation || 'Raipur, CG'}</small>
                    </div>
                    <span class="status-pill-pending">⏳ PENDING</span>
                </div>
                <div class="crop-meta-list">
                    <div class="meta-row">
                        <span>AI Confidence:</span>
                        <strong style="color: ${confNum >= 75 ? '#059669' : '#D97706'}">${confNum.toFixed(1)}%</strong>
                    </div>
                    <div class="meta-row">
                        <span>Severity / Stage:</span>
                        <strong>${scan.severity || 'Moderate'} • ${scan.growth_stage || 'Flowering'}</strong>
                    </div>
                    <div class="meta-row">
                        <span>Proposed ICAR Chemical:</span>
                        <strong style="font-size:12px; color:#1E293B;">${scan.prescription_chemical || 'Mancozeb 75% WP'}</strong>
                    </div>
                    <div class="meta-row">
                        <span>Pre-Harvest Interval (PHI):</span>
                        <strong style="font-size:12px; color:#DC2626;">${scan.prescription_phi || '7-10 Days PHI'}</strong>
                    </div>
                </div>
                <div class="disease-card-actions">
                    <button class="btn-approve-rx" onclick="approveDiseaseScan(${scan.id})">
                        ✅ Approve (Issue Rx)
                    </button>
                    <button class="btn-reject-dispatch" onclick="rejectDiseaseScan(${scan.id})">
                        ❌ Reject (Dispatch Visit)
                    </button>
                </div>
            `;
            container.appendChild(card);
        });

    } catch (err) {
        console.error("Failed to load disease scans:", err);
        if (kpiElem) kpiElem.textContent = "0";
        if (container) {
            container.innerHTML = `
                <div class="empty-state">
                    <p style="color:#64748B;">Unable to load disease scans.</p>
                </div>
            `;
        }
    }
}

// ==========================================================================
// 8. APPROVE DISEASE SCAN (Action APPROVE)
// ==========================================================================
async function approveDiseaseScan(recordId) {
    if (!confirm("Confirm approval of this diagnosis? This will issue an ICAR-compliant prescription to the farmer and update crop health records. (Zero marketplace impact).")) {
        return;
    }

    try {
        const res = await fetch(`${API_DISEASE_SCANS}/${recordId}/approve`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                agent_name: "Field Agent Rahul (Agri-Student)",
                remarks: "Diagnosis and foliage lesions verified. ICAR agronomic prescription authorized."
            })
        });

        const data = await res.json();
        if (!res.ok || !data.success) {
            throw new Error(data.detail || "Approval failed");
        }

        alert(`✅ Approved!\nPrescription issued: ${data.prescription ? data.prescription.chemical_name : 'Authorized'}\nFarmer Notification: ${data.notification ? data.notification.title : 'Sent'}`);
        await Promise.all([
            loadDiseaseScansQueue(),
            loadFieldVisitsQueue()
        ]);

    } catch (err) {
        console.error("Approve disease scan failed:", err);
        alert(`⚠️ Approval Error: ${err.message}`);
    }
}

// ==========================================================================
// 9. REJECT DISEASE SCAN (Action REJECT)
// ==========================================================================
async function rejectDiseaseScan(recordId) {
    const reason = prompt(
        "Enter reason for physical dispatch / on-site audit:",
        "Symptom presentation ambiguous. Leaf lesions require in-person inspection."
    );

    if (reason === null) return;

    try {
        const res = await fetch(`${API_DISEASE_SCANS}/${recordId}/reject`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                agent_name: "Field Agent Rahul (Agri-Student)",
                reason: reason
            })
        });

        const data = await res.json();
        if (!res.ok || !data.success) {
            throw new Error(data.detail || "Rejection failed");
        }

        alert(`🚨 Case Moved to Pending Field Visits!\nDispatch Status: PENDING_FIELD_DISPATCH\nFarmer notified: "Your disease scan requires on-site verification. An Agri-Student Agent has been assigned to visit your field."`);
        await Promise.all([
            loadDiseaseScansQueue(),
            loadFieldVisitsQueue()
        ]);

    } catch (err) {
        console.error("Reject disease scan failed:", err);
        alert(`⚠️ Rejection Error: ${err.message}`);
    }
}

// ==========================================================================
// 10. LOAD PENDING FIELD VISITS QUEUE
// ==========================================================================
async function loadFieldVisitsQueue() {
    const container = document.getElementById("field-visits-container");
    const kpiElem = document.getElementById("kpi-field-visits");

    try {
        const res = await fetch(`${API_DISEASE_SCANS}?status=NEEDS_PHYSICAL_VISIT`);
        if (!res.ok) throw new Error(`Field visits API error: ${res.status}`);

        const data = await res.json();
        const visits = Array.isArray(data.disease_scans) ? data.disease_scans : [];

        if (kpiElem) kpiElem.textContent = visits.length;
        if (!container) return;
        container.innerHTML = "";

        if (visits.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p style="color: #059669;">✅ No pending on-site visits required! All farms are cleared.</p>
                </div>
            `;
            return;
        }

        visits.forEach(visit => {
            const card = document.createElement("div");
            card.className = "visit-card";

            const dateStr = visit.verified_at ? new Date(visit.verified_at).toLocaleDateString() : "Recent";
            const inspDateStr = visit.inspection_date ? new Date(visit.inspection_date).toLocaleDateString() : "Tomorrow";
            const inspStatus = visit.inspection_status || "SCHEDULED";

            let statusBadge = `<span class="esc-badge" style="background:#FEE2E2; color:#991B1B; border:1px solid #FECACA;">🚨 ON-SITE AUDIT</span>`;
            if (inspStatus === "CONFIRMED") {
                statusBadge = `<span class="esc-badge" style="background:#DCFCE7; color:#166534; border:1px solid #BBF7D0;">✅ FARMER CONFIRMED</span>`;
            } else if (inspStatus === "RESCHEDULED") {
                statusBadge = `<span class="esc-badge" style="background:#FEF3C7; color:#92400E; border:1px solid #FDE68A;">📅 RESCHEDULED BY FARMER</span>`;
            } else if (inspStatus === "REJECTED") {
                statusBadge = `<span class="esc-badge" style="background:#F1F5F9; color:#64748B; border:1px solid #E2E8F0;">❌ DECLINED BY FARMER</span>`;
            }

            card.innerHTML = `
                <div class="esc-header">
                    <span class="esc-plan-id" style="color:#991B1B;">Farm Audit #${visit.id} • Farmer ID: ${visit.farmer_id}</span>
                    ${statusBadge}
                </div>
                <h4 class="esc-title" style="margin:0; color:#1E293B;">${(visit.crop_type || 'Crop').toUpperCase()} — ${visit.predicted_pathogen}</h4>
                <p class="esc-reason" style="margin:0; color:#7F1D1D;">${visit.agent_remarks || 'Physical on-site leaf inspection required.'}</p>
                ${visit.farmer_notes ? `<p style="margin:4px 0 0 0; font-size:12px; color:#475569; background:#F8FAFC; padding:4px 8px; border-radius:6px;">💬 <strong>Farmer Note:</strong> ${visit.farmer_notes}</p>` : ''}
                <div class="esc-footer">
                    <span class="esc-time">📍 ${visit.geolocation || 'India'} • <strong>Visit: ${inspDateStr}</strong></span>
                    <a href="/frontend/pages/field-agent-map.html" class="btn-inspect-esc" style="background:#991B1B; color:#FFFFFF; padding:6px 14px; border-radius:12px; text-decoration:none; font-size:12px; font-weight:700;">
                        🗺️ View on Map
                    </a>
                </div>
            `;
            container.appendChild(card);
        });

    } catch (err) {
        console.error("Failed to load field visits queue:", err);
        if (kpiElem) kpiElem.textContent = "0";
        if (container) {
            container.innerHTML = `
                <div class="empty-state">
                    <p style="color:#64748B;">No pending field visits.</p>
                </div>
            `;
        }
    }
}

// ==========================================================================
// 11. CLIENT-SIDE SEARCH FILTER
// ==========================================================================
function filterCropCards() {
    const input = document.getElementById("cropSearchInput");
    if (!input) return;

    const term = input.value.trim().toLowerCase();
    const cards = document.querySelectorAll("#pending-container .pending-card");

    cards.forEach(card => {
        const cropName = card.getAttribute("data-crop-name") || "";
        const cardText = card.textContent.toLowerCase();
        if (cropName.includes(term) || cardText.includes(term)) {
            card.style.display = "flex";
        } else {
            card.style.display = "none";
        }
    });
}

// Start loading when DOM is ready
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadDashboard);
} else {
    loadDashboard();
}

