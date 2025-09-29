from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.models import db_models  # noqa: F401 - ensure models are imported

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def init_db() -> None:
    """Initialize database schema and seed baseline data."""

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        admin = _ensure_user(
            db,
            username="admin",
            password="admin123",
            role=db_models.UserRole.ADMIN,
            full_name="Administrador Padrao",
        )
        user = _ensure_user(
            db,
            username="user",
            password="user123",
            role=db_models.UserRole.USER,
            full_name="Usuario Demonstracao",
        )

        room = _ensure_resource(
            db,
            name="Sala 101",
            description="Sala principal para reunioes",
            resource_type="room",
            location="Bloco A",
            capacity=10,
        )
        lab = _ensure_resource(
            db,
            name="Laboratorio de Informatica",
            description="Laboratorio com 20 computadores",
            resource_type="lab",
            location="Bloco B",
            capacity=20,
        )

        _ensure_device(
            db,
            name="Tranca Sala 101",
            device_type=db_models.DeviceType.LOCK,
            status="locked",
            resource=room,
        )
        _ensure_device(
            db,
            name="Sensor Temperatura Lab",
            device_type=db_models.DeviceType.SENSOR,
            status="active",
            resource=lab,
            numeric_value=24.5,
        )

        _ensure_permission(db, user, room)
        _ensure_permission(db, user, lab)
        _ensure_permission(db, admin, room)
        _ensure_permission(db, admin, lab)

        db.commit()


def _ensure_user(
    db: Session,
    *,
    username: str,
    password: str,
    role: db_models.UserRole,
    full_name: str,
) -> db_models.User:
    existing = db.scalar(select(db_models.User).where(db_models.User.username == username))
    if existing:
        if existing.full_name != full_name:
            existing.full_name = full_name
        if existing.role != role:
            existing.role = role
        if not pwd_context.verify(password, existing.password_hash):
            existing.password_hash = pwd_context.hash(password)
        return existing

    user = db_models.User(
        username=username,
        password_hash=pwd_context.hash(password),
        role=role,
        full_name=full_name,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def _ensure_resource(
    db: Session,
    *,
    name: str,
    description: str,
    resource_type: str,
    location: str,
    capacity: int,
) -> db_models.Resource:
    existing = db.scalar(select(db_models.Resource).where(db_models.Resource.name == name))
    if existing:
        return existing

    resource = db_models.Resource(
        name=name,
        description=description,
        type=resource_type,
        location=location,
        capacity=capacity,
        status=db_models.ResourceStatus.AVAILABLE,
    )
    db.add(resource)
    db.flush()
    return resource


def _ensure_device(
    db: Session,
    *,
    name: str,
    device_type: db_models.DeviceType,
    status: str,
    resource: db_models.Resource,
    numeric_value: float | None = None,
) -> db_models.Device:
    existing = db.scalar(select(db_models.Device).where(db_models.Device.name == name))
    if existing:
        if existing.resource_id != resource.id:
            existing.resource_id = resource.id
        if existing.status != status:
            existing.status = status
        if existing.numeric_value != numeric_value:
            existing.numeric_value = numeric_value
        return existing

    device = db_models.Device(
        name=name,
        type=device_type,
        status=status,
        resource_id=resource.id,
        numeric_value=numeric_value,
    )
    db.add(device)
    return device


def _ensure_permission(
    db: Session, user: db_models.User, resource: db_models.Resource
) -> None:
    exists = db.scalar(
        select(db_models.ResourcePermission)
        .where(db_models.ResourcePermission.user_id == user.id)
        .where(db_models.ResourcePermission.resource_id == resource.id)
    )
    if not exists:
        db.add(
            db_models.ResourcePermission(user_id=user.id, resource_id=resource.id)
        )
