"""
Pydantic schemas for the Ports domain.
File: domains/ports/schemas.py

Defines the strict API contracts for validating incoming requests 
and serializing outgoing responses for network Ports.
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class PortIn(BaseModel):
    """Schema for creating a new port record via POST."""
    port_id: Optional[UUID] = Field(None, description="Optional UUID; DB will generate if omitted")
    mac_address: Optional[str] = Field(None, description="MAC address of the port")
    port_name: str = Field(..., description="Name of the port (e.g., ae0, gig-1/0/1)")
    port_speed: str = Field(..., description="Speed of the port (e.g., 10G, 100G, 400G)")
    device_id: UUID = Field(..., description="UUID of the associated device")
    port_description: Optional[str] = Field(None, description="Description of the port")
    port_optic: Optional[str] = Field(None, description="Optic type (e.g., 400G-LR4)")
    port_tagging: Optional[str] = Field(None, description="Tagging mode (Untagged, Tagged)")
    port_cktid: Optional[str] = Field(None, description="Circuit ID associated with the port")
    customer_id: Optional[UUID] = Field(None, description="UUID of the associated customer")
    port_service_status: str = Field(..., description="Service status (Available, Assigned, etc.)")
    port_type: str = Field(..., description="Type of port (Physical, LAG, UNI, ENNI)")
    port_health_status: Optional[int] = Field(4, description="Health status code")
    admin_status: Optional[str] = Field("up", description="Administrative status")
    oper_status: Optional[str] = Field("down", description="Operational status")

class PortUpdate(BaseModel):
    """Schema for updating an existing port record via PUT/PATCH."""
    mac_address: Optional[str] = None
    port_name: Optional[str] = None
    port_speed: Optional[str] = None
    device_id: Optional[UUID] = None
    port_description: Optional[str] = None
    port_optic: Optional[str] = None
    port_tagging: Optional[str] = None
    port_cktid: Optional[str] = None
    customer_id: Optional[UUID] = None
    port_service_status: Optional[str] = None
    port_type: Optional[str] = None
    port_health_status: Optional[int] = None
    admin_status: Optional[str] = None
    oper_status: Optional[str] = None

class PortOut(BaseModel):
    """Standard schema for returning port details to the client."""
    port_id: UUID 
    mac_address: Optional[str] = None
    port_name: str
    port_speed: str
    device_id: UUID
    port_description: Optional[str] = None
    port_optic: Optional[str] = None
    port_tagging: Optional[str] = None
    port_cktid: Optional[str] = None
    customer_id: Optional[UUID] = None 
    port_service_status: str
    port_type: str
    port_health_status: Optional[int] = None
    admin_status: str
    oper_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) 

class DevicePortOut(BaseModel):
    """
    Schema representing the VDevicePorts view.
    Provides pre-joined device and port telemetry for the UI.
    """
    device_id: UUID = Field(..., description="Unique UUID identifier for the device")
    device_name: Optional[str] = Field(None, description="Name of the device")
    device_health_status: Optional[int] = Field(None, description="Health status of the device")
    availability_zone: Optional[str] = Field(None, description="Availability zone where the device resides")

    port_id: UUID = Field(..., description="Unique UUID identifier for the port")
    port_name: Optional[str] = Field(None, description="Name of the port")
    port_speed: Optional[str] = Field(None, description="Speed of the port (e.g., 1G, 10G)")
    port_type: Optional[str] = Field(None, description="Type of the port (e.g., Ethernet, Fiber)")
    port_service_status: Optional[str] = Field(None, description="Service status of the port")
    port_health_status: Optional[int] = Field(None, description="Health status of the port")

    admin_status: Optional[str] = None   
    oper_status: Optional[str] = None   

    mac_address: Optional[str] = Field(None, description="MAC address associated with the port")
    port_optic: Optional[str] = Field(None, description="Optic type used on the port")
    port_tagging: Optional[str] = Field(None, description="Tagging information for the port")
    port_cktid: Optional[str] = Field(None, description="Circuit ID associated with the port")

    lag_parent_id: Optional[UUID] = Field(None, description="UUID of the parent LAG if applicable")
    customer_id: Optional[UUID] = Field(None, description="UUID of the associated customer if applicable")

    port_created_at: Optional[datetime] = Field(None, description="Timestamp when the port record was created")
    port_updated_at: Optional[datetime] = Field(None, description="Timestamp when the port record was last updated")

    model_config = ConfigDict(from_attributes=True)