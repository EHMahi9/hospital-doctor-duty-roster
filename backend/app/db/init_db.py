from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import engine
from app.models import Department, User
from app.models.enums import UserRole

DEFAULT_DEPARTMENTS = [
    ("Emergency", "EMR"),
    ("Medicine", "MED"),
    ("Surgery", "SUR"),
    ("Cardiology", "CAR"),
    ("Obstetrics & Gynaecology", "OBG"),
    ("Paediatrics", "PED"),
    ("Orthopaedics", "ORT"),
    ("ICU", "ICU"),
]


def create_database_schema() -> None:
    Base.metadata.create_all(bind=engine)


def ensure_initial_data(db: Session) -> None:
    for name, code in DEFAULT_DEPARTMENTS:
        exists = db.query(Department).filter(Department.code == code).one_or_none()
        if not exists:
            db.add(Department(name=name, code=code))

    admin = db.query(User).filter(User.email == settings.first_super_admin_email).one_or_none()
    if not admin:
        db.add(
            User(
                email=settings.first_super_admin_email,
                full_name="System Super Admin",
                hashed_password=get_password_hash(settings.first_super_admin_password),
                role=UserRole.SUPER_ADMIN,
                is_active=True,
            )
        )
    db.commit()
