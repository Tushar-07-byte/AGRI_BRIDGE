// =========================================
// AGRIBRIDGE i18n — INTERNATIONALIZATION ENGINE
// =========================================

// Supported languages with native script names
const SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "हिन्दी",
    "mr": "मराठी",
    "bn": "বাংলা",
    "te": "తెలుగు",
    "ta": "தமிழ்",
    "kn": "ಕನ್ನಡ",
    "ml": "മലയാളം",
    "gu": "ગુજરાતી",
    "pa": "ਪੰਜਾਬੀ",
    "or": "ଓଡ଼ିଆ"
};

// Default language
const DEFAULT_LANGUAGE = "en";

// Translation cache
let translationCache = {};

// Current language
let currentLanguage = DEFAULT_LANGUAGE;


// =========================================
// GET CURRENT LANGUAGE
// =========================================

function getCurrentLanguage() {
    const saved = localStorage.getItem("selectedLanguage");

    if (saved && SUPPORTED_LANGUAGES[saved]) {
        return saved;
    }

    return DEFAULT_LANGUAGE;
}


// =========================================
// SET LANGUAGE
// =========================================

async function setLanguage(language) {
    if (!SUPPORTED_LANGUAGES[language]) {
        console.warn("Unsupported language:", language);
        language = DEFAULT_LANGUAGE;
    }

    currentLanguage = language;
    localStorage.setItem("selectedLanguage", language);

    // Update document lang attribute
    document.documentElement.lang = language;

    // Load translation if not cached
    if (!translationCache[language]) {
        await loadTranslation(language);
    }

    // Apply translations to the page
    applyTranslations();

    // Update language selector if it exists
    updateLanguageSelectorUI();

    // Dispatch event for other scripts to listen to
    window.dispatchEvent(
        new CustomEvent("languageChanged", {
            detail: { language: language }
        })
    );
}


// =========================================
// LOAD TRANSLATION FILE
// =========================================

async function loadTranslation(language) {
    // Return cached translation if available
    if (translationCache[language]) {
        return translationCache[language];
    }

    try {
        const response = await fetch(
            `/frontend/translations/${language}.json`
        );

        if (!response.ok) {
            console.warn(
                `Failed to load translation for ${language}: ${response.status}`
            );
            return null;
        }

        const data = await response.json();
        translationCache[language] = data;
        return data;

    } catch (error) {
        console.warn(
            `Error loading translation for ${language}:`,
            error
        );
        return null;
    }
}


// =========================================
// TRANSLATE A KEY
// =========================================

function translate(key, fallback) {
    if (!key) return fallback || "";

    // Try current language first
    let result = getNestedValue(
        translationCache[currentLanguage],
        key
    );

    if (result !== undefined && result !== null) {
        return result;
    }

    // Fallback to English
    if (currentLanguage !== DEFAULT_LANGUAGE) {
        result = getNestedValue(
            translationCache[DEFAULT_LANGUAGE],
            key
        );

        if (result !== undefined && result !== null) {
            return result;
        }
    }

    // Return fallback or the key itself
    return fallback || key;
}


// =========================================
// GET NESTED VALUE FROM OBJECT
// =========================================

function getNestedValue(obj, key) {
    if (!obj) return undefined;

    const keys = key.split(".");
    let current = obj;

    for (let i = 0; i < keys.length; i++) {
        if (
            current === undefined ||
            current === null ||
            typeof current !== "object"
        ) {
            return undefined;
        }
        current = current[keys[i]];
    }

    return current;
}


// =========================================
// APPLY TRANSLATIONS TO DOM
// =========================================

function applyTranslations() {
    // Translate text content
    document.querySelectorAll("[data-i18n]").forEach(
        function (element) {
            const key = element.getAttribute("data-i18n");
            const translated = translate(key);

            if (translated && translated !== key) {
                // Preserve child elements with their own i18n
                const hasChildrenWithI18n =
                    element.querySelector("[data-i18n]");

                if (!hasChildrenWithI18n) {
                    element.textContent = translated;
                }
            }
        }
    );

    // Translate placeholders
    document.querySelectorAll("[data-i18n-placeholder]").forEach(
        function (element) {
            const key =
                element.getAttribute("data-i18n-placeholder");
            const translated = translate(key);

            if (translated && translated !== key) {
                element.placeholder = translated;
            }
        }
    );

    // Translate title attributes
    document.querySelectorAll("[data-i18n-title]").forEach(
        function (element) {
            const key =
                element.getAttribute("data-i18n-title");
            const translated = translate(key);

            if (translated && translated !== key) {
                element.title = translated;
            }
        }
    );

    // Translate aria-label attributes
    document.querySelectorAll("[data-i18n-aria]").forEach(
        function (element) {
            const key =
                element.getAttribute("data-i18n-aria");
            const translated = translate(key);

            if (translated && translated !== key) {
                element.setAttribute("aria-label", translated);
            }
        }
    );

    // Translate select option text
    document.querySelectorAll("select[data-i18n-options]").forEach(
        function (select) {
            const optionsMap =
                select.getAttribute("data-i18n-options");

            try {
                const mapping = JSON.parse(optionsMap);

                Array.from(select.options).forEach(
                    function (option) {
                        const optKey = mapping[option.value];

                        if (optKey) {
                            const translated = translate(optKey);

                            if (translated && translated !== optKey) {
                                option.textContent = translated;
                            }
                        }
                    }
                );
            } catch (e) {
                // Invalid JSON, skip
            }
        }
    );
}


// =========================================
// UPDATE LANGUAGE SELECTOR UI
// =========================================

function updateLanguageSelectorUI() {
    document.querySelectorAll(".lang-select").forEach(
        function (select) {
            select.value = currentLanguage;
        }
    );
}


// =========================================
// INITIALIZE i18n ON PAGE LOAD
// =========================================

async function initI18n() {
    currentLanguage = getCurrentLanguage();
    document.documentElement.lang = currentLanguage;

    // Load English first (fallback)
    await loadTranslation(DEFAULT_LANGUAGE);

    // Load current language if not English
    if (currentLanguage !== DEFAULT_LANGUAGE) {
        await loadTranslation(currentLanguage);
    }

    // Apply translations
    applyTranslations();

    // Update language selector
    updateLanguageSelectorUI();

    console.log("i18n initialized:", currentLanguage);
}


// =========================================
// AUTO-INITIALIZE
// =========================================

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initI18n);
} else {
    initI18n();
}
