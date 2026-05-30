from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BalanceLedger(Base):
    __tablename__ = "balance_ledgers"
    __table_args__ = (UniqueConstraint("doctor_id", "month", "year", name="uq_balance_doctor_month"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False, index=True)
    month: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    emergency_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    indoor_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    outdoor_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    night_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_duties: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    extra_duties: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    missed_duties: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    overtime_hours: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    fairness_score: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    workload_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    doctor = relationship("Doctor", back_populates="balance_ledgers")
