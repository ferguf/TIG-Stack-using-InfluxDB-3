import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

# IMPORTANT: Centralized database session dependency
from core.database import get_db

# Native relative imports within the domain slice
from . import operations
from .schemas import TemplateIn, TemplateOut, TemplateUpdate

logger = logging.getLogger(__name__)

# Replace "template" with your specific domain name (e.g., "interfaces")
router = APIRouter(prefix="/template", tags=["Template Domain"])

@router.post("/", response_model=TemplateOut, status_code=201)
def create_template_route(payload: TemplateIn, db: Session = Depends(get_db)):
    try:
        return operations.create_record(db, payload)
    except Exception as e:
        logger.error(f"Error creating record: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[TemplateOut])
def list_template_route(db: Session = Depends(get_db)):
    return operations.get_all_records(db)

@router.get("/{record_id:uuid}", response_model=TemplateOut)
def get_template_route(record_id: UUID, db: Session = Depends(get_db)):
    record = operations.get_record_by_id(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record

@router.put("/{record_id:uuid}", response_model=TemplateOut)
def update_template_route(record_id: UUID, payload: TemplateUpdate, db: Session = Depends(get_db)):
    updated_record = operations.update_record(db, record_id, payload)
    if not updated_record:
        raise HTTPException(status_code=404, detail="Record not found")
    return updated_record

@router.delete("/{record_id:uuid}")
def delete_template_route(record_id: UUID, db: Session = Depends(get_db)):
    success = operations.delete_record(db, record_id)
    if not success:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"detail": "Record deleted successfully"}