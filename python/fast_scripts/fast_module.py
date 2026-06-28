# fast_module.py
import requests
from tabulate import tabulate
from typing import Any, Callable, Dict, List, Optional

BASE_URL = "http://localhost:8000"


def get_customers():
    url = f"{BASE_URL}/customers/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Normalize: wrap dict in list if needed
        if isinstance(data, dict):
            customers = [data]
        elif isinstance(data, list):
            customers = data
        else:
            customers = []

        if not customers:
            print("No customers found.")
            return []

        headers = ["Account ID", "Customer Name", "Customer ID"]
        rows = [
            [cust.get("account_id"), cust.get("customer_name"), cust.get("customer_id")]
            for cust in customers
        ]

        print("\n✅ Customers retrieved successfully:\n")
        print(tabulate(rows, headers=headers, tablefmt="grid"))

        return customers

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching customers: {e}")
        return []

def show_customer(customer_id: str):
    """Fetch and display details for a specific customer."""
    try:
        response = requests.get(f"{BASE_URL}/customers/{customer_id}")
        response.raise_for_status()
        customer = response.json()
        print("\nCustomer Details:")
        print(f"Name: {customer.get('customer_name')}")
        print(f"Account ID: {customer.get('account_id')}")
        print(f"Customer ID: {customer.get('customer_id')}")
        return customer
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching customer {customer_id}: {e}")
        return None

# ----------------------------
# Core getters (lists)
# ----------------------------

def get_devices() -> List[Dict[str, Any]]:
    """Return all devices."""
    try:
        resp = requests.get(f"{BASE_URL}/devices/")
        resp.raise_for_status()
        devices = resp.json() or []
        return devices
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching devices: {e}")
        return []

def get_ports(device_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    If device_name is provided, return ports for that device.
    """
    try:
        url = f"{BASE_URL}/ports/device/{device_name}"
        resp = requests.get(url)
        resp.raise_for_status()
        ports = resp.json() or []
        return ports
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching ports: {e}")
        return []

def get_fabric_services() -> List[Dict[str, Any]]:
    """Return all fabric connections."""
    try:
        resp = requests.get(f"{BASE_URL}/fabric_services/")
        resp.raise_for_status()
        connections = resp.json() or []
        return connections
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching fabric services: {e}")
        return []
    
def get_fabric_services_by_customer(customer_id: str) -> List[Dict[str, Any]]:
    """
    Return all fabric services for a given customer_id.

    - customer_id: UUID string of the customer
    - returns: List of fabric service objects (empty list if none found)
    - example:
      GET /fabric_services/customer/{customer_id}
      → [
        {"service_id":"uuid","name":"ServiceA","description":"Customer-specific service"},
        {"service_id":"uuid","name":"ServiceB","description":"Another customer service"}
      ]
    """
    try:
        resp = requests.get(f"{BASE_URL}/fabric_services/customer/{customer_id}")
        resp.raise_for_status()
        services = resp.json() or []
        return services
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching fabric services for customer {customer_id}: {e}")
        return []

def get_fabric_connection_by_service(service_id: str) -> List[Dict[str, Any]]:
    """
    Return all fabric connections for a given service_id.

    - service_id: UUID string of the Fabric Service
    - returns: List of fabric connection objects (empty list if none found)
    - example:
      GET /fabric_connections/service/{service_id}
      → [
        {"connection_id":"uuid","connection_status":"assigned","port_a_id":"uuid","port_b_id":"uuid"},
        {"connection_id":"uuid","connection_status":"configured","port_a_id":"uuid","port_b_id":"uuid"}
      ]
    """
    try:
        resp = requests.get(f"{BASE_URL}/fabric_connections/service/{service_id}")
        resp.raise_for_status()
        connections = resp.json() or []
        return connections
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching fabric connections for service {service_id}: {e}")
        return []


def get_fabric_connections() -> List[Dict[str, Any]]:
    """Return all fabric connections."""
    try:
        resp = requests.get(f"{BASE_URL}/fabric_connections/")
        resp.raise_for_status()
        connections = resp.json() or []
        return connections
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching fabric connections: {e}")
        return []

# ----------------------------
# Device helpers
# ----------------------------

def get_device(device_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetch device details by device_name.
    Returns dict with attributes or None on error/not found.
    """
    try:
        resp = requests.get(f"{BASE_URL}/devices/{device_name}")
        if resp.status_code == 404:
            print(f"ℹ️ Device not found: {device_name}")
            return None
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching device {device_name}: {e}")
        return None

def get_device_name(device_name: str) -> Optional[str]:
    """
    Fetch device_id by device_name.
    Returns device_id or None.
    """
    device = get_device(device_name)
    return device.get("device_id") if device else None

# ----------------------------
# Port UI helpers
# ----------------------------

def list_ports(device_name: str) -> List[Dict[str, Any]]:
    """
    Print a tabulated summary of ports for a device.
    Returns the raw list of port dicts.
    """
    ports = get_ports(device_name)
    if not ports:
        print(f"No ports found for device: {device_name}")
        return []

    rows = [
        [
            p.get("port_name"),
            p.get("port_speed"),
            p.get("port_type"),
            p.get("port_service_status"),
        ]
        for p in ports
    ]
    print(tabulate(rows, headers=["Port Name", "Speed", "Type", "Service Status"], tablefmt="grid"))
    return ports

def update_port_by_id(port_id: str, fields: dict) -> dict:
    """
    Update a port by its ID using the FastAPI endpoint.

    Args:
        port_id (str): UUID of the port to update.
        fields (dict): Dictionary of fields to update. Must match backend schema.

    Returns:
        dict: The updated port object from the API, or {} on error.
    """
    url = f"{BASE_URL}/ports/id/{port_id}"
    headers = {"accept": "application/json", "Content-Type": "application/json"}

    try:
        response = requests.put(url, json=fields, headers=headers)
        response.raise_for_status()
        updated = response.json()
        print(f"✅ Port {updated.get('port_name')} updated successfully.")
        return updated
    except requests.exceptions.RequestException as e:
        print(f"❌ Error updating port {port_id}: {e}")
        return {}

def update_port(device_name: str, port_name: str) -> Optional[Dict[str, Any]]:
    """
    Interactively update an existing port's speed and service status.
    Returns the updated port dict or None on error.
    """
    payload: Dict[str, Any] = {}
    print("Leave blank to skip updating a field.")
    new_speed = input("New port speed: ").strip()
    if new_speed:
        payload["port_speed"] = new_speed
    new_status = input("New service status: ").strip()
    if new_status:
        payload["port_service_status"] = new_status

    try:
        resp = requests.put(f"{BASE_URL}/ports/{device_name}/{port_name}", json=payload)
        resp.raise_for_status()
        updated = resp.json()
        print("✅ Updated port successfully.")
        return updated
    except requests.exceptions.RequestException as e:
        print(f"❌ Error updating port {port_name} on {device_name}: {e}")
        return None

# ----------------------------
# Generalized table selector
# ----------------------------

def select_table(
    items: List[Dict[str, Any]],
    headers: List[str],
    row_builder: Callable[[Dict[str, Any], int], List[Any]],
    id_key: str,
    label: str = "Items",
) -> Optional[Any]:
    """
    Generalized table selector.

    - items: list of dicts
    - headers: column headers
    - row_builder: function(item, idx) -> row list
    - id_key: key to return from selected item
    - label: display label (plural), e.g. "Customers", "Services"

    Returns the selected item's id (any type) or None.
    """
    if not items:
        print(f"No {label.lower()} found.")
        return None

    rows = [row_builder(item, idx) for idx, item in enumerate(items, start=1)]
    print(f"\nAvailable {label}:\n")
    print(tabulate(rows, headers=headers, tablefmt="grid"))

    try:
        singular = label[:-1] if label.endswith("s") else label
        choice = int(input(f"\nSelect a {singular} by number: ").strip())
        if not (1 <= choice <= len(items)):
            print("❌ Invalid selection.")
            return None
        selected = items[choice - 1]
        selected_id = selected.get(id_key)
        print(f"\n➡️ Selected {singular}: {selected_id}")
        return selected_id
    except ValueError:
        print("❌ Please enter a valid number.")
        return None

# ----------------------------
# Entity selectors using select_table
# ----------------------------

def select_customer() -> Optional[str]:
    """Present customers in a table and return chosen customer_id."""
    customers = get_customers()  # if you have a dedicated get_customers(), use that
    return select_table(
        customers,
        headers=["#", "Customer Name", "Account ID", "Customer ID"],
        row_builder=lambda cust, idx: [
            idx,
            cust.get("customer_name"),
            cust.get("account_id"),
            cust.get("customer_id"),
        ],
        id_key="customer_id",
        label="Customers",
    )

def select_service(customer_id: Optional[str] = None) -> Optional[Dict[str, str]]:
    """
    Present fabric services for a customer (if customer_id is given)
    or all services (if no customer_id is provided).
    Returns the chosen service_id and service_type.
    """
    if customer_id:
        services = get_fabric_services_by_customer(customer_id)
    else:
        services = get_fabric_services()

    if not services:
        scope = f"customer {customer_id}" if customer_id else "system"
        print(f"❌ No fabric services available for {scope}.")
        return None

    selected_id = select_table(
        services,
        headers=["#", "Service Type", "Service ID", "Status"],
        row_builder=lambda fs, idx: [
            idx,
            fs.get("service_type", "N/A"),
            fs.get("service_id", "N/A"),
            fs.get("service_status", "N/A"),
        ],
        id_key="service_id",
        label="Fabric Services",
    )

    if selected_id:
        fs = next((s for s in services if s.get("service_id") == selected_id), None)
        if fs:
            return {
                "service_id": fs.get("service_id"),
                "service_type": fs.get("service_type"),
            }

    return None



def select_connection() -> Optional[str]:
    """Present fabric connections in a table and return chosen connection_id."""
    connections = get_fabric_connections()
    return select_table(
        connections,
        headers=["#", "Connection Name", "Service ID", "Connection ID", "Status"],
        row_builder=lambda conn, idx: [
            idx,
            conn.get("connection_name"),
            conn.get("service_id"),
            conn.get("connection_id"),
            conn.get("connection_status"),
        ],
        id_key="connection_id",
        label="Connections",
    )

def select_device():
    devices = get_devices()
    if not devices:
        return None, None
    headers = ["#", "Device Name", "Device ID", "Role", "Model"]
    rows = [
        [idx, dev.get("device_name"), dev.get("device_id"), dev.get("device_role"), dev.get("device_model")]
        for idx, dev in enumerate(devices, start=1)
    ]
    print("\nAvailable Devices:\n")
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    choice = int(input("\nSelect a Device by number: ").strip())
    selected = devices[choice - 1]
    return selected.get("device_id"), selected.get("device_name")

def select_port(device_name: str) -> Optional[str]:
    """Present ports for a device in a table and return chosen port_id."""
    ports = get_ports(device_name)
    return select_table(
        ports,
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
    
    
    def update_fabric_connection(connection_id: str, **kwargs) -> dict:
        """
        Update a Fabric Connection by ID.

        Args:
            connection_id (str): The UUID of the Fabric Connection.
            kwargs: Fields to update (e.g., connection_name, connection_status, port_a_id, port_b_id, service_bw).

        Returns:
            dict: The updated Fabric Connection object from the API.
        """
    url = f"{BASE_URL}/{connection_id}"
    headers = {"accept": "application/json", "Content-Type": "application/json"}

    payload = {k: v for k, v in kwargs.items() if v is not None}

    response = requests.put(url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to update Fabric Connection {connection_id}: {response.status_code} {response.text}")
