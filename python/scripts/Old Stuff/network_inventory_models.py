"""File Name: 'network_inventory_models.py' and version '1.1.2' date: 'November 30, 2025 11:10 AM MST' (Change: Model class definition refresh to fix 'invalid keyword argument' error during object instantiation.) """
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

# Define the base class for declarative class definitions
Base = declarative_base()

def generate_uuid():
    """Generates a UUID string for primary keys."""
    return str(uuid.uuid4())

class Customer(Base):
    """Represents a customer entity."""
    __tablename__ = 'customer' # Table name is singular

    customer_id = Column(String, primary_key=True, default=generate_uuid)
    customer_name = Column(String, nullable=False, unique=True)
    account_id = Column(String, nullable=False, unique=True)

    # Relationships 
    # Removed the explicit 'primaryjoin' because the ForeignKey definition below
    # should allow SQLAlchemy to automatically detect the relationship.
    services = relationship(
        "FabricService", 
        back_populates="customer"
        # primaryjoin="Customer.customer_id == FabricService.customer_id" <-- Removed this
    )

    def __repr__(self):
        return f"<Customer(name='{self.customer_name}', id='{self.customer_id[-4:]}')>"

class FabricService(Base):
    """Represents a high-level customer service instance."""
    __tablename__ = 'fabric_service' # Table name is singular

    service_id = Column(String, primary_key=True, default=generate_uuid)
    
    # FIX: Ensure this ForeignKey points to the singular 'customer.customer_id'.
    # The error message 'could not find table customers' implies this reference 
    # was still pointing to the plural form.
    customer_id = Column(String, ForeignKey('customer.customer_id'), nullable=False)
    
    service_name = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.now)
    service_type = Column(String, nullable=False, default='EPL')

    # Relationships
    customer = relationship("Customer", back_populates="services")
    # connections = relationship("FabricConnection", back_populates="service")

    def __repr__(self):
        return f"<FabricService(name='{self.service_name}', type='{self.service_type}')>"


class Port(Base):
    """Represents a physical or logical port on a network device."""
    __tablename__ = 'ports'
    port_id = Column(String, primary_key=True, default=generate_uuid)
    port_name = Column(String, nullable=False) # e.g., 'Port-A-1/1/1'
    device_id = Column(String, nullable=False)
    port_service_status = Column(String, default='AVAILABLE') 
    port_type = Column(String, default='UNKNOWN') 
    max_capacity_mbits = Column(Integer, default=10000)
    port_description = Column(String, nullable=True)
    service_id = Column(String, ForeignKey('fabric_services.service_id'), nullable=True)
    def __repr__(self):
        return f"<Port(name='{self.port_name}', status='{self.port_service_status}')>"

class Interface(Base):
    """Represents the logical interface associated with a physical port."""
    __tablename__ = 'interfaces'
    interface_id = Column(String, primary_key=True, default=generate_uuid)
    port_id = Column(String, ForeignKey('ports.port_id'), nullable=False)
    interface_name = Column(String, nullable=False) # e.g., 'interface_001'
    is_active = Column(Boolean, default=True)

    # Relationships
    port = relationship("Port")
    connections = relationship("FabricConnection", back_populates="interface")

    def __repr__(self):
        return f"<Interface(name='{self.interface_name}', port_id='{self.port_id[-4:]}')>"

class Device(Base):
    """
    Data model representing a physical or virtual network device.
    This structure is mapped directly from the SQL schema provided.
    """
    __tablename__ = 'devices'
    device_id = Column(String, primary_key=True, default=generate_uuid)
    device_name = Column(String, nullable=False, unique=True)
    location = Column(String, nullable=False, unique=True)
    device_role = Column(String, nullable=False)
    device_model = Column(String, nullable=True)
    device_vendor = Column(String, nullable=False)
    serial_number = Column(String, nullable=True)
    availability_zone = Column(String, nullable=True)
    lifecycle_status = Column(String, nullable=False, default='Active')
    planning_status = Column(String, nullable=False, default='Planned')
    health_status = Column(Integer, nullable=True) # e.g., 1 - Green, 2 - Amber, 3 - Red, 4 - Unknown
    device_description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

# class FabricConnection(Base):
#     """Represents a deployed, active connection (e.g., the E-Line itself)."""
#     __tablename__ = 'fabric_connection'
#     connection_id = Column(String, primary_key=True, default=generate_uuid)
#     connection_name = Column(String, nullable=False, unique=True)
#     service_id = Column(String, ForeignKey('fabric_services.service_id'), nullable=False)
#     interface_id = Column(String, ForeignKey('interfaces.interface_id'), nullable=False)
    
#     connection_type = Column(String, nullable=False, default='EPL')
#     bandwidth_mbits = Column(Integer, nullable=False)
#     port1_id = Column(String, ForeignKey('ports.port_id'), nullable=False)
#     port2_id = Column(String, ForeignKey('ports.port_id'), nullable=False)
    
#     # Relationships
#     service = relationship("FabricService", back_populates="connections")
#     interface = relationship("Interface", back_populates="connections")
#     port1 = relationship("Port", foreign_keys=[port1_id])
#     port2 = relationship("Port", foreign_keys=[port2_id])

    def __repr__(self):
        return (f"<FabricConnection(name='{self.connection_name}', "
                f"bw={self.bandwidth_mbits}M, type='{self.connection_type}')>")
        
def validate_service_type(service_name: str) -> bool:
    """
    Validates if a given service name is one of the defined SERVICE_TYPES.
    This function demonstrates how the SERVICE_TYPES constant can be used
    in a conditional structure.
    """
    if service_name in SERVICE_TYPES:
        return True
    else:
        # The 'else' block handles invalid service types
        raise ValueError(
            f"Invalid service type '{service_name}'. "
            f"Must be one of: {', '.join(SERVICE_TYPES)}"
        )        