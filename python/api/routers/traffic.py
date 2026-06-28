from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, or_
from typing import List

from datetime import date as dt_date

from scripts.api_session import get_db

# Existing models
from scripts.api_model import (
    VGlobalTrafficSummary,
    VPopToPopTraffic,
    VPopSummary,
    VTrafficRouterDetail,MVTrafficRouterDetail,MVTrafficPop2Pop
)

# Existing schemas
from scripts.api_schema import (
    GlobalTrafficSummary,
    PopSummaryResponse,
    PopToPopTraffic,
    PopSummary,
    TrafficRouterDetail,RouterSummary,RouterDetailResponse
)

router = APIRouter(prefix="/traffic", tags=["traffic"])


# -----------------------------
# GLOBAL SUMMARY
# -----------------------------
@router.get(
    "/summary/global",
    summary="Global + Regional traffic summary"
)
def get_global_summary(db: Session = Depends(get_db)):
    result = db.execute(
        text("SELECT api_global_region_summary()")
    ).scalar()

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
    limit: int = Query(25, ge=1, le=200),  # ✅ LIMIT CONTROL
    db: Session = Depends(get_db)
):
    rows = (
        db.query(MVTrafficPop2Pop)
        .filter(
            or_(
                MVTrafficPop2Pop.src_pop == pop.lower(),
                MVTrafficPop2Pop.dst_pop == pop.lower()
            )
        )
        .order_by(MVTrafficPop2Pop.rank)
        .limit(limit)   # ✅ APPLY LIMIT
        .all()
    )

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"POP '{pop}' not found"
        )

    return rows


# =====================================================
# POP SUMMARY
# =====================================================

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
    result = db.execute(
        text("""
            SELECT api_pop_summary_with_routers(
                :pop,
                :report_date,
                :router_limit
            )
        """),
        {
            "pop": pop.lower(),
            "report_date": report_date,
            "router_limit": router_limit
        }
    ).scalar()

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"POP '{pop}' not found"
        )

    return result
# -----------------------------
# Region POP
# -----------------------------


@router.get("/regions/detail", summary="Region Provider POP Router hierarchy")
def get_regions_detail(
    report_date: dt_date = Query(default=dt_date(2026, 4, 25)),
    pop_limit: int | None = Query(default=None),
    router_limit: int | None = Query(default=None),
    db: Session = Depends(get_db)
):
    row = db.execute(
        text("SELECT api_region_detail(:d, :pl, :rl)"),
        {"d": report_date, "pl": pop_limit, "rl": router_limit}
    ).scalar()
    if not row:
        raise HTTPException(status_code=404, detail="No data found")
    return row


# -----------------------------
# SINGLE POP
# -----------------------------
from datetime import datetime, timedelta


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
    """
    Returns POP summary over a rolling time window

    Params:
    - pop: POP name
    - days: number of days (default 1 = today)
    - limit: top N rows (default 10)
    """

    # ✅ Calculate date range
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days - 1)

    query = text("""
        SELECT
            pop,
            SUM(total_bytes) AS total_bytes,
            SUM(router_bytes) AS router_bytes,
            SUM(intra_bytes) AS intra_bytes,
            SUM(inter_bytes) AS inter_bytes,
            MAX(global_bytes) AS global_bytes,
            ROUND(SUM(total_bytes) / NULLIF(MAX(global_bytes), 0) * 100, 4) AS pct_of_global
        FROM v_pop_to_pop_traffic
        WHERE pop = :pop
          AND report_date BETWEEN :start_date AND :end_date
        GROUP BY pop
        ORDER BY total_bytes DESC
        LIMIT :limit
    """)

    result = db.execute(
        query,
        {
            "pop": pop,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit
        }
    ).fetchall()

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"POP '{pop}' not found for last {days} day(s)"
        )


# =====================================================
# ✅ ROUTER TRAFFIC DETAIL (TOP N - ORM STYLE)
# =====================================================

@router.get(
    "/routers",
    response_model=List[RouterSummary],
    summary="Top N router summaries (fast, from MV)"
)
def get_router_summaries(
    report_date: dt_date = Query(default=dt_date.today()),
    limit: int = Query(default=10, ge=1, le=200),
    sort: str = Query(default="egress_total"),  # egress_total | inter | intra | local | pct_global
    order: str = Query(default="desc"),
    db: Session = Depends(get_db)
):
    sort_map = {
        "egress_total": MVTrafficRouterDetail.router_egress_total_bytes,
        "inter": MVTrafficRouterDetail.inter_egress_bytes,
        "intra": MVTrafficRouterDetail.intra_egress_bytes,
        "local": MVTrafficRouterDetail.local_egress_bytes,
        "pct_global": MVTrafficRouterDetail.pct_router_egress_of_global
    }
    sort_col = sort_map.get(sort, MVTrafficRouterDetail.router_egress_total_bytes)

    q = db.query(MVTrafficRouterDetail).filter(MVTrafficRouterDetail.report_date == report_date)
    q = q.order_by(sort_col.asc() if order.lower() == "asc" else sort_col.desc())

    rows = q.limit(limit).all()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No router summary rows for {report_date}")
    return rows



@router.get(
    "/router/detail",
    response_model=RouterDetailResponse,
    summary="Router detail with egress and ingress flow breakdown"
)
def get_router_detail(
    router_name: str,
    report_date: dt_date,
    egress_limit: int = Query(25, ge=1, le=100),
    ingress_limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    result = db.execute(
        text("""
            SELECT api_router_detail_json(
                :report_date,
                :router,
                :egress_limit,
                :ingress_limit
            )
        """),
        {
            "report_date": report_date,
            "router": router_name,
            "egress_limit": egress_limit,
            "ingress_limit": ingress_limit
        }
    ).scalar()

    return result

@router.get(
    "/router/{router_name}/detail",
    summary="Router detail with location, classification, egress and ingress flows"
)

@router.get(
    "/router/{router_name}/detail",
    summary="Router detail with location, classification, egress and ingress flows"
)
def get_router_detail_by_name(
    router_name: str = "ear1.den1",
    report_date: dt_date = Query(default=dt_date(2026, 4, 21)),
    egress_limit: int = Query(25, ge=1, le=100),
    ingress_limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    result = db.execute(
        text("""
            SELECT api_router_detail_json(
                :report_date,
                :router,
                :egress_limit,
                :ingress_limit
            )
        """),
        {
            "report_date": report_date,
            "router": router_name.lower(),
            "egress_limit": egress_limit,
            "ingress_limit": ingress_limit
        }
    ).scalar()

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Router '{router_name}' not found for {report_date}"
        )

    return result