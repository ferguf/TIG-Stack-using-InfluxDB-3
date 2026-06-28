import streamlit as st

class MessageCenter:
    @staticmethod
    def set_success(text: str):
        """Stores a success message in the Data Bus to survive reruns."""
        st.session_state["pending_success"] = text

    @staticmethod
    def display_messages():
        """Checks the Data Bus and renders any waiting messages."""
        if "pending_success" in st.session_state:
            st.success(st.session_state["pending_success"])
            # We also trigger a toast as a backup for better UX
            st.toast(st.session_state["pending_success"], icon="✅")
            # Clear it so it doesn't repeat
            del st.session_state["pending_success"]
            
    @staticmethod
    def set_error(text: str):
        """Displays an immediate error (no rerun needed usually)."""
        st.error(text)
        
