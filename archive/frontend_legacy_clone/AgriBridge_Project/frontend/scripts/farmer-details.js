// =========================================
// FARMER DETAILS
// =========================================


// =========================================
// GET HTML ELEMENTS
// =========================================

const farmerDetailsForm =
    document.getElementById("farmer-details-form");

const formMessage =
    document.getElementById("form-message");


// =========================================
// FORM SUBMISSION
// =========================================

farmerDetailsForm.addEventListener(
    "submit",
    function (event) {

        // Stop page reload
        event.preventDefault();


        // =====================================
        // GET VALUES
        // =====================================

        const farmerName =
            document.getElementById("farmer-name")
                .value
                .trim();

        const farmArea =
            document.getElementById("farm-area")
                .value
                .trim();

        const farmLocation =
            document.getElementById("farm-location")
                .value
                .trim();

        const phone =
            document.getElementById("phone")
                .value
                .trim();


        // =====================================
        // VALIDATION
        // =====================================

        if (
            !farmerName ||
            !farmArea ||
            !farmLocation ||
            !phone
        ) {

            formMessage.textContent =
                typeof translate === "function" ? translate("profile.errors.fillAllFields") : "Please complete all fields.";

            formMessage.style.color =
                "#c62828";

            return;
        }


        // =====================================
        // CREATE FARMER PROFILE
        // =====================================

        const farmerProfile = {

            name: farmerName,

            farmArea: farmArea,

            farmAreaUnit: "acres",

            location: farmLocation,

            phone: phone

        };


        // =====================================
        // SAVE PROFILE
        // =====================================

        localStorage.setItem(
            "farmerProfile",
            JSON.stringify(farmerProfile)
        );


        // =====================================
        // SUCCESS MESSAGE
        // =====================================

        formMessage.textContent =
            typeof translate === "function" ? translate("profile.farmerProfile.savedSuccessfully") : "✓ Profile saved successfully!";

        formMessage.style.color =
            "#2E7D32";


        // =====================================
        // GO TO FARMER DASHBOARD
        // =====================================

        setTimeout(function () {

            window.location.href =
                "/frontend/pages/farmer-dashboard.html";

        }, 500);

    }
);