// =========================================
// FIELD AGENT DASHBOARD
// =========================================

console.log("=== FIELD AGENT DASHBOARD START ===");


// =========================================
// HTML ELEMENTS
// =========================================

const pendingContainer =
    document.getElementById("pending-container");


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
// LOAD DASHBOARD DATA
// =========================================

async function loadDashboard() {

    if (!pendingContainer) {

        console.error(
            "Pending container not found."
        );

        return;
    }


    pendingContainer.innerHTML =
        `<p>${typeof translate === "function" ? translate("fieldAgent.dashboard.loadingSubmissions") : "Loading crop submissions..."}</p>`;


    try {

        // =====================================
        // GET LISTINGS
        // =====================================

        const listingsResponse =
            await fetch(API_LISTINGS);


        if (!listingsResponse.ok) {

            throw new Error(
                `Listings API returned ${listingsResponse.status}`
            );

        }


        const listingsData =
            await listingsResponse.json();


        // =====================================
        // GET VERIFICATIONS
        // =====================================

        const verificationsResponse =
            await fetch(API_VERIFICATIONS);


        if (!verificationsResponse.ok) {

            throw new Error(
                `Verification API returned ${verificationsResponse.status}`
            );

        }


        const verificationsData =
            await verificationsResponse.json();


        // =====================================
        // DEBUG
        // =====================================

        console.log(
            "Listings:",
            listingsData
        );

        console.log(
            "Verifications:",
            verificationsData
        );


        // =====================================
        // CHECK API DATA
        // =====================================

        if (
            !listingsData.success ||
            !Array.isArray(listingsData.listings)
        ) {

            throw new Error(
                "Invalid listings API response."
            );

        }


        if (
            !verificationsData.success ||
            !Array.isArray(verificationsData.verifications)
        ) {

            throw new Error(
                "Invalid verification API response."
            );

        }


        // =====================================
        // FIND PENDING LISTINGS
        //
        // A listing is pending only if it has a
        // verification record with status "pending".
        // Listings without a verification record
        // are NOT treated as pending.
        // =====================================

        const pendingListings =
            listingsData.listings.filter(listing => {

                const verification =
                    verificationsData.verifications.find(
                        v =>
                            String(v.listing_id) ===
                            String(listing.id)
                    );

                return (
                    verification &&
                    verification.status === "pending"
                );

            });

        // =====================================
        // UPDATE DASHBOARD COUNTS
        // =====================================

        updateDashboardCounts(
            listingsData.listings,
            verificationsData.verifications
        );


        // =====================================
        // CLEAR CONTAINER
        // =====================================

        pendingContainer.innerHTML = "";


        // =====================================
        // NO PENDING CROPS
        // =====================================

        if (
            pendingListings.length === 0
        ) {

            const emptyMessage =
                document.createElement("p");


            emptyMessage.textContent =
                typeof translate === "function" ? translate("fieldAgent.dashboard.noPendingCrops") : "No crops are currently pending verification.";


            pendingContainer.appendChild(
                emptyMessage
            );


            return;
        }


        // =====================================
        // DISPLAY PENDING CROPS
        // =====================================

        pendingListings.forEach(
            listing => {

                const verification =
                    verificationsData.verifications.find(
                        v =>
                            String(v.listing_id) ===
                            String(listing.id)
                    );

                createCropCard(
                    listing,
                    verification
                );

            }
        );

    }


    catch (error) {

        console.error(
            "Failed to load dashboard:",
            error
        );


        pendingContainer.innerHTML =
            `
            <p>
                ${typeof translate === "function" ? translate("fieldAgent.dashboard.unableToLoad") : "Unable to load crop submissions. Please check that FastAPI is running."}
            </p>
            `;

    }

}


// =========================================
// CREATE CROP CARD
// =========================================

function createCropCard(listing, verification) {

    const cropCard =
        document.createElement("div");


    cropCard.classList.add(
        "pending-card"
    );

    // =====================================
    // IMAGE
    // =====================================

    const image = document.createElement("img");

    image.classList.add("pending-image");

    const imageUrl =
        getImageUrl(listing.photo_path);

    console.log(
        "Listing image:",
        listing.id,
        listing.photo_path,
        imageUrl
    );

    image.onerror = function () {

        console.error(
            "Crop image failed:",
            imageUrl
        );

    };

    image.src = imageUrl;

    image.alt =
        listing.crop_type || "Crop";


    // =====================================
    // CROP NAME
    // =====================================

    const name =
        document.createElement("h3");


    name.textContent =
        listing.crop_type ||
        "Unknown Crop";


    // =====================================
    // QUANTITY
    // =====================================

    const quantity =
        document.createElement("p");


    quantity.textContent =
        `${typeof translate === "function" ? translate("fieldAgent.dashboard.quantity") : "Quantity:"} ${listing.quantity_est ?? 0
        } kg`;


    // =====================================
    // HARVEST DATE
    // =====================================

    const harvestDate =
        document.createElement("p");


    harvestDate.textContent =
        `${typeof translate === "function" ? translate("fieldAgent.dashboard.harvestDate") : "Harvest Date:"} ${listing.harvest_date ??
        "Not available"
        }`;


    // =====================================
    // HEALTH STATUS
    // =====================================

    const healthStatus =
        document.createElement("p");


    healthStatus.textContent =
        `${typeof translate === "function" ? translate("fieldAgent.dashboard.aiResult") : "AI Result:"} ${listing.health_status ??
        "Not available"
        }`;


    // =====================================
    // CONFIDENCE
    // =====================================

    const confidence =
        document.createElement("p");


    if (
        listing.confidence !== null &&
        listing.confidence !== undefined
    ) {

        confidence.textContent =
            `${typeof translate === "function" ? translate("fieldAgent.dashboard.aiConfidence") : "AI Confidence:"} ${(
                Number(listing.confidence) *
                100
            ).toFixed(2)
            }%`;

    }

    else {

        confidence.textContent =
            typeof translate === "function" ? translate("fieldAgent.dashboard.aiConfidenceNA") : "AI Confidence: Not available";

    }


    // =====================================
    // REVIEW BUTTON
    // =====================================

    const reviewButton =
        document.createElement("button");


    reviewButton.textContent =
        typeof translate === "function" ? translate("fieldAgent.dashboard.reviewCrop") : "Review Crop";


    reviewButton.classList.add(
        "review-button"
    );


    // =====================================
    // REVIEW BUTTON CLICK
    // =====================================

    reviewButton.addEventListener(
        "click",
        function () {

            // Save listing data for the review page
            localStorage.setItem(
                "listingId",
                String(listing.id)
            );

            localStorage.setItem(
                "agentListing",
                JSON.stringify(listing)
            );

            // Navigate with both IDs in URL
            window.location.href =
                `/frontend/pages/verification-review.html` +
                `?listing_id=${listing.id}` +
                `&verification_id=${verification.id}`;

        }
    );



    // =====================================
    // ADD ELEMENTS TO CARD
    // =====================================

    cropCard.appendChild(
        image
    );

    cropCard.appendChild(
        name
    );

    cropCard.appendChild(
        quantity
    );

    cropCard.appendChild(
        harvestDate
    );

    cropCard.appendChild(
        healthStatus
    );

    cropCard.appendChild(
        confidence
    );

    cropCard.appendChild(
        reviewButton
    );


    // =====================================
    // ADD CARD TO CONTAINER
    // =====================================

    pendingContainer.appendChild(
        cropCard
    );

}


// =========================================
// UPDATE DASHBOARD COUNTS
// =========================================

function updateDashboardCounts(
    listings,
    verifications
) {

    let pending = 0;
    let verified = 0;
    let rejected = 0;


    verifications.forEach(verification => {

        if (verification.status === "pending") {

            pending++;

        }

        else if (verification.status === "verified") {

            verified++;

        }

        else if (verification.status === "rejected") {

            rejected++;

        }

    });


    const cards =
        document.querySelectorAll(
            ".overview-card"
        );


    if (cards.length >= 3) {

        cards[0]
            .querySelector("p")
            .textContent = pending;

        cards[1]
            .querySelector("p")
            .textContent = verified;

        cards[2]
            .querySelector("p")
            .textContent = rejected;

    }

}


// =========================================
// START DASHBOARD
// =========================================

loadDashboard();
