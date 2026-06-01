from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import get_password_hash
from app.db.base import Base
from app.models.department import Department
from app.models.doctor import Doctor
from app.models.enums import LeaveStatus, LeaveType, PreferredShift, UserRole
from app.models.leave import LeaveRequest
from app.models.user import User
from app.services.roster_scheduler import RosterScheduler


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


def seed_minimum(db):
    department = Department(name="Emergency", code="EMR")
    admin = User(
        email="admin@test.local",
        full_name="Admin",
        hashed_password=get_password_hash("12345678"),
        role=UserRole.ADMIN,
    )
    db.add_all([department, admin])
    db.flush()
    for index in range(1, 26):
        user = User(
            email=f"doctor{index}@test.local",
            full_name=f"Doctor {index}",
            hashed_password=get_password_hash("Doctor@123"),
            role=UserRole.DOCTOR,
        )
        db.add(user)
        db.flush()
        db.add(
            Doctor(
                user_id=user.id,
                name=f"Doctor {index}",
                email=user.email,
                phone=f"+880170000{index:04d}",
                department_id=department.id,
                designation="Medical Officer",
                max_monthly_duty=12,
                preferred_shift=PreferredShift.FLEXIBLE,
                weekly_off_day="Friday",
            )
        )
    db.commit()
    return admin


def test_scheduler_respects_leave_and_single_duty_per_day(db_session):
    admin = seed_minimum(db_session)
    doctor = db_session.query(Doctor).first()
    leave_date = date(2026, 6, 10)
    db_session.add(
        LeaveRequest(
            doctor_id=doctor.id,
            leave_date=leave_date,
            leave_type=LeaveType.CASUAL,
            reason="Approved test leave",
            status=LeaveStatus.APPROVED,
        )
    )
    db_session.commit()

    result = RosterScheduler(db_session).generate_monthly_roster(month=6, year=2026, actor=admin, overwrite=True, seed=7)

    assignments = result["run"].assignments
    doctor_day_pairs = {(item.doctor_id, item.duty_date) for item in assignments}
    assert len(doctor_day_pairs) == len(assignments)
    assert all(not (item.doctor_id == doctor.id and item.duty_date == leave_date) for item in assignments)
