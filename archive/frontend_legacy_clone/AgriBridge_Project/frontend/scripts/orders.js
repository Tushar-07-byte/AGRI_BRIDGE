// =========================================
// FARMER COMMITMENTS
// =========================================


// =========================================
// GET HTML ELEMENTS
// =========================================

const ordersContainer =
    document.getElementById("orders-container");

const dashboardButton =
    document.getElementById("dashboard-button");


// =========================================
// GET SAVED DATA
// =========================================

const savedCropData =
    localStorage.getItem("cropData");

const savedCropImage =
    localStorage.getItem("cropImage");

const buyerCommitment =
    localStorage.getItem("buyerCommitment");


// =========================================
// CHECK COMMITMENT
// =========================================

if (
    savedCropData &&
    buyerCommitment === "true"
) {

    const cropData =
        JSON.parse(savedCropData);

    if (cropData.status === "committed") {

        createOrderCard(
            cropData,
            savedCropImage
        );

    } else {

        showEmptyMessage();

    }

} else {

    showEmptyMessage();

}


// =========================================
// CREATE ORDER CARD
// =========================================

function createOrderCard(cropData, imageData) {

    // =====================================
    // MAIN CARD
    // =====================================

    const orderCard =
        document.createElement("div");

    orderCard.classList.add("order-card");


    // =====================================
    // CROP IMAGE
    // =====================================

    if (imageData) {

        const image =
            document.createElement("img");

        image.src = imageData;

        image.alt =
            cropData.cropName;

        image.classList.add("order-image");

        orderCard.appendChild(image);

    }


    // =====================================
    // DETAILS CONTAINER
    // =====================================

    const details =
        document.createElement("div");

    details.classList.add("order-details");


    // =====================================
    // TITLE
    // =====================================

    const title =
        document.createElement("h2");

    title.textContent =
        typeof translate === "function" ? translate("orders.newBuyerCommitment") : "🎉 New Buyer Commitment";


    // =====================================
    // CROP NAME
    // =====================================

    const cropName =
        document.createElement("p");

    const cropLabel = typeof translate === "function" ? translate("orders.crop") : "Crop:";
    cropName.innerHTML =
        `<strong>${cropLabel}</strong> ${cropData.cropName}`;


    // =====================================
    // QUANTITY
    // =====================================

    const quantity =
        document.createElement("p");

    const qtyLabel = typeof translate === "function" ? translate("orders.quantity") : "Quantity:";
    quantity.innerHTML =
        `<strong>${qtyLabel}</strong> ${cropData.quantity} kg`;


    // =====================================
    // LOCATION
    // =====================================

    const location =
        document.createElement("p");

    const locLabel = typeof translate === "function" ? translate("orders.farmLocation") : "Farm Location:";
    location.innerHTML =
        `<strong>${locLabel}</strong> ${cropData.location}`;


    // =====================================
    // HARVEST DATE
    // =====================================

    const harvestDate =
        document.createElement("p");

    const harvestLabel = typeof translate === "function" ? translate("orders.expectedHarvest") : "Expected Harvest:";
    harvestDate.innerHTML =
        `<strong>${harvestLabel}</strong> ${cropData.harvestDate}`;


    // =====================================
    // STATUS
    // =====================================

    const status =
        document.createElement("span");

    status.textContent =
        typeof translate === "function" ? translate("orders.buyerCommitted") : "✓ Buyer Committed";

    status.classList.add("order-status");


    // =====================================
    // ADD DETAILS
    // =====================================

    details.appendChild(title);

    details.appendChild(cropName);

    details.appendChild(quantity);

    details.appendChild(location);

    details.appendChild(harvestDate);

    details.appendChild(status);


    // =====================================
    // ADD DETAILS TO CARD
    // =====================================

    orderCard.appendChild(details);


    // =====================================
    // ADD CARD TO PAGE
    // =====================================

    ordersContainer.appendChild(orderCard);
}


// =========================================
// EMPTY STATE
// =========================================

function showEmptyMessage() {

    const message =
        document.createElement("div");

    message.classList.add(
        "empty-message"
    );

    message.textContent =
        typeof translate === "function" ? translate("orders.noCommitments") : "No buyer commitments yet.";

    ordersContainer.appendChild(message);
}


// =========================================
// BACK TO DASHBOARD
// =========================================

dashboardButton.addEventListener(
    "click",
    function () {

        window.location.href =
            "/frontend/pages/farmer-dashboard.html";

    }
);