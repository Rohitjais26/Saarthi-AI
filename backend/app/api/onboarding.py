from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import MetricEvent, OnboardingCase, ProgramCatalog, YouthProfile
from app.db.session import get_db
from app.integrations.base import ProviderError
from app.integrations.provider_factory import get_provider
from app.services.localization import generate_outreach_script
from app.services.rag_service import answer_faq

router = APIRouter()

VALID_STATES = [
    'registration_started',
    'eligibility_check',
    'docs_pending',
    'orientation_pending',
    'confirmed',
    'retained_followup',
    'abandoned',
]


def _event_id(prefix: str) -> str:
    return f'{prefix}-{datetime.utcnow().strftime("%Y%m%d%H%M%S%f")}'[:64]


class OnboardingStartRequest(BaseModel):
    lead_id: str
    program_id: str | None = None


class OnboardingStepRequest(BaseModel):
    state: str
    current_step: str


class OnboardingDocumentRequest(BaseModel):
    document_type: str
    document_ref: str


class OnboardingReminderRequest(BaseModel):
    channel: str | None = None
    note: str | None = None


class AutoReminderRunRequest(BaseModel):
    stale_after_hours: int = 24
    max_cases: int = 100


def _pick_channel(lead: YouthProfile, preferred: str | None) -> str:
    if preferred:
        return preferred.lower()
    if lead.consent_whatsapp:
        return 'whatsapp'
    if lead.consent_sms:
        return 'sms'
    if lead.consent_voice:
        return 'voice'
    if lead.consent_email:
        return 'email'
    return 'community_poster'


def _send_reminder(
    db: Session,
    case: OnboardingCase,
    lead: YouthProfile,
    channel: str,
    note: str | None = None,
) -> dict:
    program_name = 'SkillTrack'
    if case.program_id:
        program = db.get(ProgramCatalog, case.program_id)
        if program:
            program_name = program.program_name

    reminder_text = generate_outreach_script(
        channel=channel,
        lead_name=lead.first_name or 'Learner',
        district=lead.district_code,
        program=program_name,
        cta_link='https://example.org/onboarding',
        language=lead.preferred_language,
        deadline='this week',
    )
    if note:
        reminder_text = f'{reminder_text} {note}'

    provider = get_provider(channel)
    result = provider.send_message(
        channel=channel,
        recipient=lead.id,
        content=reminder_text,
        metadata={'onboarding_case_id': case.id, 'district': lead.district_code},
    )
    case.reminder_count = (case.reminder_count or 0) + 1
    case.last_reminder_ts = datetime.utcnow()
    db.merge(case)
    db.merge(MetricEvent(
        id=_event_id(f'evt-onb-reminder-{case.id}-{channel}'),
        event_name='onboarding.reminder.sent',
        lead_id=lead.id,
        channel=channel,
        props_json={'case_id': case.id, 'provider_result': result},
    ))
    return result


@router.post('/start')
def start_onboarding(payload: OnboardingStartRequest, db: Session = Depends(get_db)):
    lead = db.get(YouthProfile, payload.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail='Lead not found')

    case = OnboardingCase(
        id=f'onb-{payload.lead_id}',
        lead_id=payload.lead_id,
        program_id=payload.program_id,
        state='registration_started',
        current_step='registration',
        step_status_json={'registration': 'in_progress'},
        documents_json={'uploaded': []},
    )
    db.merge(case)
    db.merge(MetricEvent(id=_event_id(f'evt-onb-start-{payload.lead_id}'), event_name='onboarding.started', lead_id=payload.lead_id))
    db.commit()
    return {'case_id': case.id, 'state': case.state}


@router.post('/{case_id}/step')
def update_step(case_id: str, payload: OnboardingStepRequest, db: Session = Depends(get_db)):
    case = db.get(OnboardingCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail='Onboarding case not found')
    if payload.state not in VALID_STATES:
        raise HTTPException(status_code=400, detail='Invalid state')

    status = case.step_status_json or {}
    status[payload.current_step] = 'completed'
    case.state = payload.state
    case.current_step = payload.current_step
    case.step_status_json = status
    case.updated_at = datetime.utcnow()
    db.merge(case)
    db.merge(MetricEvent(
        id=_event_id(f'evt-onb-step-{case_id}-{payload.current_step}'),
        event_name='onboarding.step.completed',
        lead_id=case.lead_id,
        props_json={'state': payload.state, 'step': payload.current_step},
    ))

    if payload.state == 'confirmed':
        db.merge(MetricEvent(
            id=_event_id(f'evt-onb-enrolled-{case_id}'),
            event_name='onboarding.enrolled',
            lead_id=case.lead_id,
            props_json={'case_id': case_id},
        ))
    elif payload.state == 'abandoned':
        db.merge(MetricEvent(
            id=_event_id(f'evt-onb-abandoned-{case_id}'),
            event_name='onboarding.abandoned',
            lead_id=case.lead_id,
            props_json={'case_id': case_id},
        ))

    db.commit()
    return {'case_id': case_id, 'state': payload.state, 'current_step': payload.current_step}


@router.post('/{case_id}/documents')
def upload_document(case_id: str, payload: OnboardingDocumentRequest, db: Session = Depends(get_db)):
    case = db.get(OnboardingCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail='Onboarding case not found')

    docs = case.documents_json or {'uploaded': []}
    uploaded = docs.get('uploaded', [])
    uploaded.append(
        {
            'document_type': payload.document_type,
            'document_ref': payload.document_ref,
            'uploaded_at': datetime.utcnow().isoformat(),
        }
    )
    docs['uploaded'] = uploaded
    case.documents_json = docs
    case.current_step = 'document_upload'
    case.state = 'docs_pending'
    case.step_status_json = {**(case.step_status_json or {}), 'document_upload': 'completed'}
    case.updated_at = datetime.utcnow()

    db.merge(case)
    db.merge(MetricEvent(
        id=_event_id(f'evt-onb-doc-upload-{case_id}'),
        event_name='onboarding.document.uploaded',
        lead_id=case.lead_id,
        props_json={'document_type': payload.document_type},
    ))
    db.commit()
    return {'case_id': case_id, 'uploaded_documents': len(uploaded), 'state': case.state}


@router.post('/{case_id}/reminder')
def send_onboarding_reminder(case_id: str, payload: OnboardingReminderRequest, db: Session = Depends(get_db)):
    case = db.get(OnboardingCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail='Onboarding case not found')
    lead = db.get(YouthProfile, case.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail='Lead not found')

    channel = _pick_channel(lead, payload.channel)
    try:
        result = _send_reminder(db, case, lead, channel=channel, note=payload.note)
        db.commit()
        return {'case_id': case_id, 'channel': channel, 'status': 'sent', 'provider_result': result}
    except ProviderError as exc:
        db.merge(MetricEvent(
            id=_event_id(f'evt-onb-reminder-failed-{case.id}-{channel}'),
            event_name='onboarding.reminder.failed',
            lead_id=lead.id,
            channel=channel,
            props_json={'error': str(exc)},
        ))
        db.commit()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/reminders/run')
def run_stale_case_reminders(payload: AutoReminderRunRequest, db: Session = Depends(get_db)):
    cutoff = datetime.utcnow() - timedelta(hours=max(1, payload.stale_after_hours))
    rows = db.execute(
        select(OnboardingCase).where(
            OnboardingCase.updated_at <= cutoff,
            OnboardingCase.state.notin_(['confirmed', 'abandoned']),
        ).limit(max(1, payload.max_cases))
    ).scalars().all()

    sent = 0
    failed = 0
    for case in rows:
        lead = db.get(YouthProfile, case.lead_id)
        if not lead:
            failed += 1
            continue
        channel = _pick_channel(lead, None)
        try:
            _send_reminder(db, case, lead, channel=channel, note='Please continue your application steps.')
            sent += 1
        except ProviderError:
            failed += 1

    db.commit()
    return {'stale_cases': len(rows), 'reminders_sent': sent, 'reminders_failed': failed}


@router.get('/{case_id}/faq')
def onboarding_faq(case_id: str, q: str, locale: str = 'en', db: Session = Depends(get_db)):
    case = db.get(OnboardingCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail='Onboarding case not found')

    rag = answer_faq(question=q, locale=locale, program=case.program_id)
    return {'answer': rag.answer, 'citations': rag.citations}
