# Automated Outreach & Enrollment Agents

End-to-end implementation of an AI-assisted outreach and enrollment system covering:
1. Data integration and segmentation across 15 states.
2. AI targeting model for youth cluster identification.
3. Multi-channel campaign generation and deployment.
4. Localized outreach scripting.
5. Onboarding automation with reminders and FAQ support.
6. Monitoring and optimization loops.

## Tech Stack
- Backend: FastAPI + SQLAlchemy + Alembic + Celery
- DB: SQLite default (switchable to Postgres)
- Queue: Redis
- Frontend: React + Vite
- Integrations: Mock + production adapters (Twilio/Meta/SMTP/Voice/Community Poster)

## Quick Start
1. Start Redis
   - `docker compose up -d`
2. Backend setup
   - `cd backend`
   - `python -m venv .venv`
   - `.venv\Scripts\activate`
   - `pip install -r requirements.txt`
   - `copy .env.example .env`
   - `alembic upgrade head`
   - `python scripts/seed_data.py`
   - `uvicorn app.main:app --reload`
3. Optional worker
   - `celery -A app.workers.celery_app.celery worker -l info`
4. Frontend setup
   - `cd frontend`
   - `npm install`
   - `npm run dev`

## Demo Flow
- Use dashboard button: `Run Full Pipeline Demo`
- It runs ingestion -> lead scoring -> campaign plan/deploy -> onboarding -> analytics optimization

## Provider Setup
- Keep defaults for local mock sends:
  - `SMS_PROVIDER=mock`
  - `WHATSAPP_PROVIDER=mock`
  - `EMAIL_PROVIDER=mock`
  - `VOICE_PROVIDER=mock`
  - `POSTER_PROVIDER=community`
- Production examples:
  - `SMS_PROVIDER=twilio`
  - `WHATSAPP_PROVIDER=meta`
  - `EMAIL_PROVIDER=smtp`
  - `VOICE_PROVIDER=twilio`

## API Surface
- Leads: create + targeting score
- Data: regional skill/economic ingestion + coverage checks
- Campaigns: create, plan, approve, deploy
- Messages: send, reply tracking, opt-out
- Onboarding: start, step transitions, document upload, reminders, FAQ
- Analytics: KPIs, event feed, optimization recommendations

See [docs/api.md](docs/api.md), [docs/event-spec.md](docs/event-spec.md), [docs/safety-policy.md](docs/safety-policy.md).
