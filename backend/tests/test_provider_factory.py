from app.integrations.mock_provider import MockProvider
from app.integrations.provider_factory import get_provider
from app.integrations.community_poster import CommunityPosterProvider


def test_default_sms_provider_is_mock():
    provider = get_provider('sms')
    assert isinstance(provider, MockProvider)


def test_community_poster_provider_resolves():
    provider = get_provider('community_poster')
    assert isinstance(provider, CommunityPosterProvider)
