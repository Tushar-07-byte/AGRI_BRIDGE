// ==============================================================================
// AGRIBRIDGE — SIGNUP PAGE LOGIC (signup.js)
// ==============================================================================

document.addEventListener("DOMContentLoaded", () => {

    const signupForm = document.getElementById("signup-form");
    const nameInput = document.getElementById("signup-name");
    const mobileInput = document.getElementById("signup-mobile");
    const passwordInput = document.getElementById("signup-password");
    const confirmPasswordInput = document.getElementById("signup-confirm-password");
    const roleCards = document.querySelectorAll(".role-select-card");
    const roleSelect = document.getElementById("choose-role");
    const submitBtn = document.getElementById("signup-submit-btn");
    const alertBox = document.getElementById("signup-alert-box");
    const strengthBar = document.getElementById("password-strength-fill");
    const strengthText = document.getElementById("password-strength-text");
    const togglePasswordBtn = document.getElementById("toggle-signup-password");

    let selectedRole = "farmer";

    // -------------------------------------------------------------------------
    // 1. URL PREFILL (e.g. login.html -> signup.html?mobile=9876543210)
    // -------------------------------------------------------------------------
    const urlParams = new URLSearchParams(window.location.search);
    const prefillMobile = urlParams.get("mobile");
    if (prefillMobile && mobileInput) {
        mobileInput.value = prefillMobile.replace("+91", "").trim();
    }

    // -------------------------------------------------------------------------
    // 2. ALERT HELPERS
    // -------------------------------------------------------------------------
    function showAlert(msg, type = "error", actionHtml = "") {
        if (!alertBox) return;
        alertBox.className = `auth-alert-box ${type}`;
        alertBox.innerHTML = `<span>${msg}</span> ${actionHtml}`;
        alertBox.style.display = "block";
    }

    function hideAlert() {
        if (!alertBox) return;
        alertBox.style.display = "none";
        alertBox.innerHTML = "";
    }

    // -------------------------------------------------------------------------
    // 3. ROLE SELECTION CARDS
    // -------------------------------------------------------------------------
    roleCards.forEach(card => {
        card.addEventListener("click", () => {
            roleCards.forEach(c => c.classList.remove("active"));
            card.classList.add("active");
            const role = card.getAttribute("data-role");
            if (role) {
                selectedRole = role;
                if (roleSelect) roleSelect.value = role;
            }
        });
    });

    // -------------------------------------------------------------------------
    // 4. SHOW / HIDE PASSWORD
    // -------------------------------------------------------------------------
    if (togglePasswordBtn && passwordInput) {
        togglePasswordBtn.addEventListener("click", () => {
            const isPassword = passwordInput.getAttribute("type") === "password";
            passwordInput.setAttribute("type", isPassword ? "text" : "password");
            if (confirmPasswordInput) {
                confirmPasswordInput.setAttribute("type", isPassword ? "text" : "password");
            }
            togglePasswordBtn.textContent = isPassword ? "🙈 Hide" : "👁️ Show";
        });
    }

    // -------------------------------------------------------------------------
    // 5. LIVE PASSWORD STRENGTH EVALUATOR
    // -------------------------------------------------------------------------
    if (passwordInput && strengthBar && strengthText) {
        passwordInput.addEventListener("input", () => {
            const pwd = passwordInput.value;
            let score = 0;

            if (pwd.length >= 8) score += 25;
            if (/[A-Z]/.test(pwd)) score += 25;
            if (/[0-9]/.test(pwd)) score += 25;
            if (/[^A-Za-z0-9]/.test(pwd)) score += 25;

            strengthBar.style.width = `${score}%`;

            if (score === 0) {
                strengthBar.style.backgroundColor = "#e0e0e0";
                strengthText.textContent = "";
            } else if (score <= 25) {
                strengthBar.style.backgroundColor = "#e53935";
                strengthText.textContent = "Weak (min 8 characters)";
                strengthText.style.color = "#e53935";
            } else if (score <= 75) {
                strengthBar.style.backgroundColor = "#fb8c00";
                strengthText.textContent = "Medium (add uppercase/symbols)";
                strengthText.style.color = "#fb8c00";
            } else {
                strengthBar.style.backgroundColor = "#43a047";
                strengthText.textContent = "Strong password";
                strengthText.style.color = "#43a047";
            }
        });
    }

    // -------------------------------------------------------------------------
    // 6. FORM SUBMISSION
    // -------------------------------------------------------------------------
    if (signupForm) {
        signupForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            hideAlert();

            const name = nameInput.value.trim();
            const rawMobile = mobileInput.value.trim();
            const password = passwordInput.value;
            const confirmPassword = confirmPasswordInput.value;

            if (!name || name.length < 2) {
                showAlert("Please enter your full name.", "error");
                return;
            }

            if (!rawMobile || rawMobile.length < 10) {
                showAlert("Please enter a valid 10-digit mobile number.", "error");
                return;
            }

            if (!password || password.length < 8) {
                showAlert("Password must be at least 8 characters long.", "error");
                return;
            }

            if (password !== confirmPassword) {
                showAlert("Passwords do not match.", "error");
                return;
            }

            submitBtn.disabled = true;
            submitBtn.textContent = "Creating Account...";

            try {
                const res = await fetch("/api/auth/register", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        name: name,
                        mobile: rawMobile,
                        password: password,
                        confirm_password: confirmPassword,
                        role: selectedRole
                    })
                });

                const data = await res.json();

                if (!res.ok || !data.success) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = "Create Account & Continue →";

                    if (data.code === "ACCOUNT_EXISTS") {
                        showAlert(
                            "This mobile number is already registered.",
                            "warning",
                            `<a href="/frontend/pages/login.html?mobile=${encodeURIComponent(rawMobile)}" class="alert-action-link">Log In Instead →</a>`
                        );
                    } else {
                        showAlert(data.message || "Registration failed.", "error");
                    }
                    return;
                }

                // Registration Succeeded!
                showAlert("✓ Account created successfully! Redirecting to login...", "success");

                // Ensure NO active session or JWT is set during registration
                if (window.AgriBridgeAuth) {
                    window.AgriBridgeAuth.clearAuth();
                }

                setTimeout(() => {
                    const redirectTarget = data.redirect || `/frontend/pages/login.html?registered=true&mobile=${encodeURIComponent(rawMobile)}`;
                    window.location.href = redirectTarget;
                }, 700);

            } catch (err) {
                showAlert("Unable to connect to server. Please check backend status.", "error");
                submitBtn.disabled = false;
                submitBtn.textContent = "Create Account & Continue →";
            }
        });
    }

});

