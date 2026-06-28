"""
Business logic / operations layer for the Customers domain.
File: app/python/domains/customers/operations.py

Domain-specific logic for Customer and Tenant management.
Handles primary CRUD for customers and aggregated summary reporting.
"""

import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import UUID

# Phase 1: Local proxy imports
from .models import Customer, CustomerSummary

logger = logging.getLogger(__name__)

# --- Primary ORM CRUD Methods ---

def get_all_customers(db: Session) -> List[Customer]:
    """
    Fetches all customer records from the primary database table.
    """
    return db.query(Customer).all()


def get_customer_summaries(db: Session) -> List[CustomerSummary]:
    """
    Fetches the aggregated summary data for all customers from the 
    v_customer_summary view.
    """
    return db.query(CustomerSummary).all()


def get_customer_by_id(db: Session, customer_id: UUID) -> Optional[Customer]:
    """
    Return a single Customer object by customer_id.
    """
    return db.query(Customer).filter(Customer.customer_id == customer_id).first()


def create_customer(db: Session, customer_data: dict) -> Optional[Customer]:
    """
    Creates a new customer.
    Handles UUID conversion by letting the DB default handle ID generation
    to prevent serialization errors.
    """
    try:
        # We omit customer_id here to allow the Postgres 
        # 'gen_random_uuid()' default to trigger.
        new_customer = Customer(**customer_data)
        
        db.add(new_customer)
        db.commit()
        db.refresh(new_customer)
        return new_customer
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating customer: {e}")
        return None


def update_customer(db: Session, customer_id: UUID, update_data: dict) -> Optional[Customer]:
    """
    Updates an existing customer's basic details by ID.
    """
    try:
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        if not customer:
            return None
            
        for key, value in update_data.items():
            setattr(customer, key, value)
            
        db.commit()
        db.refresh(customer)
        return customer
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating customer {customer_id}: {e}")
        return None


def delete_customer(db: Session, customer_id: UUID) -> bool:
    """
    Removes a customer record from the database.
    """
    try:
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        if not customer:
            return False
            
        db.delete(customer)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting customer {customer_id}: {e}")
        return False