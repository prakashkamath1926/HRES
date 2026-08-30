import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "HRES - Heat Response Emergency System"
    DEBUG: bool = True
    API_V1_STR: str = "/api"

    # Database
    DATABASE_URL: str = "sqlite:///./data/hres.db"

    # API Keys (Simulated / Optional for MVP)
    FORTYGUARD_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    KIRO_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    RESEND_API_KEY: str | None = None
    GOOGLE_MAPS_API_KEY: str | None = None

    # Google Auth and RBAC Security
    GOOGLE_CLIENT_ID: str | None = None
    JWT_SECRET: str = "super_secret_dev_key_change_in_production"

    # Email Service Configuration
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None

    # App configuration (e.g. for Jaipur campus)
    DEFAULT_LATITUDE: float = 26.9124
    DEFAULT_LONGITUDE: float = 75.7873
    DEFAULT_LOCATION_NAME: str = "HeatShield Campus Zone, Jaipur"

    # Production: extra allowed origins (comma-separated)
    ALLOWED_ORIGINS: str = ""

    # Config model configuration to read from env file
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
