from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID as UUIDType
from typing import List

from scripts.api_session import get_db
from scripts.api_schema import RouteVisionCreate, RouteVisionRead

# Import CRUD functions
from scripts.api_operation_route_vision import (
    get_routes,
    get_routes_by_service,
    create_routes_bulk,
    update_route,
    delete_route
)

# -------------------------------------------------------------------
# FastAPI Router
# -------------------------------------------------------------------
router = APIRouter(prefix="/routeVision", tags=["routeVision"])


@router.get("/", response_model=list[RouteVisionRead])
def api_get_all_routes(db: Session = Depends(get_db)):
    return get_routes(db)


@router.get("/{service_id}", response_model=list[RouteVisionRead])
def api_get_routes_by_service(service_id: UUIDType, db: Session = Depends(get_db)):
    return get_routes_by_service(db, service_id)


@router.post("/{service_id}", response_model=list[RouteVisionRead])
def api_create_routes(
    service_id: UUIDType,
    data: List[RouteVisionCreate],
    db: Session = Depends(get_db)
):
    return create_routes_bulk(db, service_id, data)


@router.put("/{service_id}/{route_id}", response_model=RouteVisionRead)
def api_update_route(
    service_id: UUIDType,
    route_id: UUIDType,
    data: RouteVisionCreate,
    db: Session = Depends(get_db)
):
    return update_route(db, service_id, route_id, data)


@router.delete("/{route_id}", response_model=RouteVisionRead)
def api_delete_route(route_id: UUIDType, db: Session = Depends(get_db)):
    return delete_route(db, route_id)