import requests
from typing import List, Dict, Any, Optional

# --- Configuration ---
BASE_URL = "http://localhost:8000" 

# -----------------------------------------------------
# --- Fabric Service Client CRUD Methods ---
# -----------------------------------------------------

# GET /fabric_services/
def get_fabric_services() -> List[Dict[str, Any]]:
    """Fetches all fabric services."""
    url = f"{BASE_URL}/fabric_services/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else [data] if data else []
    except requests.exceptions.RequestException as e:
        # print(f"❌ Error fetching fabric services: {e}") # Suppress for testing
        return []

# GET /fabric_services/{service_id}
def show_fabric_service(service_id: str) -> Optional[Dict[str, Any]]:
    """Fetches details for a specific fabric service."""
    url = f"{BASE_URL}/fabric_services/{service_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

# GET /fabric_services/customer/{customer_id}
def get_services_by_customer(customer_id: str) -> List[Dict[str, Any]]:
    """Fetches services belonging to a specific customer."""
    url = f"{BASE_URL}/fabric_services/customer/{customer_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else [data] if data else []
    except requests.exceptions.RequestException as e:
        # print(f"❌ Error fetching customer's services: {e}")
        return []

# POST /fabric_services/
def create_fabric_service(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Creates a new fabric service."""
    url = f"{BASE_URL}/fabric_services/"
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating fabric service: {e}")
        # print(f"Response: {getattr(e.response, 'text', 'No response body')}")
        return None

# PUT /fabric_services/{service_id}
def update_fabric_service(service_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Updates a fabric service by ID."""
    url = f"{BASE_URL}/fabric_services/{service_id}"
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    
    # NOTE: The update payload needs ALL required fields for the PUT operation 
    # to avoid a 422 error, even if you are only changing one field (like service_name).
    # Since we don't know the exact schema, we only send the provided fields.
    # If this causes a 422, the payload needs to be expanded in the test script.
    
    try:
        response = requests.put(url, json=fields, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error updating fabric service {service_id}: {e}")
        return None

# DELETE /fabric_services/{service_id}
def delete_fabric_service(service_id: str) -> bool:
    """Deletes a fabric service by ID."""
    url = f"{BASE_URL}/fabric_services/{service_id}"
    try:
        requests.delete(url).raise_for_status()
        return True
    except requests.exceptions.RequestException:
        return False

# NOTE: check_api_connection_via_docs() from customer module can be reused.
# If you don't have a shared module, you can copy its definition here.