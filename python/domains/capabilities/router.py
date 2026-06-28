# domains/capabilities/router.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

# Import the correct FastAPI dependency generator
from core.database import get_db 

from .schemas import (
    RefServiceCreate, RefServiceResponse, 
    HardwareProfileCreate, HardwareProfileResponse,
    ProfileServiceAssign, ProfileServiceResponse, LocationCapabilitiesResponse
)
from .service import (
    create_ref_service, fetch_location_aggregate, get_all_ref_services,
    create_hardware_profile, assign_service_to_profile,
    update_ref_service, delete_ref_service  # Ensure these are added to service.py
)

router = APIRouter(
    prefix="/api/v1/capabilities",
    tags=["Capabilities Matrix"]
)

@router.get(
    "/location/{location_id}", 
    response_model=LocationCapabilitiesResponse,
    status_code=status.HTTP_200_OK
)
def get_location_capabilities(
    location_id: UUID, 
    db: Session = Depends(get_db) 
):
    try:
        capabilities = fetch_location_aggregate(db, location_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Database aggregation failed: {str(e)}"
        )
        
    if not capabilities:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Capabilities not found. This location may not exist or has no deployed hardware profiles."
        )
        
    return capabilities

# --- Master Reference CRUD ---

@router.get("/reference/services", response_model=List[RefServiceResponse])
def api_get_all_ref_services(db: Session = Depends(get_db)):
    return get_all_ref_services(db)

@router.post("/reference/services", response_model=RefServiceResponse, status_code=status.HTTP_201_CREATED)
def api_create_ref_service(
    service_in: RefServiceCreate, 
    db: Session = Depends(get_db)
):
    try:
        return create_ref_service(db, service_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/reference/services/{service_id}", response_model=RefServiceResponse, status_code=status.HTTP_200_OK)
def api_update_ref_service(
    service_id: UUID,
    service_in: RefServiceCreate,
    db: Session = Depends(get_db)
):
    try:
        updated_service = update_ref_service(db, service_id, service_in)
        if not updated_service:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found.")
        return updated_service
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/reference/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def api_delete_ref_service(
    service_id: UUID,
    db: Session = Depends(get_db)
):
    success = delete_ref_service(db, service_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found.")
    return None

# --- Hardware Profile CRUD ---

@router.post("/profiles", response_model=HardwareProfileResponse, status_code=status.HTTP_201_CREATED)
def api_create_hardware_profile(
    profile_in: HardwareProfileCreate, 
    db: Session = Depends(get_db)
):
    try:
        return create_hardware_profile(db, profile_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/profiles/{profile_id}/services", response_model=ProfileServiceResponse, status_code=status.HTTP_201_CREATED)
def api_assign_service(
    profile_id: UUID,
    assignment_in: ProfileServiceAssign,
    db: Session = Depends(get_db)
):
    try:
        return assign_service_to_profile(db, profile_id, assignment_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))