
# AgriBridge AI/ML Handoff Package

## Purpose

This package contains the AI/ML-side components of the
AgriBridge All India Crop Monitoring System.

The package is intended for handoff to the backend team.

## Supported Country

India

## Supported Crops

16 crops are registered in the AgriBridge crop registry.

## Included AI/ML Components

- Crop registry
- Scientific crop calendars
- Crop management calendars
- Date-aware crop lifecycle context
- Dynamic stage context
- Open-Meteo weather integration/context
- Gemini recommendation context
- Gemini production prompt/context
- Structured Gemini response schema
- Safety validation context
- Calendar event generation
- Farmer notification event generation
- Marketplace context
- Disease/AI models available under models/

## Gemini

Provider: Google Gemini

Model: gemini-3.6-flash

The Gemini API key is NOT included in this package.

Backend deployment should provide the API key
through a secure environment secret.

Expected environment variable:

AGRIBRIDGE_LLM_API_KEY

## Weather

Provider:

Open-Meteo

The weather integration is designed for dynamic
Indian farmer locations.

No weather API key is required for the Open-Meteo
forecast integration used by this module.

## Disease Safety Policy

Disease handling is inspection-only in the
crop monitoring LLM pipeline.

The LLM must NOT:

- diagnose disease
- confirm disease
- predict disease
- claim that a model confirmed disease
- perform disease model inference

Disease prediction/detection models are separate
AI/ML components and should be integrated by the
backend according to the agreed application flow.

## LLM Input

The backend should provide the model with:

- farmer location
- crop
- planting date when available
- current crop stage when available
- scientific calendar
- management calendar
- current weather
- seven-day forecast
- weather risk
- marketplace context

## LLM Output

The expected structured response is available at:

schemas/gemini_response_schema.json

Required recommendation fields include:

- current_stage
- stage_status
- next_stage
- weather_summary
- weather_risk
- weather_decision
- recommended_action
- irrigation_guidance
- fertilizer_guidance
- crop_protection_guidance
- monitoring_guidance
- marketplace_guidance
- safety_information
- important_note
- sources

## Calendar

Calendar events are date-aware and based on
the crop planting date and crop-specific schedule.

The backend scheduler/notification service should
consume these events and deliver notifications
when scheduled dates arrive.

## Important

This is an AI/ML handoff package.

FastAPI server code, authentication, database,
deployment infrastructure, push notification
providers and backend business services are
outside this package.

Generated:

2026-09-01T08:09:17.693318
