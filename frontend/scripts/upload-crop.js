// =========================================
// Upload Crop - Frontend JavaScript
// =========================================


// Get HTML elements
const cropForm = document.getElementById("crop-form");

const cropName = document.getElementById("crop-name");
const quantity = document.getElementById("quantity");
const harvestDate = document.getElementById("harvest-date");
const locationInput = document.getElementById("location");

const cropImage = document.getElementById("crop-image");
const imagePreview = document.getElementById("image-preview");

const message = document.getElementById("message");


// =========================================
// 1. IMAGE PREVIEW
// =========================================

cropImage.addEventListener("change", function () {

    // Get selected file
    const file = cropImage.files[0];

    // If no file is selected
    if (!file) {
        imagePreview.style.display = "none";
        imagePreview.src = "";
        return;
    }

    // Make sure selected file is an image
    if (!file.type.startsWith("image/")) {
        message.textContent = "Please select a valid image.";
        imagePreview.style.display = "none";
        return;
    }

    // Create temporary URL for selected image
    const imageURL = URL.createObjectURL(file);

    // Show image in preview
    imagePreview.src = imageURL;
    imagePreview.style.display = "block";

    // Clear previous message
    message.textContent = "";
});


// =========================================
// 2. FORM SUBMISSION
// =========================================

cropForm.addEventListener("submit", function (event) {

    // Stop the page from refreshing
    event.preventDefault();

    // Get form values
    const crop = cropName.value.trim();
    const amount = quantity.value;
    const date = harvestDate.value;
    const farmLocation = locationInput.value.trim();
    const image = cropImage.files[0];


    // =====================================
    // Validation
    // =====================================

    if (!crop || !amount || !date || !farmLocation || !image) {

        message.textContent = "Please fill in all fields.";

        return;
    }


    // =====================================
    // Crop data
    // =====================================

    const cropData = {
        cropName: crop,
        quantity: Number(amount),
        harvestDate: date,
        location: farmLocation,
        status: "pending"
    };


    // =====================================
    // Convert image to Base64
    // =====================================

    const reader = new FileReader();

    reader.onload = function () {

        // Save image
        localStorage.setItem(
            "cropImage",
            reader.result
        );

        // Save crop details
        localStorage.setItem(
            "cropData",
            JSON.stringify(cropData)
        );

        console.log("Crop data:", cropData);
        console.log("Image saved successfully.");

        // Go to AI result page
        window.location.href = "ai-result.html";
    };


    // Start reading the image
    reader.readAsDataURL(image);

});

