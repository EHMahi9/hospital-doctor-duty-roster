from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DutyType, ShiftType
from app.schemas.doctor import DoctorRead


class DutyAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    doctor_id: int
    duty_date: date
    duty_type: DutyType
    shift: ShiftType
    is_manual_override: bool
    source: str
    notes: str | None
    created_at: datetime
    doctor: DoctorRead


class RosterGenerateRequest(BaseModel):
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2020, le=2100)
    overwrite: bool = False
    preserve_manual_overrides: bool = True
    seed: int | None = None


class RosterManualOverrideRequest(BaseModel):
    doctor_id: int
    duty_date: date
    duty_type: DutyType
    notes: str | None = Field(default=None, max_length=255)
    force: bool = False


class ConflictRead(BaseModel):
    code: str
    severity: str
    message: str
    duty_date: date | None = None
    duty_type: DutyType | None = None
    doctor_id: int | None = None
    doctor_name: str | None = None
    assignment_id: int | None = None


class RosterRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    month: int
    year: int
    status: str
    seed: int | None
    summary_json: dict[str, Any] | None
    created_at: datetime


class RosterGenerateResponse(BaseModel):
    run: RosterRunRead
    assignments_created: int
    conflicts: list[ConflictRead]


class MonthlySummary(BaseModel):
    month: int
    year: int
    total_duties: int
    emergency_duties: int
    indoor_duties: int
    outdoor_duties: int
    night_duties: int
    overtime_hours: float
    by_doctor: list[dict[str, Any]]
