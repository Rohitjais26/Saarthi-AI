from app.db import models
from app.services.scoring import compute_targeting_decision


def test_targeting_decision_outputs_cluster_and_channels():
    lead = models.YouthProfile(
        id='L-test',
        first_name='Asha',
        age_band='18-21',
        district_code='D001',
        preferred_language='hi',
        digital_literacy_level='medium',
        employment_status='unemployed',
        household_income_band='low',
        consent_sms=True,
        consent_whatsapp=True,
    )
    geo = models.Geography(
        id=1,
        state_code='UP',
        state_name='Uttar Pradesh',
        district_code='D001',
        district_name='Lucknow',
        unemployment_rate=13.5,
        internet_penetration_rate=43.0,
        skill_gap_index=74.0,
    )

    decision = compute_targeting_decision(lead, geo)

    assert decision.cluster_id in {'c1', 'c2', 'c3', 'c4'}
    assert 0 <= decision.propensity_score <= 0.99
    assert decision.confidence_score >= 0.55
    assert 'community_poster' in decision.recommended_channels
