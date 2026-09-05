// =========================================
// AGRIBRIDGE — REUSABLE LANGUAGE SELECTOR
// =========================================

function createLanguageSelector() {
    const currentLang = getCurrentLanguage();

    // Create selector container
    const container = document.createElement("div");
    container.classList.add("language-selector-container");

    // Create globe icon + label
    const label = document.createElement("span");
    label.classList.add("lang-label");
    label.textContent = "🌐";

    // Create select element
    const select = document.createElement("select");
    select.classList.add("lang-select");
    select.setAttribute("aria-label", "Select language");

    // Add language options
    Object.keys(SUPPORTED_LANGUAGES).forEach(function (code) {
        const option = document.createElement("option");
        option.value = code;
        option.textContent = SUPPORTED_LANGUAGES[code];

        if (code === currentLang) {
            option.selected = true;
        }

        select.appendChild(option);
    });

    // Handle language change
    select.addEventListener("change", function () {
        setLanguage(select.value);
    });

    // Assemble
    container.appendChild(label);
    container.appendChild(select);

    return container;
}


// =========================================
// INJECT LANGUAGE SELECTOR INTO NAV
// =========================================

function injectLanguageSelector() {
    // Find all navigation bars
    const navs = document.querySelectorAll("nav.nav");

    navs.forEach(function (nav) {
        // Check if selector already exists
        if (nav.querySelector(".language-selector-container")) {
            return;
        }

        // Find the register/user section
        const registerSection = nav.querySelector(".register");

        if (registerSection) {
            // Insert inside the register section so it clusters with action buttons
            registerSection.prepend(createLanguageSelector());
        }
    });

    // Also handle pages without nav (standalone pages)
    const standalonePages = document.querySelectorAll(
        ".analysis-page, .verification-page, .verification-card, .review-page, .profile-page, .signup-card, main.container"
    );

    standalonePages.forEach(function (page) {
        if (!page.querySelector(".language-selector-container")) {
            const selector = createLanguageSelector();
            selector.style.position = "fixed";
            selector.style.top = "10px";
            selector.style.right = "10px";
            selector.style.zIndex = "1000";
            selector.style.background = "white";
            selector.style.padding = "6px 12px";
            selector.style.borderRadius = "8px";
            selector.style.boxShadow = "0 2px 8px rgba(0,0,0,0.15)";
            page.prepend(selector);
        }
    });
}


// =========================================
// INITIALIZE ON DOM READY
// =========================================

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
        // Small delay to let i18n initialize first
        setTimeout(injectLanguageSelector, 100);
    });
} else {
    setTimeout(injectLanguageSelector, 100);
}
