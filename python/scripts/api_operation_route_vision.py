"""
operations_route_vision.py
Summary view for Route Vision.
"""

from http.client import HTTPException
import logging
import uuid
from uuid import UUID
from typing import List, Optional
from sqlalchemy.orm import Session
from scripts.api_model import RouteVision, VGlobalTrafficSummary
from scripts.api_schema import RouteVisionCreate, RouteVisionRead
from uuid import UUID as UUIDType

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# CRUD Functions
# -------------------------------------------------------------------

def create_routes_bulk(db: Session, service_id: UUIDType, routes: list[RouteVisionCreate]):
    """
    Inserts multiple routes, stamping each with the parent service_id.
    """
    created = []
    for data in routes:
        # We manually unpack to ensure the service_id from the path parameter is used
        route = RouteVision(
            fabric_service_id=service_id,
            fabric_connection_id=data.fabric_connection_id,
            ip_prefix=data.ip_prefix,
            route_type=data.route_type,
            route_status=data.route_status,
            route_target=data.route_target,
            route_distinguisher=data.route_distinguisher,
            ip_next_hop=data.ip_next_hop,
            bgp_asn=data.bgp_asn,
            bgp_as_path=data.bgp_as_path,
            bgp_community=data.bgp_community,
        )
        db.add(route)
        created.append(route)

    try:
        db.commit()
        for r in created:
            db.refresh(r)
        return created
    except Exception as e:
        db.rollback()
        logger.error(f"Bulk route creation failed: {e}")
        raise e

def get_routes(db: Session):
    return db.query(RouteVision).all()

def get_routes_by_service(db: Session, service_id: UUIDType):
    return (
        db.query(RouteVision)
        .filter(RouteVision.fabric_service_id == service_id)
        .all()
    )

def update_route(db: Session, service_id: UUIDType, route_id: UUIDType, data: RouteVisionCreate):
    route = (
        db.query(RouteVision)
        .filter(
            RouteVision.route_id == route_id,
            RouteVision.fabric_service_id == service_id
        )
        .first()
    )

    if not route:
        raise HTTPException(status_code=404, detail="Route not found for this service")

    for k, v in data.model_dump().items():
        setattr(route, k, v)

    db.commit()
    db.refresh(route)
    return route

def delete_route(db: Session, route_id: UUIDType):
    route = db.query(RouteVision).filter(RouteVision.route_id == route_id).first()

    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    route.route_status = "Deleted"
    db.commit()
    db.refresh(route)
    return route

def list_routes(db: Session, fabric_service_id: UUID = None):
    q = db.query(RouteVision)
    if fabric_service_id:
        q = q.filter(RouteVision.fabric_service_id == fabric_service_id)
    return q.all()

def update_route(db: Session, route_id: UUID, data: RouteVisionCreate):
    route = get_routes(db, route_id)
    for k, v in data.model_dump().items():
        setattr(route, k, v)
    db.commit()
    db.refresh(route)
    return route

def delete_route(db: Session, route_id: UUID):
    route = get_routes(db, route_id)
    route.route_status = "Deleted"
    db.commit()
    return route

def get_global_traffic_summary(db: Session):
    return db.query(VGlobalTrafficSummary).all()