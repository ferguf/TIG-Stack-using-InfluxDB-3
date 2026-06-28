import uuid
from psycopg2 import Error
from python.db_config import get_db_connection, handle_db_error, handle_connection_close
from datetime import datetime

# --- UTILITY FUNCTIONS ---

def get_device_id_by_name(device_name: str) -> uuid.UUID | None:
    """Retrieves the device_id (UUID) for a given device_name."""
    conn = None
    device_id = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        select_query = "SELECT device_id FROM devices WHERE device_name = %s;"
        cur.execute(select_query, (device_name,))
        result = cur.fetchone()
        if result:
            device_id = result[0]
    except Exception as e:
        handle_db_error(f"during fetching device_id for {device_name}: {e}", conn)
    finally:
        handle_connection_close(conn)
    return device_id

def get_lag_id_by_name_and_device(lag_name: str, device_id: uuid.UUID) -> uuid.UUID | None:
    """Retrieves the lag_id (UUID) for a given LAG name and device ID."""
    conn = None
    lag_id = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        select_query = "SELECT lag_id FROM lags WHERE lag_name = %s AND device_id = %s;"
        cur.execute(select_query, (lag_name, device_id))
        result = cur.fetchone()
        if result:
            lag_id = result[0]
    except Exception as e:
        # Note: We don't use handle_db_error here to avoid verbose output if lag doesn't exist.
        pass
    finally:
        handle_connection_close(conn)
    return lag_id

def get_port_id_by_name_and_device(port_name: str, device_id: uuid.UUID) -> uuid.UUID | None:
    """Retrieves the port_id (UUID) for a given port name and device ID."""
    conn = None
    port_id = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        select_query = "SELECT port_id FROM ports WHERE port_name = %s AND device_id = %s;"
        cur.execute(select_query, (port_name, device_id))
        result = cur.fetchone()
        if result:
            port_id = result[0]
    except Exception as e:
        # Note: We don't use handle_db_error here to avoid verbose output if port doesn't exist.
        pass
    finally:
        handle_connection_close(conn)
    return port_id


# -------------------------------------------------------------
# --- LAG (Link Aggregation Group) CRUD OPERATIONS ---
# -------------------------------------------------------------
# [LAG CRUD functions are assumed to be here, omitted for brevity but remain unchanged from the previous version, operating on the 'lags' table.]
# NOTE: The LAG functions (create_lag, get_lags_by_device_name, update_lag, delete_lag) from the previous file are conceptually here.

def create_lag(
    device_name: str, 
    lag_name: str, 
    lag_protocol: str, 
    admin_status: str,
    oper_status: str
) -> str | None:
    """Inserts a new LAG record."""
    device_id = get_device_id_by_name(device_name)
    if not device_id:
        print(f"❌ LAG creation failed: Device '{device_name}' not found.")
        return None

    conn = None
    new_lag_id = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        insert_query = """
        INSERT INTO lags (
            device_id, lag_name, lag_protocol, admin_status, oper_status
        )
        VALUES (%s, %s, %s, %s, %s)
        RETURNING lag_id;
        """
        cur.execute(insert_query, (
            device_id, lag_name, lag_protocol, admin_status, oper_status
        ))
        
        new_lag_id = cur.fetchone()[0]
        conn.commit()
        
        print(f"✅ Created LAG '{lag_name}' for device '{device_name}' with ID: {str(new_lag_id)[:8]}...")
        return str(new_lag_id)

    except Error as e:
        if 'duplicate key value violates unique constraint' in str(e) and 'lags_device_id_lag_name_key' in str(e):
            handle_db_error(f"LAG creation failed: LAG '{lag_name}' already exists on device '{device_name}'.", conn)
        else:
            handle_db_error(f"during LAG creation: {e}", conn)
        return None
    except Exception as e:
        handle_db_error(f"during LAG creation: {e}", conn)
        return None
    finally:
        handle_connection_close(conn)

def get_lags_by_device_name(device_name: str):
    """Retrieves all LAGs for a given device name."""
    device_id = get_device_id_by_name(device_name)
    if not device_id:
        print(f"⚠️ Device '{device_name}' not found.")
        return []

    conn = None
    lags = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        select_query = """
        SELECT 
            lag_id, lag_name, lag_protocol, admin_status, oper_status
        FROM lags 
        WHERE device_id = %s
        ORDER BY lag_name;
        """
        cur.execute(select_query, (device_id,))
        lags = cur.fetchall()

        if not lags:
            print(f"⚠️ No LAGs found for device '{device_name}'.")
            return []

        print(f"\n--- LAGs for Device: {device_name} ---")
        print("-" * 80)
        print(f"{'#ID':<8} | {'LAG Name':<10} | {'Protocol':<10} | {'Admin Status':<15} | {'Oper Status':<15}")
        print("-" * 80)

        for lag in lags:
            lag_id, name, proto, admin, oper = lag
            print(
                f"{str(lag_id)[:8]:<8} | {name:<10} | {proto:<10} | {admin:<15} | {oper:<15}"
            )
        print("-" * 80)

    except (Exception, Error) as error:
        handle_db_error(f"during fetching LAGs for device '{device_name}': {error}", conn)
    finally:
        handle_connection_close(conn)
    return lags

def update_lag(
    device_name: str,
    original_lag_name: str, 
    new_lag_name: str = None, 
    new_protocol: str = None, 
    new_admin_status: str = None, 
    new_oper_status: str = None
) -> bool:
    """
    Updates specified fields for a LAG based on device name and original LAG name.
    """
    device_id = get_device_id_by_name(device_name)
    if not device_id:
        print(f"❌ LAG update failed: Device '{device_name}' not found.")
        return False
        
    conn = None
    updates = []
    params = []
    
    if new_lag_name is not None:
        updates.append("lag_name = %s")
        params.append(new_lag_name)
    if new_protocol is not None:
        updates.append("lag_protocol = %s")
        params.append(new_protocol)
    if new_admin_status is not None:
        updates.append("admin_status = %s")
        params.append(new_admin_status)
    if new_oper_status is not None:
        updates.append("oper_status = %s")
        params.append(new_oper_status)

    if not updates:
        print("⚠️ No fields provided for LAG update.")
        return False

    params.append(device_id)
    params.append(original_lag_name)
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        update_query = f"""
        UPDATE lags
        SET {', '.join(updates)}
        WHERE device_id = %s AND lag_name = %s;
        """
        cur.execute(update_query, tuple(params))
        
        if cur.rowcount == 1:
            conn.commit()
            print(f"✅ Successfully updated LAG '{original_lag_name}' on device '{device_name}'.")
            return True
        else:
            print(f"⚠️ Update failed: LAG '{original_lag_name}' not found on device '{device_name}'.")
            return False

    except Error as e:
        if 'duplicate key value violates unique constraint' in str(e) and 'lags_device_id_lag_name_key' in str(e):
             handle_db_error(f"Update failed: New LAG Name '{new_lag_name}' already exists on device '{device_name}'.", conn)
        else:
            handle_db_error(f"during LAG update: {e}", conn)
        return False
    except Exception as e:
        handle_db_error(f"during LAG update: {e}", conn)
        return False
    finally:
        handle_connection_close(conn)

def delete_lag(device_name: str, lag_name: str) -> bool:
    """
    Deletes a LAG record based on device name and LAG name.
    """
    device_id = get_device_id_by_name(device_name)
    if not device_id:
        print(f"❌ LAG deletion failed: Device '{device_name}' not found.")
        return False

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        delete_query = "DELETE FROM lags WHERE device_id = %s AND lag_name = %s;"
        cur.execute(delete_query, (device_id, lag_name))
        
        if cur.rowcount == 1:
            conn.commit()
            print(f"✅ Successfully deleted LAG '{lag_name}' from device '{device_name}'.")
            return True
        else:
            print(f"⚠️ Deletion failed: LAG '{lag_name}' not found on device '{device_name}'.")
            return False

    except (Exception, Error) as error:
        handle_db_error(f"during LAG deletion: {error}", conn)
        return False
    finally:
        handle_connection_close(conn)

# -------------------------------------------------------------
# --- PORT (Physical/LAG Member) CRUD OPERATIONS ---
# (Operating on the 'ports' table using the provided schema)
# -------------------------------------------------------------

def create_port(
    device_name: str, 
    port_name: str, 
    port_speed: str, 
    fabric_port_type: str, 
    port_tagging: str, 
    service_status: str,
    lag_name: str = None, 
    customer_alias: str = None, 
    mac_address: str = None,
    port_optic: str = None,
    health: int = None,
    port_description: str = None
) -> str | None:
    """Inserts a new port (physical or LAG member) record."""
    device_id = get_device_id_by_name(device_name)
    if not device_id:
        print(f"❌ Port creation failed: Device '{device_name}' not found.")
        return None

    lag_id = None
    if lag_name:
        lag_id = get_lag_id_by_name_and_device(lag_name, device_id)
        if not lag_id:
            print(f"❌ Port creation failed: LAG '{lag_name}' not found on device '{device_name}'.")
            return None

    conn = None
    new_port_id = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        insert_query = """
        INSERT INTO ports (
            device_id, port_name, lag_id, port_speed, fabric_port_type, port_tagging, 
            service_status, customer_alias, mac_address, port_optic, health, port_description
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING port_id;
        """
        cur.execute(insert_query, (
            device_id, port_name, lag_id, port_speed, fabric_port_type, port_tagging, 
            service_status, customer_alias, mac_address, port_optic, health, port_description
        ))
        
        new_port_id = cur.fetchone()[0]
        conn.commit()
        
        print(f"✅ Created port '{port_name}' (Speed: {port_speed}) for device '{device_name}' with ID: {str(new_port_id)[:8]}...")
        return str(new_port_id)

    except Error as e:
        if 'duplicate key value violates unique constraint' in str(e) and 'ports_device_id_port_name_key' in str(e):
            handle_db_error(f"Port creation failed: Port '{port_name}' already exists on device '{device_name}'.", conn)
        else:
            handle_db_error(f"during port creation: {e}", conn)
        return None
    except Exception as e:
        handle_db_error(f"during port creation: {e}", conn)
        return None
    finally:
        handle_connection_close(conn)


def get_ports_by_device_name(device_name: str):
    """Retrieves all ports for a given device name, including LAG name if linked."""
    device_id = get_device_id_by_name(device_name)
    if not device_id:
        print(f"⚠️ Device '{device_name}' not found.")
        return []

    conn = None
    ports = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        select_query = """
        SELECT 
            p.port_id, p.port_name, p.port_speed, p.fabric_port_type, p.port_tagging, 
            p.service_status, p.health, p.port_description, l.lag_name
        FROM ports p
        LEFT JOIN lags l ON p.lag_id = l.lag_id
        WHERE p.device_id = %s
        ORDER BY p.port_name;
        """
        cur.execute(select_query, (device_id,))
        ports = cur.fetchall()

        if not ports:
            print(f"⚠️ No ports found for device '{device_name}'.")
            return []

        print(f"\n--- Ports (Physical/LAG Members) for Device: {device_name} ---")
        print("-" * 150)
        print(f"{'#ID':<8} | {'Port Name':<15} | {'LAG':<10} | {'Speed':<10} | {'Type':<15} | {'Tagging':<10} | {'Svc Status':<12} | {'Health':<6} | {'Description':<50}")
        print("-" * 150)

        for port in ports:
            p_id, name, speed, p_type, tagging, svc_status, health, desc, lag_name = port
            print(
                f"{str(p_id)[:8]:<8} | {name:<15} | {lag_name or 'N/A':<10} | {speed:<10} | {p_type:<15} | {tagging:<10} | {svc_status:<12} | {health or 'N/A':<6} | {desc or 'N/A':<50}"
            )
        print("-" * 150)

    except (Exception, Error) as error:
        handle_db_error(f"during fetching ports for device '{device_name}': {error}", conn)
    finally:
        handle_connection_close(conn)
    return ports

def update_port(
    device_name: str,
    original_port_name: str, 
    new_port_name: str = None, 
    new_lag_name: str = None, 
    new_speed: str = None, 
    new_type: str = None,
    new_tagging: str = None,
    new_svc_status: str = None,
    new_health: int = None,
    new_description: str = None
) -> bool:
    """
    Updates specified fields for a port based on device name and original port name.
    """
    device_id = get_device_id_by_name(device_name)
    if not device_id:
        print(f"❌ Port update failed: Device '{device_name}' not found.")
        return False
        
    conn = None
    updates = []
    params = []
    
    # Handle LAG update separately as it requires looking up lag_id
    if new_lag_name is not None:
        lag_id = get_lag_id_by_name_and_device(new_lag_name, device_id)
        if new_lag_name and not lag_id:
            print(f"❌ Port update failed: New LAG '{new_lag_name}' not found on device '{device_name}'.")
            return False
        updates.append("lag_id = %s")
        params.append(lag_id)
    
    if new_port_name is not None:
        updates.append("port_name = %s")
        params.append(new_port_name)
    if new_speed is not None:
        updates.append("port_speed = %s")
        params.append(new_speed)
    if new_type is not None:
        updates.append("fabric_port_type = %s")
        params.append(new_type)
    if new_tagging is not None:
        updates.append("port_tagging = %s")
        params.append(new_tagging)
    if new_svc_status is not None:
        updates.append("service_status = %s")
        params.append(new_svc_status)
    if new_health is not None:
        updates.append("health = %s")
        params.append(new_health)
    if new_description is not None:
        updates.append("port_description = %s")
        params.append(new_description)

    if not updates:
        print("⚠️ No fields provided for port update.")
        return False

    params.append(device_id)
    params.append(original_port_name)
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        update_query = f"""
        UPDATE ports
        SET {', '.join(updates)}
        WHERE device_id = %s AND port_name = %s;
        """
        cur.execute(update_query, tuple(params))
        
        if cur.rowcount == 1:
            conn.commit()
            print(f"✅ Successfully updated port '{original_port_name}' on device '{device_name}'.")
            return True
        else:
            print(f"⚠️ Update failed: Port '{original_port_name}' not found on device '{device_name}'.")
            return False

    except Error as e:
        if 'duplicate key value violates unique constraint' in str(e) and 'ports_device_id_port_name_key' in str(e):
             handle_db_error(f"Update failed: New Port Name '{new_port_name}' already exists on device '{device_name}'.", conn)
        else:
            handle_db_error(f"during port update: {e}", conn)
        return False
    except Exception as e:
        handle_db_error(f"during port update: {e}", conn)
        return False
    finally:
        handle_connection_close(conn)


def delete_port(device_name: str, port_name: str) -> bool:
    """
    Deletes a port record based on device name and port name.
    """
    device_id = get_device_id_by_name(device_name)
    if not device_id:
        print(f"❌ Port deletion failed: Device '{device_name}' not found.")
        return False

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        delete_query = "DELETE FROM ports WHERE device_id = %s AND port_name = %s;"
        cur.execute(delete_query, (device_id, port_name))
        
        if cur.rowcount == 1:
            conn.commit()
            print(f"✅ Successfully deleted port '{port_name}' from device '{device_name}'.")
            return True
        else:
            print(f"⚠️ Deletion failed: Port '{port_name}' not found on device '{device_name}'.")
            return False

    except (Exception, Error) as error:
        handle_db_error(f"during port deletion: {error}", conn)
        return False
    finally:
        handle_connection_close(conn)


# -------------------------------------------------------------
# --- LOGICAL INTERFACE (IP Config) CRUD OPERATIONS ---
# (Operating on the 'logical_interfaces' table)
# -------------------------------------------------------------

def create_logical_interface(
    device_name: str, 
    full_interface_name: str,
    unit_number: int,
    admin_status: str,
    oper_status: str,
    parent_name: str, # Can be Port Name or LAG Name
    ipv4_address: str = None, 
    ipv6_address: str = None, 
    description: str = None
) -> str | None:
    """Inserts a new logical interface (IP sub-interface) record."""
    device_id = get_device_id_by_name(device_name)
    if not device_id:
        print(f"❌ Logical Interface creation failed: Device '{device_name}' not found.")
        return None

    parent_port_id = get_port_id_by_name_and_device(parent_name, device_id)
    parent_lag_id = get_lag_id_by_name_and_device(parent_name, device_id)
    
    if not parent_port_id and not parent_lag_id:
        print(f"❌ Logical Interface creation failed: Parent '{parent_name}' (Port or LAG) not found on device '{device_name}'.")
        return None

    if parent_port_id and parent_lag_id:
        print("❌ Logical Interface creation failed: Parent name is ambiguous (found both Port and LAG).")
        return None
    
    conn = None
    new_interface_id = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        insert_query = """
        INSERT INTO logical_interfaces (
            device_id, full_interface_name, unit_number, parent_port_id, parent_lag_id, 
            ipv4_address, ipv6_address, admin_status, oper_status, description
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING interface_id;
        """
        cur.execute(insert_query, (
            device_id, full_interface_name, unit_number, parent_port_id, parent_lag_id, 
            ipv4_address, ipv6_address, admin_status, oper_status, description
        ))
        
        new_interface_id = cur.fetchone()[0]
        conn.commit()
        
        print(f"✅ Created Logical Interface '{full_interface_name}' (Unit: {unit_number}) on parent '{parent_name}' with ID: {str(new_interface_id)[:8]}...")
        return str(new_interface_id)

    except Error as e:
        if 'duplicate key value violates unique constraint' in str(e) and 'logical_interfaces_device_id_full_interface_name_key' in str(e):
            handle_db_error(f"Logical Interface creation failed: Interface '{full_interface_name}' already exists on device '{device_name}'.", conn)
        else:
            handle_db_error(f"during Logical Interface creation: {e}", conn)
        return None
    except Exception as e:
        handle_db_error(f"during Logical Interface creation: {e}", conn)
        return None
    finally:
        handle_connection_close(conn)


def get_logical_interfaces_by_device_name(device_name: str):
    """Retrieves all logical interfaces for a given device name."""
    device_id = get_device_id_by_name(device_name)
    if not device_id:
        print(f"⚠️ Device '{device_name}' not found.")
        return []

    conn = None
    interfaces = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        select_query = """
        SELECT 
            li.interface_id, li.full_interface_name, li.unit_number, 
            li.ipv4_address, li.ipv6_address, li.admin_status, 
            li.oper_status, COALESCE(p.port_name, l.lag_name) as parent_name
        FROM logical_interfaces li
        LEFT JOIN ports p ON li.parent_port_id = p.port_id
        LEFT JOIN lags l ON li.parent_lag_id = l.lag_id
        WHERE li.device_id = %s
        ORDER BY li.full_interface_name;
        """
        cur.execute(select_query, (device_id,))
        interfaces = cur.fetchall()

        if not interfaces:
            print(f"⚠️ No logical interfaces found for device '{device_name}'.")
            return []

        print(f"\n--- Logical Interfaces (IP Config) for Device: {device_name} ---")
        print("-" * 140)
        print(f"{'#ID':<8} | {'Interface Name':<20} | {'Unit':<6} | {'Parent':<15} | {'IPv4 Address':<30} | {'IPv6 Address':<30} | {'Admin':<7} | {'Oper':<7}")
        print("-" * 140)

        for iface in interfaces:
            int_id, name, unit, ipv4, ipv6, admin, oper, parent = iface
            print(
                f"{str(int_id)[:8]:<8} | {name:<20} | {unit:<6} | {parent or 'N/A':<15} | {ipv4 or 'N/A':<30} | {ipv6 or 'N/A':<30} | {admin:<7} | {oper:<7}"
            )
        print("-" * 140)

    except (Exception, Error) as error:
        handle_db_error(f"during fetching logical interfaces for device '{device_name}': {error}", conn)
    finally:
        handle_connection_close(conn)
    return interfaces

def update_logical_interface(
    device_name: str,
    original_interface_name: str, 
    new_interface_name: str = None, 
    new_unit_number: int = None,
    new_ipv4: str = None, 
    new_ipv6: str = None, 
    new_admin_status: str = None, 
    new_oper_status: str = None, 
    new_parent_name: str = None, 
    new_description: str = None
) -> bool:
    """
    Updates specified fields for a logical interface.
    """
    device_id = get_device_id_by_name(device_name)
    if not device_id:
        print(f"❌ Logical Interface update failed: Device '{device_name}' not found.")
        return False
        
    conn = None
    updates = []
    params = []
    
    # Handle parent update (Port/LAG)
    if new_parent_name is not None:
        parent_port_id = get_port_id_by_name_and_device(new_parent_name, device_id)
        parent_lag_id = get_lag_id_by_name_and_device(new_parent_name, device_id)

        if not parent_port_id and not parent_lag_id:
            print(f"❌ Logical Interface update failed: New Parent '{new_parent_name}' (Port or LAG) not found.")
            return False
        if parent_port_id and parent_lag_id:
            print("❌ Logical Interface update failed: New Parent name is ambiguous (found both Port and LAG).")
            return False
        
        updates.append("parent_port_id = %s")
        updates.append("parent_lag_id = %s")
        params.extend([parent_port_id, parent_lag_id])
    
    if new_interface_name is not None:
        updates.append("full_interface_name = %s")
        params.append(new_interface_name)
    if new_unit_number is not None:
        updates.append("unit_number = %s")
        params.append(new_unit_number)
    if new_ipv4 is not None:
        updates.append("ipv4_address = %s")
        params.append(new_ipv4)
    if new_ipv6 is not None:
        updates.append("ipv6_address = %s")
        params.append(new_ipv6)
    if new_admin_status is not None:
        updates.append("admin_status = %s")
        params.append(new_admin_status)
    if new_oper_status is not None:
        updates.append("oper_status = %s")
        params.append(new_oper_status)
    if new_description is not None:
        updates.append("description = %s")
        params.append(new_description)

    if not updates:
        print("⚠️ No fields provided for logical interface update.")
        return False

    params.append(device_id)
    params.append(original_interface_name)
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        update_query = f"""
        UPDATE logical_interfaces
        SET {', '.join(updates)}
        WHERE device_id = %s AND full_interface_name = %s;
        """
        cur.execute(update_query, tuple(params))
        
        if cur.rowcount == 1:
            conn.commit()
            print(f"✅ Successfully updated Logical Interface '{original_interface_name}' on device '{device_name}'.")
            return True
        else:
            print(f"⚠️ Update failed: Logical Interface '{original_interface_name}' not found on device '{device_name}'.")
            return False

    except Error as e:
        if 'duplicate key value violates unique constraint' in str(e) and 'logical_interfaces_device_id_full_interface_name_key' in str(e):
             handle_db_error(f"Update failed: New Interface Name '{new_interface_name}' already exists on device '{device_name}'.", conn)
        else:
            handle_db_error(f"during Logical Interface update: {e}", conn)
        return False
    except Exception as e:
        handle_db_error(f"during Logical Interface update: {e}", conn)
        return False
    finally:
        handle_connection_close(conn)


def delete_logical_interface(device_name: str, full_interface_name: str) -> bool:
    """
    Deletes a logical interface record based on device name and full interface name.
    """
    device_id = get_device_id_by_name(device_name)
    if not device_id:
        print(f"❌ Logical Interface deletion failed: Device '{device_name}' not found.")
        return False

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        delete_query = "DELETE FROM logical_interfaces WHERE device_id = %s AND full_interface_name = %s;"
        cur.execute(delete_query, (device_id, full_interface_name))
        
        if cur.rowcount == 1:
            conn.commit()
            print(f"✅ Successfully deleted Logical Interface '{full_interface_name}' from device '{device_name}'.")
            return True
        else:
            print(f"⚠️ Deletion failed: Logical Interface '{full_interface_name}' not found on device '{device_name}'.")
            return False

    except (Exception, Error) as error:
        handle_db_error(f"during Logical Interface deletion: {error}", conn)
        return False
    finally:
        handle_connection_close(conn)

# -------------------------------------------------------------
# --- EXISTING CRUD OPERATIONS (DEVICES and HARDWARE) ---
# -------------------------------------------------------------
# NOTE: The content below this line is the existing code from the previous interaction.
# (Existing device and hardware CRUD functions are included here for completeness)

def create_device(
    device_name: str, 
    gw_shortname: str, 
    device_role: str, 
    device_status: str, 
    device_type: str = None, 
    availability_zone: str = None, 
    lifecycle_status: str = None, 
    device_model: str = None, 
    device_vendor: str = None, 
    health: int = None
) -> str | None:
    """
    Inserts a new device record into the 'devices' table.
    device_id is auto-generated by the database.
    """
    conn = None
    new_device_id = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        insert_query = """
        INSERT INTO devices (
            device_name, gw_shortname, device_role, device_status, 
            device_type, availability_zone, lifecycle_status, 
            device_model, device_vendor, health
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING device_id;
        """
        cur.execute(insert_query, (
            device_name, gw_shortname, device_role, device_status, 
            device_type, availability_zone, lifecycle_status, 
            device_model, device_vendor, health
        ))
        
        # Fetch the newly generated device_id
        new_device_id = cur.fetchone()[0]
        conn.commit()
        
        print(f"✅ Created device '{device_name}' (Role: {device_role}, Status: {device_status}) with ID: {str(new_device_id)[:8]}...")
        return str(new_device_id)

    except Error as e:
        # Catch unique constraint violations for device_name
        if 'duplicate key value violates unique constraint "devices_devicename_key"' in str(e):
            handle_db_error(f"Device creation failed: Device Name '{device_name}' already exists.", conn)
        else:
            handle_db_error(f"during device creation: {e}", conn)
        return None
    except Exception as e:
        handle_db_error(f"during device creation: {e}", conn)
        return None
    finally:
        handle_connection_close(conn)


def get_all_devices():
    """
    Retrieves and prints all records from the 'devices' table.
    """
    conn = None
    devices = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Removed 'created_at' from the selection
        select_query = """
        SELECT 
            device_id, device_name, gw_shortname, device_role, device_type, 
            availability_zone, lifecycle_status, device_status, device_model, 
            device_vendor, health
        FROM devices 
        ORDER BY device_name;
        """
        cur.execute(select_query)
        devices = cur.fetchall()
        
        if not devices:
            print("⚠️ No devices found in the database.")
            return []

        print("\n--- All Network Devices ---")
        print("-" * 150)
        # Displaying a subset of key fields for the list view
        print(f"{'#ID':<8} | {'Device Name':<15} | {'GW Shortname':<15} | {'Role':<10} | {'Type':<12} | {'Status':<10} | {'Vendor':<10} | {'Health':<6} | {'AZ':<10}")
        print("-" * 150)

        for device in devices:
            device_id, name, shortname, role, dev_type, az, lifecycle, status, model, vendor, health = device
            print(
                f"{str(device_id)[:8]:<8} | {name:<15} | {shortname:<15} | {role:<10} | {dev_type or 'N/A':<12} | {status:<10} | {vendor or 'N/A':<10} | {health or 'N/A':<6} | {az or 'N/A':<10}"
            )
            
        print("-" * 150)

    except (Exception, Error) as error:
        handle_db_error(f"during fetching all devices: {error}", conn)
    finally:
        handle_connection_close(conn)
    return devices


def get_device_by_name(device_name: str) -> dict | None:
    """
    Retrieves a single device record using the unique device_name.
    """
    conn = None
    device_info = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        select_query = """
        SELECT 
            device_id, device_name, gw_shortname, device_role, device_type, 
            availability_zone, lifecycle_status, device_status, device_model, 
            device_vendor, health
        FROM devices 
        WHERE device_name = %s;
        """
        cur.execute(select_query, (device_name,))
        result = cur.fetchone()
        
        if result:
            # Match the number of selected columns
            device_id, name, shortname, role, dev_type, az, lifecycle, status, model, vendor, health = result
            device_info = {
                'device_id': str(device_id),
                'device_name': name,
                'gw_shortname': shortname,
                'device_role': role,
                'device_type': dev_type,
                'availability_zone': az,
                'lifecycle_status': lifecycle,
                'device_status': status,
                'device_model': model,
                'device_vendor': vendor,
                'health': health,
            }
        
    except (Exception, Error) as error:
        handle_db_error(f"during fetching device by name: {error}", conn)
    finally:
        handle_connection_close(conn)
    return device_info


def update_device(
    original_name: str, 
    new_name: str = None, 
    new_shortname: str = None, 
    new_role: str = None, 
    new_type: str = None, 
    new_az: str = None,
    new_lifecycle: str = None,
    new_status: str = None,
    new_model: str = None,
    new_vendor: str = None,
    new_health: int = None
) -> bool:
    """
    Updates specified fields for the device record matching the original_name.
    """
    conn = None
    updates = []
    params = []
    
    if new_name is not None:
        updates.append("device_name = %s")
        params.append(new_name)
    if new_shortname is not None:
        updates.append("gw_shortname = %s")
        params.append(new_shortname)
    if new_role is not None:
        updates.append("device_role = %s")
        params.append(new_role)
    if new_type is not None:
        updates.append("device_type = %s")
        params.append(new_type)
    if new_az is not None:
        updates.append("availability_zone = %s")
        params.append(new_az)
    if new_lifecycle is not None:
        updates.append("lifecycle_status = %s")
        params.append(new_lifecycle)
    if new_status is not None:
        updates.append("device_status = %s")
        params.append(new_status)
    if new_model is not None:
        updates.append("device_model = %s")
        params.append(new_model)
    if new_vendor is not None:
        updates.append("device_vendor = %s")
        params.append(new_vendor)
    if new_health is not None:
        updates.append("health = %s")
        params.append(new_health)

    if not updates:
        print("⚠️ No fields provided for update.")
        return False

    params.append(original_name)
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        update_query = f"""
        UPDATE devices
        SET {', '.join(updates)}
        WHERE device_name = %s;
        """
        cur.execute(update_query, tuple(params))
        
        if cur.rowcount == 1:
            conn.commit()
            print(f"✅ Successfully updated device '{original_name}'.")
            return True
        else:
            print(f"⚠️ Update failed: Device '{original_name}' not found.")
            return False

    except Error as e:
        # Catch unique constraint violations
        if 'duplicate key value violates unique constraint "devices_devicename_key"' in str(e):
             handle_db_error(f"Update failed: New Device Name '{new_name}' already exists.", conn)
        else:
            handle_db_error(f"during device update: {e}", conn)
        return False
    except Exception as e:
        handle_db_error(f"during device update: {e}", conn)
        return False
    finally:
        handle_connection_close(conn)


def delete_device(device_name: str) -> bool:
    """
    Deletes a device record based on the unique device_name.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        delete_query = "DELETE FROM devices WHERE device_name = %s;"
        cur.execute(delete_query, (device_name,))
        
        if cur.rowcount == 1:
            conn.commit()
            print(f"✅ Successfully deleted device '{device_name}'.")
            return True
        else:
            print(f"⚠️ Deletion failed: Device '{device_name}' not found.")
            return False

    except (Exception, Error) as error:
        handle_db_error(f"during device deletion: {error}", conn)
        return False
    finally:
        handle_connection_close(conn)


def create_hardware_component(
    device_name: str, 
    component_type: str, 
    model_number: str, 
    manufacturer: str = None, 
    serial_number: str = None, 
    firmware_version: str = None, 
    health_status: str = None
) -> str | None:
    """Inserts a new hardware component record."""
    device_id = get_device_id_by_name(device_name)
    if not device_id:
        print(f"❌ Hardware creation failed: Device '{device_name}' not found.")
        return None

    conn = None
    new_hardware_id = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        insert_query = """
        INSERT INTO device_hardware (
            device_id, component_type, model_number, manufacturer, 
            serial_number, firmware_version, health_status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING hardware_id;
        """
        cur.execute(insert_query, (
            device_id, component_type, model_number, manufacturer, 
            serial_number, firmware_version, health_status
        ))
        
        new_hardware_id = cur.fetchone()[0]
        conn.commit()
        
        print(f"✅ Created hardware component '{component_type} ({model_number})' for device '{device_name}' with ID: {str(new_hardware_id)[:8]}...")
        return str(new_hardware_id)

    except Error as e:
        if 'duplicate key value violates unique constraint "device_hardware_serial_number_key"' in str(e):
            handle_db_error(f"Hardware creation failed: Serial Number '{serial_number}' already exists.", conn)
        else:
            handle_db_error(f"during hardware component creation: {e}", conn)
        return None
    except Exception as e:
        handle_db_error(f"during hardware component creation: {e}", conn)
        return None
    finally:
        handle_connection_close(conn)


def get_hardware_components_by_device_name(device_name: str):
    """Retrieves all hardware components for a given device name."""
    device_id = get_device_id_by_name(device_name)
    if not device_id:
        print(f"⚠️ Device '{device_name}' not found.")
        return []

    conn = None
    components = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        select_query = """
        SELECT 
            hardware_id, component_type, model_number, manufacturer, 
            serial_number, firmware_version, health_status
        FROM device_hardware 
        WHERE device_id = %s
        ORDER BY component_type, serial_number;
        """
        cur.execute(select_query, (device_id,))
        components = cur.fetchall()

        if not components:
            print(f"⚠️ No hardware components found for device '{device_name}'.")
            return []

        print(f"\n--- Hardware Components for Device: {device_name} ---")
        print("-" * 120)
        print(f"{'#ID':<8} | {'Component Type':<20} | {'Model Number':<20} | {'Manufacturer':<15} | {'Serial Number':<20} | {'Health':<10}")
        print("-" * 120)

        for component in components:
            hw_id, c_type, m_num, mfr, sn, fw_ver, health = component
            print(
                f"{str(hw_id)[:8]:<8} | {c_type:<20} | {m_num:<20} | {mfr or 'N/A':<15} | {sn or 'N/A':<20} | {health or 'N/A':<10}"
            )
        print("-" * 120)

    except (Exception, Error) as error:
        handle_db_error(f"during fetching hardware for device '{device_name}': {error}", conn)
    finally:
        handle_connection_close(conn)
    return components


def update_hardware_component(
    serial_number: str, 
    new_type: str = None, 
    new_model: str = None, 
    new_mfr: str = None, 
    new_fw: str = None, 
    new_health: str = None
) -> bool:
    """
    Updates specified fields for the hardware component matching the serial_number.
    """
    conn = None
    updates = []
    params = []
    
    if new_type is not None:
        updates.append("component_type = %s")
        params.append(new_type)
    if new_model is not None:
        updates.append("model_number = %s")
        params.append(new_model)
    if new_mfr is not None:
        updates.append("manufacturer = %s")
        params.append(new_mfr)
    if new_fw is not None:
        updates.append("firmware_version = %s")
        params.append(new_fw)
    if new_health is not None:
        updates.append("health_status = %s")
        params.append(new_health)

    if not updates:
        print("⚠️ No fields provided for hardware component update.")
        return False

    params.append(serial_number)
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        update_query = f"""
        UPDATE device_hardware
        SET {', '.join(updates)}
        WHERE serial_number = %s;
        """
        cur.execute(update_query, tuple(params))
        
        if cur.rowcount == 1:
            conn.commit()
            print(f"✅ Successfully updated hardware component with serial number '{serial_number}'.")
            return True
        else:
            print(f"⚠️ Update failed: Hardware component with serial number '{serial_number}' not found.")
            return False

    except (Exception, Error) as error:
        handle_db_error(f"during hardware component update: {error}", conn)
        return False
    finally:
        handle_connection_close(conn)


def delete_hardware_component(serial_number: str) -> bool:
    """
    Deletes a hardware component record based on the unique serial_number.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        delete_query = "DELETE FROM device_hardware WHERE serial_number = %s;"
        cur.execute(delete_query, (serial_number,))
        
        if cur.rowcount == 1:
            conn.commit()
            print(f"✅ Successfully deleted hardware component with serial number '{serial_number}'.")
            return True
        else:
            print(f"⚠️ Deletion failed: Hardware component with serial number '{serial_number}' not found.")
            return False

    except (Exception, Error) as error:
        handle_db_error(f"during hardware component deletion: {error}", conn)
        return False
    finally:
        handle_connection_close(conn)