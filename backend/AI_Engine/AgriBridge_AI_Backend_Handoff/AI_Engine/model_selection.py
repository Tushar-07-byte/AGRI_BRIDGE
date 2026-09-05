
# ================================================================
# AGRIBRIDGE AI — MODEL SELECTION
# ================================================================

MODEL_SELECTION = {

    "plantvillage": {
        "model_name":
            "AgriBridge_PlantVillage_EfficientNetB0_Stage2_Best.keras",

        "model_path": r"../AgriBridge_PlantVillage_EfficientNetB0_Stage2_Best.keras",

        "num_classes": 38
    },

    "rice": {
        "model_name":
            "AgriBridge Rice EfficientNetB0 V2",

        "model_path": r"../AgriBridge_Rice_EfficientNetB0_V2_Phase2_Best.keras",

        "num_classes": 6
    },

    "wheat": {
        "model_name":
            "AgriBridge Wheat EfficientNetB0 Stage 2 Best",

        "model_path": r"../AgriBridge_Wheat_EfficientNetB0_Stage2_Best.keras",

        "num_classes": 5
    }
}


# ================================================================
# PLANT → MODEL → VALID CLASS IDS
# ================================================================

PLANT_MODEL_MAP = {

    "apple": {
        "model": "plantvillage",
        "class_ids": [0, 1, 2, 3]
    },

    "blueberry": {
        "model": "plantvillage",
        "class_ids": [4]
    },

    "cherry": {
        "model": "plantvillage",
        "class_ids": [5, 6]
    },

    "corn": {
        "model": "plantvillage",
        "class_ids": [7, 8, 9, 10]
    },

    "grape": {
        "model": "plantvillage",
        "class_ids": [11, 12, 13, 14]
    },

    "orange": {
        "model": "plantvillage",
        "class_ids": [15]
    },

    "peach": {
        "model": "plantvillage",
        "class_ids": [16, 17]
    },

    "pepper": {
        "model": "plantvillage",
        "class_ids": [18, 19]
    },

    "potato": {
        "model": "plantvillage",
        "class_ids": [20, 21, 22]
    },

    "raspberry": {
        "model": "plantvillage",
        "class_ids": [23]
    },

    "soybean": {
        "model": "plantvillage",
        "class_ids": [24]
    },

    "squash": {
        "model": "plantvillage",
        "class_ids": [25]
    },

    "strawberry": {
        "model": "plantvillage",
        "class_ids": [26, 27]
    },

    "tomato": {
        "model": "plantvillage",
        "class_ids": [
            28, 29, 30, 31, 32,
            33, 34, 35, 36, 37
        ]
    },

    "rice": {
        "model": "rice",
        "class_ids": [0, 1, 2, 3, 4, 5]
    },

    "wheat": {
        "model": "wheat",
        "class_ids": [0, 1, 2, 3, 4]
    }
}
