from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

# --- Base Network Links ---

class NetworkLinkIn(BaseModel):
    endpoint_a: UUID = Field(..., description="UUID of the A-side endpoint (port or interface).")
    endpoint_a_type: str = Field(..., max_length=20, description="Type of A-side endpoint ('port' or 'interface').")
    endpoint_b: UUID = Field(..., description="UUID of the B-side endpoint.")
    endpoint_b_type: str = Field(..., max_length=20, description="Type of B-side endpoint ('port' or 'interface').")
    link_type: str = Field(..., max_length=30, description="Link type (e.g., 'port-to-port', 'interface-to-interface').")
    description: Optional[str] = Field(None, max_length=512)
    channel: Optional[int] = Field(None, ge=0, le=64, description="Channel ID (1–32) for ROP links.")
    frequency: Optional[Decimal] = Field(None, description="Frequency value for ROP links.")

class NetworkLinkUpdate(BaseModel):
    endpoint_a: Optional[UUID] = None
    endpoint_a_type: Optional[str] = None
    endpoint_b: Optional[UUID] = None
    endpoint_b_type: Optional[str] = None
    link_type: Optional[str] = None
    description: Optional[str] = None
    channel: Optional[int] = Field(None, ge=1, le=32)
    frequency: Optional[Decimal] = None

class NetworkLinkOut(NetworkLinkIn):
    link_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- ROP Channels ---

class ROPChannelMemberIn(BaseModel):
    rop_link_id: UUID = Field(..., description="The NetworkLink UUID of the parent ROP.")
    channel_id: int = Field(..., ge=0, le=64, description="The unique channel number within this ROP.")
    a_side_endpoint_id: UUID = Field(..., description="UUID of the A-side interface/port.")
    a_side_endpoint_type: str = Field(..., max_length=50) 
    z_side_endpoint_id: UUID = Field(..., description="UUID of the Z-side interface/port.")
    z_side_endpoint_type: str = Field(..., max_length=50) 
    description: Optional[str] = None

class ROPChannelMemberUpdate(BaseModel):
    rop_link_id: Optional[UUID] = None
    channel_id: Optional[int] = Field(None, ge=0, le=32)
    a_side_endpoint_id: Optional[UUID] = None
    a_side_endpoint_type: Optional[str] = None
    z_side_endpoint_id: Optional[UUID] = None
    z_side_endpoint_type: Optional[str] = None
    description: Optional[str] = None

class ROPChannelMemberOut(ROPChannelMemberIn):
    rop_member_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Views ---

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
    a_port_health_status: Optional[str]

    b_port_id: Optional[UUID]
    b_port_name: Optional[str]
    b_port_type: Optional[str]
    b_port_speed: Optional[str]
    b_port_health_status: Optional[str]
    
    device_id: Optional[UUID]
    device_name: Optional[str]
    device_role: Optional[str]
    device_vendor: Optional[str]
    device_location: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class VNetworkLinksDetailOut(BaseModel):
    link_id: UUID
    link_type: Optional[str]
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

    model_config = ConfigDict(from_attributes=True)