from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from uuid import UUID
from domains.netlink import models, schemas

# --- Base Network Link Management ---

def get_network_links(db: Session) -> List[models.NetworkLink]:
    return db.query(models.NetworkLink).all()

def get_network_link_by_id(db: Session, link_id: UUID) -> Optional[models.NetworkLink]:
    return db.query(models.NetworkLink).filter(models.NetworkLink.link_id == link_id).first()

def post_network_link(db: Session, link_data: schemas.NetworkLinkIn) -> models.NetworkLink:
    new_link = models.NetworkLink(**link_data.model_dump())
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    return new_link

def put_network_link(db: Session, link_id: UUID, link_data: schemas.NetworkLinkUpdate) -> Optional[models.NetworkLink]:
    db_link = db.query(models.NetworkLink).filter(models.NetworkLink.link_id == link_id).first()
    if not db_link:
        return None

    update_data = link_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_link, key, value)

    db.commit()
    db.refresh(db_link)
    return db_link

def delete_network_link_by_id(db: Session, link_id: UUID) -> bool:
    result = db.query(models.NetworkLink).filter(models.NetworkLink.link_id == link_id).delete()
    db.commit()
    return result > 0

# --- Detail & View Operations ---

def get_network_links_detail(db: Session) -> List[models.VNetworkLinksDetail]:
    return db.query(models.VNetworkLinksDetail).all()

def get_network_links_detail_by_device(db: Session, device_id: UUID) -> List[models.VNetworkLinksDetail]:
    return db.query(models.VNetworkLinksDetail).filter(
        or_(
            models.VNetworkLinksDetail.a_device_id == device_id,
            models.VNetworkLinksDetail.b_device_id == device_id
        )
    ).all()

def get_network_links_detail_by_network(
    db: Session, 
    network_name: str, 
    pop: Optional[str] = None,
    link_type: Optional[str] = None
) -> List[models.VNetworkLinksDetail]:
    
    query = db.query(models.VNetworkLinksDetail).filter(
        or_(
            models.VNetworkLinksDetail.a_network.ilike(network_name),
            models.VNetworkLinksDetail.b_network.ilike(network_name)
        )
    )
    if pop:
        query = query.filter(
            or_(
                models.VNetworkLinksDetail.a_device_location.ilike(pop),
                models.VNetworkLinksDetail.b_device_location.ilike(pop)
            )
        )
    if link_type:
        query = query.filter(models.VNetworkLinksDetail.link_type.ilike(link_type))
        
    return query.all()

def get_network_links_lag(db: Session) -> List[models.VNetworkLinksLAG]:
    return db.query(models.VNetworkLinksLAG).all()

def get_network_links_lag_by_device(db: Session, device_id: UUID) -> List[models.VNetworkLinksLAG]:
    return db.query(models.VNetworkLinksLAG).filter(models.VNetworkLinksLAG.device_id == device_id).all()

# --- ROP Operations ---

def get_rop_channel_members(db: Session) -> List[models.ROPChannelMember]:
    return db.query(models.ROPChannelMember).all()

def get_channels_by_rop_link(db: Session, rop_link_id: UUID) -> List[models.ROPChannelMember]:
    return db.query(models.ROPChannelMember).filter(models.ROPChannelMember.rop_link_id == rop_link_id).all()

def post_rop_channel_member(db: Session, data: schemas.ROPChannelMemberIn) -> models.ROPChannelMember:
    new_member = models.ROPChannelMember(**data.model_dump())
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member