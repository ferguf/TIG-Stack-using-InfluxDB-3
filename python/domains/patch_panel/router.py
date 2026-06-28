from fastapi import APIRouter, HTTPException, Depends
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from scripts.api_session import get_db
# DDD Imports
from domains.patch_panel.service import PatchPanelService
from scripts.api_schema import PatchPanelIn, PatchPanelOut

router = APIRouter(
    prefix="/patchPanels",
    tags=["Patch Panels"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=PatchPanelOut, summary="Create a new Patch Panel")
def create_patch_panel_route(data: PatchPanelIn, db: Session = Depends(get_db)):
    return PatchPanelService.create(db, data)

@router.get("/{port_id}", response_model=PatchPanelOut, summary="Get a single Patch Panel by ID")
def get_patch_panel_route(port_id: UUID, db: Session = Depends(get_db)):
    panel = PatchPanelService.get_by_id(db, port_id)
    if not panel:
        raise HTTPException(status_code=404, detail=f"Patch Panel {port_id} not found")
    return panel

@router.get("/device/{device_id}", response_model=List[PatchPanelOut], summary="Get Patch Panels by Device ID")
def get_patch_panel_by_device_route(device_id: UUID, db: Session = Depends(get_db)):
    return PatchPanelService.get_by_device(db, device_id)

@router.put("/{port_id}", response_model=PatchPanelOut, summary="Update a Patch Panel")
def update_patch_panel_route(port_id: UUID, data: PatchPanelIn, db: Session = Depends(get_db)):
    updated = PatchPanelService.update(db, port_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Patch Panel {port_id} not found")
    return updated