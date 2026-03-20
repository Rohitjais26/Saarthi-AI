import smtplib
from email.message import EmailMessage
from datetime import datetime

from app.core.config import settings
from app.integrations.base import MessageProvider, ProviderError, SendResult


class SMTPEmailProvider(MessageProvider):
    def send_message(self, channel: str, recipient: str, content: str, metadata: dict | None = None) -> dict:
        if not settings.smtp_host or not settings.smtp_from:
            raise ProviderError('SMTP host/from are not configured')

        subject = (metadata or {}).get('subject', 'Program Opportunity')
        msg = EmailMessage()
        msg['From'] = settings.smtp_from
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.set_content(content)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            server.starttls()
            if settings.smtp_user and settings.smtp_pass:
                server.login(settings.smtp_user, settings.smtp_pass)
            server.send_message(msg)

        result = SendResult(
            provider='smtp',
            channel=channel,
            recipient=recipient,
            status='sent',
            provider_message_id=f'smtp-{int(datetime.utcnow().timestamp())}',
            metadata=metadata or {},
        )
        return result.as_dict()
