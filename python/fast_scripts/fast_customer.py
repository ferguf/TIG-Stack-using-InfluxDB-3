import requests
import sys
from typing import List, Dict, Any, Optional

# --- Configuration ---
# Ensure this matches the address where your Docker container is exposed
BASE_URL = "http://localhost:8000" 

# -----------------------------------------------------
# --- Utility Functions ---
# -----------------------------------------------------

def check_api_connection_via_docs() -> bool:
    """Checks if the API is reachable by hitting the /docs endpoint."""
    url = f"{BASE_URL}/docs"
    print(f"Attempting to verify API connection via: {url}")
    try:
        response = requests.get(url, timeout=5) 
        response.raise_for_status() 
        print(f"✅ API Server is running and reachable at {BASE_URL}.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"\n❌ FATAL ERROR: Could not connect to API at {BASE_URL}/docs. Details: {e}")
        return False

# -----------------------------------------------------
# --- Client CRUD Methods ---
# -----------------------------------------------------

# GET /customers/
def get_customers() -> List[Dict[str, Any]]:
    """Fetches all customers (GET /customers/)."""
    url = f"{BASE_URL}/customers/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        # Handle cases where the API might return a single object or null
        customers = data if isinstance(data, list) else [data] if data else []
        return customers
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching customers: {e}")
        return []

# POST /customers/
def create_customer(customer_name: str, account_id: str) -> Optional[Dict[str, Any]]:
    """Creates a new customer (POST /customers/)."""
    url = f"{BASE_URL}/customers/"
    # service_count is not strictly needed for creation but is often included 
    # if the server ignores extra fields or if the schema requires it.
    payload = {"customer_name": customer_name, "account_id": account_id}
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating customer: {e}")
        return None

# GET /customers/{customer_id}
def show_customer(customer_id: str) -> Optional[Dict[str, Any]]:
    """Fetches details for a specific customer (GET /customers/{id})."""
    url = f"{BASE_URL}/customers/{customer_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        # Expected for 404/NotFound status (when checking after deletion)
        return None

# PUT /customers/{customer_id}
def update_customer(customer_id: str, fields: dict) -> Optional[Dict[str, Any]]:
    """Updates a customer by ID (PUT /customers/{id}). Requires account_id in fields."""
    url = f"{BASE_URL}/customers/{customer_id}"
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    
    # Required check based on API requirements
    if "account_id" not in fields:
        print("🛑 Error: 'account_id' is mandatory in the update payload.")
        return None
        
    try:
        response = requests.put(url, json=fields, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error updating customer {customer_id}: {e}")
        return None

# DELETE /customers/{customer_id}
def delete_customer(customer_id: str) -> bool:
    """Deletes a customer by ID (DELETE /customers/{id})."""
    url = f"{BASE_URL}/customers/{customer_id}"
    try:
        requests.delete(url).raise_for_status()
        return True
    except requests.exceptions.RequestException:
        return False

# NOTE: This file should not contain any direct execution logic (i.e., no if __name__ == '__main__': block)
# It is designed purely for import.
