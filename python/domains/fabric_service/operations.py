"""
Business logic / operations layer for the Fabric Services domain.
File: domains/fabric_service/operations.py
"""
import logging
import uuid
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

# Local domain imports
from .models import FabricService, FabricServiceDetail
from .schemas import FabricServiceIn, FabricServiceUpdate

logger = logging.getLogger(__name__)


def get_fabric_services(db: Session) -> List[FabricService]:
    """
    Fetches all fabric service records from the primary database table.
    """
    return db.query(FabricService).all()


def get_fabric_service_detail(db: Session, service_id: UUID) -> Optional[FabricServiceDetail]:
    """
    Fetches the enriched view of a fabric service including its nested topology elements.
    """
    return db.query(FabricServiceDetail).filter(FabricServiceDetail.service_id == service_id).first()


def get_fabric_service_by_id(db: Session, service_id: UUID) -> Optional[FabricService]:
    """
    Fetches a single raw fabric service record by UUID.
    """
    return db.query(FabricService).filter(FabricService.service_id == service_id).first()


def get_fabric_services_by_customer(db: Session, customer_id: UUID) -> List[FabricService]:
    """
    Fetches all fabric services associated with a specific customer UUID.
    """
    return db.query(FabricService).filter(FabricService.customer_id == customer_id).all()


def post_fabric_service(db: Session, data: FabricServiceIn) -> FabricService:
    """
    Creates a new fabric service.
    """
    try:
        service_data = data.model_dump(exclude_unset=True)
        service_data["service_id"] = uuid.uuid4()
        
        new_service = FabricService(**service_data)
        db.add(new_service)
        db.commit()
        db.refresh(new_service)
        return new_service
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating fabric service: {e}")
        raise e


def update_fabric_service(db: Session, service_id: UUID, data: FabricServiceUpdate) -> Optional[FabricService]:
    """
    Updates an existing fabric service's properties.
    """
    try:
        service = db.query(FabricService).filter(FabricService.service_id == service_id).first()
        if not service:
            return None
            
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(service, key, value)
            
        db.commit()
        db.refresh(service)
        return service
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating fabric service {service_id}: {e}")
        raise e


def delete_fabric_service(db: Session, service_id: UUID) -> bool:
    """
    Deletes a fabric service record from the database.
    """
    try:
        service = db.query(FabricService).filter(FabricService.service_id == service_id).first()
        if not service:
            return False
            
        db.delete(service)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting fabric service {service_id}: {e}")
        raise e