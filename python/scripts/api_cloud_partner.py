"""
api_routing_interface.py
Summary view accessors for all analytics views.
"""

import logging
from uuid import UUID
from typing import Optional,List
from sqlalchemy import select
from sqlalchemy.orm import Session

from scripts.api_schema import BGPNeighborIn, BGPNeighborUpdate, InterfaceIn, InterfaceUpdate, RoutingPolicyIn, RoutingPolicyUpdate, StaticRouteIn, StaticRouteUpdate
from scripts.api_model import (
    BGPNeighbor,
    RoutingPolicy,
    StaticRoute,
    Interface
)

logger = logging.getLogger(__name__)

# ============================================================
#  INTERNAL HELPER (UNIFIED FETCH PATTERN)
# ============================================================

