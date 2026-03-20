from datetime import datetime

import httpx

from app.core.config import settings
from app.integrations.base import MessageProvider, ProviderError, SendResult


class TwilioSMSProvider(MessageProvider):
    def send_message(self, channel: str, recipient: str, content: str, metadata: dict | None = None) -> dict:
        if not settings.twilio_account_sid or not settings.twilio_auth_token or not settings.twilio_sms_from:
            raise ProviderError('Twilio SMS credentials are not configured')

        url = f'https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json'
        payload = {
            'From': settings.twilio_sms_from,
            'To': recipient,
            'Body': content,
        }

        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, data=payload, auth=(settings.twilio_account_sid, settings.twilio_auth_token))
        if response.status_code >= 300:
            raise ProviderError(f'Twilio SMS send failed: {response.status_code}')

        body = response.json()
        result = SendResult(
            provider='twilio',
            channel=channel,
            recipient=recipient,
            status=body.get('status', 'queued'),
            provider_message_id=body.get('sid', f'twilio-sms-{int(datetime.utcnow().timestamp())}'),
            metadata=metadata or {},
        )
        return result.as_dict()
