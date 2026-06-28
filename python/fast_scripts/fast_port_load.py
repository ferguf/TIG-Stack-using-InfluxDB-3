import requests
import uuid
import csv
import os
import sys
from tabulate import tabulate  # pip install tabulate

BASE_URL = "http://localhost:8000"
CSV_DIR = os.path.join("python", "templates","roles")

def get_device(device_name):
    """Fetch device details (id, role, model) by device_name."""
    resp = requests.get(f"{BASE_URL}/devices/{device_name}")
    if resp.status_code == 200:
        device = resp.json()
        return {
            "device_id": device.get("device_id"),
            "role": device.get("device_role"),
            "model": device.get("device_model"),
        }
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

def create_ports_from_csv(device_name):
    """Create new ports for a device using its role+model CSV file."""
    device = get_device(device_name)
    if not device or not device["device_id"]:
        print("Device not found.")
        return

    role = (device["role"] or "").lower()
    model = (device["model"] or "").lower()
    csv_filename = f"{role}_{model}.csv"
    csv_path = os.path.join(CSV_DIR, csv_filename)

    if not os.path.exists(csv_path):
        print(f"CSV file not found for role/model: {csv_path}")
        return

    print(f"Using CSV: {csv_path}")

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            payload = {
                "port_id": str(uuid.uuid4()),
                "device_id": device["device_id"],
                "mac_address": None,
                "port_name": row["port_name"],
                "port_speed": row["port_speed"],
                "port_description": row["port_description"],
                "port_optic": row["port_optic"],
                "port_tagging": row["port_tagging"],
                "port_cktid": row["port_cktid"],
                "service_id": None,
                "port_service_status": row["port_service_status"],
                "port_type": row["port_type"],
                "port_health_status": int(row["port_health_status"]),
            }

            resp = requests.post(f"{BASE_URL}/ports/{device_name}", json=payload)
            if resp.status_code == 200:
                print(f"Created port {row['port_name']} successfully.")
            else:
                print(f"Error creating port {row['port_name']}: {resp.status_code} {resp.text}")

def menu():
    """Interactive menu for port management."""
    while True:
        print("\nPort Management Menu")
        print("1. List ports for a device")
        print("2. Create new ports from role+model CSV")
        print("3. Exit")

        choice = input("Enter choice: ")
        if choice == "1":
            device = input("Device name: ")
            list_ports(device)
        elif choice == "2":
            device = input("Device name: ")
            create_ports_from_csv(device)
        elif choice == "3":
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # device name passed as command-line argument
        device_name = sys.argv[1]
        create_ports_from_csv(device_name)
    else:
        # no argument, show menu
        menu()