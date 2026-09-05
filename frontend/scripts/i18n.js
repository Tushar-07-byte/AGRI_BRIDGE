// =========================================
// AGRIBRIDGE i18n — MASTER INTERNATIONALIZATION ENGINE
// =========================================

// Supported languages with native script names
const SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "हिन्दी (Hindi)",
    "mr": "मराठी (Marathi)",
    "pa": "ਪੰਜਾਬੀ (Punjabi)",
    "bn": "বাংলা (Bengali)",
    "te": "తెలుగు (Telugu)",
    "ta": "தமிழ் (Tamil)",
    "kn": "ಕನ್ನಡ (Kannada)",
    "ml": "മലയാളം (Malayalam)",
    "gu": "ગુજરાતી (Gujarati)",
    "or": "ଓଡ଼ିଆ (Odia)"
};

// Default language
const DEFAULT_LANGUAGE = "en";

// Translation cache by language code
let translationCache = {};
let phraseMap = {}; // Lowercase English phrase -> Translated string

// Current language
let currentLanguage = DEFAULT_LANGUAGE;
let isTranslating = false;

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
// BUILD PHRASE MAP FROM EN -> TARGET
// =========================================

function buildPhraseMap(enData, targetData) {
    phraseMap = {};
    if (!enData || !targetData) return;

    function extract(enObj, targetObj) {
        for (const key in enObj) {
            if (
                typeof enObj[key] === "object" && enObj[key] !== null &&
                typeof targetObj[key] === "object" && targetObj[key] !== null
            ) {
                extract(enObj[key], targetObj[key]);
            } else if (
                typeof enObj[key] === "string" &&
                typeof targetObj[key] === "string"
            ) {
                const enStr = enObj[key].trim();
                const targetStr = targetObj[key].trim();
                if (enStr && targetStr && enStr !== targetStr) {
                    phraseMap[enStr.toLowerCase()] = targetStr;
                }
            }
        }
    }
    extract(enData, targetData);
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

    // Load master English (for fallback & phrase mapping)
    if (!translationCache[DEFAULT_LANGUAGE]) {
        await loadTranslation(DEFAULT_LANGUAGE);
    }

    // Load translation if not cached
    if (!translationCache[language]) {
        await loadTranslation(language);
    }

    // Build English -> Target phrase mapping
    buildPhraseMap(translationCache[DEFAULT_LANGUAGE], translationCache[language]);

    // Apply translations to the page
    applyTranslations();

    // Update language selector UI
    updateLanguageSelectorUI();

    // Dispatch event for other scripts
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
    if (translationCache[language]) {
        return translationCache[language];
    }

    try {
        const response = await fetch(`/frontend/translations/${language}.json`);
        if (!response.ok) {
            console.warn(`Failed to load translation for ${language}: ${response.status}`);
            return null;
        }

        const data = await response.json();
        translationCache[language] = data;
        return data;
    } catch (error) {
        console.warn(`Error loading translation for ${language}:`, error);
        return null;
    }
}

// =========================================
// TRANSLATE A KEY
// =========================================

function translate(key, fallback) {
    if (!key) return fallback || "";

    // Try current language first
    let result = getNestedValue(translationCache[currentLanguage], key);
    if (result !== undefined && result !== null) {
        return result;
    }

    // Fallback to English
    if (currentLanguage !== DEFAULT_LANGUAGE) {
        result = getNestedValue(translationCache[DEFAULT_LANGUAGE], key);
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
        if (current === undefined || current === null || typeof current !== "object") {
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
    if (isTranslating) return;
    isTranslating = true;

    try {
        // 1. Explicit data-i18n attributes
        document.querySelectorAll("[data-i18n]").forEach(function (element) {
            const key = element.getAttribute("data-i18n");
            const translated = translate(key);
            if (translated && translated !== key) {
                if (!element.querySelector("[data-i18n]")) {
                    element.textContent = translated;
                }
            }
        });

        // 2. Explicit data-i18n-placeholder
        document.querySelectorAll("[data-i18n-placeholder]").forEach(function (element) {
            const key = element.getAttribute("data-i18n-placeholder");
            const translated = translate(key);
            if (translated && translated !== key) {
                element.placeholder = translated;
            }
        });

        // 3. Explicit data-i18n-title
        document.querySelectorAll("[data-i18n-title]").forEach(function (element) {
            const key = element.getAttribute("data-i18n-title");
            const translated = translate(key);
            if (translated && translated !== key) {
                element.title = translated;
            }
        });

        // 4. Explicit data-i18n-aria
        document.querySelectorAll("[data-i18n-aria]").forEach(function (element) {
            const key = element.getAttribute("data-i18n-aria");
            const translated = translate(key);
            if (translated && translated !== key) {
                element.setAttribute("aria-label", translated);
            }
        });

        // 5. Explicit select options
        document.querySelectorAll("select[data-i18n-options]").forEach(function (select) {
            const optionsMap = select.getAttribute("data-i18n-options");
            try {
                const mapping = JSON.parse(optionsMap);
                Array.from(select.options).forEach(function (option) {
                    const optKey = mapping[option.value];
                    if (optKey) {
                        const translated = translate(optKey);
                        if (translated && translated !== optKey) {
                            option.textContent = translated;
                        }
                    }
                });
            } catch (e) {}
        });

        // 6. Comprehensive Auto-Translation for General UI elements
        const candidateSelectors = "h1, h2, h3, h4, h5, h6, p, span, a, button, label, th, td, div.ab-badge, .kpi-label, .card-title, .quick-chip, .btn-text, .chip-label, .welcome-sub";
        const uiElements = document.querySelectorAll(candidateSelectors);

        uiElements.forEach(function (el) {
            // Ignore script, code, inputs, language selector itself
            if (
                el.closest(".language-selector-container") ||
                el.closest("select") ||
                el.tagName === "INPUT" ||
                el.tagName === "TEXTAREA" ||
                el.tagName === "SCRIPT" ||
                el.tagName === "STYLE" ||
                el.tagName === "CODE"
            ) {
                return;
            }

            // Only translate leaf text nodes or elements without complex child structures
            if (el.children.length === 0) {
                let orig = el.getAttribute("data-orig-text");
                if (orig === null) {
                    orig = el.textContent.trim();
                    if (orig) {
                        el.setAttribute("data-orig-text", orig);
                    }
                }

                if (orig) {
                    if (currentLanguage === DEFAULT_LANGUAGE) {
                        el.textContent = orig;
                    } else {
                        const lowerOrig = orig.toLowerCase();
                        if (phraseMap[lowerOrig]) {
                            el.textContent = phraseMap[lowerOrig];
                        }
                    }
                }
            } else {
                // If element has text child nodes along with icons/tags, translate individual text nodes
                Array.from(el.childNodes).forEach(function (node) {
                    if (node.nodeType === Node.TEXT_NODE) {
                        const raw = node.textContent.trim();
                        if (raw.length > 1) {
                            const lowerRaw = raw.toLowerCase();
                            if (currentLanguage === DEFAULT_LANGUAGE) {
                                // No op
                            } else if (phraseMap[lowerRaw]) {
                                node.textContent = node.textContent.replace(raw, phraseMap[lowerRaw]);
                            }
                        }
                    }
                });
            }
        });

    } finally {
        isTranslating = false;
    }
}

// =========================================
// UPDATE LANGUAGE SELECTOR UI
// =========================================

function updateLanguageSelectorUI() {
    document.querySelectorAll(".lang-select").forEach(function (select) {
        select.value = currentLanguage;
    });
}

// =========================================
// DOM MUTATION OBSERVER (DYNAMIC JS RENDERING)
// =========================================

let mutationTimeout = null;
function setupMutationObserver() {
    if (typeof MutationObserver === "undefined") return;
    const observer = new MutationObserver(function (mutations) {
        if (currentLanguage === DEFAULT_LANGUAGE) return;
        if (mutationTimeout) clearTimeout(mutationTimeout);
        mutationTimeout = setTimeout(function () {
            applyTranslations();
        }, 60);
    });
    observer.observe(document.body, { childList: true, subtree: true });
}

// =========================================
// INITIALIZE i18n ON PAGE LOAD
// =========================================

async function initI18n() {
    currentLanguage = getCurrentLanguage();
    document.documentElement.lang = currentLanguage;

    // Load English master
    await loadTranslation(DEFAULT_LANGUAGE);

    // Load target language if not English
    if (currentLanguage !== DEFAULT_LANGUAGE) {
        await loadTranslation(currentLanguage);
        buildPhraseMap(translationCache[DEFAULT_LANGUAGE], translationCache[currentLanguage]);
    }

    // Apply translations
    applyTranslations();
    updateLanguageSelectorUI();
    setupMutationObserver();

    console.log("i18n initialized:", currentLanguage);
}

// Export global helper
window.AgriBridgeI18n = {
    setLanguage: setLanguage,
    getCurrentLanguage: getCurrentLanguage,
    translate: translate,
    applyTranslations: applyTranslations,
    SUPPORTED_LANGUAGES: SUPPORTED_LANGUAGES
};

// Auto-initialize
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initI18n);
} else {
    initI18n();
}

