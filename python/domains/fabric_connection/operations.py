"""
Business logic / operations layer for Fabric Connections.
File: domains/fabric_connection/operations.py
"""
import uuid
from sqlalchemy.orm import Session
from .models import FabricConnection
from .schemas import FabricConnectionIn, FabricConnectionUpdate

def get_fabric_connections(db: Session):
    return db.query(FabricConnection).all()

def get_fabric_connections_by_service_id(db: Session, service_id: str):
    return db.query(FabricConnection).filter(FabricConnection.service_id == service_id).all()

def post_fabric_connection(db: Session, data: FabricConnectionIn):
    new_conn = FabricConnection(**data.model_dump())
    db.add(new_conn)
    db.commit()
    db.refresh(new_conn)
    return new_conn

def update_fabric_connection(db: Session, connection_id: str, data: FabricConnectionUpdate):
    conn = db.query(FabricConnection).filter(FabricConnection.connection_id == connection_id).first()
    if conn:
        for key, val in data.model_dump(exclude_unset=True).items():
            setattr(conn, key, val)
        db.commit()
        db.refresh(conn)
    return conn

def delete_fabric_connection(db: Session, connection_id: str) -> bool:
    conn = db.query(FabricConnection).filter(FabricConnection.connection_id == connection_id).first()
    if conn:
        db.delete(conn)
        db.commit()
        return True
    return False