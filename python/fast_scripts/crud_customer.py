import uuid
import sys
from typing import Optional

# 1. Import all necessary functions from the client module
from fast_customer import (
    check_api_connection_via_docs,
    get_customers,
    create_customer,
    show_customer,
    update_customer,
    delete_customer
)

# --- Configuration and Sample Data Generation ---
# Generate a unique prefix for THIS test run to ensure data isolation
TEST_PREFIX = f"TEST-{uuid.uuid4().hex[:6]}" 

# Data for POST (Creation)
NEW_CUSTOMER_NAME = f"{TEST_PREFIX}-InitialCorp"
NEW_ACCOUNT_ID = f"ACC-{TEST_PREFIX}"

# Data for PUT (Update) - MUST be unique due to database constraints
UNIQUE_UPDATE_SUFFIX = uuid.uuid4().hex[:6] 
UPDATED_CUSTOMER_NAME = f"{TEST_PREFIX}-UpdatedName"
UPDATED_ACCOUNT_ID = f"ACC-UPDATED-{UNIQUE_UPDATE_SUFFIX}" 

# Define patterns used by the script for cleanup
CLEANUP_PATTERNS = ["ACC-TEST-", "ACC-UPDATED-", "ACC-REQUIRED-PUT"] 

NEW_CUSTOMER_ID: Optional[str] = None 

# -----------------------------------------------------
# --- Global Utility and Cleanup Functions ---
# -----------------------------------------------------

def cleanup_test_customers():
    """
    Fetches all customers and deletes any whose account_id matches known test patterns.
    Runs at the start of the script to ensure a clean slate.
    """
    print("\n--- STEP 0: GLOBAL CLEANUP (Pre-Test) ---")
    
    all_customers = get_customers() # Reuses imported function
    if not all_customers:
        print("✅ Cleanup successful: No customers retrieved or list is empty.")
        return
        
    cleanup_count = 0
    
    for customer in all_customers:
        customer_id = customer.get("customer_id")
        account_id = customer.get("account_id", "")
        
        is_test_data = False
        
        # Check if the account ID contains any of the known test patterns
        for pattern in CLEANUP_PATTERNS:
            if pattern in account_id:
                is_test_data = True
                break
        
        if is_test_data:
            print(f"   🗑️ Deleting test customer: {customer_id} (Account: {account_id})")
            
            # Reuses imported function
            if delete_customer(customer_id):
                cleanup_count += 1
            else:
                print(f"   ❌ Failed to delete {customer_id}.")

    if cleanup_count > 0:
        print(f"✅ Cleanup successful: Removed {cleanup_count} previous test record(s).")
    else:
        print("✅ Cleanup successful: No old test records matching test patterns found.")


# -----------------------------------------------------
# --- Test Execution Steps ---
# -----------------------------------------------------

def step_1_read_all_customers():
    """Tests GET /customers/."""
    print("\n--- STEP 1: Testing GET /customers/ (READ ALL) ---")
    customers = get_customers()
    print(f"   Found {len(customers)} customers after cleanup.")

def step_2_create_new_customer():
    """Tests POST /customers/ and sets NEW_CUSTOMER_ID."""
    global NEW_CUSTOMER_ID
    print("\n--- STEP 2: Testing POST /customers/ (CREATE) ---")
    
    customer = create_customer(NEW_CUSTOMER_NAME, NEW_ACCOUNT_ID)
    if not customer:
        print("❌ FAILED: Customer creation failed.")
        sys.exit(1)
        
    NEW_CUSTOMER_ID = customer.get('customer_id')
    print(f"   ➡️ New Customer ID created: {NEW_CUSTOMER_ID}")
    
    # Assertions
    if customer.get('account_id') == NEW_ACCOUNT_ID:
        print("✅ CREATE Verification successful.")
    else:
        print("❌ FAILED: Created customer has incorrect account ID.")
        sys.exit(1)


def step_3_read_specific_customer(customer_id: str):
    """Tests GET /customers/{id} and verifies the new customer."""
    print("\n--- STEP 3: Testing GET /customers/{id} (READ SPECIFIC) ---")
    
    customer_data = show_customer(customer_id)
    
    if not customer_data:
        print(f"❌ FAILED: Could not retrieve customer {customer_id}.")
        sys.exit(1)
    
    if customer_data.get('customer_name') == NEW_CUSTOMER_NAME:
        print("✅ READ Verification successful: Data retrieved matches created data.")
    else:
        print("❌ FAILED: Retrieved data does NOT match expected data.")
        sys.exit(1)

def step_4_update_customer(customer_id: str):
    """Tests PUT /customers/{id} with required fields and verifies the change."""
    print("\n--- STEP 4: Testing PUT /customers/{id} (UPDATE) ---")
    
    # Define Update Payload with MANDATORY 'account_id'
    update_payload = {
        "customer_name": UPDATED_CUSTOMER_NAME,
        "account_id": UPDATED_ACCOUNT_ID
    }
    
    updated_data = update_customer(customer_id, update_payload)
    
    if not updated_data or updated_data.get('customer_name') != UPDATED_CUSTOMER_NAME:
        print("❌ FAILED: Update failed or returned incorrect data.")
        sys.exit(1)

    # Verification (Read after Update)
    verification_data = show_customer(customer_id)
    
    if verification_data and \
       verification_data.get('customer_name') == UPDATED_CUSTOMER_NAME and \
       verification_data.get('account_id') == UPDATED_ACCOUNT_ID:
        
        print("✅ UPDATE Verification successful: Both Name and Account ID were changed and persisted.")
    else:
        print("❌ FAILED: GET verification failed. Data was not persisted.")
        sys.exit(1)

def step_5_delete_customer(customer_id: str):
    """Tests DELETE /customers/{id} and verifies deletion."""
    print("\n--- STEP 5: Testing DELETE /customers/{id} (CLEANUP) ---")
    
    if delete_customer(customer_id):
        # Final Verification: Attempt to read the resource again (should fail/return None)
        deleted_check = show_customer(customer_id)
        if deleted_check is None:
            print("✅ DELETE Verification successful: Customer is gone (404/None received).")
        else:
            print("❌ FAILED: Customer still exists after DELETE operation.")
            sys.exit(1)
    else:
        print("❌ FAILED: Deletion operation failed.")
        sys.exit(1)

# -----------------------------------------------------
# --- Main Execution ---
# -----------------------------------------------------
if __name__ == '__main__':
    
    if not check_api_connection_via_docs():
        sys.exit(1)

    # --- START CLEANUP & TEST RUN ---
    cleanup_test_customers()
    
    print("\n" + "="*60)
    print("STARTING CUSTOMER CRUD INTEGRATION TEST SUITE")
    print("="*60)

    try:
        # Step 1: Read All (Initial Check)
        step_1_read_all_customers()

        # Step 2: Create (Setup the resource)
        step_2_create_new_customer()

        # Step 3: Read Specific (Verify creation)
        step_3_read_specific_customer(NEW_CUSTOMER_ID)

        # Step 4: Update (Test modification logic)
        step_4_update_customer(NEW_CUSTOMER_ID)

        # Step 5: Delete (Test cleanup and complete CRUD cycle)
        step_5_delete_customer(NEW_CUSTOMER_ID)

        print("\n" + "="*60)
        print("CUSTOMER CRUD INTEGRATION TEST SUITE PASSED SUCCESSFULLY.")
        print("="*60)

    except Exception as e:
        print(f"\nCRITICAL FAILURE DURING TEST EXECUTION: {e}")
        # Final safety cleanup for the current run's data if it wasn't deleted in Step 5
        if NEW_CUSTOMER_ID:
            print(f"\nAttempting cleanup of failed test resource: {NEW_CUSTOMER_ID}")
            delete_customer(NEW_CUSTOMER_ID)
        sys.exit(1)