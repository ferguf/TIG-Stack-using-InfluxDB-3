"""
api_operation_customer.py
Methods for managing Customers and their aggregated summaries.
"""
from typing import List, Optional
from scripts.api_session import get_db_session
from scripts.api_model import Customer, CustomerSummaryView

def get_customers() -> List[Customer]:
    """Fetches all customers from the base table."""
    with get_db_session() as db:
        return db.query(Customer).all()

def get_customer_summaries() -> List[CustomerSummaryView]:
    """Fetches the high-level business intelligence summary for all customers."""
    with get_db_session() as db:
        return db.query(CustomerSummaryView).all()

def delete_customer(customer_id: str) -> bool:
    """Removes a customer and returns success status."""
    with get_db_session() as db:
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        if not customer: return False
        db.delete(customer)
        db.commit()
        return True