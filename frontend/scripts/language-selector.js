// =========================================
// AGRIBRIDGE — REUSABLE LANGUAGE SELECTOR
// =========================================

function createLanguageSelector() {
    const currentLang = typeof getCurrentLanguage === "function" ? getCurrentLanguage() : (localStorage.getItem("selectedLanguage") || "en");
    const langs = typeof SUPPORTED_LANGUAGES !== "undefined" ? SUPPORTED_LANGUAGES : {
        "en": "English", "hi": "हिन्दी (Hindi)", "mr": "मराठी (Marathi)", "pa": "ਪੰਜਾਬੀ (Punjabi)",
        "bn": "বাংলা (Bengali)", "te": "తెలుగు (Telugu)", "ta": "தமிழ் (Tamil)", "kn": "ಕನ್ನಡ (Kannada)",
        "ml": "മലയാളം (Malayalam)", "gu": "ગુજરાતી (Gujarati)", "or": "ଓଡ଼ିଆ (Odia)"
    };

    // Create selector container
    const container = document.createElement("div");
    container.classList.add("language-selector-container");
    container.style.display = "inline-flex";
    container.style.alignItems = "center";
    container.style.gap = "6px";
    container.style.margin = "0 8px";

    // Create globe icon + label
    const label = document.createElement("span");
    label.classList.add("lang-label");
    label.textContent = "🌐";
    label.style.fontSize = "16px";

    // Create select element
    const select = document.createElement("select");
    select.classList.add("lang-select");
    select.setAttribute("aria-label", "Select language");
    select.style.padding = "6px 10px";
    select.style.borderRadius = "8px";
    select.style.border = "1px solid #cbd5e1";
    select.style.background = "#ffffff";
    select.style.color = "#1e293b";
    select.style.fontSize = "13px";
    select.style.fontWeight = "600";
    select.style.cursor = "pointer";
    select.style.outline = "none";

    // Add language options
    Object.keys(langs).forEach(function (code) {
        const option = document.createElement("option");
        option.value = code;
        option.textContent = langs[code];

        if (code === currentLang) {
            option.selected = true;
        }

        select.appendChild(option);
    });

    // Handle language change
    select.addEventListener("change", function () {
        if (typeof setLanguage === "function") {
            setLanguage(select.value);
        } else {
            localStorage.setItem("selectedLanguage", select.value);
            window.dispatchEvent(new CustomEvent("languageChanged", { detail: { language: select.value } }));
        }
    });

    // Assemble
    container.appendChild(label);
    container.appendChild(select);

    return container;
}


// =========================================
// INJECT LANGUAGE SELECTOR INTO NAV / PAGES
// =========================================

function injectLanguageSelector() {
    // 1. Populate any explicit containers
    const explicitContainers = document.querySelectorAll("#language-selector-container, .language-selector-container");
    explicitContainers.forEach(function (container) {
        if (!container.querySelector(".lang-select")) {
            const selector = createLanguageSelector();
            container.appendChild(selector);
        }
    });

    // 2. Find all navigation bars
    const navs = document.querySelectorAll("nav.nav, header.nav, .navbar, .top-nav");

    navs.forEach(function (nav) {
        if (nav.querySelector(".lang-select")) {
            return;
        }

        const registerSection = nav.querySelector(".register, .nav-actions, .user-actions, .right-side");

        if (registerSection) {
            registerSection.prepend(createLanguageSelector());
        } else {
            nav.appendChild(createLanguageSelector());
        }
    });

    // 3. Handle standalone pages without nav
    const standalonePages = document.querySelectorAll(
        ".analysis-page, .verification-page, .verification-card, .review-page, .profile-page, .signup-card, main.container"
    );

    standalonePages.forEach(function (page) {
        if (!page.querySelector(".lang-select") && !document.querySelector("nav .lang-select")) {
            const selector = createLanguageSelector();
            selector.style.position = "fixed";
            selector.style.top = "12px";
            selector.style.right = "12px";
            selector.style.zIndex = "9999";
            selector.style.background = "#ffffff";
            selector.style.padding = "6px 12px";
            selector.style.borderRadius = "10px";
            selector.style.boxShadow = "0 4px 14px rgba(0,0,0,0.15)";
            page.prepend(selector);
        }
    });
}


// =========================================
// INITIALIZE ON DOM READY
// =========================================

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
        setTimeout(injectLanguageSelector, 50);
    });
} else {
    setTimeout(injectLanguageSelector, 50);
}

