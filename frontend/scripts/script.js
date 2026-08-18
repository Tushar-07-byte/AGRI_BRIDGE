let cropName = document.getElementById('cropname');
let quantity = document.getElementById('quantity');
let harvestDate = document.getElementById("date");
let farmLocation = document.getElementById('location');
let cropImage = document.getElementById('cropImage');
let submitButton = document.getElementById('submit');
let category = document.getElementById('cropCategory');
let message = document.getElementById('message');
let preview = document.getElementById('preview');

submitButton.addEventListener("click", function () {

    if (cropName.value === "") {
        message.textContent = "Please enter the crop name.";
        return;
    }

    console.log(cropName.value);
    console.log(quantity.value);
    console.log(harvestDate.value);
    console.log(farmLocation.value);
    console.log(category.value);

    message.textContent = "Listing submitted successfully!";

    let listing = {
        cropName: cropName.value,
        quantity: quantity.value,
        harvestDate: harvestDate.value,
        location: farmLocation.value
    }

    console.log(listing)

    cropName.value = "";
    quantity.value = "";
    farmLocation.value = "";
    harvestDate.value = "";
    cropImage.value = "";
    preview.src = "";



});

cropImage.addEventListener("change", function () {
    let file = cropImage.files[0];
    preview.src = URL.createObjectURL(file);
});

let apiResponse = {

cropName : "Tomato",

health : "Healthy",

confidence : 96

};

console.log(apiResponse.cropName)
console.log(apiResponse.health)
console.log(apiResponse.confidence)

let listings = [

{

name:"Tomato",

confidence:96

},

{

name:"Rice",

confidence:94

}

];

for (let index = 0; index < listings.length; index++) {
    console.log(listings[index].name)
}