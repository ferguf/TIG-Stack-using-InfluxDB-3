from typing import List, Optional
from datetime import date as dt_date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database import get_db
from domains.traffic.service import TrafficService

# Assuming these schemas are available in your domains/traffic/schemas.py
from domains.traffic.schemas import (
    RouterDetailResponse, 
    RouterSummary, 
    PopToPopTraffic
)

router = APIRouter(prefix="/traffic", tags=["Traffic Domain"])

# -----------------------------
# GLOBAL & REGIONAL SUMMARY
# -----------------------------

@router.get(
    "/summary/global",
    summary="Global + Regional traffic summary"
)
def get_global_summary(db: Session = Depends(get_db)):
    result = TrafficService.get_global_summary(db)
    if not result:
        raise HTTPException(status_code=404, detail="Global summary data not found")
    return result

@router.get(
    "/regions/detail", 
    summary="Region Provider POP Router hierarchy"
)
def get_regions_detail(
    report_date: dt_date = Query(default=dt_date(2026, 4, 25)),
    pop_limit: Optional[int] = Query(default=None),
    router_limit: Optional[int] = Query(default=None),
    db: Session = Depends(get_db)
):
    result = TrafficService.get_regions_detail(db, report_date, pop_limit, router_limit)
    if not result:
        raise HTTPException(status_code=404, detail="No region detail data found")
    return result


# -----------------------------
# POP-TO-POP MATRIX
# -----------------------------

@router.get(
    "/pop2pop/{pop}",
    response_model=List[PopToPopTraffic],
    summary="Return POP-to-POP rows for a specific POP"
)
def get_pop_to_pop_for_pop(
    pop: str,
    limit: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db)
):
    rows = TrafficService.get_pop_to_pop_for_pop(db, pop, limit)
    if not rows:
        raise HTTPException(status_code=404, detail=f"POP '{pop}' not found")
    return rows


# -----------------------------
# SINGLE POP EXECUTIONS
# -----------------------------

@router.get(
    "/pops/{pop}/summary",
    summary="POP summary + routers (local/intra/inter) for a given day"
)
def get_pop_summary_with_routers(
    pop: str,
    report_date: dt_date = Query(..., description="YYYY-MM-DD"),
    router_limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    result = TrafficService.get_pop_summary_with_routers(db, pop, report_date, router_limit)
    if not result:
        raise HTTPException(status_code=404, detail=f"POP '{pop}' summary not found")
    return result

@router.get(
    "/pops/{pop}",
    summary="Return POP summary over N days (default today)"
)
def get_pop(
    pop: str,
    days: int = Query(default=1, ge=1, le=30),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    result = TrafficService.get_pop_rolling_summary(db, pop, days, limit)
    if not result:
        raise HTTPException(status_code=404, detail=f"POP '{pop}' not found for last {days} day(s)")
    return result


# -----------------------------
# ROUTER TRAFFIC & DETAIL
# -----------------------------

@router.get(
    "/routers",
    response_model=List[RouterSummary],
    summary="Top N router summaries (fast, from MV)"
)
def get_router_summaries(
    report_date: dt_date = Query(default_factory=dt_date.today),
    limit: int = Query(default=10, ge=1, le=200),
    sort: str = Query(default="egress_total", description="egress_total | inter | intra | local | pct_global"),
    order: str = Query(default="desc", description="asc or desc"),
    db: Session = Depends(get_db)
):
    # This explicit mapping fixes the TypeError and 500 error previously encountered
    rows = TrafficService.get_router_summaries(
        db=db, 
        report_date=report_date, 
        limit=limit, 
        sort_col=sort, 
        order=order
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"No router summary rows for {report_date}")
    return rows

@router.get(
    "/router/{router_name}/detail",
    response_model=RouterDetailResponse,
    summary="Router detail with location, classification, egress and ingress flows"
)
def get_router_detail_by_name(
    router_name: str,
    report_date: dt_date = Query(default=dt_date(2026, 4, 21)),
    egress_limit: int = Query(25, ge=1, le=100),
    ingress_limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    result = TrafficService.get_router_detail(
        db=db,
        router_name=router_name.lower(),
        report_date=report_date,
        egress_limit=egress_limit,
        ingress_limit=ingress_limit
    )
    if not result:
        raise HTTPException(
            status_code=404, 
            detail=f"Router '{router_name}' not found for {report_date}"
        )
    return result