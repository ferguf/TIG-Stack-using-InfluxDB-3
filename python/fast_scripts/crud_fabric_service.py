import uuid
import sys
from typing import Optional, Dict, Any, List
from fast_customer import check_api_connection_via_docs
# Assuming fast_service.py is saved in the same location
from fast_service import (
    get_fabric_services,
    create_fabric_service,
    show_fabric_service,
    update_fabric_service,
    delete_fabric_service,
    # NOTE: Assuming check_api_connection_via_docs is imported/available.
    # If not, ensure it's defined or imported from another module (like reusable_api_client).
    # For this script, we'll assume it's available or defined locally.
)

# --- Define check_api_connection_via_docs if not imported ---
# (Place the full function definition here if it's not in fast_service.py)
# from reusable_api_client import check_api_connection_via_docs
# ------------------------------------------------------------


# --- Configuration and Sample Data Generation ---

# NOTE: You MUST use a customer_id that exists in your database for POST/PUT to work.
EXISTING_CUSTOMER_ID = "85161ccd-8199-4905-b9e5-663af2a3005b" # Replace with a known, active Customer ID

# Generate a unique prefix for THIS test run
TEST_PREFIX = f"TEST-{uuid.uuid4().hex[:6]}" 

# Data for POST (Creation)
NEW_SERVICE_NAME = f"{TEST_PREFIX}-ELINE-EPL"
NEW_SERVICE_ALIAS = f"{TEST_PREFIX}-ALIAS"
NEW_ROUTE_TARGET = f"RT:{uuid.uuid4().hex[:8]}"

NEW_SERVICE_PAYLOAD: Dict[str, Any] = {
    "customer_id": EXISTING_CUSTOMER_ID,
    "service_name": NEW_SERVICE_NAME,
    "service_alias": NEW_SERVICE_ALIAS,
    "service_type": "ELine EPL 2", 
    "route_target": NEW_ROUTE_TARGET,
    "health_status": 4, 
    # NOTE: created_at/updated_at/service_count are usually server-generated, 
    # but included if your schema requires them. Omitted here for simplicity.
}

# Data for PUT (Update)
UPDATED_SERVICE_NAME = f"{TEST_PREFIX}-ELINE-UPDATED"
# The update payload should only contain the fields you want to change,
# but often requires mandatory fields if the server uses a strict Pydantic model.
UPDATE_PAYLOAD = {
    "service_name": UPDATED_SERVICE_NAME
    # If your PUT requires other fields like customer_id, add them here:
    # "customer_id": EXISTING_CUSTOMER_ID 
}

# Define patterns used by the script for cleanup
CLEANUP_PATTERNS = ["TEST-", "RT:"] 

NEW_SERVICE_ID: Optional[str] = None 


# -----------------------------------------------------
# --- Global Utility and Cleanup Functions ---
# -----------------------------------------------------

def cleanup_test_services():
    """Fetches all services and deletes any whose name/RT matches known test patterns."""
    print("\n--- STEP 0: GLOBAL CLEANUP (Pre-Test) ---")
    
    all_services = get_fabric_services()
    if not all_services:
        print("✅ Cleanup successful: No services retrieved or list is empty.")
        return
        
    cleanup_count = 0
    
    for service in all_services:
        service_id = service.get("service_id")
        service_name = service.get("service_name", "")
        route_target = service.get("route_target", "")
        
        is_test_data = False
        
        # Check if service_name or route_target contains any of the known test patterns
        for pattern in CLEANUP_PATTERNS:
            if pattern in service_name or pattern in route_target:
                is_test_data = True
                break
        
        if is_test_data:
            print(f"   🗑️ Deleting test service: {service_id} (Name: {service_name[:20]}...)")
            
            if delete_fabric_service(service_id):
                cleanup_count += 1
            else:
                print(f"   ❌ Failed to delete {service_id}.")

    if cleanup_count > 0:
        print(f"✅ Cleanup successful: Removed {cleanup_count} previous test service record(s).")
    else:
        print("✅ Cleanup successful: No old test service records found.")


# -----------------------------------------------------
# --- Test Execution Steps ---
# -----------------------------------------------------

def step_1_read_all_services():
    """Tests GET /fabric_services/."""
    print("\n--- STEP 1: Testing GET /fabric_services/ (READ ALL) ---")
    services = get_fabric_services()
    print(f"   Found {len(services)} services after cleanup.")


def step_2_create_new_service():
    """Tests POST /fabric_services/ and sets NEW_SERVICE_ID."""
    global NEW_SERVICE_ID
    print("\n--- STEP 2: Testing POST /fabric_services/ (CREATE) ---")
    
    service = create_fabric_service(NEW_SERVICE_PAYLOAD)
    if not service:
        print("❌ FAILED: Service creation failed.")
        sys.exit(1)
        
    NEW_SERVICE_ID = service.get('service_id')
    print(f"   ➡️ New Service ID created: {NEW_SERVICE_ID}")
    
    # Assertions
    if service.get('service_name') == NEW_SERVICE_NAME and service.get('customer_id') == EXISTING_CUSTOMER_ID:
        print("✅ CREATE Verification successful.")
    else:
        print("❌ FAILED: Created service has incorrect data.")
        sys.exit(1)


def step_3_read_specific_service(service_id: str):
    """Tests GET /fabric_services/{id} and verifies the new service."""
    print("\n--- STEP 3: Testing GET /fabric_services/{id} (READ SPECIFIC) ---")
    
    service_data = show_fabric_service(service_id)
    
    if not service_data:
        print(f"❌ FAILED: Could not retrieve service {service_id}.")
        # sys.exit(1)
    
    if service_data.get('service_name') == NEW_SERVICE_NAME:
        print("✅ READ Verification successful: Data retrieved matches created data.")
    else:
        print("❌ FAILED: Retrieved data does NOT match expected data.")
        sys.exit(1)


def step_5_update_service(service_id: str):
    """Tests PUT /fabric_services/{id} and verifies the change."""
    print("\n--- STEP 5: Testing PUT /fabric_services/{id} (UPDATE) ---")
    
    updated_data = update_fabric_service(service_id, UPDATE_PAYLOAD)
    
    if not updated_data or updated_data.get('service_name') != UPDATED_SERVICE_NAME:
        print("❌ FAILED: Update failed or returned incorrect data.")
        sys.exit(1)

    # Verification (Read after Update)
    verification_data = show_fabric_service(service_id)
    
    if verification_data and verification_data.get('service_name') == UPDATED_SERVICE_NAME:
        print("✅ UPDATE Verification successful: Service Name was changed and persisted.")
    else:
        print("❌ FAILED: GET verification failed. Updated data was not persisted.")
        sys.exit(1)


def step_6_delete_service(service_id: str):
    """Tests DELETE /fabric_services/{id} and verifies deletion."""
    print("\n--- STEP 6: Testing DELETE /fabric_services/{id} (FINAL CLEANUP) ---")
    
    if delete_fabric_service(service_id):
        # Final Verification: Attempt to read the resource again (should fail/return None)
        deleted_check = show_fabric_service(service_id)
        if deleted_check is None:
            print("✅ DELETE Verification successful: Service is gone (404/None received).")
        else:
            print("❌ FAILED: Service still exists after DELETE operation.")
            sys.exit(1)
    else:
        print("❌ FAILED: Deletion operation failed.")
        sys.exit(1)

# -----------------------------------------------------
# --- Main Execution ---
# -----------------------------------------------------
if __name__ == '__main__':
    
    # NOTE: Please define or import check_api_connection_via_docs if needed
    # if not check_api_connection_via_docs():
    #     sys.exit(1)

    # --- START CLEANUP & TEST RUN ---
    cleanup_test_services()
    
    print("\n" + "="*60)
    print("STARTING FABRIC SERVICE CRUD INTEGRATION TEST SUITE")
    print("="*60)

    try:
        # 1. Read All (Initial Check)
        step_1_read_all_services()

        # 2. Create (Setup the resource)
        step_2_create_new_service()

        # 3. Read Specific (Verify creation)
        step_3_read_specific_service(NEW_SERVICE_ID)
        
        # 4. Read By Customer (Verify the service is linked)
        step_4_read_services_by_customer(EXISTING_CUSTOMER_ID)

        # 5. Update (Test modification logic)
        step_5_update_service(NEW_SERVICE_ID)

        # 6. Delete (Test cleanup and complete CRUD cycle)
        step_6_delete_service(NEW_SERVICE_ID)

        print("\n" + "="*60)
        print("FABRIC SERVICE CRUD INTEGRATION TEST SUITE PASSED SUCCESSFULLY.")
        print("="*60)

    except Exception as e:
        print(f"\nCRITICAL FAILURE DURING TEST EXECUTION: {e}")
        if NEW_SERVICE_ID:
            print(f"\nAttempting cleanup of failed test resource: {NEW_SERVICE_ID}")
            delete_fabric_service(NEW_SERVICE_ID)
        sys.exit(1)