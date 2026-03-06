import os

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Pollution Monitoring and Alert System"
    db_url: str = os.getenv("PMAS_DB_URL", "sqlite:///./pmas.db")
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
