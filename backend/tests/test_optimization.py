from datetime import datetime

from app.db.models import MetricEvent
from app.services.optimization import build_optimization_report


def test_optimization_report_has_recommendations():
    events = [
        MetricEvent(id='1', event_name='campaign.message.sent', channel='sms', ts=datetime.utcnow()),
        MetricEvent(id='2', event_name='campaign.message.sent', channel='sms', ts=datetime.utcnow()),
        MetricEvent(id='3', event_name='campaign.message.replied', channel='sms', ts=datetime.utcnow()),
        MetricEvent(id='4', event_name='onboarding.started', ts=datetime.utcnow()),
        MetricEvent(id='5', event_name='onboarding.abandoned', ts=datetime.utcnow()),
    ]
    report = build_optimization_report(events)
    assert 'summary' in report
    assert 'recommendations' in report
    assert len(report['recommendations']) >= 1
