"""
SQLAlchemy models for the Inventory domain.
File: domains/inventory/models.py

Defines the read-only mappings for the aggregated inventory and dashboard views.
"""

from sqlalchemy import Column, String, Integer, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from core.database import Base

# ============================================================
# MASTER SUMMARY VIEWS
# ============================================================

class NetworkSummaryMaster(Base):
    """Mapped to the 'v_network_summary_master' database view."""
    __tablename__ = "v_network_summary_master"
    __table_args__ = {'info': {'is_view': True}, "extend_existing": True}

    unique_id = Column(String, primary_key=True)
    category = Column(String)
    dimension = Column(JSON)
    count_value = Column(Integer)


class NetworkSummaryMasterV2(Base):
    """Mapped to the 'v_network_summary_master_v2' database view."""
    __tablename__ = "v_network_summary_master_v2"
    __table_args__ = {'info': {'is_view': True}, "extend_existing": True}

    unique_id = Column(String, primary_key=True)
    category = Column(String)
    dimension = Column(JSON)
    count_value = Column(Integer)


# ============================================================
# GRANULAR SUMMARY VIEWS (Formerly Table autoloads)
# ============================================================

class VSummaryDevices(Base):
    __tablename__ = "v_summary_devices"
    __table_args__ = {'info': {'is_view': True}, "extend_existing": True}

    network = Column(Text, primary_key=True)
    role = Column(Text, primary_key=True)
    model = Column(Text, primary_key=True)
    device_count = Column(Integer)


class VSummaryPorts(Base):
    __tablename__ = "v_summary_ports"
    __table_args__ = {'info': {'is_view': True}, "extend_existing": True}

    port_type = Column(Text, primary_key=True)
    port_speed = Column(Text, primary_key=True)
    service_status = Column(Text, primary_key=True)
    port_count = Column(Integer)


class VSummaryPortHealth(Base):
    __tablename__ = "v_summary_port_health"
    __table_args__ = {'info': {'is_view': True}, "extend_existing": True}

    port_type = Column(Text, primary_key=True)
    port_speed = Column(Text, primary_key=True)
    health_status = Column(Integer, primary_key=True)
    port_count = Column(Integer)


class VSummaryLinks(Base):
    __tablename__ = "v_summary_links"
    __table_args__ = {'info': {'is_view': True}, "extend_existing": True}

    link_type = Column(Text, primary_key=True)
    link_count = Column(Integer)


class VSummaryLinksByLocation(Base):
    __tablename__ = "v_summary_links_by_location"
    __table_args__ = {'info': {'is_view': True}, "extend_existing": True}

    location = Column(Text, primary_key=True)
    link_type = Column(Text, primary_key=True)
    link_endpoint_count = Column(Integer)


class VSummaryCustomers(Base):
    __tablename__ = "v_summary_customers"
    __table_args__ = {'info': {'is_view': True}, "extend_existing": True}

    customer_count = Column(Integer, primary_key=True)


class VSummaryCustomerServices(Base):
    __tablename__ = "v_summary_customer_services"
    __table_args__ = {'info': {'is_view': True}, "extend_existing": True}

    customer_id = Column(UUID(as_uuid=True), primary_key=True)
    customer_name = Column(Text)
    account_id = Column(Text)
    service_count = Column(Integer)


class VSummaryServices(Base):
    __tablename__ = "v_summary_services"
    __table_args__ = {'info': {'is_view': True}, "extend_existing": True}

    service_type = Column(Text, primary_key=True)
    service_status = Column(Text, primary_key=True)
    service_count = Column(Integer)


class VSummaryConnections(Base):
    __tablename__ = "v_summary_connections"
    __table_args__ = {'info': {'is_view': True}, "extend_existing": True}

    connection_status = Column(Text, primary_key=True)
    service_bw = Column(Integer, primary_key=True)
    vrf_name = Column(Text, primary_key=True)
    connection_count = Column(Integer)
    
# domains/inventory/models.py

from sqlalchemy import Column, String, Text, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

class InventoryAsset(Base):
    """
    Physical hardware and asset tracking for the network digital twin.
    Maps to the inventory_assets table.
    """
    __tablename__ = 'inventory_assets'

    asset_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    vendor = Column(String(100), nullable=False, doc="Name of the hardware manufacturer")
    vendor_id = Column(String(100), nullable=False, doc="Manufacturer part number or external vendor identifier")
    lumen_id = Column(String(100), unique=True, nullable=False, doc="Internal corporate asset tracking tag")
    
    description = Column(Text, doc="Detailed description of the hardware asset")
    
    # Financial Tracking
    list_price = Column(Numeric(12, 2), default=0.00, doc="MSRP or base catalog price")
    discount = Column(Numeric(5, 2), default=0.00, doc="Applied percentage or flat discount")
    lumen_price = Column(Numeric(12, 2), default=0.00, doc="Final calculated internal cost")
    
    # Lifecycle Auditing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())