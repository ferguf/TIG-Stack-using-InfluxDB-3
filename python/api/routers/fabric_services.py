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
from scripts.api_model import FabricService
import scripts.api_operation as api_operation
from scripts.api_schema import (
    FabricServiceDetailOut,
    FabricServiceOut,
    FabricServiceIn,
    FabricServiceUpdate,
    DeleteResponse,
)

router = APIRouter(prefix="/fabric_services", tags=["Fabric Services"])

# -----------------------------
# READ Fabric Services
# -----------------------------
@router.get(
    "/",
    response_model=List[FabricServiceOut],
    summary="Get all fabric services"
)
def get_fabric_services(db: Session = Depends(get_db)):
    """
    Retrieve all fabric services in the system.
    - **returns**: Array of fabric service objects
    - **example**: 
      ```
      GET /fabric_services/
      → [
        {"service_id":"uuid","name":"ServiceA","description":"Core fabric service"},
        {"service_id":"uuid","name":"ServiceB","description":"Edge fabric service"}
      ]
      ```
    """
    services = api_operation.get_fabric_services(db)
    return [FabricServiceOut.model_validate(s) for s in services]


@router.get("/detail/{service_id}", response_model=FabricServiceDetailOut,
            summary="Get full Fabric Service detail including nested connections")
def fetch_fabric_service_detail(service_id: UUID, db: Session = Depends(get_db)):
    service = api_operation.get_fabric_service_detail(db, service_id)

    if not service:
        raise HTTPException(
            status_code=404,
            detail=f"Fabric Service {service_id} not found"
        )

    return service


@router.get("/customer/{customer_id}", response_model=List[FabricServiceOut])
def get_fabric_services_for_customer(customer_id: str, db: Session = Depends(get_db)):
    """
    API endpoint to list all fabric services for a given customer.
    """
    services = api_operation.get_fabric_services_by_customer(db, customer_id)
    return [FabricServiceOut.model_validate(s) for s in services]

@router.get("/{service_id}", response_model=List[FabricServiceOut])
def get_fabric_services_for_customer(service_id: str, db: Session = Depends(get_db)):
    """
    API endpoint to list all fabric services for a given customer.
    """
    services = api_operation.get_fabric_services_by_service(db, service_id)
    return [FabricServiceOut.model_validate(s) for s in services]

# -----------------------------
# CREATE Fabric Service
# -----------------------------
@router.post(
    "/",
    response_model=FabricServiceOut,
    summary="Create a new fabric service"
)
def post_fabric_service(data: FabricServiceIn, db: Session = Depends(get_db)):
    """
    Create a new fabric service in the system.
    - **data**: Request body containing the fabric service details
    - **returns**: Newly created fabric service object
    - **example**:
      ```
      POST /fabric_services/
      {
        "name": "ServiceA",
        "description": "Core fabric service"
      }
      → {"service_id":"uuid","name":"ServiceA","description":"Core fabric service"}
      ```
    """
    new_service = api_operation.post_fabric_service(db, data)
    return FabricServiceOut.model_validate(new_service)

# -----------------------------
# UPDATE Fabric Service
# -----------------------------
# @router.put(
#     "/{service_id}",
#     response_model=FabricServiceOut,
#     summary="Update an existing fabric service"
# )

@router.put("/{service_id}")
def update_fabric_service(
    service_id: UUID,
    data: FabricServiceUpdate,
    db: Session = Depends(get_db)
):
    updated_service = api_operation.update_fabric_service(db, service_id, data)
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
    """
    Delete a fabric service by its UUID.
    - **service_id**: Path parameter for the fabric service UUID
    - **returns**: Success message if deleted
    - **example**:
      ```
      DELETE /fabric_services/123e4567-e89b-12d3-a456-426614174000
      → {"detail":"FabricPort 123e4567-e89b-12d3-a456-426614174000 deleted successfully"}
      ```
    """
    deleted = api_operation.delete_fabric_service(db, service_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="FabricPort not found")
    return DeleteResponse(detail=f"FabricPort {service_id} deleted successfully")