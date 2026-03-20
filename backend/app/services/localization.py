TEMPLATES = {
    'en': {
        'whatsapp_short': 'Hi {{name}}, seats for {{program}} in {{district}} are open. Apply here: {{cta_link}}',
        'sms_short': '{{name}}, {{program}} enrollment is open in {{district}}. Start now: {{cta_link}} Reply STOP to opt out.',
        'email_subject': '{{name}}, you may be eligible for {{program}}',
        'email_body': 'Hello {{name}}, opportunities in {{district}} are open. Register at {{cta_link}} before {{deadline}}.',
        'voice_script': 'Hello {{name}}, this is support for {{program}} in {{district}}. Press 1 to continue your application.',
        'community_poster': '{{program}} enrollment help desk now active in {{district}}. Visit {{cta_link}} for support.',
    },
    'hi': {
        'whatsapp_short': 'Namaste {{name}}, {{district}} mein {{program}} ke liye registration khula hai. Yahan apply karein: {{cta_link}}',
        'sms_short': '{{name}}, {{district}} mein {{program}} registration open hai. Shuru karein: {{cta_link}} STOP bhejkar opt-out karein.',
        'email_subject': '{{name}}, aap {{program}} ke liye eligible ho sakte hain',
        'email_body': 'Namaste {{name}}, {{district}} mein avsar uplabdh hain. {{cta_link}} par registration karein. Last date: {{deadline}}.',
        'voice_script': 'Namaste {{name}}, {{district}} mein {{program}} sahayata ke liye 1 dabaiye.',
        'community_poster': '{{district}} mein {{program}} registration camp shuru. Madad ke liye {{cta_link}} par jayein.',
    },
}


def render_template(template_key: str, values: dict[str, str], language: str = 'en') -> str:
    language = (language or 'en').lower()
    templates = TEMPLATES.get(language, TEMPLATES['en'])
    template = templates.get(template_key, TEMPLATES['en'].get(template_key, ''))
    for k, v in values.items():
        template = template.replace('{{' + k + '}}', str(v))
    return template


def generate_outreach_script(
    channel: str,
    lead_name: str,
    district: str,
    program: str,
    cta_link: str,
    language: str = 'en',
    deadline: str = 'soon',
) -> str:
    template_map = {
        'whatsapp': 'whatsapp_short',
        'sms': 'sms_short',
        'email': 'email_body',
        'voice': 'voice_script',
        'voice_task': 'voice_script',
        'community_poster': 'community_poster',
    }
    template_key = template_map.get(channel, 'whatsapp_short')
    values = {
        'name': lead_name or 'Learner',
        'district': district,
        'program': program,
        'cta_link': cta_link,
        'deadline': deadline,
    }
    return render_template(template_key, values, language=language)
