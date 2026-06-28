import requests
import csv
import os
from tabulate import tabulate
import subprocess

BASE_URL = "http://localhost:8000"

# centralize CSV directory

CSV_DIR = os.path.join("python", "templates", "base")

def get_devices():
    """Retrieve all devices and display them in a table with extended fields."""
    url = f"{BASE_URL}/devices/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        devices = response.json()

        if not devices:
            print("No devices found.")
            return

        headers = ["Device Name", "Device", "Device Role", "Device Model", "Created At"]
        rows = [
            [
                dev.get("device_name"),
                dev.get("device"),
                dev.get("device_role"),
                dev.get("device_model"),
                dev.get("created_at"),
            ]
            for dev in devices
        ]

        print("\n✅ Devices retrieved successfully:\n")
        print(tabulate(rows, headers=headers, tablefmt="grid"))

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching devices: {e}")


def create_device(
    device_name: str,
    location: str,
    device_role: str,
    device_vendor: str,
    device_model: str = None,
    serial_number: str = None,
    availability_zone: str = None,
    lifecycle_status: str = "Active",
    planning_status: str = "Planned",
    health_status: int = 4,
    device_description: str = None,
):
    """Create a new device with all required fields and then call fast_load_device."""
    url = f"{BASE_URL}/devices/"
    payload = {
        "device_name": device_name,
        "location": location,
        "device_role": device_role,
        "device_vendor": device_vendor,
        "device_model": device_model,
        "serial_number": serial_number,
        "availability_zone": availability_zone,
        "lifecycle_status": lifecycle_status,
        "planning_status": planning_status,
        "health_status": health_status,
        "device_description": device_description,
    }
    try:
        print(f"➡️ Sending payload: {payload}")
        response = requests.post(url, json=payload, headers={"accept": "application/json"})
        response.raise_for_status()
        created = response.json()
        print(f"✅ Added device {created.get('device_name')} (Vendor: {created.get('device_vendor')})")

        # Call fast_load_device script with the device_name
        try:
            print(f"➡️ Calling fast_load_device for {device_name}...")
            subprocess.run(
                ["python", "python/fast_scripts/fast_port_load.py", device_name],
                check=True
            )
            print(f"✅ fast_load_device executed successfully for {device_name}")
        except subprocess.CalledProcessError as e:
            print(f"❌ fast_load_device failed for {device_name}: {e}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating device {device_name}: {e}")


def delete_device_by_name(device_name: str):
    """Delete a device by its name."""
    url = f"{BASE_URL}/devices/{device_name}"
    try:
        response = requests.delete(url, headers={"accept": "application/json"})
        if response.status_code == 200:
            print(f"✅ Deleted device: {device_name}")
        else:
            print(f"❌ Failed to delete device {device_name}: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error deleting device {device_name}: {e}")

def process_csv(filename="devices.csv"):
    """Process devices from a CSV file with actions add/delete."""
    file_path = os.path.join(CSV_DIR, filename)
    print(f"\n📂 Processing CSV file: {file_path}\n")
    try:
        with open(file_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                action = (row.get("action") or "").strip().lower()

                # Required fields
                required_fields = ["device_name", "location", "device_role", "device_vendor"]
                missing = [f for f in required_fields if not row.get(f)]
                if missing:
                    print(f"❌ Row failed: missing required fields {missing}")
                    continue  # skip this row

                device_name = row["device_name"].strip()
                location = row["location"].strip()
                device_role = row["device_role"].strip()
                device_vendor = row["device_vendor"].strip()

                # Optional fields
                device_model = (row.get("device_model") or "").strip() or None
                serial_number = (row.get("serial_number") or "").strip() or None
                availability_zone = (row.get("availability_zone") or "").strip() or None
                lifecycle_status = (row.get("lifecycle_status") or "").strip() or "Active"
                planning_status = (row.get("planning_status") or "").strip() or "Planned"
                health_status = (row.get("health_status") or "").strip() or 4
                device_description = (row.get("device_description") or "").strip() or None

                try:
                    health_status = int(health_status)
                except ValueError:
                    health_status = 4

                if action == "add":
                    create_device(
                        device_name, location, device_role, device_vendor,
                        device_model, serial_number, availability_zone,
                        lifecycle_status, planning_status, health_status, device_description
                    )
                elif action == "delete":
                    delete_device_by_name(device_name)
                else:
                    print(f"⚠️ Unknown action '{action}' for device {device_name}")
    except Exception as e:
        print(f"❌ Error processing CSV: {e}")

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

def main_menu():
    """Interactive menu for device operations."""
    print("\n🚀 Starting FastAPI Device Client...\n")
    while True:
        print("\n=== FastAPI Device Client ===")
        print("1. Get all devices")
        print("2. Create a new device")
        print("3. Delete a device by name")
        print("4. Process devices from CSV (in python/templates/roles)")
        print("0. Exit")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            get_devices()
        elif choice == "2":
            device_name = input("Enter Device Name: ").strip()
            location = input("Enter Location: ").strip()
            device_role = input("Enter Device Role: ").strip()
            device_vendor = input("Enter Device Vendor: ").strip()
            device_model = input("Enter Device Model (optional): ").strip() or None
            serial_number = input("Enter Serial Number (optional): ").strip() or None
            availability_zone = input("Enter Availability Zone (optional): ").strip() or None
            lifecycle_status = input("Enter Lifecycle Status [default Active]: ").strip() or "Active"
            planning_status = input("Enter Planning Status [default Planned]: ").strip() or "Planned"
            health_status = input("Enter Health Status [default 4]: ").strip() or 4
            device_description = input("Enter Device Description (optional): ").strip() or None

            try:
                health_status = int(health_status)
            except ValueError:
                health_status = 4

            create_device(
                device_name, location, device_role, device_vendor,
                device_model, serial_number, availability_zone,
                lifecycle_status, planning_status, health_status, device_description
            )
        elif choice == "3":
            device_name = input("Enter Device Name to delete: ").strip()
            delete_device_by_name(device_name)
        elif choice == "4":
            filename = input("Enter CSV filename (default devices.csv): ").strip() or "devices.csv"
            process_csv(filename)
        elif choice == "0":
            print("Exiting...")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    try:
        main_menu()
    except Exception as e:
        print(f"❌ Script crashed: {e}")