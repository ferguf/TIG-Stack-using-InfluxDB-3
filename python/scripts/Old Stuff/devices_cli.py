import sys
import device_operations as db 
from python.bulk_load_devices import bulk_load_devices_main # Retained for bulk loading

# Available status and lifecycle options based on schema checks
DEVICE_STATUS_OPTIONS = ['Planned', 'Active', 'Capped']
LIFECYCLE_STATUS_OPTIONS = ['Growth', 'Cap Growth', 'Cap provisioning', 'Remove']
HARDWARE_HEALTH_STATUS_OPTIONS = ['Healthy', 'Warning', 'Critical', 'Decommissioned'] # Assumption

# Default values for the VAR role
VAR_DEFAULTS = {
    'vendor': 'Juniper',
    'model': 'MX10004',
    'az': 'Zone 0',
    'lifecycle': 'Growth',
    'status': 'Planned',
    'health': 1 # Default health specified by user
}

def print_help():
    """Prints usage instructions."""
    print("\n--- Device Management Commands ---")
    print("  c - Create a new device")
    print("  r - Read (list) all devices")
    print("  u - Update an existing device's details")
    print("  d - Delete an existing device")
    print("\n--- Hardware Management Commands ---")
    print("  hc - Create a new hardware component")
    print("  hr - Read/List hardware components for a device")
    print("  hu - Update an existing hardware component (by Serial Number)")
    print("  hd - Delete a hardware component (by Serial Number)")
    print("\n--- Utility ---")
    print("  lb - Load Bulk: Load devices from CSV (uses default path if none specified)")
    print("  h - Show this help message")
    print("  q - Quit the application")

# --- New Handler for Bulk Loading ---
def handle_load_bulk():
    """Handles the bulk loading of devices from CSV."""
    print("\n--- Execute Bulk Device Load ---")
    # Prompt for optional path; bulk_load_devices_main handles the default path logic
    path_input = input("Enter path/to/csv or directory (leave blank for default): ").strip() or None
    bulk_load_devices_main(path_input)

def handle_create():
    """Handles the creation of a new device record with role-based defaults."""
    print("\n--- Create New Device ---")
    
    # 1. Mandatory Input: Device Name
    name = input("Enter Device Name (e.g., VAR.1.DEN1): ").strip()
    if not name:
        print("❌ Device Name is required.")
        return

    # Initialize all fields
    role = None
    shortname = None
    dev_type = None
    az = None
    lifecycle = None
    status = None
    model = None
    vendor = None
    health = None

    # Try to parse role and shortname from device_name (e.g., ROLE.ID.LOCATION)
    parts = name.split('.')
    if len(parts) >= 2:
        role = parts[0].upper()
        shortname = parts[-1]
        print(f"Inferred Role: {role}, GW Shortname: {shortname}")
    else:
        print("⚠️ Device Name format not recognized (expected ROLE.ID.LOCATION).")
    
    # --- Check for VAR Defaults ---
    is_var_role = (role == 'VAR')

    if is_var_role:
        print(f"Applying defaults for {role} role (Vendor=Juniper, Model=MX10004, Status=Planned, Health=1)...")
        vendor = VAR_DEFAULTS['vendor']
        model = VAR_DEFAULTS['model']
        az = VAR_DEFAULTS['az']
        lifecycle = VAR_DEFAULTS['lifecycle']
        status = VAR_DEFAULTS['status']
        health = VAR_DEFAULTS['health']
    
    # --- Handle Mandatory/Missing Fields (Non-VAR or Parse Failure) ---
    
    # Ensure mandatory fields are set (prompt if derived value is missing)
    if not shortname:
        shortname = input("Enter GW Shortname (Mandatory): ").strip() or None
    if not role:
        role = input("Enter Device Role (Mandatory): ").strip() or None
    
    # Status is mandatory (but set by default for VAR), so prompt only if not VAR
    if not is_var_role or status is None:
        status = input(f"Enter Device Status {DEVICE_STATUS_OPTIONS} (Mandatory): ").strip() or None

    # --- Handle Optional Fields (Prompt only if not set by VAR defaults) ---
    if not is_var_role or dev_type is None:
        dev_type = input("Enter Device Type (optional): ").strip() or None
    
    if not is_var_role or az is None:
        az = input("Enter Availability Zone (optional): ").strip() or None

    if not is_var_role or lifecycle is None:
        lifecycle = input(f"Enter Lifecycle Status {LIFECYCLE_STATUS_OPTIONS} (optional): ").strip() or None
    
    if not is_var_role or model is None:
        model = input("Enter Device Model (optional): ").strip() or None

    if not is_var_role or vendor is None:
        vendor = input("Enter Device Vendor (optional): ").strip() or None
    
    if not is_var_role or health is None:
        health_str = input("Enter Health (integer, optional, default 1): ").strip()
        health = int(health_str) if health_str.isdigit() else 1
    
    # Final check for mandatory fields before DB call
    if not all([name, shortname, role, status]):
        print("❌ Creation failed: Device Name, GW Shortname, Device Role, and Device Status are mandatory.")
        return

    # --- Check against constraints (IMPROVED: Abort if invalid status/lifecycle is provided) ---
    if status is not None and status not in DEVICE_STATUS_OPTIONS:
        print(f"❌ Error: Device Status '{status}' is invalid. Options are {DEVICE_STATUS_OPTIONS}. Creation aborted.")
        return

    if lifecycle is not None and lifecycle not in LIFECYCLE_STATUS_OPTIONS:
        print(f"❌ Error: Lifecycle Status '{lifecycle}' is invalid. Options are {LIFECYCLE_STATUS_OPTIONS}. Creation aborted.")
        return
    # -----------------------------------------------------------------------------------------

    db.create_device(
        device_name=name,
        gw_shortname=shortname,
        device_role=role,
        device_status=status,
        device_type=dev_type,
        availability_zone=az,
        lifecycle_status=lifecycle,
        device_model=model,
        device_vendor=vendor,
        health=health
    )

def handle_read():
    """Handles the reading/listing of all devices."""
    db.get_all_devices()

def select_device_for_action(action: str) -> str | None:
    """
    Lists devices and prompts the user to select one by index or Device Name.
    Returns the Device Name of the selected device.
    """
    print(f"\n--- Select Device to {action.upper()} ---")
    
    devices = db.get_all_devices(silent=True) # Assuming 'silent=True' prevents the DB module from printing, 
                                             # allowing the CLI to format the output.
    
    if not devices:
        print("No devices found to select.")
        return None

    # --- FIX: Print the indexed list of devices for user selection ---
    print("\nAvailable Devices:")
    selection_map = {} # Map index to device_name
    for index, device in enumerate(devices, start=1):
        # Assuming typical SQLite row structure: (id, name, shortname, role, type, az, status, lifecycle, model, vendor, health)
        try:
            device_name = device[1]
            role_info = device[3]
            status_info = device[6]
            print(f"  [{index}] {device_name} (Role: {role_info}, Status: {status_info})")
            selection_map[str(index)] = device_name
        except IndexError:
            # Fallback for unexpected data structure
            print(f"  [{index}] Device ID {device[0]} (Data structure incomplete)")
            selection_map[str(index)] = device[1] if len(device) > 1 else str(device[0])
    # -----------------------------------------------------------------
    
    while True:
        selection = input(f"Enter index or Device Name to {action}: ").strip()
        
        if not selection:
            print("Action cancelled.")
            return None

        # 1. Check if selection is an index number
        if selection in selection_map:
            return selection_map[selection]
        
        # 2. Assume selection is the Device Name and check if it exists
        selected_device = db.get_device_by_name(selection)
        if selected_device:
            # get_device_by_name returns a dict, so we ensure the key is correct
            return selected_device.get('device_name')
        
        print("❌ Invalid selection. Please enter a valid index number or an existing Device Name.")


def handle_update():
    """Handles updating an existing device's details."""
    original_name = select_device_for_action("Update")
    if not original_name:
        return

    device_data = db.get_device_by_name(original_name)
    if not device_data:
        print(f"❌ Could not retrieve details for {original_name}.")
        return

    print(f"\n--- Update Device: {original_name} ---")
    print("Enter new value for the field, or leave blank to keep the current value.")
    
    # Collect all possible updates
    updates = {}
    
    updates['new_name'] = input(f"  [1] Device Name (Current: {device_data.get('device_name')}): ").strip() or None
    updates['new_shortname'] = input(f"  [2] GW Shortname (Current: {device_data.get('gw_shortname')}): ").strip() or None
    updates['new_role'] = input(f"  [3] Device Role (Current: {device_data.get('device_role')}): ").strip() or None
    updates['new_type'] = input(f"  [4] Device Type (Current: {device_data.get('device_type')}): ").strip() or None
    updates['new_az'] = input(f"  [5] Availability Zone (Current: {device_data.get('availability_zone')}): ").strip() or None
    
    # Lifecycle Status validation is critical here
    new_lifecycle_input = input(f"  [6] Lifecycle Status {LIFECYCLE_STATUS_OPTIONS} (Current: {device_data.get('lifecycle_status')}): ").strip() or None
    if new_lifecycle_input is not None and new_lifecycle_input not in LIFECYCLE_STATUS_OPTIONS:
        print(f"❌ Error: Lifecycle Status '{new_lifecycle_input}' is invalid. Options are {LIFECYCLE_STATUS_OPTIONS}. Update aborted.")
        return
    updates['new_lifecycle'] = new_lifecycle_input

    # Device Status validation is critical here
    new_status_input = input(f"  [7] Device Status {DEVICE_STATUS_OPTIONS} (Current: {device_data.get('device_status')}): ").strip() or None
    if new_status_input is not None and new_status_input not in DEVICE_STATUS_OPTIONS:
        print(f"❌ Error: Device Status '{new_status_input}' is invalid. Options are {DEVICE_STATUS_OPTIONS}. Update aborted.")
        return
    updates['new_status'] = new_status_input

    updates['new_model'] = input(f"  [8] Device Model (Current: {device_data.get('device_model')}): ").strip() or None
    updates['new_vendor'] = input(f"  [9] Device Vendor (Current: {device_data.get('device_vendor')}): ").strip() or None
    
    new_health_str = input(f" [10] Health (integer) (Current: {device_data.get('health')}): ").strip()
    updates['new_health'] = int(new_health_str) if new_health_str.isdigit() else None
    
    # Execute update, only passing fields that were entered (or None if health was not a digit)
    db.update_device(
        original_name,
        new_name=updates['new_name'],
        new_shortname=updates['new_shortname'],
        new_role=updates['new_role'],
        new_type=updates['new_type'],
        new_az=updates['new_az'],
        new_lifecycle=updates['new_lifecycle'],
        new_status=updates['new_status'],
        new_model=updates['new_model'],
        new_vendor=updates['new_vendor'],
        new_health=updates['new_health']
    )


def handle_delete():
    """Handles deleting an existing device record."""
    device_name = select_device_for_action("Delete")
    if not device_name:
        return

    device_info = db.get_device_by_name(device_name)
    if not device_info:
        # get_device_by_name already handles printing failure/not found
        return 

    print(f"\n⚠️ WARNING: Deleting device '{device_info['device_name']}' (Shortname: {device_info['gw_shortname']}).")
    print("This action may affect related records in 'device_hardware' and 'interfaces' tables.")
    confirm = input("Type 'YES' to confirm deletion: ").strip()

    if confirm == 'YES':
        db.delete_device(device_name)
    else:
        print("Deletion cancelled.")

# --- NEW HARDWARE HANDLERS ---

def handle_hardware_create():
    """Handles creating a new hardware component."""
    print("\n--- Create New Hardware Component ---")
    device_name = input("Enter Device Name to attach component to: ").strip()
    if not device_name:
        print("❌ Device Name is required.")
        return

    # Mandatory fields
    c_type = input("Enter Component Type (e.g., Linecard, PSU, Fan): ").strip()
    model_num = input("Enter Model Number: ").strip()
    
    if not all([c_type, model_num]):
        print("❌ Component Type and Model Number are mandatory.")
        return

    # Optional fields
    mfr = input("Enter Manufacturer (optional): ").strip() or None
    s_num = input("Enter Serial Number (optional, must be unique): ").strip() or None
    fw_ver = input("Enter Firmware Version (optional): ").strip() or None
    
    health = input(f"Enter Health Status {HARDWARE_HEALTH_STATUS_OPTIONS} (optional): ").strip() or None
    if health is not None and health not in HARDWARE_HEALTH_STATUS_OPTIONS:
        print(f"❌ Error: Health Status '{health}' is invalid. Options are {HARDWARE_HEALTH_STATUS_OPTIONS}. Creation aborted.")
        return

    db.create_hardware_component(
        device_name=device_name,
        component_type=c_type,
        model_number=model_num,
        manufacturer=mfr,
        serial_number=s_num,
        firmware_version=fw_ver,
        health_status=health
    )

def handle_hardware_read():
    """Handles listing hardware components for a specific device."""
    print("\n--- List Hardware Components ---")
    device_name = input("Enter Device Name to view components: ").strip()
    if not device_name:
        print("❌ Device Name is required.")
        return
    
    db.get_hardware_components_by_device_name(device_name)

def handle_hardware_update():
    """Handles updating a hardware component based on its Serial Number."""
    print("\n--- Update Hardware Component ---")
    serial_number = input("Enter Serial Number of the component to update: ").strip()
    if not serial_number:
        print("❌ Serial Number is required for update.")
        return

    print("\nUpdating component with Serial Number: " + serial_number)
    print("Enter new value for the field, or leave blank to keep current.")

    new_type = input("Component Type (optional): ").strip() or None
    new_model = input("Model Number (optional): ").strip() or None
    new_mfr = input("Manufacturer (optional): ").strip() or None
    new_fw = input("Firmware Version (optional): ").strip() or None
    
    new_health = input(f"Health Status {HARDWARE_HEALTH_STATUS_OPTIONS} (optional): ").strip() or None
    if new_health is not None and new_health not in HARDWARE_HEALTH_STATUS_OPTIONS:
        print(f"❌ Error: Health Status '{new_health}' is invalid. Options are {HARDWARE_HEALTH_STATUS_OPTIONS}. Update aborted.")
        return

    db.update_hardware_component(
        serial_number=serial_number,
        new_type=new_type,
        new_model=new_model,
        new_mfr=new_mfr,
        new_fw=new_fw,
        new_health=new_health
    )

def handle_hardware_delete():
    """Handles deleting a hardware component based on its Serial Number."""
    print("\n--- Delete Hardware Component ---")
    serial_number = input("Enter Serial Number of the component to delete: ").strip()
    if not serial_number:
        print("❌ Serial Number is required for deletion.")
        return
    
    print(f"\n⚠️ WARNING: Deleting component with Serial Number '{serial_number}'.")
    confirm = input("Type 'YES' to confirm deletion: ").strip()

    if confirm == 'YES':
        db.delete_hardware_component(serial_number)
    else:
        print("Deletion cancelled.")


def main():
    """Main application loop for the Device CLI."""
    print("=============================================")
    print("      Network Device Management Tool (CRUD)      ")
    print("=============================================")
    print_help()
    
    while True:
        try:
            command = input("\nEnter command (h for help): ").strip().lower()
            
            if command == 'c':
                handle_create()
            elif command == 'r':
                handle_read()
            elif command == 'u':
                handle_update()
            elif command == 'd':
                handle_delete()
            # New Hardware Commands
            elif command == 'hc':
                handle_hardware_create()
            elif command == 'hr':
                handle_hardware_read()
            elif command == 'hu':
                handle_hardware_update()
            elif command == 'hd':
                handle_hardware_delete()
            # Utility Commands
            elif command == 'lb':
                handle_load_bulk()
            elif command == 'q':
                print("Exiting application. Goodbye!")
                sys.exit(0)
            elif command == 'h':
                print_help()
            elif command:
                print(f"Unknown command: '{command}'. Type 'h' for help.")
        except KeyboardInterrupt:
            print("\nExiting application. Goodbye!")
            sys.exit(0)
        except Exception as e:
            # Catching generic database or runtime errors
            print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    # When run directly, we ignore any initial command line arguments
    # and 
    # proceed directly into the interactive loop.
    main()