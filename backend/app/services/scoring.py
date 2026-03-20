from dataclasses import dataclass

from app.db import models


@dataclass
class TargetingDecision:
    propensity_score: float
    confidence_score: float
    cluster_id: str
    cluster_label: str
    rationale: list[str]
    recommended_action: str
    recommended_channels: list[str]


def _age_to_score(age_band: str) -> float:
    if age_band in {'18-21', '22-25'}:
        return 0.95
    if age_band in {'26-29'}:
        return 0.8
    if age_band in {'15-17'}:
        return 0.55
    return 0.45


def _literacy_to_score(level: str) -> float:
    table = {'high': 0.95, 'medium': 0.75, 'low': 0.4}
    return table.get(level.lower(), 0.55)


def _income_need_score(band: str | None) -> float:
    if not band:
        return 0.5
    mapping = {
        'low': 0.9,
        'lower_middle': 0.75,
        'middle': 0.5,
        'upper_middle': 0.3,
        'high': 0.15,
    }
    return mapping.get(band.lower(), 0.5)


def _employment_need_score(status: str | None) -> float:
    if not status:
        return 0.55
    mapping = {
        'unemployed': 0.9,
        'underemployed': 0.75,
        'student': 0.65,
        'part_time': 0.6,
        'full_time': 0.3,
    }
    return mapping.get(status.lower(), 0.55)


def _recommended_channels(lead: models.YouthProfile, geo: models.Geography | None) -> list[str]:
    channels: list[str] = []
    if lead.consent_whatsapp:
        channels.append('whatsapp')
    if lead.consent_sms:
        channels.append('sms')
    if lead.consent_email:
        channels.append('email')
    if lead.consent_voice:
        channels.append('voice')

    internet = geo.internet_penetration_rate if geo else 55.0
    if internet < 45:
        # Lower digital access areas receive assisted outreach through posters.
        channels.append('community_poster')

    if not channels:
        channels = ['community_poster']
    return channels


def compute_targeting_decision(lead: models.YouthProfile, geo: models.Geography | None = None) -> TargetingDecision:
    reasons: list[str] = []

    consent_count = sum([
        1 if lead.consent_sms else 0,
        1 if lead.consent_whatsapp else 0,
        1 if lead.consent_email else 0,
        1 if lead.consent_voice else 0,
    ])
    channel_score = min(consent_count / 3.0, 1.0)

    age_score = _age_to_score(lead.age_band)
    literacy_score = _literacy_to_score(lead.digital_literacy_level)
    income_need = _income_need_score(lead.household_income_band)
    employment_need = _employment_need_score(lead.employment_status)

    geo_need = 0.5
    geo_access = 0.55
    if geo:
        geo_need = min(max((geo.unemployment_rate / 100.0) * 0.6 + (geo.skill_gap_index / 100.0) * 0.4, 0.0), 1.0)
        geo_access = min(max(geo.internet_penetration_rate / 100.0, 0.0), 1.0)
        if geo.unemployment_rate >= 12:
            reasons.append('District unemployment indicates strong need for skilling intervention')
        if geo.skill_gap_index >= 65:
            reasons.append('Regional skill gap is high and aligns with program relevance')
    else:
        reasons.append('Geography profile not found, using conservative defaults')

    need_score = (income_need * 0.45) + (employment_need * 0.35) + (geo_need * 0.2)

    propensity = (
        age_score * 0.25
        + literacy_score * 0.2
        + channel_score * 0.25
        + need_score * 0.2
        + geo_access * 0.1
    )
    propensity = min(max(propensity, 0.0), 0.99)

    confidence = 0.55
    if lead.household_income_band:
        confidence += 0.1
    if lead.employment_status:
        confidence += 0.1
    if geo:
        confidence += 0.15
    if consent_count > 0:
        confidence += 0.05
    confidence = min(confidence, 0.98)

    if need_score >= 0.7 and propensity >= 0.65:
        cluster_id = 'c1'
        cluster_label = 'high_need_high_potential'
    elif need_score >= 0.7 and propensity < 0.65:
        cluster_id = 'c2'
        cluster_label = 'high_need_low_readiness'
    elif need_score < 0.7 and propensity >= 0.72:
        cluster_id = 'c3'
        cluster_label = 'market_ready_fast_track'
    else:
        cluster_id = 'c4'
        cluster_label = 'nurture_segment'

    if lead.preferred_language != 'en':
        reasons.append('Localized communication is available in the preferred language')
    if consent_count >= 2:
        reasons.append('Multiple consented channels support higher engagement probability')
    if literacy_score >= 0.75:
        reasons.append('Digital literacy supports low-friction onboarding steps')

    channels = _recommended_channels(lead, geo)

    if 'whatsapp' in channels:
        action = 'send_whatsapp_then_sms_48h_followup'
    elif 'sms' in channels:
        action = 'send_sms_then_voice_task_48h'
    else:
        action = 'create_community_poster_and_call_assist'

    return TargetingDecision(
        propensity_score=round(propensity, 4),
        confidence_score=round(confidence, 4),
        cluster_id=cluster_id,
        cluster_label=cluster_label,
        rationale=reasons or ['Segment scored with regional and individual context'],
        recommended_action=action,
        recommended_channels=channels,
    )
