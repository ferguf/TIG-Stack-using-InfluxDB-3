from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import sys, os

# Ensure scripts directory is on path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(BASE_DIR, "..", "..", "scripts")
sys.path.append(SCRIPTS_DIR)

import uuid as uuid
from uuid import UUID
from scripts.api_session import get_db
from scripts.api_model import FabricConnection
import scripts.api_operation as api_operation
from scripts.api_schema import (
    FabricConnectionOut,
    FabricConnectionIn,
    FabricConnectionUpdate,
    DeleteResponse,
)

router = APIRouter(
    prefix="/fabric_connections",
    tags=["fabric_connections"],
)

@router.get("/", response_model=List[FabricConnectionOut])
def get_fabric_connections(db: Session = Depends(get_db)):
    connections = api_operation.get_fabric_connections(db)
    return [FabricConnectionOut.model_validate(c) for c in connections]

@router.get("/service/{service_id}", response_model=List[FabricConnectionOut])
def get_fabric_connections_by_service_id(service_id: str, db: Session = Depends(get_db)):
    # SWAP THESE: Pass db first, then service_id
    connections = api_operation.get_fabric_connections_by_service_id(db, service_id)
    return [FabricConnectionOut.model_validate(c) for c in connections] 


@router.post("/", response_model=FabricConnectionOut)
def post_fabric_connection(data: FabricConnectionIn, db: Session = Depends(get_db)):
    new_connection = api_operation.post_fabric_connection(db, data)
    return FabricConnectionOut.model_validate(new_connection)  # <-- convert ORM to Pydantic

@router.put("/{connection_id}", response_model=FabricConnectionOut)
def update_fabric_connection(
    connection_id: UUID,
    data: FabricConnectionUpdate,   # <-- use an update schema
    db: Session = Depends(get_db)
):
    updated_connection = api_operation.update_fabric_connection(db, connection_id, data)
    return FabricConnectionOut.model_validate(updated_connection)

@router.delete("/{connection_id}", response_model=DeleteResponse)
def delete_fabric_connection(
    connection_id: UUID,
    db: Session = Depends(get_db)
):
    deleted = api_operation.delete_fabric_connection(db, connection_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="FabricConnection not found")
    return DeleteResponse(detail=f"FabricConnection {connection_id} deleted successfully")