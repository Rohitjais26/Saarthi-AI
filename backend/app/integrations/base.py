from dataclasses import dataclass


class ProviderError(Exception):
    pass


@dataclass
class SendResult:
    provider: str
    channel: str
    recipient: str
    status: str
    provider_message_id: str
    metadata: dict

    def as_dict(self) -> dict:
        return {
            'provider': self.provider,
            'channel': self.channel,
            'recipient': self.recipient,
            'status': self.status,
            'provider_message_id': self.provider_message_id,
            'metadata': self.metadata,
        }


class MessageProvider:
    def send_message(self, channel: str, recipient: str, content: str, metadata: dict | None = None) -> dict:
        raise NotImplementedError
