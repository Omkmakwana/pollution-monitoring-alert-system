import os

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Pollution Monitoring and Alert System"
    db_url: str = os.getenv("PMAS_DB_URL", "sqlite:///./pmas.db")
    api_key: str = os.getenv("PMAS_API_KEY", "")
    log_level: str = os.getenv("PMAS_LOG_LEVEL", "INFO").upper()
    default_page_size: int = int(os.getenv("PMAS_DEFAULT_PAGE_SIZE", "30"))
    max_page_size: int = int(os.getenv("PMAS_MAX_PAGE_SIZE", "100"))
    notification_retry_count: int = int(os.getenv("PMAS_NOTIFICATION_RETRY_COUNT", "2"))
    notification_retry_backoff_seconds: float = float(os.getenv("PMAS_NOTIFICATION_RETRY_BACKOFF_SECONDS", "0.5"))
    smtp_host: str = os.getenv("PMAS_SMTP_HOST", "")
    smtp_port: int = int(os.getenv("PMAS_SMTP_PORT", "587"))
    smtp_user: str = os.getenv("PMAS_SMTP_USER", "")
    smtp_password: str = os.getenv("PMAS_SMTP_PASSWORD", "")
    smtp_use_tls: bool = os.getenv("PMAS_SMTP_USE_TLS", "true").lower() == "true"
    email_from: str = os.getenv("PMAS_EMAIL_FROM", "")
    twilio_account_sid: str = os.getenv("PMAS_TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("PMAS_TWILIO_AUTH_TOKEN", "")
    twilio_from_phone: str = os.getenv("PMAS_TWILIO_FROM_PHONE", "")


settings = Settings()


def validate_settings() -> None:
    if settings.default_page_size < 1:
        raise ValueError("PMAS_DEFAULT_PAGE_SIZE must be >= 1")
    if settings.max_page_size < settings.default_page_size:
        raise ValueError("PMAS_MAX_PAGE_SIZE must be >= PMAS_DEFAULT_PAGE_SIZE")
    if settings.notification_retry_count < 0:
        raise ValueError("PMAS_NOTIFICATION_RETRY_COUNT must be >= 0")
    if settings.notification_retry_backoff_seconds < 0:
        raise ValueError("PMAS_NOTIFICATION_RETRY_BACKOFF_SECONDS must be >= 0")
