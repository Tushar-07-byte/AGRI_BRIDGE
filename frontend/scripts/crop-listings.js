// =========================================
// CROP LISTINGS
// =========================================


// =========================================
// GET HTML ELEMENTS
// =========================================

const cropImage =
    document.getElementById("crop-image");

const cropName =
    document.getElementById("crop-name");

const cropQuantity =
    document.getElementById("crop-quantity");

const harvestDate =
    document.getElementById("harvest-date");

const cropLocation =
    document.getElementById("crop-location");

const verificationStatus =
    document.getElementById("verification-status");

const buyerStatus =
    document.getElementById("buyer-status");

const listingCard =
    document.querySelector(".listing-card");

const noListing =
    document.getElementById("no-listing");

const dashboardButton =
    document.getElementById("dashboard-button");

const uploadButton =
    document.getElementById("upload-button");


// =========================================
// GET CROP DATA
// =========================================

const savedCropData =
    localStorage.getItem("cropData");

const savedCropImage =
    localStorage.getItem("cropImage");


// =========================================
// CHECK IF CROP EXISTS
// =========================================

if (!savedCropData) {

    // Hide listing
    listingCard.style.display = "none";

    // Show no listing message
    noListing.style.display = "block";

} else {

    // Convert saved data back to object
    const cropData =
        JSON.parse(savedCropData);


    // =====================================
    // DISPLAY CROP DETAILS
    // =====================================

    cropName.textContent =
        cropData.cropName || "Unknown Crop";

    cropQuantity.textContent =
        (cropData.quantity || "-") + " kg";

    harvestDate.textContent =
        cropData.harvestDate || "-";

    cropLocation.textContent =
        cropData.location || "-";


    // =====================================
    // DISPLAY IMAGE
    // =====================================

    if (savedCropImage) {

        cropImage.src =
            savedCropImage;

    } else {

        cropImage.alt =
            "No crop image available";

    }


    // =====================================
    // VERIFICATION STATUS
    // =====================================

    const status =
        cropData.status || "pending";


    if (status === "verified") {

        verificationStatus.textContent =
            "✓ Verified";

        verificationStatus.className =
            "status verified";

    }

    else if (status === "rejected") {

        verificationStatus.textContent =
            "✕ Rejected";

        verificationStatus.className =
            "status rejected";

    }

    else {

        verificationStatus.textContent =
            "Pending";

        verificationStatus.className =
            "status pending";

    }


    // =====================================
    // BUYER STATUS
    // =====================================

    if (status === "committed") {

        // Crop is already committed
        verificationStatus.textContent =
            "✓ Verified";

        verificationStatus.className =
            "status verified";

        buyerStatus.textContent =
            "🤝 Buyer Committed";

        buyerStatus.className =
            "status committed";

    }

    else {

        buyerStatus.textContent =
            "No Buyer Yet";

        buyerStatus.className =
            "status pending";

    }

}


// =========================================
// BACK TO DASHBOARD
// =========================================

dashboardButton.addEventListener(
    "click",
    function () {

        window.location.href =
            "farmer-dashboard.html";

    }
);


// =========================================
// UPLOAD CROP BUTTON
// =========================================

uploadButton.addEventListener(
    "click",
    function () {

        window.location.href =
            "upload-crop.html";

    }
);