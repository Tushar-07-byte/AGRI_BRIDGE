AGRIBRIDGE BACKEND HANDOFF
SH-AGR-01 – Autonomous Farm-to-Field Advisory & Action Orchestration Agents

AI/ML flow:
Farmer Context -> Live Weather (Open-Meteo) -> Risk Intelligence
-> Action Planner -> Calendar & Notification -> Task Tracking
-> Field Agent Escalation

Implemented:
- Dynamic India state/district/village/crop input
- Multi-crop / All-India design
- Dynamic Open-Meteo geocoding and 7-day weather
- Weather, water/moisture and disease/pest environmental risk signals
- Disease/pest signal is inspection-only, NOT definitive diagnosis
- Action plan with WHAT, WHEN, WHERE, WHY
- Weather, safety and cost constraints
- Calendar event generation
- Notification event generation
- Weather re-check and rescheduling instruction
- Task statuses
- Field-agent escalation policy

Escalation:
Low -> routine monitoring
Moderate -> farmer action + monitoring
High -> field agent
Critical -> field agent
High/critical disease inspection uncertainty -> field agent

Backend responsibilities:
- Receive farmer request
- Call AI/ML service
- Persist outputs
- Run scheduler
- Deliver notifications
- Update task status
- Re-check weather and reschedule
- Route field-agent escalation
- Authentication, APIs, deployment and secrets

Important:
AI/ML GENERATES notification events. Backend performs actual notification delivery.
No API keys or secrets are included in this handoff.

Verified demo:
Rice, Dhanpatganj, Sultanpur, Uttar Pradesh
Planting date 2026-09-02, stage flowering
Live weather received; overall risk moderate; action required; calendar and notification generated;
field-agent escalation false after corrected production policy.
