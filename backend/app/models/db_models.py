from __future__ import annotations

import enum
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import (
    String,
    Text,
    Integer,
    Float,
    DateTime,
    Boolean,
    Enum as SqlEnum,
    ForeignKey,
    UniqueConstraint,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserRole(str, enum.Enum):
    """Supported user roles."""

    ADMIN = "admin"
    USER = "user"


class ResourceStatus(str, enum.Enum):
    """Resource availability status."""

    AVAILABLE = "available"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"


class ReservationStatus(str, enum.Enum):
    """Lifecycle of a reservation."""

    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class DeviceType(str, enum.Enum):
    """Supported device types."""

    LOCK = "lock"
    SENSOR = "sensor"
    CAMERA = "camera"
    OTHER = "other"


class User(Base):
    """System user with role-based access control."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole), default=UserRole.USER, nullable=False
    )
    full_name: Mapped[Optional[str]] = mapped_column(String(120))
    email: Mapped[Optional[str]] = mapped_column(String(120), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), default=func.now()
    )

    reservations: Mapped[List["Reservation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    permissions: Mapped[List["ResourcePermission"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(back_populates="user")


class Resource(Base):
    """Resource managed by the IoT system."""

    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(50), default="generic")
    location: Mapped[Optional[str]] = mapped_column(String(120))
    capacity: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[ResourceStatus] = mapped_column(
        SqlEnum(ResourceStatus), default=ResourceStatus.AVAILABLE, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), default=func.now()
    )

    device: Mapped[Optional["Device"]] = relationship(
        back_populates="resource", uselist=False
    )
    reservations: Mapped[List["Reservation"]] = relationship(
        back_populates="resource", cascade="all, delete-orphan"
    )
    permitted_users: Mapped[List["ResourcePermission"]] = relationship(
        back_populates="resource", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(back_populates="resource")


class Device(Base):
    """IoT devices associated with resources."""

    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[DeviceType] = mapped_column(SqlEnum(DeviceType), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="inactive")
    numeric_value: Mapped[Optional[float]] = mapped_column(Float)
    text_value: Mapped[Optional[str]] = mapped_column(String(255))
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON)
    last_reported_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    resource_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("resources.id", ondelete="SET NULL"), unique=True
    )

    resource: Mapped[Optional[Resource]] = relationship(back_populates="device")
    audit_logs: Mapped[List["AuditLog"]] = relationship(back_populates="device")


class Reservation(Base):
    """Reservation for resource usage."""

    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    resource_id: Mapped[int] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[ReservationStatus] = mapped_column(
        SqlEnum(ReservationStatus), default=ReservationStatus.ACTIVE, nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text)
    released_by_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    resource: Mapped[Resource] = relationship(back_populates="reservations")
    user: Mapped[User] = relationship(back_populates="reservations")
    audit_logs: Mapped[List["AuditLog"]] = relationship(back_populates="reservation")


class ResourcePermission(Base):
    """Association table for user permissions over resources."""

    __tablename__ = "resource_permissions"

    __table_args__ = (UniqueConstraint("user_id", "resource_id", name="uix_user_resource"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    resource_id: Mapped[int] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="permissions")
    resource: Mapped[Resource] = relationship(back_populates="permitted_users")


class AuditLog(Base):
    """Audit log capturing key actions."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_id: Mapped[Optional[int]] = mapped_column(ForeignKey("resources.id"))
    device_id: Mapped[Optional[int]] = mapped_column(ForeignKey("devices.id"))
    reservation_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("reservations.id")
    )
    result: Mapped[str] = mapped_column(String(20), default="success")
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    user: Mapped[Optional[User]] = relationship(back_populates="audit_logs")
    resource: Mapped[Optional[Resource]] = relationship(back_populates="audit_logs")
    device: Mapped[Optional[Device]] = relationship(back_populates="audit_logs")
    reservation: Mapped[Optional[Reservation]] = relationship(
        back_populates="audit_logs"
    )
