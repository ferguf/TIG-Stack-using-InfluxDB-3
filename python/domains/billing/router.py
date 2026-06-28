"""
Billing Router - MCP Ready (READ vs WRITE tagging)
"""

from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from sqlalchemy.dialects.postgresql import insert

# Core DB
from core.database import get_db

# Domain imports
from . import models as m
from . import operations as ops
from . import schemas as s
from .operations import (
    BillingValidationError,
    BillingNotFoundError,
    BillingConflictError,
)

# ✅ IMPORTANT: No global tags
router = APIRouter(prefix="/billing")


# =========================================================
# ERROR HANDLING
# =========================================================

def handle_error(e: Exception):
    if isinstance(e, BillingNotFoundError):
        raise HTTPException(status_code=404, detail=str(e))
    if isinstance(e, BillingValidationError):
        raise HTTPException(status_code=422, detail=str(e))
    if isinstance(e, BillingConflictError):
        raise HTTPException(status_code=409, detail=str(e))
    raise HTTPException(status_code=500, detail=str(e))


# =========================================================
# MODELS
# =========================================================

@router.post("/models", response_model=s.BillingModelResponse, tags=["write"])
def create_model(payload: s.BillingModelCreate, db: Session = Depends(get_db)):
    try:
        return ops.create_model(db, payload)
    except Exception as e:
        handle_error(e)

@router.get("/models", response_model=List[s.BillingModelResponse], tags=["read"])
def list_models(db: Session = Depends(get_db)):
    return ops.list_models(db)

@router.put("/models/", response_model=s.BillingModelResponse, tags=["write"])
def update_model(model_id: str, payload: s.BillingModelCreate, db: Session = Depends(get_db)):
    try:
        return ops.update_model(db, model_id, payload)
    except Exception as e:
        handle_error(e)

@router.delete("/models/", tags=["write"])
def delete_model(model_id: str, db: Session = Depends(get_db)):
    try:
        return ops.delete_model(db, model_id)
    except Exception as e:
        handle_error(e)


# =========================================================
# RATES
# =========================================================

@router.post("/rates", response_model=s.BillingRateResponse, tags=["write"])
def create_rate(payload: s.BillingRateCreate, db: Session = Depends(get_db)):
    try:
        return ops.create_rate(db, payload)
    except Exception as e:
        handle_error(e)

@router.get("/rates", response_model=List[s.BillingRateResponse], tags=["read"])
def list_rates(db: Session = Depends(get_db)):
    return ops.list_rates(db)

@router.put("/rates/", response_model=s.BillingRateResponse, tags=["write"])
def update_rate(rate_id: str, payload: s.BillingRateCreate, db: Session = Depends(get_db)):
    try:
        return ops.update_rate(db, rate_id, payload)
    except Exception as e:
        handle_error(e)

@router.delete("/rates/", tags=["write"])
def delete_rate(rate_id: str, db: Session = Depends(get_db)):
    try:
        return ops.delete_rate(db, rate_id)
    except Exception as e:
        handle_error(e)


# =========================================================
# PROVIDERS
# =========================================================

@router.post("/providers", response_model=s.BillingProviderResponse, tags=["write"])
def create_provider(payload: s.BillingProviderCreate, db: Session = Depends(get_db)):
    try:
        return ops.create_provider(db, payload)
    except Exception as e:
        handle_error(e)

@router.get("/providers", response_model=List[s.BillingProviderResponse], tags=["read"])
def list_providers(db: Session = Depends(get_db)):
    return ops.list_providers(db)

@router.put("/providers/", response_model=s.BillingProviderResponse, tags=["write"])
def update_provider(provider_id: str, payload: s.BillingProviderCreate, db: Session = Depends(get_db)):
    try:
        return ops.update_provider(db, provider_id, payload)
    except Exception as e:
        handle_error(e)

@router.delete("/providers/", tags=["write"])
def delete_provider(provider_id: str, db: Session = Depends(get_db)):
    try:
        return ops.delete_provider(db, provider_id)
    except Exception as e:
        handle_error(e)


# =========================================================
# QUERY / COMPOSITE (READ)
# =========================================================

@router.get("/rates/composite", response_model=s.BillingCompositeResponse, tags=["read"])
def get_composite_catalog(rate_id: str, db: Session = Depends(get_db)):
    sql = text("SELECT * FROM v_rate_card_composite WHERE rate_id = CAST(:rate_id AS UUID)")
    result = db.execute(sql, {"rate_id": rate_id}).mappings().first()
    if not result:
        raise HTTPException(status_code=404, detail="Rate not found")
    return dict(result)


@router.get("/customers/rates", response_model=List[s.BillingRateResponse], tags=["read"])
def get_customer_rates(customer_id: str, db: Session = Depends(get_db)):
    try:
        sql = text("""
        SELECT r.* FROM billing_rate r
        JOIN customer_rate_cards crc ON r.id = crc.rate_id
        WHERE crc.customer_id = :customer_id
        """)
        result = db.execute(sql, {"customer_id": customer_id}).mappings().all()
        return [dict(row) for row in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers/rates", response_model=List[s.BillingRateResponse], tags=["read"])
def get_provider_rates(provider_id: str, db: Session = Depends(get_db)):
    try:
        sql = text("""
        SELECT r.* FROM billing_rate r
        JOIN provider_rate_cards prc ON r.id = prc.rate_id
        WHERE prc.provider_id = :provider_id
        """)
        result = db.execute(sql, {"provider_id": provider_id}).mappings().all()
        return [dict(row) for row in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))