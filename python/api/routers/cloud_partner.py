from uuid import UUID
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, selectinload

from scripts.api_schema import (
    CloudPartnerIn,
    CloudPartnerOut,
    CloudPartnerUpdate,
    CloudConnectionIn,
    CloudConnectionOut,
    CloudConnectionUpdate,
)

from scripts.api_session import get_db
from scripts.api_model import CloudPartner, CloudPartnerBandwidth, CloudConnection, CloudPartnerTable

router = APIRouter(
    prefix="/cloudPartner",
    tags=["cloudPartner"],
    responses={404: {"description": "Not found"}},
)

# ---------------------------------------------------------------------------
# CLOUD PARTNER CRUD
# ---------------------------------------------------------------------------


@router.post("/", response_model=CloudPartnerOut)
def create_cloud_partner(payload: CloudPartnerIn, db: Session = Depends(get_db)):
    # 1. Write to the physical Table
    new_entry = CloudPartnerTable(
        **payload.model_dump(exclude={"bandwidth_tiers"})
    )
    db.add(new_entry)
    db.commit() # This triggers the Postgres DEFAULTs for timestamps

    # 2. Handle the bandwidth tiers in their physical table
    for bw in payload.bandwidth_tiers:
        db.add(CloudPartnerBandwidth(partner_id=new_entry.partner_id, service_bw=bw))
    db.commit()

    # 3. Read back from the View to return the fully aggregated JSON
    return db.query(CloudPartner).filter(CloudPartner.partner_id == new_entry.partner_id).first()


# TO THIS:
@router.get("/", response_model=List[CloudPartnerOut])
def list_cloud_partners(db: Session = Depends(get_db)):
    # Just a simple query. The JSONB data is already in the row!
    return db.query(CloudPartner).all()


@router.get("/{partner_id}", response_model=CloudPartnerOut)
def get_cloud_partner(partner_id: UUID, db: Session = Depends(get_db)):
    # Just query the partner. The view handles the bandwidth tiers automatically.
    partner = db.query(CloudPartner).filter(CloudPartner.partner_id == partner_id).first()
    
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    return partner

@router.put("/{partner_id}", response_model=CloudPartnerOut)
def update_cloud_partner(partner_id: UUID, payload: CloudPartnerUpdate, db: Session = Depends(get_db)):
    partner = db.query(CloudPartner).filter(CloudPartner.partner_id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Cloud partner not found")

    # Update simple fields
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field != "bandwidth_tiers":
            setattr(partner, field, value)

    # Update bandwidth tiers
    if payload.bandwidth_tiers is not None:
        # Delete old tiers
        db.query(CloudPartnerBandwidth).filter(
            CloudPartnerBandwidth.partner_id == partner_id
        ).delete()

        # Insert new tiers
        for bw in payload.bandwidth_tiers:
            db.add(CloudPartnerBandwidth(partner_id=partner_id, service_bw=bw))

    db.commit()
    db.refresh(partner)

    return partner


@router.delete("/{partner_id}")
def delete_cloud_partner(partner_id: UUID, db: Session = Depends(get_db)):
    partner = db.query(CloudPartner).filter(CloudPartner.partner_id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Cloud partner not found")

    db.delete(partner)
    db.commit()
    return {"detail": "Cloud partner deleted"}


# ---------------------------------------------------------------------------
# CLOUD CONNECTION CRUD
# ---------------------------------------------------------------------------

@router.post("/connection/", response_model=CloudConnectionOut)
def create_cloud_connection(payload: CloudConnectionIn, db: Session = Depends(get_db)):
    conn = CloudConnection(**payload.model_dump())
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


@router.get("/connection/", response_model=List[CloudConnectionOut])
def list_cloud_connections(db: Session = Depends(get_db)):
    return db.query(CloudConnection).all()


@router.get("/connection/{connection_id}", response_model=CloudConnectionOut)
def get_cloud_connection(connection_id: UUID, db: Session = Depends(get_db)):
    conn = db.query(CloudConnection).filter(
        CloudConnection.cloud_connection_id == connection_id
    ).first()

    if not conn:
        raise HTTPException(status_code=404, detail="Cloud connection not found")

    return conn


@router.put("/connection/{connection_id}", response_model=CloudConnectionOut)
def update_cloud_connection(connection_id: UUID, payload: CloudConnectionUpdate, db: Session = Depends(get_db)):
    conn = db.query(CloudConnection).filter(
        CloudConnection.cloud_connection_id == connection_id
    ).first()

    if not conn:
        raise HTTPException(status_code=404, detail="Cloud connection not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(conn, field, value)

    db.commit()
    db.refresh(conn)
    return conn


@router.delete("/connection/{connection_id}")
def delete_cloud_connection(connection_id: UUID, db: Session = Depends(get_db)):
    conn = db.query(CloudConnection).filter(
        CloudConnection.cloud_connection_id == connection_id
    ).first()

    if not conn:
        raise HTTPException(status_code=404, detail="Cloud connection not found")

    db.delete(conn)
    db.commit()
    return {"detail": "Cloud connection deleted"}