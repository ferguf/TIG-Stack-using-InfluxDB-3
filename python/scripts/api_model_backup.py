"""
File Name: 'api_model_backup.py'
Description: Exact physical table definitions for schema restoration. 
Verification: Validated against provided IPv6, PatchPanel, and LocationInfo snippets.
"""

import uuid
from sqlalchemy import (
    Column, String, Numeric, Integer, ForeignKey, DateTime,
    Text, BigInteger, Boolean, Date, func, UniqueConstraint,
    CheckConstraint, Computed, Table, TIMESTAMP, text
)
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB, CIDR
from sqlalchemy.orm import relationship
from scripts.api_session import Base

# --- Physical Infrastructure ---

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

# --- Inventory & Locations ---

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
    customer_id = Column(UUID(as_uuid=True), nullable=True) # Relationship omitted for backup file safety
    port_service_status = Column(String(50), nullable=True)
    port_type = Column(String(50), nullable=False)
    port_health_status = Column(Integer)
    device = relationship("Device", back_populates="ports")

# --- Services & IP Management ---

class Customer(Base):
    __tablename__ = 'customers'
    customer_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_name = Column(String(255), nullable=False)
    account_id = Column(String(50))
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

class FabricService(Base):
    __tablename__ = "fabric_services"
    service_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.customer_id"), nullable=False)
    service_name = Column(String(100))
    service_alias = Column(String(100))
    service_type = Column(String(50))
    service_description = Column(Text)
    route_target = Column(String(50))
    health_status = Column(Integer, default=4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class FabricConnection(Base):
    __tablename__ = 'fabric_connections'
    connection_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    connection_name = Column(String(100))
    service_id = Column(UUID(as_uuid=True), ForeignKey('fabric_services.service_id', ondelete="CASCADE"), nullable=False)
    connector_a_id = Column(UUID(as_uuid=True))
    connector_b_id = Column(UUID(as_uuid=True))
    connector_a_table = Column(Text)
    connector_b_table = Column(Text)
    connection_status = Column(String(100))
    vrf_name = Column(String(50))
    service_bw = Column(Integer)
    s_vlan = Column(Integer)
    c_vlan_list = Column(String(100))
    health_status = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Interface(Base):
    __tablename__ = "interface"
    interface_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True))
    port_id = Column(UUID(as_uuid=True))
    ckt_id = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    interface_name = Column(String(100), nullable=False)
    interface_type = Column(String(50), nullable=False)
    svlan_id = Column(Integer)
    cvlan_id = Column(Integer)
    dhcp_relay_enabled = Column(Boolean, nullable=False, default=False)
    service_bw_mbps = Column(BigInteger)
    status = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    __table_args__ = (UniqueConstraint('port_id', 'interface_name', name='uq_interface_on_port'),)

class IPv4Interface(Base):
    __tablename__ = "ipv4_interfaces"
    ipv4_address_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interface_id = Column(UUID(as_uuid=True), ForeignKey('interface.interface_id', ondelete='CASCADE'), nullable=False)
    lumen_ip_address = Column(INET, nullable=False)
    customer_ip_address = Column(INET, nullable=False)
    network_mask_cidr = Column(Integer, nullable=False)
    bring_your_own_ip = Column(Boolean, nullable=False, default=False)

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

# --- Hardware & Topology ---

class PowerOption(Base):
    __tablename__ = "power_options"
    power_source_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    power_type = Column(String(50), nullable=False)
    voltage = Column(String(50), nullable=False)
    description = Column(String(255))

class HardwareSpecs(Base):
    __tablename__ = "hardware_specs"
    hardware_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(100), nullable=False)
    manufacturer = Column(String(100))
    power_source_id = Column(UUID(as_uuid=True), ForeignKey('power_options.power_source_id'), nullable=False)
    nebs_level = Column(String(50))

class HardwareDocument(Base):
    __tablename__ = "hardware_documents"
    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hardware_id = Column(UUID(as_uuid=True), ForeignKey('hardware_specs.hardware_id'), nullable=False)
    document_name = Column(String(255), nullable=False)
    storage_path = Column(String(512), nullable=False)

class LRICCostModel(Base):
    __tablename__ = "lric_cost_model"
    cost_model_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    base_cost = Column(Numeric(15, 4), nullable=False)
    lric_fill = Column(Integer)
    calculated_lric_cost = Column(Numeric(15, 4), Computed("(base_cost * (lric_fill::numeric / 100.0))", persisted=True))

class NetworkLink(Base):
    __tablename__ = "topology_links"
    link_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    endpoint_a = Column(UUID(as_uuid=True), nullable=False)
    endpoint_b = Column(UUID(as_uuid=True), nullable=False)
    link_type = Column(String(30), nullable=False)
    description = Column(String(500))

class RouteVision(Base):
    __tablename__ = "routeVision"
    route_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fabric_service_id = Column(UUID(as_uuid=True), ForeignKey("fabric_services.service_id"), nullable=False)
    fabric_connection_id = Column(UUID(as_uuid=True), ForeignKey("fabric_connections.connection_id"))
    ip_prefix = Column(CIDR, nullable=False)
    route_type = Column(String(20), nullable=False)
    ip_next_hop = Column(String(200), nullable=False)
    route_status = Column(String(20), nullable=False, server_default="Active")
    bgp_asn = Column(Integer)
    bgp_as_path = Column(String(200))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))