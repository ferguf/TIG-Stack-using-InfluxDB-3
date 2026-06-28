import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

# Centralized core DB 
from core.database import get_db

# Native relative imports from the domain slice
from . import operations
from .schemas import (
    FabricServiceDetailOut,
    FabricServiceOut,
    FabricServiceIn,
    FabricServiceUpdate,
    DeleteResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fabric_services", tags=["Fabric Services Domain"])

# -----------------------------
# READ Fabric Services
# -----------------------------
@router.get(
    "/",
    response_model=List[FabricServiceOut],
    summary="Get all fabric services"
)
def get_fabric_services(db: Session = Depends(get_db)):
    """Retrieve all fabric services in the system."""
    services = operations.get_fabric_services(db)
    return [FabricServiceOut.model_validate(s) for s in services]


@router.get(
    "/detail/{service_id}", 
    response_model=FabricServiceDetailOut,
    summary="Get full Fabric Service detail including nested connections"
)
def fetch_fabric_service_detail(service_id: UUID, db: Session = Depends(get_db)):
    """Retrieve the enriched dashboard view of a specific fabric service."""
    service = operations.get_fabric_service_detail(db, service_id)
    if not service:
        raise HTTPException(
            status_code=404,
            detail=f"Fabric Service {service_id} not found"
        )
    return FabricServiceDetailOut.model_validate(service)


@router.get(
    "/customer/{customer_id}", 
    response_model=List[FabricServiceOut],
    summary="Get services for a specific customer"
)
def get_fabric_services_for_customer(customer_id: UUID, db: Session = Depends(get_db)):
    """List all fabric services assigned to a specific customer UUID."""
    services = operations.get_fabric_services_by_customer(db, customer_id)
    return [FabricServiceOut.model_validate(s) for s in services]


@router.get(
    "/{service_id}", 
    response_model=FabricServiceOut,
    summary="Get a specific fabric service by ID"
)
def get_fabric_service_by_id(service_id: UUID, db: Session = Depends(get_db)):
    """Retrieve a single fabric service by its UUID."""
    service = operations.get_fabric_service_by_id(db, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Fabric Service not found")
    return FabricServiceOut.model_validate(service)


# -----------------------------
# CREATE Fabric Service
# -----------------------------
@router.post(
    "/",
    response_model=FabricServiceOut,
    summary="Create a new fabric service"
)
def post_fabric_service(data: FabricServiceIn, db: Session = Depends(get_db)):
    """Create a new fabric service in the system."""
    try:
        new_service = operations.post_fabric_service(db, data)
        return FabricServiceOut.model_validate(new_service)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------
# UPDATE Fabric Service
# -----------------------------
@router.put(
    "/{service_id}",
    response_model=FabricServiceOut,
    summary="Update an existing fabric service"
)
def update_fabric_service(
    service_id: UUID,
    data: FabricServiceUpdate,
    db: Session = Depends(get_db)
):
    """Update properties of an existing fabric service."""
    updated_service = operations.update_fabric_service(db, service_id, data)
    if not updated_service:
        raise HTTPException(status_code=404, detail="Fabric Service not found")
    return FabricServiceOut.model_validate(updated_service)
  

# -----------------------------
# DELETE Fabric Service
# -----------------------------
@router.delete(
    "/{service_id}",
    response_model=DeleteResponse,
    summary="Delete a fabric service by ID"
)
def delete_fabric_service(service_id: UUID, db: Session = Depends(get_db)):
    """Delete a fabric service by its UUID."""
    deleted = operations.delete_fabric_service(db, service_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Fabric Service not found")
    return DeleteResponse(detail=f"Fabric Service {service_id} deleted successfully")