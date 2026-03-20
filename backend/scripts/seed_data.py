from datetime import datetime, timedelta
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.models import Geography, MessageTemplate, ProgramCatalog, RegionalSkillSnapshot
from app.db.session import SessionLocal


def seed() -> None:
    db = SessionLocal()
    try:
        geography_rows = [
            ('MH', 'Maharashtra', 'D001', 'Pune', 130000, 42.0, 10.8, 185000, 74.0, 62.0),
            ('UP', 'Uttar Pradesh', 'D002', 'Lucknow', 165000, 36.0, 13.5, 126000, 58.0, 71.0),
            ('GJ', 'Gujarat', 'D003', 'Ahmedabad', 120000, 41.0, 9.1, 198000, 78.0, 54.0),
            ('RJ', 'Rajasthan', 'D004', 'Jaipur', 118000, 35.5, 11.4, 132000, 61.0, 68.0),
            ('MP', 'Madhya Pradesh', 'D005', 'Bhopal', 112000, 34.0, 12.7, 124000, 59.0, 72.0),
            ('BR', 'Bihar', 'D006', 'Patna', 172000, 29.0, 15.6, 98000, 49.0, 78.0),
            ('WB', 'West Bengal', 'D007', 'Kolkata', 121000, 38.0, 10.9, 142000, 67.0, 63.0),
            ('KA', 'Karnataka', 'D008', 'Bengaluru Urban', 140000, 45.0, 8.3, 214000, 82.0, 49.0),
            ('TN', 'Tamil Nadu', 'D009', 'Chennai', 132000, 44.0, 8.9, 209000, 80.0, 52.0),
            ('AP', 'Andhra Pradesh', 'D010', 'Visakhapatnam', 116000, 39.0, 10.1, 156000, 69.0, 61.0),
            ('TS', 'Telangana', 'D011', 'Hyderabad', 127000, 43.0, 8.7, 205000, 81.0, 51.0),
            ('OD', 'Odisha', 'D012', 'Bhubaneswar', 108000, 33.0, 12.2, 122000, 57.0, 74.0),
            ('KL', 'Kerala', 'D013', 'Thiruvananthapuram', 98000, 46.0, 7.1, 219000, 84.0, 46.0),
            ('HR', 'Haryana', 'D014', 'Gurugram', 101000, 40.0, 9.8, 231000, 79.0, 53.0),
            ('PB', 'Punjab', 'D015', 'Ludhiana', 97000, 39.0, 9.5, 188000, 72.0, 58.0),
        ]

        geographies: list[Geography] = []
        snapshots: list[RegionalSkillSnapshot] = []
        for index, row in enumerate(geography_rows, start=1):
            state_code, state_name, district_code, district_name, youth_pop, female_pr, unemp, income, internet, skill_gap = row
            geographies.append(
                Geography(
                    id=index,
                    state_code=state_code,
                    state_name=state_name,
                    district_code=district_code,
                    district_name=district_name,
                    rural_ratio=max(0.0, min(1.0, (100.0 - internet) / 100.0)),
                    youth_population=youth_pop,
                    female_participation_rate=female_pr,
                    unemployment_rate=unemp,
                    median_household_income=income,
                    internet_penetration_rate=internet,
                    skill_gap_index=skill_gap,
                )
            )
            snapshots.append(
                RegionalSkillSnapshot(
                    id=f'rss-seed-{district_code}',
                    state_code=state_code,
                    district_code=district_code,
                    source='seed_2026',
                    demographics_json={'youth_population': youth_pop, 'female_participation_rate': female_pr},
                    economics_json={'unemployment_rate': unemp, 'median_household_income': income},
                    skills_json={
                        'top_skills': ['basic_computing', 'retail', 'field_sales'],
                        'demand_skills': ['digital_marketing', 'logistics', 'healthcare_assistant'],
                        'skill_gap_index': skill_gap,
                    },
                )
            )

        programs = [
            ProgramCatalog(
                id='P101',
                program_name='SkillTrack',
                state_code='MH',
                min_age=18,
                max_age=29,
                required_education_level='class_10',
                requires_docs=True,
                deadline=datetime.utcnow() + timedelta(days=45),
                active=True,
            ),
            ProgramCatalog(
                id='P102',
                program_name='JobReady',
                state_code='UP',
                min_age=18,
                max_age=27,
                required_education_level='class_12',
                requires_docs=False,
                deadline=datetime.utcnow() + timedelta(days=60),
                active=True,
            ),
            ProgramCatalog(
                id='P103',
                program_name='DigitalSales Pro',
                state_code='KA',
                min_age=18,
                max_age=30,
                required_education_level='class_12',
                requires_docs=True,
                deadline=datetime.utcnow() + timedelta(days=50),
                active=True,
            ),
        ]

        templates = [
            MessageTemplate(
                id='wa_short_v2_en',
                channel='whatsapp',
                language='en',
                locale='default',
                tone='supportive',
                content='Hi {{name}}, seats for {{program}} in {{district}} are open. Apply: {{cta_link}} Reply STOP to opt out.',
                content_type='text',
                safety_flags_json={'contains_optout': True},
                version=2,
            ),
            MessageTemplate(
                id='wa_short_v2_hi',
                channel='whatsapp',
                language='hi',
                locale='default',
                tone='supportive',
                content='Namaste {{name}}, {{district}} mein {{program}} registration open hai: {{cta_link}} STOP bhejkar opt-out karein.',
                content_type='text',
                safety_flags_json={'contains_optout': True},
                version=2,
            ),
            MessageTemplate(
                id='sms_short_v2_en',
                channel='sms',
                language='en',
                locale='default',
                tone='supportive',
                content='{{name}}, {{program}} enrollment open in {{district}}. Start: {{cta_link}} Reply STOP to opt out.',
                content_type='text',
                safety_flags_json={'contains_optout': True},
                version=2,
            ),
            MessageTemplate(
                id='voice_v2_en',
                channel='voice',
                language='en',
                locale='default',
                tone='supportive',
                content='Hello {{name}}, this is support for {{program}} in {{district}}. Press 1 to continue.',
                content_type='text',
                safety_flags_json={'contains_optout': False},
                version=2,
            ),
            MessageTemplate(
                id='poster_v1_en',
                channel='community_poster',
                language='en',
                locale='default',
                tone='informative',
                content='{{program}} enrollment desk now open in {{district}}. Visit {{cta_link}} for assistance.',
                content_type='text',
                safety_flags_json={'contains_optout': False},
                version=1,
            ),
        ]

        for row in geographies + snapshots + programs + templates:
            db.merge(row)

        db.commit()
        print('Seed data inserted/updated for 15 states.')
    finally:
        db.close()


if __name__ == '__main__':
    seed()
