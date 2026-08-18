// =========================================
// VERIFICATION STATUS
// =========================================


// =========================================
// GET HTML ELEMENTS
// =========================================

const dashboardButton =
    document.getElementById("dashboard-button");

const statusValue =
    document.querySelector(".status-value");

const statusTitle =
    document.querySelector(".status-title");

const statusMessage =
    document.querySelector(".status-message");


// =========================================
// GET CROP DATA
// =========================================

const savedCropData =
    localStorage.getItem("cropData");


// =========================================
// CHECK ELEMENTS
// =========================================

if (!statusValue || !statusTitle || !statusMessage) {

    console.error(
        "Verification status elements not found."
    );

}


// =========================================
// UPDATE VERIFICATION STATUS
// =========================================

if (savedCropData) {

    const cropData =
        JSON.parse(savedCropData);


    // =====================================
    // PENDING
    // =====================================

    if (cropData.status === "pending") {

        statusValue.textContent =
            "Pending";

        statusTitle.textContent =
            "Waiting for Verification";

        statusMessage.textContent =
            "Your crop has passed the initial AI health check and is now waiting for field-agent verification.";

    }


    // =====================================
    // VERIFIED
    // =====================================

    else if (cropData.status === "verified") {

        statusValue.textContent =
            "✓ Verified";

        statusTitle.textContent =
            "Crop Verified!";

        statusMessage.textContent =
            "Your crop has been verified by a field agent and is now available to buyers.";

    }


    // =====================================
    // COMMITTED
    // =====================================

    else if (cropData.status === "committed") {

        statusValue.textContent =
            "🤝 Buyer Committed";

        statusTitle.textContent =
            "Buyer Found!";

        statusMessage.textContent =
            "A buyer has committed to purchase your crop.";

    }


    // =====================================
    // REJECTED
    // =====================================

    else if (cropData.status === "rejected") {

        statusValue.textContent =
            "✕ Rejected";

        statusTitle.textContent =
            "Crop Rejected";

        statusMessage.textContent =
            "The field agent rejected this crop. Please review the crop information and resubmit.";

    }


    // =====================================
    // UNKNOWN STATUS
    // =====================================

    else {

        statusValue.textContent =
            "Unknown";

        statusTitle.textContent =
            "Status Unavailable";

        statusMessage.textContent =
            "We could not determine the current verification status.";

    }

} else {

    // =====================================
    // NO CROP DATA
    // =====================================

    statusValue.textContent =
        "No Crop";

    statusTitle.textContent =
        "No Crop Submitted";

    statusMessage.textContent =
        "No crop submission was found.";

}


// =========================================
// BACK TO DASHBOARD
// =========================================

if (dashboardButton) {

    dashboardButton.addEventListener(
        "click",
        function () {

            window.location.href =
                "farmer-dashboard.html";

        }
    );

}