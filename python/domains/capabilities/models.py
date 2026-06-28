# domains/capabilities/models.py

from sqlalchemy import Column, String, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# --- Master Reference Tables ---

class RefSpeed(Base):
    __tablename__ = 'capabilities_ref_speeds'
    
    speed_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    speed_value = Column(String(20), unique=True, nullable=False)
    is_fabric_port_capable = Column(Boolean, default=False)
    is_service_capable = Column(Boolean, default=True)


class RefOptic(Base):
    __tablename__ = 'capabilities_ref_optics'
    
    optic_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    optic_name = Column(String(50), unique=True, nullable=False)
    form_factor = Column(String(50))


class RefPersonality(Base):
    __tablename__ = 'capabilities_ref_personalities'
    
    personality_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    personality_name = Column(String(50), unique=True, nullable=False)


class RefService(Base):
    __tablename__ = 'capabilities_ref_services'
    
    service_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    service_name = Column(String(50), unique=True, nullable=False)
    layer = Column(String(10))


# --- Hardware Profiles & Assignments ---

class HardwareProfile(Base):
    __tablename__ = 'capabilities_hardware_profiles'
    
    profile_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    device_role = Column(String(50), nullable=False)
    device_model = Column(String(100), nullable=False)
    
    # Relationships for eager loading if needed
    ports = relationship("ProfilePort", backref="profile", cascade="all, delete-orphan")
    personalities = relationship("ProfilePersonality", backref="profile", cascade="all, delete-orphan")
    services = relationship("ProfileService", backref="profile", cascade="all, delete-orphan")


class ProfilePort(Base):
    __tablename__ = 'capabilities_profile_ports'
    
    capability_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    profile_id = Column(UUID(as_uuid=True), ForeignKey('capabilities_hardware_profiles.profile_id', ondelete='CASCADE'), nullable=False)
    speed_id = Column(UUID(as_uuid=True), ForeignKey('capabilities_ref_speeds.speed_id'), nullable=False)
    optic_id = Column(UUID(as_uuid=True), ForeignKey('capabilities_ref_optics.optic_id'), nullable=False)

    __table_args__ = (
        Index('idx_cap_ports_profile', 'profile_id'),
    )


class ProfilePersonality(Base):
    __tablename__ = 'capabilities_profile_personalities'
    
    capability_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    profile_id = Column(UUID(as_uuid=True), ForeignKey('capabilities_hardware_profiles.profile_id', ondelete='CASCADE'), nullable=False)
    personality_id = Column(UUID(as_uuid=True), ForeignKey('capabilities_ref_personalities.personality_id'), nullable=False)

    __table_args__ = (
        Index('idx_cap_pers_profile', 'profile_id'),
    )


class ProfileService(Base):
    __tablename__ = 'capabilities_profile_services'
    
    capability_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    profile_id = Column(UUID(as_uuid=True), ForeignKey('capabilities_hardware_profiles.profile_id', ondelete='CASCADE'), nullable=False)
    service_id = Column(UUID(as_uuid=True), ForeignKey('capabilities_ref_services.service_id'), nullable=False)
    speed_id = Column(UUID(as_uuid=True), ForeignKey('capabilities_ref_speeds.speed_id'), nullable=False)

    __table_args__ = (
        Index('idx_cap_serv_profile', 'profile_id'),
    )