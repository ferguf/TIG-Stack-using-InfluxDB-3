"""
Pydantic schemas for the Customers domain.
File: app/python/domains/customers/schemas.py

Defines the strict API contracts for validating incoming requests 
and serializing outgoing responses for Customer and Tenant data.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime


class CustomerIn(BaseModel):
    """Schema for creating a new customer record via POST."""
    account_id: str = Field(..., description="Account ID associated with the customer")
    customer_name: str = Field(..., description="Full name of the customer")


class CustomerUpdate(BaseModel):
    """Schema for updating an existing customer record via PUT/PATCH."""
    customer_id: Optional[UUID] = Field(None, description="Unique UUID identifier for the customer")
    customer_name: Optional[str] = Field(None, description="Full name of the customer")
    account_id: Optional[str] = Field(None, description="Associated account identifier for the customer")


class CustomerOut(BaseModel):
    """Schema for returning standard customer details to the client."""
    customer_id: UUID = Field(..., description="Unique UUID identifier for the customer")
    customer_name: Optional[str] = Field(None, description="Full name of the customer")
    account_id: Optional[str] = Field(None, description="Associated account identifier for the customer")
    service_count: Optional[int] = Field(0, description="Number of active services linked to the customer")
    
    created_at: Optional[datetime] = Field(None, description="Timestamp when the customer record was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the customer record was last updated")

    # Enables Pydantic to read directly from the SQLAlchemy ORM model
    model_config = ConfigDict(from_attributes=True)


class CustomerSummaryOut(BaseModel):
    """
    Schema for returning the aggregated customer summary view.
    Used heavily by the Streamlit UI to display high-level dashboard metrics.
    """
    customer_id: UUID = Field(..., description="Unique UUID identifier for the customer")
    customer_name: Optional[str] = Field(None, description="Full name of the customer")
    account_id: Optional[str] = Field(None, description="Associated account identifier for the customer")
    
    # Aggregated counts from the database view
    service_count: int = Field(0, description="Total number of services linked to the customer")
    fabric_connection_count: int = Field(0, description="Total number of fabric connections")
    port_count: int = Field(0, description="Total number of physical or logical ports")
    interface_count: int = Field(0, description="Total number of interfaces")

    model_config = ConfigDict(from_attributes=True)


class DeleteResponse(BaseModel):
    """Standardized response schema for successful DELETE operations."""
    detail: str