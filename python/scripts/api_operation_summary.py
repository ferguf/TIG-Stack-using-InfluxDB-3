"""
operations_summary.py
Summary view accessors for all analytics views.
"""

import logging
from sqlalchemy import select
from sqlalchemy.orm import Session

from scripts.api_model import (
    VTelegrafInventory,
    VSummaryDevices,
    VSummaryPorts,
    VSummaryLinks,
    VSummaryLinksByLocation,
    VSummaryCustomers,
    VSummaryServices,
    VSummaryConnections,
)

logger = logging.getLogger(__name__)

# ============================================================
#  INTERNAL HELPER (UNIFIED FETCH PATTERN)
# ============================================================

def _fetch_all(db: Session, model):
    """Unified accessor for all summary views."""
    stmt = select(model)
    return db.execute(stmt).mappings().all()

# ============================================================
#  SUMMARY VIEW ACCESSORS (CLEAN + STANDARDIZED)
# ============================================================
def get_telegraf_inventory(db):
    return db.query(VTelegrafInventory).all()

def get_summary_devices(db: Session):
    return _fetch_all(db, VSummaryDevices)

def get_summary_ports(db: Session):
    return _fetch_all(db, VSummaryPorts)

def get_summary_links(db: Session):
    return _fetch_all(db, VSummaryLinks)

def get_summary_links_by_location(db: Session):
    return _fetch_all(db, VSummaryLinksByLocation)

def get_summary_customers(db: Session):
    return _fetch_all(db, VSummaryCustomers)

def get_summary_services(db: Session):
    return _fetch_all(db, VSummaryServices)

def get_summary_connections(db: Session):
    return _fetch_all(db, VSummaryConnections)