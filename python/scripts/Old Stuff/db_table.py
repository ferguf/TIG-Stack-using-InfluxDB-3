"""File Name: 'db_table.py' and version '1.0.31' date: 'November 29, 2025 2:35 PM MST' (Change: Minor version bump.) """
import db_config # FIX: Must import 'db_config' to match the actual file name.
from psycopg2 import Error
import sys

# NOTE: This file's sole purpose is to act as a bridge, calling the full schema 
# initialization function defined in db_config.py.

def initialize_schema():
    """
    Calls the comprehensive schema initialization function from db_config to 
    set up the entire database structure (tables and enums).
    """
    # The actual, complete schema creation logic resides in db_config.py
    db_config.initialize_schema()


if __name__ == '__main__':
    # This block is for testing the schema creation independently
    try:
        initialize_schema()
        # Also run seeding when running db_table directly for convenience
        db_config.seed_inventory_data() 
    except Exception as e:
        print(f"Error running schema initialization stand-alone: {e}")