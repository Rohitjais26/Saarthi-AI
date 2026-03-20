from collections import Counter, defaultdict

from app.db.models import MetricEvent


def build_optimization_report(events: list[MetricEvent]) -> dict:
    counts = Counter(event.event_name for event in events)
    sent = counts.get('campaign.message.sent', 0)
    replied = counts.get('campaign.message.replied', 0)
    enrolled = counts.get('onboarding.enrolled', 0)
    abandoned = counts.get('onboarding.abandoned', 0)
    started = counts.get('onboarding.started', 0)

    reply_rate = (replied / sent) if sent else 0.0
    enrollment_rate = (enrolled / sent) if sent else 0.0
    dropout_rate = (abandoned / started) if started else 0.0

    channel = defaultdict(lambda: {'sent': 0, 'replied': 0, 'failed': 0})
    for event in events:
        if not event.channel:
            continue
        if event.event_name == 'campaign.message.sent':
            channel[event.channel]['sent'] += 1
        elif event.event_name == 'campaign.message.replied':
            channel[event.channel]['replied'] += 1
        elif event.event_name == 'campaign.message.failed':
            channel[event.channel]['failed'] += 1

    channel_effectiveness: dict[str, dict] = {}
    for key, value in channel.items():
        sent_count = value['sent']
        channel_effectiveness[key] = {
            **value,
            'reply_rate': round((value['replied'] / sent_count), 4) if sent_count else 0.0,
            'failure_rate': round((value['failed'] / sent_count), 4) if sent_count else 0.0,
        }

    recommendations: list[str] = []
    if reply_rate < 0.12:
        recommendations.append('Reply rate is low. Prioritize WhatsApp copy variant A and shorten CTA length.')
    if dropout_rate > 0.2:
        recommendations.append('Dropout is elevated. Trigger orientation reminders within 24 hours of docs completion.')
    if enrollment_rate < 0.08:
        recommendations.append('Enrollment conversion is low. Add call-assist for high-need segments.')
    if channel_effectiveness.get('sms', {}).get('failure_rate', 0) > 0.1:
        recommendations.append('SMS failure rate is high. Switch fallback path to voice and community poster outreach.')
    if not recommendations:
        recommendations.append('Current performance is stable. Continue A/B testing and monitor weekly drift.')

    return {
        'summary': {
            'sent': sent,
            'replied': replied,
            'enrolled': enrolled,
            'abandoned': abandoned,
            'reply_rate': round(reply_rate, 4),
            'enrollment_rate': round(enrollment_rate, 4),
            'dropout_rate': round(dropout_rate, 4),
        },
        'channel_effectiveness': channel_effectiveness,
        'recommendations': recommendations,
    }
