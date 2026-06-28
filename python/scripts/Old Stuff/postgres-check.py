import psycopg2
from psycopg2 import Error

# --- 1. Database Configuration ---
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "mydatabase",  # <-- CHANGE THIS
    "user": "myuser",          # <-- CHANGE THIS
    "password": "mypassword"   # <-- CHANGE THIS
}

def check_db_connection(config: dict):
    """Attempts to establish a connection to the PostgreSQL database."""
    conn = None
    try:
        print(f"Attempting to connect to database '{config['database']}' at {config['host']}:{config['port']}...")
        
        # Attempt connection
        conn = psycopg2.connect(**config)
        
        # If the connection attempt succeeds, we are connected.
        print("\n✅ CONNECTION SUCCESSFUL!")
        print("Database connection parameters:")
        print(f"  - Host: {config['host']}")
        print(f"  - Database: {config['database']}")
        print(f"  - User: {config['user']}")

    except (Exception, Error) as error:
        # Handle connection-specific errors (e.g., incorrect host, port, credentials)
        print("\n❌ CONNECTION FAILED!")
        print(f"Error details: {error}")
        print("\nTroubleshooting Steps:")
        print("1. Check if PostgreSQL server is running.")
        print("2. Verify `DB_CONFIG` credentials, host, and port are correct.")
        print("3. Check firewall rules if the database is remote.")
        
    finally:
        # Always close the connection, whether successful or failed
        if conn:
            conn.close()
            print("\nDatabase connection closed.")

# --- 2. Main Execution ---
if __name__ == "__main__":
    check_db_connection(DB_CONFIG)