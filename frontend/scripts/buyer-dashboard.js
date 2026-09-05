// ==============================================================================
// AGRIBRIDGE — BUYER DASHBOARD CONTROLLER (buyer-dashboard.js)
// Agrova Modern Dark Forest Design System
// ==============================================================================

const API_BASE = window.location.origin;

// Determine current buyer identity
let BUYER_ID = 101;
let currentBuyerName = "Verified Buyer";

if (window.AgriBridgeAuth) {
    window.AgriBridgeAuth.requireAuth(["buyer"]);
    const currentUser = window.AgriBridgeAuth.getCurrentUser();
    if (currentUser && currentUser.id) {
        BUYER_ID = currentUser.id;
        if (currentUser.name) {
            currentBuyerName = currentUser.name;
        }
    }
}

// Update Buyer Badge in Navbar
document.addEventListener("DOMContentLoaded", function () {
    const badgeElem = document.getElementById("buyer-badge");
    const statusText = document.getElementById("buyer-status-text");
    if (badgeElem && currentBuyerName) {
        badgeElem.innerHTML = `🛒 ${currentBuyerName}`;
    }
    if (statusText && currentBuyerName) {
        statusText.innerHTML = `Account: <strong>${currentBuyerName} • Active</strong>`;
    }
});

// Cache for client-side search & filtering
let allVerifiedListings = [];
let allBuyerOrders = [];
let committedListingIds = new Set();

// ==============================================================================
// 1. INITIALIZE DATA ON LOAD
// ==============================================================================

async function initBuyerDashboard() {
    await Promise.all([
        loadVerifiedListings(),
        loadMyOrders()
    ]);
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initBuyerDashboard);
} else {
    initBuyerDashboard();
}

// ==============================================================================
// 2. LOAD VERIFIED LISTINGS FROM BACKEND
// ==============================================================================

async function loadVerifiedListings() {
    const listingsContainer = document.getElementById("listings-container");
    const kpiLots = document.getElementById("kpi-available-lots");
    const kpiVolume = document.getElementById("kpi-total-volume");

    try {
        // Fetch verified listings
        const listingsRes = await fetch(`${API_BASE}/api/listings/marketplace`);
        if (!listingsRes.ok) throw new Error(`Marketplace API error: ${listingsRes.status}`);

        const listingsData = await listingsRes.json();
        allVerifiedListings = Array.isArray(listingsData.listings) ? listingsData.listings : [];

        // Fetch orders to determine committed state
        const ordersRes = await fetch(`${API_BASE}/api/orders/`);
        if (ordersRes.ok) {
            const ordersData = await ordersRes.json();
            allBuyerOrders = Array.isArray(ordersData.orders) ? ordersData.orders : [];
            committedListingIds.clear();
            allBuyerOrders.forEach(function (order) {
                if (order.buyer_id === BUYER_ID) {
                    committedListingIds.add(order.listing_id);
                }
            });
        }

        // Update KPIs
        if (kpiLots) {
            kpiLots.textContent = allVerifiedListings.length;
        }

        if (kpiVolume) {
            const totalKg = allVerifiedListings.reduce((sum, item) => sum + (Number(item.quantity_est) || 0), 0);
            if (totalKg >= 1000) {
                kpiVolume.textContent = `${(totalKg / 100).toFixed(1)} Qtl`;
            } else {
                kpiVolume.textContent = `${totalKg.toLocaleString()} kg`;
            }
        }

        // Render Cards
        renderListings(allVerifiedListings);

    } catch (error) {
        console.error("Failed to load verified listings:", error);
        if (listingsContainer) {
            listingsContainer.innerHTML = `
                <div class="empty-state">
                    <p style="color: #64748B;">⚠️ Unable to reach marketplace service — please verify backend connection and try again.</p>
                </div>
            `;
        }
    }
}

// ==============================================================================
// 3. RENDER LISTING CARDS
// ==============================================================================

function renderListings(listings) {
    const listingsContainer = document.getElementById("listings-container");
    if (!listingsContainer) return;

    listingsContainer.innerHTML = "";

    if (!listings || listings.length === 0) {
        showEmptyMessage();
        return;
    }

    listings.forEach(function (listing) {
        const isCommitted = committedListingIds.has(listing.id);
        createCropCard(listing, isCommitted);
    });
}

function showEmptyMessage() {
    const listingsContainer = document.getElementById("listings-container");
    if (!listingsContainer) return;
    const msg = typeof translate === "function" ? translate("buyer.dashboard.noVerifiedCrops") : "No verified crops available in marketplace yet.";
    listingsContainer.innerHTML = `
        <div class="empty-state">
            <span style="font-size: 32px;">🌾</span>
            <p>${msg}</p>
        </div>
    `;
}

// ==============================================================================
// 4. CREATE CROP CARD
// ==============================================================================

function createCropCard(listing, isCommitted) {
    const listingsContainer = document.getElementById("listings-container");
    if (!listingsContainer) return;

    const card = document.createElement("div");
    card.classList.add("crop-card");
    card.setAttribute("data-crop-type", (listing.crop_type || "").toLowerCase());
    card.setAttribute("data-listing-id", listing.id);

    // Image URL with fallback
    let imgSrc = "/frontend/assets/icons/pre-harvest.png";
    if (listing.photo_path) {
        imgSrc = typeof getImageUrl === "function" ? getImageUrl(listing.photo_path) : `/${listing.photo_path}`;
    }

    // Top verified badge
    const topBadge = document.createElement("span");
    topBadge.className = "card-top-badge";
    topBadge.textContent = "✓ AGENT VERIFIED";

    // Image Wrapper
    const imgWrapper = document.createElement("div");
    imgWrapper.className = "card-img-wrapper";

    const image = document.createElement("img");
    image.src = imgSrc;
    image.alt = listing.crop_type || "Crop";
    image.onerror = function () {
        this.src = "/frontend/assets/icons/pre-harvest.png";
    };

    imgWrapper.appendChild(image);
    imgWrapper.appendChild(topBadge);

    // Header Row: Crop Title & Farmer Info
    const headerRow = document.createElement("div");
    headerRow.className = "card-header-row";

    const titleGroup = document.createElement("div");
    const name = document.createElement("h3");
    name.textContent = (listing.crop_type || "Verified Crop").toUpperCase();

    const farmerSub = document.createElement("p");
    farmerSub.className = "crop-farmer-sub";
    farmerSub.textContent = `Lot #${listing.id} • Farmer #${listing.farmer_id || 'N/A'}`;

    titleGroup.appendChild(name);
    titleGroup.appendChild(farmerSub);

    // Status Pill
    const badge = document.createElement("span");
    badge.textContent = typeof translate === "function" ? translate("buyer.dashboard.verifiedBadge") : "✓ Field Verified";
    badge.classList.add("verified-badge");

    headerRow.appendChild(titleGroup);
    headerRow.appendChild(badge);

    // Metadata Grid (2-column matrix)
    const metaGrid = document.createElement("div");
    metaGrid.className = "crop-meta-grid";

    // Quantity
    const qtyVal = Number(listing.quantity_est) || 0;
    const qtyDisplay = qtyVal >= 100 ? `${(qtyVal / 100).toFixed(1)} Qtl (${qtyVal} kg)` : `${qtyVal} kg`;
    const qtyItem = document.createElement("div");
    qtyItem.className = "meta-item";
    qtyItem.innerHTML = `
        <span class="meta-label">${typeof translate === "function" ? translate("buyer.dashboard.quantity") : "Quantity"}</span>
        <span class="meta-value highlight-green">📦 ${qtyDisplay}</span>
    `;

    // Harvest Date
    const hDate = listing.harvest_date || "Within 15 Days";
    const dateItem = document.createElement("div");
    dateItem.className = "meta-item";
    dateItem.innerHTML = `
        <span class="meta-label">${typeof translate === "function" ? translate("buyer.dashboard.expectedHarvest") : "Expected Harvest"}</span>
        <span class="meta-value">📅 ${hDate}</span>
    `;

    // Health Status
    const healthStatus = listing.health_status || "Optimal Stand (Grade A)";
    const healthItem = document.createElement("div");
    healthItem.className = "meta-item";
    healthItem.innerHTML = `
        <span class="meta-label">${typeof translate === "function" ? translate("buyer.dashboard.health") : "Health Stand"}</span>
        <span class="meta-value">🌿 ${healthStatus}</span>
    `;

    // Verified By
    const agentName = listing.agent_name || "Rahul (Field Agronomist)";
    const agentItem = document.createElement("div");
    agentItem.className = "meta-item";
    agentItem.innerHTML = `
        <span class="meta-label">Inspected By</span>
        <span class="meta-value highlight-gold">👨‍🌾 ${agentName}</span>
    `;

    metaGrid.appendChild(qtyItem);
    metaGrid.appendChild(dateItem);
    metaGrid.appendChild(healthItem);
    metaGrid.appendChild(agentItem);

    // Commit Action Button
    const commitButton = document.createElement("button");
    commitButton.type = "button";
    commitButton.classList.add("commit-button");

    // Commitment Message Box
    const commitmentMessage = document.createElement("div");
    commitmentMessage.classList.add("commitment-message");
    const commitTitle = typeof translate === "function" ? translate("buyer.dashboard.purchaseCommittedTitle") : "Purchase Committed!";
    const commitDesc = typeof translate === "function" ? translate("buyer.dashboard.purchaseCommittedDesc") : "Forward agreement sent to farmer. Dispatch schedule queued.";
    commitmentMessage.innerHTML = `
        <div class="success-icon">✓</div>
        <div>
            <h3>${commitTitle}</h3>
            <p>${commitDesc}</p>
        </div>
    `;

    // Button state
    if (isCommitted) {
        commitButton.textContent = typeof translate === "function" ? translate("buyer.dashboard.purchaseCommitted") : "✓ Purchase Committed";
        commitButton.disabled = true;
    } else {
        commitButton.textContent = typeof translate === "function" ? translate("buyer.dashboard.commitToBuy") : "Commit to Buy (Forward Order)";
    }

    commitButton.addEventListener("click", function () {
        handleCommitToBuy(listing, commitButton, commitmentMessage);
    });

    // Hidden backward-compatibility elements for any older automated queries
    const hiddenQuantity = document.createElement("p");
    hiddenQuantity.style.display = "none";
    hiddenQuantity.textContent = `${typeof translate === "function" ? translate("buyer.dashboard.quantity") : "Quantity:"} ${listing.quantity_est || 0} kg`;

    const hiddenHarvest = document.createElement("p");
    hiddenHarvest.style.display = "none";
    hiddenHarvest.textContent = `${typeof translate === "function" ? translate("buyer.dashboard.expectedHarvest") : "Expected Harvest:"} ${listing.harvest_date || "Not available"}`;

    const hiddenHealth = document.createElement("p");
    hiddenHealth.style.display = "none";
    hiddenHealth.textContent = `${typeof translate === "function" ? translate("buyer.dashboard.health") : "Health:"} ${listing.health_status || "Unknown"}`;

    // Assemble Card
    card.appendChild(imgWrapper);
    card.appendChild(headerRow);
    card.appendChild(metaGrid);
    card.appendChild(commitButton);
    card.appendChild(commitmentMessage);
    card.appendChild(hiddenQuantity);
    card.appendChild(hiddenHarvest);
    card.appendChild(hiddenHealth);

    listingsContainer.appendChild(card);
}

// ==============================================================================
// 5. COMMIT TO BUY HANDLER
// ==============================================================================

async function handleCommitToBuy(listing, commitButton, commitmentMessage) {
    console.log("Commit to Buy clicked for listing:", listing.id);

    commitButton.disabled = true;
    commitButton.textContent = typeof translate === "function" ? translate("buyer.dashboard.processing") : "Processing Order...";

    try {
        const response = await fetch(`${API_BASE}/api/orders/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                listing_id: listing.id,
                buyer_id: BUYER_ID
            })
        });

        const data = await response.json();

        if (!response.ok) {
            alert(data.detail || "Failed to commit purchase. Only verified listings can be ordered.");
            commitButton.disabled = false;
            commitButton.textContent = "Commit to Buy";
            return;
        }

        // Update state
        committedListingIds.add(listing.id);

        // Success: update button and reveal commitment banner
        commitButton.textContent = typeof translate === "function" ? translate("buyer.dashboard.purchaseCommitted") : "✓ Purchase Committed";
        commitButton.disabled = true;
        commitmentMessage.style.display = "flex";

        // Refresh orders section and KPI
        await loadMyOrders();

    } catch (err) {
        console.error("Error creating order:", err);
        alert("Failed to commit purchase due to network error.");
        commitButton.disabled = false;
        commitButton.textContent = "Commit to Buy";
    }
}

// ==============================================================================
// 6. LOAD MY ORDERS SECTION
// ==============================================================================

async function loadMyOrders() {
    const ordersContainer = document.getElementById("orders-container");
    const kpiOrders = document.getElementById("kpi-my-orders");

    try {
        const res = await fetch(`${API_BASE}/api/orders/`);
        if (!res.ok) throw new Error(`Orders API error: ${res.status}`);

        const data = await res.json();
        const orders = Array.isArray(data.orders) ? data.orders : [];

        // Filter orders for this buyer
        const myOrders = orders.filter(o => o.buyer_id === BUYER_ID);

        if (kpiOrders) {
            kpiOrders.textContent = myOrders.length;
        }

        if (!ordersContainer) return;
        ordersContainer.innerHTML = "";

        if (myOrders.length === 0) {
            ordersContainer.innerHTML = `
                <div class="empty-state">
                    <span style="font-size: 32px;">🤝</span>
                    <p>No active purchase commitments yet. Browse verified lots above to place direct orders.</p>
                </div>
            `;
            return;
        }

        myOrders.forEach(order => {
            const card = document.createElement("div");
            card.className = "order-card";

            const dateStr = order.committed_at ? new Date(order.committed_at).toLocaleDateString() : "Recent";

            // Find matching listing info if available in cache
            const matchingListing = allVerifiedListings.find(l => l.id === order.listing_id);
            const cropName = matchingListing ? matchingListing.crop_type.toUpperCase() : "AGRI LOT";
            const qtyStr = matchingListing ? `${matchingListing.quantity_est} kg` : "Standard Lot";
            const farmerIdStr = matchingListing ? `#${matchingListing.farmer_id}` : "Registered";

            card.innerHTML = `
                <div class="order-header">
                    <span class="order-id">Contract #${order.id} • Lot #${order.listing_id}</span>
                    <span class="order-badge">✓ COMMITTED</span>
                </div>
                <h4 class="order-title">📦 ${cropName}</h4>
                <div class="order-meta-list">
                    <div class="order-meta-row">
                        <span>Contract Volume:</span>
                        <strong>${qtyStr}</strong>
                    </div>
                    <div class="order-meta-row">
                        <span>Contract Date:</span>
                        <strong>${dateStr}</strong>
                    </div>
                    <div class="order-meta-row">
                        <span>Farmer Partner:</span>
                        <strong>Farmer ${farmerIdStr}</strong>
                    </div>
                    <div class="order-meta-row">
                        <span>Dispatch Stage:</span>
                        <strong style="color: #059669;">Pending Harvest Fulfillment</strong>
                    </div>
                </div>
            `;
            ordersContainer.appendChild(card);
        });

    } catch (err) {
        console.error("Failed to load my orders:", err);
        if (kpiOrders) kpiOrders.textContent = "0";
        if (ordersContainer) {
            ordersContainer.innerHTML = `
                <div class="empty-state">
                    <p style="color: #64748B;">Unable to load order history.</p>
                </div>
            `;
        }
    }
}

// ==============================================================================
// 7. CLIENT-SIDE SEARCH & FILTER
// ==============================================================================

function filterListings() {
    const searchInput = document.getElementById("cropSearchInput");
    const filterSelect = document.getElementById("cropTypeFilter");

    const term = searchInput ? searchInput.value.trim().toLowerCase() : "";
    const selectedType = filterSelect ? filterSelect.value.trim().toLowerCase() : "";

    const cards = document.querySelectorAll("#listings-container .crop-card");

    cards.forEach(card => {
        const cropType = card.getAttribute("data-crop-type") || "";
        const cardText = card.textContent.toLowerCase();

        const matchesSearch = !term || cardText.includes(term) || cropType.includes(term);
        const matchesType = !selectedType || cropType.includes(selectedType);

        if (matchesSearch && matchesType) {
            card.style.display = "flex";
        } else {
            card.style.display = "none";
        }
    });
}
