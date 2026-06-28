"""File Name: 'db_cli.py' and version '1.0.1' date: 'November 29, 2025 11:32 AM MST' (Change: Updated hardcoded lookup values for Account ID and Device Name to 'ACC-1' and 'VAR1.DEN1'.) """
import sys
import os

# Assuming db_config.py is in the same directory, import the utility function
try:
    # get_id_by_name is the primary function we are demonstrating
    from db_config import get_id_by_name, handle_connection_close, get_db_connection 
except ImportError:
    print("❌ Error: Could not import 'get_id_by_name' from db_config.py.")
    print("Please ensure db_config.py is in the current directory.")
    sys.exit(1)


def demonstrate_lookup():
    """
    Demonstrates fetching UUIDs (Primary Keys) using the reusable 
    get_id_by_name utility function for various tables.
    """
    print("--- ID Lookup Demonstration ---")
    
    # Example 1: Find the UUID for a Customer using their unique account ID
    account_id_to_find = 'ACC-1' # The unique identifying value
    print(f"1. Attempting to find customer_id for Account ID: {account_id_to_find}")
    
    # Call the utility: (table_name, name_column, unique_name_value)
    # The function automatically constructs 'SELECT customer_id FROM customer WHERE account_id = ...'
    customer_uuid = get_id_by_name("customer", "account_id", account_id_to_find)
    
    if customer_uuid:
        print(f"   ✅ Found customer_id: {customer_uuid}")
    else:
        print(f"   ❌ Customer with account ID '{account_id_to_find}' not found. Did you seed the data?")
        
    print("-" * 30)

    # Example 2: Find the UUID for a Device using its unique device name
    device_name_to_find = 'VAR1.DEN1' # The unique identifying value
    print(f"2. Attempting to find device_id for Device Name: {device_name_to_find}")
    
    # Call the utility: (table_name, name_column, unique_name_value)
    # The function automatically constructs 'SELECT device_id FROM devices WHERE device_name = ...'
    device_uuid = get_id_by_name("devices", "device_name", device_name_to_find)
    
    if device_uuid:
        print(f"   ✅ Found device_id: {device_uuid}")
    else:
        print(f"   ❌ Device named '{device_name_to_find}' not found. Did you seed the data?")
    
    print("-" * 30)
    
    # Example 3: Finding an ID that doesn't exist
    missing_service_name = 'NonExistent-Service'
    print(f"3. Attempting to find service_id for Service Name: {missing_service_name}")
    
    missing_uuid = get_id_by_name("fabric_service", "service_name", missing_service_name)
    
    if missing_uuid:
        print(f"   Unexpectedly found service_id: {missing_uuid}")
    else:
        print(f"   ✅ Correctly returned None (Service not found).")
        

if __name__ == '__main__':
    # Execute the demonstration function when the script is run directly
    demonstrate_lookup()