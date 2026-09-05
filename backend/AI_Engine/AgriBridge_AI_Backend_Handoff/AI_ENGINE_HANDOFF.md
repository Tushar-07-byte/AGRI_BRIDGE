
# AGRIBRIDGE AI — AI ENGINE HANDOFF
====================================

AI ENGINE STATUS
----------------
Status: READY FOR BACKEND INTEGRATION

Project:
AgriBridge AI

AI Components:
- Plant-aware disease prediction
- EfficientNetB0 models
- Farm-specific recommendation logic
- Verified recommendation database integration


1. TRAINED MODELS
-----------------

PlantVillage:
Model:
AgriBridge_PlantVillage_EfficientNetB0_Stage2_Best.keras

Classes:
38


Rice:
Model:
AgriBridge_Rice_EfficientNetB0_V2_Phase2_Best.keras

Classes:
6


Wheat:
Model:
AgriBridge_Wheat_EfficientNetB0_Phase1.keras

Classes:
5


2. SUPPORTED PLANTS
-------------------

PlantVillage:
- Apple
- Blueberry
- Cherry
- Corn
- Grape
- Orange
- Peach
- Pepper
- Potato
- Raspberry
- Soybean
- Squash
- Strawberry
- Tomato

Additional models:
- Rice
- Wheat


3. AI INPUT
-----------

The backend sends:

image_path
plant


Example:

predict_disease(
    image_path="leaf.jpg",
    plant="tomato"
)


4. AI OUTPUT
------------

The prediction engine returns:

{
    "plant": "...",
    "model": "...",
    "model_name": "...",
    "class_id": 0,
    "confidence": 95.5
}


5. DATABASE LOOKUP
------------------

After prediction, the backend/database layer should
retrieve the verified recommendation using:

model + class_id


Example:

plantvillage_29
rice_3
wheat_4


Do NOT use confidence to select the disease record.


6. FARM PROFILE
---------------

The frontend should collect:

- farm_area
- growth_stage
- irrigation_method
- irrigation_status
- recent_rainfall
- humidity
- fertilizer_applied
- previous_crop
- disease_severity
- region


7. FARM-SPECIFIC ADVICE
-----------------------

The AI advice engine combines:

Verified disease recommendation
+
Farmer farm profile

and generates:

- irrigation advice
- weather advice
- fertilizer advice
- field sanitation advice
- disease severity advice
- growth-stage information
- regional information


8. IMPORTANT ARCHITECTURE
-------------------------

Frontend
   |
   | image + plant + farm profile
   ↓
Backend API
   |
   ↓
AI Engine
   |
   | class_id + confidence
   ↓
Recommendation Database
   |
   | verified disease information
   ↓
Farm-Specific Advice Engine
   |
   ↓
Backend JSON Response
   |
   ↓
Frontend


9. DATABASE
-----------

Validated recommendation dataset:

PlantVillage: 38
Rice:          6
Wheat:         5
----------------
Total:        49


10. SAFETY
----------

Recommendations must retain the verification
and safety information supplied by the database.

Chemical recommendations must be presented
according to registered product labels and
local agricultural guidance.


11. MAIN AI MODULES
------------------

AI_Engine/
    model_selection.py
    prediction.py
    farm_advice.py
    backend_pipeline.py


12. FARM PROFILE SCHEMA
-----------------------

farm_profile_schema.json


13. RECOMMENDATION DATABASE
---------------------------

recommendation_database.json


14. BACKEND INTEGRATION
-----------------------

The backend should treat the AI engine as a service/module.

The backend is responsible for:

- receiving frontend requests
- validating user input
- storing farmer information
- obtaining recommendation records
- returning API responses

The AI engine is responsible for:

- model selection
- image inference
- class prediction
- confidence
- farm-specific advice


END OF AI HANDOFF
=================
