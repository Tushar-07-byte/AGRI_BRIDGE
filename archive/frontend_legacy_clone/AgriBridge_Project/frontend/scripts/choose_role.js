document.addEventListener("DOMContentLoaded", () => {

    const roleForm =
        document.getElementById("role-form");

    const roleSelect =
        document.getElementById("choose-role");


    roleForm.addEventListener(
        "submit",
        function (event) {

            event.preventDefault();

            try {
                const selectedRole = roleSelect.value;
                const newLog = {
                    id: `LOG-${Math.floor(500 + Math.random() * 499)}`,
                    user: `${selectedRole.toUpperCase()} Team Session`,
                    role: selectedRole,
                    ip: "Local Network",
                    device: navigator.userAgent.includes("Mobile") ? "Mobile Device" : "Desktop Browser",
                    time: "Today " + new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
                    status: "Successful"
                };
                const existingLogs = JSON.parse(localStorage.getItem("agribridge_live_logins") || "[]");
                existingLogs.unshift(newLog);
                localStorage.setItem("agribridge_live_logins", JSON.stringify(existingLogs.slice(0, 30)));
            } catch (e) {}

            if (roleSelect.value === "farmer") {

                window.location.href =
                    "/frontend/pages/farmer-details.html";

            }

            else if (roleSelect.value === "buyer") {

                window.location.href =
                    "/frontend/pages/buyer-dashboard.html";

            }

            else if (roleSelect.value === "field-agent") {

                window.location.href =
                    "/frontend/pages/field-agent-dashboard.html";

            }

            else if (roleSelect.value === "admin") {

                window.location.href =
                    "/frontend/pages/admin-dashboard.html";

            }

            else {

                alert(
                    "Please select a role."
                );

            }

        }
    );

});