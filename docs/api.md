# API Endpoints

## Leads
- POST `/leads`
- POST `/leads/{lead_id}/score`

## Data Integration
- POST `/data/ingest/regional-skill`
- GET `/data/coverage`

## Campaigns
- POST `/campaigns`
- POST `/campaigns/{campaign_id}/plan`
- POST `/campaigns/{campaign_id}/approve`
- POST `/campaigns/{campaign_id}/deploy`

## Messages
- POST `/messages/send`
- POST `/messages/reply`
- POST `/messages/optout`

## Onboarding
- POST `/onboarding/start`
- POST `/onboarding/{case_id}/step`
- POST `/onboarding/{case_id}/documents`
- POST `/onboarding/{case_id}/reminder`
- POST `/onboarding/reminders/run`
- GET `/onboarding/{case_id}/faq?q=...`

## Analytics
- GET `/analytics/kpis`
- GET `/analytics/events`
- GET `/analytics/optimize`

## Migrations / Seed
- `alembic upgrade head`
- `python scripts/seed_data.py`
