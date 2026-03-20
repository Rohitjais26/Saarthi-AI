from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Geography, MetricEvent, RegionalSkillSnapshot
from app.db.session import get_db
from app.schemas.data import RegionalSkillIngestRequest

router = APIRouter()


@router.post('/ingest/regional-skill')
def ingest_regional_skill_data(payload: RegionalSkillIngestRequest, db: Session = Depends(get_db)):
    if not payload.rows:
        return {'ingested_rows': 0, 'states_covered': 0}

    next_geo_id = db.execute(select(func.coalesce(func.max(Geography.id), 0))).scalar_one() + 1
    states: set[str] = set()

    for index, row in enumerate(payload.rows):
        states.add(row.state_code)
        geo = db.query(Geography).filter(Geography.district_code == row.district_code).first()
        if not geo:
            geo = Geography(
                id=next_geo_id,
                state_code=row.state_code,
                state_name=row.state_name,
                district_code=row.district_code,
                district_name=row.district_name,
            )
            next_geo_id += 1

        geo.state_code = row.state_code
        geo.state_name = row.state_name
        geo.district_name = row.district_name
        geo.youth_population = row.youth_population
        geo.female_participation_rate = row.female_participation_rate
        geo.unemployment_rate = row.unemployment_rate
        geo.median_household_income = row.median_household_income
        geo.internet_penetration_rate = row.internet_penetration_rate
        geo.skill_gap_index = row.skill_gap_index
        geo.rural_ratio = max(0.0, min(1.0, (100.0 - row.internet_penetration_rate) / 100.0))
        db.merge(geo)

        snapshot_id = f"rss-{row.district_code}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{index}"
        snapshot = RegionalSkillSnapshot(
            id=snapshot_id,
            state_code=row.state_code,
            district_code=row.district_code,
            source=row.source,
            demographics_json={
                'youth_population': row.youth_population,
                'female_participation_rate': row.female_participation_rate,
            },
            economics_json={
                'unemployment_rate': row.unemployment_rate,
                'median_household_income': row.median_household_income,
            },
            skills_json={
                'top_skills': row.top_skills,
                'demand_skills': row.demand_skills,
                'skill_gap_index': row.skill_gap_index,
            },
        )
        db.merge(snapshot)

    event = MetricEvent(
        id=f"evt-data-ingested-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        event_name='data.ingested',
        props_json={
            'rows': len(payload.rows),
            'states_covered': len(states),
        },
    )
    db.merge(event)
    db.commit()

    return {
        'ingested_rows': len(payload.rows),
        'states_covered': len(states),
        'states': sorted(states),
    }


@router.get('/coverage')
def data_coverage(db: Session = Depends(get_db)):
    states = db.execute(select(func.count(func.distinct(Geography.state_code)))).scalar_one()
    districts = db.execute(select(func.count(Geography.id))).scalar_one()
    snapshots = db.execute(select(func.count(RegionalSkillSnapshot.id))).scalar_one()
    latest_snapshot_ts = db.execute(select(func.max(RegionalSkillSnapshot.ts))).scalar_one()
    return {
        'states_count': states,
        'district_count': districts,
        'snapshot_count': snapshots,
        'latest_snapshot_ts': latest_snapshot_ts.isoformat() if latest_snapshot_ts else None,
    }
