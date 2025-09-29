import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.models.db_models import (
    Base,
    User,
    UserRole,
    Resource,
    ResourceStatus,
    Device,
    DeviceType,
    ResourcePermission,
    DeviceCommand,
)
from app.services import reservation_service, device_commands


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite://", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, future=True)
    try:
        with SessionLocal() as session:
            yield session
            session.rollback()
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def _add_user(session, *, username="admin", role=UserRole.ADMIN) -> User:
    user = User(
        username=username,
        password_hash="hashed",
        role=role,
        is_active=True,
        full_name="Usuario Teste",
    )
    session.add(user)
    session.flush()
    return user


def _add_resource_with_device(session, *, name="Sala", device_type=DeviceType.LOCK) -> Resource:
    resource = Resource(
        name=name,
        description="Recurso teste",
        type="room",
        status=ResourceStatus.AVAILABLE,
    )
    session.add(resource)
    session.flush()

    device = Device(
        name=f"Dispositivo {name}",
        type=device_type,
        status="locked" if device_type == DeviceType.LOCK else "active",
        resource_id=resource.id,
    )
    session.add(device)
    session.flush()
    session.refresh(resource)
    return resource


def test_create_reservation_queues_unlock_command(db_session):
    admin = _add_user(db_session)
    resource = _add_resource_with_device(db_session)
    db_session.add(
        ResourcePermission(user_id=admin.id, resource_id=resource.id)
    )
    db_session.flush()

    reservation = reservation_service.create_reservation(
        db_session,
        resource=resource,
        user=admin,
        duration_minutes=30,
    )

    commands = db_session.scalars(select(DeviceCommand)).all()
    assert len(commands) == 1
    assert commands[0].action == "unlock"
    assert commands[0].consumed_at is None
    assert resource.status == ResourceStatus.RESERVED

    fetched = device_commands.fetch_next_command(db_session, resource.device.id)
    assert fetched is not None
    assert fetched.action == "unlock"
    assert fetched.consumed_at is not None

    # No second command pending yet.
    assert device_commands.fetch_next_command(db_session, resource.device.id) is None

    updated = reservation_service.release_reservation(
        db_session,
        reservation=reservation,
        by_user=admin,
        notes=None,
        force=True,
    )

    assert updated.status in {reservation_service.ReservationStatus.COMPLETED}
    pending = db_session.scalars(select(DeviceCommand).where(DeviceCommand.consumed_at.is_(None))).all()
    assert any(cmd.action == "lock" for cmd in pending)
    lock_command = device_commands.fetch_next_command(db_session, resource.device.id)
    assert lock_command is not None
    assert lock_command.action == "lock"
    assert resource.status == ResourceStatus.AVAILABLE


def test_unauthorized_user_cannot_manage_resource(db_session):
    user = _add_user(db_session, username="user", role=UserRole.USER)
    resource = _add_resource_with_device(db_session)

    with pytest.raises(HTTPException):
        reservation_service.ensure_user_can_manage_resource(user, resource)

    db_session.add(ResourcePermission(user_id=user.id, resource_id=resource.id))
    db_session.flush()
    # should not raise now
    reservation_service.ensure_user_can_manage_resource(user, resource)


