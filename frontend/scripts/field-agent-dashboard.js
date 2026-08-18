// =========================================
// GET PENDING CONTAINER
// =========================================

const pendingContainer =
    document.getElementById("pending-container");


// =========================================
// GET FARMER CROP DATA
// =========================================

const savedCropData =
    localStorage.getItem("cropData");

const savedCropImage =
    localStorage.getItem("cropImage");


// =========================================
// CHECK IF CROP EXISTS
// =========================================

if (savedCropData) {

    // Convert JSON string back into object
    const cropData = JSON.parse(savedCropData);


    // =====================================
    // CREATE PENDING CROP CARD
    // =====================================

    const cropCard =
        document.createElement("div");

    cropCard.classList.add("pending-card");


    // =====================================
    // IMAGE
    // =====================================

    const image =
        document.createElement("img");

    image.classList.add("pending-image");

    image.src = savedCropImage;

    image.alt = cropData.cropName;


    // =====================================
    // CROP NAME
    // =====================================

    const name =
        document.createElement("h3");

    name.textContent =
        cropData.cropName;


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
        `Location: ${cropData.location}`;


    // =====================================
    // AI STATUS
    // =====================================

    const aiStatus =
        document.createElement("p");

    aiStatus.textContent =
        "AI Status: ✓ Passed";

    aiStatus.classList.add("ai-status");


    // =====================================
    // REVIEW BUTTON
    // =====================================

    const reviewButton =
        document.createElement("button");

    reviewButton.textContent =
        "Review Crop";

    reviewButton.classList.add("review-button");


    // =====================================
    // BUTTON CLICK
    // =====================================

    reviewButton.addEventListener("click", function () {

        window.location.href =
            `verification-review.html?crop=${encodeURIComponent(cropData.cropName)}`;

    });


    // =====================================
    // ADD EVERYTHING TO CARD
    // =====================================

    cropCard.appendChild(image);

    cropCard.appendChild(name);

    cropCard.appendChild(quantity);

    cropCard.appendChild(location);

    cropCard.appendChild(aiStatus);

    cropCard.appendChild(reviewButton);


    // =====================================
    // ADD CARD TO PAGE
    // =====================================

    pendingContainer.appendChild(cropCard);


} else {

    // =====================================
    // NO PENDING CROPS
    // =====================================

    const emptyMessage =
        document.createElement("p");

    emptyMessage.textContent =
        "No crops are currently pending verification.";

    pendingContainer.appendChild(emptyMessage);

}

