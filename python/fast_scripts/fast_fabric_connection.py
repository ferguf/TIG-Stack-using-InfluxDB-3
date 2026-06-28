import requests
import json
import python.fast_scripts.fast_service as fast_service 
from uuid import uuid4
from tabulate import tabulate
from fast_customer import get_customers
from fast_module import (
    get_fabric_services_by_customer,
    get_fabric_connection_by_service,
    get_devices,
    get_ports,
    select_customer,
    select_service,
    select_device,
    select_port,
    update_port_by_id,
    select_table
)



BASE_URL = "http://localhost:8000"

def main():
    customers = get_customers()
    if customers:
        # Access full attributes programmatically
        for cust in customers:
            print(f"Customer ID: {cust.get('customer_id')}, "
                  f"Account ID: {cust.get('account_id')}, "
                  f"Name: {cust.get('customer_name')}")
    else:
        print("No customers available.")


def get_fabric_service():
    """Retrieve all fabric services for selection."""
    url = f"{BASE_URL}/fabric_services/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:5
6

def get_fabric_connections():
    """Retrieve all fabric connections and display them."""
    url = f"{BASE_URL}/fabric_connections/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        connections = response.json()

        if not connections:
            print("No fabric connections found.")
            return

        headers = ["Connection ID", "Service ID", "Connection Name", "Status"]
        rows = [
            [
                conn.get("connection_id"),
                conn.get("service_id"),
                conn.get("connection_name"),
                conn.get("connection_status"),
            ]
            for conn in connections
        ]

        print("\n✅ Fabric connections retrieved successfully:\n")
        print(tabulate(rows, headers=headers, tablefmt="grid"))

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching connections: {e}")

def create_fabric_connection():
    """Create a new fabric connection tied to a service."""

    # Step 1: Select Customer
    customer_id = select_customer()
    if not customer_id:
        print("❌ Cannot create connection without a valid customer.")
        return

    # Step 2: Select Service (returns dict with service_id and service_type)
    service = select_service(customer_id)
    if not service:
        print("❌ Cannot create connection without a valid service.")
        return

    service_id = service["service_id"]
    service_type = service["service_type"]

    # Step 3: Rule enforcement — check existing connections
    url = f"{BASE_URL}/fabric_connections/service/{service_id}"
    try:
        existing = requests.get(url, headers={"accept": "application/json"})
        existing.raise_for_status()
        connections = existing.json() or []
    except requests.exceptions.RequestException as e:
        print(f"❌ Error checking existing connections: {e}")
        return

    if service_type == "Eline EPL" and connections:
        print("❌ Eline EPL services can only have one connection.")
        return

    # Step 4: Gather connection details
    connection_id = str(uuid4())
    connection_name = input("Enter Connection Name: ").strip()

    # Defaults
    payload = {
        "connection_id": connection_id,
        "service_id": service_id,
        "connection_name": connection_name,
        "connection_status": "assigned",
        "health_status": 4,
        "c_vlan_list": "not configured",
    }

    # Step 5: Create connection
    print(f"\n➡️ Sending payload: {json.dumps(payload, indent=2)}")
    try:
        response = requests.post(
            f"{BASE_URL}/fabric_connections/",
            json=payload,
            headers={"accept": "application/json"},
        )
        response.raise_for_status()
        created = response.json()
        print(f"\n✅ Added fabric connection {created.get('connection_name')} "
              f"(ID: {created.get('connection_id')})")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating fabric connection: {e}")

def update_fabric_connection(connection_id: str, **updates):
    """Update an existing fabric connection."""
    url = f"{BASE_URL}/fabric_connections/{connection_id}"
    payload = {k: v for k, v in updates.items() if v is not None}
    try:
        print(f"➡️ Updating connection {connection_id} with {payload}")
        response = requests.put(url, json=payload, headers={"accept": "application/json"})
        response.raise_for_status()
        updated = response.json()
        print(f"✅ Updated fabric connection {updated.get('connection_name')} (ID: {updated.get('connection_id')})")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error updating connection {connection_id}: {e}")

def delete_fabric_connection(connection_id: str):
    """Delete a fabric connection by ID."""
    url = f"{BASE_URL}/fabric_connections/{connection_id}"
    try:
        response = requests.delete(url, headers={"accept": "application/json"})
        if response.status_code == 200:
            print(f"✅ Deleted fabric connection: {connection_id}")
        else:
            print(f"❌ Failed to delete connection {connection_id}: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error deleting connection {connection_id}: {e}")

def assign_port_to_service():
    """
    Interactive workflow to assign a port to a fabric service.
    Uses fast_module helpers and update_port_by_id for consistency.
    """

    # Step 1: Select a fabric service
    service_id = select_service()
    if not service_id:
        print("❌ No service selected.")
        return

    # Step 2: Select a device
    device_id, device_name = select_device()  # modified select_device returns both
    if not device_id:
        print("❌ No device selected.")
        return

    # Step 3: Select an eligible port
    ports = get_ports(device_name)
    eligible = [
        p for p in ports
        if p.get("port_type") == "Physical"
        and p.get("port_service_status") in {"Staged", "available", "ready for use"}
    ]
    if not eligible:
        print("No eligible ports found for this device.")
        return

    port_id = select_table(
        eligible,
        headers=["#", "Port Name", "Speed", "Type", "Service Status", "Port ID"],
        row_builder=lambda port, idx: [
            idx,
            port.get("port_name"),
            port.get("port_speed"),
            port.get("port_type"),
            port.get("port_service_status"),
            port.get("port_id"),
        ],
        id_key="port_id",
        label="Ports",
    )
    if not port_id:
        print("❌ No port selected.")
        return

    # Step 4: Update port assignment using update_port_by_id
    payload = {
        "service_id": service_id,          # UUID string only
        "port_service_status": "Assigned",
        "port_type": "Fabric Port",
    }

    updated = update_port_by_id(port_id, payload)
    if updated:
        print(f"\n✅ Port {updated.get('port_name')} assigned to service {service_id}.")
    else:
        print(f"❌ Failed to assign port {port_id} to service {service_id}.")

def attach_port_to_connection():
    """
    Attach Fabric Ports (FPs) to a Fabric Connection (FC).
    Logic varies by Fabric Service (FS) type.
    Currently implemented: Eline EPL.
    """

    # Step 1: Select Customer
    customer_id = select_customer()
    if not customer_id:
        return

    # Step 2: Select Fabric Service (FS)
    service_id = select_service(customer_id)
    if not service_id:
        print("❌ No service selected.")
        return

    # # Fetch the full service object so we can inspect service_type
    # services = get_fabric_services_by_customer(customer_id)
    # fs = next((s for s in services if s["service_id"] == service_id), None)
    # if not fs:
    #     print("❌ Could not retrieve service details.")
    #     return

    # Step 3: Select Fabric Connection (FC) with status=assigned
    connections = [
        fc for fc in get_fabric_connection_by_service(service_id)
        if fc["connection_status"] == "assigned"
    ]
    if not connections:
        print("No assigned Fabric Connections available.")
        return

    print("\nAvailable Fabric Connections:")
    for idx, fc in enumerate(connections, 1):
        print(f"{idx}. {fc['id']} (status: {fc['connection_status']})")

    fc_choice = int(input("Select Fabric Connection: ").strip())
    fc = connections[fc_choice - 1]

    # Step 4: Select Ports with status=assigned
    ports = [
        p for p in get_ports(service_id)
        if p["port_status"] == "assigned"
    ]
    if len(ports) < 2:
        print("❌ Need at least 2 assigned ports for EPL.")
        return

    print("\nAvailable Ports:")
    for idx, p in enumerate(ports, 1):
        print(f"{idx}. Port {p['id']} (speed: {p['port_speed']})")

    port_a_choice = int(input("Select Port A: ").strip())
    port_b_choice = int(input("Select Port B: ").strip())
    port_a = ports[port_a_choice - 1]
    port_b = ports[port_b_choice - 1]

    # Step 5: EPL logic — single FC between 2 FPs
    if fs["service_type"].lower() == "eline epl":
        # Update FC
        fc["connection_status"] = "configured"
        fc["port_a_id"] = port_a["id"]
        fc["port_b_id"] = port_b["id"]
        fc["service_bw"] = min(port_a["port_speed"], port_b["port_speed"])

        update_fabric_connection(fc["id"], **fc)

        # Update Ports
        for port in (port_a, port_b):
            port["port_service_status"] = "configured"
            port["port_health_status"] = 2
            port["port_tagging"] = "All2One"
            update_port(port["id"], **port)

        print(f"\n✅ EPL Connection {fc['id']} configured between Port {port_a['id']} and Port {port_b['id']}.")

def main_menu():
    while True:
        print("\n=== FastAPI Fabric Connection Client ===")
        print("1. Get all fabric connections")
        print("2. Create a new fabric connection")
        print("3. Update a fabric connection")
        print("4. Delete a fabric connection")
        print("5. Assign a port to a fabric service")
        print("6. Attach a fabric port to a fabric connection")
        print("0. Exit")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            get_fabric_connections()
        elif choice == "2":
            create_fabric_connection()
        elif choice == "3":
            conn_id = input("Enter Connection ID to update: ").strip()
            conn_name = input("Enter new Connection Name (blank to skip): ").strip() or None
            conn_status = input("Enter new Connection Status (blank to skip): ").strip() or None
            update_fabric_connection(conn_id, connection_name=conn_name, connection_status=conn_status)
        elif choice == "4":
            conn_id = input("Enter Connection ID to delete: ").strip()
            delete_fabric_connection(conn_id)
        elif choice == "5":
            assign_port_to_service()
        elif choice == "6":
            attach_port_to_connection()
        elif choice == "0":
            print("Exiting...")
            break
        else:
            print("Invalid choice, please try again.")


if __name__ == "__main__":
    main_menu()