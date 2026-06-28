# ./python/fast_mcp/loader.py

# CRITICAL: This file MUST NOT have any top-level imports from your own package

# FIX: Accept the mcp_app instance as an argument
def load_all_mcp_tools(mcp_app):
    """
    Forces Python to load and register all tool and resource modules 
    by passing them the locally created mcp_app instance.
    """
    
    # CRITICAL: Import inside the function to delay execution and break the cycle.
    from . import mcp_devices 
    from . import mcp_resources 
    
    # 1. Register Resources
    mcp_resources.register_resources(mcp_app) # Pass mcp_app
    
    # 2. Register Tools
    mcp_devices.register_device_tools(mcp_app) # Pass mcp_app
    
    return True