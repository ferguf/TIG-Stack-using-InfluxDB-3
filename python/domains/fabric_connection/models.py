"""
SQLAlchemy model for Fabric Connections.
File: domains/fabric_connection/models.py
"""
from sqlalchemy import Column, String, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from core.database import Base

class FabricConnection(Base):
    """
    Physical table for storing Fabric Connections.
    """
    __tablename__ = "fabric_connections"
    __table_args__ = {"extend_existing": True}

    connection_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id = Column(UUID(as_uuid=True), ForeignKey("fabric_services.service_id"), nullable=False)
    
    connection_name = Column(String(100), nullable=True)
    connection_type = Column(String(50), nullable=True)
    status = Column(String(50), nullable=True)
    
    # Relationships
    service = relationship("FabricService", backref="connections")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)