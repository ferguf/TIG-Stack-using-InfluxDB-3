from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

# Aligning with your main architecture imports
from core.database import Base

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

class VNetworkLinksDetail(Base):
    __tablename__ = "v_network_links_detail"
    __table_args__ = {"extend_existing": True}

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

    a_network = Column(String)
    b_network = Column(String)

class ROPChannelMember(Base):
    __tablename__ = "rop_channel_members"
    __table_args__ = (
        UniqueConstraint('rop_link_id', 'channel_id', name='uq_rop_link_channel'),
        {"extend_existing": True},
    )

    rop_member_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rop_link_id = Column(UUID(as_uuid=True), ForeignKey('topology_links.link_id'), nullable=False)
    channel_id = Column(Integer, nullable=False)

    a_side_endpoint_id = Column(UUID(as_uuid=True), nullable=False)
    a_side_endpoint_type = Column(String(50), nullable=False)

    z_side_endpoint_id = Column(UUID(as_uuid=True), nullable=False)
    z_side_endpoint_type = Column(String(50), nullable=False)

    description = Column(String(255))

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())