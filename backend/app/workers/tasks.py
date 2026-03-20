from app.integrations.provider_factory import get_provider
from app.workers.celery_app import celery


@celery.task(bind=True, max_retries=3)
def send_message_task(self, channel: str, recipient: str, content: str, metadata: dict | None = None):
    try:
        provider = get_provider(channel)
        return provider.send_message(channel=channel, recipient=recipient, content=content, metadata=metadata)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
