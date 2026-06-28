"""
Pydantic schemas for billing domain
File: Scripts/billing/schema.py
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# =========================================================
# SHARED BASE
# =========================================================

def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class BaseModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
        use_enum_values=True,
    )


# =========================================================
# BILLING MODEL
# =========================================================

class BillingModelCreate(BaseModel):
    code: str
    description: str
    is_usage_based: bool
    bandwidth_change_allowed: bool


class BillingModelUpdate(BaseModel):
    code: Optional[str] = None
    description: Optional[str] = None
    is_usage_based: Optional[bool] = None
    bandwidth_change_allowed: Optional[bool] = None


class BillingModelResponse(BaseModel):
    id: UUID
    code: str
    description: str
    is_usage_based: bool
    bandwidth_change_allowed: bool


# =========================================================
# BILLING RATE CARD
# =========================================================

class BillingRateCreate(BaseModel):
    name: str
    currency_code: str = "USD"
    effective_start_ts: datetime
    effective_end_ts: Optional[datetime] = None
    is_active: bool = True


class BillingRateUpdate(BaseModel):
    name: Optional[str] = None
    currency_code: Optional[str] = None
    effective_start_ts: Optional[datetime] = None
    effective_end_ts: Optional[datetime] = None
    is_active: Optional[bool] = None


class BillingRateResponse(BaseModel):
    id: UUID
    name: str
    currency_code: str
    effective_start_ts: datetime
    effective_end_ts: Optional[datetime]
    is_active: bool
    created_at: Optional[datetime] = None


# =========================================================
# BILLING PORT SPEED
# =========================================================

class BillingPortSpeedResponse(BaseModel):
    port_speed_mbps: int


# =========================================================
# BILLING PORT RATE
# =========================================================

class BillingPortCreate(BaseModel):
    rate_id: UUID
    port_speed_mbps: int
    nrc_amount: Decimal = Decimal("0")
    mrc_amount: Decimal = Decimal("0")

    @field_validator("port_speed_mbps")
    @classmethod
    def validate_port_speed(cls, v: int):
        if v <= 0:
            raise ValueError("portSpeedMbps must be greater than 0")
        return v


class BillingPortUpdate(BaseModel):
    rate_id: Optional[UUID] = None
    port_speed_mbps: Optional[int] = None
    nrc_amount: Optional[Decimal] = None
    mrc_amount: Optional[Decimal] = None


class BillingPortResponse(BaseModel):
    id: UUID
    rate_id: UUID
    port_speed_mbps: int
    nrc_amount: Decimal
    mrc_amount: Decimal
    
    created_at: Optional[datetime] = None

# =========================================================
# BILLING ACCESS RATE
# =========================================================


class BillingAccessUpdate(BaseModel):
    rate_id: Optional[UUID] = None
    access_code: Optional[str] = None
    port_speed_mbps: int
    location_type: Optional[str] = None
    nrc_amount: Optional[Decimal] = None
    mrc_amount: Optional[Decimal] = None


class BillingAccessResponse(BaseModel):
    id: UUID
    rate_id: UUID
    access_code: str
    port_speed_mbps: int
    location_type: str
    nrc_amount: Decimal
    mrc_amount: Decimal
    
    created_at: Optional[datetime] = None



# =========================================================
# BILLING BANDWIDTH RATE
# =========================================================

class BillingBwCreate(BaseModel):
    rate_id: UUID
    service_type: str
    service_bw_mbps: int
    nrc_amount: Decimal = Decimal("0")
    mrc_amount: Decimal = Decimal("0")

    # The decorator must ONLY reference fields that exist in the class above
    @field_validator("service_bw_mbps")
    @classmethod
    def validate_positive_bandwidth(cls, v: int):
        if v <= 0:
            raise ValueError("bandwidth values must be greater than 0")
        return v


class BillingBwUpdate(BaseModel):
    rate_id: Optional[UUID] = None
    service_type: Optional[str] = None
    port_speed_mbps: Optional[int] = None
    service_bw_mbps: Optional[int] = None
    nrc_amount: Optional[Decimal] = None
    mrc_amount: Optional[Decimal] = None


class BillingBwResponse(BaseModel):
    id: UUID
    rate_id: UUID
    service_type: str
    
    # port_speed_mbps is completely removed from here
    service_bw_mbps: int
    
    nrc_amount: Decimal
    mrc_amount: Decimal
    created_at: Optional[datetime] = None
# =========================================================
# BILLING TOKEN RATE
# =========================================================

class BillingTokenCreate(BaseModel):
    rate_id: UUID
    service_type: str
    port_speed_mbps: int
    included_gb_per_month: Decimal = Decimal("0")
    mrc_amount: Decimal = Decimal("0")

    @field_validator("port_speed_mbps")
    @classmethod
    def validate_port_speed(cls, v: int):
        if v <= 0:
            raise ValueError("portSpeedMbps must be greater than 0")
        return v


class BillingTokenUpdate(BaseModel):
    rate_id: Optional[UUID] = None
    service_type: Optional[str] = None
    token_cost_per_gb: Optional[Decimal] = None
    included_gb_per_month: Optional[Decimal] = None
    mrc_amount: Optional[Decimal] = None


class BillingTokenResponse(BaseModel):
    id: UUID
    rate_id: UUID
    service_type: str
    token_cost_per_gb: Decimal
    included_gb_per_month: Decimal
    mrc_amount: Decimal


# =========================================================
# BILLING PROVIDER
# =========================================================

class BillingProviderCreate(BaseModel):
    name: str
    code: str
    is_active: bool = True


class BillingProviderUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    is_active: Optional[bool] = None


class BillingProviderResponse(BaseModel):
    id: UUID
    name: str
    code: str
    is_active: bool


# =========================================================
# BILLING PROVIDER MODEL SUPPORT
# =========================================================

class BillingProviderModelCreate(BaseModel):
    provider_id: UUID
    model_id: UUID
    is_supported: bool = True


class BillingProviderModelUpdate(BaseModel):
    provider_id: Optional[UUID] = None
    model_id: Optional[UUID] = None
    is_supported: Optional[bool] = None


class BillingProviderModelResponse(BaseModel):
    id: UUID
    provider_id: UUID
    model_id: UUID
    is_supported: bool


# =========================================================
# BILLING PROVIDER PORT RATE
# =========================================================

class BillingProviderPortCreate(BaseModel):
    provider_id: UUID
    port_speed_mbps: int
    nrc_amount: Decimal = Decimal("0")
    mrc_amount: Decimal = Decimal("0")


class BillingProviderPortUpdate(BaseModel):
    provider_id: Optional[UUID] = None
    port_speed_mbps: Optional[int] = None
    nrc_amount: Optional[Decimal] = None
    mrc_amount: Optional[Decimal] = None


class BillingProviderPortResponse(BaseModel):
    id: UUID
    provider_id: UUID
    port_speed_mbps: int
    nrc_amount: Decimal
    mrc_amount: Decimal


# =========================================================
# BILLING PROVIDER SERVICE RATE
# =========================================================

class BillingProviderSvcCreate(BaseModel):
    provider_id: UUID
    service_type: str
    mrc_amount: Decimal = Decimal("0")


class BillingProviderSvcUpdate(BaseModel):
    provider_id: Optional[UUID] = None
    service_type: Optional[str] = None
    mrc_amount: Optional[Decimal] = None


class BillingProviderSvcResponse(BaseModel):
    id: UUID
    provider_id: UUID
    service_type: str
    mrc_amount: Decimal


# =========================================================
# BILLING PROVIDER BANDWIDTH OPTION
# =========================================================

class BillingProviderBwCreate(BaseModel):
    provider_id: UUID
    port_speed_mbps: int
    service_bw_mbps: int

    @field_validator("port_speed_mbps", "service_bw_mbps")
    @classmethod
    def validate_positive_bandwidth(cls, v: int):
        if v <= 0:
            raise ValueError("bandwidth values must be greater than 0")
        return v


class BillingProviderBwUpdate(BaseModel):
    provider_id: Optional[UUID] = None
    port_speed_mbps: Optional[int] = None
    service_bw_mbps: Optional[int] = None


class BillingProviderBwResponse(BaseModel):
    id: UUID
    provider_id: UUID
    port_speed_mbps: int
    service_bw_mbps: int


# =========================================================
# BILLING SERVICE INSTANCE
# =========================================================

class BillingSvcCreate(BaseModel):
    customer_account_id: int
    service_id: int

    rate_id: UUID
    model_id: UUID

    access_code: str
    service_type: str

    port_speed_mbps: int
    service_bw_mbps: Optional[int] = None
    token_commit_mbps: Optional[int] = None

    provider_id: Optional[UUID] = None


class BillingSvcUpdate(BaseModel):
    customer_account_id: Optional[int] = None
    service_id: Optional[int] = None
    rate_id: Optional[UUID] = None
    model_id: Optional[UUID] = None
    access_code: Optional[str] = None
    service_type: Optional[str] = None
    port_speed_mbps: Optional[int] = None
    service_bw_mbps: Optional[int] = None
    token_commit_mbps: Optional[int] = None
    provider_id: Optional[UUID] = None


class BillingSvcResponse(BaseModel):
    id: UUID
    customer_account_id: int
    service_id: int
    rate_id: UUID
    model_id: UUID
    access_code: str
    service_type: str
    port_speed_mbps: int
    service_bw_mbps: Optional[int]
    token_commit_mbps: Optional[int]
    provider_id: Optional[UUID]


# =========================================================
# BILLING USAGE
# =========================================================

class BillingUsageCreate(BaseModel):
    svc_id: UUID
    usage_start_ts: datetime
    usage_end_ts: datetime
    consumed_gb: Decimal


class BillingUsageUpdate(BaseModel):
    svc_id: Optional[UUID] = None
    usage_start_ts: Optional[datetime] = None
    usage_end_ts: Optional[datetime] = None
    consumed_gb: Optional[Decimal] = None


class BillingUsageResponse(BaseModel):
    id: UUID
    svc_id: UUID
    usage_start_ts: datetime
    usage_end_ts: datetime
    consumed_gb: Decimal


# =========================================================
# INTENT API SCHEMAS (FOR LATER / PROCESS LAYER)
# =========================================================

class BillingSvcIntentRequest(BaseModel):
    customer_account_id: int
    service_id: int
    service_type: str

    rate_id: UUID
    model_id: UUID

    access_code: str
    port_speed_mbps: int

    service_bw_mbps: Optional[int] = None
    token_commit_mbps: Optional[int] = None

    provider_id: Optional[UUID] = None
    provider_service_type: Optional[str] = None
    location_type: str = "DEFAULT"


class BillingSvcIntentResponse(BaseModel):
    success: bool
    message: str
    svc_id: Optional[UUID] = None
    created_entities: list[str] = Field(default_factory=list)

# =========================================================
# BILLING COMPOSITE VIEW
# =========================================================

class BillingCompositeResponse(BaseModel):
    rate_id: UUID
    rate_name: str
    currency_code: str
    effective_start_ts: Optional[datetime] = None
    assigned_customers: list = []
    assigned_providers: list = []
    ports: List[BillingPortResponse] = []
    access_tiers: List[BillingAccessResponse] = []
    bandwidth_ladders: List[BillingBwResponse] = []
    usage_tokens: List[BillingTokenResponse] = []

# =========================================================
# BILLING ACCESS RATE
# =========================================================

class BillingAccessCreate(BaseModel):
    rate_id: UUID
    access_code: str
    location_type: str = "DEFAULT"
    port_speed_mbps: int = 1000
    nrc_amount: Decimal = Decimal("0")
    mrc_amount: Decimal = Decimal("0")

class BillingAccessUpdate(BaseModel):
    rate_id: Optional[UUID] = None
    access_code: Optional[str] = None
    location_type: Optional[str] = None
    port_speed_mbps: Optional[int] = None
    nrc_amount: Optional[Decimal] = None
    mrc_amount: Optional[Decimal] = None

class BillingAccessResponse(BaseModel):
    id: UUID
    rate_id: UUID
    access_code: str
    location_type: str
    port_speed_mbps: int
    nrc_amount: Decimal
    mrc_amount: Decimal
    created_at: Optional[datetime] = None

# =========================================================
# BILLING USAGE TOKENS
# =========================================================

class BillingTokenCreate(BaseModel):
    rate_id: UUID
    service_type: str
    port_speed_mbps: int
    included_gb_per_month: Decimal
    token_cost_per_gb: Decimal
    mrc_amount: Decimal = Decimal("0")

class BillingTokenUpdate(BaseModel):
    rate_id: Optional[UUID] = None
    service_type: Optional[str] = None
    port_speed_mbps: Optional[int] = None
    included_gb_per_month: Optional[Decimal] = None
    token_cost_per_gb: Optional[Decimal] = None
    mrc_amount: Optional[Decimal] = None

class BillingTokenResponse(BaseModel):
    id: UUID
    rate_id: UUID
    service_type: str
    port_speed_mbps: int
    included_gb_per_month: Decimal
    token_cost_per_gb: Decimal
    mrc_amount: Decimal
    created_at: Optional[datetime] = None