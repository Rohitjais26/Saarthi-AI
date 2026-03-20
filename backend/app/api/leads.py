from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import Geography, MetricEvent, SegmentationScore, YouthProfile
from app.db.session import get_db
from app.schemas.leads import LeadCreate, LeadScoreResponse
from app.services.scoring import compute_targeting_decision

router = APIRouter()


@router.post('')
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)):
    lead = YouthProfile(
        id=payload.id,
        first_name=payload.first_name,
        age_band=payload.age_band,
        district_code=payload.district_code,
        education_level=payload.education_level,
        employment_status=payload.employment_status,
        household_income_band=payload.household_income_band,
        preferred_language=payload.preferred_language,
        digital_literacy_level=payload.digital_literacy_level,
        consent_sms=payload.consent_sms,
        consent_whatsapp=payload.consent_whatsapp,
        consent_email=payload.consent_email,
        consent_voice=payload.consent_voice,
        consent_ts=datetime.utcnow(),
    )
    db.merge(lead)
    db.merge(MetricEvent(id=f'evt-lead-created-{payload.id}', event_name='lead.created', lead_id=payload.id))
    db.commit()
    return {'lead_id': payload.id, 'status': 'created'}


@router.post('/{lead_id}/score', response_model=LeadScoreResponse)
def score_lead(lead_id: str, db: Session = Depends(get_db)):
    lead = db.get(YouthProfile, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail='Lead not found')

    geo = db.query(Geography).filter(Geography.district_code == lead.district_code).first()
    decision = compute_targeting_decision(lead, geo)
    row = SegmentationScore(
        id=f'score-{lead_id}',
        lead_id=lead_id,
        cluster_id=decision.cluster_id,
        cluster_label=decision.cluster_label,
        propensity_score=decision.propensity_score,
        confidence_score=decision.confidence_score,
        recommended_channels_json={'channels': decision.recommended_channels},
        rationale_json={'reasons': decision.rationale},
        model_version='targeting_v2',
    )
    db.merge(row)
    db.merge(MetricEvent(
        id=f'evt-lead-scored-{lead_id}',
        event_name='lead.scored',
        lead_id=lead_id,
        props_json={
            'cluster_id': decision.cluster_id,
            'cluster_label': decision.cluster_label,
            'propensity_score': decision.propensity_score,
            'confidence_score': decision.confidence_score,
        },
    ))
    db.commit()

    return LeadScoreResponse(
        lead_id=lead_id,
        cluster_id=decision.cluster_id,
        cluster_label=decision.cluster_label,
        propensity_score=decision.propensity_score,
        confidence_score=decision.confidence_score,
        recommended_channels=decision.recommended_channels,
        recommended_next_action=decision.recommended_action,
        rationale=decision.rationale,
        model_version='targeting_v2',
    )
