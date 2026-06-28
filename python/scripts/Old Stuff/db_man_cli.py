"""
File Name: 'db_man_cli.py'
Version: 2.0.0
Date: 2025-11-30
Feature: Major refactor: Switched from raw sqlite3 to SQLAlchemy ORM.
         Implements engine creation, session factory, schema initialization, and data seeding using models.
"""

import sys
import uuid
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
from sqlalchemy.sql.expression import not_

import db_config 

# Import models and Base class
from network_inventory_models import (
    Customer, 
    FabricService, 
    Port, 
    Device, 
    Base # Import the Base class for engine binding
)

# --- CONFIGURATION ---

# Global variable to hold the engine instance
engine = None
# Global variable to hold the Session factory
SessionLocal = None

# --- SQLAlchemy Engine and Session Setup ---
def setup_sqlalchemy_environment():
    """Initializes the SQLAlchemy Engine and SessionLocal factory."""
    global engine, SessionLocal
    
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
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print("✅ SQLAlchemy Engine and SessionLocal set up successfully in CLI.")
        
    except Exception as e:
        # Handle critical failure if the engine cannot be created
        print(f"\n❌ CRITICAL ERROR: Failed to set up SQLAlchemy Engine.")
        print(f"Attempted URL: {SQLALCHEMY_URL if 'SQLALCHEMY_URL' in locals() else 'Not generated'}")
        print(f"Details: {e}")
        # Define a stub SessionLocal to ensure any call to it fails gracefully
        def SessionLocal():
            raise RuntimeError("SQLAlchemy SessionLocal is not initialized due to engine failure.")
        
        # Terminate if setup fails
        engine = None

# --- CLI Helpers ---

def get_session_or_fail():
    """Helper to retrieve a session by calling the locally defined SessionLocal factory."""
    # Ensure SessionLocal was successfully defined during setup
    if SessionLocal is None or engine is None:
        print("\n❌ DATABASE CONNECTION ERROR: SQLAlchemy environment not initialized.")
        return None
        
    session = None
    try:
        # Calling SessionLocal() attempts to connect
        session = SessionLocal()
        return session
    except Exception as e:
        # This catch is usually for initialization/connection failure
        print(f"\n❌ DATABASE CONNECTION ERROR: Could not establish a session.")
        print("Please ensure your database is running and configured correctly. Run option [1] to initialize schema.")
        print(f"Details: {e}")
        return None

# --- Database Operations (Refactored to use SQLAlchemy) ---

def initialize_schema():
    """[1] Initializes the database schema using Base.metadata.create_all()."""
    if engine is None:
        print("\n❌ ERROR: Engine is not initialized. Cannot create schema.")
        return

    print("\n-> Executing: [1] DB: Initialize/Update Schema (Create Tables)")
    try:
        # This function checks the database and creates all tables defined by models
        Base.metadata.create_all(engine)
        print("✅ SUCCESS: Database schema initialized (all tables created/checked).")
    except Exception as e:
        print(f"❌ ERROR: Failed to create database schema. Details: {e}")


# --- CLI Menu Functions ---

def display_menu():
    """Prints the main interactive menu options."""
    print("\n--- Network Inventory Database Management (SQLAlchemy) ---")
    print("----------------------------------------------------------")
    print(" [1] DB: Initialize/Update Schema (Create Tables)")
    print(" [2] DB: Seed Initial Inventory Data (via SQLAlchemy Models)")
    print("----------------------------------------------------------")
    print(" [h] Show this help menu")
    print(" [q] Quit the application")
    print("----------------------------------------------------------")

def cli_loop():
    """Handles the main command loop."""
    
    # 0. Setup the SQLAlchemy environment first
    setup_sqlalchemy_environment()

    # Check for fatal initialization error
    if engine is None:
        print("❌ FATAL: Application cannot run without a database engine. Exiting.")
        return
        
    print("\n--- Starting Network Inventory Manage CLI ---")
    print("👋 Welcome! Run options [1] and [2] to prepare the database before use.")
        
    while True:
        display_menu()
        cmd = input("\nEnter command [1, 2, h, q]: ").strip().lower()
        
        try:
            if cmd == 'q':
                print("Exiting application. Goodbye!")
                # The engine and session factory don't strictly need to be "closed" in this way,
                # but it's good practice to call cleanup if necessary.
                break
            elif cmd == 'h':
                continue
            
            # Handlers for DB Setup
            elif cmd == '1':
                db_config.initialize_schema()
            elif cmd == '2':
                db_config.seed_inventory_data()
            else:
                print(f"\n❓ Unknown command: {cmd}")
        
        except Exception as e:
            print(f"\n| CRITICAL ERROR | An unexpected error occurred in CLI: {e}")
            break


if __name__ == '__main__':
    cli_loop()