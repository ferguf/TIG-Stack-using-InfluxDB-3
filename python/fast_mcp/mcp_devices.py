from fastmcp import FastMCP
from sqlalchemy.orm import Session
from scripts import api_operation
from scripts.api_session import get_db, get_db_session
from scripts.api_schema import DeviceIn

def register_device_tools(mcp: FastMCP):  # <--- Use this name

    @mcp.tool(name="list_network_inventory")
    def list_devices() -> str:
        """
        Retrieves a summary of all devices in the network inventory.
        Useful for getting an overview of the digital twin's current state.
        """
        devices = api_operation.get_devices()
        if not devices:
            return "No devices found in the inventory."
        
        output = ["### Current Network Inventory:"]
        for d in devices:
            output.append(f"- **{d.device_name}** | Vendor: {d.device_vendor} | Status: {d.health_status}")
        
        return "\n".join(output)

    @mcp.tool(name="inspect_device")
    def get_device(device_name: str) -> str:
        """
        Retrieves full technical specifications for a specific device by name.
        Use this to check location, model, and lifecycle status.
        """
        # Note: Your api_operation filters by device_name internally
        device = api_operation.get_device_by_id(device_name)
        if not device:
            return f"Error: Device '{device_name}' not found."
        
        return (
            f"## Device Details: {device.device_name}\n"
            f"- **ID:** {device.device_id}\n"
            f"- **Hardware:** {device.device_vendor} {device.device_model}\n"
            f"- **Location:** {device.location} (Zone: {device.availability_zone})\n"
            f"- **Status:** Health is {device.health_status}, Lifecycle is {device.lifecycle_status}\n"
            f"- **Description:** {device.device_description or 'No description provided.'}"
        )

    @mcp.tool(name="register_new_device")
    def register_device(
        device_name: str, 
        device_vendor: str, 
        device_model: str, 
        location: str,
        device_role: str = "ACCESS"
    ) -> str:
        """
        Adds a new piece of hardware to the digital twin inventory.
        Default role is ACCESS if not specified.
        """
        # Mapping MCP inputs to your Pydantic Schema
        new_device_data = DeviceIn(
            device_name=device_name,
            device_vendor=device_vendor,
            device_model=device_model,
            location=location,
            device_role=device_role,
            health_status="Healthy",   # Initializing as Healthy
            lifecycle_status="Active",  # Initializing as Active
            planning_status="Planned"
        )

        try:
            # We open a manual session here because api_operation.post_device 
            # requires a db Session object passed in.
            with get_db_session() as db:
                result = api_operation.post_device(db, new_device_data)
                return f"Successfully registered {result.device_name} (ID: {result.device_id})."
        except Exception as e:
            return f"Failed to register device: {str(e)}"