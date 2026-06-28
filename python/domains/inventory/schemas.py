"""
Pydantic schemas for the Inventory domain.
File: domains/inventory/schemas.py

Validation and serialization for aggregated metrics and dashboards.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict
from uuid import UUID

# ============================================================
# MASTER SUMMARY SCHEMAS
# ============================================================

class SummaryRow(BaseModel):
    id: int
    category: str
    dimension: dict
    count_value: int

class SummaryRowV2(BaseModel):
    id: int
    category: str
    dimension: dict
    count_value: int

class SummaryGroupedResponse(BaseModel):
    devices: List[SummaryRow] = []
    device_health: List[SummaryRow] = []
    device_lifecycle: List[SummaryRow] = []
    device_location: List[SummaryRow] = []
    device_vendor_model: List[SummaryRow] = []
    ports: List[SummaryRow] = []
    port_type: List[SummaryRow] = []
    port_speed: List[SummaryRow] = []
    port_optic: List[SummaryRow] = []
    port_health: List[SummaryRow] = []
    links_by_type: List[SummaryRow] = []
    links_by_location: List[SummaryRow] = []

class SummaryGroupedResponseV2(BaseModel):
    devices: List[SummaryRowV2] = []
    device_health: List[SummaryRowV2] = []

# ============================================================
# GRANULAR VIEW RESPONSE SCHEMAS
# ============================================================

class SummaryDevices(BaseModel):
    network: str = Field(..., description="Logical network or fabric grouping")
    role: str = Field(..., description="Device role (e.g., VAR, SDR, ES)")
    model: str = Field(..., description="Device hardware model")
    device_count: int = Field(..., description="Number of devices in this group")
    model_config = ConfigDict(from_attributes=True)

class SummaryPorts(BaseModel):
    port_type: str = Field(..., description="Port type (Physical, Logical, LAG, etc.)")
    port_speed: str = Field(..., description="Port speed (1G, 10G, 100G, etc.)")
    service_status: str = Field(..., description="Operational service status")
    port_count: int = Field(..., description="Number of ports in this group")
    model_config = ConfigDict(from_attributes=True)

class SummaryPortHealth(BaseModel):
    port_type: str = Field(..., description="Port type")
    port_speed: str = Field(..., description="Port speed")
    health_status: int = Field(..., description="Health status code")
    port_count: int = Field(..., description="Number of ports in this health group")
    model_config = ConfigDict(from_attributes=True)

class SummaryLinks(BaseModel):
    link_type: str = Field(..., description="Type of link (fiber, wireless, cross-connect)")
    link_count: int = Field(..., description="Number of links of this type")
    model_config = ConfigDict(from_attributes=True)

class SummaryLinksByLocation(BaseModel):
    location: str = Field(..., description="Device location associated with link endpoints")
    link_type: str = Field(..., description="Type of link")
    link_endpoint_count: int = Field(..., description="Number of link endpoints at this location")
    model_config = ConfigDict(from_attributes=True)

class SummaryCustomers(BaseModel):
    customer_count: int = Field(..., description="Total number of customers")
    model_config = ConfigDict(from_attributes=True)

class SummaryCustomerServices(BaseModel):
    customer_id: UUID = Field(..., description="Customer UUID")
    customer_name: str = Field(..., description="Customer name")
    account_id: str = Field(..., description="Account identifier")
    service_count: int = Field(..., description="Number of services for this customer")
    model_config = ConfigDict(from_attributes=True)

class SummaryServices(BaseModel):
    service_type: str = Field(..., description="Type of service (EPL, EVPL, etc.)")
    service_status: str = Field(..., description="Operational status of the service")
    service_count: int = Field(..., description="Number of services in this group")
    model_config = ConfigDict(from_attributes=True)

class SummaryConnections(BaseModel):
    connection_status: str = Field(..., description="Operational status of the connection")
    service_bw: int = Field(..., description="Provisioned bandwidth")
    vrf_name: str = Field(..., description="VRF name")
    connection_count: int = Field(..., description="Number of connections in this group")
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# MASTER DASHBOARD SCHEMAS
# ============================================================

class RoleCount(BaseModel):
    role: Optional[str] = "Unknown" 
    count: Optional[int] = 0

class LinkCapacityMetrics(BaseModel):
    link_type: Optional[str] = "Unknown"
    total_links: Optional[int] = 0
    total_capacity_gbps: Optional[float] = 0.0

class VNetworkDashboardOut(BaseModel):
    network: str
    pop_location: str
    city: Optional[str] = "Unknown"
    latitude: Optional[float] = 0.0
    longitude: Optional[float] = 0.0
    total_devices: Optional[int] = 0
    role_distribution: List[RoleCount] = []
    link_distribution: List[LinkCapacityMetrics] = []
    model_config = ConfigDict(from_attributes=True)
    
# domains/inventory/schemas.py

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

class InventoryAssetBase(BaseModel):
    vendor: str = Field(..., max_length=100, description="Name of the hardware manufacturer")
    vendor_id: str = Field(..., max_length=100, description="Manufacturer part number (SKU)")
    lumen_id: str = Field(..., max_length=100, description="Internal corporate asset tracking tag")
    description: Optional[str] = Field(None, description="Detailed description of the hardware asset")
    list_price: Decimal = Field(default=Decimal("0.00"), description="MSRP or base catalog price", max_digits=12, decimal_places=2)
    discount: Decimal = Field(default=Decimal("0.00"), description="Applied percentage or flat discount", max_digits=5, decimal_places=2)
    lumen_price: Decimal = Field(default=Decimal("0.00"), description="Final calculated internal cost", max_digits=12, decimal_places=2)

class InventoryAssetCreate(InventoryAssetBase):
    """Payload expected when creating a new asset."""
    pass

class InventoryAssetUpdate(BaseModel):
    """Payload expected when updating an asset (all fields optional)."""
    vendor: Optional[str] = Field(None, max_length=100)
    vendor_id: Optional[str] = Field(None, max_length=100)
    lumen_id: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    list_price: Optional[Decimal] = Field(None, max_digits=12, decimal_places=2)
    discount: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2)
    lumen_price: Optional[Decimal] = Field(None, max_digits=12, decimal_places=2)

class InventoryAssetResponse(InventoryAssetBase):
    """The formatted response object returned to the API client."""
    asset_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)