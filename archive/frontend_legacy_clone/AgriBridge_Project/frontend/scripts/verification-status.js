// =========================================
// VERIFICATION STATUS
// =========================================

const dashboardButton =
    document.getElementById("dashboard-button");

const statusValue =
    document.getElementById("status-value");

const statusTitle =
    document.getElementById("status-title");

const statusMessage =
    document.getElementById("status-message");


// =========================================
// API
// =========================================

const API_URL =
    "http://127.0.0.1:8000/api/verifications/";


// =========================================
// LOAD VERIFICATION STATUS
// =========================================

async function loadVerificationStatus() {

    // =====================================
    // GET LISTING ID
    //
    // Primary: separate localStorage key
    // Fallback: cropData.listingId
    // =====================================

    let listingId =
        localStorage.getItem("listingId");

    console.log(
        "LISTING ID:",
        listingId
    );


    // Fallback: read from cropData
    if (!listingId) {

        const savedCropData =
            localStorage.getItem("cropData");

        if (savedCropData) {

            const cropData =
                JSON.parse(savedCropData);

            listingId =
                cropData.listingId
                    ? String(cropData.listingId)
                    : null;

            console.log(
                "Listing ID from cropData fallback:",
                listingId
            );

        }

    }


    // =====================================
    // NO LISTING ID
    // =====================================

    if (!listingId) {

        statusValue.textContent =
            typeof translate === "function" ? translate("verification.status.noListing") : "No Listing";

        statusTitle.textContent =
            typeof translate === "function" ? translate("verification.status.listingNotFound") : "Listing Not Found";

        statusMessage.textContent =
            typeof translate === "function" ? translate("verification.status.noListingFound") : "No crop listing was found.";

        return;
    }


    // =====================================
    // LOADING
    // =====================================

    statusValue.textContent =
        typeof translate === "function" ? translate("common.loading") : "Loading...";

    statusTitle.textContent =
        typeof translate === "function" ? translate("verification.status.checkingStatus") : "Checking Verification Status";

    statusMessage.textContent =
        typeof translate === "function" ? translate("verification.status.pleaseWait") : "Please wait while we check the field-agent verification.";


    try {

        const response =
            await fetch(API_URL);


        if (!response.ok) {

            throw new Error(
                `Server returned ${response.status}`
            );

        }


        const data =
            await response.json();


        console.log(
            "Verification API response:",
            data
        );


        // =================================
        // FIND CURRENT LISTING
        // =================================

        const verification =
            data.verifications.find(
                verification =>
                    String(verification.listing_id) ===
                    String(listingId)
            );


        console.log(
            "Matching verification:",
            verification
        );

        console.log(
            "API VERIFICATION:",
            verification
        );

        console.log(
            "FINAL VERIFICATION STATUS:",
            verification?.status
        );


        // =================================
        // NO VERIFICATION
        // =================================

        if (!verification) {

            statusValue.textContent =
                typeof translate === "function" ? translate("verification.status.verificationMissing") : "Verification Missing";

            statusTitle.textContent =
                typeof translate === "function" ? translate("verification.status.unableToCheckStatus") : "Unable to Check Status";

            statusMessage.textContent =
                typeof translate === "function" ? translate("verification.status.verificationMissingDesc") : "A verification record was not found for this listing. Please contact support.";

            return;
        }


        // =================================
        // SAVE STATUS LOCALLY
        // =================================

        const savedCropData =
            localStorage.getItem("cropData");

        if (savedCropData) {

            const cropData =
                JSON.parse(savedCropData);

            cropData.status =
                verification.status;

            localStorage.setItem(
                "cropData",
                JSON.stringify(cropData)
            );
        }


        // =================================
        // PENDING
        // =================================

        if (verification.status === "pending") {

            statusValue.textContent =
                typeof translate === "function" ? translate("verification.status.pending") : "Pending";

            statusTitle.textContent =
                typeof translate === "function" ? translate("verification.status.waitingForVerification") : "Waiting for Verification";

            statusMessage.textContent =
                typeof translate === "function" ? translate("verification.status.waitingDesc") : "Your crop has passed the initial AI health check and is waiting for field-agent verification.";
        }


        // =================================
        // VERIFIED
        // =================================

        else if (verification.status === "verified") {

            statusValue.textContent =
                typeof translate === "function" ? translate("verification.status.verified") : "✓ Verified";

            statusTitle.textContent =
                typeof translate === "function" ? translate("verification.status.cropVerifiedTitle") : "Crop Verified!";

            statusMessage.textContent =
                typeof translate === "function" ? translate("verification.status.cropVerifiedDesc") : "Your crop has been verified by a field agent and is now available to buyers.";
        }


        // =================================
        // REJECTED
        // =================================

        else if (verification.status === "rejected") {

            statusValue.textContent =
                typeof translate === "function" ? translate("verification.status.rejected") : "✕ Rejected";

            statusTitle.textContent =
                typeof translate === "function" ? translate("verification.status.cropRejectedTitle") : "Crop Rejected";

            statusMessage.textContent =
                typeof translate === "function" ? translate("verification.status.cropRejectedDesc") : "The field agent rejected this crop. Please review the crop information and resubmit.";
        }


        // =================================
        // UNKNOWN
        // =================================

        else {

            statusValue.textContent =
                verification.status;

            statusTitle.textContent =
                typeof translate === "function" ? translate("verification.status.verificationStatus") : "Verification Status";

            statusMessage.textContent =
                typeof translate === "function" ? translate("verification.status.agentUpdated") : "The field agent has updated the verification status.";
        }

    }

    catch (error) {

        console.error(
            "Failed to load verification status:",
            error
        );


        statusValue.textContent =
            typeof translate === "function" ? translate("verification.status.error") : "Error";

        statusTitle.textContent =
            typeof translate === "function" ? translate("verification.status.unableToCheckStatus") : "Unable to Check Status";

        statusMessage.textContent =
            typeof translate === "function" ? translate("verification.status.couldNotConnect") : "We could not connect to the verification server. Please try again.";
    }
}


// =========================================
// BACK TO DASHBOARD
// =========================================

if (dashboardButton) {

    dashboardButton.addEventListener(
        "click",
        function () {

            window.location.href =
                "/frontend/pages/farmer-dashboard.html";

        }
    );
}


// =========================================
// START
// =========================================

loadVerificationStatus();
