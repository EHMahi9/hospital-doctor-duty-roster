from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.doctor import Doctor
from app.models.duty import DutyAssignment
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.roster import (
    ConflictRead,
    DutyAssignmentRead,
    MonthlySummary,
    RosterGenerateRequest,
    RosterGenerateResponse,
    RosterManualOverrideRequest,
)
from app.services.analytics_service import calculate_monthly_summary, month_bounds
from app.services.export_service import export_roster_pdf, export_roster_xlsx
from app.services.roster_scheduler import RosterScheduler

router = APIRouter()


@router.get("", response_model=list[DutyAssignmentRead])
def monthly_roster(
    month: int = Query(ge=1, le=12),
    year: int = Query(ge=2020, le=2100),
    department_id: int | None = None,
    doctor_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[DutyAssignment]:
    start, end = month_bounds(month, year)
    query = (
        db.query(DutyAssignment)
        .options(joinedload(DutyAssignment.doctor).joinedload(Doctor.department))
        .filter(DutyAssignment.duty_date >= start, DutyAssignment.duty_date <= end)
    )
    if doctor_id:
        query = query.filter(DutyAssignment.doctor_id == doctor_id)
    if department_id:
        query = query.join(Doctor).filter(Doctor.department_id == department_id)
    return query.order_by(DutyAssignment.duty_date.asc(), DutyAssignment.duty_type.asc()).all()


@router.post("/generate", response_model=RosterGenerateResponse)
def generate_roster(
    payload: RosterGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
) -> dict:
    scheduler = RosterScheduler(db)
    try:
        return scheduler.generate_monthly_roster(actor=current_user, **payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/manual-override", response_model=DutyAssignmentRead)
def manual_override(
    payload: RosterManualOverrideRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
) -> DutyAssignment:
    assignment, conflicts = RosterScheduler(db).manual_override(actor=current_user, **payload.model_dump())
    if conflicts and not payload.force:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=conflicts)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=conflicts)
    return assignment


@router.get("/conflicts", response_model=list[ConflictRead])
def roster_conflicts(
    month: int = Query(ge=1, le=12),
    year: int = Query(ge=2020, le=2100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[dict]:
    return RosterScheduler(db).detect_conflicts(month=month, year=year)


@router.get("/summary", response_model=MonthlySummary)
def monthly_summary(
    month: int = Query(ge=1, le=12),
    year: int = Query(ge=2020, le=2100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    return calculate_monthly_summary(db, month, year)


@router.get("/export.xlsx")
def export_xlsx(
    month: int = Query(ge=1, le=12),
    year: int = Query(ge=2020, le=2100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    stream = export_roster_xlsx(db, month, year)
    filename = f"hospital-roster-{year}-{month:02d}.xlsx"
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export.pdf")
def export_pdf(
    month: int = Query(ge=1, le=12),
    year: int = Query(ge=2020, le=2100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    stream = export_roster_pdf(db, month, year)
    filename = f"hospital-roster-{year}-{month:02d}.pdf"
    return StreamingResponse(
        stream,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
