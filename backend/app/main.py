from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analytics, campaigns, data, leads, messages, onboarding

app = FastAPI(title='Automated Outreach & Enrollment Agents')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(leads.router, prefix='/leads', tags=['leads'])
app.include_router(campaigns.router, prefix='/campaigns', tags=['campaigns'])
app.include_router(messages.router, prefix='/messages', tags=['messages'])
app.include_router(onboarding.router, prefix='/onboarding', tags=['onboarding'])
app.include_router(analytics.router, prefix='/analytics', tags=['analytics'])
app.include_router(data.router, prefix='/data', tags=['data'])


@app.get('/health')
def health():
    return {'status': 'ok'}
