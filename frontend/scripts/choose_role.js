// =========================================
// AGRIBRIDGE — CHOOSE ROLE & AUTH LOGIC
// =========================================

document.addEventListener("DOMContentLoaded", () => {

    const roleCards = document.querySelectorAll(".role-select-card");
    const roleSelect = document.getElementById("choose-role");
    const roleForm = document.getElementById("role-form");

    let selectedRole = "farmer";

    // 1. Role Card Click Handler
    roleCards.forEach(card => {
        card.addEventListener("click", () => {
            // Remove active class from all
            roleCards.forEach(c => c.classList.remove("active"));
            
            // Set active on clicked card
            card.classList.add("active");

            // Update state
            const role = card.getAttribute("data-role");
            if (role) {
                selectedRole = role;
                if (roleSelect) {
                    roleSelect.value = role;
                }
            }
        });
    });

    // 2. Form Submission (Login & Create Account)
    if (roleForm) {
        roleForm.addEventListener("submit", (event) => {
            event.preventDefault();

            const currentRole = roleSelect ? roleSelect.value || selectedRole : selectedRole;
            localStorage.setItem("userRole", currentRole);

            // If user filled a name on signup, store basic profile info
            const nameInput = document.getElementById("auth-name");
            const phoneInput = document.getElementById("auth-phone");
            
            let profile = JSON.parse(localStorage.getItem("farmerProfile") || "{}");
            if (nameInput && nameInput.value) {
                profile.name = nameInput.value.trim();
            }
            if (phoneInput && phoneInput.value) {
                profile.phone = phoneInput.value.trim();
            }
            localStorage.setItem("farmerProfile", JSON.stringify(profile));

            // Determine if on signup or login
            const currentPath = window.location.pathname.toLowerCase();
            const isSignup = currentPath.includes("signup");

            if (currentRole === "farmer") {
                window.location.href = isSignup 
                    ? "/frontend/pages/farmer-details.html" 
                    : "/frontend/pages/farmer-dashboard.html";
            } else if (currentRole === "buyer") {
                window.location.href = "/frontend/pages/buyer-dashboard.html";
            } else if (currentRole === "field-agent") {
                window.location.href = "/frontend/pages/field-agent-dashboard.html";
            } else {
                window.location.href = "/frontend/pages/farmer-dashboard.html";
            }
        });
    }

});