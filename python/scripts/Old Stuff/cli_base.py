"""File Name: 'python/cli_base.py' and version '1.0.25' date: 'November 30, 2025' (Refactor: Extracted common database and configuration setup logic into a reusable base module for all CLI scripts.) """
import sys
import uuid
import datetime
from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker, joinedload, relationship 
from sqlalchemy.sql.expression import not_

import db_config 

SERVICE_TYPES = (
    'E-Line EPL',
    'E-Line EVPL',
    'E-LAN EPLAN',
    'E-LAN EVPLAN',
    'IPVPN',
    'DIA',
    'IOD',
    'MCGW'
)
def validation_service_type(service_name: str) -> bool:
    """
    Validates if a given service name is one of the defined SERVICE_TYPES.
    This function demonstrates how the SERVICE_TYPES constant can be used
    in a conditional structure.
    """
    if service_name in SERVICE_TYPES:
        return True
    else:
        # The 'else' block handles invalid service types
        raise ValueError(
            f"Invalid service type '{service_name}'. "
            f"Must be one of: {', '.join(SERVICE_TYPES)}"
        )   

# Import models and Base class
# NOTE: These model imports are needed here so that the Base class is aware of all tables 
# when Base.metadata.create_all is called (usually in the main CLI entry point).
from network_inventory_models import (
    Customer, 
    FabricService, 
    Port, 
    Device, 
    # PortLink, <--- Removed: No longer needed as per schema definition
    Base, # Import the Base class for engine binding
    # FabricConnection # Assuming this model is defined in network_inventory_models
)

# --- SQLAlchemy Engine and Session Setup ---

# 1. Create the engine using the SQLAlchemy URL format
try:
    # Use the helper function from db_config to get the correct URL format
    SQLALCHEMY_URL = db_config.get_sqlalchemy_url()
    
    # Create the engine using the correctly formatted URL
    engine = create_engine(
        SQLALCHEMY_URL,
        pool_pre_ping=True
    )
    
    # 2. Define the session factory
    # This SessionLocal can be imported and used in any CLI script
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print("✅ SQLAlchemy Engine and SessionLocal set up successfully in CLI base module.")
    
except Exception as e:
    # Handle critical failure if the engine cannot be created
    print(f"\n❌ CRITICAL ERROR: Failed to set up SQLAlchemy Engine.")
    print(f"Attempted URL: {SQLALCHEMY_URL if 'SQLALCHEMY_URL' in locals() else 'Not generated'}")
    print(f"Details: {e}")
    # Define a stub SessionLocal to ensure any call to it fails gracefully
    def SessionLocal():
        raise RuntimeError("SQLAlchemy SessionLocal is not initialized due to engine failure.")