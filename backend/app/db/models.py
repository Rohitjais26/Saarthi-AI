from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Geography(Base):
    __tablename__ = 'geography'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    state_code: Mapped[str] = mapped_column(String(10), index=True)
    state_name: Mapped[str] = mapped_column(String(100))
    district_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    district_name: Mapped[str] = mapped_column(String(120))
    rural_ratio: Mapped[float | None] = mapped_column(Float, default=0.0)
    youth_population: Mapped[int] = mapped_column(Integer, default=0)
    female_participation_rate: Mapped[float] = mapped_column(Float, default=0.0)
    unemployment_rate: Mapped[float] = mapped_column(Float, default=0.0)
    median_household_income: Mapped[float] = mapped_column(Float, default=0.0)
    internet_penetration_rate: Mapped[float] = mapped_column(Float, default=0.0)
    skill_gap_index: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class YouthProfile(Base):
    __tablename__ = 'youth_profile'

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    age_band: Mapped[str] = mapped_column(String(20), index=True)
    gender_optional: Mapped[str | None] = mapped_column(String(20), nullable=True)
    phone_hash: Mapped[str | None] = mapped_column(String(256), nullable=True)
    email_hash: Mapped[str | None] = mapped_column(String(256), nullable=True)
    district_code: Mapped[str] = mapped_column(String(20), index=True)
    education_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    employment_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    household_income_band: Mapped[str | None] = mapped_column(String(30), nullable=True)
    preferred_language: Mapped[str] = mapped_column(String(10), default='en', index=True)
    digital_literacy_level: Mapped[str] = mapped_column(String(20), default='medium')

    consent_sms: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_whatsapp: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_email: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_voice: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_ts: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    opt_out_ts: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ProgramCatalog(Base):
    __tablename__ = 'program_catalog'

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    program_name: Mapped[str] = mapped_column(String(255), index=True)
    state_code: Mapped[str] = mapped_column(String(10), index=True)
    min_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    required_education_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    requires_docs: Mapped[bool] = mapped_column(Boolean, default=False)
    deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class SegmentationScore(Base):
    __tablename__ = 'segmentation_score'

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    lead_id: Mapped[str] = mapped_column(String(64), ForeignKey('youth_profile.id'), index=True)
    cluster_id: Mapped[str] = mapped_column(String(50), index=True)
    cluster_label: Mapped[str] = mapped_column(String(120), index=True)
    propensity_score: Mapped[float] = mapped_column(Float, index=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5)
    recommended_channels_json: Mapped[dict] = mapped_column(JSON, default=dict)
    rationale_json: Mapped[dict] = mapped_column(JSON, default=dict)
    model_version: Mapped[str] = mapped_column(String(50), default='heuristic_v1')
    scored_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Campaign(Base):
    __tablename__ = 'campaign'

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    goal: Mapped[str] = mapped_column(String(120))
    segment_filter_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default='draft', index=True)
    created_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    deployment_mode: Mapped[str] = mapped_column(String(30), default='manual')
    deployed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CampaignVariant(Base):
    __tablename__ = 'campaign_variant'

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(64), ForeignKey('campaign.id'), index=True)
    channel: Mapped[str] = mapped_column(String(20), index=True)
    variant_key: Mapped[str] = mapped_column(String(20), index=True)
    template_id: Mapped[str] = mapped_column(String(64))
    allocation_pct: Mapped[int] = mapped_column(Integer, default=100)
    cadence_json: Mapped[dict] = mapped_column(JSON, default=dict)


class MessageTemplate(Base):
    __tablename__ = 'message_template'

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    channel: Mapped[str] = mapped_column(String(20), index=True)
    language: Mapped[str] = mapped_column(String(10), index=True)
    locale: Mapped[str] = mapped_column(String(20), default='default')
    tone: Mapped[str] = mapped_column(String(20), default='supportive')
    content: Mapped[str] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(String(20), default='text')
    safety_flags_json: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)


class Conversation(Base):
    __tablename__ = 'conversation'

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    lead_id: Mapped[str] = mapped_column(String(64), ForeignKey('youth_profile.id'), index=True)
    channel: Mapped[str] = mapped_column(String(20), index=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    last_intent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resolution_status: Mapped[str] = mapped_column(String(20), default='open')
    last_activity_ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class OnboardingCase(Base):
    __tablename__ = 'onboarding_case'

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    lead_id: Mapped[str] = mapped_column(String(64), ForeignKey('youth_profile.id'), index=True)
    program_id: Mapped[str | None] = mapped_column(String(64), ForeignKey('program_catalog.id'), nullable=True)
    state: Mapped[str] = mapped_column(String(40), default='registration_started', index=True)
    current_step: Mapped[str] = mapped_column(String(40), default='registration')
    step_status_json: Mapped[dict] = mapped_column(JSON, default=dict)
    documents_json: Mapped[dict] = mapped_column(JSON, default=dict)
    reminder_count: Mapped[int] = mapped_column(Integer, default=0)
    last_reminder_ts: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RegionalSkillSnapshot(Base):
    __tablename__ = 'regional_skill_snapshot'

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    state_code: Mapped[str] = mapped_column(String(10), index=True)
    district_code: Mapped[str] = mapped_column(String(20), index=True)
    source: Mapped[str] = mapped_column(String(120), default='manual_upload')
    demographics_json: Mapped[dict] = mapped_column(JSON, default=dict)
    economics_json: Mapped[dict] = mapped_column(JSON, default=dict)
    skills_json: Mapped[dict] = mapped_column(JSON, default=dict)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class MessageDispatch(Base):
    __tablename__ = 'message_dispatch'

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(64), ForeignKey('campaign.id'), index=True)
    lead_id: Mapped[str] = mapped_column(String(64), ForeignKey('youth_profile.id'), index=True)
    channel: Mapped[str] = mapped_column(String(30), index=True)
    status: Mapped[str] = mapped_column(String(30), default='queued', index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    provider_message_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MetricEvent(Base):
    __tablename__ = 'metric_event'

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    event_name: Mapped[str] = mapped_column(String(120), index=True)
    lead_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    campaign_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    variant_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    channel: Mapped[str | None] = mapped_column(String(20), nullable=True)
    props_json: Mapped[dict] = mapped_column(JSON, default=dict)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class AuditLog(Base):
    __tablename__ = 'audit_log'

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    actor_id: Mapped[str] = mapped_column(String(64), index=True)
    actor_role: Mapped[str] = mapped_column(String(30), index=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    resource_type: Mapped[str] = mapped_column(String(60))
    resource_id: Mapped[str] = mapped_column(String(64))
    before_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
