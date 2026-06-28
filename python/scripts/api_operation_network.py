"""
/scripts/api_operation_network.py
Domain-specific logic for Network Connectivity, Interfaces, and Galileo Visualizations.
Handles inter-router links, logical interfaces, and Harry Beck grid-snapped views.
"""

import logging
from uuid import UUID
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_ , and_
from scripts.api_model import (
    NetworkLink, VNetworkLinksDetail, VNetworkLinksLAG, 
    GalileoNodes, GalileoLinks, Interface, VNetworkDashboard,
    ROPChannelMember
)


from scripts.api_schema import NetworkLinkIn, NetworkLinkUpdate, InterfaceIn, ROPChannelMemberIn

logger = logging.getLogger(__name__)

# --- Galileo Topological Views ---

def get_galileo_nodes(db: Session) -> List[GalileoNodes]:
    """
    Fetches the Harry Beck grid-snapped city hubs (NYC1, DEN1, SFO1).
    Includes the 'backpack' of internal devices from the Postgres view.
    """
    return db.query(GalileoNodes).all()

def get_galileo_links(db: Session) -> List[GalileoLinks]:
    """
    Fetches the inter-city connectivity fabric with snapped coordinates.
    Provides the clean A-to-B lines for the Plotly 'Beck' map.
    """
    return db.query(GalileoLinks).all()

# --- Network Link Management ---

def get_network_links(db: Session) -> List[NetworkLink]:
    """Fetches all raw network links from the base table."""
    return db.query(NetworkLink).all()

def get_network_link_by_id(db: Session, link_id: UUID) -> Optional[NetworkLink]:
    """Retrieves a specific link record by UUID."""
    return db.query(NetworkLink).filter(NetworkLink.link_id == link_id).first()

def get_network_summary(db: Session):
    return db.query(NetworkSummary).all()

def get_network_links_detail(db: Session) -> List[VNetworkLinksDetail]:
    """Fetches the high-fidelity link inventory view with device and port metadata."""
    return db.query(VNetworkLinksDetail).all()

def get_network_links_lag(db: Session) -> List[VNetworkLinksLAG]:
    """Retrieves the Link Aggregation Group (LAG) summary view."""
    return db.query(VNetworkLinksLAG).all()

def post_network_link(db: Session, link_data: NetworkLinkIn) -> NetworkLink:
    """Creates a new inter-router or intra-pop network link."""
    new_link = NetworkLink(**link_data.model_dump())
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    return new_link



def get_network_links_detail_by_network(
    db: Session, 
    network_name: str, 
    pop: Optional[str] = None,
    link_type: Optional[str] = None
) -> List[VNetworkLinksDetail]:
    """
    Retrieves detailed topology links filtered by a specific network identity.
    Allows optional localized market or POP sub-filtering across both sides of the link,
    and optional link type filtering (e.g., 'Inter-pop', 'Intra-pop').
    """
    # Look for the target network designation on either side of the circuit link
    query = db.query(VNetworkLinksDetail).filter(
        or_(
            VNetworkLinksDetail.a_network.ilike(network_name),
            VNetworkLinksDetail.b_network.ilike(network_name)
        )
    )
    
    # Narrows search parameters to target specific location markets if provided
    if pop:
        query = query.filter(
            or_(
                VNetworkLinksDetail.a_device_location.ilike(pop),
                VNetworkLinksDetail.b_device_location.ilike(pop)
            )
        )
        
    # Narrows search parameters to target specific link types (e.g., Inter-pop vs Intra-pop)
    if link_type:
        query = query.filter(VNetworkLinksDetail.link_type.ilike(link_type))
        
    return query.all()



def get_master_network_dashboard(db: Session, network_name: str):
    return db.query(VNetworkDashboard).filter(
        VNetworkDashboard.network == network_name
    ).all()

def get_network_links_detail_by_type(db: Session, link_type: str) -> List[VNetworkLinksDetail]:
    return (
        db.query(VNetworkLinksDetail)
        .filter(VNetworkLinksDetail.link_type == link_type)
        .all()
    )

def put_network_link(db: Session, link_id: str, link_data: NetworkLinkIn) -> NetworkLink:
    """Updates an existing inter-router or intra-pop network link."""
    # 1. Locate the existing record
    db_link = db.query(NetworkLink).filter(NetworkLink.link_id == link_id).first()
    
    if not db_link:
        return None

    # 2. Update attributes using the model_dump from your schema
    # We exclude 'link_id' from the update to prevent primary key modification
    update_data = link_data.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_link, key, value)

    db.commit()
    db.refresh(db_link)
    return db_link

def delete_network_link_by_id(db: Session, link_id: UUID) -> bool:
    """Removes a network link record."""
    result = db.query(NetworkLink).filter(NetworkLink.link_id == link_id).delete()
    db.commit()
    return result > 0

def get_interfaces(db: Session) -> List[Interface]:
    """Retrieves all logical interface configurations."""
    return db.query(Interface).all()

def get_interface_by_id(db: Session, interface_id: UUID) -> Optional[Interface]:
    """Fetches a single logical interface by UUID."""
    return db.query(Interface).filter(Interface.interface_id == interface_id).first()

def post_interface(db: Session, data: InterfaceIn) -> Interface:
    """Provisions a new logical interface with nested IP configurations."""
    new_interface = Interface(**data.model_dump(exclude={'ipv4_configs', 'ipv6_configs'}))
    db.add(new_interface)
    db.flush()  # Get interface_id for children
    return new_interface

# --- ROP & Optical Channel Management ---

def get_rop_channel_members(db: Session) -> List[ROPChannelMember]:
    """Fetches all channel assignments for Optical Path links."""
    return db.query(ROPChannelMember).all()

def get_channels_by_rop_link(db: Session, rop_link_id: UUID) -> List[ROPChannelMember]:
    """Retrieves all channels belonging to a specific ROP/Optical span."""
    return db.query(ROPChannelMember).filter(ROPChannelMember.rop_link_id == rop_link_id).all()

def post_rop_channel_member(db: Session, data: ROPChannelMemberIn) -> ROPChannelMember:
    """Assigns a member to an optical channel group."""
    new_member = ROPChannelMember(**data.model_dump())
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member