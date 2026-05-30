from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import PreferredShift, enum_values


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(40), nullable=False)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)
    designation: Mapped[str] = mapped_column(String(120), nullable=False)
    max_monthly_duty: Mapped[int] = mapped_column(Integer, default=12, nullable=False)
    preferred_shift: Mapped[PreferredShift] = mapped_column(
        Enum(PreferredShift, values_callable=enum_values, name="preferred_shift"),
        default=PreferredShift.FLEXIBLE,
        nullable=False,
    )
    weekly_off_day: Mapped[str] = mapped_column(String(12), default="Friday", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = relationship("User", back_populates="doctor_profile")
    department = relationship("Department", back_populates="doctors")
    leaves = relationship("LeaveRequest", back_populates="doctor", cascade="all, delete-orphan")
    duties = relationship("DutyAssignment", back_populates="doctor")
    balance_ledgers = relationship("BalanceLedger", back_populates="doctor")
