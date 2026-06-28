"""
operations/customer.py
Domain-specific logic for Customer and Tenant management.
Handles primary CRUD for customers and aggregated summary reporting.
"""

import logging
from typing import List, Optional
from scripts.api_session import get_db_session
from scripts.api_model import Customer, CustomerSummaryView
from scripts.api_schema import CustomerOut

logger = logging.getLogger(__name__)

# --- Primary ORM CRUD Methods ---

def get_customers() -> List[Customer]:
    """
    Fetches all customer records from the primary database table.
    """
    with get_db_session() as db:
        return db.query(Customer).all()

def get_customer(customer_id: str) -> Optional[Customer]:
    """
    Return a single Customer object by customer_id.
    """
    with get_db_session() as db:
        return db.query(Customer).filter(Customer.customer_id == customer_id).first()

def post_customer(customer_name: str, account_id: str) -> Optional[Customer]:
    """
    Creates a new customer using explicit name and account parameters.
    Handles UUID conversion by letting the DB default handle ID generation
    to prevent serialization errors.
    """
    try:
        with get_db_session() as db:
            # We omit customer_id here to allow the Postgres 
            # 'gen_random_uuid()' default to trigger.
            new_customer = Customer(
                customer_name=customer_name, 
                account_id=account_id
            )
            
            db.add(new_customer)
            db.commit()
            db.refresh(new_customer)
            return new_customer
    except Exception as e:
        logger.error(f"Error creating customer {customer_name}: {e}")
        return None



def put_customer(customer_id: str, customer_name: str, account_id: str) -> Optional[Customer]:
    """
    Updates an existing customer's basic details by ID.
    """
    with get_db_session() as db:
        customer = db.get(Customer, customer_id)
        if not customer:
            return None
        customer.customer_name = customer_name
        customer.account_id = account_id
        db.commit()
        db.refresh(customer)
        return customer

def delete_customer(customer_id: str) -> bool:
    """
    Removes a customer record from the database.
    """
    with get_db_session() as db:
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        if not customer:
            return False
        db.delete(customer)
        db.commit()
        return True

# --- Schema-Mapped CRUD Methods (Pydantic Output) ---

def create_customer_schema(customer_data: dict) -> Optional[CustomerOut]:
    """
    CREATE customer: Takes a dict and returns a validated CustomerOut schema.
    """
    try:
        with get_db_session() as db:
            new_customer = Customer(**customer_data)
            db.add(new_customer)
            db.commit()
            db.refresh(new_customer)
            return CustomerOut.from_orm(new_customer)
    except Exception as e:
        logger.error(f"Error creating customer schema: {e}")
        return None

def get_all_customers_schema() -> List[CustomerOut]:
    """
    READ all customers: Returns a list of validated CustomerOut schemas.
    """
    try:
        with get_db_session() as db:
            customers = db.query(Customer).all()
            return [CustomerOut.from_orm(c) for c in customers]
    except Exception as e:
        logger.error(f"Error retrieving customers schema: {e}")
        return []

def get_customer_by_id_schema(customer_id: str) -> Optional[CustomerOut]:
    """
    READ customer by ID: Returns a specific validated CustomerOut schema.
    """
    try:
        with get_db_session() as db:
            customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
            return CustomerOut.from_orm(customer) if customer else None
    except Exception as e:
        logger.error(f"Error retrieving customer schema {customer_id}: {e}")
        return None

def update_customer_schema(customer_id: str, update_data: dict) -> Optional[CustomerOut]:
    """
    UPDATE customer: Applies update dict and returns updated CustomerOut schema.
    """
    try:
        with get_db_session() as db:
            customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
            if not customer:
                return None
            for key, value in update_data.items():
                setattr(customer, key, value)
            db.commit()
            db.refresh(customer)
            return CustomerOut.from_orm(customer)
    except Exception as e:
        logger.error(f"Error updating customer schema {customer_id}: {e}")
        return None

def delete_customer_schema(customer_id: str) -> bool:
    """
    DELETE customer: Schema-level deletion confirmation.
    """
    try:
        with get_db_session() as db:
            customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
            if not customer:
                return False
            db.delete(customer)
            db.commit()
            return True
    except Exception as e:
        logger.error(f"Error deleting customer schema {customer_id}: {e}")
        return False

# --- Reporting / View Methods ---

def get_customer_summaries() -> List[CustomerSummaryView]:
    """
    Fetches the aggregated summary data for all customers from the 
    v_customer_summary view.
    """
    with get_db_session() as db:
        return db.query(CustomerSummaryView).all()