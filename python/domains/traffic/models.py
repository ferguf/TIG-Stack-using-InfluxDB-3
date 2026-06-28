from sqlalchemy import Column, Float, String, Numeric, Date, Integer, Text
from scripts.api_session import Base




class FECSummaryView(Base):
    __tablename__ = "fec_summary"   # materialized view

    fec_id = Column(UUID, primary_key=True)
    bucket_start = Column(DateTime, primary_key=True)
    granularity = Column(String)
    device_a_name = Column(String)
    device_b_name = Column(String)
    fec_label = Column(String)
    avg_mbps = Column(Numeric)
    min_mbps = Column(Numeric)
    max_mbps = Column(Numeric)
    p95_mbps = Column(Numeric)
    total_mbps = Column(Numeric)

class VPopToPopTraffic(Base):
    __tablename__ = "v_pop_to_pop_traffic"
    __table_args__ = {"extend_existing": True}

    row_type = Column(Text, primary_key=True)
    row_id = Column(Text, primary_key=True)

    pop = Column(Text)
    egress_pop = Column(Text)

    router_bytes = Column(Numeric)
    intra_bytes = Column(Numeric)
    inter_bytes = Column(Numeric)
    pop_total_bytes = Column(Numeric)

    router_pct_of_pop = Column(Numeric)
    intra_pct_of_pop = Column(Numeric)
    inter_pct_of_pop = Column(Numeric)

    global_bytes = Column(Numeric)
    pct_of_global = Column(Numeric)

    router_egress_bytes = Column(Numeric)
    intra_egress_bytes = Column(Numeric)
    inter_egress_bytes = Column(Numeric)
    inter_ingress_bytes = Column(Numeric)

    ingress_country = Column(Text)
    ingress_provider_tag = Column(Text)
    ingress_region_tag = Column(Text)

    egress_country = Column(Text)
    egress_provider_tag = Column(Text)
    egress_region_tag = Column(Text)

class VTrafficRouterDetail(Base):
    __tablename__ = "v_traffic_router_detail"

    # ✅ identity
    row_type = Column(String)
    row_id = Column(String, primary_key=True)
    router = Column(String)

    # ✅ traffic totals
    router_bytes = Column(Numeric)
    intra_bytes = Column(Numeric)
    inter_bytes = Column(Numeric)
    total_bytes = Column(Numeric)

    # ✅ composition (% of router traffic)
    router_pct_of_router = Column(Numeric)
    intra_pct_of_router = Column(Numeric)
    inter_pct_of_router = Column(Numeric)

    # ✅ global context
    global_bytes = Column(Numeric)
    pct_of_global = Column(Numeric)

    # ✅ directional traffic (preserved from pop_to_pop)
    router_egress_bytes = Column(Numeric)
    intra_egress_bytes = Column(Numeric)
    inter_egress_bytes = Column(Numeric)
    inter_ingress_bytes = Column(Numeric)

    # ✅ enrichment
    country = Column(String)
    provider_tag = Column(String)
    region_tag = Column(String)

class VGlobalTrafficSummary(Base):
    __tablename__ = "v_global_summary"

    region = Column(String, primary_key=True)
    provider = Column(String)

    total_pops = Column(Integer)
    total_routers = Column(Integer)

    total_router_bytes = Column(Numeric)
    total_intra_bytes = Column(Numeric)
    total_inter_bytes = Column(Numeric)
    total_bytes = Column(Numeric)

    avg_router_pct = Column(Numeric)
    avg_intra_pct = Column(Numeric)
    avg_inter_pct = Column(Numeric)

class VPopSummary(Base):
    __tablename__ = "v_pop_summary"

    pop = Column(String, primary_key=True)

    pop_total_egress_traffic = Column(Numeric)
    local_egress_traffic = Column(Numeric)
    intra_egress_traffic = Column(Numeric)
    inter_egress_traffic = Column(Numeric)
    inter_ingress_traffic = Column(Numeric)

    pop_egress_pct_of_global = Column(Float)
    pop_ingress_pct_of_global = Column(Float)
    
class PopTrafficSummary(Base):
    __tablename__ = "v_pop_traffic_summary"

    row_type = Column(String)
    pop = Column(String, primary_key=True)

    router_bytes = Column(Integer)
    intra_bytes = Column(Integer)
    inter_bytes = Column(Integer)

    pop_total_egress_bytes = Column(Integer)
    pop_total_ingress_bytes = Column(Integer)

    router_pct_of_pop = Column(Float)
    intra_pct_of_pop = Column(Float)
    inter_pct_of_pop = Column(Float)

    global_bytes = Column(Integer)
    pct_of_egress_global = Column(Float)
    pct_of_ingress_global = Column(Float)

    ingress_location_name = Column(String)
    ingress_city = Column(String)
    ingress_state = Column(String)
    ingress_country = Column(String)
    ingress_latitude = Column(Float)
    ingress_longitude = Column(Float)
    ingress_availability_zone = Column(String)
    ingress_timezone_name = Column(String)
    ingress_timezone_offset = Column(Integer)

    ingress_provider = Column(String)
    ingress_region = Column(String)

    router_role_counts = Column(JSON)

class MVTrafficPop2Pop(Base):
    __tablename__ = "mv_traffic_pop2pop"

    # ✅ rank
    rank = Column(Integer, primary_key=True)

    # ✅ POPs (directional)
    src_pop = Column(String)
    dst_pop = Column(String)

    # ✅ metrics
    total_bytes = Column(Numeric)
    router_bytes = Column(Numeric)
    intra_bytes = Column(Numeric)
    inter_bytes = Column(Numeric)

    # ✅ source enrichment
    src_location = Column(String)
    src_city = Column(String)
    src_state = Column(String)
    src_country = Column(String)
    src_region = Column(String)
    src_provider = Column(String)

    # ✅ destination enrichment
    dst_location = Column(String)
    dst_city = Column(String)
    dst_state = Column(String)
    dst_country = Column(String)
    dst_region = Column(String)
    dst_provider = Column(String)

class MVTrafficRouterDetail(Base):
    __tablename__ = "mv_traffic_router_detail"

    report_date = Column(Date, primary_key=True)
    router = Column(String, primary_key=True)

    # location enrichment
    pop = Column(String)
    short_name = Column(String)
    location_name = Column(String)
    location_code = Column(String)
    city = Column(String)
    state = Column(String)
    country = Column(String)
    timezone_name = Column(String)
    latitude = Column(Numeric)
    longitude = Column(Numeric)

    # metrics
    local_egress_bytes = Column(Numeric)
    intra_egress_bytes = Column(Numeric)
    inter_egress_bytes = Column(Numeric)
    router_egress_total_bytes = Column(Numeric)
    inter_ingress_total_bytes = Column(Numeric)

    global_egress_bytes = Column(Numeric)

    pct_router_egress_of_global = Column(Numeric)
    pct_local_of_router_egress = Column(Numeric)
    pct_intra_of_router_egress = Column(Numeric)
    pct_inter_of_router_egress = Column(Numeric)

    __tablename__ = "mv_traffic_pop2pop"
    __table_args__ = {'extend_existing': True}
        
    row_id = Column(String, primary_key=True)
    pop = Column(String)
    egress_pop = Column(String)
    router_bytes = Column(Numeric)
    intra_bytes = Column(Numeric)
    inter_bytes = Column(Numeric)
    pop_total_bytes = Column(Numeric)
    global_bytes = Column(Numeric)