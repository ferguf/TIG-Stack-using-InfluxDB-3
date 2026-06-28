import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

# Centralized core DB (Ensure this matches your actual path structure)
from core.database import get_db

# Native relative imports from the domain slice
from . import operations
from .schemas import (
    CustomerIn, 
    CustomerOut, 
    CustomerSummaryOut, 
    DeleteResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/customers", tags=["customers"])

# ---------------------------------------------------------
# READ (all)
# ---------------------------------------------------------
@router.get("/", response_model=List[CustomerOut])
def get_customers(db: Session = Depends(get_db)):
    customers = operations.get_all_customers(db)
    # Preserving legacy frontend formatting logic
    return [
        CustomerOut(
            account_id=c.account_id,
            customer_name=c.customer_name,
            customer_id=c.customer_id,
            created_at=c.created_at,
            updated_at=c.updated_at,
            service_count=0
        )
        for c in customers
    ]

# ---------------------------------------------------------
# READ SUMMARY
# ---------------------------------------------------------
@router.get("/summary", response_model=List[CustomerSummaryOut])
def get_customer_summaries(db: Session = Depends(get_db)):
    """
    Retrieves a summarized view of all customers, including counts for
    services, fabric connections, ports, and interfaces.
    """
    summaries = operations.get_customer_summaries(db)
    return [
        CustomerSummaryOut(
            customer_id=s.customer_id,
            customer_name=s.customer_name,
            account_id=s.account_id,
            service_count=s.service_count,
            fabric_connection_count=s.fabric_connection_count,
            port_count=s.port_count,
            interface_count=s.interface_count
        )
        for s in summaries
    ]

# ---------------------------------------------------------
# READ (single)
# ---------------------------------------------------------
@router.get("/{customer_id:uuid}", response_model=CustomerOut)
def get_customer(customer_id: UUID, db: Session = Depends(get_db)):
    """
    Retrieve a single customer by customer_id.
    """
    customer = operations.get_customer_by_id(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return CustomerOut(
        account_id=customer.account_id,
        customer_name=customer.customer_name,
        customer_id=customer.customer_id,
        created_at=customer.created_at,
        updated_at=customer.updated_at,
        service_count=0   
    )

# ---------------------------------------------------------
# CREATE
# ---------------------------------------------------------
@router.post("/", response_model=CustomerOut)
def post_customer(customer: CustomerIn, db: Session = Depends(get_db)):
    new_customer = operations.create_customer(db, customer.model_dump())
    if not new_customer:
        raise HTTPException(status_code=400, detail="Customer creation failed")
        
    return CustomerOut(
        account_id=new_customer.account_id,
        customer_name=new_customer.customer_name,
        customer_id=new_customer.customer_id,
        service_count=0
    )

# ---------------------------------------------------------
# UPDATE
# ---------------------------------------------------------
@router.put("/{customer_id:uuid}", response_model=CustomerOut)
def update_customer(customer_id: UUID, customer: CustomerIn, db: Session = Depends(get_db)):
    updated = operations.update_customer(db, customer_id, customer.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Customer not found or update failed")
        
    return CustomerOut(
        account_id=updated.account_id,
        customer_name=updated.customer_name,
        customer_id=updated.customer_id,
        service_count=0
    )

# ---------------------------------------------------------
# DELETE
# ---------------------------------------------------------
@router.delete("/{customer_id:uuid}", response_model=DeleteResponse, status_code=200)
def delete_customer(customer_id: UUID, db: Session = Depends(get_db)):
    deleted = operations.delete_customer(db, customer_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Customer not found or delete failed")
        
    return DeleteResponse(detail=f"Customer '{customer_id}' deleted successfully")