"""
SQLAlchemy models for the Ports domain.
File: domains/port/models.py
"""
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.database import Base

class Port(Base):
    __tablename__ = "ports"
    __table_args__ = {"extend_existing": True}

    port_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    mac_address = Column(String(17))
    port_name = Column(String(50), nullable=False)
    port_speed = Column(String(50), nullable=False)
    
    # Foreign Keys
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.device_id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.customer_id"), nullable=True)
    
    port_description = Column(String(255))
    port_optic = Column(String(100))
    port_tagging = Column(String(100))
    port_cktid = Column(String(100))
    port_service_status = Column(String(50), nullable=True)
    port_type = Column(String(50), nullable=False)
    port_health_status = Column(Integer)
    admin_status = Column(String(50), nullable=False, server_default='up')
    oper_status = Column(String(50), nullable=False, server_default='down')
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # ✅ THE DDD FIX: Inject `.ports` into the Device model
    device = relationship("Device", backref="ports")

class VDevicePorts(Base):
    """
    SQLAlchemy model mapped to the 'v_device_ports' database view.
    Provides pre-joined device and port telemetry.
    Note: Views should be treated as read-only.
    """
    __tablename__ = 'v_device_ports'
    __table_args__ = {'info': {'is_view': True}, "extend_existing": True}

    # Device side (Joined)
    device_id = Column(UUID(as_uuid=True))
    device_name = Column(String(100))
    device_health_status = Column(Integer)
    availability_zone = Column(String)

    # Port side
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

    # Define composite primary key so SQLAlchemy can map the view properly
    __mapper_args__ = {
        "primary_key": [device_id, port_id]
    }

    def __repr__(self):
        return (
            f"<VDevicePorts(device_id={self.device_id}, device_name={self.device_name}, "
            f"port_id={self.port_id}, port_name={self.port_name})>"
        )