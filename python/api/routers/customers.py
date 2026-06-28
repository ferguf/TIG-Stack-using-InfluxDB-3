# api/routers/customers.py
from fastapi import APIRouter, HTTPException
from typing import List, Optional
import sys, os
from sqlalchemy.orm import Session
from uuid import UUID

# Ensure scripts directory is on path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(BASE_DIR, "..", "..", "scripts")
sys.path.append(SCRIPTS_DIR)

import scripts.api_operation as api_operation

from scripts.api_schema import CustomerSummaryOut,CustomerIn, CustomerOut, DeleteResponse
router = APIRouter(prefix="/customers", tags=["customers"])

# --- GET: list all customers ---
@router.get("/", response_model=List[CustomerOut])
def get_customers():
    customers = api_operation.get_customers()
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

@router.get("/summary", response_model=List[CustomerSummaryOut])
def get_customer_summaries():
    """
    Retrieves a summarized view of all customers, including counts for
    services, fabric connections, ports, and interfaces.
    """
    summaries = api_operation.get_customer_summaries()
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


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: UUID):
    """
    Retrieve a single customer by customer_id.
    """
    customer = api_operation.get_customer(customer_id)
    if not customer:
        # FastAPI will automatically return 404 if you raise HTTPException
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Customer not found")

    return CustomerOut(
        account_id=customer.account_id,
        customer_name=customer.customer_name,
        customer_id=customer.customer_id,
        created_at=customer.created_at,
        updated_at=customer.updated_at,
        service_count=0   # you can replace with actual count if needed
    )


@router.post("/", response_model=CustomerOut)
def post_customer(customer: CustomerIn):
        new_customer = api_operation.post_customer(
            customer_name=customer.customer_name,
            account_id=customer.account_id
        )
        if not new_customer:
            raise HTTPException(status_code=400, detail="Customer creation failed")
        return CustomerOut(
            account_id=new_customer.account_id,
            customer_name=new_customer.customer_name,
            customer_id=new_customer.customer_id,
            service_count=0
        )

@router.put("/{customer_id}", response_model=CustomerOut)
def update_customer(customer_id: UUID, customer: CustomerIn):
    updated = api_operation.put_customer(
        customer_id=customer_id,
        customer_name=customer.customer_name,
        account_id=customer.account_id
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Customer not found or update failed")
    return CustomerOut(
        account_id=updated.account_id,
        customer_name=updated.customer_name,
        customer_id=updated.customer_id
    )

@router.delete("/{customer_id}", response_model=DeleteResponse, status_code=200)
def delete_customer(customer_id: UUID):
    deleted = api_operation.delete_customer(customer_id=customer_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Customer not found or delete failed")
    return DeleteResponse(detail=f"Customer '{customer_id}' deleted successfully")

