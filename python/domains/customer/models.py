"""
SQLAlchemy models for the Customers domain.
File: app/python/domains/customers/models.py

Defines the physical table structure for customers and 
the read-only mapping for the aggregated summary view.
"""

from sqlalchemy import Column, String, DateTime, Integer, text
from sqlalchemy.dialects.postgresql import UUID

# Ensure this path matches where you placed your centralized core
from core.database import Base 

class Customer(Base):
    """
    Physical table for storing customer/tenant identity data.
    """
    __tablename__ = "customers"

    customer_id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        server_default=text("gen_random_uuid()"),
        index=True
    )
    customer_name = Column(String, nullable=False, index=True)
    account_id = Column(String, nullable=False, unique=True, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=text("now()"), 
        onupdate=text("now()")
    )


class CustomerSummary(Base):
    """
    SQLAlchemy model mapped to the 'v_customer_summary' database view.
    Used for rapid dashboard reporting without heavy JOINs.
    Note: Views should be treated as read-only in operations.py.
    """
    __tablename__ = "v_customer_summary"

    # We map customer_id as the primary key so SQLAlchemy can index the view results
    customer_id = Column(UUID(as_uuid=True), primary_key=True)
    customer_name = Column(String)
    account_id = Column(String)
    
    service_count = Column(Integer, default=0)
    fabric_connection_count = Column(Integer, default=0)
    port_count = Column(Integer, default=0)
    interface_count = Column(Integer, default=0)