from app.services.localization import generate_outreach_script, render_template


def test_render_template_supports_hindi():
    out = render_template(
        'sms_short',
        {'name': 'Asha', 'program': 'SkillTrack', 'district': 'Pune', 'cta_link': 'https://x'},
        language='hi',
    )
    assert 'Asha' in out
    assert 'SkillTrack' in out


def test_generate_outreach_script_for_poster_channel():
    out = generate_outreach_script(
        channel='community_poster',
        lead_name='Ravi',
        district='D010',
        program='JobReady',
        cta_link='https://example.org',
        language='en',
    )
    assert 'JobReady' in out
