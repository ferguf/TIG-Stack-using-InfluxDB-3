from sqlalchemy.orm import Session
from sqlalchemy import text, or_
from datetime import date, datetime, timedelta
from typing import List, Optional

# Ensure these match your actual ORM model paths
from scripts.api_model import MVTrafficRouterDetail, MVTrafficPop2Pop

class TrafficService:
    
    @staticmethod
    def get_global_summary(db: Session):
        return db.execute(text("SELECT api_global_region_summary()")).scalar()

    @staticmethod
    def get_regions_detail(db: Session, report_date: date, pop_limit: Optional[int], router_limit: Optional[int]):
        return db.execute(
            text("SELECT api_region_detail(:d, :pl, :rl)"),
            {"d": report_date, "pl": pop_limit, "rl": router_limit}
        ).scalar()

    @staticmethod
    def get_pop_to_pop_for_pop(db: Session, pop: str, limit: int):
        rows = (
            db.query(MVTrafficPop2Pop)
            .filter(
                or_(
                    MVTrafficPop2Pop.src_pop == pop.lower(),
                    MVTrafficPop2Pop.dst_pop == pop.lower()
                )
            )
            .order_by(MVTrafficPop2Pop.rank)
            .limit(limit)
            .all()
        )

        # Explicitly project the ORM objects into dictionaries.
        # This acts as an infallible Data Transfer Object (DTO) mapping.
        mapped_results = []
        for row in rows:
            mapped_results.append({
                "pop": pop.lower(),
                # If the searched pop is the source, the peer is the dest (and vice versa)
                "egress_pop": row.dst_pop if row.src_pop.lower() == pop.lower() else row.src_pop,
                "pop_total_bytes": float(row.total_bytes) if row.total_bytes else 0.0,
                "global_bytes": float(row.global_bytes) if row.global_bytes else 0.0,
                "rank": row.rank
            })
            
        return mapped_results

    @staticmethod
    def get_pop_summary_with_routers(db: Session, pop: str, report_date: date, router_limit: int):
        return db.execute(
            text("SELECT api_pop_summary_with_routers(:pop, :report_date, :router_limit)"),
            {"pop": pop.lower(), "report_date": report_date, "router_limit": router_limit}
        ).scalar()

    @staticmethod
    def get_pop_rolling_summary(db: Session, pop: str, days: int, limit: int):
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
        
        return db.execute(
            query,
            {
                "pop": pop.lower(), 
                "start_date": start_date, 
                "end_date": end_date, 
                "limit": limit
            }
        ).fetchall()

    @staticmethod
    def get_router_summaries(
        db: Session, 
        report_date: date, 
        limit: int, 
        sort_col: str = "egress_total", 
        order: str = "desc"
    ):
        # 1. Map the string from the API to the actual SQLAlchemy Column object
        sort_map = {
            "egress_total": MVTrafficRouterDetail.router_egress_total_bytes,
            "inter": MVTrafficRouterDetail.inter_egress_bytes,
            "intra": MVTrafficRouterDetail.intra_egress_bytes,
            "local": MVTrafficRouterDetail.local_egress_bytes,
            "pct_global": MVTrafficRouterDetail.pct_router_egress_of_global
        }
        
        # Default to egress_total if an invalid string is passed
        column_obj = sort_map.get(sort_col.lower(), MVTrafficRouterDetail.router_egress_total_bytes)

        # 2. Build the query
        query = db.query(MVTrafficRouterDetail).filter(MVTrafficRouterDetail.report_date == report_date)
        
        # 3. Apply the ordering using the ORM object, not the string
        if order.lower() == "asc":
            query = query.order_by(column_obj.asc())
        else:
            query = query.order_by(column_obj.desc())

        return query.limit(limit).all()

    @staticmethod
    def get_router_detail(db: Session, router_name: str, report_date: date, egress_limit: int, ingress_limit: int):
        return db.execute(
            text("SELECT api_router_detail_json(:date, :router, :egr, :ing)"),
            {"date": report_date, "router": router_name.lower(), "egr": egress_limit, "ing": ingress_limit}
        ).scalar()