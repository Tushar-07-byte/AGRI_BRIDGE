// =========================================
// GET HTML ELEMENTS
// =========================================

const cropImage = document.getElementById("crop-image");

const resultIcon = document.getElementById("result-icon");
const resultTitle = document.getElementById("result-title");
const resultMessage = document.getElementById("result-message");

const guidanceSection = document.getElementById("guidance-section");

const continueButton = document.getElementById("continue-button");
const resubmitButton = document.getElementById("resubmit-button");


// =========================================
// LOAD SAVED IMAGE
// =========================================

const savedImage = localStorage.getItem("cropImage");

if (savedImage) {
    cropImage.src = savedImage;
} else {
    console.log("No crop image found.");
}


// =========================================
// MOCK AI RESULT
// =========================================

// For now we are pretending that AI passed
const aiPassed = true;


// =========================================
// SHOW AI RESULT
// =========================================

if (aiPassed === true) {

    // PASS STATE

    resultIcon.textContent = "🌱";

    resultTitle.textContent = "AI Check Passed";

    resultMessage.textContent =
        "Your crop has passed the initial AI health check and is ready for field verification.";

    // Hide guidance
    guidanceSection.style.display = "none";

    // Show Continue
    continueButton.style.display = "block";

    // Hide Resubmit
    resubmitButton.style.display = "none";


} else {

    // FAIL STATE

    resultIcon.textContent = "⚠️";

    resultTitle.textContent = "Needs Attention";

    resultMessage.textContent =
        "The uploaded image needs another check before your crop can move forward.";

    // Show guidance
    guidanceSection.style.display = "block";

    // Hide Continue
    continueButton.style.display = "none";

    // Show Resubmit
    resubmitButton.style.display = "block";
}

// =========================================
// CONTINUE BUTTON
// =========================================

continueButton.addEventListener("click", function () {

    window.location.href = "verification-status.html";

}); 

// =========================================
// RESUBMIT BUTTON
// =========================================

resubmitButton.addEventListener("click", function () {

    window.location.href = "upload-crop.html";

});