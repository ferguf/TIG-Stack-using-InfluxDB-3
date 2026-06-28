# api_schema.py
# scripts/api_schema.py
from decimal import Decimal
from typing import List,Optional,Dict
from pydantic import BaseModel, ConfigDict, field_validator, Field
from uuid import UUID
from datetime import date, datetime



from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from datetime import datetime


# -------------------------------
# CLOUD PARTNER SCHEMAS (FINAL)
# -------------------------------


class CloudPartnerIn(BaseModel):
    partner_key: str = Field(max_length=50)
    partner_name: str = Field(max_length=100)
    partner_code: str = Field(max_length=20)
    partner_type: str = Field(max_length=50)

    region: str = Field(max_length=100)
    service_type: str = Field(max_length=20)
    service_status: str = Field(max_length=50)

    partnership_level: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = None

    # NEW: required list of allowed bandwidth tiers
    bandwidth_tiers: List[int] = Field(
        ...,
        description="List of allowed bandwidth tiers for this partner"
    )

class CloudPartnerOut(BaseModel):
    partner_id: UUID
    partner_key: str
    partner_name: str
    partner_code: str
    partner_type: str
    region: str
    service_type: str
    service_status: str
    partnership_level: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # The View guarantees this is a List[int], so no validator is needed
    bandwidth_tiers: List[int] = []

    model_config = ConfigDict(from_attributes=True)

class CloudPartnerUpdate(BaseModel):
    partner_key: Optional[str] = None
    partner_name: Optional[str] = None
    partner_code: Optional[str] = None
    partner_type: Optional[str] = None

    region: Optional[str] = None
    service_type: Optional[str] = None
    service_status: Optional[str] = None

    partnership_level: Optional[str] = None
    notes: Optional[str] = None

    # NEW: optional update to bandwidth tiers
    bandwidth_tiers: Optional[List[int]] = None

class CloudConnectionIn(BaseModel):
    partner_id: UUID
    service_id: UUID

    connection_name: str = Field(max_length=100)
    service_type: str = Field(max_length=20)
    service_status: str = Field(max_length=50)
    region: str = Field(max_length=100)

    service_bw: Optional[int] = None
    redundancy_model: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = None

class CloudConnectionUpdate(BaseModel):
    partner_id: Optional[UUID] = None
    service_id: Optional[UUID] = None
    connection_name: Optional[str] = None
    service_type: Optional[str] = None
    service_status: Optional[str] = None
    region: Optional[str] = None

    service_bw: Optional[int] = None
    redundancy_model: Optional[str] = None
    description: Optional[str] = None

class CloudConnectionOut(BaseModel):
    cloud_connection_id: UUID
    partner_id: UUID
    service_id: Optional[UUID] = None

    
    connection_name: str
    service_type: str
    service_status: str
    region: str

    service_bw: Optional[int]
    redundancy_model: Optional[str]
    description: Optional[str]

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ============================================================
# Routing and Interfaces
# ============================================================


class IPInterfaceIn(BaseModel):
    interface_id: UUID

    lumen_ip_address: str
    customer_ip_address: str
    network_mask_cidr: int
    bring_your_own_ip: bool

class IPInterfaceUpdate(BaseModel):
    interface_id: Optional[UUID] = None

    lumen_ip_address: Optional[str] = None
    customer_ip_address: Optional[str] = None
    network_mask_cidr: Optional[int] = None
    bring_your_own_ip: Optional[bool] = None

class IPInterfaceOut(BaseModel):
    ip_address_id: UUID
    interface_id: UUID

    lumen_ip_address: str
    customer_ip_address: str
    network_mask_cidr: int
    bring_your_own_ip: bool


    model_config = ConfigDict(from_attributes=True)

class BGPNeighborIn(BaseModel):
    # Optional because DB handles generation via gen_random_uuid()
    bgp_neighbor_id: Optional[UUID] = Field(
        None, description="Optional UUID; DB will generate if omitted"
    )

    interface_id: Optional[UUID] = Field(
        None, description="UUID of associated fabric interface, or None for router-base"
    )

    neighbor_ip: str = Field(
        ..., description="IPv4 or IPv6 address of the BGP neighbor"
    )
    local_ip: Optional[str] = Field(
        None, description="Local IPv4 or IPv6 address used for the BGP session"
    )

    remote_asn: int = Field(
        ..., description="Remote ASN of the BGP neighbor"
    )
    local_asn: Optional[int] = Field(
        None, description="Local ASN if different from router default"
    )

    session_type: Optional[str] = Field(
        None, description="Session type (eBGP, iBGP, RR-client, etc.)"
    )
    session_state: Optional[str] = Field(
        None, description="Operational BGP state (Idle, Active, Established, etc.)"
    )
    description: Optional[str] = Field(
        None, description="Description of the BGP neighbor"
    )
    community: Optional[str] = Field(
        None, description="Comma-separated BGP communities applied to the neighbor"
    )

    import_policy: Optional[List[str]] = Field(
        None, description="List of import routing policies"
    )
    export_policy: Optional[List[str]] = Field(
        None, description="List of export routing policies"
    )

    multihop: Optional[int] = Field(
        None, description="TTL for eBGP multihop sessions"
    )

    auth: Optional[bool] = Field(
        False, description="Enable BGP authentication"
    )
    auth_password: Optional[str] = Field(
        None, description="Authentication password if auth is enabled"
    )

    bfd: Optional[bool] = Field(
        False, description="Enable BFD for fast failure detection"
    )
    bfd_interval: Optional[int] = Field(
        500, description="BFD interval in milliseconds"
    )
    bfd_multiple: Optional[int] = Field(
        3, description="BFD detection multiplier"
    )

class BGPNeighborOut(BaseModel):
    bgp_neighbor_id: UUID
    interface_id: Optional[UUID] = None

    neighbor_ip: str
    local_ip: Optional[str] = None

    remote_asn: int
    local_asn: Optional[int] = None

    session_type: Optional[str] = None
    session_state: Optional[str] = None
    description: Optional[str] = None
    community: Optional[str] = None

    import_policy: Optional[List[str]] = None
    export_policy: Optional[List[str]] = None

    multihop: Optional[int] = None

    auth: bool
    auth_password: Optional[str] = None

    bfd: bool
    bfd_interval: int
    bfd_multiple: int

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class BGPNeighborUpdate(BaseModel):
    interface_id: Optional[UUID] = None

    neighbor_ip: Optional[str] = None
    local_ip: Optional[str] = None

    remote_asn: Optional[int] = None
    local_asn: Optional[int] = None

    session_type: Optional[str] = None
    session_state: Optional[str] = None
    description: Optional[str] = None
    community: Optional[str] = None

    import_policy: Optional[List[str]] = None
    export_policy: Optional[List[str]] = None

    multihop: Optional[int] = None

    auth: Optional[bool] = None
    auth_password: Optional[str] = None

    bfd: Optional[bool] = None
    bfd_interval: Optional[int] = None
    bfd_multiple: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class StaticRouteIn(BaseModel):
    # Optional because DB handles generation via gen_random_uuid()

    interface_id: Optional[UUID] = Field(
        None, description="UUID of associated fabric interface, or None for router-base"
    )

    ip_prefix: str = Field(
        ..., description="IPv4 or IPv6 prefix (e.g., 10.1.1.0/24 or 2001:db8::/48)"
    )
    prefix_mask: str = Field(
        ..., description="IPv4 or IPv6 mask stored as inet"
    )
    next_hop_ip: str = Field(
        ..., description="IPv4 or IPv6 next-hop address"
    )

    metric: Optional[int] = Field(
        None, description="Optional route metric"
    )
    community: Optional[str] = Field(
        None, description="Optional BGP-style community string"
    )
    
class StaticRouteOut(BaseModel):
    route_id: UUID
    interface_id: Optional[UUID] = None

    ip_prefix: str
    prefix_mask: int   
    next_hop_ip: str

    metric: Optional[int] = None
    community: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class StaticRouteUpdate(BaseModel):
    interface_id: Optional[UUID] = None

    ip_prefix: Optional[str] = None
    prefix_mask: Optional[str] = None
    next_hop_ip: Optional[str] = None

    metric: Optional[int] = None
    community: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class RoutingPolicyIn(BaseModel):
    # Optional because DB handles generation via gen_random_uuid(), or the UI passes the one it generated
    term_id: Optional[UUID] = Field(
        None, description="Optional UUID; DB will generate if omitted, or UI can supply"
    )
    
    policy_id: UUID = Field(
        ..., description="UUID grouping all terms under a single policy container"
    )

    fabric_service_id: Optional[UUID] = Field(
        None, description="UUID of associated fabric service"
    )

    # --- Policy Context ---
    policy_name: str = Field(..., description="Name of the routing policy (e.g., EXPORT-AWS)")
    direction: str = Field(..., description="Routing direction: Import or Export")

    # --- Term Context ---
    sequence: int = Field(..., description="Sequence number for policy evaluation order (e.g., 10, 20)")
    term_name: str = Field(..., description="Human-readable name for the term (e.g., SEQ-10, deny-all)")

    # --- Routing Logic ---
    prefixes: List[str] = Field(
        default_factory=list, description="List of CIDR format prefixes (e.g., ['10.0.0.0/8'])"
    )

    match_type: str = Field(..., description="Match type: Exact, All, Upto, Auto-Summary")
    upto_mask: Optional[int] = Field(None, description="Maximum mask length for Upto match type (le)")
    action: str = Field(..., description="Routing action: Advertise or Deny")

    # --- BGP Attributes ---
    med: Optional[int] = Field(None, description="Multi-Exit Discriminator value")
    local_pref: Optional[int] = Field(None, description="Local preference value")
    as_prepend: Optional[int] = Field(None, description="AS path prepend multiplier")
    communities: Optional[List[str]] = Field(default_factory=list, description="List of BGP communities")

class RoutingPolicyUpdate(BaseModel):
    # Everything is optional for a PATCH request
    policy_id: Optional[UUID] = None
    fabric_service_id: Optional[UUID] = None

    policy_name: Optional[str] = None
    direction: Optional[str] = None

    sequence: Optional[int] = None
    term_name: Optional[str] = None

    prefixes: Optional[List[str]] = None

    match_type: Optional[str] = None
    upto_mask: Optional[int] = None
    action: Optional[str] = None

    med: Optional[int] = None
    local_pref: Optional[int] = None
    as_prepend: Optional[int] = None
    communities: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)

class RoutingPolicyOut(BaseModel):
    # Strict response model representing the DB state
    term_id: UUID
    policy_id: UUID
    fabric_service_id: Optional[UUID] = None

    policy_name: str
    direction: str

    sequence: int
    term_name: str

    prefixes: List[str]

    match_type: str
    upto_mask: Optional[int] = None
    action: str

    med: Optional[int] = None
    local_pref: Optional[int] = None
    as_prepend: Optional[int] = None
    communities: Optional[List[str]] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
# ============================================================
#  SUMMARYTelelgraf and Influxdb
# ============================================================

class TelegrafInventory(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    device_id: UUID
    device_name: str
    location: Optional[str]
    device_role: Optional[str]
    port_id: UUID
    port_name: str
    port_speed: Optional[str]
    port_cktid: Optional[str]
    port_optic: Optional[str]
    port_type: Optional[str]
    
    lag_parent_id: Optional[UUID]        
    port_health_status: int             
    customer_id: Optional[UUID]        

# ============================================================
#  SUMMARY VIEW RESPONSE MODELS
# ============================================================

class SummaryDevices(BaseModel):
    network: str = Field(..., description="Logical network or fabric grouping")
    role: str = Field(..., description="Device role (e.g., VAR, SDR, ES)")
    model: str = Field(..., description="Device hardware model")
    device_count: int = Field(..., description="Number of devices in this group")

class SummaryPorts(BaseModel):
    port_type: str = Field(..., description="Port type (Physical, Logical, LAG, etc.)")
    port_speed: str = Field(..., description="Port speed (1G, 10G, 100G, etc.)")
    service_status: str = Field(..., description="Operational service status")
    port_count: int = Field(..., description="Number of ports in this group")

class SummaryPortHealth(BaseModel):
    port_type: str = Field(..., description="Port type")
    port_speed: str = Field(..., description="Port speed")
    health_status: int = Field(..., description="Health status code")
    port_count: int = Field(..., description="Number of ports in this health group")

class SummaryLinks(BaseModel):
    link_type: str = Field(..., description="Type of link (fiber, wireless, cross-connect)")
    link_count: int = Field(..., description="Number of links of this type")

class SummaryLinksByLocation(BaseModel):
    location: str = Field(..., description="Device location associated with link endpoints")
    link_type: str = Field(..., description="Type of link")
    link_endpoint_count: int = Field(..., description="Number of link endpoints at this location")

class SummaryCustomers(BaseModel):
    customer_count: int = Field(..., description="Total number of customers")

class SummaryCustomerServices(BaseModel):
    customer_id: UUID = Field(..., description="Customer UUID")
    customer_name: str = Field(..., description="Customer name")
    account_id: str = Field(..., description="Account identifier")
    service_count: int = Field(..., description="Number of services for this customer")

class SummaryServices(BaseModel):
    service_type: str = Field(..., description="Type of service (EPL, EVPL, etc.)")
    service_status: str = Field(..., description="Operational status of the service")
    service_count: int = Field(..., description="Number of services in this group")

class SummaryConnections(BaseModel):
    connection_status: str = Field(..., description="Operational status of the connection")
    service_bw: int = Field(..., description="Provisioned bandwidth")
    vrf_name: str = Field(..., description="VRF name")
    connection_count: int = Field(..., description="Number of connections in this group")

class SummaryRow(BaseModel):
    id: int
    category: str
    dimension: dict
    count_value: int

class SummaryRowV2(BaseModel):
    id: int  # or int if row_number()
    category: str
    dimension: dict
    count_value: int

class SummaryGroupedResponseV2(BaseModel):
    devices: list[SummaryRowV2] = []
    device_health: list[SummaryRowV2] = []
    # device_location: list[SummaryRowV2] = []
    # device_lifecycle: list[SummaryRowV2] = []
    # device_vendor_model: list[SummaryRowV2] = []
    # ports: list[SummaryRowV2] = []
    # port_type: list[SummaryRowV2] = []
    # port_speed: list[SummaryRowV2] = []
    # port_optic: list[SummaryRowV2] = []
    # port_health: list[SummaryRowV2] = []
    # links_by_type: list[SummaryRowV2] = []
    # links_by_location: list[SummaryRowV2] = []

class SummaryGroupedResponse(BaseModel):
    devices: list[SummaryRow] = []
    device_health: list[SummaryRow] = []
    device_lifecycle: list[SummaryRow] = []
    device_location: list[SummaryRow] = []
    device_vendor_model: list[SummaryRow] = []
    ports: list[SummaryRow] = []
    port_type: list[SummaryRow] = []
    port_speed: list[SummaryRow] = []
    port_optic: list[SummaryRow] = []
    port_health: list[SummaryRow] = []
    links_by_type: list[SummaryRow] = []
    links_by_location: list[SummaryRow] = []

class RouteVisionCreate(BaseModel):
    # Required by DB 'NOT NULL' constraint
    fabric_connection_id: Optional[UUID] = None
    
    # Optional connection association
    interface_id: Optional[UUID] = None

    # Network Details (Postgres CIDR/Varchar)
    ip_prefix: str = Field(..., description="IP Prefix in CIDR notation (e.g. 1.1.1.0/24)")
    ip_next_hop: str = Field(..., description="Next hop IP address")
    route_type: str = Field(..., description="Static, BGP, or Connected")
    route_status: str = "Active"

    # VRF/BGP Metadata
    route_target: Optional[str] = Field(None, description="Format 'ASN:Value'")
    route_distinguisher: Optional[str] = Field(None, description="Format 'IP:ID' or 'ASN:ID'")

    bgp_asn: Optional[int] = None
    bgp_as_path: Optional[str] = None
    bgp_community: Optional[str] = None

class RouteVisionRead(BaseModel):
    route_id: UUID
    fabric_service_id: UUID
    interface_id: Optional[UUID] = None

    
    
    ip_prefix: str
    ip_next_hop: str
    route_type: str
    route_status: str
    
    route_target: Optional[str]
    route_distinguisher: Optional[str]
    
    bgp_asn: Optional[int]
    bgp_as_path: Optional[str]
    bgp_community: Optional[str]
    
    created_at: datetime
    updated_at: datetime

    # Pydantic v2 style config
    model_config = ConfigDict(from_attributes=True)

# Request model for creating/updating customers
class CustomerIn(BaseModel):
    account_id: str = Field(..., description="accoutn ID")
    customer_name: str = Field(..., description="Full name of the customer")\

class CustomerOut(BaseModel):
    customer_id: UUID = Field(..., description="Unique UUID identifier for the customer")
    customer_name: str = Field(None, description="Full name of the customer")
    account_id: str = Field(None, description="Associated account identifier for the customer")
    service_count: int = Field(None, description="Number of active services linked to the customer")
    created_at: Optional[datetime] = Field(None, description="Timestamp when the customer record was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the customer record was last updated")

class CustomerUpdate(BaseModel):
    customer_id: UUID = Field(None, description="Unique UUID identifier for the customer")
    customer_name: str = Field(None, description="Full name of the customer")
    account_id: str = Field(None, description="Associated account identifier for the customer")

class CustomerSummaryOut(BaseModel):
    customer_id: UUID = Field(..., description="Unique UUID identifier for the customer")
    customer_name: Optional[str] = Field(None, description="Full name of the customer")
    account_id: Optional[str] = Field(None, description="Associated account identifier for the customer")
    
    # Aggregated counts from the view
    service_count: int = Field(0, description="Total number of services linked to the customer")
    fabric_connection_count: int = Field(0, description="Total number of fabric connections")
    port_count: int = Field(0, description="Total number of physical or logical ports")
    interface_count: int = Field(0, description="Total number of interfaces")

    class Config:
        # Allows Pydantic to read data from the SQLAlchemy model attributes
        from_attributes = True

class DevicePortOut(BaseModel):
    device_id: UUID = Field(..., description="Unique UUID identifier for the device")
    device_name: Optional[str] = Field(None, description="Name of the device")
    device_health_status: Optional[int] = Field(None, description="Health status of the device")
    availability_zone: Optional[str] = Field(None, description="Availability zone where the device resides")

    port_id: UUID = Field(..., description="Unique UUID identifier for the port")
    port_name: Optional[str] = Field(None, description="Name of the port")
    port_speed: Optional[str] = Field(None, description="Speed of the port (e.g., 1G, 10G)")
    port_type: Optional[str] = Field(None, description="Type of the port (e.g., Ethernet, Fiber)")
    port_service_status: Optional[str] = Field(None, description="Service status of the port")
    port_health_status: Optional[int] = Field(None, description="Health status of the port")

    admin_status: Optional[str] = None   
    oper_status: Optional[str] = None   

    mac_address: Optional[str] = Field(None, description="MAC address associated with the port")
    port_optic: Optional[str] = Field(None, description="Optic type used on the port")
    port_tagging: Optional[str] = Field(None, description="Tagging information for the port")
    port_cktid: Optional[str] = Field(None, description="Circuit ID associated with the port")

    lag_parent_id: Optional[UUID] = Field(None, description="UUID of the parent LAG if applicable")
    customer_id: Optional[UUID] = Field(None, description="UUID of the associated customer if applicable")

    port_created_at: Optional[datetime] = Field(None, description="Timestamp when the port record was created")
    port_updated_at: Optional[datetime] = Field(None, description="Timestamp when the port record was last updated")

    class Config:
        from_attributes = True  # Enables ORM object validation

# Response model for fabric service     
class FabricServiceIn(BaseModel):
    customer_id: UUID
    service_name: str
    service_alias: str
    service_type: str
    service_description: str = None
    route_target: Optional[str] = None
    health_status: int = 4

class FabricServiceOut(BaseModel):
    service_id: UUID
    customer_id: Optional[UUID]
    service_name: Optional[str]
    service_alias:Optional[str]
    service_type: Optional[str]
    service_description: Optional[str] = None
    route_target: Optional[str] = None
    health_status: int
    created_at: datetime
    updated_at: datetime
    service_count: int = 0

    model_config = ConfigDict(from_attributes=True) 
        
class FabricServiceUpdate(BaseModel):
    service_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    service_name: Optional[str] = None
    service_alias: Optional[str] = None
    service_description: Optional[str] = None
    service_type: Optional[str] = None
    route_target: Optional[str] = None
    health_status: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class FabricServiceDetailOut(BaseModel):
    service_id: UUID
    customer_id: UUID
    customer_name: str
    account_id: str

    service_name: str
    service_alias: str
    service_type: str
    service_description: str

    route_target: str | None = None

    health_status: int
    created_at: datetime
    updated_at: datetime

    fabric_connections: list[dict]
    fabric_ports: list[dict]
    
    # ⭐ This is now a list of InterfaceDetail
    fabric_interfaces: list[dict]
    cloud_interconnects: list[dict]


class DeviceIn(BaseModel):
    device_name: str
    device_role: Optional[str] = None
    device_model: Optional[str] = None
    device_vendor: Optional[str] = None
    
    nos_version: Optional[str] = None    
    
    availability_zone: Optional[str] = None
    lifecycle_status: Optional[str] = "Active"
    planning_status: Optional[str] = "Planned"
    health_status: Optional[int] = 4
    
    network: Optional[str] = None

    location_id: Optional[UUID] = None
    
    # ⚠️ Legacy / compatibility (CLLI string only)
    location: Optional[str] = None
    
    floor: Optional[str] = None
    aisle: Optional[str] = None
    rack: Optional[str] = None
    
    device_description: Optional[str] = None

class DeviceUpdate(BaseModel):
    device_name: Optional[str] 
    device_role: Optional[str] = None
    device_model: Optional[str] = None
    device_vendor: Optional[str] = None
    availability_zone: Optional[str] = None   # NEW FIELD
    lifecycle_status: Optional[str] = None
    planning_status: Optional[str] = None
    health_status: Optional[int] = None
    network: Optional[str] = None
    location: Optional[str] = None
    floor: Optional[str] = None
    aisle: Optional[str] = None
    rack: Optional[str] = None
    device_description: Optional[str] = None

class DeviceOut(BaseModel):
    device_id: UUID
    device_name: str
    device_role: Optional[str]
    device_model: Optional[str]
    device_vendor: Optional[str]
    availability_zone: Optional[str]          # NEW FIELD
    lifecycle_status: Optional[str]       
    nos_version: Optional[str] = None   
    planning_status: Optional[str]
    health_status: Optional[int]
    network: Optional[str] = None
    floor: Optional[str] = None
    location: Optional[str] = None
    aisle: Optional[str] = None
    rack: Optional[str] = None
    location_id: Optional[UUID] = None
    device_description: Optional[str]
    created_at: datetime
    updated_at: datetime


    model_config = {
        "from_attributes": True
    }


class DeviceDetailsOut(BaseModel):
    device_id: UUID
    device_name: str
    device_role: str
    device_model: Optional[str]
    device_vendor: Optional[str]
    nos_version: Optional[str]

    network: Optional[str]

    location_id: Optional[UUID]
    location_code: Optional[str]
    location_name: Optional[str]
    city: Optional[str]
    state: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]

    model_config = {
        "from_attributes": True
    }



class PortIn(BaseModel):
    # Optional because DB handles generation via gen_random_uuid()
    port_id: Optional[UUID] = Field(None, description="Optional UUID; DB will generate if omitted")
    mac_address: Optional[str] = Field(None, description="MAC address of the port")
    port_name: str = Field(..., description="Name of the port (e.g., ae0, gig-1/0/1)")
    port_speed: str = Field(..., description="Speed of the port (e.g., 100G, 400G)")
    device_id: UUID = Field(..., description="UUID of the associated device")
    port_description: Optional[str] = Field(None, description="Description of the port")
    port_optic: Optional[str] = Field(None, description="Optic type (e.g., 400G-LR4)")
    port_tagging: Optional[str] = Field(None, description="Tagging mode (Untagged, Tagged)")
    port_cktid: Optional[str] = Field(None, description="Circuit ID associated with the port")
    customer_id: Optional[UUID] = Field(None, description="UUID of the associated customer")
    port_service_status: str = Field(..., description="Service status (Available, Assigned, etc.)")
    port_type: str = Field(..., description="Type of port (Physical, LAG, UNI, ENNI)")
    port_health_status: Optional[int] = Field(4, description="Health status code")
    admin_status: Optional[str] = Field("up", description="Administrative status")
    oper_status: Optional[str] = Field("down", description="Operational status")

class PortOut(BaseModel):
    port_id: UUID 
    mac_address: Optional[str] = None
    port_name: str
    port_speed: str
    device_id: UUID
    port_description: Optional[str] = None
    port_optic: Optional[str] = None
    port_tagging: Optional[str] = None
    port_cktid: Optional[str] = None
    customer_id: Optional[UUID] = None # Fixed typo from 'cusotmer_id'
    port_service_status: str
    port_type: str
    port_health_status: Optional[int] = None
    admin_status: str
    oper_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) 

class PortUpdate(BaseModel):
    # For updates, we make everything Optional so we only send what changed
    mac_address: Optional[str] = None
    port_name: Optional[str] = None
    port_speed: Optional[str] = None
    device_id: Optional[UUID] = None
    port_description: Optional[str] = None
    port_optic: Optional[str] = None
    port_tagging: Optional[str] = None
    port_cktid: Optional[str] = None
    customer_id: Optional[UUID] = None
    port_service_status: Optional[str] = None
    port_type: Optional[str] = None
    port_health_status: Optional[int] = None
    admin_status: Optional[str] = None
    oper_status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class FabricConnectionIn(BaseModel):
    # This is the "Create" model
    service_id: UUID 
    # connection_id is now optional. 
    # If the frontend doesn't send it, Postgres will generate it.
    connection_id: Optional[UUID] = None  
    connection_name: Optional[str] = None
    connector_a_id: Optional[UUID] = None
    connector_b_id: Optional[UUID] = None
    connector_a_table: Optional[str] = None
    connector_b_table: Optional[str] = None
    connection_status: Optional[str] = "Not Configured"
    vrf_name: Optional[str] = None
    service_bw: Optional[int] = None
    s_vlan: Optional[int] = 0
    c_vlan_list: Optional[str] = ""
    health_status: Optional[int] = 4

class FabricConnectionUpdate(BaseModel):
    # Everything is optional here because we might only update one field
    connection_name: Optional[str] = None
    connector_a_id: Optional[UUID] = None
    connector_b_id: Optional[UUID] = None
    connector_a_table: Optional[str] = None
    connector_b_table: Optional[str] = None
    connection_status: Optional[str] = None
    vrf_name: Optional[str] = None
    service_bw: Optional[int] = None
    s_vlan: Optional[int] = None
    c_vlan_list: Optional[str] = None
    health_status: Optional[int] = None

class FabricConnectionOut(BaseModel):
    # This is what we send BACK to the UI (includes the generated ID)
    connection_id: UUID
    service_id: UUID
    connection_name: Optional[str] = None
    connector_a_id: Optional[UUID] = None
    connector_b_id: Optional[UUID] = None
    connector_a_table: Optional[str] = None
    connector_b_table: Optional[str] = None
    connection_status: Optional[str] = None
    vrf_name: Optional[str] = None
    service_bw: Optional[int] = None
    s_vlan: Optional[int] = None
    c_vlan_list: Optional[str] = None
    health_status: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)

class InterfaceDetailOut(BaseModel):
    interface_id: UUID
    # Make this optional to handle unpatched interfaces
    port_id: Optional[UUID] = None  
    service_id: Optional[UUID] = None  
    
    ckt_id: Optional[str] = None
    description: Optional[str] = None

    interface_name: str
    interface_type: str

    svlan_id: Optional[int] = None
    cvlan_list: Optional[str] = None

    # Note: DB might return String, but Pydantic will try to cast to bool
    dhcp_relay_enabled: Optional[bool] = None
    service_bw_mbps: Optional[int] = None

    status: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    # Handle the "object full of nulls" issue
    port: Optional[PortOut] = None 
    
    # Ensure these default to empty lists if the JSONB is empty/null
    ip_addresses: List[IPInterfaceOut] = []
    bgp_neighbors: List[BGPNeighborOut] = []
    static_routes: List[StaticRouteOut] = []
   
    model_config = ConfigDict(from_attributes=True)

    @field_validator('port', mode='before')
    @classmethod
    def filter_empty_json_objects(cls, v):
        """
        Cleans up the 'port' object. If the port_id inside the JSON is null,
        it means the interface isn't patched, so we return None.
        """
        if isinstance(v, dict):
            # If the primary identifier is missing, the whole object is effectively null
            if v.get('port_id') is None:
                return None
        return v

    @field_validator('ip_addresses', 'bgp_neighbors', mode='before')
    @classmethod
    def ensure_list(cls, v):
        """
        Ensures that if the DB returns None or a non-list, we return an empty list.
        """
        if v is None:
            return []
        return v

class InterfaceOut(BaseModel):
    interface_id: UUID
    port_id: Optional[UUID]
    service_id: Optional[UUID]
 
    ckt_id: Optional[str]
    description: Optional[str]

    interface_name: Optional[str]
    interface_type: Optional[str]

    svlan_id: Optional[int]
    cvlan_list: Optional[str]

    dhcp_relay_enabled: bool

    service_bw_mbps: Optional[int]
    status: str

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class InterfaceIn(BaseModel):
    port_id: Optional[UUID] = None
    service_id: Optional[UUID] = None

    ckt_id: Optional[str] = None
    description: Optional[str] = None

    interface_name: Optional[str] = None
    interface_type: Optional[str] = None

    svlan_id: Optional[int] = None
    cvlan_list: Optional[str] = None

    dhcp_relay_enabled: Optional[bool] = True

    service_bw_mbps: Optional[int] = None
    status: str

class InterfaceUpdate(BaseModel):
    port_id: Optional[UUID] = None
    service_id: Optional[UUID] = None

    ckt_id: Optional[str] = None
    description: Optional[str] = None

    interface_name: Optional[str] = None
    interface_type: Optional[str] = None

    svlan_id: Optional[int] = None
    cvlan_list: Optional[str] = None

    dhcp_relay_enabled: Optional[bool] = None

    service_bw_mbps: Optional[int] = None
    status: Optional[str] = None

    model_config = {"from_attributes": True}

class PatchPanelIn(BaseModel):
    device_id: Optional[UUID] = None
    port_number: Optional[int] = None
    local_port: Optional[UUID] = None
    remote_port: Optional[UUID] = None
    description: Optional[str] = None
    port_name: Optional[str] = None
    connector_type: Optional[str] = None
    fiber_mode: Optional[str] = None
    status: Optional[str] = None

class PatchPanelOut(PatchPanelIn):
    port_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
# --- Parent Schemas: Patch Panel ---

class CrossConnectIn(BaseModel):
    internal_circuit_id: str = Field(..., max_length=100, description="Internal, unique circuit ID.")
    local_port_id: UUID = Field(..., description="ID of the local PanelPort (Source).")
    connect_type: str = Field(..., max_length=50, description="Type of connection (e.g., A-Z, Customer).")
    status: str = Field(..., max_length=20, description="Status of the cross connect.")

    remote_port_id: Optional[UUID] = Field(None, description="ID of the remote PanelPort (Destination).")
    service_description: Optional[str] = None
    loa_number: Optional[str] = None
    mrc: Decimal = Field(Decimal("150.00"), max_digits=10, decimal_places=2)
    nrc: Decimal = Field(Decimal("500.00"), max_digits=10, decimal_places=2)
    activation_date: Optional[date] = None

class CrossConnectUpdate(BaseModel):
    # All fields optional for update
    internal_circuit_id: Optional[str] = None
    local_port_id: Optional[UUID] = None
    remote_port_id: Optional[UUID] = None
    connect_type: Optional[str] = None
    service_description: Optional[str] = None
    loa_number: Optional[str] = None
    mrc: Optional[Decimal] = None
    nrc: Optional[Decimal] = None
    status: Optional[str] = None
    activation_date: Optional[date] = None

class CrossConnectOut(CrossConnectIn):
    connect_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {Decimal: lambda v: str(v)} # Ensure Decimal converts cleanly to string/JSON

class HardwareSpecsIn(BaseModel):
    # Required Fields
    model_name: str = Field(..., max_length=100)
    power_source_id: UUID

    # Optional Fields
    manufacturer: Optional[str] = None
    weight_kg: Optional[Decimal] = Field(None, decimal_places=2)
    height_mm: Optional[Decimal] = Field(None, decimal_places=2)
    width_mm: Optional[Decimal] = Field(None, decimal_places=2)
    depth_mm: Optional[Decimal] = Field(None, decimal_places=2)
    
    power_rating_w: Optional[Decimal] = Field(None, decimal_places=2)
    airflow_direction: Optional[str] = None
    typical_environment: Optional[str] = None
    max_environment_tempc: Optional[Decimal] = Field(None, decimal_places=2)
    min_environment_tempc: Optional[Decimal] = Field(None, decimal_places=2)
    
    nebs_level: Optional[str] = None
    nebs_status: Optional[bool] = None
    certification_data: Optional[str] = None

class HardwareSpecsUpdate(BaseModel):
    # All fields optional for update
    model_name: Optional[str] = None
    manufacturer: Optional[str] = None
    weight_kg: Optional[Decimal] = None
    height_mm: Optional[Decimal] = None
    width_mm: Optional[Decimal] = None
    depth_mm: Optional[Decimal] = None
    power_source_id: Optional[UUID] = None
    power_rating_w: Optional[Decimal] = None
    airflow_direction: Optional[str] = None
    typical_environment: Optional[str] = None
    max_environment_tempc: Optional[Decimal] = None
    min_environment_tempc: Optional[Decimal] = None
    nebs_level: Optional[str] = None
    nebs_status: Optional[bool] = None
    certification_data: Optional[str] = None

class HardwareSpecsOut(HardwareSpecsIn):
    hardware_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {Decimal: lambda v: str(v)} # Ensure Decimal converts cleanly to JSON

class HardwareDocumentIn(BaseModel):
    # Required Fields
    hardware_id: UUID
    document_name: str = Field(..., max_length=255, description="User-friendly name of the document.")
    storage_path: str = Field(..., max_length=512, description="The path or URL where the document file is stored.")

    # Optional Fields
    document_type: Optional[str] = None

class HardwareDocumentUpdate(BaseModel):
    # All fields optional for update
    hardware_id: Optional[UUID] = None
    document_name: Optional[str] = None
    storage_path: Optional[str] = None
    document_type: Optional[str] = None

class HardwareDocumentOut(HardwareDocumentIn):
    document_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LRICCostModelIn(BaseModel):
    # Required Fields
    model_id: UUID
    model_type: str = Field(..., max_length=50, description="The type of resource this cost model applies to (Device, Port, etc.).")
    base_cost: Decimal = Field(..., decimal_places=4, description="The raw cost of the resource.")
    
    # Optional Fields
    description: Optional[str] = None
    min_fill: Optional[int] = Field(None, ge=0)
    lric_fill: Optional[int] = Field(None, ge=0, le=100) # Percentage constraint enforced by DB
    type: Optional[str] = None
    min_level: Optional[Decimal] = Field(None, decimal_places=4)
    level: Optional[Decimal] = Field(None, decimal_places=4)

class LRICCostModelUpdate(BaseModel):
    # All fields optional for update
    model_id: Optional[UUID] = None
    model_type: Optional[str] = None
    description: Optional[str] = None
    base_cost: Optional[Decimal] = None
    min_fill: Optional[int] = None
    lric_fill: Optional[int] = None
    type: Optional[str] = None
    min_level: Optional[Decimal] = None
    level: Optional[Decimal] = None

class LRICCostModelOut(LRICCostModelIn):
    cost_model_id: UUID
    
    # Include the calculated cost for output
    calculated_lric_cost: Optional[Decimal] = Field(None, decimal_places=4)
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {Decimal: lambda v: str(v)}

class DeviceLocationIn(BaseModel):
    # Required Fields
    device_id: UUID
    rack_identifier: str = Field(..., max_length=20)
    location: str = Field(..., max_length=100)
    
    # Optional Fields
    clli: Optional[str] = Field(None, max_length=8)
    floor_number: Optional[str] = None
    aisle_identifier: Optional[str] = None
    rack_start_ru: Optional[int] = None
    ru_height: Optional[int] = None
    description: Optional[str] = None

class DeviceLocationUpdate(BaseModel):
    # All fields optional for update, but device_id cannot be changed (it's the PK)
    clli: Optional[str] = None
    location: Optional[str] = None
    floor_number: Optional[str] = None
    rack_identifier: Optional[str] = None
    aisle_identifier: Optional[str] = None
    rack_start_ru: Optional[int] = None
    ru_height: Optional[int] = None
    description: Optional[str] = None

class DeviceLocationOut(DeviceLocationIn):
    # date_added is treated as non-timezone-aware in the DB, so we use datetime without timezone conversion here
    date_added: Optional[datetime]
    
    class Config:
        from_attributes = True

class GalileoDeviceDetail(BaseModel):
    device_name: str
    role: str
    health: int
    status: str
    device_id: UUID

    class Config:
        from_attributes = True
        
class GalileoNodesOut(BaseModel):
    location_name: str
    location_lat: Decimal
    location_long: Decimal
    location_x: int
    location_y: int
    location_health_max: int
    # This captures the enriched list of devices for the hover-over
    devices_list: List[GalileoDeviceDetail]

    class Config:
        from_attributes = True



class GalileoLinksOut(BaseModel):
    link_id: UUID
    link_type: Optional[str]
    description: str    
    a_port_id: UUID
    b_port_id: UUID
    a_device_location: str
    a_x: int
    a_y: int
    b_device_location: str
    b_x: int
    b_y: int
    link_health: int

    class Config:
        from_attributes = True

class NetworkLocationOut(BaseModel):
    network: str
    location_id: UUID
    location_code: str
    short_name: str | None
    location_name: str
    city: str
    state: str
    country: str

    class Config:
        orm_mode = True

class VNetworkLinksLAGOut(BaseModel):
    link_id: UUID
    link_type: Optional[str]
    description: Optional[str]
    channel: Optional[int]
    frequency: Optional[Decimal]

    created_at: datetime
    updated_at: datetime

    a_port_id: Optional[UUID]
    a_port_name: Optional[str]
    a_port_type: Optional[str]
    a_port_speed: Optional[str]
    a_port_health_status: Optional[int]

    b_port_id: Optional[UUID]
    b_port_name: Optional[str]
    b_port_type: Optional[str]
    b_port_speed: Optional[str]
    b_port_health_status: Optional[int]
    
    device_id: Optional[UUID]
    device_name: Optional[str]
    device_role: Optional[str]
    device_vendor: Optional[str]
    device_location: Optional[str]

    class Config:
        from_attributes = True

class VNetworkLinksDetailOut(BaseModel):
    link_id: UUID
    link_type: str
    description: Optional[str]
    channel: Optional[int]
    frequency: Optional[int]
    created_at: datetime
    updated_at: datetime
    link_health_status: Optional[int]

    a_port_id: Optional[UUID]
    a_port_name: Optional[str]
    a_port_speed: Optional[str]
    a_port_type: Optional[str]
    a_port_service_status: Optional[str]
    a_port_health_status: Optional[int]

    a_device_id: Optional[UUID]
    a_device_name: Optional[str]
    a_device_role: Optional[str]
    a_device_vendor: Optional[str]
    a_device_location: Optional[str]
    a_device_health_status: Optional[int]
    a_device_latitude: Optional[float]
    a_device_longitude: Optional[float]

    b_port_id: Optional[UUID]
    b_port_name: Optional[str]
    b_port_speed: Optional[str]
    b_port_type: Optional[str]
    b_port_service_status: Optional[str]
    b_port_health_status: Optional[int]

    b_device_id: Optional[UUID]
    b_device_name: Optional[str]
    b_device_role: Optional[str]
    b_device_vendor: Optional[str]
    b_device_location: Optional[str]
    b_device_health_status: Optional[int]
    b_device_latitude: Optional[float]
    b_device_longitude: Optional[float]

    a_network: Optional[str]
    b_network: Optional[str]

    class Config:
        orm_mode = True


class RoleCount(BaseModel):
    role: Optional[str] = "Unknown"  # Allows nulls from the DB and defaults to "Unknown"
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

    class Config:
        from_attributes = True

class NetworkLinkIn(BaseModel):
    # --- Endpoint A (Source) ---
    endpoint_a: UUID = Field(..., description="UUID of the A-side endpoint (port or interface).")
    endpoint_a_type: str = Field(
        ..., max_length=20, description="Type of A-side endpoint ('port' or 'interface')."
    )

    # --- Endpoint B (Destination) ---
    endpoint_b: UUID = Field(..., description="UUID of the B-side endpoint.")
    endpoint_b_type: str = Field(
        ..., max_length=20, description="Type of B-side endpoint ('port' or 'interface')."
    )

    # --- Link Attributes ---
    link_type: str = Field(
        ..., max_length=30, description="Link type (e.g., 'port-to-port', 'interface-to-interface')."
    )
    description: Optional[str] = Field(None, max_length=512)

    # --- ROP Specific Attributes ---
    channel: Optional[int] = Field(
        None, ge=0, le=64, description="Channel ID (1–32) for ROP links."
    ) 
    frequency: Optional[Decimal] = Field(
        None, description="Frequency value for ROP links (NUMERIC(12) in DB)."
    )

class NetworkLinkUpdate(BaseModel):
    # All fields optional for partial update
    endpoint_a: Optional[UUID] = None
    endpoint_a_type: Optional[str] = None

    endpoint_b: Optional[UUID] = None
    endpoint_b_type: Optional[str] = None

    link_type: Optional[str] = None
    description: Optional[str] = None

    channel: Optional[int] = Field(None, ge=1, le=32)
    frequency: Optional[Decimal] = None

class NetworkLinkOut(NetworkLinkIn):
    link_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ROPChannelMemberIn(BaseModel):
    # Required Fields
    rop_link_id: UUID = Field(..., description="The NetworkLink UUID of the parent ROP.")
    channel_id: int = Field(..., ge=0, le=64, description="The unique channel number within this ROP.")
    
    a_side_endpoint_id: UUID = Field(..., description="UUID of the A-side interface/port.")
    a_side_endpoint_type: str = Field(..., max_length=50) 

    z_side_endpoint_id: UUID = Field(..., description="UUID of the Z-side interface/port.")
    z_side_endpoint_type: str = Field(..., max_length=50) 

    # Optional Fields
    description: Optional[str] = None

class ROPChannelMemberUpdate(BaseModel):
    # All fields optional for update
    rop_link_id: Optional[UUID] = None
    channel_id: Optional[int] = Field(None, ge=0, le=32)
    a_side_endpoint_id: Optional[UUID] = None
    a_side_endpoint_type: Optional[str] = None
    z_side_endpoint_id: Optional[UUID] = None
    z_side_endpoint_type: Optional[str] = None
    description: Optional[str] = None

class ROPChannelMemberOut(ROPChannelMemberIn):
    rop_member_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class LocationIn(BaseModel):
    location_code: str
    short_name: Optional[str] = None
    location_name: str
    address: Optional[str] = None
    city: str
    state: str
    postal_code: Optional[str] = None
    country: str
    timezone_name: Optional[str] = None
    timezone_offset: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    availability_zone: Optional[str] = None

class LocationUpdate(BaseModel):
    location_code: Optional[str] = None
    short_name: Optional[str] = None
    location_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    timezone_name: Optional[str] = None
    timezone_offset: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    availability_zone: Optional[str] = None

class LocationOut(BaseModel):
    location_id: UUID
    location_code: str
    short_name: Optional[str]
    location_name: str
    address: Optional[str]
    city: str
    state: str
    postal_code: Optional[str]
    country: str
    timezone_name: Optional[str]
    timezone_offset: Optional[int]
    latitude: Optional[float]
    longitude: Optional[float]
    availability_zone: Optional[str]
    created_at: datetime
    updated_at: datetime

class ErrorResponse(BaseModel):
    error: str
    reason: Optional[str] = None
    hint: Optional[str] = None
    message: Optional[str] = None

class DeleteResponse(BaseModel):
   detail: str


class FECSummary(BaseModel):
    fec_id: UUID
    bucket_start: datetime
    granularity: str
    device_a_name: str
    device_b_name: str
    fec_label: str
    avg_mbps: float
    min_mbps: float
    max_mbps: float
    p95_mbps: float
    total_mbps: float

class PopSummary(BaseModel):
    pop: str

    # traffic
    pop_total_egress_traffic: float
    local_egress_traffic: float
    intra_egress_traffic: float
    inter_egress_traffic: float
    inter_ingress_traffic: float

    # global %
    pop_egress_pct_of_global: float
    pop_ingress_pct_of_global: float

    # optional derived fields (good for UI)
  

class GlobalTrafficSummary(BaseModel):
    region: str
    provider: str

    total_pops: int
    total_routers: int

    total_router_bytes: float
    total_intra_bytes: float
    total_inter_bytes: float
    total_bytes: float

    avg_router_pct: float
    avg_intra_pct: float
    avg_inter_pct: float

    class Config:
        from_attributes = True


class TrafficRouterDetail(BaseModel):
    # ✅ identity
    row_type: str
    row_id: str
    router: str

    # ✅ traffic totals
    router_bytes: float
    intra_bytes: float
    inter_bytes: float
    total_bytes: float

    # ✅ composition (% router)
    router_pct_of_router: float
    intra_pct_of_router: float
    inter_pct_of_router: float

    # ✅ global context
    global_bytes: float
    pct_of_global: float

    # ✅ directional traffic
    router_egress_bytes: float
    intra_egress_bytes: float
    inter_egress_bytes: float
    inter_ingress_bytes: float

    # ✅ enrichment (nullable safe)
    country: str | None = None
    provider_tag: str | None = None
    region_tag: str | None = None

    class Config:
        from_attributes = True
        
class PopSummary(BaseModel):
    pop: str

    pop_total_egress_traffic: Decimal
    local_egress_traffic: Decimal
    intra_egress_traffic: Decimal
    inter_egress_traffic: Decimal
    inter_ingress_traffic: Decimal

    pop_egress_pct_of_global: Decimal
    pop_ingress_pct_of_global: Decimal


class PopSummaryResponse(BaseModel):
    global_: GlobalTrafficSummary = Field(..., alias="global")
    pops: List[PopSummary]

    class Config:
        # ✅ allows "global" in JSON while using global_ in Python
        allow_population_by_field_name = True

        # ✅ enables ORM compatibility
        from_attributes = True   # Pydantic v2
        # orm_mode = True        # use this instead if on Pydantic v1

class PopToPopTraffic(BaseModel):
    row_type: str
    row_id: str

    pop: str
    egress_pop: Optional[str]

    router_bytes: Optional[float]
    intra_bytes: Optional[float]
    inter_bytes: Optional[float]
    pop_total_bytes: Optional[float]

    router_pct_of_pop: Optional[float]
    intra_pct_of_pop: Optional[float]
    inter_pct_of_pop: Optional[float]

    global_bytes: Optional[float]
    pct_of_global: Optional[float]

    router_egress_bytes: Optional[float]
    intra_egress_bytes: Optional[float]
    inter_egress_bytes: Optional[float]
    inter_ingress_bytes: Optional[float]

    ingress_country: Optional[str]
    ingress_provider_tag: Optional[str]
    ingress_region_tag: Optional[str]

    egress_country: Optional[str]
    egress_provider_tag: Optional[str]
    egress_region_tag: Optional[str]

    class Config:
        orm_mode = True

from pydantic import BaseModel
from typing import Optional

class PopToPopFlow(BaseModel):
    rank: int

    src_pop: str
    dst_pop: str

    total_bytes: float
    router_bytes: float
    intra_bytes: float
    inter_bytes: float

    src_location: Optional[str]
    src_city: Optional[str]
    src_region: Optional[str]
    src_provider: Optional[str]

    dst_location: Optional[str]
    dst_city: Optional[str]
    dst_region: Optional[str]
    dst_provider: Optional[str]

    class Config:
        from_attributes = True

class PopToPopTraffic(BaseModel):
    rank: int

    src_pop: str
    dst_pop: str

    total_bytes: float
    router_bytes: float
    intra_bytes: float
    inter_bytes: float

    src_location: Optional[str]
    src_city: Optional[str]
    src_state: Optional[str]
    src_country: Optional[str]
    src_region: Optional[str]
    src_provider: Optional[str]

    dst_location: Optional[str]
    dst_city: Optional[str]
    dst_state: Optional[str]
    dst_country: Optional[str]
    dst_region: Optional[str]
    dst_provider: Optional[str]

class PopSummary(BaseModel):
    pop: str
    rank: int

    # ✅ location
    location_name: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    timezone: Optional[str]

    # ✅ metadata
    region: Optional[str]
    provider: Optional[str]

    # ✅ metrics
    pop_total_egress_traffic: float

    local_egress_traffic: float
    intra_egress_traffic: float
    inter_egress_traffic: float

    inter_ingress_traffic: Optional[float] = None

    # ✅ percentages
    local_pct_of_pop: float
    intra_pct_of_pop: float
    inter_egress_pct_of_pop: float

    pop_egress_pct_of_global: Optional[float] = None
    pop_ingress_pct_of_global: Optional[float] = None

class PopSummaryResponse(BaseModel):
    pops: List[PopSummary]

class Flow(BaseModel):
    peer_router: str
    peer_pop: str
    flow_type: str

    flow_bytes: float

    # EITHER one will exist depending on direction
    pct_of_router_egress: Optional[float] = None
    pct_of_router_ingress_topn: Optional[float] = None

    peer_location_name: str
    peer_city: Optional[str] = None
    peer_state: Optional[str] = None
    peer_country: Optional[str] = None

    class Config:
        from_attributes = True

class RouterSummary(BaseModel):
    
    report_date: date
    router: str

    pop: Optional[str]
    short_name: Optional[str]
    location_name: str
    location_code: Optional[str]

    city: Optional[str]
    state: Optional[str]
    country: Optional[str]

    latitude: Optional[float]
    longitude: Optional[float]
    timezone_name: Optional[str]

    local_egress_bytes: float
    intra_egress_bytes: float
    inter_egress_bytes: float

    router_egress_total_bytes: float
    inter_ingress_total_bytes: float
    global_egress_bytes: float

    pct_router_egress_of_global: float
    pct_local_of_router_egress: float
    pct_intra_of_router_egress: float
    pct_inter_of_router_egress: float

    class Config:
        from_attributes = True

class RouterDetailResponse(BaseModel):
    summary: RouterSummary
    egress_flows: List[Flow]
    ingress_flows: List[Flow]

    class Config:
        from_attributes = True
        
class RouterSummary(BaseModel):
    report_date: date
    router: str

    pop: str | None = None
    short_name: str | None = None
    location_name: str
    location_code: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    timezone_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    local_egress_bytes: float
    intra_egress_bytes: float
    inter_egress_bytes: float
    router_egress_total_bytes: float
    inter_ingress_total_bytes: float

    global_egress_bytes: float

    pct_router_egress_of_global: float
    pct_local_of_router_egress: float
    pct_intra_of_router_egress: float
    pct_inter_of_router_egress: float

    class Config:
        from_attributes = True

class PopToPopTrafficSchema(BaseModel):
    row_type: str
    row_id: str

    pop: str
    egress_pop: Optional[str]

    router_bytes: int
    intra_bytes: int
    inter_bytes: int
    pop_total_bytes: int

    router_pct_of_pop: Optional[float]
    intra_pct_of_pop: Optional[float]
    inter_pct_of_pop: Optional[float]

    global_bytes: int
    pct_of_global: Optional[float]

    ingress_location_name: Optional[str]
    ingress_city: Optional[str]
    ingress_state: Optional[str]
    ingress_country: Optional[str]
    ingress_latitude: Optional[float]
    ingress_longitude: Optional[float]
    ingress_availability_zone: Optional[str]
    ingress_timezone_name: Optional[str]
    ingress_timezone_offset: Optional[int]

    ingress_provider: Optional[str]
    ingress_region: Optional[str]

    egress_location_name: Optional[str]
    egress_city: Optional[str]
    egress_state: Optional[str]
    egress_country: Optional[str]
    egress_latitude: Optional[float]
    egress_longitude: Optional[float]
    egress_availability_zone: Optional[str]
    egress_timezone_name: Optional[str]
    egress_timezone_offset: Optional[int]

    egress_provider: Optional[str]
    egress_region: Optional[str]

    ingress_bytes: Optional[int]

    class Config:
        orm_mode = True
