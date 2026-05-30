from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import PreferredShift


class DepartmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    is_active: bool


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    code: str = Field(min_length=2, max_length=30)
    is_active: bool = True


class DoctorBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    phone: str = Field(min_length=6, max_length=40)
    department_id: int
    designation: str = Field(min_length=2, max_length=120)
    max_monthly_duty: int = Field(default=12, ge=1, le=31)
    preferred_shift: PreferredShift = PreferredShift.FLEXIBLE
    weekly_off_day: str = Field(default="Friday", max_length=12)
    is_active: bool = True


class DoctorCreate(DoctorBase):
    create_user_account: bool = True
    initial_password: str = Field(default="Doctor@123", min_length=8)


class DoctorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=6, max_length=40)
    department_id: int | None = None
    designation: str | None = Field(default=None, min_length=2, max_length=120)
    max_monthly_duty: int | None = Field(default=None, ge=1, le=31)
    preferred_shift: PreferredShift | None = None
    weekly_off_day: str | None = Field(default=None, max_length=12)
    is_active: bool | None = None


class DoctorRead(DoctorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    department: DepartmentRead
