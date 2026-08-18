// =========================================
// FARMER DASHBOARD
// =========================================

// Get the orders container
const ordersContainer =
    document.getElementById("orders-container");


// =========================================
// GET CROP DATA
// =========================================

const savedCropData =
    localStorage.getItem("cropData");

const buyerCommitment =
    localStorage.getItem("buyerCommitment");


// =========================================
// CHECK FOR INCOMING ORDER
// =========================================

if (
    savedCropData &&
    buyerCommitment === "true"
) {

    // Convert JSON string into object
    const cropData =
        JSON.parse(savedCropData);


    // Make sure buyer actually committed
    if (cropData.status === "committed") {

        createOrderCard(cropData);

    } else {

        showNoOrders();

    }

} else {

    showNoOrders();

}


// =========================================
// CREATE ORDER CARD
// =========================================

function createOrderCard(cropData) {

    // Create main card
    const orderCard =
        document.createElement("div");

    orderCard.classList.add("order-card");


    // =====================================
    // ORDER TITLE
    // =====================================

    const title =
        document.createElement("h3");

    title.textContent =
        "🎉 New Buyer Commitment";


    // =====================================
    // CROP NAME
    // =====================================

    const cropName =
        document.createElement("p");

    cropName.textContent =
        `Crop: ${cropData.cropName}`;


    // =====================================
    // QUANTITY
    // =====================================

    const quantity =
        document.createElement("p");

    quantity.textContent =
        `Quantity: ${cropData.quantity} kg`;


    // =====================================
    // LOCATION
    // =====================================

    const location =
        document.createElement("p");

    location.textContent =
        `Farm Location: ${cropData.location}`;


    // =====================================
    // HARVEST DATE
    // =====================================

    const harvestDate =
        document.createElement("p");

    harvestDate.textContent =
        `Expected Harvest: ${cropData.harvestDate}`;


    // =====================================
    // STATUS
    // =====================================

    const status =
        document.createElement("span");

    status.textContent =
        "✓ Buyer Committed";

    status.classList.add("order-status");


    // =====================================
    // ADD EVERYTHING TO CARD
    // =====================================

    orderCard.appendChild(title);

    orderCard.appendChild(cropName);

    orderCard.appendChild(quantity);

    orderCard.appendChild(location);

    orderCard.appendChild(harvestDate);

    orderCard.appendChild(status);


    // =====================================
    // ADD CARD TO PAGE
    // =====================================

    ordersContainer.appendChild(orderCard);
}


// =========================================
// NO ORDERS MESSAGE
// =========================================

function showNoOrders() {

    const message =
        document.createElement("p");

    message.classList.add("no-orders");

    message.textContent =
        "No incoming orders yet.";

    ordersContainer.appendChild(message);
}

