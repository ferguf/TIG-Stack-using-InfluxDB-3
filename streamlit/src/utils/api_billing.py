import requests
import pandas as pd
import streamlit as st

# --- Global Configuration ---
# Adjust this if your backend runs on a different port or host
API_URL = "http://fastapi:8000"

# =========================================================
# 1. READ OPERATIONS (GET)
# =========================================================

def get_billing_models() -> pd.DataFrame:
    """Fetch all billing models from FastAPI and return as DataFrame."""
    try:
        resp = requests.get(f"{API_URL}/billing/models")
        resp.raise_for_status()
        data = resp.json()
        return pd.DataFrame(data if isinstance(data, list) else [data])
    except Exception as e:
        print(f"Error fetching billing models: {e}")
        return pd.DataFrame()

def get_billing_rates() -> pd.DataFrame:
    """Fetch all billing rates from FastAPI and return as DataFrame."""
    try:
        resp = requests.get(f"{API_URL}/billing/rates")
        resp.raise_for_status()
        data = resp.json()
        return pd.DataFrame(data if isinstance(data, list) else [data])
    except Exception as e:
        print(f"Error fetching billing rates: {e}")
        return pd.DataFrame()

def get_billing_providers() -> pd.DataFrame:
    """Fetch all infrastructure providers from FastAPI and return as DataFrame."""
    try:
        resp = requests.get(f"{API_URL}/billing/providers")
        resp.raise_for_status()
        data = resp.json()
        return pd.DataFrame(data if isinstance(data, list) else [data])
    except Exception as e:
        print(f"Error fetching billing providers: {e}")
        return pd.DataFrame()


# =========================================================
# 2. SEEDING / INTENT OPERATIONS (POST)
# =========================================================

def post_seed_base() -> dict:
    """Trigger the backend to seed the foundational Models and Rates."""
    resp = requests.post(f"{API_URL}/billing/intents/seed-base")
    resp.raise_for_status()
    return resp.json()

def post_seed_provider() -> dict:
    """Trigger the backend to seed the standard infrastructure providers."""
    resp = requests.post(f"{API_URL}/billing/intents/seed-provider")
    resp.raise_for_status()
    return resp.json()

def post_service_intent(payload: dict) -> dict:
    """Execute a billing intent for a specific provisioned service."""
    resp = requests.post(f"{API_URL}/billing/intents/svc", json=payload)
    resp.raise_for_status()
    return resp.json()


# =========================================================
# 3. GRANULAR CATALOG ONBOARDING (POST)
# =========================================================

def post_billing_model(payload: dict) -> dict:
    """Create a new billing model."""
    resp = requests.post(f"{API_URL}/billing/models", json=payload)
    resp.raise_for_status()
    return resp.json()

def post_billing_rate(payload: dict) -> dict:
    """Create a new commercial rate card."""
    resp = requests.post(f"{API_URL}/billing/rates", json=payload)
    resp.raise_for_status()
    return resp.json()


def post_billing_port(payload: dict):
    """
    Pushes a single port payload to the backend.
    """
    resp = requests.post(f"{API_URL}/billing/ports", json=payload)
    
    # If FastAPI throws an error (like a 400), raise the EXACT text to Streamlit
    if resp.status_code != 200:
        raise Exception(f"Backend Error: {resp.text}")
        
    return resp.json()

def post_billing_access(payload: dict):
    """
    Pushes a single access tier payload to the backend.
    """
    resp = requests.post(f"{API_URL}/billing/access", json=payload)
    
    # Expose the exact FastAPI/SQLAlchemy error text to the UI
    if resp.status_code != 200:
        raise Exception(f"Backend Error: {resp.text}")
        
    return resp.json()

def post_billing_bw(payload: dict) -> dict:
    """Commit bandwidth ladder pricing to a rate card."""
    resp = requests.post(f"{API_URL}/billing/bandwidth", json=payload)
    
    # Expose the exact FastAPI/SQLAlchemy error text to the UI
    if resp.status_code != 200:
        raise Exception(f"Backend Error: {resp.text}")
        
    return resp.json()

def post_billing_provider(payload: dict) -> dict:
    """Register a new Off-Net or XaaS provider."""
    resp = requests.post(f"{API_URL}/billing/providers", json=payload)
    resp.raise_for_status()
    return resp.json()


# =========================================================
# 4. UPDATE OPERATIONS (PUT)
# =========================================================

def put_billing_model(model_id: str, payload: dict) -> dict:
    """Update an existing billing model."""
    resp = requests.put(f"{API_URL}/billing/models/{model_id}", json=payload)
    resp.raise_for_status()
    return resp.json()

def put_billing_rate(rate_id: str, payload: dict) -> dict:
    """Update an existing commercial rate card."""
    resp = requests.put(f"{API_URL}/billing/rates/{rate_id}", json=payload)
    resp.raise_for_status()
    return resp.json()

def put_billing_provider(provider_id: str, payload: dict) -> dict:
    """Update an existing infrastructure provider."""
    resp = requests.put(f"{API_URL}/billing/providers/{provider_id}", json=payload)
    resp.raise_for_status()
    return resp.json()


# =========================================================
# 5. DELETE OPERATIONS (DELETE)
# =========================================================

def delete_billing_model(model_id: str) -> dict:
    """Delete a billing model by ID."""
    resp = requests.delete(f"{API_URL}/billing/models/{model_id}")
    resp.raise_for_status()
    return resp.json()

def delete_billing_rate(rate_id: str) -> dict:
    """Delete a commercial rate card by ID."""
    resp = requests.delete(f"{API_URL}/billing/rates/{rate_id}")
    resp.raise_for_status()
    return resp.json()

def delete_billing_provider(provider_id: str) -> dict:
    """Delete an infrastructure provider by ID."""
    resp = requests.delete(f"{API_URL}/billing/providers/{provider_id}")
    resp.raise_for_status()
    return resp.json()
import requests

# (Ensure your API_URL is defined at the top of the file, e.g., API_URL = "http://localhost:8000")

def get_rate_card_composite(rate_id: str) -> dict:
    """
    Fetch the complete nested JSON summary of a Rate Card from the FastAPI backend.
    """
    try:
        resp = requests.get(f"{API_URL}/billing/rates/{rate_id}/composite")
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Network error fetching composite rate card: {e}")
        return {}
    except Exception as e:
        print(f"Data processing error for composite rate card: {e}")
        return {}

def post_billing_token(payload: dict) -> dict:
    """Commit usage token pricing to a rate card."""
    resp = requests.post(f"{API_URL}/billing/token", json=payload)
    
    # Expose the exact FastAPI/SQLAlchemy error text to the UI
    if resp.status_code != 200:
        raise Exception(f"Backend Error: {resp.text}")
        
    return resp.json()