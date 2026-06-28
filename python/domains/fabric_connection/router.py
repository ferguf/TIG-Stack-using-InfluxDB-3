"""
HTTP Router for Fabric Connections.
File: domains/fabric_connection/routers.py
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from core.database import get_db
from . import operations
from .schemas import (
    FabricConnectionOut,
    FabricConnectionIn,
    FabricConnectionUpdate,
    DeleteResponse
)

router = APIRouter(prefix="/fabric_connections", tags=["Fabric Connections Domain"])

@router.get("/", response_model=List[FabricConnectionOut])
def get_all(db: Session = Depends(get_db)):
    return [FabricConnectionOut.model_validate(c) for c in operations.get_fabric_connections(db)]

@router.get("/service/{service_id}", response_model=List[FabricConnectionOut])
def get_by_service(service_id: UUID, db: Session = Depends(get_db)):
    connections = operations.get_fabric_connections_by_service_id(db, str(service_id))
    return [FabricConnectionOut.model_validate(c) for c in connections]

@router.post("/", response_model=FabricConnectionOut)
def create(data: FabricConnectionIn, db: Session = Depends(get_db)):
    return FabricConnectionOut.model_validate(operations.post_fabric_connection(db, data))

@router.put("/{connection_id}", response_model=FabricConnectionOut)
def update(connection_id: UUID, data: FabricConnectionUpdate, db: Session = Depends(get_db)):
    updated = operations.update_fabric_connection(db, str(connection_id), data)
    if not updated:
        raise HTTPException(status_code=404, detail="Connection not found")
    return FabricConnectionOut.model_validate(updated)

@router.delete("/{connection_id}", response_model=DeleteResponse)
def delete(connection_id: UUID, db: Session = Depends(get_db)):
    if not operations.delete_fabric_connection(db, str(connection_id)):
        raise HTTPException(status_code=404, detail="Connection not found")
    return DeleteResponse(detail="Deleted successfully")