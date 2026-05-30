from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import DutyType, ShiftType, enum_values


class RosterRun(Base):
    __tablename__ = "roster_runs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    month: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    generated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="completed", nullable=False)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    generated_by = relationship("User")
    assignments = relationship("DutyAssignment", back_populates="roster_run")


class DutyAssignment(Base):
    __tablename__ = "duty_assignments"
    __table_args__ = (
        UniqueConstraint("doctor_id", "duty_date", name="uq_doctor_one_duty_per_day"),
        UniqueConstraint("duty_date", "duty_type", name="uq_roster_slot_once"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False, index=True)
    duty_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    duty_type: Mapped[DutyType] = mapped_column(
        Enum(DutyType, values_callable=enum_values, name="duty_type"),
        nullable=False,
        index=True,
    )
    shift: Mapped[ShiftType] = mapped_column(
        Enum(ShiftType, values_callable=enum_values, name="shift_type"),
        nullable=False,
        index=True,
    )
    roster_run_id: Mapped[int | None] = mapped_column(ForeignKey("roster_runs.id"), nullable=True)
    is_manual_override: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source: Mapped[str] = mapped_column(String(40), default="auto", nullable=False)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    doctor = relationship("Doctor", back_populates="duties")
    roster_run = relationship("RosterRun", back_populates="assignments")
    created_by = relationship("User")
