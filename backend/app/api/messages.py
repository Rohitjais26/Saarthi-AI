from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Campaign, MessageDispatch, MetricEvent, YouthProfile
from app.db.session import get_db
from app.integrations.base import ProviderError
from app.integrations.provider_factory import get_provider
from app.services.localization import generate_outreach_script, render_template

router = APIRouter()

PERSONAL_CHANNELS = {'sms', 'whatsapp', 'email', 'voice', 'voice_task'}


def _event_id(prefix: str) -> str:
    value = f'{prefix}-{datetime.utcnow().strftime("%Y%m%d%H%M%S%f")}'
    return value[:64]


def _in_quiet_hours(now: datetime) -> bool:
    start_h, start_m = [int(part) for part in settings.quiet_hours_start.split(':')]
    end_h, end_m = [int(part) for part in settings.quiet_hours_end.split(':')]
    start = now.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
    end = now.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
    if start <= end:
        return start <= now <= end
    return now >= start or now <= end


def _recent_touch_count(db: Session, lead_id: str) -> int:
    cutoff = datetime.utcnow() - timedelta(days=7)
    rows = db.execute(
        select(MetricEvent.id).where(
            MetricEvent.lead_id == lead_id,
            MetricEvent.event_name == 'campaign.message.sent',
            MetricEvent.ts >= cutoff,
        )
    ).all()
    return len(rows)


class SendMessageRequest(BaseModel):
    campaign_id: str
    lead_id: str
    channel: str
    template_key: str = 'whatsapp_short'
    values: dict[str, str] = Field(default_factory=dict)


class ReplyEventRequest(BaseModel):
    campaign_id: str
    lead_id: str
    channel: str
    sentiment: str = 'neutral'
    intent: str = 'unknown'


class OptOutRequest(BaseModel):
    lead_id: str
    channel: str | None = None


@router.post('/send')
def send_campaign_message(payload: SendMessageRequest, db: Session = Depends(get_db)):
    campaign = db.get(Campaign, payload.campaign_id)
    if not campaign or campaign.status != 'approved':
        raise HTTPException(status_code=400, detail='Campaign must be approved before sending')

    lead = db.get(YouthProfile, payload.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail='Lead not found')

    channel = payload.channel.lower()
    if lead.opt_out_ts is not None and channel in PERSONAL_CHANNELS:
        raise HTTPException(status_code=400, detail='Lead has opted out')

    channel_consent = {
        'sms': lead.consent_sms,
        'whatsapp': lead.consent_whatsapp,
        'email': lead.consent_email,
        'voice': lead.consent_voice,
        'voice_task': lead.consent_voice,
    }
    if channel in PERSONAL_CHANNELS and not channel_consent.get(channel, False):
        raise HTTPException(status_code=400, detail='No consent for selected channel')

    if channel in PERSONAL_CHANNELS and _in_quiet_hours(datetime.utcnow()):
        raise HTTPException(status_code=400, detail='Message blocked due to quiet hours policy')

    if channel in PERSONAL_CHANNELS and _recent_touch_count(db, payload.lead_id) >= settings.max_touches_per_7d:
        raise HTTPException(status_code=400, detail='Message blocked due to frequency cap')

    values = {
        'name': lead.first_name or 'Learner',
        'district': lead.district_code,
        'program': payload.values.get('program', 'SkillTrack'),
        'cta_link': payload.values.get('cta_link', 'https://example.org/apply'),
        'deadline': payload.values.get('deadline', 'soon'),
        **payload.values,
    }

    content = render_template(payload.template_key, values, language=lead.preferred_language)
    if not content:
        content = generate_outreach_script(
            channel=channel,
            lead_name=values['name'],
            district=values['district'],
            program=values['program'],
            cta_link=values['cta_link'],
            language=lead.preferred_language,
            deadline=values['deadline'],
        )

    if channel in {'sms', 'whatsapp'} and 'STOP' not in content.upper():
        content = f'{content} Reply STOP to opt out.'

    dispatch_id = _event_id(f'dispatch-{payload.campaign_id}-{payload.lead_id}-{channel}')
    dispatch = MessageDispatch(
        id=dispatch_id,
        campaign_id=payload.campaign_id,
        lead_id=payload.lead_id,
        channel=channel,
        status='queued',
        attempt_count=0,
        scheduled_for=datetime.utcnow(),
    )
    db.add(dispatch)
    db.merge(MetricEvent(
        id=_event_id(f'evt-msg-queued-{payload.campaign_id}-{payload.lead_id}-{channel}'),
        event_name='campaign.message.queued',
        lead_id=payload.lead_id,
        campaign_id=payload.campaign_id,
        channel=channel,
        props_json={'template_key': payload.template_key},
    ))

    try:
        provider = get_provider(channel)
        provider_result = provider.send_message(
            channel=channel,
            recipient=payload.lead_id,
            content=content,
            metadata={'campaign_id': payload.campaign_id, 'district': lead.district_code},
        )
        dispatch.status = 'sent'
        dispatch.attempt_count = (dispatch.attempt_count or 0) + 1
        dispatch.provider_message_id = provider_result.get('provider_message_id')
        dispatch.sent_at = datetime.utcnow()
        db.merge(MetricEvent(
            id=_event_id(f'evt-msg-sent-{payload.campaign_id}-{payload.lead_id}-{channel}'),
            event_name='campaign.message.sent',
            lead_id=payload.lead_id,
            campaign_id=payload.campaign_id,
            channel=channel,
            props_json=provider_result,
        ))
        db.commit()
        return {'status': 'sent', 'provider_result': provider_result, 'content': content}
    except ProviderError as exc:
        dispatch.status = 'failed'
        dispatch.attempt_count = (dispatch.attempt_count or 0) + 1
        dispatch.failure_reason = str(exc)
        db.merge(MetricEvent(
            id=_event_id(f'evt-msg-failed-{payload.campaign_id}-{payload.lead_id}-{channel}'),
            event_name='campaign.message.failed',
            lead_id=payload.lead_id,
            campaign_id=payload.campaign_id,
            channel=channel,
            props_json={'error': str(exc)},
        ))
        db.commit()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/reply')
def mark_reply(payload: ReplyEventRequest, db: Session = Depends(get_db)):
    lead = db.get(YouthProfile, payload.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail='Lead not found')
    event = MetricEvent(
        id=_event_id(f'evt-msg-replied-{payload.campaign_id}-{payload.lead_id}-{payload.channel}'),
        event_name='campaign.message.replied',
        lead_id=payload.lead_id,
        campaign_id=payload.campaign_id,
        channel=payload.channel.lower(),
        props_json={'sentiment': payload.sentiment, 'intent': payload.intent},
    )
    db.merge(event)
    db.commit()
    return {'status': 'recorded'}


@router.post('/optout')
def opt_out(payload: OptOutRequest, db: Session = Depends(get_db)):
    lead = db.get(YouthProfile, payload.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail='Lead not found')
    lead.opt_out_ts = datetime.utcnow()
    db.merge(lead)
    db.merge(MetricEvent(
        id=_event_id(f'evt-optout-{payload.lead_id}'),
        event_name='user.opted_out',
        lead_id=payload.lead_id,
        channel=payload.channel,
    ))
    db.commit()
    return {'lead_id': payload.lead_id, 'status': 'opted_out'}
