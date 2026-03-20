from datetime import datetime

import httpx

from app.core.config import settings
from app.integrations.base import MessageProvider, ProviderError, SendResult


class TwilioVoiceProvider(MessageProvider):
    def send_message(self, channel: str, recipient: str, content: str, metadata: dict | None = None) -> dict:
        if not settings.twilio_account_sid or not settings.twilio_auth_token or not settings.twilio_voice_from:
            raise ProviderError('Twilio Voice credentials are not configured')

        twiml = f'<Response><Say>{content}</Say></Response>'
        url = f'https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Calls.json'
        payload = {
            'From': settings.twilio_voice_from,
            'To': recipient,
            'Twiml': twiml,
        }

        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, data=payload, auth=(settings.twilio_account_sid, settings.twilio_auth_token))
        if response.status_code >= 300:
            raise ProviderError(f'Twilio Voice call failed: {response.status_code}')

        body = response.json()
        result = SendResult(
            provider='twilio_voice',
            channel=channel,
            recipient=recipient,
            status=body.get('status', 'queued'),
            provider_message_id=body.get('sid', f'twilio-voice-{int(datetime.utcnow().timestamp())}'),
            metadata=metadata or {},
        )
        return result.as_dict()
