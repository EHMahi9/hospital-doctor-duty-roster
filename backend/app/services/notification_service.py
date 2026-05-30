from datetime import datetime
from email.message import EmailMessage
import smtplib

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import NotificationChannel, NotificationStatus
from app.models.notification import Notification
from app.models.user import User


def queue_system_notification(
    db: Session,
    *,
    user: User | None,
    title: str,
    message: str,
    channel: NotificationChannel = NotificationChannel.SYSTEM,
) -> Notification:
    notification = Notification(
        user_id=user.id if user else None,
        title=title,
        message=message,
        channel=channel,
        status=NotificationStatus.PENDING,
    )
    db.add(notification)
    return notification


def send_email_notification(to_email: str, subject: str, body: str) -> bool:
    if not settings.smtp_host or not settings.smtp_username or not settings.smtp_password:
        return False

    email = EmailMessage()
    email["From"] = settings.smtp_from_email
    email["To"] = to_email
    email["Subject"] = subject
    email.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(email)
    return True


def mark_notification_sent(notification: Notification) -> None:
    notification.status = NotificationStatus.SENT
    notification.sent_at = datetime.utcnow()
