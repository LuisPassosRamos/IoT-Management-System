from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    id: int
    username: str
    password: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    role: str
    username: str
    user_id: int


class DeviceBase(BaseModel):
    name: str
    type: str
    status: str = Field(default="inactive")
    resource_id: Optional[int] = None
    value: Optional[float] = None


class Device(DeviceBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    resource_id: Optional[int] = None
    value: Optional[float] = None


class ResourceBase(BaseModel):
    name: str
    description: str
    device_id: Optional[int] = None


class Resource(ResourceBase):
    id: int
    available: bool
    reserved_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class ResourceCreate(ResourceBase):
    available: bool = Field(default=True)
    reserved_by: Optional[int] = None


class ResourceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    available: Optional[bool] = None
    reserved_by: Optional[int] = None
    device_id: Optional[int] = None


class Reservation(BaseModel):
    id: int
    resource_id: int
    user_id: int
    timestamp: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class ReservationCreate(BaseModel):
    user_id: Optional[int] = None


class ReservationUpdate(BaseModel):
    status: Optional[str] = None


class ReservationSummary(Reservation):
    resource_name: Optional[str] = None
    username: Optional[str] = None


class DeviceAction(BaseModel):
    action: str
