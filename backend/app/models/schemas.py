from typing import Optional, List
from pydantic import BaseModel


class User(BaseModel):
    id: int
    username: str
    password: str
    role: str


class Device(BaseModel):
    id: int
    name: str
    type: str
    status: str
    resource_id: Optional[int] = None
    value: Optional[float] = None


class Resource(BaseModel):
    id: int
    name: str
    description: str
    available: bool
    reserved_by: Optional[int] = None
    device_id: Optional[int] = None


class Reservation(BaseModel):
    id: int
    resource_id: int
    user_id: int
    timestamp: str
    status: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    role: str
    username: str


class DeviceAction(BaseModel):
    action: str


class ReservationRequest(BaseModel):
    user_id: int