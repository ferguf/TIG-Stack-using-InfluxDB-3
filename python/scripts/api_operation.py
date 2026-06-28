"""
api_operation.py
Manager file for Galileo database operations.
Orchestrates high-level database interaction methods by aggregating 
specialized domain modules into a single importable namespace.
"""

import logging
import sys
import os

# Ensure the logger is configured for the namespace
logger = logging.getLogger(__name__)

# --- Modular Logic Imports ---
# These star imports pull all 62 DEFs into this single namespace.
# This keeps the FastAPI routers clean and the directory structure organized.

try:
    from scripts.api_operation_port import *
    from scripts.api_routing_interface import *
    from scripts.api_operation_summary import *
    from scripts.api_operation_customer import *
    from scripts.api_operation_device import *
    from scripts.api_operation_fabric import *
    from scripts.api_operation_network import *
    from scripts.api_operation_route_vision import *

except ImportError as e:
    logger.error(f"Critical Error: Failed to import modular operations: {e}")
    # Optional: raise or handle based on your environment needs

# --- Shared Directory Constants ---
# Kept here as they are used across multiple provisioning workflows
TEMPLATE_DIR = "templates/roles"

"""
MIGRATION SUMMARY:
- Total DEFs migrated: 62
- operations/customer.py: 11 (CRUD + Summaries)
- operations/device.py:   15 (Inventory + Specs + Rack Locations)
- operations/fabric.py:   09 (Services + Logical Connections)
- operations/network.py:  13 (Links + Interfaces + Galileo Beck Views)
- operations/port.py:     14 (Ports + Bulk Logic + Patch Panels)
"""