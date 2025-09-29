from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    role: str
    username: str
    user_id: int
    full_name: Optional[str] = None


class UserBase(BaseModel):
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: str = Field(default="user")
    is_active: bool = Field(default=True)


class UserCreate(UserBase):
    password: str = Field(min_length=6)
    allowed_resource_ids: Optional[List[int]] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=6)
    allowed_resource_ids: Optional[List[int]] = None


class UserSummary(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    permitted_resource_ids: List[int] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class DeviceBase(BaseModel):
    name: str
    type: str
    status: Optional[str] = Field(default="inactive")
    resource_id: Optional[int] = None
    numeric_value: Optional[float] = None
    text_value: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    resource_id: Optional[int] = None
    numeric_value: Optional[float] = None
    text_value: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DeviceResponse(DeviceBase):
    id: int
    last_reported_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DeviceActionRequest(BaseModel):
    action: str
    payload: Optional[Dict[str, Any]] = None


class DeviceStatusReport(BaseModel):
    device_id: int
    status: str
    numeric_value: Optional[float] = None
    text_value: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ResourceBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: str = Field(default="generic")
    location: Optional[str] = None
    capacity: Optional[int] = None


class ResourceCreate(ResourceBase):
    status: Optional[str] = Field(default="available")
    device_id: Optional[int] = None


class ResourceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None
    capacity: Optional[int] = None
    status: Optional[str] = None
    device_id: Optional[int] = None


class ResourceResponse(ResourceBase):
    id: int
    status: str
    current_reservation_id: Optional[int] = None
    reserved_by_user: Optional[str] = None
    device: Optional[DeviceResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ReservationBase(BaseModel):
    resource_id: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    notes: Optional[str] = None


class ReservationCreate(BaseModel):
    duration_minutes: int = Field(default=30, ge=5, le=480)
    start_time: Optional[datetime] = None
    user_id: Optional[int] = None
    notes: Optional[str] = None


class ReservationRelease(BaseModel):
    notes: Optional[str] = None
    force: bool = Field(default=False)


class ReservationResponse(BaseModel):
    id: int
    resource_id: int
    user_id: int
    start_time: datetime
    end_time: Optional[datetime]
    expires_at: datetime
    status: str
    notes: Optional[str] = None
    released_by_admin: bool
    resource_name: Optional[str] = None
    username: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ReservationFilter(BaseModel):
    resource_id: Optional[int] = None
    user_id: Optional[int] = None
    status: Optional[str] = None
    start_from: Optional[datetime] = None
    start_to: Optional[datetime] = None


class AuditLogEntry(BaseModel):
    id: int
    timestamp: datetime
    user_id: Optional[int]
    action: str
    resource_id: Optional[int]
    device_id: Optional[int]
    reservation_id: Optional[int]
    result: str
    details: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class StatsReservationSummary(BaseModel):
    total_reservations: int
    active_reservations: int
    average_duration_minutes: float


class ResourceUsageEntry(BaseModel):
    resource_id: int
    resource_name: str
    total_reservations: int
    total_minutes: float


class StatsResponse(BaseModel):
    reservations: StatsReservationSummary
    top_resources: List[ResourceUsageEntry]
    usage_by_day: Dict[str, int]


class ExportResponse(BaseModel):
    filename: str
    content_type: str
    content: bytes


class PermissionUpdateRequest(BaseModel):
    resource_ids: List[int]
