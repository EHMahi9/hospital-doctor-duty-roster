from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.core.security import get_password_hash
from app.db.init_db import create_database_schema, ensure_initial_data
from app.db.session import SessionLocal
from app.models.department import Department
from app.models.doctor import Doctor
from app.models.enums import LeaveStatus, LeaveType, PreferredShift, UserRole
from app.models.leave import LeaveRequest
from app.models.user import User
from app.services.roster_scheduler import RosterScheduler

SAMPLE_DOCTORS = [
    ("Dr. Afsana Rahman", "afsana.rahman@hospital.bd", "+8801711000001", "EMR", "Consultant", 13, PreferredShift.MORNING, "Friday"),
    ("Dr. Mahmud Hasan", "mahmud.hasan@hospital.bd", "+8801711000002", "EMR", "Resident Medical Officer", 13, PreferredShift.NIGHT, "Thursday"),
    ("Dr. Nusrat Jahan", "nusrat.jahan@hospital.bd", "+8801711000003", "MED", "Senior Consultant", 12, PreferredShift.MORNING, "Friday"),
    ("Dr. Tanvir Ahmed", "tanvir.ahmed@hospital.bd", "+8801711000004", "MED", "Registrar", 12, PreferredShift.EVENING, "Saturday"),
    ("Dr. Farhana Karim", "farhana.karim@hospital.bd", "+8801711000005", "SUR", "Consultant", 12, PreferredShift.FLEXIBLE, "Friday"),
    ("Dr. Imran Chowdhury", "imran.chowdhury@hospital.bd", "+8801711000006", "SUR", "Assistant Registrar", 12, PreferredShift.NIGHT, "Sunday"),
    ("Dr. Sadia Islam", "sadia.islam@hospital.bd", "+8801711000007", "CAR", "Cardiologist", 11, PreferredShift.MORNING, "Friday"),
    ("Dr. Rezaul Kabir", "rezaul.kabir@hospital.bd", "+8801711000008", "CAR", "Medical Officer", 12, PreferredShift.EVENING, "Monday"),
    ("Dr. Priyanka Saha", "priyanka.saha@hospital.bd", "+8801711000009", "OBG", "Consultant", 12, PreferredShift.MORNING, "Friday"),
    ("Dr. Sabrina Akter", "sabrina.akter@hospital.bd", "+8801711000010", "OBG", "Registrar", 12, PreferredShift.NIGHT, "Wednesday"),
    ("Dr. Arif Hossain", "arif.hossain@hospital.bd", "+8801711000011", "PED", "Paediatrician", 11, PreferredShift.MORNING, "Friday"),
    ("Dr. Miftah Uddin", "miftah.uddin@hospital.bd", "+8801711000012", "PED", "Medical Officer", 12, PreferredShift.FLEXIBLE, "Tuesday"),
    ("Dr. Samira Khan", "samira.khan@hospital.bd", "+8801711000013", "ORT", "Orthopaedic Surgeon", 12, PreferredShift.EVENING, "Friday"),
    ("Dr. Faisal Bari", "faisal.bari@hospital.bd", "+8801711000014", "ORT", "Registrar", 12, PreferredShift.NIGHT, "Saturday"),
    ("Dr. Lamia Noor", "lamia.noor@hospital.bd", "+8801711000015", "ICU", "ICU Consultant", 14, PreferredShift.NIGHT, "Friday"),
    ("Dr. Asif Rahman", "asif.rahman@hospital.bd", "+8801711000016", "ICU", "Critical Care Officer", 14, PreferredShift.FLEXIBLE, "Thursday"),
]


def upsert_admin(db) -> User:
    admin = db.query(User).filter(User.email == "momenulislam900@gmail.com").one_or_none()
    if admin:
        return admin
    admin = User(
        email="momenulislam900@gmail.com",
        full_name="Hospital Admin",
        hashed_password=get_password_hash("12345678"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(admin)
    db.flush()
    return admin


def seed_doctors(db) -> None:
    departments = {department.code: department for department in db.query(Department).all()}
    for name, email, phone, department_code, designation, max_duty, preferred_shift, off_day in SAMPLE_DOCTORS:
        if db.query(Doctor).filter(Doctor.email == email).one_or_none():
            continue
        user = User(
            email=email,
            full_name=name,
            hashed_password=get_password_hash("Doctor@123"),
            role=UserRole.DOCTOR,
            is_active=True,
        )
        db.add(user)
        db.flush()
        db.add(
            Doctor(
                user_id=user.id,
                name=name,
                email=email,
                phone=phone,
                department_id=departments[department_code].id,
                designation=designation,
                max_monthly_duty=max_duty,
                preferred_shift=preferred_shift,
                weekly_off_day=off_day,
                is_active=True,
            )
        )
    db.flush()


def seed_leaves(db) -> None:
    today = date.today()
    doctors = db.query(Doctor).order_by(Doctor.id.asc()).limit(4).all()
    for index, doctor in enumerate(doctors, start=3):
        leave_date = today.replace(day=1) + timedelta(days=index * 3)
        exists = db.query(LeaveRequest).filter(LeaveRequest.doctor_id == doctor.id, LeaveRequest.leave_date == leave_date).one_or_none()
        if exists:
            continue
        db.add(
            LeaveRequest(
                doctor_id=doctor.id,
                leave_date=leave_date,
                leave_type=LeaveType.CASUAL,
                reason="Seeded sample leave for roster conflict testing.",
                status=LeaveStatus.APPROVED,
            )
        )
    db.flush()


def main() -> None:
    create_database_schema()
    db = SessionLocal()
    try:
        ensure_initial_data(db)
        admin = upsert_admin(db)
        seed_doctors(db)
        seed_leaves(db)
        db.commit()
        scheduler = RosterScheduler(db)
        today = date.today()
        result = scheduler.generate_monthly_roster(month=today.month, year=today.year, actor=admin, overwrite=True, seed=202605)
        print(
            f"Seed complete. Admin login: momenulislam900@gmail.com / 12345678. "
            f"Doctor login password: Doctor@123. Generated {result['assignments_created']} duties."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
