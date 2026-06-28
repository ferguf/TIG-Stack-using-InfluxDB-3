###############################   
## Telegraf API Router     ####
###############################
import threading
import logging
import json
import os
import time
import random
import requests
from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import text
from sqlalchemy.orm import Session

from scripts.api_session import get_db
from scripts.api_schema import TelegrafInventory
import scripts.api_operation as api_operation
from scripts.api_model import VTelegrafInventory

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/telegraf",
    tags=["telegraf"]
)

# Global control flag for the simulation loop
SIMULATION_RUNNING = False

# -----------------------------
# Inventory Endpoints
# -----------------------------

@router.get("/inventory", response_model=List[TelegrafInventory])
async def get_telegraf_inventory_route(db: Session = Depends(get_db)):
    """
    Retrieve all inventory records from the view for troubleshooting.
    """
    rows = db.query(VTelegrafInventory).limit(1).all()
    if rows:
        print(f"DEBUG: First row dict: {rows[0].__dict__}")

    return api_operation.get_telegraf_inventory(db)

@router.post("/inventory/bake")
async def trigger_inventory_bake(db: Session = Depends(get_db)):
    """
    Triggers the creation of the inventory_lookup.json file.
    """
    try:
        count = bake_inventory_from_view(db)
        return {"status": "success", "entries_baked": count}
    except Exception as e:
        logger.error(f"Bake failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bake failed: {str(e)}")

# -----------------------------
# Simulation Endpoints
# -----------------------------
@router.post("/sim/fec/start", summary="Start MPLS LDP FEC Simulation")
async def start_fec_simulation():
    global SIMULATION_RUNNING
    if SIMULATION_RUNNING:
        return {"message": "Simulation is already running."}
    
    SIMULATION_RUNNING = True
    
    # Using a dedicated Thread ensures the API response returns INSTANTLY
    # while the loop runs independently in the background.
    thread = threading.Thread(target=run_fec_simulation_worker, daemon=True)
    thread.start()
    
    return {"status": "started", "message": "FEC telemetry simulation is running in background thread."}
@router.post("/sim/fec/stop", summary="Stop MPLS LDP FEC Simulation")
async def stop_fec_simulation():
    """
    Sets the global flag to False to break the simulation loop.
    """
    global SIMULATION_RUNNING
    SIMULATION_RUNNING = False
    return {"status": "stopped", "message": "Simulation stop signal sent."}

# -----------------------------
# Internal Logic Functions
# -----------------------------

def bake_inventory_from_view(db: Session, file_path: str = "/app/telegraf/inventory_lookup.json"):
    """
    Reads the ordered View and writes the 'Bread' for Telegraf.
    Using /app/telegraf/... to match the Docker volume mount.
    """
    rows = db.query(VTelegrafInventory).all()
    if not rows:
        return 0

    inventory_data = []
    for row in rows:
        # Validate against the Pydantic schema
        item = TelegrafInventory.model_validate(row)
        inventory_data.append(item.model_dump(mode="json"))

    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    temp_path = f"{file_path}.tmp"
    with open(temp_path, "w") as f:
        json.dump(inventory_data, f, indent=2)
    
    os.replace(temp_path, file_path)
    return len(inventory_data)


def run_fec_simulation_worker():
    """
    Simulation worker that generates MPLS LDP FEC traffic data.
    Sends data to Telegraf via HTTP Listener on port 8080.
    """
    global SIMULATION_RUNNING
    
    # Target Telegraf service on the Docker network
    telegraf_url = "http://telegraf:8080/telegraf"
    
    # Path to your 'baked' inventory metadata
    inventory_path = "/app/telegraf/inventory_lookup.json"
    
    try:
        with open(inventory_path, 'r') as f:
            inventory = json.load(f)
    except Exception as e:
        print(f"FAILED TO LOAD INVENTORY: {e}")
        SIMULATION_RUNNING = False
        return

    # Initialize byte counters for each device
    counters = {dev['device_id']: random.randint(1000000, 5000000) for dev in inventory}

    print(f"SIMULATION STARTED: Sending to {telegraf_url}")

    while SIMULATION_RUNNING:
        for source in inventory:
            dev_id = source['device_id']
            
            # Simulate traffic increment (delta)
            # Roughly 100Mbps to 500Mbps increase per 10s interval
            bytes_increment = random.randint(1250000, 6250000)
            counters[dev_id] += bytes_increment
            
            # Construct InfluxDB Line Protocol
            # Format: measurement,tag1=val,tag2=val field=val
            # Ensure no space between measurement and tags
            lp = (
                f"mpls_ldp_fec,"
                f"device_id={dev_id},"
                f"device_name={source['device_name']},"
                f"port_name={source['port_name']},"
                f"port_cktid={source['port_cktid']},"
                f"site={source.get('site', 'DEN1')} " # Space here starts field set
                f"bytes_total={counters[dev_id]}i"    # 'i' suffix for integer
            )

            try:
                # No 'Authorization' header needed; Telegraf handles the Token
                response = requests.post(telegraf_url, data=lp, timeout=2)
                if response.status_code != 200 and response.status_code != 204:
                    print(f"TELEGRAF REJECTED DATA: {response.status_code} - {response.text}")
                else:
                    print(f"DEBUG PUSH: {source['device_name']} -> {counters[dev_id]} bytes (Status {response.status_code})")
            except Exception as e:
                print(f"TELEGRAF CONNECTION ERROR: {e}")

        time.sleep(10)