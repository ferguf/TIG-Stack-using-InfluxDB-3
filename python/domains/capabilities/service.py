# domains/capabilities/service.py

from sqlalchemy.orm import Session
from sqlalchemy import text, select
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from uuid import UUID

from .models import RefService, HardwareProfile, ProfileService, RefSpeed
from .schemas import (
    RefServiceCreate, 
    RefServiceResponse, 
    HardwareProfileCreate, 
    HardwareProfileResponse,
    ProfileServiceAssign, 
    ProfileServiceResponse,
    LocationCapabilitiesResponse
)

def fetch_location_aggregate(db: Session, location_id: UUID) -> Optional[LocationCapabilitiesResponse]:
    """
    Executes a query against the vw_capabilities_location view to retrieve
    the dynamically aggregated service and port capabilities for a specific site.
    """
    query = text("""
        SELECT 
            location_id,
            deployed_hardware,
            location_supported_ports,
            location_supported_services
        FROM vw_capabilities_location
        WHERE location_id = :loc_id
    """)
    
    result = db.execute(query, {"loc_id": location_id})
    row = result.fetchone()
    
    if not row:
        return None
        
    return LocationCapabilitiesResponse(
        location_id=row.location_id,
        deployed_hardware=row.deployed_hardware,
        location_supported_ports=row.location_supported_ports,
        location_supported_services=row.location_supported_services
    )

def create_ref_service(db: Session, obj_in: RefServiceCreate) -> RefService:
    """
    Creates a new Master Template service (e.g., E-Line EVPL).
    """
    db_obj = RefService(
        service_name=obj_in.service_name,
        layer=obj_in.layer
    )
    db.add(db_obj)
    try:
        db.commit()
        db.refresh(db_obj)
        return db_obj
    except IntegrityError:
        db.rollback()
        raise ValueError(f"Service '{obj_in.service_name}' already exists.")

def get_all_ref_services(db: Session) -> List[RefService]:
    """
    Retrieves the complete 100% universe of defined services.
    """
    query = select(RefService).order_by(RefService.service_name)
    result = db.execute(query)
    return result.scalars().all()

def update_ref_service(db: Session, service_id: UUID, obj_in: RefServiceCreate) -> Optional[RefService]:
    """
    Updates an existing Master Template service.
    """
    db_obj = db.get(RefService, service_id)
    if not db_obj:
        return None
        
    db_obj.service_name = obj_in.service_name
    db_obj.layer = obj_in.layer
    
    try:
        db.commit()
        db.refresh(db_obj)
        return db_obj
    except IntegrityError:
        db.rollback()
        raise ValueError(f"Service name '{obj_in.service_name}' is already in use.")

def delete_ref_service(db: Session, service_id: UUID) -> bool:
    """
    Deletes a Master Template service.
    """
    db_obj = db.get(RefService, service_id)
    if not db_obj:
        return False
        
    db.delete(db_obj)
    db.commit()
    return True

def create_hardware_profile(db: Session, obj_in: HardwareProfileCreate) -> HardwareProfile:
    """
    Creates the anchor profile for a Role/Model combination.
    """
    db_obj = HardwareProfile(
        device_role=obj_in.device_role,
        device_model=obj_in.device_model
    )
    db.add(db_obj)
    try:
        db.commit()
        db.refresh(db_obj)
        return db_obj
    except IntegrityError:
        db.rollback()
        raise ValueError(f"Profile for {obj_in.device_role} {obj_in.device_model} already exists.")

def assign_service_to_profile(db: Session, profile_id: UUID, obj_in: ProfileServiceAssign) -> ProfileService:
    """
    Maps a Master Service and Master Speed to a specific Hardware Profile.
    """
    db_obj = ProfileService(
        profile_id=profile_id,
        service_id=obj_in.service_id,
        speed_id=obj_in.speed_id
    )
    db.add(db_obj)
    try:
        db.commit()
        db.refresh(db_obj)
        return db_obj
    except IntegrityError:
        db.rollback()
        raise ValueError("This specific service and speed combination is already mapped to this profile.")