from datetime import datetime

from app.integrations.base import MessageProvider, SendResult


class MockProvider(MessageProvider):
    def send_message(self, channel: str, recipient: str, content: str, metadata: dict | None = None) -> dict:
        result = SendResult(
            provider='mock',
            channel=channel,
            recipient=recipient,
            status='sent',
            provider_message_id=f'mock-{channel}-{int(datetime.utcnow().timestamp())}',
            metadata={
                'content': content,
                **(metadata or {}),
            },
        )
        return result.as_dict()
