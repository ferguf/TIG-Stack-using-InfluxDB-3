"""File Name: 'db_config.py' and version '1.1.15' date: 'November 29, 2025 4:48 PM MST' (Enhancement: Added get_sqlalchemy_url() helper for use with SQLAlchemy configurations.)"""
import psycopg2
from psycopg2 import Error
import sys
from typing import Optional, Any, Dict
import uuid 
import csv 
import os 
from datetime import datetime

# --- DATABASE CONNECTION DETAILS ---
# NOTE: Replace with your actual connection details
# IMPORTANT: Ensure your PostgreSQL service is running and these details are correct.
# Explicitly adding the default PostgreSQL port (5432) for robustness.
DB_CONN_STRING = "dbname=mydatabase user=myuser password=mypassword host=localhost port=5432"
SCHEMA_FILE = 'customer_setup.sql'

# --- DATA FILE CONFIGURATION ---
DATA_DIR = 'python/data'
CUSTOMERS_CSV_FILE = os.path.join(DATA_DIR, 'db_customers.csv')
FABRIC_SERVICES_CSV_FILE = os.path.join(DATA_DIR, 'db_fabric_services.csv')
DEVICE_CSV_FILE = os.path.join(DATA_DIR, 'db_devices.csv')
PORTS_CSV_FILE = os.path.join(DATA_DIR, 'db_ports.csv')


def get_db_connection():
    """
    Establishes a connection to the PostgreSQL database using psycopg2.
    Returns the connection object or None on failure, without exiting the process.
    """
    conn = None
    try:
        conn = psycopg2.connect(DB_CONN_STRING)
        # print("✅ Database connection established.")
        return conn
    except psycopg2.OperationalError as e:
        # Print failure but do NOT call sys.exit(1) here.
        print(f"❌ DATABASE CONNECTION FAILED: {e}")
        print(f"Connection string: {DB_CONN_STRING}")
        print("Please ensure the PostgreSQL service is running and the connection details are correct.")
        return None 
    except Exception as e:
        print(f"❌ An unexpected error occurred during connection: {e}")
        return None

def get_sqlalchemy_url() -> str:
    """
    Converts the psycopg2 connection string to the SQLAlchemy URL format.
    Example: postgresql://user:password@host:port/dbname
    """
    # Parse the key=value pairs from DB_CONN_STRING
    params = dict(item.split('=') for item in DB_CONN_STRING.split(' '))
    
    db_name = params.get('dbname', 'mydatabase')
    user = params.get('user', 'myuser')
    password = params.get('password', 'mypassword')
    host = params.get('host', 'localhost')
    port = params.get('port', '5432')
    
    # Construct the URL expected by SQLAlchemy
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
        
def handle_db_error(message: str, conn: Optional[Any], rollback: bool = True):
    """Handles database errors by printing the message and rolling back the transaction."""
    if conn and rollback:
        conn.rollback()
    print(f"❌ DB ERROR: {message}")

def handle_connection_close(conn: Optional[Any]):
    """Safely closes the database connection."""
    if conn:
        try:
            conn.close()
            # print("✅ Database connection closed.")
        except Error as e:
            # Catch potential error during close operation
            print(f"    Error during connection close: {e}")


# --- UTILITY FUNCTIONS ---

def get_id_by_name(table_name: str, name_column: str, unique_name: str) -> Optional[str]:
    """
    Fetches the UUID (primary key) from a table given a unique name.
    """
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return None # Connection failed
            
        cur = conn.cursor()
        
        # --- FIX: Explicitly map table names to their correct primary key column names ---
        pk_mapping = {
            'customers': 'customer_id',
            'devices': 'device_id',
            # PK for 'fabric_service' table is 'service_id'
            'fabric_services': 'service_id', 
            'ports': 'port_id'
        }
        
        pk_column = pk_mapping.get(table_name.lower())
        
        if not pk_column:
             # Fallback for unexpected table names, stripping a possible 's' for simple plural-to-singular
             pk_column = f"{table_name.rstrip('s').lower()}_id"
             
        if not pk_column:
             raise ValueError(f"Could not determine primary key for table: {table_name}")
        # --------------------------------------------------------------------------------
        
        query = f"SELECT {pk_column} FROM {table_name} WHERE {name_column} = %s;"
        cur.execute(query, (unique_name,))
        result = cur.fetchone()
        
        return str(result[0]) if result else None
    
    except Error as e:
        handle_db_error(f"Failed to fetch ID for {unique_name} in table {table_name}: {e}", conn, rollback=False)
        return None
    except ValueError as e:
        handle_db_error(f"Configuration error in get_id_by_name: {e}", conn, rollback=False)
        return None
    finally:
        handle_connection_close(conn)


# --- CLI OPTION 4: Schema Setup ---
def initialize_schema():
    """
    [CLI Option 4] Reads and executes the entire SQL script from 'customer_setup.sql' to
    create all tables, enums, sequences, and trigger functions (Schema Setup).
    
    NOTE: The SQL file MUST be idempotent (e.g., use CREATE TABLE IF NOT EXISTS)
    to prevent data destruction on subsequent runs.
    """
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return # Connection error handled in get_db_connection
            
        cur = conn.cursor()

        print(f"--- [4] Initializing Database Schema from {SCHEMA_FILE} ---")
        
        # Read the entire SQL file
        if not os.path.exists(SCHEMA_FILE):
             raise FileNotFoundError(f"SQL schema file not found at: {SCHEMA_FILE}")

        with open(SCHEMA_FILE, 'r') as f:
            sql_script = f.read()

        # Execute the entire script
        cur.execute(sql_script)
        
        conn.commit()
        print("💾 Database schema initialized successfully (all tables, enums, and triggers created).")

    except Error as e:
        handle_db_error(f"during comprehensive schema creation: {e}", conn, rollback=True)
        sys.exit(1) # Keep exit here for critical schema creation failure
    except FileNotFoundError as e:
        print(f"❌ SCHEMA FILE ERROR: {e}")
        sys.exit(1) # Keep exit here for missing file
    finally:
        handle_connection_close(conn)

# --- CLI OPTION 5: Database Seeding ---
def seed_inventory_data():
    """
    [CLI Option 5] Seeds the core tables from respective CSV files (Database Seeding).
    
    NOTE: This seeding process is idempotent. It only inserts data if a record 
    with the unique identifier (e.g., account_id, device_name) does not already exist.
    """
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return # Connection error handled in get_db_connection
            
        cur = conn.cursor()
        
        customer_map: Dict[str, str] = {} # Map account_id to customer_id (UUID string)
        service_map: Dict[str, str] = {} # Map service_name to service_id
        
        print("\n--- [5] Starting Inventory Data Seeding (Idempotent) ---")

        # --- 1. Seed Customers ---
        inserted_customers_count = 0
        if os.path.exists(CUSTOMERS_CSV_FILE):
            with open(CUSTOMERS_CSV_FILE, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader) 
                
                for row in reader:
                    if len(row) < 2: continue
                    customer_name, account_id = [r.strip() for r in row[:2]]
                    
                    cur.execute("SELECT customer_id FROM customers WHERE account_id = %s;", (account_id,))
                    existing_customer = cur.fetchone()
                    
                    if existing_customer is None:
                        cur.execute(
                            "INSERT INTO customers (customer_name, account_id) VALUES (%s, %s) RETURNING customer_id;",
                            (customer_name, account_id)
                        )
                        customer_id = cur.fetchone()[0]
                        inserted_customers_count += 1
                    else:
                        customer_id = existing_customer[0]
                            
                    customer_map[account_id] = str(customer_id)
                        
            print(f"    Seeding customers: Added {inserted_customers_count} new customers.")
        else:
            print(f"⚠️ Skipping customer seeding: CSV file not found at {CUSTOMERS_CSV_FILE}")

        # --- 2. Seed Fabric Services ---
        inserted_services_count = 0
        if os.path.exists(FABRIC_SERVICES_CSV_FILE) and customer_map:
            with open(FABRIC_SERVICES_CSV_FILE, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader) 
                
                print(f"    Seeding services...")

                for row in reader:
                    if len(row) < 5: continue
                    
                    # CSV Format expected: customer_account_id, service_name, service_alias, service_type, service_description
                    customer_account_id, service_name, service_alias, service_type, service_description = [r.strip() for r in row[:5]]
                    
                    customer_id = customer_map.get(customer_account_id)
                    if not customer_id: continue
                    
                    cur.execute("SELECT service_id FROM fabric_services WHERE service_name = %s;", (service_name,))
                    existing_service = cur.fetchone()
                    
                    if existing_service is None:
                        # NEW: Using mock data/defaults for route_target (will be updated by trigger later) and health_status (1=Green)
                        mock_health_status = 1 
                        mock_route_target = None # Let the trigger auto-generate this on a real service
                        
                        cur.execute(
                            """
                            INSERT INTO fabric_services 
                            (customer_id, service_name, service_alias, service_type, service_description, health_status, route_target) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING service_id;
                            """,
                            (customer_id, service_name, service_alias, service_type, service_description, mock_health_status, mock_route_target)
                        )
                        service_id = cur.fetchone()[0]
                        inserted_services_count += 1
                    else:
                        service_id = existing_service[0]

                    service_map[service_name] = str(service_id)
                        
            print(f"    Seeding services: Added {inserted_services_count} new services.")
        else:
            print(f"⚠️ Skipping service seeding: Check if {FABRIC_SERVICES_CSV_FILE} exists or customers are loaded.")


        # --- 3. Seed Devices ---
        inserted_devices_count = 0
        if os.path.exists(DEVICE_CSV_FILE):
            with open(DEVICE_CSV_FILE, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader) 
                
                print(f"    Seeding devices...")

                for row in reader:
                    if len(row) < 4: continue
                        
                    # CSV Format expected: device_name, gw_shortname (now location), device_role, device_model
                    device_name, location, device_role, device_model = [r.strip() for r in row[:4]]

                    cur.execute("SELECT device_id FROM devices WHERE device_name = %s;", (device_name,))
                    if cur.fetchone() is None:
                        # NEW: Providing mock data/defaults for the additional columns in the 'devices' table
                        mock_vendor = 'Juniper' if 'RTR' in device_name else 'Cisco'
                        mock_serial = f"SN-{device_name}-{datetime.now().strftime('%f')}"
                        mock_zone = location.upper() + '-A'
                        mock_description = f"Core device at {location} for role {device_role}."
                        mock_health = 1 # Green
                        
                        cur.execute(
                            """
                            INSERT INTO devices (device_name, location, device_role, device_model, device_vendor, serial_number, availability_zone, lifecycle_status, planning_status, health_status, device_description) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                            """,
                            (device_name, location, device_role, device_model, mock_vendor, mock_serial, mock_zone, 'Active', 'Deployed', mock_health, mock_description)
                        )
                        inserted_devices_count += 1
                            
            print(f"    Seeding devices: Added {inserted_devices_count} new devices.")
        else:
            print(f"⚠️ Skipping device seeding: CSV file not found at {DEVICE_CSV_FILE}")


        # --- 4. Seed Ports ---
        
        cur.execute("SELECT device_id, device_name FROM devices;")
        device_data = cur.fetchall()
        device_ids = {name: dev_id for dev_id, name in device_data}
        
        inserted_ports_count = 0

        if os.path.exists(PORTS_CSV_FILE):
            with open(PORTS_CSV_FILE, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader) 
                
                print(f"    Seeding ports...")

                for row in reader:
                    if len(row) < 5: continue
                        
                    # CSV Format expected: device_name, port_name, port_service_status, port_type, port_speed
                    device_name, port_name, status, port_type, speed = [r.strip() for r in row[:5]]
                    
                    dev_id = device_ids.get(device_name)
                    if not dev_id: continue
                        
                    cur.execute("SELECT port_id FROM ports WHERE device_id = %s AND port_name = %s;", (dev_id, port_name))
                    if cur.fetchone() is None:
                        # NEW: Providing mock data/defaults for the additional columns in the 'ports' table
                        mock_description = f"Uplink for {device_name}"
                        mock_optic = f"{speed}-LR"
                        mock_tagging = 'Tagged'
                        mock_cktid = f"CKT-{device_name}-{port_name}"
                        mock_health = 1
                        
                        # Note: service_id is defaulted to NULL since it's unassigned inventory
                        cur.execute(
                            """
                            INSERT INTO ports (device_id, port_name, port_speed, port_description, port_optic, port_tagging, port_cktid, port_service_status, port_type, port_health_status)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                            """,
                            (dev_id, port_name, speed, mock_description, mock_optic, mock_tagging, mock_cktid, status, port_type, mock_health)
                        )
                        inserted_ports_count += 1
                            
            if inserted_ports_count > 0:
                print(f"    Seeding ports: Added {inserted_ports_count} new ports.")
            else:
                print("    Inventory already seeded. Skipping port insertion.")
        else:
            print(f"⚠️ Skipping port seeding: CSV file not found at {PORTS_CSV_FILE}")
        
        conn.commit()


    except Error as e:
        handle_db_error(f"during inventory seeding: {e}", conn, rollback=True)
    except FileNotFoundError:
        handle_db_error(f"during inventory seeding: Check if necessary CSV files exist in the '{DATA_DIR}' directory.", conn, rollback=True)
    finally:
        handle_connection_close(conn)

if __name__ == '__main__':
    initialize_schema()
    seed_inventory_data()