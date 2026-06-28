# ./python/fast_mcp/mcp_resources.py

from typing import Dict, Any 
# No need to import mcp_app here anymore

# 1. DEFINE THE RESOURCE FUNCTION (MUST BE TOP-LEVEL)
def get_network_config() -> Dict[str, Any]:
    """Provides static lookup data for device roles, status codes, and locations."""
    return {
        "supported_roles": ["CORE", "SPINE", "LEAF", "ACCESS", "BORDER"],
        "lifecycle_statuses": ["Active", "Decommissioning", "Planned"],
        "health_status_codes": {
            1: "Green (Operational)",
            2: "Amber (Degraded)",
            3: "Red (Down/Critical)",
            4: "Unknown"
        }
    }

# 2. NEW REGISTRATION FUNCTION (MUST BE DEFINED AFTER THE RESOURCE)
# It takes mcp_app as an argument now.
def register_resources(mcp_app):
    """Manually registers the resource onto the mcp_app instance."""
    # This line now correctly sees the top-level function definition
    mcp_app.resource("config://network-data")(get_network_config)