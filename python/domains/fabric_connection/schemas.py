"""
Pydantic schemas for Fabric Connections.
File: domains/fabric_connection/schemas.py
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

class FabricConnectionIn(BaseModel):
    service_id: UUID
    connection_name: str
    connection_type: Optional[str] = None
    status: Optional[str] = None

class FabricConnectionUpdate(BaseModel):
    connection_name: Optional[str] = None
    connection_type: Optional[str] = None
    status: Optional[str] = None

class FabricConnectionOut(BaseModel):
    connection_id: UUID
    service_id: UUID
    connection_name: Optional[str]
    connection_type: Optional[str]
    status: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DeleteResponse(BaseModel):
    detail: str