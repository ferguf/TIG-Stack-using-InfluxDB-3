import csv
import sys
import os
from psycopg2 import Error
from typing import List, Tuple, Any

# Import shared configuration and database handlers
from python.db_config import get_db_connection, handle_db_error, handle_connection_close

# --- Constants for Bulk Loading ---

# --- Health Status Mapping ---
HEALTH_MAPPING = {
    1: 'Good',
    2: 'Amber',
    3: 'Red',
}

# Expected column names in the CSV file (10 columns total)
EXPECTED_COLUMNS = [
    'device_name', 'gw_shortname', 'device_role', 'device_type', 
    'availability_zone', 'lifecycle_status', 'device_status', 
    'device_model', 'device_vendor', 'health'
]
EXPECTED_COL_COUNT = len(EXPECTED_COLUMNS)

def read_devices_from_csv(filepath: str) -> List[Tuple[Any, ...]]:
    """
    Reads device data from a CSV file, validates the header, 
    and converts the 'health' column to an integer.
    """
    devices_data = []
    print(f"Attempting to read data from {filepath}...")
    
    try:
        with open(filepath, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            
            # Read and validate header
            try:
                header = next(reader)
                if header != EXPECTED_COLUMNS:
                    print("❌ Error: CSV header mismatch.")
                    print(f"Expected: {EXPECTED_COLUMNS}")
                    print(f"Found: {header}")
                    return []
            except StopIteration:
                print("❌ Error: CSV file is empty.")
                return []
                
            # Read data rows
            for i, row in enumerate(reader, 2): # Start counting from line 2 (first data row)
                if len(row) != EXPECTED_COL_COUNT:
                    print(f"❌ Error on line {i}: Expected {EXPECTED_COL_COUNT} columns, found {len(row)}. Skipping row.")
                    continue
                
                # Convert the last element (health score) to integer
                try:
                    health_score = int(row[-1])
                    if health_score not in HEALTH_MAPPING:
                        print(f"⚠️ Warning on line {i}: Health score '{row[-1]}' is invalid. Must be 1, 2, or 3. Defaulting to 1.")
                        health_score = 1
                    
                    processed_row = tuple(row[:-1]) + (health_score,)
                    devices_data.append(processed_row)
                    
                except ValueError:
                    print(f"❌ Error on line {i}: 'health' value ('{row[-1]}') must be an integer. Skipping row.")
                    continue
                    
    except FileNotFoundError:
        print(f"❌ Error: File not found at '{filepath}'.")
        return []
    except Exception as e:
        print(f"❌ An unexpected error occurred while reading the CSV: {e}")
        return []

    print(f"Successfully read {len(devices_data)} valid device records.")
    return devices_data


def insert_new_devices(devices_data: list):
    """
    Connects to PostgreSQL, checks for existing devices by name, 
    and inserts only the new devices in a batch.
    """
    if not devices_data:
        print("No data provided for insertion. Exiting.")
        return
        
    conn = None
    try:
        print("Connecting to the PostgreSQL database...")
        conn = get_db_connection()
        cur = conn.cursor()
        
        # --- A. Check for Existing Devices ---
        cur.execute("SELECT device_name FROM devices;")
        existing_devices = {row[0] for row in cur.fetchall()}
        
        new_devices_to_insert = []
        devices_skipped = 0
        
        for device_row in devices_data:
            device_name = device_row[0]
            
            if device_name in existing_devices:
                devices_skipped += 1
            else:
                new_devices_to_insert.append(device_row)
        
        print(f"\nChecked {len(devices_data)} total devices from CSV.")
        print(f"Skipped {devices_skipped} existing devices.")
        print(f"Found {len(new_devices_to_insert)} new devices to insert.")

        if not new_devices_to_insert:
            print("No new devices to insert. Operation finished.")
            return

        # --- B. Perform Batch Insertion of New Devices ---

        insert_query = """
        INSERT INTO devices (
            device_name, gw_shortname, device_role, device_type, availability_zone, 
            lifecycle_status, device_status, device_model, device_vendor, health
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
        handle_db_error(f"during database operation: {error}", conn)
    finally:
        handle_connection_close(conn)


def bulk_load_devices_main(filepath: str = None):
    """
    Main function for bulk device loading. Handles argument parsing and execution.
    This function is designed to be called by a CLI tool.
    """
    CSV_FILENAME = 'add_devices.csv'
    # Default directory as specified by the user
    DEFAULT_DIR = r'C:\Users\fergu\TIG-Stack-using-InfluxDB-3\python\data' 

    if filepath:
        if os.path.isdir(filepath):
            # If the input is a directory, join it with the expected filename
            final_filepath = os.path.join(filepath, CSV_FILENAME)
        else:
            # Assume it's the full, explicit filepath
            final_filepath = filepath
        print(f"Using provided path: '{final_filepath}'")
    else:
        # No argument provided, use the absolute default path
        final_filepath = os.path.join(DEFAULT_DIR, CSV_FILENAME)
        print(f"Using default path: '{final_filepath}'")

    devices_data = read_devices_from_csv(final_filepath)
    insert_new_devices(devices_data)

if __name__ == "__main__":
    # Allows bulk_load_devices.py to run directly for testing/single-use
    path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    bulk_load_devices_main(path_arg)