from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_roles
from app.core.security import get_password_hash
from app.db.session import get_db
from app.models.department import Department
from app.models.doctor import Doctor
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.doctor import DepartmentCreate, DepartmentRead, DoctorCreate, DoctorRead, DoctorUpdate
from app.services.audit_service import write_audit_log

router = APIRouter()


@router.get("/departments", response_model=list[DepartmentRead])
def list_departments(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[Department]:
    return db.query(Department).order_by(Department.name.asc()).all()


@router.post("/departments", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
) -> Department:
    if db.query(Department).filter(or_(Department.name == payload.name, Department.code == payload.code)).one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Department name or code already exists.")
    department = Department(**payload.model_dump())
    db.add(department)
    db.flush()
    write_audit_log(db, actor=current_user, action="department.create", entity_type="Department", entity_id=department.id)
    db.commit()
    db.refresh(department)
    return department


@router.get("", response_model=list[DoctorRead])
def list_doctors(
    search: str | None = None,
    department_id: int | None = None,
    is_active: bool | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Doctor]:
    query = db.query(Doctor).options(joinedload(Doctor.department))
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(Doctor.name.ilike(pattern), Doctor.email.ilike(pattern), Doctor.phone.ilike(pattern)))
    if department_id:
        query = query.filter(Doctor.department_id == department_id)
    if is_active is not None:
        query = query.filter(Doctor.is_active == is_active)
    return query.order_by(Doctor.name.asc()).offset(offset).limit(limit).all()


@router.post("", response_model=DoctorRead, status_code=status.HTTP_201_CREATED)
def create_doctor(
    payload: DoctorCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
) -> Doctor:
    department = db.query(Department).filter(Department.id == payload.department_id, Department.is_active.is_(True)).one_or_none()
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found.")
    if db.query(Doctor).filter(Doctor.email == payload.email).one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Doctor email already exists.")

    user = None
    if payload.create_user_account:
        existing_user = db.query(User).filter(User.email == payload.email).one_or_none()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this doctor email already exists.")
        user = User(
            email=payload.email,
            full_name=payload.name,
            hashed_password=get_password_hash(payload.initial_password),
            role=UserRole.DOCTOR,
            is_active=payload.is_active,
        )
        db.add(user)
        db.flush()

    data = payload.model_dump(exclude={"create_user_account", "initial_password"})
    doctor = Doctor(**data, user_id=user.id if user else None)
    db.add(doctor)
    db.flush()
    write_audit_log(
        db,
        actor=current_user,
        action="doctor.create",
        entity_type="Doctor",
        entity_id=doctor.id,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(doctor)
    return doctor


@router.get("/{doctor_id}", response_model=DoctorRead)
def get_doctor(doctor_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Doctor:
    doctor = db.query(Doctor).options(joinedload(Doctor.department)).filter(Doctor.id == doctor_id).one_or_none()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")
    return doctor


@router.patch("/{doctor_id}", response_model=DoctorRead)
def update_doctor(
    doctor_id: int,
    payload: DoctorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
) -> Doctor:
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).one_or_none()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")
    data = payload.model_dump(exclude_unset=True)
    if "department_id" in data:
        department = db.query(Department).filter(Department.id == data["department_id"], Department.is_active.is_(True)).one_or_none()
        if not department:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found.")
    if "email" in data and data["email"] != doctor.email:
        if db.query(Doctor).filter(Doctor.email == data["email"], Doctor.id != doctor_id).one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Doctor email already exists.")
    for key, value in data.items():
        setattr(doctor, key, value)
    if doctor.user:
        doctor.user.email = doctor.email
        doctor.user.full_name = doctor.name
        doctor.user.is_active = doctor.is_active
    write_audit_log(db, actor=current_user, action="doctor.update", entity_type="Doctor", entity_id=doctor.id, metadata=data)
    db.commit()
    db.refresh(doctor)
    return doctor


@router.delete("/{doctor_id}", response_model=MessageResponse)
def delete_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
) -> MessageResponse:
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).one_or_none()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")
    doctor.is_active = False
    if doctor.user:
        doctor.user.is_active = False
    write_audit_log(db, actor=current_user, action="doctor.deactivate", entity_type="Doctor", entity_id=doctor.id)
    db.commit()
    return MessageResponse(message="Doctor deactivated successfully.")
