
# ================================================================
# AGRIBRIDGE AI — FARM-SPECIFIC ADVICE ENGINE
# ================================================================

def generate_farm_specific_advice(
    recommendation,
    farm_info,
    weather_context=None
):
    """
    Generate field-specific advice using:

        Verified disease recommendation
                    +
              Farmer profile
                    +
             Weather context (optional)

    The disease recommendation comes from the database.
    This function adapts the advice to the farmer's
    current field conditions and dynamic weather context.
    """

    if not isinstance(
        recommendation,
        dict
    ):
        raise TypeError(
            "recommendation must be a dictionary."
        )

    if not isinstance(
        farm_info,
        dict
    ):
        raise TypeError(
            "farm_info must be a dictionary."
        )

    # Weather context can be passed directly or via farm_info
    if weather_context is None and isinstance(farm_info.get("weather_context"), dict):
        weather_context = farm_info.get("weather_context")


    # ============================================================
    # FARM INFORMATION
    # ============================================================

    irrigation_method = farm_info.get(
        "irrigation_method",
        ""
    )

    irrigation_status = farm_info.get(
        "irrigation_status",
        ""
    )

    rainfall = farm_info.get(
        "recent_rainfall",
        ""
    )

    humidity = farm_info.get(
        "humidity",
        ""
    )

    fertilizer = farm_info.get(
        "fertilizer_applied",
        ""
    )

    previous_crop = farm_info.get(
        "previous_crop",
        ""
    )

    severity = farm_info.get(
        "disease_severity",
        ""
    )

    growth_stage = farm_info.get(
        "growth_stage",
        ""
    )

    region = farm_info.get(
        "region",
        ""
    )


    # ============================================================
    # IRRIGATION ADVICE
    # ============================================================

    irrigation_advice = []

    database_irrigation = recommendation.get(
        "irrigation_advice",
        ""
    )

    if database_irrigation:

        if isinstance(
            database_irrigation,
            list
        ):
            irrigation_advice.extend(
                str(x)
                for x in database_irrigation
            )

        else:
            irrigation_advice.append(
                str(database_irrigation)
            )


    if irrigation_status in [
        "wet",
        "waterlogged"
    ]:

        irrigation_advice.append(
            "Field moisture is high. "
            "Avoid unnecessary irrigation "
            "until the field condition improves."
        )

    elif irrigation_status == "dry":

        irrigation_advice.append(
            "Field moisture is low. "
            "Assess crop water requirement "
            "before irrigation."
        )


    if irrigation_method:

        irrigation_advice.append(
            f"Current irrigation method: "
            f"{irrigation_method}."
        )

    # Weather context integration for irrigation
    if weather_context:
        upcoming_rain = weather_context.get("upcoming_rainfall", 0) or weather_context.get("rainfall", 0)
        temp = weather_context.get("temperature")
        if upcoming_rain and float(upcoming_rain) > 5.0:
            irrigation_advice.append(
                f"Rainfall forecast ({upcoming_rain}mm expected). "
                "Delay planned irrigation and clear field drainage channels."
            )
        if temp and float(temp) > 33.0:
            irrigation_advice.append(
                f"Elevated temperatures ({temp}°C). Irrigate during early morning or evening to minimize evaporation."
            )


    # ============================================================
    # WEATHER / HUMIDITY
    # ============================================================

    weather_advice = []

    database_weather = recommendation.get(
        "weather_condition",
        ""
    )

    if database_weather:

        if isinstance(
            database_weather,
            list
        ):
            weather_advice.extend(
                str(x)
                for x in database_weather
            )

        else:
            weather_advice.append(
                str(database_weather)
            )


    if humidity == "high":

        weather_advice.append(
            "High humidity can increase "
            "disease development or disease spread."
        )

    if rainfall in [
        "moderate",
        "heavy"
    ]:

        weather_advice.append(
            f"Recent {rainfall} rainfall reported. "
            "Continue monitoring disease progression."
        )

    # Dynamic weather context advice
    if weather_context:
        w_cond = weather_context.get("weather_condition")
        w_wind = weather_context.get("wind_speed")
        w_hum = weather_context.get("humidity")
        if w_cond:
            weather_advice.append(f"Current weather condition: {w_cond}.")
        if w_wind and float(w_wind) > 15.0:
            weather_advice.append(
                f"Wind speed is {w_wind} km/h. Postpone foliar spraying until calmer conditions to prevent spray drift."
            )
        elif w_wind and float(w_wind) <= 10.0:
            weather_advice.append("Favourable calm wind conditions for foliar nutrient and organic protection sprays.")
        if w_hum and float(w_hum) >= 70:
            weather_advice.append(f"High relative humidity ({w_hum}%) creates conditions favourable for fungal sporulation. Inspect lower leaf canopy.")


    # ============================================================
    # FERTILIZER ADVICE
    # ============================================================

    fertilizer_advice = []

    database_fertilizer = recommendation.get(
        "fertilizer_advice",
        ""
    )

    if database_fertilizer:

        if isinstance(
            database_fertilizer,
            list
        ):
            fertilizer_advice.extend(
                str(x)
                for x in database_fertilizer
            )

        else:
            fertilizer_advice.append(
                str(database_fertilizer)
            )


    if fertilizer:

        fertilizer_advice.insert(
            0,
            f"Recently applied fertilizer: "
            f"{fertilizer}."
        )


    # ============================================================
    # FIELD SANITATION
    # ============================================================

    sanitation_advice = []

    database_sanitation = recommendation.get(
        "field_sanitation",
        ""
    )

    if database_sanitation:

        if isinstance(
            database_sanitation,
            list
        ):
            sanitation_advice.extend(
                str(x)
                for x in database_sanitation
            )

        else:
            sanitation_advice.append(
                str(database_sanitation)
            )


    if previous_crop:

        sanitation_advice.append(
            f"Previous crop reported: "
            f"{previous_crop}. "
            "Consider crop history when planning "
            "field sanitation and crop rotation."
        )


    # ============================================================
    # DISEASE SEVERITY
    # ============================================================

    severity_advice = []

    if severity:

        severity_advice.append(
            f"Reported disease severity: "
            f"{severity}."
        )

        if severity == "high":

            severity_advice.append(
                "High disease severity reported. "
                "Prioritize monitoring and follow "
                "the verified treatment guidance."
            )

        elif severity == "moderate":

            severity_advice.append(
                "Moderate disease severity reported. "
                "Continue regular monitoring and "
                "follow the recommended treatment."
            )

        elif severity == "low":

            severity_advice.append(
                "Low disease severity reported. "
                "Continue preventive measures and "
                "monitor the crop."
            )


    # ============================================================
    # GROWTH STAGE
    # ============================================================

    growth_stage_advice = []

    if growth_stage:

        growth_stage_advice.append(
            f"Current growth stage: "
            f"{growth_stage}."
        )


    # ============================================================
    # REGIONAL ADVICE
    # ============================================================

    regional_advice = []

    database_regional = recommendation.get(
        "regional_advice",
        ""
    )

    if database_regional:

        if isinstance(
            database_regional,
            list
        ):
            regional_advice.extend(
                str(x)
                for x in database_regional
            )

        else:
            regional_advice.append(
                str(database_regional)
            )


    if region:

        regional_advice.append(
            f"Farmer region: {region}."
        )


    # ============================================================
    # FINAL FARM-SPECIFIC RESPONSE
    # ============================================================

    return {

        "irrigation_advice":
            irrigation_advice,

        "weather_advice":
            weather_advice,

        "fertilizer_advice":
            fertilizer_advice,

        "field_sanitation":
            sanitation_advice,

        "disease_severity":
            severity_advice,

        "growth_stage":
            growth_stage_advice,

        "regional_advice":
            regional_advice
    }
