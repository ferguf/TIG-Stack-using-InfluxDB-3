
"""
Configuration file for Database credentials (PostgreSQL & InfluxDB).
File Name: 'db_config.py'
"""

# --- PostgreSQL Configuration ---
DB_USER = "myuser"
DB_PASSWORD = "mypassword"
DB_HOST = "db" 
DB_PORT = "5432"
DB_NAME = "mydatabase"

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# --- InfluxDB 3 Configuration ---
INFLUX_URL = "http://influxdb3-core:8181"
# Use the official generated token to avoid 401 errors
INFLUX_TOKEN = "apiv3_aAcM9fWA-xBEv3DJhD3Zvx-PCjrLFSvbP_s0ArjY8qf8aS1Ac55VKBVssyKvy8mB445W7ryAX-g0zsOiHsaiJg"
INFLUX_ORG = "default"
INFLUX_DB = "network_inventory"
