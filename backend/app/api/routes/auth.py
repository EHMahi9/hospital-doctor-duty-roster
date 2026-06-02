from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.session import get_db
from app.models.doctor import Doctor
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, TokenUser, UserCreate, UserRead
from app.services.audit_service import write_audit_log

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive.")

    token = create_access_token(user.id, {"role": user.role.value})
    write_audit_log(
        db,
        actor=user,
        action="auth.login",
        entity_type="User",
        entity_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return TokenResponse(
        access_token=token,
        expires_in_minutes=settings.access_token_expire_minutes,
        user=TokenUser.model_validate(user),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    if not settings.allow_public_registration:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Public registration is disabled.")

    existing = db.query(User).filter(User.email == payload.email).one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists.")

    role = UserRole.STAFF
    doctor: Doctor | None = None
    full_name = payload.full_name

    if payload.account_type == "doctor":
        doctor = db.query(Doctor).filter(Doctor.email == payload.email).one_or_none()
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor profile not found. Ask an admin to add this doctor first.",
            )
        if doctor.user_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This doctor already has a user account.")
        role = UserRole.DOCTOR
        full_name = doctor.name

    user = User(
        email=payload.email,
        full_name=full_name,
        hashed_password=get_password_hash(payload.password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.flush()

    if doctor:
        doctor.user_id = user.id

    write_audit_log(
        db,
        actor=None,
        action="auth.register",
        entity_type="User",
        entity_id=user.id,
        metadata={"role": role.value},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, {"role": user.role.value})
    return TokenResponse(
        access_token=token,
        expires_in_minutes=settings.access_token_expire_minutes,
        user=TokenUser.model_validate(user),
    )


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
) -> User:
    if payload.role == UserRole.SUPER_ADMIN and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only super admins can create super admins.")
    existing = db.query(User).filter(User.email == payload.email).one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists.")
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
        is_active=payload.is_active,
    )
    db.add(user)
    db.flush()
    write_audit_log(db, actor=current_user, action="user.create", entity_type="User", entity_id=user.id)
    db.commit()
    db.refresh(user)
    return user
