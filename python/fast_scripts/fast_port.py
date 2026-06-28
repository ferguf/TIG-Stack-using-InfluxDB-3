import requests
import uuid
from tabulate import tabulate  # pip install tabulate

BASE_URL = "http://localhost:8000"

def get_device_name(device_name):
    """Fetch device_id by device_name."""
    resp = requests.get(f"{BASE_URL}/devices/{device_name}")
    if resp.status_code == 200:
        device = resp.json()
        return device.get("device_id")
    else:
        print("Error fetching device:", resp.status_code, resp.text)
        return None

def list_ports(device_name):
    """List all ports for a device in table format."""
    resp = requests.get(f"{BASE_URL}/ports/{device_name}")
    if resp.status_code == 200:
        ports = resp.json()
        if not ports:
            print("No ports found for device:", device_name)
            return
        table = [
            [
                port.get("port_name"),
                port.get("port_speed"),
                port.get("port_type"),
                port.get("port_service_status"),
            ]
            for port in ports
        ]
        print(tabulate(table, headers=["Port Name", "Speed", "Type", "Service Status"], tablefmt="grid"))
    else:
        print("Error:", resp.status_code, resp.text)

def create_port(device_name):
    """Create a new port for a device."""
    device_id = get_device_name(device_name)
    if not device_id:
        print("Device not found.")
        return

    payload = {
        "port_id": str(uuid.uuid4()),  # generate new UUID
        "device_id": device_id,
        "mac_address": input("MAC address: "),
        "port_name": input("Port name: "),
        "port_speed": input("Port speed (e.g., 100G): "),
        "port_description": input("Description: "),
        "port_optic": input("Optic type: "),
        "port_tagging": input("Tagging mode: "),
        "port_cktid": input("Circuit ID: "),
        "service_id": None,  # optional
        "port_service_status": input("Service status: "),
        "port_type": input("Port type (Physical, LAG, UNI, ENNI): "),
        "port_health_status": int(input("Health status code (1=Green, 2=Amber, 3=Red, 4=Unknown): "))
    }

    resp = requests.post(f"{BASE_URL}/ports/{device_name}", json=payload)
    if resp.status_code == 200:
        print("Created port successfully.")
        print(resp.json())
    else:
        print("Error:", resp.status_code, resp.text)

def update_port(device_name, port_name):
    """Update an existing port."""
    payload = {}
    print("Leave blank to skip updating a field.")
    new_speed = input("New port speed: ")
    if new_speed:
        payload["port_speed"] = new_speed
    new_status = input("New service status: ")
    if new_status:
        payload["port_service_status"] = new_status

    resp = requests.put(f"{BASE_URL}/ports/{device_name}/{port_name}", json=payload)
    if resp.status_code == 200:
        print("Updated port successfully.")
        print(resp.json())
    else:
        print("Error:", resp.status_code, resp.text)

def delete_port(device_name, port_name):
    """Delete a port."""
    resp = requests.delete(f"{BASE_URL}/ports/{device_name}/{port_name}")
    if resp.status_code == 200:
        print("Deleted port successfully.")
    else:
        print("Error:", resp.status_code, resp.text)

def menu():
    """Interactive menu for port management."""
    while True:
        print("\nPort Management Menu")
        print("1. List ports for a device")
        print("2. Create a new port")
        print("3. Update a port")
        print("4. Delete a port")
        print("5. Exit")

        choice = input("Enter choice: ")
        if choice == "1":
            device = input("Device name: ")
            list_ports(device)
        elif choice == "2":
            device = input("Device name: ")
            create_port(device)
        elif choice == "3":
            device = input("Device name: ")
            port = input("Port name: ")
            update_port(device, port)
        elif choice == "4":
            device = input("Device name: ")
            port = input("Port name: ")
            delete_port(device, port)
        elif choice == "5":
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    menu()