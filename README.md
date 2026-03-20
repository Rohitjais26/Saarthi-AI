# Saarthi Ai - Automated Outreach and Enrollment Platform

Saarthi Ai is an end-to-end AI-assisted outreach and onboarding platform built as an internship project.  
It automates regional data ingestion, lead targeting, campaign generation, onboarding guidance, and optimization analytics.

## Problem Statement
Conventional outreach and enrollment workflows are slow, manual, and fragmented across channels.  
Saarthi Ai provides a unified system that improves speed, personalization, and measurable conversion outcomes.

## Requirement Coverage (All 6 Tasks)
| Internship Task | Implemented In | Proof |
|---|---|---|
| 1. Data Integration & Segmentation | Regional data ingestion + coverage APIs, 15-state seed | `POST /data/ingest/regional-skill`, `GET /data/coverage` |
| 2. AI Targeting Model | Lead scoring with cluster + confidence + channels | `POST /leads/{lead_id}/score` |
| 3. Campaign Generation | Create -> approve -> plan -> deploy multi-channel campaigns | `/campaigns/*` including `/deploy` |
| 4. Outreach Scripting | Localized, channel-specific script generation | `/messages/send`, onboarding reminders, localization service |
| 5. Onboarding Automation | Start, document upload, reminders, step transitions, FAQ | `/onboarding/*` |
| 6. Monitoring & Optimization | KPI dashboard, event stream, optimization recommendations | `/analytics/kpis`, `/analytics/events`, `/analytics/optimize` |

## Key Features
- AI lead scoring and segmentation with recommended next actions
- Multi-channel campaign orchestration (WhatsApp, SMS, email, voice, community poster)
- Localized outreach templates and FAQ responses
- Onboarding funnel automation with reminders and status tracking
- Real-time KPI and event-driven optimization insights
- Advanced dashboard with presentation mode, funnel view, campaign comparisons, and live telemetry

## Tech Stack
- Backend: FastAPI, SQLAlchemy, Alembic, Celery
- Database: SQLite (default), Postgres-ready
- Queue/Broker: Redis
- Frontend: React + TypeScript + Vite
- Integrations: Mock, Twilio, Meta WhatsApp, SMTP, Community Poster

## Repository Structure
```text
backend/
  app/
    api/            # FastAPI routes
    db/             # Models, session
    services/       # Scoring, planning, optimization, localization
    integrations/   # Channel providers
  alembic/          # DB migrations
  scripts/          # Seed script
  tests/            # Backend tests
frontend/
  src/
    pages/          # Dashboard UI
    components/     # KPI and UI components
docs/
  api.md
  event-spec.md
  safety-policy.md
scripts/
  demo.ps1          # End-to-end API demo flow
```

## Local Setup
### Prerequisites
- Python 3.10+
- Node.js 18+
- Redis (or Docker)

### 1) Start Redis
```bash
docker compose up -d
```

### 2) Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
python scripts/seed_data.py
uvicorn app.main:app --reload
```

### 3) Frontend
```bash
cd frontend
npm install
npm run dev
```

## Run URLs
- Frontend dashboard: `http://localhost:5173`
- Backend API docs (Swagger): `http://localhost:8000/docs`
- Health endpoint: `http://localhost:8000/health`

## Demo Flow
### Option A: UI
1. Open dashboard
2. Click `Run Full Pipeline Demo`
3. Review KPIs, funnel, event stream, and recommendations

### Option B: Script
```bash
powershell -ExecutionPolicy Bypass -File scripts/demo.ps1
```

## API Surface
See detailed docs in [docs/api.md](docs/api.md).

High-level groups:
- Leads: create + score
- Data: ingest + coverage
- Campaigns: create + approve + plan + deploy
- Messages: send + reply + opt-out
- Onboarding: start + documents + reminders + steps + FAQ
- Analytics: kpis + events + optimize

## Configuration
Environment variables are documented in:
- [backend/.env.example](backend/.env.example)

Key vars:
- `DATABASE_URL`
- `REDIS_URL`
- `SMS_PROVIDER`, `WHATSAPP_PROVIDER`, `EMAIL_PROVIDER`, `VOICE_PROVIDER`, `POSTER_PROVIDER`
- `QUIET_HOURS_START`, `QUIET_HOURS_END`, `MAX_TOUCHES_PER_7D`

## Safety and Compliance
- Consent checks by channel
- Opt-out support and blocking
- Campaign approval gate
- Quiet hours and frequency caps
- Traceable metric events and audit-ready records

See:
- [docs/safety-policy.md](docs/safety-policy.md)
- [docs/event-spec.md](docs/event-spec.md)

## Testing
Backend tests:
```bash
cd backend
..\venv\Scripts\python.exe -m pytest -q
```

Frontend build:
```bash
cd frontend
npm run build
```

## Current Status
This project is complete at MVP/PoC level for internship functional requirements.  
Recommended next step for production readiness: CI/CD, authentication hardening, and live deployment.
