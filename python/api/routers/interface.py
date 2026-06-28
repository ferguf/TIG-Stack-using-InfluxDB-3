import uuid as uuid
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends
from typing import List 
from sqlalchemy.orm import Session
import scripts.api_routing_interface as api_routing_interface
from scripts.api_schema import (
    BGPNeighborIn, BGPNeighborOut, DeviceIn, DeviceOut, DeviceUpdate, 
    IPInterfaceIn, IPInterfaceOut, IPInterfaceUpdate, InterfaceDetailOut, 
    InterfaceIn, InterfaceOut, InterfaceUpdate, PortOut, RoutingPolicyIn, 
    RoutingPolicyOut, RoutingPolicyUpdate, StaticRouteIn, StaticRouteOut, 
    StaticRouteUpdate
)
from scripts.api_session import get_db
from scripts.api_model import Device, IPInterface, InterfaceDetail

router = APIRouter(
    prefix="/interface",
    tags=["interface"],
    responses={404: {"description": "Not found"}},
)

# =========================================================
# 1. SPECIALIZED / DETAIL ROUTES (Must come first)
# =========================================================

@router.get("/detail/{interface_id}", response_model=InterfaceDetailOut)
def get_interface_detail_by_id(interface_id: UUID, db: Session = Depends(get_db)):
    """
    Retrieves a high-level view of an interface including device and port data.
    """
    result = db.query(InterfaceDetail).filter(InterfaceDetail.interface_id == interface_id).first()
    if not result:
        raise HTTPException(status_code=404, detail=f"Interface {interface_id} not found")
    return result

# =========================================================
# 2. BGP NEIGHBOR ROUTES
# =========================================================

@router.get("/bgpNeighbor/{bgp_neighbor_id}", response_model=BGPNeighborOut)
def get_bgp_neighbor(bgp_neighbor_id: UUID, db: Session = Depends(get_db)):
    neighbor = api_routing_interface.get_bgp_neighbor_by_id(bgp_neighbor_id, db)
    if not neighbor:
        raise HTTPException(status_code=404, detail="BGP neighbor not found")
    return neighbor

@router.get("/bgpNeighbor/interface/{interface_id}", response_model=List[BGPNeighborOut])
def get_bgp_neighbors_by_interface(interface_id: UUID, db: Session = Depends(get_db)):
    return api_routing_interface.get_bgp_neighbors_by_interface(interface_id, db)

@router.post("/bgpNeighbor", response_model=BGPNeighborOut)
def create_bgp_neighbor(neighbor_in: BGPNeighborIn, db: Session = Depends(get_db)):
    return api_routing_interface.create_bgp_neighbor(neighbor_in, db)

@router.delete("/bgpNeighbor/{bgp_neighbor_id}")
def delete_bgp_neighbor(bgp_neighbor_id: UUID, db: Session = Depends(get_db)):
    deleted = api_routing_interface.delete_bgp_neighbor(bgp_neighbor_id, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="BGP neighbor not found")
    return {"detail": "BGP neighbor deleted successfully"}

# =========================================================
# 3. ROUTING POLICY ROUTES
# =========================================================
@router.get("/routingPolicy", response_model=List[RoutingPolicyOut])
def list_all_routing_policy_terms(db: Session = Depends(get_db)):
    return api_routing_interface.get_routing_policies(db)

@router.get(
    "/routingPolicy/fabricService/{fabric_service_id}",
    response_model=List[RoutingPolicyOut]
)
def get_routing_policies_by_fabric_service(
    fabric_service_id: UUID,
    db: Session = Depends(get_db)
):
    policies = api_routing_interface.get_routing_policies_by_fabric_service(
        fabric_service_id, db
    )
    if not policies:
        raise HTTPException(status_code=404, detail="No routing policies found")
    policies.sort(key=lambda p: p.sequence)
    return policies

@router.get("/routingPolicy/term/{term_id}", response_model=RoutingPolicyOut)
def get_routing_policy_term(term_id: UUID, db: Session = Depends(get_db)):
    term = api_routing_interface.get_routing_policy_term_by_id(term_id, db)
    if not term:
        raise HTTPException(status_code=404, detail="Routing policy term not found")
    return term

# DYNAMIC ROUTES LAST
@router.get("/routingPolicy/{policy_id}", response_model=List[RoutingPolicyOut])
def get_routing_policy(policy_id: UUID, db: Session = Depends(get_db)):
    policy_terms = api_routing_interface.get_routing_policy_by_id(policy_id, db)
    if not policy_terms:
        raise HTTPException(status_code=404, detail="Routing policy not found")
    return policy_terms

@router.put("/routingPolicy/{policy_id}", response_model=List[RoutingPolicyOut])
def replace_routing_policy(
    policy_id: UUID,
    policies_in: List[RoutingPolicyIn],
    db: Session = Depends(get_db)
):
    api_routing_interface.delete_routing_policy_terms(policy_id, db)

    return api_routing_interface.create_routing_policy(
        policies_in,
        db,
        existing_policy_id=policy_id
    )
@router.post("/routingPolicy", response_model=List[RoutingPolicyOut])
def create_routing_policy(
    policies_in: List[RoutingPolicyIn],
    db: Session = Depends(get_db)
):
    """
    Creates a brand‑new routing policy.
    The request body is an array of terms; a new policy_id is generated.
    """
    return api_routing_interface.create_routing_policy(
        policies_in,
        db,
        existing_policy_id=None  # POST always creates a new policy
    )

@router.get("/staticRoute/{interface_id}", response_model=List[StaticRouteOut])
def get_static_routes_by_interface(interface_id: UUID, db: Session = Depends(get_db)):
    return api_routing_interface.get_static_routes_by_interface(db, interface_id)

@router.post("/staticRoute", response_model=StaticRouteOut)
def create_static_route(route_in: StaticRouteIn, db: Session = Depends(get_db)):
    return api_routing_interface.create_static_route(db, route_in)

# =========================================================
# 5. IP ADDRESS ROUTES
# =========================================================

@router.get("/ipAddress/", response_model=List[IPInterfaceOut])
def list_ip_interfaces(db: Session = Depends(get_db)):
    return db.query(IPInterface).all()

@router.post("/ipAddress/", response_model=IPInterfaceOut)
def create_ip_interface(payload: IPInterfaceIn, db: Session = Depends(get_db)):
    ipif = IPInterface(**payload.model_dump())
    db.add(ipif)
    db.commit()
    db.refresh(ipif)
    return ipif

# =========================================================
# 6. BASE INTERFACE ROUTES (Broadest routes at the bottom)
# =========================================================

@router.get("/", response_model=List[InterfaceOut])
def get_all_interfaces(db: Session = Depends(get_db)):
    return api_routing_interface.get_interfaces(db)

@router.get("/device/{device_id}", response_model=List[InterfaceOut])
def get_interfaces_by_device(device_id: UUID, db: Session = Depends(get_db)):
    return api_routing_interface.get_interfaces_by_device(device_id, db)

@router.get("/{interface_id}", response_model=InterfaceOut)
def get_interface(interface_id: UUID, db: Session = Depends(get_db)):
    interface = api_routing_interface.get_interface_by_id(interface_id, db)
    if not interface:
        raise HTTPException(status_code=404, detail="Interface not found")
    return interface

@router.post("/", response_model=InterfaceOut)
def create_interface(interface_in: InterfaceIn, db: Session = Depends(get_db)):
    return api_routing_interface.create_interface(interface_in, db)

@router.put("/{interface_id}", response_model=InterfaceOut)
def update_interface(interface_id: UUID, interface_update: InterfaceUpdate, db: Session = Depends(get_db)):
    updated = api_routing_interface.update_interface(interface_id, interface_update, db)
    if not updated:
        raise HTTPException(status_code=404, detail="Interface not found")
    return updated