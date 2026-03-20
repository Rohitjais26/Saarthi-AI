from datetime import datetime


def _safe_pct(value: float) -> int:
    return max(0, min(100, int(round(value))))


def _allocation_from_readiness(whatsapp_ratio: float, sms_ratio: float, voice_ratio: float, poster_ratio: float) -> list[dict]:
    allocations = [
        {'type': 'whatsapp', 'allocation_pct': _safe_pct(whatsapp_ratio * 100)},
        {'type': 'sms', 'allocation_pct': _safe_pct(sms_ratio * 100)},
        {'type': 'voice', 'allocation_pct': _safe_pct(voice_ratio * 100)},
        {'type': 'community_poster', 'allocation_pct': _safe_pct(poster_ratio * 100)},
    ]
    total = sum(row['allocation_pct'] for row in allocations)
    if total != 100:
        allocations[0]['allocation_pct'] += (100 - total)
    return allocations


def build_campaign_plan(
    campaign_id: str,
    segment_filter: dict,
    lead_profiles: list | None = None,
    avg_internet_penetration: float = 55.0,
) -> dict:
    lead_profiles = lead_profiles or []
    lead_count = max(1, len(lead_profiles))

    whatsapp_ratio = sum(1 for lead in lead_profiles if getattr(lead, 'consent_whatsapp', False)) / lead_count
    sms_ratio = sum(1 for lead in lead_profiles if getattr(lead, 'consent_sms', False)) / lead_count
    voice_ratio = sum(1 for lead in lead_profiles if getattr(lead, 'consent_voice', False)) / lead_count
    email_ratio = sum(1 for lead in lead_profiles if getattr(lead, 'consent_email', False)) / lead_count

    poster_ratio = 0.05
    if avg_internet_penetration < 50:
        poster_ratio = 0.2
        whatsapp_ratio = max(0.2, whatsapp_ratio - 0.05)

    total = whatsapp_ratio + sms_ratio + voice_ratio + poster_ratio
    if total <= 0:
        whatsapp_ratio, sms_ratio, voice_ratio, poster_ratio = 0.5, 0.25, 0.15, 0.1
    else:
        whatsapp_ratio /= total
        sms_ratio /= total
        voice_ratio /= total
        poster_ratio /= total

    return {
        'campaign_id': campaign_id,
        'generated_at': datetime.utcnow().isoformat(),
        'segment_filter': segment_filter,
        'channels': _allocation_from_readiness(whatsapp_ratio, sms_ratio, voice_ratio, poster_ratio),
        'cadence': {
            'max_touches_per_7d': 3,
            'steps': [
                {'day_offset': 0, 'channel': 'whatsapp', 'template_id': 'whatsapp_short'},
                {'day_offset': 2, 'channel': 'sms', 'template_id': 'sms_short'},
                {'day_offset': 4, 'channel': 'voice', 'template_id': 'voice_script'},
                {'day_offset': 5, 'channel': 'community_poster', 'template_id': 'community_poster'},
            ],
        },
        'ab_test': {
            'experiment_key': 'copy_tone_test',
            'variants': ['supportive', 'urgent_benefit'],
            'split_pct': [50, 50],
        },
        'compliance': {
            'require_consent': True,
            'opt_out_keyword': 'STOP',
            'quiet_hours_local': {'start': '21:00', 'end': '08:00'},
        },
        'personalization': {
            'language_adaptive': True,
            'include_local_reference': True,
            'email_ratio': round(email_ratio, 3),
        },
    }
