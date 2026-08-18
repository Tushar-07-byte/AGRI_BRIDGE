// =========================================
// BUYER DASHBOARD
// =========================================


// =========================================
// GET HTML ELEMENTS
// =========================================

const listingsContainer =
    document.getElementById("listings-container");


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

    showEmptyMessage();

} else {

    const cropData =
        JSON.parse(savedCropData);


    // =====================================
    // ONLY SHOW VERIFIED CROPS
    // =====================================

    if (cropData.status === "verified") {

        createCropCard(
            cropData,
            savedCropImage
        );

    } else {

        showEmptyMessage();

    }

}


// =========================================
// CREATE CROP CARD
// =========================================

function createCropCard(cropData, imageData) {


    // =====================================
    // CARD
    // =====================================

    const card =
        document.createElement("div");

    card.classList.add("crop-card");


    // =====================================
    // IMAGE
    // =====================================

    const image =
        document.createElement("img");

    if (imageData) {

        image.src =
            imageData;

    }

    image.alt =
        cropData.cropName || "Crop";


    // =====================================
    // CROP NAME
    // =====================================

    const name =
        document.createElement("h3");

    name.textContent =
        cropData.cropName || "Unknown Crop";


    // =====================================
    // QUANTITY
    // =====================================

    const quantity =
        document.createElement("p");

    quantity.textContent =
        `Quantity: ${cropData.quantity || 0} kg`;


    // =====================================
    // LOCATION
    // =====================================

    const location =
        document.createElement("p");

    location.textContent =
        `Farm Location: ${cropData.location || "Not available"}`;


    // =====================================
    // HARVEST DATE
    // =====================================

    const harvestDate =
        document.createElement("p");

    harvestDate.textContent =
        `Expected Harvest: ${cropData.harvestDate || "Not available"}`;


    // =====================================
    // VERIFIED BADGE
    // =====================================

    const badge =
        document.createElement("span");

    badge.textContent =
        "✓ Field Agent Verified";

    badge.classList.add(
        "verified-badge"
    );


    // =====================================
    // COMMIT BUTTON
    // =====================================

    const commitButton =
        document.createElement("button");

    commitButton.type =
        "button";

    commitButton.textContent =
        "Commit to Buy";

    commitButton.classList.add(
        "commit-button"
    );


    // =====================================
    // COMMIT TO BUY
    // =====================================

    commitButton.addEventListener(
        "click",
        function () {


            console.log(
                "Commit to Buy clicked"
            );


            // =================================
            // GET LATEST CROP DATA
            // =================================

            const latestCropData =
                localStorage.getItem("cropData");


            if (!latestCropData) {

                alert(
                    "Crop data could not be found."
                );

                return;

            }


            // =================================
            // CONVERT DATA
            // =================================

            const updatedCropData =
                JSON.parse(latestCropData);


            // =================================
            // CHECK STATUS
            // =================================

            if (
                updatedCropData.status !==
                "verified"
            ) {

                alert(
                    "This crop is no longer available for purchase."
                );

                return;

            }


            // =================================
            // SAVE BUYER COMMITMENT
            // =================================

            localStorage.setItem(
                "buyerCommitment",
                "true"
            );


            // =================================
            // UPDATE CROP STATUS
            // =================================

            updatedCropData.status =
                "committed";


            // =================================
            // SAVE UPDATED CROP
            // =================================

            localStorage.setItem(
                "cropData",
                JSON.stringify(
                    updatedCropData
                )
            );


            // =================================
            // UPDATE BUTTON
            // =================================

            commitButton.textContent =
                "✓ Purchase Committed";

            commitButton.disabled =
                true;


            // =================================
            // UPDATE BUTTON STYLE
            // =================================

            commitButton.style.backgroundColor =
                "#66bb6a";

            commitButton.style.cursor =
                "default";


            // =================================
            // SHOW POLISHED CONFIRMATION
            // =================================

            commitmentMessage.style.display =
                "flex";


            // =================================
            // LOG SUCCESS
            // =================================

            console.log(
                "Buyer commitment saved successfully."
            );

        }
    );


    // =====================================
    // ADD ELEMENTS
    // =====================================

    card.appendChild(image);

    card.appendChild(name);

    card.appendChild(quantity);

    card.appendChild(location);

    card.appendChild(harvestDate);

    card.appendChild(badge);

    card.appendChild(commitButton);


    // =====================================
    // SUCCESS MESSAGE
    // =====================================

    const commitmentMessage =
        document.createElement("div");

    commitmentMessage.classList.add(
        "commitment-message"
    );

    commitmentMessage.innerHTML = `
    <div class="success-icon">✓</div>

    <div>
        <h3>Purchase Committed!</h3>

        <p>
            Your commitment has been sent to the farmer.
        </p>
    </div>
`;

    card.appendChild(commitmentMessage);


    // =====================================
    // ADD CARD TO PAGE
    // =====================================

    listingsContainer.appendChild(card);

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
        "No verified crops are currently available.";

    listingsContainer.appendChild(
        message
    );

}