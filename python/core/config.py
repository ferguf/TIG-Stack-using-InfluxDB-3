"""
Configuration file for Database credentials (PostgreSQL & InfluxDB).
Centralized for the Vertical Slice Architecture.
"""
import os

# --- PostgreSQL Configuration ---
DB_USER = os.getenv("DB_USER", "myuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mypassword")
DB_HOST = os.getenv("DB_HOST", "db") 
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "mydatabase")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# --- InfluxDB 3 Configuration ---
INFLUX_URL = os.getenv("INFLUX_URL", "http://influxdb3-core:8181")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "apiv3_aAcM9fWA-xBEv3DJhD3Zvx-PCjrLFSvbP_s0ArjY8qf8aS1Ac55VKBVssyKvy8mB445W7ryAX-g0zsOiHsaiJg")
INFLUX_ORG = os.getenv("INFLUX_ORG", "default")
INFLUX_DB = os.getenv("INFLUX_DB", "network_inventory")