from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import scripts.api_operation_network as api_operation
from scripts.api_schema import (
    NetworkLinkIn, NetworkLinkOut, NetworkLinkUpdate, 
    ROPChannelMemberIn, ROPChannelMemberOut, ROPChannelMemberUpdate, VNetworkLinksDetailOut, 
    VNetworkLinksLAGOut
)
from scripts.cli_base import get_db

router = APIRouter(
    prefix="/networkLinks",
    tags=["Network Links (Polymorphic)"],
    responses={404: {"description": "Not found"}},
)

# --- STATIC LAG ROUTES (Must be above dynamic {link_id}) ---

@router.get("/lag", response_model=List[VNetworkLinksLAGOut], summary="List all LAG View links")
def list_lag_links(db: Session = Depends(get_db)):
    return api_operation.get_network_links_lag(db)

@router.get("/lag/{device_id}", response_model=List[VNetworkLinksLAGOut], summary="List LAG View links for a specific device")
def list_lag_links_for_device(device_id: UUID, db: Session = Depends(get_db)):
    return api_operation.get_network_links_lag_by_device(db, device_id)

# --- STATIC DETAILS ROUTES (Must be above dynamic {link_id}) ---

@router.get("/detail", response_model=List[VNetworkLinksDetailOut], summary="Get detailed info for all Network Links")
def list_network_links_detail(db: Session = Depends(get_db)):
    details = api_operation.get_network_links_detail(db)
    if not details:
        raise HTTPException(status_code=404, detail="No detailed network links found")
    return details

@router.get("/detail/device/{device_id}", response_model=List[VNetworkLinksDetailOut], summary="Get detailed Network Links for a device")
def list_network_links_detail_by_device(device_id: UUID, db: Session = Depends(get_db)):
    details = api_operation.get_network_links_detail_by_device(db, device_id)
    if not details:
        raise HTTPException(status_code=404, detail=f"No detailed links found for device '{device_id}'")
    return details

# --- NEW: SCALABLE UNIFIED FILTER ROUTE ---

@router.get("/detail/filter", response_model=List[VNetworkLinksDetailOut], summary="Filter Network Links with UI Defaults")
def filter_network_links_detail(
    network: str = Query("AS3356", description="Target Network ASN or Name"), 
    pop: Optional[str] = Query(None, description="Target POP or Market Location"), 
    link_type: str = Query("All", description="Specific link type or 'All'"),
    db: Session = Depends(get_db)
):
    """
    Dedicated endpoint for the Network Digital Twin UI filter controls. 
    Applies default parameters automatically and supports combined vector searches.
    """
    parsed_link_type = None if link_type.lower() == "all" else link_type
    
    details = api_operation.get_network_links_detail_by_network(
        db, 
        network_name=network, 
        pop=pop,
        link_type=parsed_link_type
    )
    
    if not details:
        pop_msg = f" and POP/Market '{pop}'" if pop else ""
        type_msg = f" of type '{link_type}'" if parsed_link_type else ""
        raise HTTPException(
            status_code=404, 
            detail=f"No detailed links found for network '{network}'{pop_msg}{type_msg}"
        )
        
    return details

# --- STATIC ROP ROUTES ---

@router.get("/ROP/", response_model=List[ROPChannelMemberOut], summary="List all ROP Channel Members")
def list_rop_channels(db: Session = Depends(get_db)):
    members = api_operation.get_rop_channel_members(db)
    if not members:
        raise HTTPException(status_code=404, detail={"error": "No ROP Channel Members found"})
    return members

# --- DYNAMIC GENERIC ROUTES ---

@router.get("/", response_model=List[NetworkLinkOut], summary="List all Abstract Network Links")
def list_network_links(db: Session = Depends(get_db)):
    links = api_operation.get_network_links(db)
    if not links:
        raise HTTPException(status_code=404, detail={"error": "No network links found"})
    return links

@router.get("/{link_id}", response_model=NetworkLinkOut, summary="Get a Network Link by ID")
def get_network_link_by_id(link_id: UUID, db: Session = Depends(get_db)):
    link = api_operation.get_network_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Network Link not found")
    return link

# --- POST / PUT / DELETE ---

@router.post("/", response_model=NetworkLinkOut, status_code=201, summary="Create a new Network Link")
def create_network_link(data: NetworkLinkIn, db: Session = Depends(get_db)):
    try:
        new_link = api_operation.post_network_link(db, data)
        return new_link
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "Data validation failed", "message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Unexpected error creating link", "message": str(e)})

@router.put("/{link_id}", response_model=NetworkLinkOut, summary="Update Network Link details")
def update_network_link(link_id: UUID, update: NetworkLinkUpdate, db: Session = Depends(get_db)):
    try:
        updated_link = api_operation.put_network_link(db, link_id, update)
        if not updated_link:
            raise HTTPException(status_code=404, detail="Network Link not found")
        return updated_link
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "Update failed", "message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Unexpected error updating link", "message": str(e)})

@router.delete("/{link_id}", response_model=dict, summary="Delete a Network Link")
def delete_network_link(link_id: UUID, db: Session = Depends(get_db)):
    try:
        success = api_operation.delete_network_link_by_id(db, link_id)
        if not success:
            raise HTTPException(status_code=404, detail={"error": f"Network Link {link_id} not found"})
        return {"message": f"Network Link {link_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Unexpected error deleting link", "message": str(e)})

# --- ROP SUB-RESOURCE DYNAMICS (Specific IDs) ---

@router.get("/ROP/{rop_link_id}", response_model=List[ROPChannelMemberOut])
def list_channels_by_rop(rop_link_id: UUID, db: Session = Depends(get_db)):
    members = api_operation.get_channels_by_rop_link(db, rop_link_id)
    if not members:
        raise HTTPException(status_code=404, detail={"error": f"No channels found for ROP link ID {rop_link_id}"})
    return members