"""
Pydantic schemas for the Devices domain.
File: app/python/domains/devices/schemas.py
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal

# ==========================================
# DEVICES
# ==========================================

class DeviceIn(BaseModel):
    device_name: str
    device_role: Optional[str] = None
    device_model: Optional[str] = None
    device_vendor: Optional[str] = None
    nos_version: Optional[str] = None    
    availability_zone: Optional[str] = None
    lifecycle_status: Optional[str] = "Active"
    planning_status: Optional[str] = "Planned"
    health_status: Optional[int] = 4
    network: Optional[str] = None
    location_id: Optional[UUID] = None
    location: Optional[str] = None
    floor: Optional[str] = None
    aisle: Optional[str] = None
    rack: Optional[str] = None
    device_description: Optional[str] = None

class DeviceUpdate(BaseModel):
    device_name: Optional[str] = None
    device_role: Optional[str] = None
    device_model: Optional[str] = None
    device_vendor: Optional[str] = None
    availability_zone: Optional[str] = None   
    lifecycle_status: Optional[str] = None
    planning_status: Optional[str] = None
    health_status: Optional[int] = None
    network: Optional[str] = None
    location: Optional[str] = None
    floor: Optional[str] = None
    aisle: Optional[str] = None
    rack: Optional[str] = None
    device_description: Optional[str] = None

class DeviceOut(BaseModel):
    device_id: UUID
    device_name: str
    device_role: Optional[str] = None
    device_model: Optional[str] = None
    device_vendor: Optional[str] = None
    availability_zone: Optional[str] = None
    lifecycle_status: Optional[str] = None      
    nos_version: Optional[str] = None   
    planning_status: Optional[str] = None
    health_status: Optional[int] = None
    network: Optional[str] = None
    floor: Optional[str] = None
    location: Optional[str] = None
    aisle: Optional[str] = None
    rack: Optional[str] = None
    location_id: Optional[UUID] = None
    device_description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class DeviceDetailsOut(BaseModel):
    device_id: UUID
    device_name: str
    device_role: str
    device_model: Optional[str] = None
    device_vendor: Optional[str] = None
    nos_version: Optional[str] = None
    network: Optional[str] = None
    location_id: Optional[UUID] = None
    location_code: Optional[str] = None
    location_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# DEVICE LOCATIONS
# ==========================================

class DeviceLocationIn(BaseModel):
    device_id: UUID
    rack_identifier: str = Field(..., max_length=20)
    location: str = Field(..., max_length=100)
    clli: Optional[str] = Field(None, max_length=8)
    floor_number: Optional[str] = None
    aisle_identifier: Optional[str] = None
    rack_start_ru: Optional[int] = None
    ru_height: Optional[int] = None
    description: Optional[str] = None

class DeviceLocationUpdate(BaseModel):
    clli: Optional[str] = None
    location: Optional[str] = None
    floor_number: Optional[str] = None
    rack_identifier: Optional[str] = None
    aisle_identifier: Optional[str] = None
    rack_start_ru: Optional[int] = None
    ru_height: Optional[int] = None
    description: Optional[str] = None

class DeviceLocationOut(DeviceLocationIn):
    date_added: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)