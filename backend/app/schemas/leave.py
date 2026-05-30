from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import LeaveStatus, LeaveType
from app.schemas.doctor import DoctorRead


class LeaveBase(BaseModel):
    doctor_id: int
    leave_date: date
    leave_type: LeaveType = LeaveType.CASUAL
    reason: str = Field(min_length=3, max_length=1200)


class LeaveCreate(LeaveBase):
    pass


class LeaveDecision(BaseModel):
    status: LeaveStatus
    review_note: str | None = Field(default=None, max_length=500)


class LeaveRead(LeaveBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: LeaveStatus
    reviewed_by_id: int | None = None
    reviewed_at: datetime | None = None
    created_at: datetime
    doctor: DoctorRead


class LeaveConflict(BaseModel):
    leave_id: int
    doctor_id: int
    doctor_name: str
    leave_date: date
    duty_assignment_id: int
    duty_type: str
