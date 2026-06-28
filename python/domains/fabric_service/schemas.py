"""
Pydantic schemas for the Fabric Services domain.
File: domains/fabric_service/schemas.py
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class FabricServiceIn(BaseModel):
    """Schema for creating a new fabric service record via POST."""
    customer_id: UUID
    service_name: str
    service_alias: str
    service_type: str
    service_description: Optional[str] = None
    route_target: Optional[str] = None
    health_status: int = 4


class FabricServiceUpdate(BaseModel):
    """Schema for updating an existing fabric service record via PUT/PATCH."""
    service_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    service_name: Optional[str] = None
    service_alias: Optional[str] = None
    service_description: Optional[str] = None
    service_type: Optional[str] = None
    route_target: Optional[str] = None
    health_status: Optional[int] = None


class FabricServiceOut(BaseModel):
    """Standard schema for returning fabric service details to the client."""
    service_id: UUID
    customer_id: Optional[UUID]
    service_name: Optional[str]
    service_alias: Optional[str]
    service_type: Optional[str]
    service_description: Optional[str] = None
    route_target: Optional[str] = None
    health_status: int
    created_at: datetime
    updated_at: datetime
    service_count: int = 0

    model_config = ConfigDict(from_attributes=True) 


class FabricServiceDetailOut(BaseModel):
    """
    Schema representing the VFabricServiceDetail view.
    Provides pre-joined service telemetry for the UI.
    """
    service_id: UUID
    customer_id: UUID
    customer_name: str
    account_id: str

    service_name: str
    service_alias: str
    service_type: str
    service_description: str

    route_target: Optional[str] = None
    health_status: int
    
    created_at: datetime
    updated_at: datetime

    # Nested objects from the DB View
    fabric_connections: List[Dict[str, Any]] = []
    fabric_ports: List[Dict[str, Any]] = []
    fabric_interfaces: List[Dict[str, Any]] = []
    cloud_interconnects: List[Dict[str, Any]] = []

    model_config = ConfigDict(from_attributes=True)


class DeleteResponse(BaseModel):
    """Standardized response schema for successful DELETE operations."""
    detail: str