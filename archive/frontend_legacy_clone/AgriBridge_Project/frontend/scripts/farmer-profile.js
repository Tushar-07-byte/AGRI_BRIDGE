// =========================================
// FARMER PROFILE
// =========================================


// =========================================
// GET FORM ELEMENTS
// =========================================

const profileForm =
    document.getElementById(
        "farmer-profile-form"
    );

const profileMessage =
    document.getElementById(
        "profile-message"
    );


// =========================================
// FORM SUBMIT
// =========================================

profileForm.addEventListener(
    "submit",
    function (event) {

        event.preventDefault();


        // =====================================
        // GET VALUES
        // =====================================

        const name =
            document.getElementById(
                "farmer-name"
            ).value.trim();


        const farmName =
            document.getElementById(
                "farm-name"
            ).value.trim();


        const farmArea =
            document.getElementById(
                "farm-area"
            ).value;


        const farmAreaUnit =
            document.getElementById(
                "area-unit"
            ).value;


        const location =
            document.getElementById(
                "location"
            ).value.trim();


        const state =
            document.getElementById(
                "state"
            ).value;


        const crops =
            document.getElementById(
                "main-crops"
            ).value.trim();


        const phone =
            document.getElementById(
                "phone"
            ).value.trim();


        // =====================================
        // BASIC VALIDATION
        // =====================================

        if (
            !name ||
            !farmArea ||
            !location ||
            !state ||
            !phone
        ) {

            showMessage(
                typeof translate === "function" ? translate("profile.errors.fillAllFields") : "Please complete all required fields.",
                "#c62828"
            );

            return;

        }


        // =====================================
        // PHONE VALIDATION
        // =====================================

        if (!/^[0-9]{10}$/.test(phone)) {

            showMessage(
                typeof translate === "function" ? translate("errors.fillRequiredFields") : "Please enter a valid 10-digit phone number.",
                "#c62828"
            );

            return;

        }


        // =====================================
        // CREATE FARMER PROFILE
        // =====================================

        const farmerProfile = {

            name: name,

            farmName: farmName,

            farmArea: farmArea,

            farmAreaUnit: farmAreaUnit,

            location: location,

            state: state,

            crops: crops,

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

        showMessage(
            typeof translate === "function" ? translate("profile.farmerProfile.savedSuccessfully") : "Profile saved successfully!",
            "#2E7D32"
        );


        // =====================================
        // GO TO DASHBOARD
        // =====================================

        setTimeout(function () {

            window.location.href =
                "/frontend/pages/farmer-dashboard.html";

        }, 500);

    }
);


// =========================================
// MESSAGE FUNCTION
// =========================================

function showMessage(message, color) {

    profileMessage.textContent =
        message;

    profileMessage.style.color =
        color;

}