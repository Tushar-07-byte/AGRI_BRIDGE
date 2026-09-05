// =========================================================
// AGRIBRIDGE — LANDING PAGE SCRIPT (VIDEO FIX STATE)
// =========================================================

document.addEventListener("DOMContentLoaded", function () {
    console.log("=== AGRIBRIDGE LANDING PAGE INITIALIZED ===");

    // 1. HERO VIDEO AUTOPLAY CONTROLLER
    const heroVideo = document.querySelector(".hero-video") || document.getElementById("hero-bg-video");

    if (heroVideo) {
        heroVideo.muted = true;
        heroVideo.defaultMuted = true;
        heroVideo.playsInline = true;
        heroVideo.setAttribute("playsinline", "");
        heroVideo.setAttribute("webkit-playsinline", "");
        heroVideo.loop = true;

        const attemptPlay = () => {
            const playPromise = heroVideo.play();
            if (playPromise !== undefined) {
                playPromise
                    .then(() => {
                        console.log("✓ AgriBridge Hero Background Video is actively playing.");
                    })
                    .catch((err) => {
                        console.warn("Autoplay deferred:", err.message);
                        const triggerPlay = () => {
                            heroVideo.play().catch(() => {});
                            document.removeEventListener("click", triggerPlay);
                            document.removeEventListener("touchstart", triggerPlay);
                        };
                        document.addEventListener("click", triggerPlay, { once: true });
                        document.addEventListener("touchstart", triggerPlay, { once: true });
                    });
            }
        };

        heroVideo.load();
        attemptPlay();

        document.addEventListener("visibilitychange", function () {
            if (document.visibilityState === "visible" && heroVideo.paused) {
                attemptPlay();
            }
        });
    }

    // 2. NAVBAR SCROLL ELEVATION
    const nav = document.querySelector("nav.nav");
    if (nav) {
        window.addEventListener("scroll", function () {
            if (window.scrollY > 40) {
                nav.classList.add("scrolled");
            } else {
                nav.classList.remove("scrolled");
            }
        }, { passive: true });
    }

    // 3. SMOOTH SCROLLING FOR INTERNAL LINKS
    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener("click", function (e) {
            const targetId = this.getAttribute("href");
            if (targetId && targetId !== "#") {
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    e.preventDefault();
                    targetElement.scrollIntoView({
                        behavior: "smooth",
                        block: "start"
                    });
                }
            }
        });
    });
});
