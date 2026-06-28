"""File Name: 'customer_operations.py' and version '1.1.3' date: 'November 29, 2025 2:54 PM MST' (Change: Integrated version control string and reviewed implementation.)"""
import uuid
import random
import string
from psycopg2 import Error
import db_config as config # Standardizing the import alias for consistency
from datetime import datetime
from typing import Optional, Any, Dict, List

# --- Conceptual Status Storage ---
# This dictionary holds the conceptual status of services for the duration of the 
# script execution. Default status for new services is 'Pending'.
_conceptual_service_statuses = {} 

# --- HELPER FUNCTIONS ---

def get_customer_uuid_by_account_id(account_id: str) -> Optional[str]:
    """Retrieves the internal UUID for a customer using their public Account ID."""
    conn = None
    customer_uuid = None
    try:
        conn = config.get_db_connection()
        if not conn: return None
        cur = conn.cursor()
        select_query = "SELECT customer_id FROM customer WHERE account_id = %s;"
        cur.execute(select_query, (account_id,))
        result = cur.fetchone()
        
        if result:
            customer_uuid = str(result[0])
        
    except (Exception, Error) as error:
        config.handle_db_error(f"during fetching customer UUID by account ID: {error}", conn)
    finally:
        config.handle_connection_close(conn)
    return customer_uuid

def get_device_id_by_name(device_name: str) -> Optional[str]:
    """Retrieves the internal UUID for a device using its device_name."""
    conn = None
    device_uuid = None
    try:
        conn = config.get_db_connection()
        if not conn: return None
        cur = conn.cursor()
        # NOTE: Using 'devices' table as defined in the configuration history
        select_query = "SELECT device_id FROM devices WHERE device_name = %s;"
        cur.execute(select_query, (device_name,))
        result = cur.fetchone()
        
        if result:
            device_uuid = str(result[0])
        else:
            print(f"⚠️ Device '{device_name}' not found in the 'devices' inventory.")
        
    except (Exception, Error) as error:
        config.handle_db_error(f"during fetching device UUID by name: {error}", conn)
    finally:
        config.handle_connection_close(conn)
    return device_uuid


def update_service_status(service_id: str, new_status: str) -> None:
    """
    [CONCEPTUAL ONLY] Updates the status of a service in the conceptual store.
    """
    service_id_str = str(service_id)
    global _conceptual_service_statuses
    if service_id_str in _conceptual_service_statuses:
        _conceptual_service_statuses[service_id_str] = new_status
        print(f"    ✓ Service {service_id_str[:8]}... status updated to '{new_status}'.")
    else:
        # If the service doesn't exist in the conceptual store, initialize it
        _conceptual_service_statuses[service_id_str] = new_status
        print(f"⚠️ Warning: Service {service_id_str[:8]}... initialized with status '{new_status}'.")


def get_customer_name_by_id(customer_id: str) -> Optional[str]:
    """Retrieves the customer name using their internal UUID."""
    conn = None
    customer_name = None
    try:
        conn = config.get_db_connection()
        if not conn: return None
        cur = conn.cursor()
        select_query = "SELECT customer_name FROM customer WHERE customer_id = %s;"
        cur.execute(select_query, (customer_id,))
        result = cur.fetchone()
        
        if result:
            customer_name = result[0]
        
    except (Exception, Error) as error:
        config.handle_db_error(f"during fetching customer name by ID: {error}", conn)
    finally:
        config.handle_connection_close(conn)
    return customer_name

# --- CUSTOMER CRUD OPERATIONS ---

def create_customer(customer_name: str, account_id: str) -> Optional[str]:
    """Adds a new customer record to the database."""
    conn = None
    new_customer_id = None
    try:
        conn = config.get_db_connection()
        if not conn: return None
        cur = conn.cursor()
        
        insert_query = """
        INSERT INTO customer (customer_name, account_id)
        VALUES (%s, %s) RETURNING customer_id;
        """
        cur.execute(insert_query, (customer_name, account_id))
        
        new_customer_id = cur.fetchone()[0]
        conn.commit()
        
        print(f"✅ Created new customer '{customer_name}' with Account ID: {account_id}.")
        return str(new_customer_id)

    except Error as e:
        if 'unique constraint' in str(e):
              config.handle_db_error(f"Customer creation failed: Account ID '{account_id}' already exists.", conn)
        else:
            config.handle_db_error(f"during customer creation: {e}", conn)
        return None
    finally:
        config.handle_connection_close(conn)

def get_customer_by_account_id(account_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single customer record using their public Account ID."""
    conn = None
    customer_data = None
    try:
        conn = config.get_db_connection()
        if not conn: return None
        cur = conn.cursor()
        
        select_query = "SELECT customer_id, customer_name, account_id, created_at FROM customer WHERE account_id = %s;"
        cur.execute(select_query, (account_id,))
        result = cur.fetchone()
        
        if result:
            customer_data = {
                'customer_id': str(result[0]),
                'customer_name': result[1],
                'account_id': result[2],
                'created_at': result[3]
            }
        
    except (Exception, Error) as error:
        config.handle_db_error(f"during fetching customer by Account ID: {error}", conn)
    finally:
        config.handle_connection_close(conn)
    return customer_data


def update_customer_name(account_id: str, new_name: str) -> bool:
    """Updates the name of an existing customer."""
    conn = None
    try:
        conn = config.get_db_connection()
        if not conn: return False
        cur = conn.cursor()
        
        update_query = "UPDATE customer SET customer_name = %s WHERE account_id = %s;"
        cur.execute(update_query, (new_name, account_id))
        conn.commit()
        
        if cur.rowcount > 0:
            print(f"✅ Customer (ID: {account_id}) name updated to '{new_name}'.")
            return True
        else:
            print(f"⚠️ Update failed: Customer with Account ID '{account_id}' not found.")
            return False

    except (Exception, Error) as error:
        config.handle_db_error(f"during customer update: {error}", conn)
        return False
    finally:
        config.handle_connection_close(conn)


def delete_customer(account_id: str) -> bool:
    """Deletes a customer and cascade-deletes all associated services, ports, and RTs."""
    conn = None
    try:
        conn = config.get_db_connection()
        if not conn: return False
        cur = conn.cursor()
        
        delete_query = "DELETE FROM customer WHERE account_id = %s;"
        cur.execute(delete_query, (account_id,))
        conn.commit()
        
        if cur.rowcount > 0:
            print(f"✅ Customer (ID: {account_id}) and all associated records DELETED.")
            return True
        else:
            print(f"⚠️ Deletion failed: Customer with Account ID '{account_id}' not found.")
            return False

    except (Exception, Error) as error:
        config.handle_db_error(f"during customer deletion: {error}", conn)
        return False
    finally:
        config.handle_connection_close(conn)


def get_all_customers() -> List[tuple]:
    """Retrieves all records from the 'customer' table used for selection/data lookup."""
    conn = None
    customers = []
    try:
        conn = config.get_db_connection()
        if not conn: return []
        cur = conn.cursor()

        # Select query for raw data (4 columns)
        select_query = "SELECT customer_id, customer_name, account_id, created_at FROM customer ORDER BY customer_name;"
        cur.execute(select_query)
        customers = cur.fetchall()
        
    except (Exception, Error) as error:
        config.handle_db_error(f"during fetching all customers: {error}", conn)
    finally:
        config.handle_connection_close(conn)
    return customers


def list_customers_with_service_count() -> List[tuple]:
    """Retrieves customer records, joins with fabric_service to count services, and prints the formatted output."""
    conn = None
    customers = []
    try:
        conn = config.get_db_connection()
        if not conn: return []
        cur = conn.cursor()

        select_query = """
        SELECT 
            c.customer_id, c.customer_name, c.account_id, c.created_at,
            COUNT(fs.service_id) AS service_count
        FROM customer c
        LEFT JOIN fabric_service fs ON c.customer_id = fs.customer_id
        GROUP BY c.customer_id, c.customer_name, c.account_id, c.created_at
        ORDER BY c.customer_name;
        """
        cur.execute(select_query)
        customers = cur.fetchall()
        
        if not customers:
            print("⚠️ No customers found in the database.")
            return []

        print("\n--- All Customers ---")
        separator_width = 135
        print("-" * separator_width) 
        print(f"{'ID (First 8)':<12} | {'Customer Name':<30} | {'Account ID':<15} | {'Created At':<30} | {'Services':<10}") 
        print("-" * separator_width)

        for customer in customers:
            customer_id, name, account_id, created_at, service_count = customer
            formatted_date = created_at.strftime('%Y-%m-%d %H:%M:%S %Z').strip()
            print(f"{str(customer_id)[:8]:<12} | {name:<30} | {account_id:<15} | {formatted_date:<30} | {service_count:<10}")
            
        print("-" * separator_width)

    except (Exception, Error) as error:
        config.handle_db_error(f"during fetching all customers with service count: {error}", conn)
    finally:
        config.handle_connection_close(conn)
    return customers


# --- FABRIC SERVICE OPERATIONS ---

def create_fabric_service(customer_id: str, service_name: str, alias: str, service_type: str, description: str) -> Optional[str]:
    """Creates a new fabric service record."""
    conn = None
    new_service_id = None
    try:
        conn = config.get_db_connection()
        if not conn: return None
        cur = conn.cursor()
        
        insert_query = """
        INSERT INTO fabric_service (customer_id, service_name, service_alias, service_type, service_description)
        VALUES (%s, %s, %s, %s, %s) RETURNING service_id;
        """
        cur.execute(insert_query, (customer_id, service_name, alias, service_type, description))
        
        new_service_id = cur.fetchone()[0]
        conn.commit()
        
        # Initialize conceptual status
        update_service_status(new_service_id, 'Pending')

        print(f"✅ Created new service '{service_name}' ({service_type}) for customer {customer_id[:8]}...")
        return str(new_service_id)

    except Error as e:
        if 'violates unique constraint' in str(e):
              config.handle_db_error(f"Service creation failed: Service name '{service_name}' already exists.", conn)
        elif 'violates foreign key constraint' in str(e):
              config.handle_db_error(f"Service creation failed: Customer ID '{customer_id}' does not exist.", conn)
        else:
            config.handle_db_error(f"during fabric service creation: {e}", conn)
        return None
    finally:
        config.handle_connection_close(conn)


def list_all_fabric_services() -> List[Dict[str, Any]]:
    """Retrieves and lists all fabric services with customer name and conceptual status."""
    conn = None
    services = []
    try:
        conn = config.get_db_connection()
        if not conn: return []
        cur = conn.cursor()

        select_query = """
        SELECT 
            fs.service_id, fs.service_name, fs.service_type, fs.service_alias, 
            c.customer_name, fs.created_at
        FROM fabric_service fs
        JOIN customer c ON fs.customer_id = c.customer_id
        ORDER BY c.customer_name, fs.service_name;
        """
        cur.execute(select_query)
        results = cur.fetchall()
        
        if not results:
            print("⚠️ No fabric services found.")
            return []

        print("\n--- All Fabric Services ---")
        separator_width = 170
        print("-" * separator_width)
        print(f"{'ID (First 8)':<12} | {'Customer Name':<30} | {'Service Name':<30} | {'Type':<15} | {'Alias':<25} | {'Status (Conceptual)':<20}")
        print("-" * separator_width)

        for row in results:
            service_id, name, service_type, alias, customer_name, created_at = row
            service_id_str = str(service_id)
            # Retrieve conceptual status, default to 'Pending' if not set
            status = _conceptual_service_statuses.get(service_id_str, 'Pending')
            
            services.append({
                'service_id': service_id_str,
                'service_name': name,
                'customer_name': customer_name,
                'service_type': service_type,
                'alias': alias,
                'status': status
            })
            
            print(f"{service_id_str[:8]:<12} | {customer_name:<30} | {name:<30} | {service_type:<15} | {alias:<25} | {status:<20}")
            
        print("-" * separator_width)

    except (Exception, Error) as error:
        config.handle_db_error(f"during fetching all fabric services: {error}", conn)
    finally:
        config.handle_connection_close(conn)
    return services


# --- FABRIC PORT/INVENTORY OPERATIONS ---

def get_unassigned_ports(device_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieves and returns unassigned ports from the 'ports' table that meet 
    the criteria for provisioning (Physical type, Available or Ready for use status).
    """
    conn = None
    ports = []
    try:
        conn = config.get_db_connection()
        if not conn: return []
        cur = conn.cursor()
        
        select_query = """
        SELECT 
            d.device_name,
            p.port_id, 
            p.port_name, 
            p.port_service_status,
            p.fabric_port_type
        FROM ports p
        JOIN devices d ON p.device_id = d.device_id 
        WHERE p.service_id IS NULL -- Unassigned
          AND p.fabric_port_type = 'Physical' -- Physical only
          AND p.port_service_status IN ('Available', 'Ready for use') -- Ready for provisioning
        """
        params = []
        
        if device_name:
            select_query += "\n  AND d.device_name = %s"
            params.append(device_name)
        
        select_query += "\nORDER BY d.device_name, p.port_name;"

        cur.execute(select_query, params)
        
        results = cur.fetchall()
        
        for row in results:
            device_name, port_id, port_name, port_service_status, fabric_port_type = row 
            ports.append({
                'device_name': device_name,
                'port_id': str(port_id),
                'port_name': port_name, 
                'port_service_status': port_service_status,
                'fabric_port_type': fabric_port_type
            })

    except (Exception, Error) as error:
        config.handle_db_error(f"during fetching filtered unassigned fabric ports: {error}", conn)
    finally:
        config.handle_connection_close(conn)
    return ports


def list_assigned_ports(service_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieves and returns ports currently assigned to a service (or all assigned ports).
    """
    conn = None
    ports = []
    try:
        conn = config.get_db_connection()
        if not conn: return []
        cur = conn.cursor()
        
        select_query = """
        SELECT 
            d.device_name,
            p.port_id, 
            p.port_name, 
            p.port_service_status,
            c.customer_name,
            fs.service_name
        FROM ports p
        JOIN devices d ON p.device_id = d.device_id 
        JOIN fabric_service fs ON p.service_id = fs.service_id
        JOIN customer c ON fs.customer_id = c.customer_id
        WHERE p.service_id IS NOT NULL 
        """
        params = []
        
        if service_id:
            select_query += "\n  AND p.service_id = %s"
            params.append(service_id)
        
        select_query += "\nORDER BY d.device_name, p.port_name;"

        cur.execute(select_query, params)
        results = cur.fetchall()
        
        if not results:
            print("⚠️ No ports currently assigned to services.")
            return []

        print("\n--- Assigned Fabric Ports ---")
        separator_width = 150
        print("-" * separator_width)
        print(f"{'Customer':<20} | {'Service':<20} | {'Device':<15} | {'Port Name':<25} | {'Status':<15} | {'Port ID (First 8)':<18}")
        print("-" * separator_width)
        
        for row in results:
            device_name, port_id, port_name, port_service_status, customer_name, service_name = row 
            
            ports.append({
                'device_name': device_name,
                'port_id': str(port_id),
                'port_name': port_name, 
                'port_service_status': port_service_status,
                'customer_name': customer_name,
                'service_name': service_name
            })
            
            print(f"{customer_name[:18]:<20} | {service_name[:18]:<20} | {device_name:<15} | {port_name:<25} | {port_service_status:<15} | {str(port_id)[:8]}...")
            
        print("-" * separator_width)
        
    except (Exception, Error) as error:
        config.handle_db_error(f"during fetching assigned fabric ports: {error}", conn)
    finally:
        config.handle_connection_close(conn)
    return ports


def add_fabric_port(
    service_id: str,
    device_name: str, 
    port_name: str, 
    new_port_status: str = 'Assigned', 
    new_port_type: str = 'Fabric Port' 
) -> Optional[str]:
    """
    Updates an existing port's configuration to link it to a service and sets
    its type and status using the unique device_name and port_name combination.
    """
    
    device_id = get_device_id_by_name(device_name)
    if not device_id:
        print(f"❌ Provisioning failed: Device '{device_name}' not found.")
        return None

    conn = None
    new_port_id = None
    try:
        conn = config.get_db_connection()
        if not conn: return None
        cur = conn.cursor()
        
        # Check if the port is currently unassigned (service_id IS NULL)
        cur.execute("""
            SELECT port_id FROM ports 
            WHERE device_id = %s AND port_name = %s AND service_id IS NULL;
        """, (device_id, port_name))
        
        if cur.fetchone() is None:
            print(f"❌ Provisioning failed: Port '{port_name}' on device '{device_name}' is not unassigned/available.")
            return None
        
        update_query = """
        UPDATE ports
        SET
            service_id = %s,
            port_service_status = %s::port_service_status_enum,
            fabric_port_type = %s::fabric_port_type_enum
        WHERE device_id = %s AND port_name = %s 
        RETURNING port_id;
        """
        cur.execute(update_query, (
            service_id, 
            new_port_status,
            new_port_type,
            device_id, 
            port_name 
        ))
        
        new_port_id = cur.fetchone()[0]
        conn.commit()

        # Update service conceptual status
        update_service_status(service_id, 'Active')
        
        print(f"✅ Provisioned Port '{port_name}' on '{device_name}' to Service {service_id[:8]}...")
        return str(new_port_id)

    except Error as e:
        config.handle_db_error(f"during provisioning fabric port: {e}", conn)
        return None
    finally:
        config.handle_connection_close(conn)


def release_fabric_port(device_name: str, port_name: str) -> bool:
    """
    Releases a port from its assigned service, setting service_id to NULL, 
    status to 'Available', and fabric_port_type back to 'Physical'.
    """
    device_id = get_device_id_by_name(device_name)
    if not device_id:
        print(f"❌ Release failed: Device '{device_name}' not found.")
        return False
        
    conn = None
    try:
        conn = config.get_db_connection()
        if not conn: return False
        cur = conn.cursor()

        # Get service_id before releasing for conceptual status update
        cur.execute("""
            SELECT service_id FROM ports 
            WHERE device_id = %s AND port_name = %s;
        """, (device_id, port_name))
        result = cur.fetchone()
        
        if result and result[0]:
            released_service_id = str(result[0])
            
            # Update the port record, resetting service_id, status, AND type.
            update_query = """
            UPDATE ports
            SET
                service_id = NULL,
                port_service_status = 'Available'::port_service_status_enum,
                fabric_port_type = 'Physical'::fabric_port_type_enum -- RESET TO PHYSICAL
            WHERE device_id = %s AND port_name = %s 
            """
            cur.execute(update_query, (device_id, port_name))
            conn.commit()
            
            if cur.rowcount > 0:
                print(f"✅ Released Port '{port_name}' on '{device_name}'. Now available.")
                
                # Check if the released service still has other assigned ports
                cur.execute("SELECT COUNT(*) FROM ports WHERE service_id = %s AND service_id IS NOT NULL;", (released_service_id,))
                remaining_ports = cur.fetchone()[0]
                
                if remaining_ports == 0:
                    update_service_status(released_service_id, 'Idle')
                
                return True
        else:
            print(f"⚠️ Release failed: Port '{port_name}' on device '{device_name}' is already unassigned or does not exist.")
            return False

    except (Exception, Error) as error:
        config.handle_db_error(f"during releasing fabric port: {error}", conn)
        return False
    finally:
        config.handle_connection_close(conn)