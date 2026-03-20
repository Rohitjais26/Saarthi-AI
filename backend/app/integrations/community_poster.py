from datetime import datetime

from app.integrations.base import MessageProvider, SendResult


class CommunityPosterProvider(MessageProvider):
    def send_message(self, channel: str, recipient: str, content: str, metadata: dict | None = None) -> dict:
        location = (metadata or {}).get('district', 'community_board')
        result = SendResult(
            provider='community_poster',
            channel=channel,
            recipient=recipient,
            status='posted',
            provider_message_id=f'poster-{location}-{int(datetime.utcnow().timestamp())}',
            metadata={
                'location': location,
                'content': content,
                **(metadata or {}),
            },
        )
        return result.as_dict()
