import os
import time
import pandas as pd
import streamlit as st

class MessageHandler:
    LOG_DIR = "templates/base"
    LOG_FILE = os.path.join(LOG_DIR, "fdp_operations.log")
    CATEGORIES = ["API", "UI", "Forms"]

    @staticmethod
    def initialize():
        if not os.path.exists(MessageHandler.LOG_DIR):
            os.makedirs(MessageHandler.LOG_DIR)
        
        if "process_messages" not in st.session_state:
            st.session_state.process_messages = []
            
        # Initialize category toggles
        for cat in MessageHandler.CATEGORIES:
            key = f"debug_active_{cat.lower()}"
            if key not in st.session_state:
                st.session_state[key] = False

    @staticmethod
    def add(text, type="info", category=None):
        """
        BACKWARD COMPATIBLE: 
        If category is None (default), it logs normally. 
        If category is provided, it respects the debug toggles.
        """
        if category:
            state_key = f"debug_active_{category.lower()}"
            # If the toggle is OFF, we exit and don't log
            if not st.session_state.get(state_key, False):
                return

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cat_label = f"[{category.upper()}]" if category else "[SYS]"
        
        # UI Storage
        st.session_state.process_messages.append({
            "text": f"{cat_label} {text}", 
            "type": type, 
            "time": timestamp
        })

        # File Logging
        try:
            with open(MessageHandler.LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {cat_label} [{type.upper()}] {text}\n")
        except:
            pass

    @staticmethod
    def render_ui_logs(key_suffix="default"):
        """The modern log viewer."""
        MessageHandler.initialize()
        if st.session_state.get("process_messages"):
            with st.expander("📋 Activity & Debug Logs", expanded=True):
                # Download button and log display logic here
                for msg in st.session_state.process_messages[-10:]:
                    fmt = f"**{msg['time']}** | {msg['text']}"
                    if msg["type"] == "success": st.success(fmt)
                    elif msg["type"] == "error": st.error(fmt)
                    elif msg["type"] == "warning": st.warning(fmt)
                    else: st.info(fmt)

    # --- BACKWARD COMPATIBILITY ALIAS ---
    @staticmethod
    def render(key_suffix="default"):
        """Maps 'render' to 'render_ui_logs' so old code doesn't break."""
        MessageHandler.render_ui_logs(key_suffix=key_suffix)

    @staticmethod
    def render_debug_controls():
        """New: Place in sidebar to toggle API/UI/Forms logging."""
        MessageHandler.initialize()
        st.sidebar.markdown("### 🛠️ Debug Control Center")
        for cat in MessageHandler.CATEGORIES:
            st.sidebar.toggle(cat, key=f"debug_active_{cat.lower()}")

def find_and_read_role_file(device_model: str, role: str):
    """
    Constructs filename as {role}_{model}.csv 
    Example: var_mx10004.csv
    """
    base_path = "templates/roles"
    
    # Standardize names
    clean_role = str(role).lower().strip()
    clean_model = str(device_model).lower().strip()
    
    filename = f"{clean_role}_{clean_model}.csv"
    file_path = os.path.join(base_path, filename)

    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            MessageHandler.add(f"📄 Loaded template: {filename}", "success")
            return df, file_path
        except Exception as e:
            MessageHandler.add(f"❌ Error reading {filename}: {e}", "error")
            return None, None
    else:
        # Debugging message to show the user exactly what path failed
        MessageHandler.add(f"⚠️ File Missing at {file_path}", "error")
        return None, None

def find_and_read_connect_file(device_name: str):
    """
    Looks for connectivity templates in templates/devices/{device_name}_connect.csv
    """
    # Standardize the filename based on your requirements
    filename = f"{str(device_name).strip()}_connect.csv"
    target_path = os.path.join("templates", "devices", filename)

    if os.path.exists(target_path):
        try:
            df = pd.read_csv(target_path)
            MessageHandler.add(f"📖 Blueprint found: {filename}", "success")
            return normalize_dataframe_columns(df), filename
        except Exception as e:
            MessageHandler.add(f"❌ Error reading {filename}: {e}", "error")
            return None, filename
    else:
        # We don't necessarily want an error log immediately if it's a search, 
        # but we return None to let the UI handle the warning.
        return None, filename

def normalize_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes CSV headers: lowercase, snake_case, and whitespace removal."""
    df.columns = [
        str(c).lower().strip().replace(' ', '_').replace('-', '_') 
        for c in df.columns
    ]
    return df

def sanitize_for_api(df: pd.DataFrame) -> pd.DataFrame:
    """Prepares data for JSON serialization (NaN -> None)."""
    return df.where(pd.notnull(df), None)

def get_new_records_only(uploaded_df: pd.DataFrame, db_records: list) -> pd.DataFrame:
    """
    Compares uploaded CSV against database to filter out existing devices.
    """
    if 'device_name' not in uploaded_df.columns or not db_records:
        return uploaded_df
    
    # Create a set of uppercase names already in the DB for fast lookup
    existing_names = {
        str(r['device_name']).upper().strip() 
        for r in db_records if r.get('device_name')
    }
    
    # Filter the dataframe
    uploaded_df['temp_norm'] = uploaded_df['device_name'].astype(str).str.upper().str.strip()
    new_df = uploaded_df[~uploaded_df['temp_norm'].isin(existing_names)].copy()
    
    return new_df.drop(columns=['temp_norm'])

def clean_device_payload(row_dict: dict) -> dict:
    """
    Standardizes row data and logs the finalized payload for debugging.
    """
    def safe_str(val):
        if pd.isna(val) or val is None or str(val).lower() == 'nan':
            return ""
        return str(val).strip()

    payload = {
        "device_name":        safe_str(row_dict.get("device_name")),
        "device_role":        safe_str(row_dict.get("device_role")),
        "device_model":       safe_str(row_dict.get("device_model")),
        "device_vendor":      safe_str(row_dict.get("device_vendor")),
        "availability_zone":  safe_str(row_dict.get("availability_zone", "0")),
        "lifecycle_status":   safe_str(row_dict.get("lifecycle_status", "Active")),
        "planning_status":    safe_str(row_dict.get("planning_status", "Planned")),
        "health_status":      int(row_dict.get("health_status", 4)),
        "device_description": safe_str(row_dict.get("device_description")),
        "network":            safe_str(row_dict.get("network")),
        "location":           safe_str(row_dict.get("location")),
        "floor":              safe_str(row_dict.get("floor")),
        "aisle":              safe_str(row_dict.get("aisle")),
        "rack":               safe_str(row_dict.get("rack")),
    }

    # 🔍 DEBUG: Log the payload to the UI Console
    msg = (f"📤 STAGED PAYLOAD | Name: {payload['device_name']} | "
           f"Loc: {payload['location']} | Aisle: {payload['aisle']} | Net: {payload['network']}")
    MessageHandler.add(msg, "info", category="DEBUG")
    
    return payload
