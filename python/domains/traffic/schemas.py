from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import date

class RouterSummary(BaseModel):
    report_date: date
    router: str

    pop: str | None = None
    short_name: str | None = None
    location_name: str
    location_code: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    timezone_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    local_egress_bytes: float
    intra_egress_bytes: float
    inter_egress_bytes: float
    router_egress_total_bytes: float
    inter_ingress_total_bytes: float

    global_egress_bytes: float

    pct_router_egress_of_global: float
    pct_local_of_router_egress: float
    pct_intra_of_router_egress: float
    pct_inter_of_router_egress: float

    class Config:
        from_attributes = True

class PopToPopTraffic(BaseModel):
    pop: str
    egress_pop: Optional[str]
    router_bytes: float
    intra_bytes: float
    inter_bytes: float
    pop_total_bytes: float
    global_bytes: float
    
    model_config = ConfigDict(from_attributes=True)

# ---------------------------------------------------------
# ROUTER DETAIL NESTED SCHEMAS
# ---------------------------------------------------------

class FlowDetail(BaseModel):
    # Guaranteed fields from DB
    peer_pop: str
    flow_type: str
    flow_bytes: float
    flow_Gbytes: float
    peer_router: str
    
    # Missing from DB payload (must be Optional)
    peer_location_name: Optional[str] = None
    
    # Metrics differ between egress/ingress arrays (must be Optional)
    pct_of_router_egress: Optional[float] = None
    pct_of_router_ingress: Optional[float] = None
    pct_of_router_egress_topn: Optional[float] = None
    pct_of_router_ingress_topn: Optional[float] = None


class RouterLocationDetail(BaseModel):
    # Assuming these are guaranteed based on previous successful traces
    pop: str
    role: str
    router: str
    network: str
    sum_Gbytes: Optional[float] = None


class RouterSummaryDetail(BaseModel):
    # Guaranteed fields present in the DB 'input' dictionary
    pop: str
    router: str
    report_date: date
    inter_egress_bytes: Optional[float] = None
    intra_egress_bytes: Optional[float] = None
    local_egress_bytes: Optional[float] = None
    router_egress_total_bytes: Optional[float] = None
    router_ingress_total_bytes: Optional[float] = None

    # Missing fields triggering the 422 errors (Forced to Optional)
    location_name: Optional[str] = None
    inter_ingress_total_bytes: Optional[float] = None
    global_egress_bytes: Optional[float] = None
    pct_router_egress_of_global: Optional[float] = None
    pct_local_of_router_egress: Optional[float] = None
    pct_intra_of_router_egress: Optional[float] = None
    pct_inter_of_router_egress: Optional[float] = None


class RouterDetailResponse(BaseModel):
    summary: RouterSummaryDetail
    location: RouterLocationDetail
    egress_flows: List[FlowDetail] = []
    ingress_flows: List[FlowDetail] = []
    
    class Config:
        from_attributes = True