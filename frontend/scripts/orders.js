// =========================================
// AGRIBRIDGE — FARMER ORDERS & COMMITMENTS (orders.js)
// =========================================

const ordersContainer = document.getElementById("orders-container");
const dashboardButton = document.getElementById("dashboard-button");

if (dashboardButton) {
    dashboardButton.addEventListener("click", function () {
        window.location.href = "/frontend/pages/farmer-dashboard.html";
    });
}

// Initialize page
document.addEventListener("DOMContentLoaded", initOrdersPage);
if (document.readyState !== "loading") {
    initOrdersPage();
}

async function initOrdersPage() {
    if (!ordersContainer) return;

    const urlParams = new URLSearchParams(window.location.search);
    const orderIdParam = urlParams.get("order_id");

    ordersContainer.innerHTML = `<div style="text-align: center; padding: 40px; color: #64748B;">Loading buyer commitment contracts...</div>`;

    let ordersRendered = 0;

    // 1. Fetch from live Backend Orders API
    try {
        const currentUser = (window.AgriBridgeAuth && window.AgriBridgeAuth.getCurrentUser) ? window.AgriBridgeAuth.getCurrentUser() : null;
        let url = "/api/orders/";
        if (orderIdParam) {
            url = `/api/orders/${orderIdParam}`;
        } else if (currentUser && currentUser.id) {
            url = `/api/orders/farmer/${currentUser.id}`;
        }

        const res = await fetch(url);
        if (res.ok) {
            const data = await res.json();
            const orderList = data.order ? [data.order] : (data.orders || []);
            if (orderList.length > 0) {
                ordersContainer.innerHTML = "";
                orderList.forEach(order => {
                    createDbOrderCard(order);
                    ordersRendered++;
                });
            }
        }
    } catch (e) {
        console.warn("Unable to fetch backend orders:", e);
    }

    // 2. Check localStorage fallback if no DB orders found
    if (ordersRendered === 0) {
        const savedCropData = localStorage.getItem("cropData");
        const savedCropImage = localStorage.getItem("cropImage");
        const buyerCommitment = localStorage.getItem("buyerCommitment");

        if (savedCropData && buyerCommitment === "true") {
            try {
                const cropData = JSON.parse(savedCropData);
                if (cropData.status === "committed") {
                    ordersContainer.innerHTML = "";
                    createOrderCard(cropData, savedCropImage);
                    ordersRendered++;
                }
            } catch (e) {}
        }
    }

    // 3. If none found, show empty state
    if (ordersRendered === 0) {
        showEmptyMessage();
    }
}

// =========================================
// CREATE DB ORDER CARD
// =========================================

function createDbOrderCard(order) {
    const card = document.createElement("div");
    card.classList.add("order-card");

    // Image
    let imgSrc = "/frontend/assets/logo/logo.png";
    if (order.photo_path) {
        imgSrc = typeof getImageUrl === "function" ? getImageUrl(order.photo_path) : `/${order.photo_path}`;
    }
    const img = document.createElement("img");
    img.src = imgSrc;
    img.alt = order.crop_type || "Crop";
    img.onerror = function () { this.src = "/frontend/assets/logo/logo.png"; };
    img.classList.add("order-image");
    card.appendChild(img);

    // Details
    const details = document.createElement("div");
    details.classList.add("order-details");

    const title = document.createElement("h2");
    title.textContent = `🎉 Purchase Contract #${order.id}`;

    const cropName = document.createElement("p");
    cropName.innerHTML = `<strong>Crop:</strong> ${order.crop_type}`;

    const buyerInfo = document.createElement("p");
    buyerInfo.innerHTML = `<strong>Buyer Partner:</strong> ${order.buyer_name}`;

    const quantity = document.createElement("p");
    quantity.innerHTML = `<strong>Committed Quantity:</strong> ${order.quantity} Quintals`;

    const price = document.createElement("p");
    price.innerHTML = `<strong>Agreed Benchmark Rate:</strong> ${order.price}`;

    const harvestDate = document.createElement("p");
    harvestDate.innerHTML = `<strong>Expected Harvest Window:</strong> ${order.harvest_date}`;

    const committedDate = document.createElement("p");
    const formattedDate = order.committed_at ? new Date(order.committed_at).toLocaleDateString() : "Active Contract";
    committedDate.innerHTML = `<strong>Contract Signed:</strong> ${formattedDate}`;

    const status = document.createElement("span");
    status.textContent = `✓ ${order.status}`;
    status.classList.add("order-status");

    details.appendChild(title);
    details.appendChild(cropName);
    details.appendChild(buyerInfo);
    details.appendChild(quantity);
    details.appendChild(price);
    details.appendChild(harvestDate);
    details.appendChild(committedDate);
    details.appendChild(status);

    card.appendChild(details);
    ordersContainer.appendChild(card);
}

// =========================================
// CREATE LOCAL STORAGE ORDER CARD (Backward Compatibility)
// =========================================

function createOrderCard(cropData, imageData) {
    const orderCard = document.createElement("div");
    orderCard.classList.add("order-card");

    if (imageData) {
        const image = document.createElement("img");
        image.src = imageData;
        image.alt = cropData.cropName || "Crop";
        image.classList.add("order-image");
        orderCard.appendChild(image);
    }

    const details = document.createElement("div");
    details.classList.add("order-details");

    const title = document.createElement("h2");
    title.textContent = typeof translate === "function" ? translate("orders.newBuyerCommitment") : "🎉 New Buyer Commitment";

    const cropName = document.createElement("p");
    const cropLabel = typeof translate === "function" ? translate("orders.crop") : "Crop:";
    cropName.innerHTML = `<strong>${cropLabel}</strong> ${cropData.cropName || "Crop"}`;

    const quantity = document.createElement("p");
    const qtyLabel = typeof translate === "function" ? translate("orders.quantity") : "Quantity:";
    quantity.innerHTML = `<strong>${qtyLabel}</strong> ${cropData.quantity || 50} kg`;

    const location = document.createElement("p");
    const locLabel = typeof translate === "function" ? translate("orders.farmLocation") : "Farm Location:";
    location.innerHTML = `<strong>${locLabel}</strong> ${cropData.location || "Local Plot"}`;

    const harvestDate = document.createElement("p");
    const harvestLabel = typeof translate === "function" ? translate("orders.expectedHarvest") : "Expected Harvest:";
    harvestDate.innerHTML = `<strong>${harvestLabel}</strong> ${cropData.harvestDate || "Next Month"}`;

    const status = document.createElement("span");
    status.textContent = typeof translate === "function" ? translate("orders.buyerCommitted") : "✓ Buyer Committed";
    status.classList.add("order-status");

    details.appendChild(title);
    details.appendChild(cropName);
    details.appendChild(quantity);
    details.appendChild(location);
    details.appendChild(harvestDate);
    details.appendChild(status);

    orderCard.appendChild(details);
    ordersContainer.appendChild(orderCard);
}

// =========================================
// EMPTY STATE
// =========================================

function showEmptyMessage() {
    const message = document.createElement("div");
    message.classList.add("empty-message");
    message.textContent = typeof translate === "function" ? translate("orders.noCommitments") : "No buyer commitments yet.";
    ordersContainer.appendChild(message);
}