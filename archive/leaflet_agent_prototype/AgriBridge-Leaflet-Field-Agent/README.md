# AgriBridge Leaflet Field Agent

Standalone Leaflet-based field verification map for the AgriBridge project.

## Features

- Interactive Leaflet map
- OpenStreetMap tiles
- Farmer farm locations
- Pending / Verified / Rejected markers
- Farm information popups
- Crop submission cards
- Search farmer/crop/district
- Status filtering
- Current field-agent location
- View farm on map
- Responsive design

## Current Version

The current version uses sample farm data inside `app.js`.

## Future Integration

The sample data will be replaced by the AgriBridge FastAPI endpoint.

Expected API response:

```json
{
    "success": true,
    "listings": [
        {
            "id": 15,
            "farmer_name": "Ramesh Kumar",
            "crop_type": "Tomato",
            "district": "Raipur",
            "quantity_est": 5000,
            "harvest_date": "2026-09-18",
            "status": "pending",
            "latitude": 21.2514,
            "longitude": 81.6296
        }
    ]
}