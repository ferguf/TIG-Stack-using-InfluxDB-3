import logging
import os
from fastapi import FastAPI

# ==========================================
# 1. INITIALIZE MODELS & CORE
# ==========================================
import scripts.api_model # Force SQLAlchemy mapping

from core.exceptions import setup_exception_handlers
from mcp.server import setup_mcp

# ==========================================
# 2. ROUTER IMPORTS (Legacy & Slices)
# ==========================================
# Note: Remove 'locations' from this list once it is fully migrated to a Vertical Slice!
from api.routers import cloud_partner, influxdb, telegraf, route_vision, galileo, docs, locations
from api.routers import ports, customers, fabric_services, devices, fabric_connections, traffic
from api.routers import interface, patch_panel, cross_connect, network_links, inventory, billing

# Import your new Vertical Slices here (e.g., Template)
from domains.template.router import router as template_router

# ==========================================
# 3. FASTAPI APP INIT
# ==========================================
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("uvicorn.error")

app = FastAPI(
    title="Network As Inventory - Network Digital Twin", 
    version="1.0.0"
)

# Apply global error handlers
setup_exception_handlers(app)

# ==========================================
# 4. MOUNT ROUTERS
# ==========================================
# Core / New Slices
app.include_router(template_router)

# Legacy Routers
app.include_router(docs.router)
app.include_router(billing.router)
app.include_router(traffic.router)
app.include_router(cloud_partner.router)
app.include_router(influxdb.router)
app.include_router(telegraf.router)
app.include_router(inventory.router)
app.include_router(route_vision.router)
app.include_router(galileo.router)
app.include_router(customers.router)
app.include_router(fabric_services.router)
app.include_router(fabric_connections.router) 
app.include_router(devices.router)
app.include_router(ports.router)
app.include_router(interface.router)
app.include_router(patch_panel.router)
app.include_router(cross_connect.router)
app.include_router(network_links.router)
app.include_router(locations.router)

# ==========================================
# 5. MOUNT MCP PROTOCOL BRIDGE
# ==========================================
setup_mcp(app)

# ==========================================
# 6. HEALTH CHECK
# ==========================================
@app.get("/health")
def health_check():
    logger.debug("--- DEBUG: Health check endpoint accessed ---")
    try:
        mcp_mounted = any(getattr(r, "path", "") == "/mcp" for r in app.routes)
        logger.debug(f"--- DEBUG: FastMCP Mounted Status: {mcp_mounted} ---")
    except Exception as e:
        logger.debug(f"--- DEBUG: Could not verify MCP status: {e} ---")

    return {"status": "ok"}