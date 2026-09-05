// =========================================
// FIELD AGENT HELP
// =========================================


// =========================================
// GET HTML ELEMENTS
// =========================================

const agentsContainer =
    document.getElementById("agents-container");

const requestMessage =
    document.getElementById("request-message");

const backDashboard =
    document.getElementById("back-dashboard");


// =========================================
// FIELD AGENTS
// =========================================
// Temporary frontend data.
// Backend will eventually provide this.

const fieldAgents = [

    {
        id: 1,
        name: "Rajesh Kumar",
        specialization: "Crop Health & Disease",
        location: "Bhopal",
        status: "Available"
    },

    {
        id: 2,
        name: "Amit Sharma",
        specialization: "Soil & Irrigation",
        location: "Sehore",
        status: "Available"
    },

    {
        id: 3,
        name: "Suresh Patel",
        specialization: "Crop Management",
        location: "Vidisha",
        status: "Available"
    }

];


// =========================================
// DISPLAY AGENTS
// =========================================

fieldAgents.forEach(function (agent) {

    createAgentCard(agent);

});


// =========================================
// CREATE AGENT CARD
// =========================================

function createAgentCard(agent) {

    const card =
        document.createElement("div");

    card.classList.add("agent-card");


    // =====================================
    // PROFILE
    // =====================================

    const profile =
        document.createElement("div");

    profile.classList.add("agent-profile");


    const avatar =
        document.createElement("div");

    avatar.classList.add("agent-avatar");

    avatar.textContent = "🧑‍🌾";


    const profileText =
        document.createElement("div");


    const name =
        document.createElement("h3");

    name.textContent =
        agent.name;


    const role =
        document.createElement("span");

    role.classList.add("agent-role");

    role.textContent =
        "Field Agent";


    profileText.appendChild(name);

    profileText.appendChild(role);

    profile.appendChild(avatar);

    profile.appendChild(profileText);


    // =====================================
    // SPECIALIZATION
    // =====================================

    const specialization =
        document.createElement("p");

    specialization.classList.add(
        "agent-specialization"
    );

    specialization.textContent =
        `🌱 ${agent.specialization}`;


    // =====================================
    // LOCATION
    // =====================================

    const location =
        document.createElement("p");

    location.classList.add(
        "agent-location"
    );

    location.textContent =
        `📍 ${agent.location}`;


    // =====================================
    // STATUS
    // =====================================

    const status =
        document.createElement("span");

    status.classList.add(
        "agent-status"
    );

    status.textContent =
        `● ${agent.status}`;


    // =====================================
    // REQUEST BUTTON
    // =====================================

    const requestButton =
        document.createElement("button");

    requestButton.classList.add(
        "request-button"
    );

    requestButton.textContent =
        typeof translate === "function" ? translate("fieldAgentHelp.requestHelp") : "Request Help";


    requestButton.addEventListener(
        "click",
        function () {

            requestHelp(
                agent,
                requestButton
            );

        }
    );


    // =====================================
    // ADD ELEMENTS
    // =====================================

    card.appendChild(profile);

    card.appendChild(specialization);

    card.appendChild(location);

    card.appendChild(status);

    card.appendChild(requestButton);


    agentsContainer.appendChild(card);

}


// =========================================
// REQUEST HELP
// =========================================

function requestHelp(agent, button) {

    const farmerProfile =
        localStorage.getItem(
            "farmerProfile"
        );


    // =====================================
    // CHECK FARMER PROFILE
    // =====================================

    if (!farmerProfile) {

        requestMessage.textContent =
            typeof translate === "function" ? translate("fieldAgentHelp.profileRequired") : "Please complete your farmer profile first.";

        requestMessage.style.color =
            "#c62828";

        return;

    }


    const farmer =
        JSON.parse(farmerProfile);


    // =====================================
    // CREATE HELP REQUEST
    // =====================================

    const helpRequest = {

        farmerName:
            farmer.name,

        farmArea:
            farmer.farmArea,

        farmLocation:
            farmer.location,

        agentId:
            agent.id,

        agentName:
            agent.name,

        specialization:
            agent.specialization,

        status:
            "pending",

        requestedAt:
            new Date().toISOString()

    };


    // =====================================
    // SAVE REQUEST
    // =====================================

    localStorage.setItem(
        "fieldAgentHelpRequest",
        JSON.stringify(helpRequest)
    );


    // =====================================
    // UPDATE BUTTON
    // =====================================

    button.textContent =
        typeof translate === "function" ? translate("fieldAgentHelp.helpRequested") : "✓ Help Requested";

    button.disabled = true;


    // =====================================
    // MESSAGE
    // =====================================

    requestMessage.textContent =
        `${typeof translate === "function" ? translate("fieldAgentHelp.requestSentTo") : "Help request sent to"} ${agent.name}.`;

    requestMessage.style.color =
        "#2E7D32";


    console.log(
        "Field agent help request:",
        helpRequest
    );

}


// =========================================
// BACK TO DASHBOARD
// =========================================

backDashboard.addEventListener(
    "click",
    function () {

        window.location.href =
            "/frontend/pages/farmer-dashboard.html";

    }
);