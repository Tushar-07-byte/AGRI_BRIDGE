// =========================================
// AGRIBRIDGE WEATHER SYSTEM
// =========================================


// =========================================
// HTML ELEMENTS
// =========================================

const weatherLocation =
    document.getElementById("weather-location");

const weatherUpdated =
    document.getElementById("weather-updated");

const weatherIcon =
    document.getElementById("weather-icon");

const currentTemperature =
    document.getElementById("current-temperature");

const rainProbability =
    document.getElementById("rain-probability");

const windSpeed =
    document.getElementById("wind-speed");

const humidity =
    document.getElementById("humidity");

const forecastContainer =
    document.getElementById("forecast-container");


// =========================================
// DEFAULT LOCATION
// =========================================

const defaultLocation = {

    city: "Bhopal, Madhya Pradesh",

    latitude: 23.2599,

    longitude: 77.4126

};


// =========================================
// START WEATHER SYSTEM
// =========================================

initializeWeather();


// =========================================
// INITIALIZE WEATHER
// =========================================

async function initializeWeather() {

    let farmLocation =
        defaultLocation;


    // =====================================
    // GET FARMER PROFILE
    // =====================================

    const savedProfile =
        localStorage.getItem("farmerProfile");


    if (savedProfile) {

        try {

            const farmerProfile =
                JSON.parse(savedProfile);


            const location =
                farmerProfile.location
                    ? farmerProfile.location.trim()
                    : "";


            const state =
                farmerProfile.state
                    ? farmerProfile.state.trim()
                    : "";


            console.log(
                "Farmer profile:",
                farmerProfile
            );


            // =================================
            // FARMER LOCATION EXISTS
            // =================================

            if (location) {

                const searchLocation =
                    `${location}, ${state}, India`;


                console.log(
                    "Searching weather location:",
                    searchLocation
                );


                const coordinates =
                    await geocodeLocation(
                        location,
                        state
                    );


                if (coordinates) {

                    farmLocation = {

                        city:
                            state
                                ? `${location}, ${state}`
                                : location,

                        latitude:
                            coordinates.latitude,

                        longitude:
                            coordinates.longitude

                    };

                }

            }

        } catch (error) {

            console.error(
                "Profile error:",
                error
            );

        }

    }


    console.log(
        "Final weather location:",
        farmLocation
    );


    // =====================================
    // LOAD WEATHER
    // =====================================

    loadWeather(
        farmLocation
    );

}


// =========================================
// GEOCODE LOCATION
// =========================================

async function geocodeLocation(
    location,
    state
) {

    try {

        // IMPORTANT:
        // Search only the city/location name.
        // Open-Meteo works more reliably this way.

        const url =
            `https://geocoding-api.open-meteo.com/v1/search?` +
            `name=${encodeURIComponent(location)}` +
            `&count=10` +
            `&language=en` +
            `&format=json`;


        console.log(
            "Geocoding URL:",
            url
        );


        const response =
            await fetch(url);


        if (!response.ok) {

            throw new Error(
                `Geocoding failed: ${response.status}`
            );

        }


        const data =
            await response.json();


        console.log(
            "Geocoding response:",
            data
        );


        if (
            !data.results ||
            data.results.length === 0
        ) {

            console.warn(
                "Location not found:",
                location
            );

            return null;

        }


        // =================================
        // TRY TO MATCH STATE
        // =================================

        if (state) {

            const stateMatch =
                data.results.find(
                    result =>
                        result.admin1 &&
                        result.admin1
                            .toLowerCase()
                            .includes(
                                state.toLowerCase()
                            )
                );


            if (stateMatch) {

                return {

                    latitude:
                        stateMatch.latitude,

                    longitude:
                        stateMatch.longitude

                };

            }

        }


        // =================================
        // OTHERWISE USE FIRST RESULT
        // =================================

        const result =
            data.results[0];


        return {

            latitude:
                result.latitude,

            longitude:
                result.longitude

        };

    } catch (error) {

        console.error(
            "Geocoding Error:",
            error
        );

        return null;

    }

}


// =========================================
// LOAD WEATHER
// =========================================

async function loadWeather(
    farmLocation
) {

    try {

        // =====================================
        // DISPLAY LOCATION
        // =====================================

        weatherLocation.textContent =
            `🌾 ${farmLocation.city}`;


        weatherUpdated.textContent =
            "Loading latest forecast...";


        // =====================================
        // WEATHER API URL
        // =====================================

        const url =
            `https://api.open-meteo.com/v1/forecast?` +

            `latitude=${farmLocation.latitude}` +

            `&longitude=${farmLocation.longitude}` +

            `&current=` +
            `temperature_2m,` +
            `relative_humidity_2m,` +
            `wind_speed_10m,` +
            `weather_code` +

            `&daily=` +
            `weather_code,` +
            `temperature_2m_max,` +
            `temperature_2m_min,` +
            `precipitation_probability_max` +

            `&forecast_days=5` +

            `&timezone=auto`;


        console.log(
            "Weather API:",
            url
        );


        // =====================================
        // FETCH WEATHER
        // =====================================

        const response =
            await fetch(url);


        if (!response.ok) {

            throw new Error(
                `Weather API failed: ${response.status}`
            );

        }


        const data =
            await response.json();


        console.log(
            "Weather data:",
            data
        );


        // =====================================
        // CURRENT WEATHER
        // =====================================

        const current =
            data.current;


        currentTemperature.textContent =
            `${Math.round(
                current.temperature_2m
            )}°C`;


        humidity.textContent =
            `${current.relative_humidity_2m}%`;


        windSpeed.textContent =
            `${Math.round(
                current.wind_speed_10m
            )} km/h`;


        rainProbability.textContent =
            `${data.daily
                .precipitation_probability_max[0]
            }%`;


        // =====================================
        // CURRENT WEATHER ICON
        // =====================================

        weatherIcon.textContent =
            getWeatherIcon(
                current.weather_code
            );


        // =====================================
        // UPDATED TIME
        // =====================================

        weatherUpdated.textContent =
            `Updated: ${formatDateTime(
                current.time
            )}`;


        // =====================================
        // 5 DAY FORECAST
        // =====================================

        createForecast(
            data.daily
        );


    } catch (error) {

        console.error(
            "Weather Error:",
            error
        );


        weatherUpdated.textContent =
            "Unable to load weather";


        forecastContainer.innerHTML = `

            <div class="weather-error">

                ⚠️ Weather service is currently unavailable.

                <br><br>

                Please refresh the page.

            </div>

        `;

    }

}


// =========================================
// CREATE 5 DAY FORECAST
// =========================================

function createForecast(
    daily
) {

    forecastContainer.innerHTML = "";


    for (
        let i = 0;
        i < daily.time.length;
        i++
    ) {

        const card =
            document.createElement("div");


        card.classList.add(
            "forecast-card"
        );


        const date =
            new Date(
                daily.time[i]
            );


        const day =
            document.createElement("div");

        day.classList.add(
            "forecast-day"
        );


        day.textContent =
            i === 0
                ? "Today"
                : date.toLocaleDateString(
                    "en-IN",
                    {
                        weekday: "short"
                    }
                );


        const icon =
            document.createElement("div");

        icon.classList.add(
            "forecast-icon"
        );


        icon.textContent =
            getWeatherIcon(
                daily.weather_code[i]
            );


        const temperature =
            document.createElement("div");

        temperature.classList.add(
            "forecast-temp"
        );


        temperature.textContent =
            `${Math.round(
                daily.temperature_2m_max[i]
            )}° / ${Math.round(
                daily.temperature_2m_min[i]
            )}°C`;


        const rain =
            document.createElement("div");

        rain.classList.add(
            "forecast-rain"
        );


        rain.textContent =
            `🌧️ ${
                daily
                    .precipitation_probability_max[i]
            }% rain`;


        card.appendChild(day);

        card.appendChild(icon);

        card.appendChild(temperature);

        card.appendChild(rain);


        forecastContainer.appendChild(
            card
        );

    }

}


// =========================================
// WEATHER ICON
// =========================================

function getWeatherIcon(
    code
) {

    if (code === 0) {

        return "☀️";

    }


    if (
        code === 1 ||
        code === 2
    ) {

        return "🌤️";

    }


    if (code === 3) {

        return "☁️";

    }


    if (
        code >= 45 &&
        code <= 48
    ) {

        return "🌫️";

    }


    if (
        code >= 51 &&
        code <= 67
    ) {

        return "🌧️";

    }


    if (
        code >= 71 &&
        code <= 77
    ) {

        return "❄️";

    }


    if (
        code >= 80 &&
        code <= 82
    ) {

        return "🌦️";

    }


    if (
        code >= 95 &&
        code <= 99
    ) {

        return "⛈️";

    }


    return "🌤️";

}


// =========================================
// FORMAT DATE
// =========================================

function formatDateTime(
    dateTime
) {

    const date =
        new Date(dateTime);


    return date.toLocaleString(
        "en-IN",
        {
            day: "numeric",
            month: "short",
            hour: "numeric",
            minute: "2-digit"
        }
    );

}