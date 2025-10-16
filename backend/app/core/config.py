from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENV: str = "development"
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"
    JWT_SECRET: str = "changeme"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


class AppSettings(BaseSettings):
    APP_NAME: str = "Hack Your Own Web"


    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


class MailSettings(BaseSettings):
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@example.com"
    MAIL_FROM_NAME: str = "Hack Your Own Web"
    MAIL_PORT: str = "587"
    MAIL_SERVER: str = "smtp.example.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    MAIL_DEBUG: bool = False
    USE_CREDENTIALS: bool = True


    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


class CelerySettings(BaseSettings):
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


class ZAPSettings(BaseSettings):
    ZAP_HOST: str = "localhost"
    ZAP_PORT: int = 8090
    ZAP_API_KEY: str = "changeme"
    USE_DOCKER_ZAP: bool = True
    ZAP_DOCKER_IMAGE: str = "ghcr.io/zaproxy/zaproxy:stable"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


Config = Settings()
AppConfig = AppSettings()
MailConfig = MailSettings()
CeleryConfig = CelerySettings()
ZAPConfig = ZAPSettings()
