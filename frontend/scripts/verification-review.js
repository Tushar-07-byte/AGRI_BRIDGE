// =========================================
// VERIFICATION REVIEW
// =========================================


// =========================================
// GET HTML ELEMENTS
// =========================================

const cropImageElement =
    document.getElementById("crop-image");

const approveButton =
    document.getElementById("approve-button");

const rejectButton =
    document.getElementById("reject-button");

const decisionMessage =
    document.getElementById("decision-message");


// =========================================
// GET SAVED CROP DATA
// =========================================

const savedCropData =
    localStorage.getItem("cropData");

const savedImage =
    localStorage.getItem("cropImage");


// =========================================
// CHECK CROP DATA
// =========================================

if (!savedCropData) {

    decisionMessage.textContent =
        "Crop data not found.";

    decisionMessage.style.color =
        "#c62828";

    approveButton.disabled = true;
    rejectButton.disabled = true;

} else {

    // Convert JSON into object
    const cropData =
        JSON.parse(savedCropData);


    // =====================================
    // DISPLAY CROP IMAGE
    // =====================================

    if (savedImage) {

        cropImageElement.src =
            savedImage;

        cropImageElement.alt =
            cropData.cropName;

    } else {

        cropImageElement.alt =
            "No crop image available";

    }


    // =====================================
    // DISPLAY CROP DETAILS
    // =====================================

    document.getElementById("crop-name").textContent =
        cropData.cropName || "Not available";

    document.getElementById("farmer-name").textContent =
        cropData.farmerName || "Farmer";

    document.getElementById("crop-quantity").textContent =
        `${cropData.quantity || 0} kg`;

    document.getElementById("crop-location").textContent =
        cropData.location || "Not available";

    document.getElementById("harvest-date").textContent =
        cropData.harvestDate || "Not available";


    // =====================================
    // SHOW CURRENT STATUS
    // =====================================

    if (cropData.status === "verified") {

        decisionMessage.textContent =
            "✓ This crop has already been verified.";

        decisionMessage.style.color =
            "#2E7D32";

        approveButton.disabled = true;
        rejectButton.disabled = true;

    }

    else if (cropData.status === "rejected") {

        decisionMessage.textContent =
            "✕ This crop has already been rejected.";

        decisionMessage.style.color =
            "#c62828";

        approveButton.disabled = true;
        rejectButton.disabled = true;

    }

}


// =========================================
// APPROVE / VERIFY CROP
// =========================================

approveButton.addEventListener(
    "click",
    function () {

        const savedCropData =
            localStorage.getItem("cropData");


        // Check again
        if (!savedCropData) {

            decisionMessage.textContent =
                "Crop data not found.";

            decisionMessage.style.color =
                "#c62828";

            return;
        }


        // Convert JSON into object
        const cropData =
            JSON.parse(savedCropData);


        // =================================
        // CHANGE STATUS
        // =================================

        cropData.status =
            "verified";


        // =================================
        // SAVE UPDATED DATA
        // =================================

        localStorage.setItem(
            "cropData",
            JSON.stringify(cropData)
        );


        // =================================
        // SUCCESS MESSAGE
        // =================================

        decisionMessage.textContent =
            "✓ Crop verified successfully!";

        decisionMessage.style.color =
            "#2E7D32";


        // =================================
        // DISABLE BUTTONS
        // =================================

        approveButton.disabled =
            true;

        rejectButton.disabled =
            true;


        // =================================
        // GO TO STATUS PAGE
        // =================================

        setTimeout(function () {

            window.location.href =
                "verification-status.html";

        }, 800);

    }
);


// =========================================
// REJECT CROP
// =========================================

rejectButton.addEventListener(
    "click",
    function () {

        const savedCropData =
            localStorage.getItem("cropData");


        // Check again
        if (!savedCropData) {

            decisionMessage.textContent =
                "Crop data not found.";

            decisionMessage.style.color =
                "#c62828";

            return;
        }


        // Convert JSON into object
        const cropData =
            JSON.parse(savedCropData);


        // =================================
        // CHANGE STATUS
        // =================================

        cropData.status =
            "rejected";


        // =================================
        // SAVE UPDATED DATA
        // =================================

        localStorage.setItem(
            "cropData",
            JSON.stringify(cropData)
        );


        // =================================
        // SUCCESS MESSAGE
        // =================================

        decisionMessage.textContent =
            "✕ Crop rejected. Farmer needs to resubmit.";

        decisionMessage.style.color =
            "#c62828";


        // =================================
        // DISABLE BUTTONS
        // =================================

        approveButton.disabled =
            true;

        rejectButton.disabled =
            true;

    }
);