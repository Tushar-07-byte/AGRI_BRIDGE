// =========================================
// FARMER PROFILE — AUTHENTICATED
// =========================================

// Guard page for farmer role
if (window.AgriBridgeAuth) {
    window.AgriBridgeAuth.requireAuth(["farmer"]);
}

// Prefill authenticated name and phone
document.addEventListener("DOMContentLoaded", () => {
    const currentUser = window.AgriBridgeAuth ? window.AgriBridgeAuth.getCurrentUser() : null;
    const nameInput = document.getElementById("farmer-name");
    const phoneInput = document.getElementById("phone");

    if (currentUser) {
        if (nameInput && currentUser.name) nameInput.value = currentUser.name;
        if (phoneInput && currentUser.mobile) phoneInput.value = currentUser.mobile;

        // Load existing saved profile for this user
        const saved = localStorage.getItem(`farmer_profile_${currentUser.id}`) || localStorage.getItem("farmerProfile");
        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                const farmNameInput = document.getElementById("farm-name");
                const farmAreaInput = document.getElementById("farm-area");
                const locationInput = document.getElementById("location");
                const stateSelect = document.getElementById("state");

                if (farmNameInput && parsed.farmName) farmNameInput.value = parsed.farmName;
                if (farmAreaInput && parsed.farmArea) farmAreaInput.value = parsed.farmArea;
                if (locationInput && parsed.location) locationInput.value = parsed.location;
                if (stateSelect && parsed.state) stateSelect.value = parsed.state;
            } catch (e) {}
        }
    }
});

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

        const currentUser = window.AgriBridgeAuth ? window.AgriBridgeAuth.getCurrentUser() : null;
        const userKey = currentUser ? `farmer_profile_${currentUser.id}` : "farmerProfile";
        localStorage.setItem(userKey, JSON.stringify(farmerProfile));
        localStorage.setItem("farmerProfile", JSON.stringify(farmerProfile));

        if (currentUser && window.AgriBridgeAuth) {
            currentUser.name = name;
            window.AgriBridgeAuth.setCurrentUser(currentUser);
        }


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