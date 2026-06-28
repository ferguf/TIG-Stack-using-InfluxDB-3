from fastapi import FastAPI
import sys
import os

# --- Ensure python/scripts is on the import path ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(BASE_DIR, "..", "scripts")
sys.path.append(SCRIPTS_DIR)

# --- Now you can import your scripts/modules ---
import api_operations   # example: your script in python/scripts

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "FastAPI is running!"}

@app.get("/customers")
def get_all_customers():
    # Example: call a function from db_man_cli
    # Suppose db_man_cli has a function `load_customers()`
    customers = api_operations.get_all_customers()
    return {"customers": customers}

@app.get("/fabric_service") 
def get_all_fabric_services():
    # Example: call a function from db_man_cli
    # Suppose db_man_cli has a function `load_customers()`
    fabric_service = api_operations.get_all_fabric_services()
    return {"fabric_services": fabric_service}


@app.get("/health")
def health_check():
    return {"status": "ok"}