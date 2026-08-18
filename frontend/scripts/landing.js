let button = document.getElementById("get-started");

button.addEventListener("click", function () {
    document
        .getElementById("how-it-works")
        .scrollIntoView({
            behavior: "smooth"
        });
});

let demo_button = document.getElementById("demo");

demo_button.addEventListener("click", function () {
    document
        .getElementById("demo-workflow")
        .scrollIntoView({
            behavior: "smooth"
        });
});

