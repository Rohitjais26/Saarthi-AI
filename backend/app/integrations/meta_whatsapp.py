from datetime import datetime

import httpx

from app.core.config import settings
from app.integrations.base import MessageProvider, ProviderError, SendResult


class MetaWhatsAppProvider(MessageProvider):
    def send_message(self, channel: str, recipient: str, content: str, metadata: dict | None = None) -> dict:
        if not settings.meta_whatsapp_token or not settings.meta_whatsapp_phone_number_id:
            raise ProviderError('Meta WhatsApp credentials are not configured')

        url = f'https://graph.facebook.com/v21.0/{settings.meta_whatsapp_phone_number_id}/messages'
        headers = {
            'Authorization': f'Bearer {settings.meta_whatsapp_token}',
            'Content-Type': 'application/json',
        }
        payload = {
            'messaging_product': 'whatsapp',
            'to': recipient,
            'type': 'text',
            'text': {'body': content},
        }

        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, headers=headers, json=payload)
        if response.status_code >= 300:
            raise ProviderError(f'Meta WhatsApp send failed: {response.status_code}')

        body = response.json()
        message_id = (
            ((body.get('messages') or [{}])[0]).get('id')
            if isinstance(body.get('messages'), list)
            else f'meta-wa-{int(datetime.utcnow().timestamp())}'
        )

        result = SendResult(
            provider='meta_whatsapp',
            channel=channel,
            recipient=recipient,
            status='sent',
            provider_message_id=message_id,
            metadata=metadata or {},
        )
        return result.as_dict()
