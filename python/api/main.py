import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# ==========================================
# 1. ARCHITECTURAL BOOTSTRAP
# ==========================================
# IMPORTANT: Initialize ORM models BEFORE importing routers
# to ensure SQLAlchemy relationships are fully mapped.
import scripts.api_model 

# --- Core Modules ---
from core.database import get_db
from core.exceptions import setup_exception_handlers
from core.mcp import setup_mcp

# --- New Vertical Slices ---
from domains.docs.router import router as docs_router
from domains.billing.router import router as billing_router
from domains.location.router import router as location_router
from domains.customer.router import router as customer_router
from domains.device.router import router as device_router
from domains.port.router import router as port_router
from domains.inventory.router import router as inventory_router
from domains.fabric_service.router import router as fabric_service_router
from domains.fabric_connection.router import router as fabric_connection_router
from domains.galileo.router import router as galileo_router
from domains.interface.router import router as interface_router
from domains.traffic.router import router as traffic_router
from domains.netlink.router import router as netlink_router
from domains.capabilities.router import router as capabilities_router


# --- Legacy Routers (Pending Migration) ---
from api.routers import (
    cloud_partner, influxdb, telegraf, route_vision, galileo, docs, 
    fabric_services, fabric_connections, traffic, interface, 
    patch_panel, cross_connect, network_links, inventory
)

# ==========================================
# 2. APP INITIALIZATION
# ==========================================
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("uvicorn.error")

app = FastAPI(
    title="Network As Inventory - Network Digital Twin", 
    version="1.0.0"
)

# Apply centralized error handling (core.exceptions)
setup_exception_handlers(app)

# ==========================================
# 3. ROUTER MOUNTING
# ==========================================
# Mount Vertical Slices
app.include_router(docs_router)
app.include_router(billing_router)
app.include_router(location_router)
app.include_router(customer_router)
app.include_router(device_router)
app.include_router(port_router)
app.include_router(inventory_router)
app.include_router(fabric_service_router)
app.include_router(fabric_connection_router)
app.include_router(galileo_router)
app.include_router(interface_router)
app.include_router(traffic_router)
app.include_router(netlink_router)
app.include_router(capabilities_router)
# Mount Legacy Routers

app.include_router(cloud_partner.router)

app.include_router(influxdb.router)
app.include_router(telegraf.router)
app.include_router(route_vision.router)

app.include_router(cross_connect.router)


# ==========================================
# 4. MCP INTEGRATION
# ==========================================
setup_mcp(app)

# ==========================================
# 5. HEALTH CHECK
# ==========================================
@app.get("/health", tags=["system"])
def health_check():
    """System health check endpoint."""
    logger.debug("Health check hit.")
    return {"status": "ok", "version": "1.0.0"}