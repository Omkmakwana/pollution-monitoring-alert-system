import smtplib
from email.message import EmailMessage

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from app import crud, models
from app.config import settings


def send_email_alert(to_email: str, subject: str, body: str) -> tuple[bool, str | None, str | None]:
    if not settings.smtp_host or not settings.smtp_user or not settings.smtp_password or not settings.email_from:
        return False, None, "Email settings are not configured"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.email_from
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)
        return True, None, None
    except (OSError, smtplib.SMTPException) as exc:
        return False, None, str(exc)


def send_sms_alert(to_phone: str, body: str) -> tuple[bool, str | None, str | None]:
    if not settings.twilio_account_sid or not settings.twilio_auth_token or not settings.twilio_from_phone:
        return False, None, "Twilio settings are not configured"

    try:
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        message = client.messages.create(from_=settings.twilio_from_phone, to=to_phone, body=body)
        return True, message.sid, None
    except TwilioRestException as exc:
        return False, None, str(exc)


def notify_subscribers_for_alert(db, alert: models.Alert) -> None:
    subscribers = crud.list_active_subscribers(db)
    if not subscribers:
        return

    subject = f"[PMAS Alert:{alert.severity.upper()}] {alert.pollutant}"
    body = f"Station {alert.station_id}: {alert.message}"

    for subscriber in subscribers:
        if subscriber.channel == "email":
            success, provider_id, error_message = send_email_alert(subscriber.destination, subject, body)
        elif subscriber.channel == "sms":
            success, provider_id, error_message = send_sms_alert(subscriber.destination, body)
        else:
            success, provider_id, error_message = False, None, "Unsupported channel"

        crud.create_notification_log(
            db=db,
            alert_id=alert.id,
            channel=subscriber.channel,
            destination=subscriber.destination,
            delivery_status="sent" if success else "failed",
            provider_message_id=provider_id,
            error_message=error_message,
        )
