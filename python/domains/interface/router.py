from fastapi import APIRouter, HTTPException, Depends
from typing import List 
from uuid import UUID
from sqlalchemy.orm import Session
from scripts.api_session import get_db
# DDD Imports
from domains.interface.service import InterfaceService
from scripts.api_schema import (
    InterfaceOut, InterfaceIn, InterfaceUpdate, InterfaceDetailOut
)

router = APIRouter(prefix="/interface", tags=["interface"])

@router.get("/", response_model=List[InterfaceOut])
def get_all_interfaces(db: Session = Depends(get_db)):
    return InterfaceService.get_all(db)

@router.get("/{interface_id}", response_model=InterfaceOut)
def get_interface(interface_id: UUID, db: Session = Depends(get_db)):
    interface = InterfaceService.get_by_id(db, interface_id)
    if not interface:
        raise HTTPException(status_code=404, detail="Interface not found")
    return interface

@router.get("/detail/{interface_id}", response_model=InterfaceDetailOut)
def get_interface_detail(interface_id: UUID, db: Session = Depends(get_db)):
    detail = InterfaceService.get_detail(db, interface_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Interface detail not found")
    return detail

@router.post("/", response_model=InterfaceOut)
def create_interface(interface_in: InterfaceIn, db: Session = Depends(get_db)):
    return InterfaceService.create(db, interface_in)