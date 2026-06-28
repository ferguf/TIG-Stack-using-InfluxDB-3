import sys
import uuid
from psycopg2 import Error

from python.db_config import get_db_connection, handle_connection_close
import db_operations as db

# Mock Device IDs for demonstration (for environments where the 'devices' table isn't fully populated)
MOCK_DEVICE_IDS = {
    "RTR-01": str(uuid.uuid4()),
    "SW-02": str(uuid.uuid4()),
    "FW-03": str(uuid.uuid4()),
}

def get_device_id_by_name(device_name: str) -> str | None:
    """Retrieves a device ID from the database or a mock list."""
    conn = None
    try:
        conn = get_db_connection()
        if not conn: return None
        cur = conn.cursor()
        
        # Attempt to get ID from database
        cur.execute("SELECT device_id FROM devices WHERE device_name = %s;", (device_name,))
        result = cur.fetchone()
        if result:
            return result[0]
        
        # Fallback to mock ID if not found in DB
        mock_id = MOCK_DEVICE_IDS.get(device_name)
        if mock_id:
             print(f"⚠️ Using Mock ID for Device '{device_name}'. Ensure DB is populated for real use.")
        else:
             print(f"❌ Error: Device '{device_name}' not found.")
        return mock_id

    except (Exception, Error) as error:
        print(f"Error fetching device ID: {error}")
        return MOCK_DEVICE_IDS.get(device_name)
    finally:
        handle_connection_close(conn)


def select_lag_from_list(device_name: str, device_id: str) -> tuple[str, str, str] | None:
    """Lists LAGs for a device and prompts the user to select one."""
    conn = None
    try:
        conn = get_db_connection()
        if not conn: return None
        cur = conn.cursor()

        # Get LAGs using the new helper function
        lags = db.get_ports_by_type(cur, device_id, port_type='AggregateEthernet')
        
        if not lags:
            print(f"⚠️ No Aggregated Ethernet interfaces (LAGs) found on {device_name}.")
            return None

        lag_map = {}
        print(f"\n--- Available LAGs on Device: {device_name} ---")
        print("-" * 80)
        print(f"{'#':<4} | {'Port Name':<20} | {'Speed':<10} | {'Status':<15}")
        print("-" * 80)

        for index, lag in enumerate(lags, start=1):
            lag_id, lag_name, lag_speed, lag_status = lag
            print(f"{index:<4} | {lag_name:<20} | {lag_speed:<10} | {lag_status:<15}")
            lag_map[str(index)] = (lag_id, lag_name, lag_speed) # (id, name, speed)
        print("-" * 80)

        while True:
            selection = input("Enter the index of the LAG to link: ").strip()
            if selection in lag_map:
                return lag_map[selection]
            print("❌ Invalid selection. Please enter a valid index number.")

    except (Exception, Error) as error:
        print(f"Error while listing LAGs: {error}")
        return None
    finally:
        handle_connection_close(conn)

def link_command():
    """
    Implements the interactive command to link two LAG interfaces and their members.
    """
    print("\n==============================================")
    print("        🔗 Link Aggregated Ethernet (LAGs)        ")
    print("==============================================")

    # --- 1. Select Device A and LAG A ---
    device_a_name = input("Enter the name of Device A: ").strip()
    device_a_id = get_device_id_by_name(device_a_name)
    if not device_a_id: return

    ae_a_info = select_lag_from_list(device_a_name, device_a_id)
    if not ae_a_info: return

    ae_a_id, ae_a_name, ae_a_speed = ae_a_info
    
    # --- 2. Select Device B and LAG B ---
    device_b_name = input("\nEnter the name of Device B: ").strip()
    device_b_id = get_device_id_by_name(device_b_name)
    if not device_b_id: return

    ae_b_info = select_lag_from_list(device_b_name, device_b_id)
    if not ae_b_info: return

    ae_b_id, ae_b_name, ae_b_speed = ae_b_info

    # --- 3. Get Members and Check Counts ---
    conn = None
    try:
        conn = get_db_connection()
        if not conn: return
        cur = conn.cursor()
        
        # Get member ports using the new helper function
        members_a = db.get_lag_members(cur, ae_a_id)
        members_b = db.get_lag_members(cur, ae_b_id)
        
        if not members_a or not members_b:
            print("❌ Error: Both LAGs must have at least one member port assigned to be linked externally.")
            return

        print(f"\n{ae_a_name} has {len(members_a)} member port(s).")
        print(f"{ae_b_name} has {len(members_b)} member port(s).")
        print(f"You can link up to {min(len(members_a), len(members_b))} member pair(s).")

        # --- 4. Interactive Member Pairing ---
        
        # Maps index to (id, name, speed) for the members
        map_a = {str(i+1): (m[0], m[1], m[2]) for i, m in enumerate(members_a)} # ID, Name, Speed
        map_b = {str(i+1): (m[0], m[1], m[2]) for i, m in enumerate(members_b)} # ID, Name, Speed
        
        available_a = set(map_a.keys())
        available_b = set(map_b.keys())
        
        member_pairings = [] # Stores (member_a_id, member_a_speed, member_b_id, member_b_speed)

        print("\n--- Member Port Pairing ---")
        
        while available_a and available_b:
            print(f"\nPorts for {ae_a_name}:")
            for idx in sorted(list(available_a)):
                _, m_name, m_speed = map_a[idx]
                print(f"  [{idx}] {m_name} ({m_speed})")

            print(f"\nPorts for {ae_b_name}:")
            for idx in sorted(list(available_b)):
                _, m_name, m_speed = map_b[idx]
                print(f"  [{idx}] {m_name} ({m_speed})")

            a_selection = input(f"Select port from {ae_a_name} index (or 'done'): ").strip()
            if a_selection.lower() == 'done': break

            if a_selection not in available_a:
                print("❌ Invalid selection for Port A.")
                continue

            b_selection = input(f"Select port from {ae_b_name} index: ").strip()
            if b_selection not in available_b:
                print("❌ Invalid selection for Port B.")
                continue

            # Process valid selection
            port_a = map_a[a_selection] # (id, name, speed)
            port_b = map_b[b_selection] # (id, name, speed)

            # Store (ID A, Speed A, ID B, Speed B)
            member_pairings.append((port_a[0], port_a[2], port_b[0], port_b[2]))
            
            # Remove selected ports from availability lists
            available_a.remove(a_selection)
            available_b.remove(b_selection)

            print(f"✅ Paired: {port_a[1]} <-> {port_b[1]}.")
            
        if not member_pairings:
            print("⚠️ No member pairs were selected. Aborting link operation.")
            return

        # --- 5. Execute Transaction ---
        print("\n--- Executing Database Link Transaction ---")
        db.link_lags_transaction(ae_a_info, ae_b_info, member_pairings)

    except (Exception, Error) as error:
        print(f"An error occurred during the linking process: {error}")
    finally:
        handle_connection_close(conn)


def print_help():
    """Prints usage instructions."""
    print("\nAvailable Commands:")
    print("  link        - Interactively links two Aggregated Ethernet (LAG) interfaces on separate devices and their members.")
    print("  exit / quit - Exit the application.")
    print("\nNote: This tool assumes the 'devices' and 'ports' tables are populated.")

def main():
    """Main application loop."""
    print("--- Network Inventory Tool ---")
    while True:
        try:
            command = input("\nEnter command ('link' or 'help'): ").strip().lower()
            
            if command == 'link':
                link_command()
            elif command in ['exit', 'quit']:
                print("Exiting application. Goodbye!")
                sys.exit(0)
            elif command == 'help':
                print_help()
            elif command:
                print(f"Unknown command: '{command}'. Type 'help' for available commands.")
        except KeyboardInterrupt:
            print("\nExiting application. Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    main()