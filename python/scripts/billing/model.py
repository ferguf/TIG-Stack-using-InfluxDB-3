"""
SQLAlchemy models for billing domain
Aligned to UUID schema + db_session.py
"""
from __future__ import annotations
from sqlalchemy import Column, String, Boolean, ForeignKey, Numeric, Integer, DateTime
from sqlalchemy.sql import func

import enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    text,
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from scripts.api_session import Base   # ✅ USE YOUR EXISTING BASE


# =========================================================
# ENUM MAPPINGS (DB already owns enums)
# =========================================================

class BillingModelCode(str, enum.Enum):
    FIXED = "FIXED"
    ON_DEMAND = "ON_DEMAND"
    TOKENIZED = "TOKENIZED"


class BillingAccessCode(str, enum.Enum):
    ONNET = "ONNET"
    OFFNET = "OFFNET"


# =========================================================
# REFERENCE
# =========================================================

class BillingPortSpeed(Base):
    __tablename__ = "billing_port_speed"

    port_speed_mbps = Column(Integer, primary_key=True)


# =========================================================
# BILLING MODEL
# =========================================================

class BillingModel(Base):
    __tablename__ = "billing_model"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

    code = Column(
        SqlEnum(BillingModelCode, name="billing_model_code", create_type=False),
        nullable=False,
        unique=True
    )

    description = Column(Text, nullable=False)
    is_usage_based = Column(Boolean, nullable=False)
    bandwidth_change_allowed = Column(Boolean, nullable=False)


# =========================================================
# RATE CARD
# =========================================================

class BillingRate(Base):
    __tablename__ = "billing_rate"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

    name = Column(Text, nullable=False, unique=True)
    currency_code = Column(Text, nullable=False, server_default=text("'USD'"))

    effective_start_ts = Column(DateTime(timezone=True), nullable=False)
    effective_end_ts = Column(DateTime(timezone=True))

    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))

    __table_args__ = (
        CheckConstraint(
            "effective_end_ts is null or effective_end_ts > effective_start_ts",
            name="ck_billing_rate_dates"
        ),
    )


# =========================================================
# PORT RATE
# =========================================================

class BillingPort(Base):
    __tablename__ = "billing_port"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

    rate_id = Column(UUID(as_uuid=True), ForeignKey("billing_rate.id", ondelete="CASCADE"), nullable=False)

    port_speed_mbps = Column(
        Integer,
        ForeignKey("billing_port_speed.port_speed_mbps"),
        nullable=False
    )

    nrc_amount = Column(Numeric(14, 2), nullable=False, server_default=text("0"))
    mrc_amount = Column(Numeric(14, 2), nullable=False, server_default=text("0"))

    __table_args__ = (
        UniqueConstraint("rate_id", "port_speed_mbps"),
        CheckConstraint("nrc_amount >= 0 and mrc_amount >= 0"),
    )


# =========================================================
# ACCESS RATE
# =========================================================

class CustomerRateCard(Base):
    __tablename__ = "customer_rate_cards"
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.customer_id", ondelete="CASCADE"), primary_key=True)
    rate_id = Column(UUID(as_uuid=True), ForeignKey("billing_rate.id", ondelete="CASCADE"), primary_key=True)
    assigned_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

class ProviderRateCard(Base):
    __tablename__ = "provider_rate_cards"
    provider_id = Column(UUID(as_uuid=True), ForeignKey("billing_provider.id", ondelete="CASCADE"), primary_key=True)
    rate_id = Column(UUID(as_uuid=True), ForeignKey("billing_rate.id", ondelete="CASCADE"), primary_key=True)
    assigned_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

# --- UPDATED: Billing Access Table ---

class BillingAccess(Base):
    __tablename__ = "billing_access"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default= text("gen_random_uuid()"))
    rate_id = Column(UUID(as_uuid=True), ForeignKey("billing_rate.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Using String/VARCHAR to handle the 'ONNET' / 'OFFNET' ENUM safely in ORM
    access_code = Column(String, nullable=False) 
    location_type = Column(String, nullable=False, default="DEFAULT")
    
    # NEW: Bandwidth integer for Offnet matrix scaling
    port_speed_mbps = Column(Integer, ForeignKey("billing_port_speed.port_speed_mbps"), nullable=False, default=1000)
    
    nrc_amount = Column(Numeric(14, 2), nullable=False, default=0)
    mrc_amount = Column(Numeric(14, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    rate = relationship("BillingRate", backref="access_tiers")

# =========================================================
# BANDWIDTH RATE
# =========================================================

class BillingBw(Base):
    __tablename__ = "billing_bw"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

    rate_id = Column(UUID(as_uuid=True), ForeignKey("billing_rate.id"), nullable=False)

    service_type = Column(Text, nullable=False)

    # Note: port_speed_mbps is completely gone from here
    service_bw_mbps = Column(Integer, nullable=False)

    nrc_amount = Column(Numeric(14, 2), server_default=text("0"))
    mrc_amount = Column(Numeric(14, 2), server_default=text("0"))

    __table_args__ = (
        UniqueConstraint("rate_id", "service_type", "service_bw_mbps", name="uq_billing_bw"),
    )
# =========================================================
# TOKEN RATE
# =========================================================

class BillingToken(Base):
    __tablename__ = "billing_token"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    rate_id = Column(UUID(as_uuid=True), ForeignKey("billing_rate.id"), nullable=False)
    
    service_type = Column(Text, nullable=False)
    port_speed_mbps = Column(Integer, nullable=False)
    
    included_gb_per_month = Column(Numeric(14, 2), nullable=False)
    token_cost_per_gb = Column(Numeric(14, 4), nullable=False) # 4 decimal places for granular overage costs
    
    mrc_amount = Column(Numeric(14, 2), server_default=text("0"))

    __table_args__ = (
        UniqueConstraint("rate_id", "service_type", "port_speed_mbps", name="uq_billing_token"),
    )
# =========================================================
# PROVIDER
# =========================================================

class BillingProvider(Base):
    __tablename__ = "billing_provider"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

    name = Column(Text, nullable=False, unique=True)
    code = Column(Text, nullable=False, unique=True)

    is_active = Column(Boolean, server_default=text("true"))


# =========================================================
# CUSTOMER SERVICE
# =========================================================

class BillingSvc(Base):
    __tablename__ = "billing_svc"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

    customer_account_id = Column(Integer, nullable=False)
    service_id = Column(Integer, nullable=False)

    # ✅ CORRECT: Single definition with the cascade rule applied
    rate_id = Column(UUID(as_uuid=True), ForeignKey("billing_rate.id", ondelete="CASCADE"), nullable=False)
    
    model_id = Column(UUID(as_uuid=True), ForeignKey("billing_model.id"), nullable=False)

    access_code = Column(
        SqlEnum(BillingAccessCode, name="billing_access_code", create_type=False),
        nullable=False
    )

    service_type = Column(Text, nullable=False)

    port_speed_mbps = Column(Integer, ForeignKey("billing_port_speed.port_speed_mbps"))

    service_bw_mbps = Column(Integer)
    token_commit_mbps = Column(Integer)

    provider_id = Column(UUID(as_uuid=True), ForeignKey("billing_provider.id"))

    __table_args__ = (
        CheckConstraint(
            "(service_bw_mbps is not null and token_commit_mbps is null) OR "
            "(service_bw_mbps is null and token_commit_mbps is not null)"
        ),
    )


# =========================================================
# USAGE
# =========================================================

class BillingUsage(Base):
    __tablename__ = "billing_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

    svc_id = Column(UUID(as_uuid=True), ForeignKey("billing_svc.id", ondelete="CASCADE"), nullable=False)

    usage_start_ts = Column(DateTime(timezone=True), nullable=False)
    usage_end_ts = Column(DateTime(timezone=True), nullable=False)

    consumed_gb = Column(Numeric(18, 6), nullable=False)

    __table_args__ = (
        CheckConstraint("usage_end_ts > usage_start_ts"),
    )