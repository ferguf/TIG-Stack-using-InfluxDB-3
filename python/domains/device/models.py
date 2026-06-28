"""
SQLAlchemy models for the Device domain.
File: domains/device/models.py
"""
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from core.database import Base

class Device(Base):
    __tablename__ = "devices"
    __table_args__ = {"extend_existing": True}

    device_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_name = Column(String(100), unique=True, nullable=False)
    device_role = Column(String(50), nullable=False)
    device_model = Column(String(100))
    device_vendor = Column(String(100), nullable=False)
    nos_version = Column(String(100))
    availability_zone = Column(String(100))
    lifecycle_status = Column(String(50), default="Active")
    planning_status = Column(String(50), default="Planned")
    health_status = Column(Integer, default=4)
    network = Column(Text)
    location = Column(Text) # Legacy string

    # Foreign Key to Location
    location_id = Column(UUID(as_uuid=True), ForeignKey("location_info.location_id"), nullable=False)

    floor = Column(Text)
    aisle = Column(Text)
    rack = Column(Text)
    device_description = Column(Text)

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # ✅ THE DDD FIX: Use `backref` instead of `back_populates`.
    # This tells SQLAlchemy to automatically create the `.devices` property on LocationInfo!
    location_info = relationship("LocationInfo", backref="devices")
    
