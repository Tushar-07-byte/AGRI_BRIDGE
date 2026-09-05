// =========================================
// FARMER DASHBOARD
// =========================================

// =========================================
// LOAD FARMER PROFILE
// =========================================

const savedFarmerProfile =
    localStorage.getItem("farmerProfile");


if (savedFarmerProfile) {

    const farmerProfile =
        JSON.parse(savedFarmerProfile);


    // Farmer name

    const farmerName =
        document.getElementById("farmer-name");

    if (farmerName && farmerProfile.name) {

        farmerName.textContent =
            farmerProfile.name;

    }


    // Farm area

    const farmArea =
        document.getElementById("farm-area");

    if (
        farmArea &&
        farmerProfile.farmArea
    ) {

        farmArea.textContent =
            `${farmerProfile.farmArea} ${farmerProfile.farmAreaUnit || "acres"
            }`;

    }


    // Farm location

    const farmLocation =
        document.getElementById("farm-location");

    if (
        farmLocation &&
        farmerProfile.location
    ) {

        farmLocation.textContent =
            farmerProfile.location;

    }

}


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
        typeof translate === "function"
            ? translate("orders.newBuyerCommitment")
            : "🎉 New Buyer Commitment";


    // =====================================
    // CROP NAME
    // =====================================

    const cropName =
        document.createElement("p");

    cropName.textContent =
        `${typeof translate === "function" ? translate("orders.crop") : "Crop:"} ${cropData.cropName}`;


    // =====================================
    // QUANTITY
    // =====================================

    const quantity =
        document.createElement("p");

    quantity.textContent =
        `${typeof translate === "function" ? translate("orders.quantity") : "Quantity:"} ${cropData.quantity} kg`;


    // =====================================
    // LOCATION
    // =====================================

    const location =
        document.createElement("p");

    location.textContent =
        `${typeof translate === "function" ? translate("orders.farmLocation") : "Farm Location:"} ${cropData.location}`;


    // =====================================
    // HARVEST DATE
    // =====================================

    const harvestDate =
        document.createElement("p");

    harvestDate.textContent =
        `${typeof translate === "function" ? translate("orders.expectedHarvest") : "Expected Harvest:"} ${cropData.harvestDate}`;


    // =====================================
    // STATUS
    // =====================================

    const status =
        document.createElement("span");

    status.textContent =
        typeof translate === "function"
            ? translate("orders.buyerCommitted")
            : "✓ Buyer Committed";

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
        typeof translate === "function"
            ? translate("orders.noCommitments")
            : "No buyer commitments yet.";

    ordersContainer.appendChild(message);
}
