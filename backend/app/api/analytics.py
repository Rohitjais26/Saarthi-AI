from collections import Counter, defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import MetricEvent
from app.db.session import get_db
from app.services.optimization import build_optimization_report

router = APIRouter()


@router.get('/kpis')
def get_kpis(db: Session = Depends(get_db)):
    rows = db.execute(select(MetricEvent)).scalars().all()
    counts = Counter(row.event_name for row in rows)
    sent = counts.get('campaign.message.sent', 0)
    replied = counts.get('campaign.message.replied', 0)
    enrolled = counts.get('onboarding.enrolled', 0)
    started = counts.get('onboarding.started', 0)
    abandoned = counts.get('onboarding.abandoned', 0)

    channel_stats = defaultdict(lambda: {'sent': 0, 'replied': 0, 'failed': 0})
    for event in rows:
        if not event.channel:
            continue
        if event.event_name == 'campaign.message.sent':
            channel_stats[event.channel]['sent'] += 1
        if event.event_name == 'campaign.message.replied':
            channel_stats[event.channel]['replied'] += 1
        if event.event_name == 'campaign.message.failed':
            channel_stats[event.channel]['failed'] += 1

    channel_effectiveness: dict[str, dict] = {}
    for channel, stats in channel_stats.items():
        sent_count = stats['sent']
        channel_effectiveness[channel] = {
            **stats,
            'reply_rate': round(stats['replied'] / sent_count, 4) if sent_count else 0,
            'failure_rate': round(stats['failed'] / sent_count, 4) if sent_count else 0,
        }

    campaign_stats = defaultdict(lambda: {'sent': 0, 'replied': 0, 'failed': 0})
    for event in rows:
        if not event.campaign_id:
            continue
        if event.event_name == 'campaign.message.sent':
            campaign_stats[event.campaign_id]['sent'] += 1
        if event.event_name == 'campaign.message.replied':
            campaign_stats[event.campaign_id]['replied'] += 1
        if event.event_name == 'campaign.message.failed':
            campaign_stats[event.campaign_id]['failed'] += 1

    return {
        'reach': sent,
        'reply_rate': round(replied / sent, 4) if sent else 0,
        'enrollment_rate': round(enrolled / sent, 4) if sent else 0,
        'dropout_rate': round(abandoned / started, 4) if started else 0,
        'event_counts': dict(counts),
        'channel_effectiveness': dict(channel_effectiveness),
        'campaign_effectiveness': dict(campaign_stats),
    }


@router.get('/events')
def list_events(limit: int = 100, db: Session = Depends(get_db)):
    rows = db.execute(
        select(MetricEvent).order_by(MetricEvent.ts.desc()).limit(limit)
    ).scalars().all()
    return [
        {
            'id': r.id,
            'event_name': r.event_name,
            'lead_id': r.lead_id,
            'campaign_id': r.campaign_id,
            'channel': r.channel,
            'props': r.props_json,
            'ts': r.ts.isoformat(),
        }
        for r in rows
    ]


@router.get('/optimize')
def optimize(db: Session = Depends(get_db)):
    rows = db.execute(select(MetricEvent)).scalars().all()
    return build_optimization_report(rows)
