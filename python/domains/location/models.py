from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from core.database import Base 

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

