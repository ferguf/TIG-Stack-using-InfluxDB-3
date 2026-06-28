"""
api_routing_interface.py
Summary view accessors for all analytics views.
"""

import logging
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from uuid import UUID

# Alias imports to match the logic used in the CRUD functions
import scripts.api_schema as schemas
import scripts.api_model as models
from uuid import UUID, uuid4
# Re-import specific classes if needed elsewhere in the file, 
# but the functions below will use the aliases.
from scripts.api_model import RoutingPolicy

from scripts.api_schema import BGPNeighborIn, BGPNeighborUpdate, InterfaceIn, InterfaceUpdate, RoutingPolicyIn, RoutingPolicyUpdate, StaticRouteIn, StaticRouteUpdate
from scripts.api_model import (
    BGPNeighbor,
    RoutingPolicy,
    StaticRoute,
    Interface
)

logger = logging.getLogger(__name__)

# ============================================================
#  INTERNAL HELPER (UNIFIED FETCH PATTERN)
# ============================================================

def get_static_routes(db: Session) -> List[StaticRoute]:
    """
    Retrieves all defined static routes (IPv4 and IPv6).
    """
    return db.query(StaticRoute).all()

def get_static_routes_by_fabric_connection(
    fabric_connection_id: UUID,
    db: Session) -> List[StaticRoute]:
    """
    Retrieves all static routes associated with a specific fabric connection.

    - fabric_connection_id: UUID of the fabric connection
    """
    return (
        db.query(StaticRoute)
        .filter(StaticRoute.fabric_connection_id == fabric_connection_id)
        .all()
    )

def create_static_route(db: Session, route_in: StaticRouteIn): # <--- Ensure DB is first
    """
    Creates a new static route entry.
    """
    # Create the ORM object from the Pydantic model
    # Ensure route_in is the one being dumped, not db!
    new_route = StaticRoute(**route_in.model_dump(exclude_unset=True))
    
    db.add(new_route)
    db.commit()
    db.refresh(new_route)
    return new_route

def update_static_route(
    route_id: UUID,
    route_update: StaticRouteUpdate,
    db: Session) -> Optional[StaticRoute]:
    """
    Updates an existing static route.

    - route_id: UUID of the static route
    - route_update: StaticRouteUpdate Pydantic model with fields to modify
    """
    route = db.query(StaticRoute).filter(StaticRoute.route_id == route_id).first()
    if not route:
        return None

    update_data = route_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(route, field, value)

    db.commit()
    db.refresh(route)
    return route

def delete_static_route(
    route_id: UUID,
    db: Session) -> bool:
    """
    Deletes a static route by its UUID.

    - route_id: UUID of the static route
    """
    route = db.query(StaticRoute).filter(StaticRoute.route_id == route_id).first()
    if not route:
        return False

    db.delete(route)
    db.commit()
    return True

# ============================================================
#  policy CRUD Methods (Pydantic Schemas)
# ============================================================
def get_routing_policies(db: Session) -> List[RoutingPolicy]:
    """
    Retrieves all defined BGP routing policies.
    """
    return db.query(RoutingPolicy).all()

def get_routing_policies_by_fabric_service(
    fabric_service_id: UUID,
    db: Session) -> List[RoutingPolicy]:
    """
    Retrieves all routing policies associated with a specific fabric service.
    """
    return (
        db.query(RoutingPolicy)
        .filter(RoutingPolicy.fabric_service_id == fabric_service_id)
        .all()
    )
    
def get_routing_policy_by_id(policy_id: UUID, db: Session):
    return (
        db.query(RoutingPolicy)
        .filter(RoutingPolicy.policy_id == policy_id)
        .order_by(RoutingPolicy.sequence)
        .all()
    )
    
def create_routing_policy(
    policies_in: List[schemas.RoutingPolicyIn],
    db: Session,
    existing_policy_id: UUID | None = None
) -> List[models.RoutingPolicy]:
    """
    Creates routing policy terms.
    - POST: generates a new policy_id
    - PUT: reuses existing_policy_id
    """
    try:
        new_terms = []

        # Determine policy_id for this operation
        # POST: take from first term
        # PUT: override with existing_policy_id
        policy_id = existing_policy_id or policies_in[0].policy_id

        for term_data in policies_in:
            db_term = models.RoutingPolicy(
                term_id=uuid4(),
                policy_id=policy_id,
                fabric_service_id=term_data.fabric_service_id,
                policy_name=term_data.policy_name,
                direction=term_data.direction,
                sequence=term_data.sequence,
                term_name=term_data.term_name,
                prefixes=term_data.prefixes,
                match_type=term_data.match_type,
                upto_mask=term_data.upto_mask,
                action=term_data.action,
                med=term_data.med,
                local_pref=term_data.local_pref,
                as_prepend=term_data.as_prepend,
                communities=term_data.communities
            )
            new_terms.append(db_term)

        db.add_all(new_terms)
        db.commit()

        for term in new_terms:
            db.refresh(term)

        return new_terms

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database commit failed: {str(e)}"
        )


def update_routing_policy(
    policy_id: UUID,
    policies_in: List[schemas.RoutingPolicyIn],
    db: Session
) -> List[models.RoutingPolicy]:
    """
    Replaces an entire routing policy:
    1. Deletes all existing terms
    2. Inserts new terms using the same policy_id
    """
    try:
        delete_routing_policy_terms(policy_id, db)

        return create_routing_policy(
            policies_in,
            db,
            existing_policy_id=policy_id
        )

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update routing policy: {str(e)}"
        )

def delete_routing_policy_terms(policy_id: UUID, db: Session):
    """
    Deletes all routing policy terms for a given policy_id.
    """
    try:
        db.query(models.RoutingPolicy).filter(
            models.RoutingPolicy.policy_id == policy_id
        ).delete()
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete routing policy terms: {str(e)}"
        )


def delete_routing_policy_terms(policy_id: UUID, db: Session):
    """
    Deletes all routing policy terms for a given policy_id.
    """
    db.query(RoutingPolicy).filter(
        RoutingPolicy.policy_id == policy_id
    ).delete()
    db.commit()


def get_bgp_neighbors(db: Session) -> List[BGPNeighbor]:
    """
    Retrieves all defined BGP neighbors (IPv4 and IPv6).
    """
    return db.query(BGPNeighbor).all()

def get_bgp_neighbors_by_fabric_connection(
    fabric_connection_id: UUID,
    db: Session) -> List[BGPNeighbor]:
    """
    Retrieves all BGP neighbors associated with a specific fabric connection.

    - fabric_connection_id: UUID of the fabric connection
    """
    return (
        db.query(BGPNeighbor)
        .filter(BGPNeighbor.fabric_connection_id == fabric_connection_id)
        .all()
    )
    
def get_bgp_neighbor_by_id(
    bgp_neighbor_id: UUID,
    db: Session) -> Optional[BGPNeighbor]:
    """
    Retrieves a single BGP neighbor by its UUID.

    - bgp_neighbor_id: UUID of the BGP neighbor
    """
    return (
        db.query(BGPNeighbor)
        .filter(BGPNeighbor.bgp_neighbor_id == bgp_neighbor_id)
        .first()
    )

def create_bgp_neighbor(
    neighbor_in: BGPNeighborIn,
    db: Session) -> BGPNeighbor:
    """
    Creates a new BGP neighbor entry.

    - neighbor_in: BGPNeighborIn Pydantic model containing neighbor details
    """
    new_neighbor = BGPNeighbor(**neighbor_in.model_dump(exclude_unset=True))
    db.add(new_neighbor)
    db.commit()
    db.refresh(new_neighbor)
    return new_neighbor

def update_bgp_neighbor(
    bgp_neighbor_id: UUID,
    neighbor_update: BGPNeighborUpdate,
    db: Session) -> Optional[BGPNeighbor]:
    """
    Updates an existing BGP neighbor.

    - bgp_neighbor_id: UUID of the BGP neighbor
    - neighbor_update: BGPNeighborUpdate Pydantic model with fields to modify
    """
    neighbor = (
        db.query(BGPNeighbor)
        .filter(BGPNeighbor.bgp_neighbor_id == bgp_neighbor_id)
        .first()
    )

    if not neighbor:
        return None

    update_data = neighbor_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(neighbor, field, value)

    db.commit()
    db.refresh(neighbor)
    return neighbor

def delete_bgp_neighbor(
    bgp_neighbor_id: UUID,
    db: Session
) -> bool:
    """
    Deletes a BGP neighbor by its UUID.

    - bgp_neighbor_id: UUID of the BGP neighbor
    """
    neighbor = (
        db.query(BGPNeighbor)
        .filter(BGPNeighbor.bgp_neighbor_id == bgp_neighbor_id)
        .first()
    )

    if not neighbor:
        return False

    db.delete(neighbor)
    db.commit()
    return True

# ============================================================
# Interface
# ============================================================


def get_interfaces(db: Session) -> List[Interface]:
    """
    Retrieves all interfaces.
    """
    return db.query(Interface).all()

def get_interface_by_id(
    interface_id: UUID,
    db: Session
) -> Optional[Interface]:
    """
    Retrieves a single interface by its UUID.
    """
    return (
        db.query(Interface)
        .filter(Interface.interface_id == interface_id)
        .first()
    )
    
def get_interfaces_by_device(
    device_id: UUID,
    db: Session
) -> List[Interface]:
    """
    Retrieves all interfaces associated with a specific device.
    """
    return (
        db.query(Interface)
        .filter(Interface.device_id == device_id)
        .all()
    )
    
def create_interface(
    interface_in: InterfaceIn,
    db: Session
) -> Interface:
    """
    Creates a new interface entry.
    """
    new_interface = Interface(**interface_in.model_dump(exclude_unset=True))
    db.add(new_interface)
    db.commit()
    db.refresh(new_interface)
    return new_interface

def update_interface(
    interface_id: UUID,
    interface_update: InterfaceUpdate,
    db: Session
) -> Optional[Interface]:
    """
    Updates an existing interface.
    """
    interface = (
        db.query(Interface)
        .filter(Interface.interface_id == interface_id)
        .first()
    )

    if not interface:
        return None

    update_data = interface_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(interface, field, value)

    db.commit()
    db.refresh(interface)
    return interface

def delete_interface(
    interface_id: UUID,
    db: Session
) -> bool:
    """
    Deletes an interface by its UUID.
    """
    interface = (
        db.query(Interface)
        .filter(Interface.interface_id == interface_id)
        .first()
    )

    if not interface:
        return False

    db.delete(interface)
    db.commit()
    return True