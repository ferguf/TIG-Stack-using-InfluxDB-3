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

# Import the REAL Base and engine from api_session
from scripts.api_session import Base, engine

from sqlalchemy import (
    JSON, Column, String, Numeric, Integer, ForeignKey, DateTime,
    Text, BigInteger, Boolean, Date, func, UniqueConstraint,
    CheckConstraint, Computed, Table,TIMESTAMP,text
)
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB,CIDR
from sqlalchemy.orm import relationship

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


from sqlalchemy import Column, String, DateTime, func, FetchedValue, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship

class RouteVision(Base):
    """
    Model for the route_vision table. 
    Handles BGP routing data and network prefixes.
    """
    __tablename__ = 'route_vision'

    route_id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        server_default=FetchedValue()
    )
    
    # Foreign Keys
    fabric_service_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('fabric_services.service_id'), 
        nullable=False
    )
    fabric_connection_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('fabric_connections.connection_id')
    )

    # Network Attributes
    # INET handles cidr validation/storage in Postgres via SQLAlchemy
    ip_prefix = Column(INET, nullable=False)
    route_type = Column(String(20), nullable=False)
    ip_next_hop = Column(String(200), nullable=False)
    route_status = Column(
        String(20), 
        nullable=False, 
        server_default=FetchedValue()
    )
    
    # BGP Specifics
    route_target = Column(String(100))
    route_distinguisher = Column(String(200))
    bgp_asn = Column(Integer)
    bgp_as_path = Column(String(200))
    bgp_community = Column(String(200))

    # Audit Timestamps
    # Database handles defaults via CURRENT_TIMESTAMP
    created_at = Column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=FetchedValue()
    )
    updated_at = Column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=FetchedValue(), 
        onupdate=func.now()
    )

    # Relationships
    fabric_service = relationship("FabricService", back_populates="routes")


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
        Column("port_type", Text, primary_key=True, keep_existing=True),
        Column("port_speed", Text, primary_key=True, keep_existing=True),
        Column("service_status", Text, primary_key=True, keep_existing=True),
        Column("port_count", Integer),
        autoload_with=engine,
        extend_existing=True,
    )


class VSummaryPortHealth(Base):
    __table__ = Table(
        "v_summary_port_health",
        Base.metadata,
        Column("port_type", Text, primary_key=True, keep_existing=True),
        Column("port_speed", Text, primary_key=True, keep_existing=True),
        Column("health_status", Integer, primary_key=True, keep_existing=True),
        Column("port_count", Integer),
        autoload_with=engine,
        extend_existing=True,
    )


class VSummaryLinks(Base):
    __table__ = Table(
        "v_summary_links",
        Base.metadata,
        Column("link_type", Text, primary_key=True, keep_existing=True),
        Column("link_count", Integer),
        autoload_with=engine,
        extend_existing=True,
    )


class VSummaryLinksByLocation(Base):
    __table__ = Table(
        "v_summary_links_by_location",
        Base.metadata,
        Column("location", Text, primary_key=True, keep_existing=True),
        Column("link_type", Text, primary_key=True, keep_existing=True),
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
    customer_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_name = Column(String(255), nullable=False)
    account_id = Column(String(50))
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

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


class Device(Base):
    __tablename__ = "devices"

    device_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_name = Column(String(100), unique=True, nullable=False)
    device_role = Column(String(50), nullable=False)
    device_model = Column(String(100))
    device_vendor = Column(String(100), nullable=False)
    availability_zone = Column(String(100))
    lifecycle_status = Column(String(50), default="Active")
    planning_status = Column(String(50), default="Planned")
    health_status = Column(Integer, default=4)
    network = Column(Text)
    location = Column(Text)
    floor = Column(Text)
    aisle = Column(Text)
    rack = Column(Text)
    device_description = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    ports = relationship("Port", back_populates="device", cascade="all, delete-orphan")


class Port(Base):
    __tablename__ = "ports"

    port_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mac_address = Column(String(17))
    port_name = Column(String(50), nullable=False)
    port_speed = Column(String(50), nullable=False)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.device_id", ondelete="CASCADE"), nullable=False)
    port_description = Column(String(255))
    port_optic = Column(String(100))
    port_tagging = Column(String(100))
    port_cktid = Column(String(100))
    customer_id = Column(UUID, ForeignKey("customers.customer_id"), nullable=True)
    port_service_status = Column(String(50), nullable=True)
    port_type = Column(String(50), nullable=False)
    port_health_status = Column(Integer)

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
    physical_structure = Column(String(20))
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

    interface_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), nullable=True)
    port_id = Column(UUID(as_uuid=True), nullable=True)

    ckt_id = Column(String(100), unique=True, nullable=False)
    description = Column(Text)

    interface_name = Column(String(100), nullable=False)
    interface_type = Column(String(50), nullable=False)

    svlan_id = Column(Integer)
    cvlan_id = Column(Integer, nullable=True)
    dhcp_relay_enabled = Column(Boolean, nullable=False, default=False)

    service_bw_mbps = Column(BigInteger, nullable=True)
    status = Column(String(50), nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    ipv4_configs = relationship("IPv4Interface", back_populates="interface")
    ipv6_configs = relationship("IPv6Interface", back_populates="interface")

    __table_args__ = (
        UniqueConstraint('port_id', 'interface_name', name='uq_interface_on_port'),
    )


class IPv4Interface(Base):
    __tablename__ = "ipv4_interfaces"

    ipv4_address_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interface_id = Column(UUID(as_uuid=True), ForeignKey('interface.interface_id', ondelete='CASCADE'), nullable=False)

    lumen_ip_address = Column(INET, nullable=False)
    customer_ip_address = Column(INET, nullable=False)
    network_mask_cidr = Column(Integer, nullable=False)
    bring_your_own_ip = Column(Boolean, nullable=False, default=False)

    interface = relationship("Interface", back_populates="ipv4_configs")

    __table_args__ = (
        UniqueConstraint('interface_id', 'lumen_ip_address', 'customer_ip_address', name='uq_ipv4_assignment'),
        CheckConstraint('network_mask_cidr BETWEEN 1 AND 31', name='chk_ipv4_cidr'),
    )


class IPv6Interface(Base):
    __tablename__ = "ipv6_interfaces"

    ipv6_address_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interface_id = Column(UUID(as_uuid=True), ForeignKey('interface.interface_id', ondelete='CASCADE'), nullable=False)

    lumen_ip_address = Column(INET, nullable=False)
    customer_ip_address = Column(INET, nullable=False)
    network_mask_cidr = Column(Integer, nullable=False)
    bring_your_own_ip = Column(Boolean, nullable=False, default=False)

    next_hop_address = Column(INET)
    metric = Column(Integer)

    interface = relationship("Interface", back_populates="ipv6_configs")

    __table_args__ = (
        UniqueConstraint('interface_id', 'lumen_ip_address', 'customer_ip_address', name='uq_ipv6_assignment'),
        CheckConstraint('network_mask_cidr BETWEEN 1 AND 128', name='chk_ipv6_cidr'),
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
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())


if __name__ == '__main__':
    if Engine:
        create_database_tables(Engine)
    else:
        print("Database Engine is not available.")