"""
Business logic / operations layer for billing domain.
File: domains/billing/operations.py
"""
from __future__ import annotations
from typing import Any, Optional, Type
from uuid import UUID
from sqlalchemy.orm import Session

# ✅ NATIVE RELATIVE IMPORTS WITHIN THE DOMAIN
from . import models as m
from . import schemas as s

# =========================================================
# DOMAIN EXCEPTIONS
# =========================================================

class BillingError(Exception):
    """Base billing exception."""

class BillingValidationError(BillingError):
    """Raised when business validation fails."""

class BillingNotFoundError(BillingError):
    """Raised when an entity does not exist."""

class BillingConflictError(BillingError):
    """Raised when uniqueness / conflict rules are violated."""

# =========================================================
# GENERIC CRUD HELPERS
# =========================================================

def get_by_id(db: Session, model_cls: Type[Any], entity_id: UUID):
    obj = db.get(model_cls, entity_id)
    if not obj:
        raise BillingNotFoundError(f"{model_cls.__name__} not found: {entity_id}")
    return obj

def list_all(db: Session, model_cls: Type[Any]):
    return db.query(model_cls).all()

def create_entity(db: Session, model_cls: Type[Any], payload: dict):
    obj = model_cls(**payload)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_entity(db: Session, obj: Any, payload: dict):
    for field, value in payload.items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj

def delete_entity(db: Session, obj: Any):
    db.delete(obj)
    db.commit()
    return {"deleted": True}

# =========================================================
# BILLING MODEL CRUD
# =========================================================

def list_models(db: Session):
    return list_all(db, m.BillingModel)

def get_model(db: Session, entity_id: UUID):
    return get_by_id(db, m.BillingModel, entity_id)

def create_model(db: Session, payload: s.BillingModelCreate):
    existing = db.query(m.BillingModel).filter(m.BillingModel.code == payload.code).first()
    if existing:
        raise BillingConflictError(f"Billing model code already exists: {payload.code}")
    return create_entity(db, m.BillingModel, payload.model_dump())

def update_model(db: Session, entity_id: UUID, payload: s.BillingModelUpdate):
    obj = get_model(db, entity_id)
    data = payload.model_dump(exclude_unset=True)

    if "code" in data:
        dupe = (
            db.query(m.BillingModel)
            .filter(m.BillingModel.code == data["code"], m.BillingModel.id != entity_id)
            .first()
        )
        if dupe:
            raise BillingConflictError(f"Billing model code already exists: {data['code']}")

    return update_entity(db, obj, data)

def delete_model(db: Session, entity_id: UUID):
    obj = get_model(db, entity_id)
    return delete_entity(db, obj)

# =========================================================
# BILLING RATE CRUD
# =========================================================

def list_rates(db: Session):
    return list_all(db, m.BillingRate)

def get_rate(db: Session, entity_id: UUID):
    return get_by_id(db, m.BillingRate, entity_id)

def create_rate(db: Session, payload: s.BillingRateCreate):
    existing = db.query(m.BillingRate).filter(m.BillingRate.name == payload.name).first()
    if existing:
        raise BillingConflictError(f"Billing rate name already exists: {payload.name}")
    return create_entity(db, m.BillingRate, payload.model_dump())

def update_rate(db: Session, entity_id: UUID, payload: s.BillingRateUpdate):
    obj = get_rate(db, entity_id)
    data = payload.model_dump(exclude_unset=True)

    if "name" in data:
        dupe = (
            db.query(m.BillingRate)
            .filter(m.BillingRate.name == data["name"], m.BillingRate.id != entity_id)
            .first()
        )
        if dupe:
            raise BillingConflictError(f"Billing rate name already exists: {data['name']}")

    return update_entity(db, obj, data)

def delete_rate(db: Session, entity_id: UUID):
    obj = get_rate(db, entity_id)
    return delete_entity(db, obj)

# =========================================================
# BILLING PORT CRUD
# =========================================================

def list_ports(db: Session):
    return list_all(db, m.BillingPort)

def get_port(db: Session, entity_id: UUID):
    return get_by_id(db, m.BillingPort, entity_id)

def create_port(db: Session, payload: s.BillingPortCreate):
    _ = get_rate(db, payload.rate_id)

    port_speed = db.get(m.BillingPortSpeed, payload.port_speed_mbps)
    if not port_speed:
        raise BillingValidationError(f"Unknown port speed: {payload.port_speed_mbps}")

    dupe = (
        db.query(m.BillingPort)
        .filter(
            m.BillingPort.rate_id == payload.rate_id,
            m.BillingPort.port_speed_mbps == payload.port_speed_mbps,
        )
        .first()
    )
    if dupe:
        raise BillingConflictError("billing_port already exists for rateId + portSpeedMbps")

    return create_entity(db, m.BillingPort, payload.model_dump())

def update_port(db: Session, entity_id: UUID, payload: s.BillingPortUpdate):
    obj = get_port(db, entity_id)
    data = payload.model_dump(exclude_unset=True)
    return update_entity(db, obj, data)

def delete_port(db: Session, entity_id: UUID):
    obj = get_port(db, entity_id)
    return delete_entity(db, obj)

# =========================================================
# BILLING ACCESS CRUD
# =========================================================

def list_access(db: Session):
    return list_all(db, m.BillingAccess)

def get_access(db: Session, entity_id: UUID):
    return get_by_id(db, m.BillingAccess, entity_id)

def list_providers(db: Session):
    return db.query(m.BillingProvider).all()

def create_provider(db: Session, payload: s.BillingProviderCreate):
    # Check for conflict
    if db.query(m.BillingProvider).filter_by(code=payload.code).first():
        raise BillingConflictError("Provider code already exists")
    
    new_prov = m.BillingProvider(**payload.model_dump())
    db.add(new_prov)
    db.commit()
    db.refresh(new_prov)
    return new_prov