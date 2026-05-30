from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.duty import DutyAssignment
from app.models.enums import NotificationChannel, UserRole
from app.models.notification import Notification
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.notification import NotificationRead
from app.services.notification_service import queue_system_notification

router = APIRouter()


@router.get("", response_model=list[NotificationRead])
def list_notifications(
    mine: bool = True,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Notification]:
    query = db.query(Notification)
    if mine or current_user.role not in {UserRole.SUPER_ADMIN, UserRole.ADMIN}:
        query = query.filter(Notification.user_id == current_user.id)
    return query.order_by(Notification.created_at.desc()).limit(limit).all()


@router.post("/shift-reminders", response_model=MessageResponse)
def queue_shift_reminders(
    target_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
) -> MessageResponse:
    reminder_date = target_date or (date.today() + timedelta(days=1))
    assignments = db.query(DutyAssignment).filter(DutyAssignment.duty_date == reminder_date).all()
    for assignment in assignments:
        queue_system_notification(
            db,
            user=assignment.doctor.user,
            title="Upcoming duty reminder",
            message=f"You are assigned to {assignment.duty_type.value} on {assignment.duty_date.isoformat()}.",
            channel=NotificationChannel.SYSTEM,
        )
    db.commit()
    return MessageResponse(message=f"Queued {len(assignments)} shift reminders for {reminder_date.isoformat()}.")
