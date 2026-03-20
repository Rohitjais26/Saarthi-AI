from pydantic import BaseModel


class LeadCreate(BaseModel):
    id: str
    first_name: str | None = None
    age_band: str
    district_code: str
    education_level: str | None = None
    employment_status: str | None = None
    household_income_band: str | None = None
    preferred_language: str = 'en'
    digital_literacy_level: str = 'medium'
    consent_sms: bool = False
    consent_whatsapp: bool = False
    consent_email: bool = False
    consent_voice: bool = False


class LeadScoreResponse(BaseModel):
    lead_id: str
    cluster_id: str
    cluster_label: str
    propensity_score: float
    confidence_score: float
    recommended_channels: list[str]
    recommended_next_action: str
    rationale: list[str]
    model_version: str
