from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from domains.netlink import operations, schemas
from core.database import get_db

router = APIRouter(
    prefix="/networkLinks",
    tags=["Network Links (Polymorphic)"],
    responses={404: {"description": "Not found"}},
)

# ==========================================
# 1. STATIC ROUTES (Must be evaluated first)
# ==========================================

@router.get("/lag", response_model=List[schemas.VNetworkLinksLAGOut], summary="List all LAG View links")
def list_lag_links(db: Session = Depends(get_db)):
    return operations.get_network_links_lag(db)

@router.get("/lag/{device_id}", response_model=List[schemas.VNetworkLinksLAGOut], summary="List LAG View links for a specific device")
def list_lag_links_for_device(device_id: UUID, db: Session = Depends(get_db)):
    return operations.get_network_links_lag_by_device(db, device_id)

@router.get("/detail", response_model=List[schemas.VNetworkLinksDetailOut], summary="Get detailed info for all Network Links")
def list_network_links_detail(db: Session = Depends(get_db)):
    details = operations.get_network_links_detail(db)
    if not details:
        raise HTTPException(status_code=404, detail="No detailed network links found")
    return details

@router.get("/detail/device/{device_id}", response_model=List[schemas.VNetworkLinksDetailOut], summary="Get detailed Network Links for a device")
def list_network_links_detail_by_device(device_id: UUID, db: Session = Depends(get_db)):
    details = operations.get_network_links_detail_by_device(db, device_id)
    if not details:
        raise HTTPException(status_code=404, detail=f"No detailed links found for device '{device_id}'")
    return details

@router.get("/detail/filter", response_model=List[schemas.VNetworkLinksDetailOut], summary="Filter Network Links with UI Defaults")
def filter_network_links_detail(
    network: str = Query("AS3356", description="Target Network ASN or Name"), 
    pop: Optional[str] = Query(None, description="Target POP or Market Location"), 
    link_type: str = Query("All", description="Specific link type or 'All'"),
    db: Session = Depends(get_db)
):
    parsed_link_type = None if link_type.lower() == "all" else link_type
    details = operations.get_network_links_detail_by_network(
        db, 
        network_name=network, 
        pop=pop,
        link_type=parsed_link_type
    )
    if not details:
        raise HTTPException(status_code=404, detail=f"No detailed links found for network '{network}'")
    return details

@router.get("/ROP/", response_model=List[schemas.ROPChannelMemberOut], summary="List all ROP Channel Members")
def list_rop_channels(db: Session = Depends(get_db)):
    members = operations.get_rop_channel_members(db)
    if not members:
        raise HTTPException(status_code=404, detail={"error": "No ROP Channel Members found"})
    return members

@router.post("/ROP/member", response_model=schemas.ROPChannelMemberOut, summary="Assign a channel to a ROP link")
def add_channel_to_rop(data: schemas.ROPChannelMemberIn, db: Session = Depends(get_db)):
    try:
        return operations.post_rop_channel_member(db, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": "Data validation failed", "message": str(e)})

@router.get("/ROP/{rop_link_id}", response_model=List[schemas.ROPChannelMemberOut], summary="List channels for a specific ROP link")
def list_channels_by_rop(rop_link_id: UUID, db: Session = Depends(get_db)):
    members = operations.get_channels_by_rop_link(db, rop_link_id)
    if not members:
        raise HTTPException(status_code=404, detail={"error": f"No channels found for ROP link ID {rop_link_id}"})
    return members


# ==========================================
# 2. DYNAMIC BASE ROUTES (Must be evaluated last)
# ==========================================

@router.get("/", response_model=List[schemas.NetworkLinkOut], summary="List all Abstract Network Links")
def list_network_links(db: Session = Depends(get_db)):
    links = operations.get_network_links(db)
    if not links:
        raise HTTPException(status_code=404, detail={"error": "No network links found"})
    return links

@router.post("/", response_model=schemas.NetworkLinkOut, status_code=201, summary="Create a new Network Link")
def create_network_link(data: schemas.NetworkLinkIn, db: Session = Depends(get_db)):
    try:
        return operations.post_network_link(db, data)
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Unexpected error creating link", "message": str(e)})

@router.get("/{link_id}", response_model=schemas.NetworkLinkOut, summary="Get a Network Link by ID")
def get_network_link_by_id(link_id: UUID, db: Session = Depends(get_db)):
    link = operations.get_network_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Network Link not found")
    return link

@router.put("/{link_id}", response_model=schemas.NetworkLinkOut, summary="Update Network Link details")
def update_network_link(link_id: UUID, update: schemas.NetworkLinkUpdate, db: Session = Depends(get_db)):
    try:
        updated_link = operations.put_network_link(db, link_id, update)
        if not updated_link:
            raise HTTPException(status_code=404, detail="Network Link not found")
        return updated_link
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Unexpected error updating link", "message": str(e)})

@router.delete("/{link_id}", response_model=dict, summary="Delete a Network Link")
def delete_network_link(link_id: UUID, db: Session = Depends(get_db)):
    try:
        success = operations.delete_network_link_by_id(db, link_id)
        if not success:
            raise HTTPException(status_code=404, detail={"error": f"Network Link {link_id} not found"})
        return {"message": f"Network Link {link_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Unexpected error deleting link", "message": str(e)})