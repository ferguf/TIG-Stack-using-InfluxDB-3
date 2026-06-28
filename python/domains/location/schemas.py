from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class LocationBase(BaseModel):
    location_code: str
    short_name: Optional[str] = None
    location_name: str
    city: str
    state: str
    country: str
    address: Optional[str] = None
    postal_code: Optional[str] = None
    timezone_name: Optional[str] = None
    timezone_offset: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    availability_zone: Optional[str] = None

class LocationIn(LocationBase): pass

class LocationUpdate(BaseModel):
    location_code: Optional[str] = None
    short_name: Optional[str] = None
    location_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    # ... add other optional fields as needed

class LocationOut(LocationBase):
    location_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DeviceLocationIn(BaseModel):
    device_id: UUID
    rack_identifier: str = Field(..., max_length=20)
    location: str = Field(..., max_length=100)
    clli: Optional[str] = None
    floor_number: Optional[str] = None
    rack_start_ru: Optional[int] = None
    ru_height: Optional[int] = None

class DeviceLocationOut(DeviceLocationIn):
    date_added: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)
    
class NetworkLocationOut(BaseModel):
    network: str
    location_id: UUID
    location_code: str
    short_name: str | None
    location_name: str
    city: str
    state: str
    country: str

    class Config:
        orm_mode = True

class VNetworkLinksLAGOut(BaseModel):
    link_id: UUID
    link_type: Optional[str]
    description: Optional[str]
    channel: Optional[int]
    frequency: Optional[Decimal]

    created_at: datetime
    updated_at: datetime

    a_port_id: Optional[UUID]
    a_port_name: Optional[str]
    a_port_type: Optional[str]
    a_port_speed: Optional[str]
    a_port_health_status: Optional[int]

    b_port_id: Optional[UUID]
    b_port_name: Optional[str]
    b_port_type: Optional[str]
    b_port_speed: Optional[str]
    b_port_health_status: Optional[int]
    
    device_id: Optional[UUID]
    device_name: Optional[str]
    device_role: Optional[str]
    device_vendor: Optional[str]
    device_location: Optional[str]

    class Config:
        from_attributes = True

class VNetworkLinksDetailOut(BaseModel):
    link_id: UUID
    link_type: str
    description: Optional[str]
    channel: Optional[int]
    frequency: Optional[int]
    created_at: datetime
    updated_at: datetime
    link_health_status: Optional[int]

    a_port_id: Optional[UUID]
    a_port_name: Optional[str]
    a_port_speed: Optional[str]
    a_port_type: Optional[str]
    a_port_service_status: Optional[str]
    a_port_health_status: Optional[int]

    a_device_id: Optional[UUID]
    a_device_name: Optional[str]
    a_device_role: Optional[str]
    a_device_vendor: Optional[str]
    a_device_location: Optional[str]
    a_device_health_status: Optional[int]
    a_device_latitude: Optional[float]
    a_device_longitude: Optional[float]

    b_port_id: Optional[UUID]
    b_port_name: Optional[str]
    b_port_speed: Optional[str]
    b_port_type: Optional[str]
    b_port_service_status: Optional[str]
    b_port_health_status: Optional[int]

    b_device_id: Optional[UUID]
    b_device_name: Optional[str]
    b_device_role: Optional[str]
    b_device_vendor: Optional[str]
    b_device_location: Optional[str]
    b_device_health_status: Optional[int]
    b_device_latitude: Optional[float]
    b_device_longitude: Optional[float]

    a_network: Optional[str]
    b_network: Optional[str]

    class Config:
        orm_mode = True


