"""
File Name: 'api_model.py'
Updated: 2026-01-17
Description: Cleaned SQLAlchemy ORM models with Galileo Beck Topology support.
"""

import sys
import os
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import PrimaryKeyConstraint

# Import the REAL Base and engine from api_session
from scripts.api_schema import PortOut
from scripts.api_session import Base, engine

from sqlalchemy import (
    ARRAY, JSON, Column, String, Numeric, Integer, ForeignKey, DateTime,
    Text, BigInteger, Boolean, Date, func, UniqueConstraint,
    CheckConstraint, Computed, Table,TIMESTAMP,text,FetchedValue,Float
)
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB,CIDR
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy

# --- Path Injection for cli_base ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    from cli_base import Engine
except ImportError:
    Engine = None


# --- Galileo Beck Topology Views ---
def create_database_tables(engine):
    """
    Creates all defined tables in the database.
    This function should be run once during initial setup.
    """
    print("\nAttempting to set up database tables...")
    try:
        Base.metadata.drop_all(engine)  # For clean rebuilds in dev
        Base.metadata.create_all(engine)
        print("SUCCESS: All database tables created.")
    except Exception as e:
        print(f"ERROR: Failed to create one or more tables. {e}")


class FabricServiceDetail(Base):
    __tablename__ = "v_fabric_service_detail"
    __table_args__ = {"schema": "public"}

    # -------------------------
    # Core service fields
    # -------------------------
    service_id = Column(UUID(as_uuid=True), primary_key=True)
    customer_id = Column(UUID(as_uuid=True))

    customer_name = Column(String)
    account_id = Column(String)

    service_name = Column(String)
    service_alias = Column(String)
    service_type = Column(String)
    service_description = Column(String)

    route_target = Column(String)
    health_status = Column(Integer)

    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    # -------------------------
    # JSONB nested objects
    # -------------------------
    fabric_connections = Column(JSONB)
    fabric_ports = Column(JSONB)
    fabric_interfaces = Column(JSONB)    
    cloud_interconnects = Column(JSONB)   

class InterfaceDetail(Base):
    __tablename__ = "v_interface_detail"
    __table_args__ = {"schema": "public"}

    # -------------------------
    # Core interface fields
    # -------------------------
    interface_id = Column(UUID(as_uuid=True), primary_key=True)
    port_id: Optional[UUID] = None  # Allow nulls here
    service_id:Optional[UUID] = None  # Allow nulls here
    
    ckt_id = Column(String)
    description = Column(String)

    interface_name = Column(String)
    interface_type = Column(String)

    svlan_id = Column(Integer)
    cvlan_list = Column(String)

    dhcp_relay_enabled = Column(String)
    service_bw_mbps = Column(Integer)

    status = Column(String)

    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    # -------------------------
    # JSONB nested objects
    # -------------------------
    port = Column(JSONB)
    ip_addresses = Column(JSONB)
    bgp_neighbors = Column(JSONB)
    static_routes = Column(JSONB)
    
class GalileoNodes(Base):
    """The City Hubs/Stations (NYC1, DEN1, SFO1) and their device backpacks."""
    __tablename__ = "v_render_beck_nodes"
    __table_args__ = {"extend_existing": True}

    location_name = Column(String(100), primary_key=True)
    location_lat = Column(Numeric)
    location_long = Column(Numeric)
    location_x = Column(Numeric)
    location_y = Column(Numeric)
    devices_list = Column(JSONB)
    location_health_max = Column(Integer)

class CloudPartnerTable(Base):
    __tablename__ = "cloud_partners"
    __table_args__ = {"schema": "public", "extend_existing": True}

    partner_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_key = Column(String(50), nullable=False)
    partner_name = Column(String(100), nullable=False)
    partner_code = Column(String(20), nullable=False)
    partner_type = Column(String(50), nullable=False)
    region = Column(String(100), nullable=False)
    service_type = Column(String(20), nullable=False)
    service_status = Column(String(50), nullable=False)
    partnership_level = Column(String(50))
    notes = Column(Text)
    # Do NOT define created_at/updated_at here if you want 
    # Postgres to handle the defaults automatically during INSERT.

class CloudPartner(Base):
    """
    Maps to the PostgreSQL View v_cloud_partner_detail.
    Provides pre-aggregated bandwidth_tiers for the Galileo UI.
    """
    __tablename__ = "v_cloud_partner_detail"
    __table_args__ = {"schema": "public"}

    partner_id = Column(UUID(as_uuid=True), primary_key=True)
    partner_key = Column(String(50))
    partner_name = Column(String(100))
    partner_code = Column(String(20))
    partner_type = Column(String(50))
    region = Column(String(100))
    service_type = Column(String(20))
    service_status = Column(String(50))
    partnership_level = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    
    # This column now contains the JSON array [50, 100, 500, 1000]
    # Pydantic will automatically parse this into a List[int]
    bandwidth_tiers = Column(JSONB)

class CloudPartnerBandwidth(Base):
    """
    WRITE-ONLY: Mapped to the physical table.
    Used for inserting new speed tiers into the DB.
    """
    __tablename__ = "cloud_partner_bandwidths"
    __table_args__ = {"schema": "public"}

    partner_bw_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id = Column(UUID(as_uuid=True), ForeignKey("public.cloud_partners.partner_id"), nullable=False)
    service_bw = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())



class CloudConnection(Base):
    __tablename__ = "cloud_connections"
    # Ensure this model also knows it lives in the public schema
    __table_args__ = {"schema": "public", "extend_existing": True}

    cloud_connection_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # --- THE CRITICAL UPDATE ---
    # We add "public." to match CloudPartnerTable's registration
    partner_id = Column(UUID(as_uuid=True),
                        ForeignKey("public.cloud_partners.partner_id", ondelete="CASCADE"),
                        nullable=False)

    # Recommended: Also anchor service_id if you have a FabricService model
    service_id = Column(UUID(as_uuid=True), nullable=True) 
    
    connection_name = Column(String(100), nullable=False)
    # ... rest of your columns remain the same
    service_type = Column(String(20), nullable=False)
    service_status = Column(String(50), nullable=False)
    region = Column(String(100), nullable=False)

    service_bw = Column(Integer)
    redundancy_model = Column(String(50))
    description = Column(Text)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(),
                        onupdate=func.now(), nullable=False)


class GalileoLinks(Base):
    """The Inter-city fiber connections for topological rendering."""
    __tablename__ = "v_render_beck_links"
    __table_args__ = {"extend_existing": True}

    link_id = Column(UUID(as_uuid=True), primary_key=True)
    link_type = Column(String(30))
    description = Column(String(600))
    a_device_location = Column(String(100))
    a_port_id = Column(UUID)
    a_x = Column(Numeric)
    a_y = Column(Numeric)
    b_device_location = Column(String(100))
    b_port_id = Column(UUID)
    b_x = Column(Numeric)
    b_y = Column(Numeric)
    link_health = Column(Integer)

class RouteVision(Base):
    __tablename__ = "route_vision"

    route_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    fabric_service_id = Column(UUID(as_uuid=True), ForeignKey("fabric_services.service_id"), nullable=False)
    fabric_connection_id = Column(UUID(as_uuid=True), ForeignKey("fabric_connections.connection_id"))

    ip_prefix = Column(INET, nullable=False)
    route_type = Column(String(20), nullable=False)
    ip_next_hop = Column(String(200), nullable=False)
    route_status = Column(String(20), nullable=False, server_default="Active")

    route_target = Column(String(100))
    route_distinguisher = Column(String(200))

    bgp_asn = Column(Integer)
    bgp_as_path = Column(String(200))
    bgp_community = Column(String(200))

    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))

    fabric_service = relationship("FabricService")
    fabric_connection = relationship("FabricConnection")

class NetworkSummaryMaster(Base):
    __tablename__ = "v_network_summary_master"

    unique_id = Column(String, primary_key=True)
    category = Column(String)
    dimension = Column(JSON)
    count_value = Column(Integer)

class NetworkSummaryMasterV2(Base):
    __tablename__ = "v_network_summary_master_v2"

    unique_id = Column(String, primary_key=True)
    category = Column(String)
    dimension = Column(JSON)
    count_value = Column(Integer)

# ============================================================
# Telegraf and influxdb
# ============================================================


class VTelegrafInventory(Base):
    __table__ = Table(
        "v_telegraf_inventory",
        Base.metadata,
        Column("device_id", Text, primary_key=True),
        Column("device_name", Text),
        Column("location", Text),
        Column("device_role", Text),
        Column("port_id", UUID(as_uuid=True)),
        Column("port_name", Text),
        Column("port_speed", Text),
        Column("port_cktid", Text),
        Column("port_optic", Text),
        Column("lag_parent_id", UUID(as_uuid=True)),
        Column("port_health_status", Integer),
        Column("customer_id", UUID(as_uuid=True)),
        autoload_with=engine,
        extend_existing=True,
    )



# ============================================================
#  SUMMARY VIEW ORM MODELS (CLEANED — NO keep_existing=True)
# ============================================================

class VSummaryDevices(Base):
    __table__ = Table(
        "v_summary_devices",
        Base.metadata,
        Column("network", Text, primary_key=True),
        Column("role", Text, primary_key=True),
        Column("model", Text, primary_key=True),
        Column("device_count", Integer),
        autoload_with=engine,
        extend_existing=True,
    )

class VSummaryPorts(Base):
    __table__ = Table(
        "v_summary_ports",
        Base.metadata,
        Column("port_type", Text, primary_key=True),
        Column("port_speed", Text, primary_key=True),
        Column("service_status", Text, primary_key=True),
        Column("port_count", Integer),
        autoload_with=engine,
        extend_existing=True,
    )


class VSummaryPortHealth(Base):
    __table__ = Table(
        "v_summary_port_health",
        Base.metadata,
        Column("port_type", Text, primary_key=True),
        Column("port_speed", Text, primary_key=True),
        Column("health_status", Integer, primary_key=True),
        Column("port_count", Integer),
        autoload_with=engine,
        extend_existing=True,
    )


class VSummaryLinks(Base):
    __table__ = Table(
        "v_summary_links",
        Base.metadata,
        Column("link_type", Text, primary_key=True),
        Column("link_count", Integer),
        autoload_with=engine,
        extend_existing=True,
    )


class VSummaryLinksByLocation(Base):
    __table__ = Table(
        "v_summary_links_by_location",
        Base.metadata,
        Column("location", Text, primary_key=True),
        Column("link_type", Text, primary_key=True),
        Column("link_endpoint_count", Integer),
        autoload_with=engine,
        extend_existing=True,
    )

class VSummaryCustomers(Base):
    __table__ = Table(
        "v_summary_customers",
        Base.metadata,
        Column("customer_count", Integer, primary_key=True),
        autoload_with=engine,
        extend_existing=True,
    )


class VSummaryCustomerServices(Base):
    __table__ = Table(
        "v_summary_customer_services",
        Base.metadata,
        Column("customer_id", UUID(as_uuid=True), primary_key=True),
        Column("customer_name", Text),
        Column("account_id", Text),
        Column("service_count", Integer),
        autoload_with=engine,
        extend_existing=True,
    )


class VSummaryServices(Base):
    __table__ = Table(
        "v_summary_services",
        Base.metadata,
        Column("service_type", Text, primary_key=True),
        Column("service_status", Text, primary_key=True),
        Column("service_count", Integer),
        autoload_with=engine,
        extend_existing=True,
    )


class VSummaryConnections(Base):
    __table__ = Table(
        "v_summary_connections",
        Base.metadata,
        Column("connection_status", Text, primary_key=True),
        Column("service_bw", Integer, primary_key=True),
        Column("vrf_name", Text, primary_key=True),
        Column("connection_count", Integer),
        autoload_with=engine,
        extend_existing=True,
    )

# --- Core Models ---
class Customer(Base):
    __tablename__ = 'customers'
    
    customer_id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        server_default=FetchedValue()
    )
    customer_name = Column(String(255), nullable=False)
    account_id = Column(String(50))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Ensure "FabricService" is a string here to avoid initialization timing issues
    services = relationship("FabricService", back_populates="customer", cascade="all, delete-orphan")

class CustomerSummaryView(Base):
    """Mapping for the 'v_customer_summary' database view."""
    __tablename__ = 'v_customer_summary'

    customer_id = Column(UUID(as_uuid=True), primary_key=True)
    customer_name = Column(String(100))
    account_id = Column(String(50))
    service_count = Column(BigInteger)
    fabric_connection_count = Column(BigInteger)
    port_count = Column(BigInteger)
    interface_count = Column(BigInteger)

    def __repr__(self):
        return f"<CustomerSummary(name='{self.customer_name}', connections={self.fabric_connection_count})>"

class FabricService(Base):
    __tablename__ = "fabric_services"

    service_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.customer_id"), nullable=False)

    service_name = Column(String(100), nullable=True)
    service_alias = Column(String(100), nullable=True)
    service_type = Column(String(50), nullable=True)
    service_description = Column(Text, nullable=True)
    route_target = Column(String(50), nullable=True)
    health_status = Column(Integer, default=4)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    customer = relationship("Customer", back_populates="services")

class NetworkSummary(Base):
    __tablename__ = "v_network_summary"

    network = Column(String)
    location_id = Column(UUID)
    location_code = Column(String)
    short_name = Column(String)
    location_name = Column(String)
    city = Column(String)
    state = Column(String)
    country = Column(String)

    __table_args__ = (
        PrimaryKeyConstraint("network", "location_id"),
    )

class LocationInfo(Base):
    __tablename__ = "location_info"
    __table_args__ = {"extend_existing": True}

    location_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_code = Column(String(20), nullable=False)
    short_name = Column(String(50))
    location_name = Column(String(100), nullable=False)
    address = Column(String(200))
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    postal_code = Column(String(20))
    country = Column(String(50), nullable=False)
    timezone_name = Column(String(50))
    timezone_offset = Column(Integer)
    latitude = Column(Numeric(9, 6))
    longitude = Column(Numeric(9, 6))
    availability_zone = Column(String(50))

    devices = relationship("Device", back_populates="location_ref")
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

class Device(Base):
    __tablename__ = "devices"

    device_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_name = Column(String(100), unique=True, nullable=False)
    device_role = Column(String(50), nullable=False)
    device_model = Column(String(100))
    device_vendor = Column(String(100), nullable=False)

    # ✅ NEW (structured OS version)
    nos_version = Column(String(100))

    availability_zone = Column(String(100))
    lifecycle_status = Column(String(50), default="Active")
    planning_status = Column(String(50), default="Planned")
    health_status = Column(Integer, default=4)

    network = Column(Text)

    # ⚠️ LEGACY FIELD (keep temporarily for compatibility)
    location = Column(Text)

    # ✅ NEW (canonical relationship)
    location_id = Column(UUID(as_uuid=True), ForeignKey("location_info.location_id"), nullable=False)

    floor = Column(Text)
    aisle = Column(Text)
    rack = Column(Text)

    device_description = Column(Text)

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # ✅ Relationships
    ports = relationship("Port", back_populates="device", cascade="all, delete-orphan")

    # Optional: add relationship to location_info
    location_ref = relationship("LocationInfo", back_populates="devices")

class RoutingPolicy(Base):
    __tablename__ = "routing_policies"

    # --- PRIMARY IDENTIFIERS ---
    # One row now equals one Policy Term, so term_id is the Primary Key.
    term_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    # Groups all terms under a single policy
    policy_id = Column(UUID(as_uuid=True), nullable=False)

    fabric_service_id = Column(
        UUID(as_uuid=True),
        ForeignKey("fabric_services.service_id"),
        nullable=True
    )

    # --- POLICY METADATA ---
    policy_name = Column(String(200), nullable=False)
    direction = Column(String(50), nullable=False)  # 'Import' or 'Export'

    # --- TERM METADATA ---
    sequence = Column(Integer, nullable=False)      # Replaces policy_sequence
    term_name = Column(String(200), nullable=False) # Replaces prefix_id_name

    # --- ROUTING LOGIC ---
    # Replaces ip_prefix and ip_mask. Stores CIDRs natively (e.g., ["10.0.0.0/8"])
    prefixes = Column(ARRAY(String), nullable=False, default=list)

    match_type = Column(String(50), nullable=False) # 'Exact', 'All', 'Upto', 'Auto-Summary'
    upto_mask = Column(Integer, nullable=True)      # Stores the 'le' value (e.g., 32)
    action = Column(String(50), nullable=False)     # 'Advertise' or 'Deny'

    # --- BGP ATTRIBUTES ---
    med = Column(Integer, nullable=True)            # Converted to Integer
    local_pref = Column(Integer, nullable=True)     # Converted to Integer
    as_prepend = Column(Integer, nullable=True)     # New Attribute
    communities = Column(ARRAY(String), nullable=True)

    # --- TIMESTAMP AUDIT ---
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())   

class BGPNeighbor(Base):
    __tablename__ = "bgp_neighbors"

    bgp_neighbor_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    interface_id = Column(
        UUID(as_uuid=True),
        ForeignKey("interface.interface_id"),
        nullable=True
    )

    neighbor_ip = Column(INET, nullable=False)
    local_ip = Column(INET)

    remote_asn = Column(Integer, nullable=False)
    local_asn = Column(Integer)

    session_type = Column(String(50))
    session_state = Column(String(50))
    description = Column(String(200))
    community = Column(String(200))

    # New fields
    import_policy = Column(ARRAY(String), nullable=True)
    export_policy = Column(ARRAY(String), nullable=True)

    multihop = Column(Integer)

    auth = Column(Boolean, nullable=False, server_default="false")
    auth_password = Column(String(200))

    bfd = Column(Boolean, nullable=False, server_default="false")
    bfd_interval = Column(Integer, nullable=False, server_default="500")
    bfd_multiple = Column(Integer, nullable=False, server_default="3")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class StaticRoute(Base):
    __tablename__ = "static_routes"

    # Primary key with Postgres-side UUID generation
    route_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    # Link to fabric connection or None for router-base routes
    interface_id = Column(
        UUID(as_uuid=True),
        ForeignKey("interface.interface_id"),
        nullable=True
    )

    # IPv4 or IPv6 prefix and mask
    ip_prefix = Column(INET, nullable=False)
    prefix_mask = Column(Integer, nullable=False)

    # Next-hop IPv4 or IPv6 address
    next_hop_ip = Column(INET, nullable=False)

    metric = Column(Integer, nullable=True)
    community = Column(String(200), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class IPInterface(Base):
    __tablename__ = "ip_interfaces"

    ip_address_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    interface_id = Column(
        UUID(as_uuid=True),
        nullable=False
    )

    lumen_ip_address = Column(INET, nullable=False)
    customer_ip_address = Column(INET, nullable=False)

    network_mask_cidr = Column(Integer, nullable=False)
    bring_your_own_ip = Column(Boolean, nullable=False)

class Port(Base):
    __tablename__ = "ports"

    # Use server_default so Postgres handles ID generation, as_uuid=True for Python objects
    port_id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        server_default=func.gen_random_uuid()
    )
    
    mac_address = Column(String(17))
    port_name = Column(String(50), nullable=False)
    port_speed = Column(String(50), nullable=False)
    
    # Updated to use Postgres UUID dialect specifically
    device_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("devices.device_id", ondelete="CASCADE"), 
        nullable=False
    )
    
    port_description = Column(String(255))
    port_optic = Column(String(100))
    port_tagging = Column(String(100))
    port_cktid = Column(String(100))
    
    # FIX: Use UUID(as_uuid=True) here to prevent the .replace() attribute error
    customer_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("customers.customer_id"), 
        nullable=True
    )
    
    port_service_status = Column(String(50), nullable=True)
    port_type = Column(String(50), nullable=False)
    port_health_status = Column(Integer)
    
    # Missing from previous snippet but present in DB
    admin_status = Column(String(50), nullable=False, server_default='up')
    oper_status = Column(String(50), nullable=False, server_default='down')
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    device = relationship("Device", back_populates="ports")
    
class VDevicePorts(Base):
    __tablename__ = 'v_device_ports'
    __table_args__ = {'info': {'is_view': True}}

    device_id = Column(UUID(as_uuid=True))
    device_name = Column(String(100))
    device_health_status = Column(Integer)
    availability_zone = Column(String)

    port_id = Column(UUID(as_uuid=True))
    port_name = Column(String(50))
    port_speed = Column(String(50))
    port_type = Column(String(50))
    port_service_status = Column(String(50))
    port_health_status = Column(Integer)

    mac_address = Column(String(17))
    port_optic = Column(String(100))
    port_tagging = Column(String(100))
    port_cktid = Column(String(100))

    lag_parent_id = Column(UUID(as_uuid=True))
    customer_id = Column(UUID(as_uuid=True))

    port_created_at = Column(DateTime(timezone=True))
    port_updated_at = Column(DateTime(timezone=True))

    __mapper_args__ = {
        "primary_key": [device_id, port_id]
    }

    def __repr__(self):
        return (
            f"<VDevicePorts(device_id={self.device_id}, device_name={self.device_name}, "
            f"port_id={self.port_id}, port_name={self.port_name})>"
        )

class FabricConnection(Base):
    __tablename__ = 'fabric_connections'

    connection_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    connection_name = Column(String(100), nullable=True)

    service_id = Column(UUID(as_uuid=True), ForeignKey('fabric_services.service_id', ondelete="CASCADE"), nullable=False)

    connector_a_id = Column(UUID(as_uuid=True), nullable=True)
    connector_b_id = Column(UUID(as_uuid=True), nullable=True)

    connector_a_table = Column(Text, nullable=True)
    connector_b_table = Column(Text, nullable=True)

    # Correct single definition
    connection_status = Column(String(100), nullable=True)

    vrf_name = Column(String(50), nullable=True)
    service_bw = Column(Integer, nullable=True)
    s_vlan = Column(Integer, nullable=True)
    c_vlan_list = Column(String(100), nullable=True)

    health_status = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Interface(Base):
    __tablename__ = "interface"

    interface_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    port_id = Column(UUID(as_uuid=True), nullable=True)
    service_id = Column(UUID(as_uuid=True), nullable=True)
    
    ckt_id = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)

    interface_name = Column(String(100), nullable=True)
    interface_type = Column(String(50), nullable=True)

    svlan_id = Column(Integer, nullable=True)
    cvlan_list = Column(String(100), nullable=True)

    dhcp_relay_enabled = Column(Boolean, nullable=False, server_default="true")

    service_bw_mbps = Column(BigInteger, nullable=True)
    status = Column(String(50), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

class PatchPanel(Base):
    __tablename__ = "patch_panels"
    __table_args__ = {"extend_existing": True}

    port_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True))
    port_number = Column(Integer)
    local_port = Column(UUID(as_uuid=True))
    remote_port = Column(UUID(as_uuid=True))
    description = Column(String(255))

    port_name = Column(String(50))
    connector_type = Column(String(50))
    fiber_mode = Column(String(50))
    status = Column(String(50))

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

class CrossConnect(Base):
    __tablename__ = "cross_connects"
    __table_args__ = (
        UniqueConstraint('local_port_id', 'remote_port_id', name='uq_cross_connect_endpoints'),
        {"extend_existing": True},
    )

    connect_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    internal_circuit_id = Column(String(100), unique=True, nullable=False)

    local_port_id = Column(UUID(as_uuid=True), nullable=False)
    remote_port_id = Column(UUID(as_uuid=True))

    connect_type = Column(String(50), nullable=False)
    service_description = Column(String(255))
    loa_number = Column(String(100))

    mrc = Column(Numeric(10, 2), default=0.00)
    nrc = Column(Numeric(10, 2), default=0.00)

    status = Column(String(20), nullable=False)
    activation_date = Column(Date)

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

class PowerOption(Base):
    __tablename__ = "power_options"
    __table_args__ = {"extend_existing": True}

    power_source_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    power_type = Column(String(50), nullable=False)
    voltage = Column(String(50), nullable=False)
    description = Column(String(255))

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

class HardwareSpecs(Base):
    __tablename__ = "hardware_specs"
    __table_args__ = {"extend_existing": True}

    hardware_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    model_name = Column(String(100), nullable=False)
    manufacturer = Column(String(100))

    weight_kg = Column(Numeric(6, 2))
    height_mm = Column(Numeric(6, 2))
    width_mm = Column(Numeric(6, 2))
    depth_mm = Column(Numeric(6, 2))

    power_source_id = Column(UUID(as_uuid=True), ForeignKey('power_options.power_source_id'), nullable=False)
    power_rating_w = Column(Numeric(7, 2))
    airflow_direction = Column(String(50))
    typical_environment = Column(String(255))
    max_environment_tempc = Column(Numeric(4, 2))
    min_environment_tempc = Column(Numeric(4, 2))

    nebs_level = Column(String(50))
    nebs_status = Column(Boolean)
    certification_data = Column(Text)

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

class HardwareDocument(Base):
    __tablename__ = "hardware_documents"
    __table_args__ = {"extend_existing": True}

    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hardware_id = Column(UUID(as_uuid=True), ForeignKey('hardware_specs.hardware_id'), nullable=False)

    document_type = Column(String(50))
    document_name = Column(String(255), nullable=False)
    storage_path = Column(String(512), nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    hardware_spec = relationship("HardwareSpecs", backref="documents")

class LRICCostModel(Base):
    __tablename__ = "lric_cost_model"
    __table_args__ = (
        CheckConstraint('lric_fill >= 0 AND lric_fill <= 100', name='lric_cost_model_lric_fill_check'),
        {"extend_existing": True},
    )

    cost_model_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), nullable=False)

    model_type = Column(String(50), nullable=False)
    description = Column(String(255))

    base_cost = Column(Numeric(15, 4), nullable=False)
    min_fill = Column(Integer)
    lric_fill = Column(Integer)

    type = Column(String(50))
    min_level = Column(Numeric(15, 4))
    level = Column(Numeric(15, 4))

    calculated_lric_cost = Column(
        Numeric(15, 4),
        Computed("(base_cost * (lric_fill::numeric / 100.0))", persisted=True)
    )

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

class DeviceLocation(Base):
    __tablename__ = "device_location"
    __table_args__ = {"extend_existing": True}

    device_id = Column(UUID(as_uuid=True), ForeignKey('devices.device_id'), primary_key=True)

    clli = Column(String(8))
    location = Column(String(100), nullable=False, default='Unknown Location')

    floor_number = Column(String(10))
    rack_identifier = Column(String(20), nullable=False)
    aisle_identifier = Column(String(20))

    rack_start_ru = Column(Integer)
    ru_height = Column(Integer)

    description = Column(String(255))
    date_added = Column(DateTime(timezone=False), default=func.now())

class NetworkLink(Base):
    __tablename__ = "topology_links"
    __table_args__ = {"extend_existing": True}

    link_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    endpoint_a = Column(UUID(as_uuid=True), nullable=False)
    endpoint_a_type = Column(String(20), nullable=False)

    endpoint_b = Column(UUID(as_uuid=True), nullable=False)
    endpoint_b_type = Column(String(20), nullable=False)

    link_type = Column(String(30), nullable=False)
    channel = Column(Integer)
    frequency = Column(Numeric(12))
    description = Column(String(500))

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

class VNetworkLinksLAG(Base):
    __tablename__ = "v_network_links_lag"
    __table_args__ = {"extend_existing": True}

    link_id = Column(UUID(as_uuid=True), primary_key=True)

    link_type = Column(String(30))
    description = Column(String(512))
    channel = Column(Integer)
    frequency = Column(Numeric(12))

    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))

    a_port_id = Column(UUID(as_uuid=True))
    a_port_name = Column(String(50))
    a_port_type = Column(String(50))
    a_port_speed = Column(String(50))
    a_port_health_status = Column(String(50))

    b_port_id = Column(UUID(as_uuid=True))
    b_port_name = Column(String(50))
    b_port_type = Column(String(50))
    b_port_speed = Column(String(50))
    b_port_health_status = Column(String(50))

    device_id = Column(UUID(as_uuid=True))
    device_name = Column(String(100))
    device_role = Column(String(50))
    device_vendor = Column(String(100))
    device_health_status = Column(String(100))
    device_location = Column(String(100))


class VNetworkDashboard(Base):
    __tablename__ = "v_network_dashboard"

    network = Column(Text, primary_key=True)
    pop_location = Column(String(50), primary_key=True)
    city = Column(String(100))
    latitude = Column(Numeric(9, 6))
    longitude = Column(Numeric(9, 6))
    total_devices = Column(Integer)
    role_distribution = Column(JSON)
    link_distribution = Column(JSON)

class VNetworkLinksDetail(Base):
    __tablename__ = "v_network_links_detail"

    link_id = Column(UUID(as_uuid=True), primary_key=True)
    link_type = Column(String(30))
    description = Column(String(500))
    channel = Column(Integer)
    frequency = Column(Numeric(12, 0))
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    link_health_status = Column(Integer)

    a_port_id = Column(UUID(as_uuid=True))
    a_port_name = Column(String(50))
    a_port_speed = Column(String(50))
    a_port_type = Column(String(50))
    a_port_service_status = Column(String(50))
    a_port_health_status = Column(Integer)

    a_device_id = Column(UUID(as_uuid=True))
    a_device_name = Column(String(100))
    a_device_role = Column(String(50))
    a_device_vendor = Column(String(100))
    a_device_location = Column(String(50))
    a_device_health_status = Column(Integer)
    a_device_latitude = Column(Numeric(9, 6))
    a_device_longitude = Column(Numeric(9, 6))

    b_port_id = Column(UUID(as_uuid=True))
    b_port_name = Column(String(50))
    b_port_speed = Column(String(50))
    b_port_type = Column(String(50))
    b_port_service_status = Column(String(50))
    b_port_health_status = Column(Integer)

    b_device_id = Column(UUID(as_uuid=True))
    b_device_name = Column(String(100))
    b_device_role = Column(String(50))
    b_device_vendor = Column(String(100))
    b_device_location = Column(String(50))
    b_device_health_status = Column(Integer)
    b_device_latitude = Column(Numeric(9, 6))
    b_device_longitude = Column(Numeric(9, 6))

    a_network = Column(Text)
    b_network = Column(Text)


class ROPChannelMember(Base):
    __tablename__ = "rop_channel_members"
    __table_args__ = (
        UniqueConstraint('rop_link_id', 'channel_id', name='uq_rop_link_channel'),
        {"extend_existing": True},
    )

    rop_member_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    rop_link_id = Column(UUID(as_uuid=True), ForeignKey('network_links.link_id'), nullable=False)

    channel_id = Column(Integer, nullable=False)

    a_side_endpoint_id = Column(UUID(as_uuid=True), nullable=False)
    a_side_endpoint_type = Column(String(50), nullable=False)

    z_side_endpoint_id = Column(UUID(as_uuid=True), nullable=False)
    z_side_endpoint_type = Column(String(50), nullable=False)

    description = Column(String(255))

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
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


# Place this at the absolute bottom of scripts/api_model.py
from sqlalchemy.orm import configure_mappers
configure_mappers()

if __name__ == '__main__':
    if Engine:
        create_database_tables(Engine)
    else:
        print("Database Engine is not available.")