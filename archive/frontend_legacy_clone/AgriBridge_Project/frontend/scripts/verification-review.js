// =========================================
// VERIFICATION REVIEW
// =========================================

console.log("=== VERIFICATION REVIEW START ===");


// =========================================
// API CONFIGURATION
// =========================================

const API_BASE_URL =
    "http://127.0.0.1:8000";

const API_LISTINGS =
    `${API_BASE_URL}/api/listings/`;

const API_VERIFICATIONS =
    `${API_BASE_URL}/api/verifications/`;


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
// GET IDS FROM URL
// =========================================

const params =
    new URLSearchParams(
        window.location.search
    );


const listingId =
    params.get("listing_id");


const verificationIdFromUrl =
    params.get("verification_id");


console.log(
    "Listing ID:",
    listingId
);

console.log(
    "Verification ID:",
    verificationIdFromUrl
);


// =========================================
// VERIFICATION ID (resolved after fetch)
// =========================================

let verificationId =
    verificationIdFromUrl;


// =========================================
// CHECK BOTH IDs
// =========================================

if (!listingId || !verificationId) {

    decisionMessage.textContent =
        typeof translate === "function" ? translate("verification.review.errors.listingOrVerificationMissing") : "Listing or verification information is missing.";;

    decisionMessage.style.color =
        "#c62828";

    approveButton.disabled = true;
    rejectButton.disabled = true;

} else {

    loadCropData();

}


// =========================================
// LOAD CROP DATA
// =========================================

async function loadCropData() {

    try {

        decisionMessage.textContent =
            typeof translate === "function" ? translate("verification.review.loadingCrop") : "Loading crop information...";

        decisionMessage.style.color =
            "#555";


        // =====================================
        // GET LISTINGS
        // =====================================

        const listingResponse =
            await fetch(
                API_LISTINGS
            );


        if (!listingResponse.ok) {

            throw new Error(
                `Listings API returned ${listingResponse.status}`
            );

        }


        const listingData =
            await listingResponse.json();


        // =====================================
        // FIND LISTING
        // =====================================

        const listing =
            listingData.listings.find(
                item =>
                    String(item.id) ===
                    String(listingId)
            );


        if (!listing) {

            throw new Error(
                "Listing not found."
            );

        }


        console.log(
            "Current listing:",
            listing
        );


        // =====================================
        // DISPLAY CROP INFORMATION
        // =====================================

        document.getElementById(
            "crop-name"
        ).textContent =
            listing.crop_type ||
            "Not available";


        document.getElementById(
            "crop-quantity"
        ).textContent =
            `${listing.quantity_est ?? 0} kg`;


        document.getElementById(
            "harvest-date"
        ).textContent =
            listing.harvest_date ||
            "Not available";


        // Location is currently not
        // stored in listings table.
        document.getElementById(
            "crop-location"
        ).textContent =
            "Not available";


        // Farmer ID is available.
        document.getElementById(
            "farmer-name"
        ).textContent =
            `Farmer #${listing.farmer_id}`;


        // =====================================
        // DISPLAY IMAGE
        // =====================================

        cropImageElement.onload = function () {

            console.log(
                "Crop image loaded successfully:",
                cropImageElement.src
            );

        };

        cropImageElement.onerror = function () {

            console.error(
                "Crop image failed:",
                cropImageElement.src
            );

        };

        if (listing.photo_path) {

            const imageUrl =
                getImageUrl(listing.photo_path);

            console.log(
                "Listing image:",
                listing.id,
                listing.photo_path,
                imageUrl
            );

            cropImageElement.src = imageUrl;

            cropImageElement.alt =
                listing.crop_type ||
                "Crop";


        } else {

            cropImageElement.alt =
                "No crop image available";

        }


        // =====================================
        // DISPLAY AI RESULT
        // =====================================

        const aiHeading =
            document.querySelector(
                ".ai-result-content h3"
            );


        const aiDescription =
            document.querySelector(
                ".ai-result-content p"
            );


        if (aiHeading) {

            aiHeading.textContent =
                listing.health_status ||
                "AI Analysis";

        }


        if (aiDescription) {

            let confidenceText =
                "";


            if (
                listing.confidence !== null &&
                listing.confidence !== undefined
            ) {

                confidenceText =
                    ` AI confidence: ${
                        (
                            Number(
                                listing.confidence
                            ) * 100
                        ).toFixed(2)
                    }%.`;

            }


            aiDescription.textContent =
                `AI detected: ${
                    listing.health_status ||
                    "Unknown"
                }.${confidenceText}`;

        }


        // =====================================
        // GET VERIFICATION
        // =====================================

        const verificationResponse =
            await fetch(
                `${API_BASE_URL}/api/verifications/${verificationId}`
            );


        if (!verificationResponse.ok) {

            throw new Error(
                `Verification API returned ${verificationResponse.status}`
            );

        }


        const verificationData =
            await verificationResponse.json();


        console.log(
            "Verification data:",
            verificationData
        );


        // =====================================
        // CHECK VERIFICATION EXISTS
        // =====================================

        const verification =
            verificationData.verification;


        if (!verification) {

            throw new Error(
                "Verification record not found."
            );

        }


        // =====================================
        // SAVE VERIFICATION ID
        // =====================================

        verificationId =
            verification.id;


        console.log(
            "Verification ID:",
            verificationId
        );


        // =====================================
        // CHECK CURRENT STATUS
        // =====================================

        if (
            verification.status ===
            "verified"
        ) {

            decisionMessage.textContent =
                typeof translate === "function" ? translate("verification.review.alreadyVerified") : "✓ This crop has already been verified.";

            decisionMessage.style.color =
                "#2E7D32";

            approveButton.disabled =
                true;

            rejectButton.disabled =
                true;

            return;

        }


        if (
            verification.status ===
            "rejected"
        ) {

            decisionMessage.textContent =
                typeof translate === "function" ? translate("verification.review.alreadyRejected") : "✕ This crop has already been rejected.";

            decisionMessage.style.color =
                "#c62828";

            approveButton.disabled =
                true;

            rejectButton.disabled =
                true;

            return;

        }


        // =====================================
        // READY FOR REVIEW
        // =====================================

        decisionMessage.textContent =
            typeof translate === "function" ? translate("verification.review.reviewAndChoose") : "Review the crop and choose Approve or Reject.";

        decisionMessage.style.color =
            "#555";

    }


    catch (error) {

        console.error(
            "Failed to load crop:",
            error
        );


        decisionMessage.textContent =
            `${typeof translate === "function" ? translate("verification.review.errors.unableToLoadCrop") : "Unable to load crop:"} ${error.message}`;

        decisionMessage.style.color =
            "#c62828";


        approveButton.disabled =
            true;

        rejectButton.disabled =
            true;

    }

}


// =========================================
// UPDATE VERIFICATION
// =========================================

async function updateVerification(
    newStatus
) {

    // =====================================
    // CHECK VERIFICATION ID
    // =====================================

    if (!verificationId) {

        decisionMessage.textContent =
            typeof translate === "function" ? translate("verification.review.errors.verificationIdMissing") : "Verification ID is missing.";

        decisionMessage.style.color =
            "#c62828";

        return;

    }


    // =====================================
    // DISABLE BUTTONS
    // =====================================

    approveButton.disabled =
        true;

    rejectButton.disabled =
        true;


    decisionMessage.textContent =
        typeof translate === "function" ? translate("verification.review.updatingVerification") : "Updating verification...";

    decisionMessage.style.color =
        "#555";


    try {

        // =====================================
        // PUT REQUEST
        // =====================================

        const response =
            await fetch(
                `${API_BASE_URL}/api/verifications/${verificationId}`,
                {
                    method: "PUT",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        status:
                            newStatus,

                        agent_name:
                            "Agent Rahul",

                        remarks:
                            newStatus === "verified"
                                ? "Crop verified successfully after field inspection."
                                : "Crop rejected after field inspection."

                    })
                }
            );


        // =====================================
        // READ RESPONSE
        // =====================================

        const data =
            await response.json();


        console.log(
            "Verification update response:",
            data
        );


        // =====================================
        // CHECK RESPONSE
        // =====================================

        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.detail ||
                `Verification update failed (${response.status})`
            );

        }


        // =====================================
        // UPDATE LOCAL CROP DATA
        // =====================================

        const savedCropData =
            localStorage.getItem(
                "cropData"
            );


        if (savedCropData) {

            const cropData =
                JSON.parse(
                    savedCropData
                );


            cropData.status =
                newStatus;


            localStorage.setItem(
                "cropData",
                JSON.stringify(
                    cropData
                )
            );

        }


        // =====================================
        // SUCCESS MESSAGE
        // =====================================

        if (
            newStatus ===
            "verified"
        ) {

            decisionMessage.textContent =
                "✓ Crop verified successfully!";

            decisionMessage.style.color =
                "#2E7D32";

        }

        else {

            decisionMessage.textContent =
                "✕ Crop rejected successfully.";

            decisionMessage.style.color =
                "#c62828";

        }


        // =====================================
        // REDIRECT
        // =====================================

        setTimeout(
            function () {

                window.location.href =
                    "/frontend/pages/verification-status.html";

            },
            1000
        );

    }


    catch (error) {

        console.error(
            "Verification update error:",
            error
        );


        decisionMessage.textContent =
            `Update failed: ${error.message}`;

        decisionMessage.style.color =
            "#c62828";


        // Re-enable buttons
        approveButton.disabled =
            false;

        rejectButton.disabled =
            false;

    }

}


// =========================================
// APPROVE BUTTON
// =========================================

if (approveButton) {

    approveButton.addEventListener(
        "click",
        function () {

            updateVerification(
                "verified"
            );

        }
    );

}


// =========================================
// REJECT BUTTON
// =========================================

if (rejectButton) {

    rejectButton.addEventListener(
        "click",
        function () {

            updateVerification(
                "rejected"
            );

        }
    );

}
