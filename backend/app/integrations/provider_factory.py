from app.core.config import settings
from app.integrations.base import MessageProvider, ProviderError
from app.integrations.community_poster import CommunityPosterProvider
from app.integrations.meta_whatsapp import MetaWhatsAppProvider
from app.integrations.mock_provider import MockProvider
from app.integrations.smtp_email import SMTPEmailProvider
from app.integrations.twilio_sms import TwilioSMSProvider
from app.integrations.twilio_voice import TwilioVoiceProvider


def get_provider(channel: str) -> MessageProvider:
    channel = channel.lower()

    if channel == 'sms':
        return _resolve_sms_provider()
    if channel == 'whatsapp':
        return _resolve_whatsapp_provider()
    if channel == 'email':
        return _resolve_email_provider()
    if channel in {'voice', 'voice_task'}:
        return _resolve_voice_provider()
    if channel == 'community_poster':
        return _resolve_poster_provider()

    raise ProviderError(f'Unsupported channel: {channel}')


def _resolve_sms_provider() -> MessageProvider:
    name = settings.sms_provider.lower()
    if name == 'mock':
        return MockProvider()
    if name == 'twilio':
        return TwilioSMSProvider()
    raise ProviderError(f'Unsupported SMS provider: {name}')


def _resolve_whatsapp_provider() -> MessageProvider:
    name = settings.whatsapp_provider.lower()
    if name == 'mock':
        return MockProvider()
    if name in {'meta', 'whatsapp_business'}:
        return MetaWhatsAppProvider()
    raise ProviderError(f'Unsupported WhatsApp provider: {name}')


def _resolve_email_provider() -> MessageProvider:
    name = settings.email_provider.lower()
    if name == 'mock':
        return MockProvider()
    if name in {'smtp', 'ses', 'sendgrid'}:
        return SMTPEmailProvider()
    raise ProviderError(f'Unsupported email provider: {name}')


def _resolve_voice_provider() -> MessageProvider:
    name = settings.voice_provider.lower()
    if name == 'mock':
        return MockProvider()
    if name == 'twilio':
        return TwilioVoiceProvider()
    raise ProviderError(f'Unsupported voice provider: {name}')


def _resolve_poster_provider() -> MessageProvider:
    name = settings.poster_provider.lower()
    if name in {'community', 'poster'}:
        return CommunityPosterProvider()
    if name == 'mock':
        return MockProvider()
    raise ProviderError(f'Unsupported community poster provider: {name}')
