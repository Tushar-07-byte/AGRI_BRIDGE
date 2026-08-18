document.addEventListener("DOMContentLoaded", () => {
    // Grab the form and the select dropdown
    const roleForm = document.getElementById("role-form");
    const roleSelect = document.getElementById("choose-role");

    // Listen for the form submission rather than just the button click
    roleForm.addEventListener("submit", function (event) {
        
        // This stops the page from reloading when the form is submitted
        event.preventDefault(); 

        // Your exact routing logic
        if (roleSelect.value === "farmer") {
            window.location.href = "farmer-dashboard.html";
        } 
        else if (roleSelect.value === "buyer") {
            window.location.href = "buyer-dashboard.html";
        } 
        else if (roleSelect.value === "field-agent") {
            window.location.href = "field-agent-dashboard.html";
        } 
        else {
            alert("Please select a role.");
        }
    });
});