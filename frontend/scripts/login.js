// ==============================================================================
// AGRIBRIDGE — LOGIN PAGE LOGIC (login.js)
// ==============================================================================

document.addEventListener("DOMContentLoaded", () => {

    // Form and Tab Elements
    const loginForm = document.getElementById("login-form");
    const mobileInput = document.getElementById("login-mobile");
    const passwordInput = document.getElementById("login-password");
    const passwordGroup = document.getElementById("password-group");
    const otpGroup = document.getElementById("otp-group");
    const otpInput = document.getElementById("otp-code");
    const sendOtpBtn = document.getElementById("send-otp-btn");
    const resendOtpBtn = document.getElementById("resend-otp-btn");
    const submitBtn = document.getElementById("login-submit-btn");
    const toggleOtpModeBtn = document.getElementById("toggle-otp-mode-btn");
    const togglePasswordVisibilityBtn = document.getElementById("toggle-password-visibility");
    const alertBox = document.getElementById("login-alert-box");

    // Forgot Password Elements
    const forgotPasswordLink = document.getElementById("forgot-password-link");
    const forgotPasswordModal = document.getElementById("forgot-password-modal");
    const closeForgotModalBtn = document.getElementById("close-forgot-modal-btn");
    const forgotSendOtpBtn = document.getElementById("forgot-send-otp-btn");
    const forgotResetBtn = document.getElementById("forgot-reset-btn");
    const forgotMobileInput = document.getElementById("forgot-mobile");
    const forgotOtpInput = document.getElementById("forgot-otp");
    const forgotNewPasswordInput = document.getElementById("forgot-new-password");
    const forgotConfirmPasswordInput = document.getElementById("forgot-confirm-password");
    const forgotAlertBox = document.getElementById("forgot-alert-box");
    const forgotStep1 = document.getElementById("forgot-step-1");
    const forgotStep2 = document.getElementById("forgot-step-2");

    let isOtpMode = false;
    let resendTimer = null;

    // -------------------------------------------------------------------------
    // 1. URL PREFILL & REGISTRATION NOTICE (e.g. signup.html -> login.html?registered=true&mobile=9876543210)
    // -------------------------------------------------------------------------
    const urlParams = new URLSearchParams(window.location.search);
    const prefillMobile = urlParams.get("mobile");
    if (prefillMobile && mobileInput) {
        mobileInput.value = prefillMobile.replace("+91", "").trim();
    }
    const isRegistered = urlParams.get("registered") === "true";
    if (isRegistered) {
        showAlert("✓ Account created successfully! Please enter your password to log in.", "success");
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

    function showForgotAlert(msg, type = "error") {
        if (!forgotAlertBox) return;
        forgotAlertBox.className = `auth-alert-box ${type}`;
        forgotAlertBox.textContent = msg;
        forgotAlertBox.style.display = "block";
    }

    // -------------------------------------------------------------------------
    // 3. SHOW / HIDE PASSWORD TOGGLE
    // -------------------------------------------------------------------------
    if (togglePasswordVisibilityBtn && passwordInput) {
        togglePasswordVisibilityBtn.addEventListener("click", () => {
            const isPassword = passwordInput.getAttribute("type") === "password";
            passwordInput.setAttribute("type", isPassword ? "text" : "password");
            togglePasswordVisibilityBtn.textContent = isPassword ? "🙈 Hide" : "👁️ Show";
        });
    }

    // -------------------------------------------------------------------------
    // 4. TOGGLE OTP LOGIN MODE
    // -------------------------------------------------------------------------
    if (toggleOtpModeBtn) {
        toggleOtpModeBtn.addEventListener("click", () => {
            isOtpMode = !isOtpMode;
            hideAlert();

            if (isOtpMode) {
                passwordGroup.style.display = "none";
                otpGroup.style.display = "block";
                toggleOtpModeBtn.textContent = "← Login with Password Instead";
                submitBtn.textContent = "Verify OTP & Login →";
            } else {
                passwordGroup.style.display = "block";
                otpGroup.style.display = "none";
                toggleOtpModeBtn.textContent = "Login with 6-Digit OTP";
                submitBtn.textContent = "Login to Dashboard →";
            }
        });
    }

    // -------------------------------------------------------------------------
    // 5. SEND OTP / RESEND OTP WITH 30s COUNTDOWN
    // -------------------------------------------------------------------------
    async function handleSendOtp() {
        const rawMobile = mobileInput.value.trim();
        if (!rawMobile || rawMobile.length < 10) {
            showAlert("Please enter a valid 10-digit mobile number.", "error");
            return;
        }

        hideAlert();
        sendOtpBtn.disabled = true;
        sendOtpBtn.textContent = "Sending...";

        try {
            const res = await fetch("/api/auth/send-otp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ mobile: rawMobile, purpose: "login" })
            });

            const data = await res.json();

            if (!res.ok || !data.success) {
                if (data.code === "USER_NOT_FOUND") {
                    showAlert(
                        "No AgriBridge account found with this number.",
                        "warning",
                        `<a href="/frontend/pages/signup.html?mobile=${encodeURIComponent(rawMobile)}" class="alert-action-link">Create an Account →</a>`
                    );
                } else {
                    showAlert(data.message || "Failed to send OTP.", "error");
                }
                sendOtpBtn.disabled = false;
                sendOtpBtn.textContent = "Send OTP";
                return;
            }

            showAlert(`✓ OTP sent! In dev mode: <strong>${data.dev_otp}</strong>`, "success");
            if (otpInput && data.dev_otp) {
                otpInput.value = data.dev_otp;
            }

            // Start 30s Countdown
            startOtpCountdown(30);

        } catch (err) {
            showAlert("Network error connecting to backend. Please ensure backend is active.", "error");
            sendOtpBtn.disabled = false;
            sendOtpBtn.textContent = "Send OTP";
        }
    }

    function startOtpCountdown(seconds) {
        if (sendOtpBtn) sendOtpBtn.style.display = "none";
        if (resendOtpBtn) {
            resendOtpBtn.style.display = "inline-flex";
            resendOtpBtn.disabled = true;
        }

        let remaining = seconds;
        resendOtpBtn.textContent = `Resend OTP in ${remaining}s`;

        if (resendTimer) clearInterval(resendTimer);
        resendTimer = setInterval(() => {
            remaining -= 1;
            if (remaining <= 0) {
                clearInterval(resendTimer);
                resendOtpBtn.disabled = false;
                resendOtpBtn.textContent = "Resend OTP";
            } else {
                resendOtpBtn.textContent = `Resend OTP in ${remaining}s`;
            }
        }, 1000);
    }

    if (sendOtpBtn) sendOtpBtn.addEventListener("click", handleSendOtp);
    if (resendOtpBtn) resendOtpBtn.addEventListener("click", handleSendOtp);

    // -------------------------------------------------------------------------
    // 6. MAIN LOGIN FORM SUBMISSION (PASSWORD OR OTP)
    // -------------------------------------------------------------------------
    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            hideAlert();

            const rawMobile = mobileInput.value.trim();
            if (!rawMobile || rawMobile.length < 10) {
                showAlert("Please enter a valid 10-digit mobile number.", "error");
                return;
            }

            submitBtn.disabled = true;
            submitBtn.textContent = isOtpMode ? "Verifying..." : "Logging in...";

            try {
                if (isOtpMode) {
                    // OTP Verification Login
                    const otpCode = otpInput.value.trim();
                    if (!otpCode || otpCode.length !== 6) {
                        showAlert("Please enter the 6-digit OTP.", "error");
                        submitBtn.disabled = false;
                        submitBtn.textContent = "Verify OTP & Login →";
                        return;
                    }

                    const res = await fetch("/api/auth/verify-otp", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ mobile: rawMobile, otp: otpCode })
                    });

                    const data = await res.json();
                    handleAuthResponse(res, data);

                } else {
                    // Password Login
                    const password = passwordInput.value;
                    if (!password) {
                        showAlert("Please enter your password.", "error");
                        submitBtn.disabled = false;
                        submitBtn.textContent = "Login to Dashboard →";
                        return;
                    }

                    const res = await fetch("/api/auth/login", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ mobile: rawMobile, password: password })
                    });

                    const data = await res.json();
                    handleAuthResponse(res, data);
                }
            } catch (err) {
                showAlert("Unable to connect to server. Please check backend status.", "error");
                submitBtn.disabled = false;
                submitBtn.textContent = isOtpMode ? "Verify OTP & Login →" : "Login to Dashboard →";
            }
        });
    }

    function handleAuthResponse(res, data) {
        submitBtn.disabled = false;
        submitBtn.textContent = isOtpMode ? "Verify OTP & Login →" : "Login to Dashboard →";

        if (!res.ok || !data.success) {
            if (data.code === "USER_NOT_FOUND") {
                const mob = mobileInput.value.trim();
                showAlert(
                    "No account found for this mobile number.",
                    "warning",
                    `<a href="/frontend/pages/signup.html?mobile=${encodeURIComponent(mob)}" class="alert-action-link">Create Account →</a>`
                );
            } else if (data.code === "INVALID_CREDENTIALS") {
                showAlert("Incorrect mobile number or password.", "error");
            } else {
                showAlert(data.message || "Authentication failed.", "error");
            }
            return;
        }

        // Authentication Succeeded!
        showAlert("✓ Login successful! Redirecting to your dashboard...", "success");

        if (window.AgriBridgeAuth) {
            window.AgriBridgeAuth.clearAuth();
            window.AgriBridgeAuth.setToken(data.token);
            window.AgriBridgeAuth.setCurrentUser(data.user);
        }

        setTimeout(() => {
            const redirectTarget = data.redirect || "/frontend/pages/farmer-dashboard.html";
            window.location.href = redirectTarget;
        }, 600);
    }

    // -------------------------------------------------------------------------
    // 7. FORGOT PASSWORD MODAL FLOW
    // -------------------------------------------------------------------------
    if (forgotPasswordLink && forgotPasswordModal) {
        forgotPasswordLink.addEventListener("click", (e) => {
            e.preventDefault();
            forgotPasswordModal.style.display = "flex";
            if (mobileInput.value && forgotMobileInput) {
                forgotMobileInput.value = mobileInput.value.trim();
            }
        });
    }

    if (closeForgotModalBtn && forgotPasswordModal) {
        closeForgotModalBtn.addEventListener("click", () => {
            forgotPasswordModal.style.display = "none";
        });
    }

    // Step 1: Send Reset OTP
    if (forgotSendOtpBtn) {
        forgotSendOtpBtn.addEventListener("click", async () => {
            const mob = forgotMobileInput.value.trim();
            if (!mob || mob.length < 10) {
                showForgotAlert("Please enter your registered 10-digit mobile number.", "error");
                return;
            }

            forgotSendOtpBtn.disabled = true;
            forgotSendOtpBtn.textContent = "Sending...";

            try {
                const res = await fetch("/api/auth/forgot-password", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ mobile: mob })
                });
                const data = await res.json();

                if (!res.ok || !data.success) {
                    showForgotAlert(data.message || "No account found with this number.", "error");
                    forgotSendOtpBtn.disabled = false;
                    forgotSendOtpBtn.textContent = "Send Reset OTP";
                    return;
                }

                showForgotAlert(`✓ Reset OTP sent! Dev code: ${data.dev_otp}`, "success");
                if (forgotOtpInput && data.dev_otp) {
                    forgotOtpInput.value = data.dev_otp;
                }

                // Show Step 2
                forgotStep1.style.display = "none";
                forgotStep2.style.display = "block";

            } catch (err) {
                showForgotAlert("Error connecting to server.", "error");
                forgotSendOtpBtn.disabled = false;
                forgotSendOtpBtn.textContent = "Send Reset OTP";
            }
        });
    }

    // Step 2: Reset Password
    if (forgotResetBtn) {
        forgotResetBtn.addEventListener("click", async () => {
            const mob = forgotMobileInput.value.trim();
            const otp = forgotOtpInput.value.trim();
            const newPwd = forgotNewPasswordInput.value;
            const confirmPwd = forgotConfirmPasswordInput.value;

            if (!otp || otp.length !== 6) {
                showForgotAlert("Please enter the 6-digit OTP.", "error");
                return;
            }

            if (!newPwd || newPwd.length < 8) {
                showForgotAlert("New password must be at least 8 characters.", "error");
                return;
            }

            if (newPwd !== confirmPwd) {
                showForgotAlert("Passwords do not match.", "error");
                return;
            }

            forgotResetBtn.disabled = true;
            forgotResetBtn.textContent = "Updating Password...";

            try {
                const res = await fetch("/api/auth/reset-password", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        mobile: mob,
                        otp: otp,
                        new_password: newPwd,
                        confirm_password: confirmPwd
                    })
                });

                const data = await res.json();
                if (!res.ok || !data.success) {
                    showForgotAlert(data.message || "Failed to reset password.", "error");
                    forgotResetBtn.disabled = false;
                    forgotResetBtn.textContent = "Reset Password";
                    return;
                }

                showForgotAlert("✓ Password reset successfully! You can now log in.", "success");
                setTimeout(() => {
                    forgotPasswordModal.style.display = "none";
                    if (passwordInput) passwordInput.value = newPwd;
                    showAlert("✓ Password updated. Please click login to continue.", "success");
                }, 1000);

            } catch (err) {
                showForgotAlert("Error connecting to server.", "error");
                forgotResetBtn.disabled = false;
                forgotResetBtn.textContent = "Reset Password";
            }
        });
    }

});

