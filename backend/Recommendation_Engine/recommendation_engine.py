
# ==========================================
# AGRIBRIDGE AI - RECOMMENDATION ENGINE
# ==========================================

import os
import pandas as pd


# ------------------------------------------
# PATHS
# ------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATASET_PATH = os.path.join(
    BASE_DIR,
    "agriculture_recommendation_data.csv"
)


# ------------------------------------------
# LOAD DATASET
# ------------------------------------------

if not os.path.exists(DATASET_PATH):
    raise FileNotFoundError(
        f"Recommendation dataset not found: "
        f"{DATASET_PATH}"
    )

df = pd.read_csv(DATASET_PATH)

df.columns = df.columns.str.strip()


# ------------------------------------------
# CLEAN DATA
# ------------------------------------------

text_columns = [
    "State",
    "District",
    "Season",
    "Soil_Type",
    "Primary_Recommended_Crops"
]

for column in text_columns:

    if column in df.columns:
        df[column] = (
            df[column]
            .astype(str)
            .str.strip()
        )


df["Min_pH"] = pd.to_numeric(
    df["Min_pH"],
    errors="coerce"
)

df["Max_pH"] = pd.to_numeric(
    df["Max_pH"],
    errors="coerce"
)


# ------------------------------------------
# CREATE SOIL-AWARE LOOKUP
# ------------------------------------------

df["lookup_key"] = (
    df["State"].str.lower() + "|" +
    df["District"].str.lower() + "|" +
    df["Season"].str.lower() + "|" +
    df["Soil_Type"].str.lower()
)


recommendation_index = {
    row["lookup_key"]: row.to_dict()
    for _, row in df.iterrows()
}


# ------------------------------------------
# MAIN RECOMMENDATION FUNCTION
# ------------------------------------------

def agribridge_crop_recommendation(
    state,
    district,
    season,
    soil_type,
    ph=None
):

    # Validate required inputs
    if not state:
        return {
            "status": "error",
            "message": "State is required."
        }

    if not district:
        return {
            "status": "error",
            "message": "District is required."
        }

    if not season:
        return {
            "status": "error",
            "message": "Season is required."
        }

    if not soil_type:
        return {
            "status": "error",
            "message": "Soil Type is required."
        }


    # Normalize inputs
    state = str(state).strip().lower()
    district = str(district).strip().lower()
    season = str(season).strip().lower()
    soil_type = str(soil_type).strip().lower()


    # --------------------------------------
    # pH VALIDATION
    # --------------------------------------

    if ph is not None:

        try:
            ph = float(ph)

        except (ValueError, TypeError):

            return {
                "status": "error",
                "message": "Invalid soil pH."
            }

        if ph < 0 or ph > 14:

            return {
                "status": "error",
                "message": "Soil pH must be between 0 and 14."
            }


    # --------------------------------------
    # LOOKUP
    # --------------------------------------

    lookup_key = (
        f"{state}|"
        f"{district}|"
        f"{season}|"
        f"{soil_type}"
    )

    record = recommendation_index.get(
        lookup_key
    )


    if record is None:

        return {
            "status": "error",
            "message": (
                "No recommendation found for "
                "the selected State, District, "
                "Season and Soil Type."
            )
        }


    # --------------------------------------
    # pH STATUS
    # --------------------------------------

    ph_status = "Not provided"

    if ph is not None:

        if (
            record["Min_pH"]
            <= ph
            <= record["Max_pH"]
        ):

            ph_status = "Suitable"

        else:

            ph_status = (
                "Outside recommended range"
            )


    # --------------------------------------
    # CROPS
    # --------------------------------------

    crops = [
        crop.strip()
        for crop in str(
            record[
                "Primary_Recommended_Crops"
            ]
        ).split(",")
        if crop.strip()
    ]


    # --------------------------------------
    # FINAL RESPONSE
    # --------------------------------------

    return {

        "status": "success",

        "location": {
            "state": record["State"],
            "district": record["District"]
        },

        "season": record["Season"],

        "soil": {
            "type": record["Soil_Type"],
            "recommended_ph": (
                f"{record['Min_pH']} - "
                f"{record['Max_pH']}"
            ),
            "ph_status": ph_status
        },

        "recommended_crops": crops
    }


# ------------------------------------------
# END OF ENGINE
# ------------------------------------------
