import psycopg2
from psycopg2 import Error

# --- 1. Database Configuration ---
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "mydatabase",  # <-- CHANGE THIS
    "user": "myuser",          # <-- CHANGE THIS
    "password": "mypassword"   # <-- CHANGE THIS
}

# --- 2. Health Status Mapping ---
# Maps the numeric score (1, 2, 3) to the text label for logging/reporting
HEALTH_MAPPING = {
    1: 'Good',
    2: 'Amber',
    3: 'Red',
}

# --- 3. Device Data List ---
# NOTE: The last element in the tuple is the numeric health score (1, 2, or 3).
DEVICE_LIST = [
    # (devicename, gw_shortname, devicerole, devicetype, availabilityzone, lifecyclestatus, servicestatus, devicemodel, devicevendor, health)
    ('SDR1.NYC1', 'NYC1', 'SDR', 'Router', 'Zone 0', 'Growth', 'Active', 'MX10004', 'Juniper', 1), # Good
    ('SDR2.NYC1', 'NYC1', 'SDR', 'Router', 'Zone 0', 'Growth', 'Active', 'MX10004', 'Juniper', 1), # Good
    ('VAR1.NYC1', 'NYC1', 'VAR', 'Router', 'Zone 0', 'Growth', 'Active', 'MX10004', 'Juniper', 2), # Amber
    ('VAR2.NYC1', 'NYC1', 'VAR', 'Router', 'Zone 0', 'Growth', 'Active', 'MX10004', 'Juniper', 2), # Amber
    ('VAR3.NYC1', 'NYC1', 'VAR', 'Router', 'Zone 0', 'Growth', 'Active', 'MX10004', 'Juniper', 3), # Red
]

# --- 4. Insertion Function with Existence Check ---

def insert_new_devices(devices_data: list):
    """
    Connects to PostgreSQL, checks for existing devices, 
    and inserts only the new devices in a batch.
    """
    conn = None
    try:
        print("Connecting to the PostgreSQL database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # --- A. Check for Existing Devices ---
        
        cur.execute("SELECT deviceName FROM devices;")
        existing_devices = {row[0] for row in cur.fetchall()}
        
        new_devices_to_insert = []
        devices_skipped = 0
        
        for device_row in devices_data:
            device_name = device_row[0]
            
            if device_name in existing_devices:
                # print(f"Skipping device: {device_name} (Already exists)")
                devices_skipped += 1
            else:
                new_devices_to_insert.append(device_row)
        
        print(f"\nChecked {len(devices_data)} devices.")
        print(f"Skipped {devices_skipped} existing devices.")
        print(f"Found {len(new_devices_to_insert)} new devices to insert.")

        if not new_devices_to_insert:
            print("No new devices to insert. Operation finished.")
            return

        # --- B. Perform Batch Insertion of New Devices ---

        insert_query = """
        INSERT INTO devices (
            devicename, gw_shortname, devicerole, devicetype, availabilityzone, 
            lifecyclestatus, servicestatus, devicemodel, devicevendor, health
        ) 
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        );
        """
        
        print(f"Executing batch insert for {len(new_devices_to_insert)} new devices...")
        
        cur.executemany(insert_query, new_devices_to_insert)
        
        conn.commit()
        cur.close()
        
        # Log successful inserts with the text status
        print("✅ New device data insertion complete and committed.")
        for row in new_devices_to_insert:
            device_name = row[0]
            health_score = row[-1]
            health_text = HEALTH_MAPPING.get(health_score, 'Unknown')
            print(f"  - Inserted {device_name} (Health: {health_score} - {health_text})")

    except (Exception, Error) as error:
        print(f"❌ Error during database operation: {error}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("\nPostgreSQL connection closed.")

# --- 5. Main Execution ---
if __name__ == "__main__":
    insert_new_devices(DEVICE_LIST)