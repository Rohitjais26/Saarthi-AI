from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Campaign, Geography, MessageDispatch, MetricEvent, SegmentationScore, YouthProfile
from app.db.session import get_db
from app.integrations.base import ProviderError
from app.integrations.provider_factory import get_provider
from app.schemas.campaigns import CampaignApprove, CampaignCreate, CampaignDeploy
from app.services.campaign_planner import build_campaign_plan
from app.services.localization import generate_outreach_script

router = APIRouter()


def _event_id(prefix: str) -> str:
    return f'{prefix}-{datetime.utcnow().strftime("%Y%m%d%H%M%S%f")}'[:64]


def _recommended_channels(lead: YouthProfile, score: SegmentationScore | None) -> list[str]:
    if score and isinstance(score.recommended_channels_json, dict):
        channels = score.recommended_channels_json.get('channels', [])
        if channels:
            return channels

    channels: list[str] = []
    if lead.consent_whatsapp:
        channels.append('whatsapp')
    if lead.consent_sms:
        channels.append('sms')
    if lead.consent_email:
        channels.append('email')
    if lead.consent_voice:
        channels.append('voice')
    return channels or ['community_poster']


def _eligible_leads(campaign: Campaign, db: Session, batch_limit: int) -> list[tuple[YouthProfile, SegmentationScore | None]]:
    segment = campaign.segment_filter_json or {}
    districts = segment.get('district_code', [])
    cluster_filter = set(segment.get('cluster_label', []))
    min_propensity = float(segment.get('min_propensity', 0))

    query = db.query(YouthProfile)
    if districts:
        query = query.filter(YouthProfile.district_code.in_(districts))
    leads = query.limit(max(batch_limit, 1)).all()

    selected: list[tuple[YouthProfile, SegmentationScore | None]] = []
    for lead in leads:
        score = db.get(SegmentationScore, f'score-{lead.id}')
        if min_propensity and (not score or score.propensity_score < min_propensity):
            continue
        if cluster_filter and (not score or score.cluster_label not in cluster_filter):
            continue
        selected.append((lead, score))
    return selected


@router.post('')
def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db)):
    campaign = Campaign(
        id=payload.id,
        name=payload.name,
        goal=payload.goal,
        segment_filter_json=payload.segment_filter,
        status='draft',
    )
    db.merge(campaign)
    db.merge(MetricEvent(id=_event_id(f'evt-campaign-create-{payload.id}'), event_name='campaign.created', campaign_id=payload.id))
    db.commit()
    return {'campaign_id': payload.id, 'status': 'draft'}


@router.post('/{campaign_id}/plan')
def plan_campaign(campaign_id: str, db: Session = Depends(get_db)):
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail='Campaign not found')

    leads = _eligible_leads(campaign, db, batch_limit=500)
    district_codes = sorted({lead.district_code for lead, _ in leads})
    avg_internet = 55.0
    if district_codes:
        rows = db.execute(
            select(Geography.internet_penetration_rate).where(Geography.district_code.in_(district_codes))
        ).all()
        values = [row[0] for row in rows if row[0] is not None]
        if values:
            avg_internet = sum(values) / len(values)

    return build_campaign_plan(
        campaign_id=campaign_id,
        segment_filter=campaign.segment_filter_json,
        lead_profiles=[lead for lead, _ in leads],
        avg_internet_penetration=avg_internet,
    )


@router.post('/{campaign_id}/approve')
def approve_campaign(campaign_id: str, payload: CampaignApprove, db: Session = Depends(get_db)):
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail='Campaign not found')
    campaign.status = 'approved'
    campaign.approved_by = payload.approved_by
    db.merge(campaign)
    db.merge(MetricEvent(id=_event_id(f'evt-campaign-approved-{campaign_id}'), event_name='campaign.approved', campaign_id=campaign_id))
    db.commit()
    return {'campaign_id': campaign_id, 'status': 'approved', 'approved_by': payload.approved_by}


@router.post('/{campaign_id}/deploy')
def deploy_campaign(campaign_id: str, payload: CampaignDeploy, db: Session = Depends(get_db)):
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail='Campaign not found')
    if campaign.status != 'approved':
        raise HTTPException(status_code=400, detail='Campaign must be approved before deployment')

    lead_rows = _eligible_leads(campaign, db, batch_limit=payload.batch_limit)
    if not lead_rows:
        return {'campaign_id': campaign_id, 'status': 'no_targets', 'targeted_leads': 0, 'messages': 0}

    queued = 0
    sent = 0
    failed = 0

    for lead, score in lead_rows:
        channels = _recommended_channels(lead, score)[:3]
        for channel in channels:
            dispatch_id = _event_id(f'dispatch-{campaign_id}-{lead.id}-{channel}')
            dispatch = MessageDispatch(
                id=dispatch_id,
                campaign_id=campaign_id,
                lead_id=lead.id,
                channel=channel,
                status='queued',
                attempt_count=0,
                scheduled_for=datetime.utcnow(),
            )
            db.add(dispatch)
            db.merge(MetricEvent(
                id=_event_id(f'evt-msg-queued-{campaign_id}-{lead.id}-{channel}'),
                event_name='campaign.message.queued',
                lead_id=lead.id,
                campaign_id=campaign_id,
                channel=channel,
                props_json={'dry_run': payload.dry_run},
            ))
            queued += 1

            if payload.dry_run:
                continue

            content = generate_outreach_script(
                channel=channel,
                lead_name=lead.first_name or 'Learner',
                district=lead.district_code,
                program='SkillTrack',
                cta_link=payload.cta_link,
                language=lead.preferred_language,
            )
            if channel in {'sms', 'whatsapp'} and 'STOP' not in content.upper():
                content = f'{content} Reply STOP to opt out.'

            try:
                provider = get_provider(channel)
                result = provider.send_message(
                    channel=channel,
                    recipient=lead.id,
                    content=content,
                    metadata={'campaign_id': campaign_id, 'district': lead.district_code},
                )
                dispatch.status = 'sent'
                dispatch.attempt_count = (dispatch.attempt_count or 0) + 1
                dispatch.sent_at = datetime.utcnow()
                dispatch.provider_message_id = result.get('provider_message_id')
                db.merge(MetricEvent(
                    id=_event_id(f'evt-msg-sent-{campaign_id}-{lead.id}-{channel}'),
                    event_name='campaign.message.sent',
                    lead_id=lead.id,
                    campaign_id=campaign_id,
                    channel=channel,
                    props_json=result,
                ))
                sent += 1
            except ProviderError as exc:
                dispatch.status = 'failed'
                dispatch.attempt_count = (dispatch.attempt_count or 0) + 1
                dispatch.failure_reason = str(exc)
                db.merge(MetricEvent(
                    id=_event_id(f'evt-msg-failed-{campaign_id}-{lead.id}-{channel}'),
                    event_name='campaign.message.failed',
                    lead_id=lead.id,
                    campaign_id=campaign_id,
                    channel=channel,
                    props_json={'error': str(exc)},
                ))
                failed += 1

    campaign.deployment_mode = 'dry_run' if payload.dry_run else 'auto_multi_channel'
    campaign.deployed_at = datetime.utcnow()
    db.merge(campaign)
    db.commit()

    return {
        'campaign_id': campaign_id,
        'status': 'deployed' if not payload.dry_run else 'dry_run',
        'targeted_leads': len(lead_rows),
        'messages_queued': queued,
        'messages_sent': sent,
        'messages_failed': failed,
    }
