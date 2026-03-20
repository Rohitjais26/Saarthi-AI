from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    app_env: str = 'local'
    api_host: str = '0.0.0.0'
    api_port: int = 8000
    database_url: str = 'sqlite:///./outreach.db'
    redis_url: str = 'redis://localhost:6379/0'
    jwt_secret: str = 'change_me'

    sms_provider: str = 'mock'
    whatsapp_provider: str = 'mock'
    email_provider: str = 'mock'
    voice_provider: str = 'mock'
    poster_provider: str = 'community'

    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_sms_from: str | None = None
    twilio_voice_from: str | None = None

    meta_whatsapp_token: str | None = None
    meta_whatsapp_phone_number_id: str | None = None

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_pass: str | None = None
    smtp_from: str | None = None

    default_language: str = 'en'
    quiet_hours_start: str = '21:00'
    quiet_hours_end: str = '08:00'
    max_touches_per_7d: int = 3


settings = Settings()
