import uuid as uuid
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends
from typing import List 
from sqlalchemy.orm import Session
import scripts.api_operation as api_operation
from scripts.api_schema import PatchPanelIn, PatchPanelOut
from scripts.api_session import get_db

from scripts.api_model import Device


router = APIRouter(
    prefix="/patchPanels",
    tags=["Patch Panels"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=PatchPanelOut,
             summary="Create a new Patch Panel")
def create_patch_panel_route(
    panel_data: PatchPanelIn,
    db: Session = Depends(get_db)
):
    panel = api_operation.create_patch_panel(db, panel_data)
    return panel

@router.get("/{port_id}", response_model=PatchPanelOut,
            summary="Get a single Patch Panel by ID")
def get_patch_panel_route(port_id: UUID, db: Session = Depends(get_db)):
    panel = api_operation.get_patch_panel(db, port_id)
    if panel is None:
        raise HTTPException(status_code=404,
                            detail=f"Patch Panel {port_id} not found")
    return panel

@router.get("/device/{device_id}", response_model=List[PatchPanelOut],
            summary="Get all Patch Panels for a Device")
def get_patch_panels_for_device_route(device_id: UUID, db: Session = Depends(get_db)):
    panels = api_operation.get_patch_panels_for_device(db, device_id)
    return panels

@router.get("/deviceName/{device_name}", response_model=List[PatchPanelOut],
            summary="Get all Patch Panels for a Device")
def get_patch_panels_for_device_name(device_name: str, db: Session = Depends(get_db)):
    panels = api_operation.get_patch_panel_ports_by_device_name(db, device_name)
    return panels

@router.get(
    "/deviceName/{device_name}/portName/{port_name}",
    response_model=PatchPanelOut,
    summary="Get a specific Patch Panel Port for a Device"
)
def get_patch_panel_port_route(
    device_name: str,
    port_name: str,
    db: Session = Depends(get_db)
):
    panel = api_operation.get_patch_panel_port_by_port_name(db, device_name, port_name)
    if panel is None:
        raise HTTPException(
            status_code=404,
            detail=f"Port {port_name} not found for Device {device_name}"
        )

    return panel


@router.get(
    "/device/{device_id}/port/{port_id}",
    response_model=PatchPanelOut,
    summary="Get a specific Patch Panel Port for a Device"
)
def get_patch_panel_port_route(
    device_id: UUID,
    port_id: UUID,
    db: Session = Depends(get_db)
):
    panel = api_operation.get_patch_panel_port(db, device_id, port_id)

    if panel is None:
        raise HTTPException(
            status_code=404,
            detail=f"Port {port_id} not found for Device {device_id}"
        )

    return panel

@router.put("/{port_id}", response_model=PatchPanelOut,
            summary="Update a Patch Panel")

def update_patch_panel_route(
    port_id: UUID,
    panel_data: PatchPanelIn,
    db: Session = Depends(get_db)
):
    updated = api_operation.update_patch_panel(db, port_id, panel_data)
    if updated is None:
        raise HTTPException(status_code=404,
                            detail=f"Patch Panel {port_id} not found")
    return updated

@router.patch(
    "/port/{port_id}", 
    response_model=PatchPanelOut,
    summary="Partially update a patch panel port connection"
)
def patch_patch_panel_route(
    port_id: UUID,
    panel_data: PatchPanelIn,
    db: Session = Depends(get_db)
):
    """
    Update only specific fields of a patch panel port.
    Prevents NotNullViolation by ignoring unset fields like device_id.
    """
    updated = api_operation.patch_patch_panel(db, port_id, panel_data)
    
    if updated is None:
        raise HTTPException(
            status_code=404,
            detail=f"Patch Panel Port {port_id} not found"
        )
        
    return updated