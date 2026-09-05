
# ================================================================
# AGRIBRIDGE AI — BACKEND FACING PIPELINE
# ================================================================

from prediction import predict_disease
from farm_advice import generate_farm_specific_advice


def agribridge_predict(
    image_path,
    plant,
    recommendation,
    farm_info,
    prediction=None
):
    """
    Main AI function for Backend integration.

    INPUT
    -----
    image_path:
        Uploaded crop/leaf image.

    plant:
        Farmer-selected plant.

    recommendation:
        Verified recommendation record retrieved
        from the database using model + class_id.

    farm_info:
        Farmer's field information.

    OUTPUT
    ------
    Backend-ready dictionary containing:

        prediction
        verified recommendation
        farm-specific advice
        farm profile
    """


    # ============================================================
    # STEP 1 — DISEASE PREDICTION
    # ============================================================

    if prediction is None:
        prediction = predict_disease(
            image_path=image_path,
            plant=plant
        )


    # ============================================================
    # STEP 2 — VERIFY DATABASE RECORD
    # ============================================================

    if not isinstance(
        recommendation,
        dict
    ):

        raise TypeError(
            "recommendation must be a dictionary "
            "retrieved from the recommendation database."
        )


    database_model = str(
        recommendation.get(
            "model",
            ""
        )
    ).strip().lower()


    database_class_id = int(
        recommendation.get(
            "class_id"
        )
    )


    # ============================================================
    # STEP 3 — MODEL CONSISTENCY CHECK
    # ============================================================

    if database_model != prediction["model"]:

        raise ValueError(
            "❌ Model mismatch between AI prediction "
            "and recommendation database."
        )


    # ============================================================
    # STEP 4 — CLASS CONSISTENCY CHECK
    # ============================================================

    if database_class_id != prediction["class_id"]:

        raise ValueError(
            "❌ Class ID mismatch between AI prediction "
            "and recommendation database."
        )


    # ============================================================
    # STEP 5 — FARM-SPECIFIC ADVICE
    # ============================================================

    farm_advice = generate_farm_specific_advice(
        recommendation=recommendation,
        farm_info=farm_info
    )


    # ============================================================
    # STEP 6 — FINAL BACKEND RESPONSE
    # ============================================================

    response = {

        # --------------------------------------------------------
        # AI PREDICTION
        # --------------------------------------------------------

        "prediction": {

            "plant":
                prediction["plant"],

            "model":
                prediction["model"],

            "model_name":
                prediction["model_name"],

            "class_id":
                prediction["class_id"],

            "confidence":
                prediction["confidence"]
        },


        # --------------------------------------------------------
        # VERIFIED DISEASE INFORMATION
        # --------------------------------------------------------

        "disease": {

            "crop":
                recommendation.get(
                    "crop"
                ),

            "disease":
                recommendation.get(
                    "disease"
                ),

            "description":
                recommendation.get(
                    "description"
                ),

            "treatment":
                recommendation.get(
                    "treatment"
                ),

            "prevention":
                recommendation.get(
                    "prevention"
                ),

            "organic_option":
                recommendation.get(
                    "organic_option"
                ),

            "bio_fungicide":
                recommendation.get(
                    "bio_fungicide"
                ),

            "bio_pesticide":
                recommendation.get(
                    "bio_pesticide"
                ),

            "chemical_option":
                recommendation.get(
                    "chemical_option"
                )
        },

        "recommendation": recommendation,


        # --------------------------------------------------------
        # FARM-SPECIFIC ADVICE
        # --------------------------------------------------------

        "farm_specific_advice":
            farm_advice,


        # --------------------------------------------------------
        # FARM PROFILE
        # --------------------------------------------------------

        "farm":
            farm_info,


        # --------------------------------------------------------
        # VERIFICATION
        # --------------------------------------------------------

        "verification": {

            "verified":
                recommendation.get(
                    "verified"
                ),

            "source":
                recommendation.get(
                    "source"
                ),

            "safety_note":
                recommendation.get(
                    "safety_note"
                )
        }
    }


    return response
