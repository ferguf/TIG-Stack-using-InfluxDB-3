import psycopg2
from psycopg2 import Error
import random
import string
import sys # <-- Import the sys module

# --- 1. Database Configuration ---
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "mydatabase",
    "user": "myuser",
    "password": "mypassword"
}

# --- 2. Hardware Data List (Template) ---
# NOTE: The first element is the deviceName, which will be filtered by input.
HARDWARE_TEMPLATE = [
    # (deviceName, component_type, manufacturer, model_number, serial_number, firmware_version, health_status)
    ('VAR3.NYC1', 'Route Engine 0', 'Juniper', 'JNP-RE-MX10000', None, '1.0.1', '1'),
    ('VAR3.NYC1', 'Route Engine 1', 'Juniper', 'JNP-RE-MX10000', None, '1.0.1', '1'),
    ('VAR3.NYC1', 'Line Card 0', 'Juniper', 'JNP-LC480-SF', None, '1.0.1', '1'),
    ('VAR3.NYC1', 'Line Card 1', 'Juniper', 'JNP-LC480-SF', None, '1.0.1', '1'),
    ('VAR3.NYC1', 'Line Card 2', 'Juniper', 'JNP-LC480-SF', None, '1.0.1', '1'),
    ('VAR3.NYC1', 'Power Supply 0', 'Juniper', 'JNP-PSM-2400-AC', None, '1.0.1', '1'),
    ('VAR3.NYC1', 'Power Supply 1', 'Juniper', 'JNP-PSM-2400-AC', None, '1.0.1', '3'),
    ('VAR3.NYC1', 'Power Supply 2', 'Juniper', 'JNP-PSM-2400-AC', None, '1.0.1', '2'),
    # Add other devices here, e.g., if you want to run the script for a different device:
    # ('VAR3.ALB1', 'Management Card', 'Cisco', 'MGMT-ASR', None, '5.0.0', 'OK'),
]

# --- 3. Serial Number Generation Function ---

def generate_serial(model: str, length: int = 7) -> str:
    """
    Generates a serial number based on the model and a random string.
    """
    prefix = model.split('-')[0][:4].upper()
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    generated_sn = f"{prefix}-{random_chars}"
    return generated_sn[:length]

# --- 4. Insertion Function ---

def insert_hardware(hardware_data: list, target_device_name: str):
    """
    Connects to PostgreSQL, filters data for the target device, 
    looks up device IDs, generates serial numbers, and inserts records.
    """
    conn = None
    try:
        # Filter the hardware data based on the command line input
        filtered_hardware = [row for row in hardware_data if row[0] == target_device_name]
        
        if not filtered_hardware:
            print(f"⚠️ No hardware configuration found for device: {target_device_name}")
            return

        print(f"--- Processing Hardware for {target_device_name} ---")
        print("Connecting to the PostgreSQL database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # --- A. Pre-fetch Device IDs ---
        # Get the UUID for the target device
        cur.execute("SELECT deviceId FROM devices WHERE deviceName = %s;", (target_device_name,))
        device_result = cur.fetchone()
        
        if not device_result:
            print(f"❌ Device '{target_device_name}' not found in the 'devices' table. Cannot insert hardware.")
            return
            
        target_device_id = device_result[0]

        # --- B. Prepare Data for Insertion ---
        insert_data = []
        generated_sns = set() 
        
        for row in filtered_hardware:
            (_, component_type, manufacturer, model_number, 
             _, firmware_version, health_status) = row # _ is the serial number placeholder
            
            # 1. Generate a unique serial number for the hardware component
            serial_number = generate_serial(model_number, length=7)
            
            while serial_number in generated_sns:
                serial_number = generate_serial(model_number, length=7)
                
            generated_sns.add(serial_number)

            # 2. Create the prepared row tuple
            prepared_row = (
                target_device_id, # Target Device ID (UUID)
                component_type,
                manufacturer,
                model_number,
                serial_number,    # Newly Generated SN
                firmware_version,
                health_status
            )
            insert_data.append(prepared_row)

        # --- C. Perform Batch Insertion ---
        insert_query = """
        INSERT INTO device_hardware (
            device_id, component_type, manufacturer, model_number, 
            serial_number, firmware_version, health_status
        ) 
        VALUES (
            %s, %s, %s, %s, %s, %s, %s
        );
        """
        
        print(f"\nExecuting batch insert for {len(insert_data)} hardware components...")
        
        cur.executemany(insert_query, insert_data)
        
        conn.commit()
        cur.close()
        print("✅ Hardware data insertion complete and committed.")
        for data in insert_data:
             print(f"  - Inserted {data[3]} ({data[1]}) with SN: {data[4]}")

    except (Exception, Error) as error:
        print(f"❌ Error during database operation: {error}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("PostgreSQL connection closed.")

# --- 5. Main Execution ---
if __name__ == "__main__":
    # Check for command line argument
    if len(sys.argv) < 2:
        print("Usage: python add-hardware.py <DEVICE_NAME>")
        print("Example: python add-hardware.py VAR3.NYC1")
        sys.exit(1)
        
    device_name_input = sys.argv[1]
    
    insert_hardware(HARDWARE_TEMPLATE, device_name_input)