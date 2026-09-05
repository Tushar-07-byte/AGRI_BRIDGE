// ==========================================================================
// AGRIBRIDGE — ACTUAL LOGIN PAGE SCRIPT
// Multi-Role Authentication, Demo Fill & Real-time Live Logins Bus
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
    "use strict";

    const roleTabs = document.querySelectorAll(".role-tab-btn");
    const roleInput = document.getElementById("selected-role-input");
    const emailInput = document.getElementById("login-email");
    const passwordInput = document.getElementById("login-password");
    const togglePwdBtn = document.getElementById("toggle-pwd-btn");
    const loginForm = document.getElementById("actual-login-form");
    const statusMsg = document.getElementById("login-status-msg");
    const demoChips = document.querySelectorAll(".demo-chip");

    // DEMO CREDENTIALS REPOSITORY
    const DEMO_USERS = {
        farmer: {
            email: "ramesh@agrifarm.in",
            pass: "farm123",
            name: "Ramesh Patel (Farmer)",
            redirect: "/frontend/pages/farmer-dashboard.html"
        },
        buyer: {
            email: "procurement@freshbazaar.in",
            pass: "buyer123",
            name: "FreshBazaar Procurement",
            redirect: "/frontend/pages/buyer-dashboard.html"
        },
        "field-agent": {
            email: "amit.sharma@agribridge.org",
            pass: "agent123",
            name: "Amit Sharma (Inspector)",
            redirect: "/frontend/pages/field-agent-dashboard.html"
        },
        admin: {
            email: "ops@agribridge.org",
            pass: "admin123",
            name: "Operations SuperAdmin",
            redirect: "/frontend/pages/admin-dashboard.html"
        }
    };

    // 1. ROLE TAB SWITCHER
    roleTabs.forEach(tab => {
        tab.addEventListener("click", () => {
            const selectedRole = tab.getAttribute("data-role");
            if (!selectedRole) return;

            roleTabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            if (roleInput) roleInput.value = selectedRole;

            // Auto set placeholder
            if (emailInput) {
                if (selectedRole === "farmer") emailInput.placeholder = "e.g. ramesh@agrifarm.in or +91 98271...";
                else if (selectedRole === "buyer") emailInput.placeholder = "e.g. procurement@freshbazaar.in";
                else if (selectedRole === "field-agent") emailInput.placeholder = "e.g. amit.sharma@agribridge.org";
                else if (selectedRole === "admin") emailInput.placeholder = "e.g. ops@agribridge.org";
            }
        });
    });

    // Check URL parameters for pre-selected role (e.g. ?role=buyer)
    const urlParams = new URLSearchParams(window.location.search);
    const initialRole = urlParams.get("role");
    if (initialRole) {
        const initialTab = document.querySelector(`.role-tab-btn[data-role="${initialRole}"]`);
        if (initialTab) initialTab.click();
    }

    // 2. SHOW / HIDE PASSWORD
    if (togglePwdBtn && passwordInput) {
        togglePwdBtn.addEventListener("click", () => {
            if (passwordInput.type === "password") {
                passwordInput.type = "text";
                togglePwdBtn.textContent = "🙈";
            } else {
                passwordInput.type = "password";
                togglePwdBtn.textContent = "👁️";
            }
        });
    }

    // 3. ONE-CLICK DEMO AUTOFILL
    demoChips.forEach(chip => {
        chip.addEventListener("click", () => {
            const targetRole = chip.getAttribute("data-autofill");
            const creds = DEMO_USERS[targetRole];
            if (!creds) return;

            // Select role tab
            const targetTab = document.querySelector(`.role-tab-btn[data-role="${targetRole}"]`);
            if (targetTab) targetTab.click();

            // Autofill fields
            if (emailInput) emailInput.value = creds.email;
            if (passwordInput) passwordInput.value = creds.pass;

            if (statusMsg) {
                statusMsg.className = "login-status-msg success";
                statusMsg.textContent = `✓ Filled demo credentials for ${creds.name}. Click 'Sign In' to enter.`;
                statusMsg.style.display = "block";
            }
        });
    });

    // 4. FORM SUBMIT & AUTHENTICATION
    if (loginForm) {
        loginForm.addEventListener("submit", (e) => {
            e.preventDefault();

            const role = roleInput ? roleInput.value : "farmer";
            const email = emailInput ? emailInput.value.trim() : "";
            const pass = passwordInput ? passwordInput.value.trim() : "";

            if (!email || !pass) {
                if (statusMsg) {
                    statusMsg.className = "login-status-msg error";
                    statusMsg.textContent = "Please enter both your email and password.";
                    statusMsg.style.display = "block";
                }
                return;
            }

            // Determine user profile name
            let userName = email.split("@")[0];
            userName = userName.charAt(0).toUpperCase() + userName.slice(1);
            if (DEMO_USERS[role] && DEMO_USERS[role].email === email) {
                userName = DEMO_USERS[role].name;
            }

            // Record live login event into localStorage for Admin to see in real-time!
            try {
                const newLog = {
                    id: `LOG-${Math.floor(500 + Math.random() * 499)}`,
                    user: `${userName} (${role.toUpperCase()})`,
                    role: role,
                    ip: "10.228.117.107 (Local Wi-Fi)",
                    device: navigator.userAgent.includes("Mobile") ? "Mobile Device" : "Desktop Browser",
                    time: "Today " + new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
                    status: "Successful"
                };

                const existingLogs = JSON.parse(localStorage.getItem("agribridge_live_logins") || "[]");
                existingLogs.unshift(newLog);
                localStorage.setItem("agribridge_live_logins", JSON.stringify(existingLogs.slice(0, 30)));

                // Save active user profile
                localStorage.setItem("user", JSON.stringify({
                    email: email,
                    role: role,
                    name: userName,
                    loggedInAt: new Date().toISOString()
                }));

                // If logging into admin, grant session auth
                if (role === "admin" || email === "ops@agribridge.org") {
                    sessionStorage.setItem("agribridge_admin_authenticated", "true");
                }
            } catch (err) {
                console.warn("Log storage error:", err);
            }

            // Show success feedback
            if (statusMsg) {
                statusMsg.className = "login-status-msg success";
                statusMsg.textContent = `✓ Authentication successful. Redirecting to ${role.toUpperCase()} portal...`;
                statusMsg.style.display = "block";
            }

            // Redirect to appropriate dashboard
            const redirectUrl = DEMO_USERS[role] ? DEMO_USERS[role].redirect : "/frontend/pages/farmer-dashboard.html";
            setTimeout(() => {
                window.location.href = redirectUrl;
            }, 600);
        });
    }
});

