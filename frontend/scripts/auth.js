// ==============================================================================
// AGRIBRIDGE AUTHENTICATION CLIENT & ROUTE GUARD (auth.js)
// ==============================================================================

const AgriBridgeAuth = (function () {
    const TOKEN_KEY = "agribridge_token";
    const USER_KEY = "agribridge_user";

    // -------------------------------------------------------------------------
    // 1. TOKEN & USER MANAGEMENT
    // -------------------------------------------------------------------------

    function isTokenExpired(token) {
        if (!token) return true;
        try {
            const parts = token.split(".");
            if (parts.length !== 3) return false; // Non-JWT opaque token
            const payload = JSON.parse(atob(parts[1].replace(/-/g, "+").replace(/_/g, "/")));
            if (payload && typeof payload.exp === "number") {
                return Date.now() >= payload.exp * 1000;
            }
            return false;
        } catch (e) {
            return false;
        }
    }

    function getToken() {
        const token = localStorage.getItem(TOKEN_KEY);
        if (!token) return null;
        if (isTokenExpired(token)) {
            clearAuth();
            return null;
        }
        return token;
    }

    function setToken(token) {
        if (token) {
            localStorage.setItem(TOKEN_KEY, token);
        } else {
            localStorage.removeItem(TOKEN_KEY);
        }
    }

    function getCurrentUser() {
        const token = getToken();
        if (!token) return null;
        const raw = localStorage.getItem(USER_KEY);
        if (!raw) return null;
        try {
            return JSON.parse(raw);
        } catch (e) {
            return null;
        }
    }

    function setCurrentUser(user) {
        if (user) {
            localStorage.setItem(USER_KEY, JSON.stringify(user));
            if (user.role) {
                localStorage.setItem("userRole", user.role);
            }
        } else {
            localStorage.removeItem(USER_KEY);
            localStorage.removeItem("userRole");
        }
        updateNavbarUser(user);
    }

    function clearAuth() {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
        localStorage.removeItem("userRole");

        // Clear legacy unkeyed profile and session cache to prevent cross-user leakage
        localStorage.removeItem("farmerProfile");
        localStorage.removeItem("cropData");
        localStorage.removeItem("buyerCommitment");
        localStorage.removeItem("listingId");
        localStorage.removeItem("aiResult");

        try {
            sessionStorage.clear();
        } catch (e) {}

        updateNavbarUser(null);
    }

    function isAuthenticated() {
        const token = getToken();
        const user = getCurrentUser();
        return Boolean(token && user && !isTokenExpired(token));
    }

    // -------------------------------------------------------------------------
    // 2. FETCH CURRENT USER FROM DATABASE VIA /api/auth/me
    // -------------------------------------------------------------------------

    async function fetchCurrentUser() {
        const token = getToken();
        if (!token) {
            clearAuth();
            return null;
        }

        try {
            const res = await fetch("/api/auth/me", {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                }
            });

            if (res.status === 401) {
                clearAuth();
                return null;
            }

            if (res.ok) {
                const data = await res.json();
                if (data.success && data.user) {
                    setCurrentUser(data.user);
                    return data.user;
                }
            }
        } catch (err) {
            console.warn("Unable to sync current user from backend:", err);
        }

        return getCurrentUser();
    }

    // -------------------------------------------------------------------------
    // 3. DASHBOARD REDIRECTION HELPERS
    // -------------------------------------------------------------------------

    function getDashboardUrlForRole(role) {
        if (!role) return "/frontend/pages/farmer-dashboard.html";
        const normalized = role.toLowerCase();
        if (normalized === "farmer") {
            return "/frontend/pages/farmer-dashboard.html";
        } else if (normalized === "buyer") {
            return "/frontend/pages/buyer-dashboard.html";
        } else if (normalized === "field-agent" || normalized === "field_agent" || normalized === "professional") {
            return "/frontend/pages/field-agent-dashboard.html";
        }
        return "/frontend/pages/farmer-dashboard.html";
    }

    function getRoleDisplayName(role) {
        if (!role) return "User";
        const normalized = role.toLowerCase();
        if (normalized === "farmer") return "👨‍🌾 Farmer";
        if (normalized === "buyer") return "🛒 Buyer";
        if (normalized === "field-agent" || normalized === "field_agent" || normalized === "professional") return "🌱 Field Agent";
        return role;
    }

    function escapeHtml(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // -------------------------------------------------------------------------
    // 4. NAVBAR & USER DISPLAY SYNCHRONIZATION
    // -------------------------------------------------------------------------

    function updateNavbarUser(user) {
        const currentUser = user || getCurrentUser();

        // Update Greeting / Name placeholders on page
        const farmerNameEl = document.getElementById("farmer-name");
        if (farmerNameEl) {
            farmerNameEl.textContent = currentUser ? currentUser.name : "Farmer";
        }

        const userNameEls = document.querySelectorAll(".user-name-display, .user-name, #user-name");
        userNameEls.forEach(el => {
            if (currentUser && currentUser.name) {
                el.textContent = currentUser.name;
            }
        });

        // Update Role badges
        const roleBadges = document.querySelectorAll(".user-role-badge, .user-role");
        roleBadges.forEach(badge => {
            if (currentUser && currentUser.name) {
                badge.textContent = `${getRoleDisplayName(currentUser.role)}: ${currentUser.name}`;
            }
        });

        // Update Landing Page (.landing-wrapper nav .register)
        const landingNavRegister = document.querySelector(".landing-wrapper nav .register, body > nav.nav .register");
        const isLandingPage = window.location.pathname.endsWith("index.html") || window.location.pathname === "/" || window.location.pathname === "";

        if (isLandingPage && landingNavRegister) {
            if (isAuthenticated() && currentUser && currentUser.name) {
                landingNavRegister.innerHTML = `
                    <span class="nav-user-greeting" style="color: #FFFFFF; font-weight: 700; font-size: 14px; margin-right: 6px;">
                        👤 ${escapeHtml(currentUser.name)}
                    </span>
                    <a href="${getDashboardUrlForRole(currentUser.role)}" class="stylish-btn ab-btn-primary">
                        Dashboard
                    </a>
                    <button type="button" class="stylish-btn ab-btn-secondary" onclick="AgriBridgeAuth.logout()">
                        Logout
                    </button>
                `;
            } else {
                landingNavRegister.innerHTML = `
                    <a href="/frontend/pages/login.html" class="stylish-btn ab-btn-secondary">
                        Login
                    </a>
                    <a href="/frontend/pages/signup.html" class="stylish-btn ab-btn-primary">
                        Get Started
                    </a>
                `;
            }
        }
    }

    // -------------------------------------------------------------------------
    // 5. PAGE AUTHENTICATION GUARD
    // -------------------------------------------------------------------------

    async function requireAuth(allowedRoles = []) {
        if (!isAuthenticated()) {
            const currentUrl = encodeURIComponent(window.location.pathname);
            window.location.href = `/frontend/pages/login.html?redirect=${currentUrl}`;
            return false;
        }

        // Verify fresh user record from database
        const user = await fetchCurrentUser();
        if (!user) {
            const currentUrl = encodeURIComponent(window.location.pathname);
            window.location.href = `/frontend/pages/login.html?redirect=${currentUrl}`;
            return false;
        }

        if (allowedRoles && allowedRoles.length > 0) {
            const roleAliasMap = {
                "professional": "field-agent",
                "field_agent": "field-agent",
                "field-agent": "field-agent",
                "farmer": "farmer",
                "buyer": "buyer"
            };

            const normalizedAllowed = allowedRoles.map(r => roleAliasMap[r.toLowerCase()] || r.toLowerCase());
            const userRole = (user.role || "").toLowerCase();
            const canonicalUserRole = roleAliasMap[userRole] || userRole;

            if (!normalizedAllowed.includes(canonicalUserRole)) {
                console.warn(`Unauthorized role access: user role '${userRole}' not in allowed:`, allowedRoles);
                window.location.href = getDashboardUrlForRole(userRole);
                return false;
            }
        }

        updateNavbarUser(user);
        return true;
    }

    // -------------------------------------------------------------------------
    // 6. LOGOUT ACTION
    // -------------------------------------------------------------------------

    async function logout() {
        try {
            const token = getToken();
            if (token) {
                await fetch("/api/auth/logout", {
                    method: "POST",
                    headers: {
                        "Authorization": `Bearer ${token}`,
                        "Content-Type": "application/json"
                    }
                });
            }
        } catch (err) {
            console.warn("Logout request error:", err);
        } finally {
            clearAuth();
            window.location.href = "/frontend/pages/login.html";
        }
    }

    // -------------------------------------------------------------------------
    // 7. HELPER API FETCH WITH AUTOMATIC BEARER TOKEN
    // -------------------------------------------------------------------------

    async function authFetch(url, options = {}) {
        const headers = options.headers || {};
        const token = getToken();
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }
        options.headers = headers;

        const response = await fetch(url, options);
        if (response.status === 401) {
            clearAuth();
            window.location.href = "/frontend/pages/login.html";
        }
        return response;
    }

    // -------------------------------------------------------------------------
    // 8. MOBILE NORMALIZATION UTILITY
    // -------------------------------------------------------------------------

    function normalizeMobile(mobile) {
        if (!mobile) return "";
        let cleaned = mobile.replace(/[^\d+]/g, "").trim();
        if (cleaned.startsWith("+")) cleaned = cleaned.substring(1);
        if (cleaned.startsWith("0") && cleaned.length === 11) cleaned = cleaned.substring(1);
        if (cleaned.startsWith("91") && cleaned.length === 12) cleaned = cleaned.substring(2);
        return cleaned;
    }

    // -------------------------------------------------------------------------
    // 9. AUTOMATIC INITIALIZATION & CROSS-TAB SYNC
    // -------------------------------------------------------------------------

    function init() {
        updateNavbarUser(getCurrentUser());
        if (getToken()) {
            fetchCurrentUser();
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

    async function demoLogin(role) {
        try {
            const res = await fetch("/api/auth/demo-login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ role: role })
            });
            if (res.ok) {
                const data = await res.json();
                if (data.success && data.token) {
                    setToken(data.token);
                    setCurrentUser(data.user);
                    window.location.href = getDashboardUrlForRole(role);
                    return true;
                }
            }
        } catch (e) {
            console.warn("Demo login API request error:", e);
        }

        // Fallback local mock
        const mockUser = {
            id: role === "field-agent" ? 999 : (role === "buyer" ? 888 : 1),
            name: role === "field-agent" ? "Field Agent Vikram" : (role === "buyer" ? "Buyer AgroCorp" : "Farmer Ramesh"),
            mobile: role === "field-agent" ? "+919876500003" : (role === "buyer" ? "+919876500002" : "+919876500001"),
            role: role
        };
        setToken("demo-token-" + role);
        setCurrentUser(mockUser);
        window.location.href = getDashboardUrlForRole(role);
        return true;
    }

    return {
        getToken,
        setToken,
        getCurrentUser,
        setCurrentUser,
        fetchCurrentUser,
        clearAuth,
        isAuthenticated,
        requireAuth,
        logout,
        demoLogin,
        authFetch,
        getDashboardUrlForRole,
        getRoleDisplayName,
        normalizeMobile,
        updateNavbarUser
    };
})();

// Attach to window object
window.AgriBridgeAuth = AgriBridgeAuth;
