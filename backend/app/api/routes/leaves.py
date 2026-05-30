from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.doctor import Doctor
from app.models.duty import DutyAssignment
from app.models.enums import LeaveStatus, UserRole
from app.models.leave import LeaveRequest
from app.models.user import User
from app.schemas.leave import LeaveConflict, LeaveCreate, LeaveDecision, LeaveRead
from app.services.audit_service import write_audit_log
from app.services.notification_service import queue_system_notification

router = APIRouter()


@router.get("", response_model=list[LeaveRead])
def list_leaves(
    doctor_id: int | None = None,
    status_filter: LeaveStatus | None = Query(default=None, alias="status"),
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[LeaveRequest]:
    query = db.query(LeaveRequest).options(joinedload(LeaveRequest.doctor).joinedload(Doctor.department))
    if doctor_id:
        query = query.filter(LeaveRequest.doctor_id == doctor_id)
    if status_filter:
        query = query.filter(LeaveRequest.status == status_filter)
    if from_date:
        query = query.filter(LeaveRequest.leave_date >= from_date)
    if to_date:
        query = query.filter(LeaveRequest.leave_date <= to_date)
    return query.order_by(LeaveRequest.leave_date.asc()).all()


@router.post("", response_model=LeaveRead, status_code=status.HTTP_201_CREATED)
def apply_leave(
    payload: LeaveCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeaveRequest:
    doctor = db.query(Doctor).filter(Doctor.id == payload.doctor_id, Doctor.is_active.is_(True)).one_or_none()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")
    if current_user.role == UserRole.DOCTOR and (not current_user.doctor_profile or current_user.doctor_profile.id != payload.doctor_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Doctors can only apply leave for themselves.")
    duplicate = (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.doctor_id == payload.doctor_id,
            LeaveRequest.leave_date == payload.leave_date,
            LeaveRequest.status != LeaveStatus.REJECTED,
        )
        .one_or_none()
    )
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A leave request already exists for this doctor and date.")
    leave = LeaveRequest(**payload.model_dump(), requested_by_id=current_user.id)
    db.add(leave)
    db.flush()
    write_audit_log(db, actor=current_user, action="leave.apply", entity_type="LeaveRequest", entity_id=leave.id)
    db.commit()
    db.refresh(leave)
    return leave


@router.patch("/{leave_id}/decision", response_model=LeaveRead)
def decide_leave(
    leave_id: int,
    payload: LeaveDecision,
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
) -> LeaveRequest:
    if payload.status == LeaveStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Decision must approve or reject the leave.")
    leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).one_or_none()
    if not leave:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found.")
    if payload.status == LeaveStatus.APPROVED and not force:
        duty = (
            db.query(DutyAssignment)
            .filter(DutyAssignment.doctor_id == leave.doctor_id, DutyAssignment.duty_date == leave.leave_date)
            .one_or_none()
        )
        if duty:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Doctor already has {duty.duty_type.value} on this date. Use force=true after resolving the roster.",
            )

    leave.status = payload.status
    leave.reviewed_by_id = current_user.id
    leave.reviewed_at = datetime.utcnow()
    queue_system_notification(
        db,
        user=leave.doctor.user,
        title=f"Leave {payload.status.value}",
        message=f"Your leave request for {leave.leave_date.isoformat()} has been {payload.status.value}.",
    )
    write_audit_log(
        db,
        actor=current_user,
        action=f"leave.{payload.status.value}",
        entity_type="LeaveRequest",
        entity_id=leave.id,
        metadata={"note": payload.review_note},
    )
    db.commit()
    db.refresh(leave)
    return leave


@router.get("/conflicts", response_model=list[LeaveConflict])
def leave_conflicts(
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[LeaveConflict]:
    query = (
        db.query(LeaveRequest, DutyAssignment)
        .join(
            DutyAssignment,
            (DutyAssignment.doctor_id == LeaveRequest.doctor_id)
            & (DutyAssignment.duty_date == LeaveRequest.leave_date),
        )
        .filter(LeaveRequest.status == LeaveStatus.APPROVED)
    )
    if from_date:
        query = query.filter(LeaveRequest.leave_date >= from_date)
    if to_date:
        query = query.filter(LeaveRequest.leave_date <= to_date)
    conflicts = []
    for leave, duty in query.all():
        conflicts.append(
            LeaveConflict(
                leave_id=leave.id,
                doctor_id=leave.doctor_id,
                doctor_name=leave.doctor.name,
                leave_date=leave.leave_date,
                duty_assignment_id=duty.id,
                duty_type=duty.duty_type.value,
            )
        )
    return conflicts
