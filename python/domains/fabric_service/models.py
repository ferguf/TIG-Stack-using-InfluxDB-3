"""
SQLAlchemy models for the Fabric Services domain.
File: domains/fabric_service/models.py

Defines the physical table structure for fabric services and 
the read-only mapping for the enriched service detail view.
"""
from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

# Centralized base from your Vertical Slice architecture
from core.database import Base


class FabricService(Base):
    """
    Physical table for storing Core Fabric Services.
    """
    __tablename__ = "fabric_services"
    __table_args__ = {"extend_existing": True}

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

    # Use string-based relationship to avoid circular imports with the Customers domain
    customer = relationship("Customer", backref="services")


class FabricServiceDetail(Base):
    """
    SQLAlchemy model mapped to the 'v_fabric_service_detail' database view.
    Provides pre-joined service telemetry (connections, interfaces, ports).
    Note: Views should be treated as read-only.
    """
    __tablename__ = "v_fabric_service_detail"
    __table_args__ = {'info': {'is_view': True}, "schema": "public", "extend_existing": True}

    # Core service fields
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

    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))

    # JSONB nested objects aggregated from related tables
    fabric_connections = Column(JSONB)
    fabric_ports = Column(JSONB)
    fabric_interfaces = Column(JSONB)    
    cloud_interconnects = Column(JSONB)