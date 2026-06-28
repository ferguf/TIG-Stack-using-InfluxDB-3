import psycopg2
from psycopg2 import Error
import sys

# --- 1. Database Configuration ---
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "mydatabase",  # <-- CHANGE THIS
    "user": "myuser",          # <-- CHANGE THIS
    "password": "mypassword"   # <-- CHANGE THIS
}

def get_router_ports(device_name: str):
    """
    Connects to PostgreSQL, finds the deviceId, and retrieves all ports 
    associated with that device.
    """
    conn = None
    try:
        print(f"--- Querying Interfaces for Device: {device_name} ---")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # 1. Look up the Device ID (UUID) from the devices table
        cur.execute("SELECT deviceId FROM devices WHERE deviceName = %s;", (device_name,))
        device_result = cur.fetchone()

        if not device_result:
            print(f"❌ Error: Device '{device_name}' not found in the 'devices' table.")
            return

        device_id = device_result[0]
        print(f"Found Device ID: {device_id}")

        # 2. Retrieve all interfaces using the deviceId
        query = """
        SELECT
            interface_name,
            interface_type,
            interface_status,
            service_bandwidth,
            cvlan_id,
            interface_description
        FROM
            service_interfaces
        WHERE
            device_id = %s;
        """
        cur.execute(query, (device_id,))
        ports = cur.fetchall()

        cur.close()

        # 3. Output Results
        if not ports:
            print(f"⚠️ No interfaces found for device '{device_name}'.")
            return

        print(f"\n✅ Found {len(ports)} Interfaces:")
        
        # Print a formatted table header
        print("-" * 80)
        print(f"{'Interface Name':<20} | {'Type':<15} | {'Status':<10} | {'Bandwidth':<10} | {'VLAN':<5}")
        print("-" * 80)

        for port in ports:
            interface_name, interface_type, status, bandwidth, cvlan, description = port
            print(f"{interface_name:<20} | {interface_type:<15} | {status:<10} | {bandwidth:<10} | {cvlan:<5} | {description if description else ''}")
        print("-" * 80)

    except (Exception, Error) as error:
        print(f"❌ Database error: {error}")
    finally:
        if conn:
            conn.close()
            print("PostgreSQL connection closed.")

# --- 4. Main Execution ---
if __name__ == "__main__":
    # Check for command line argument
    if len(sys.argv) < 2:
        print("Usage: python show_ports.py <DEVICE_NAME>")
        print("Example: python show_ports.py VAR2.DEN1")
        sys.exit(1)

    router_name = sys.argv[1]
    get_router_ports(router_name)