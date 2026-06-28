import streamlit as st
import requests
from urllib.parse import quote

class DocManager:
    # Ensure these match your successful curl commands
    API_BASE = "http://fastapi:8000/docs"

    @staticmethod
    @st.cache_data(ttl=300)
    def get_index():
        """Fetches the JSON list of docs."""
        try:
            r = requests.get(f"{DocManager.API_BASE}/index", timeout=2)
            if r.status_code == 200:
                return r.json()
            return []
        except Exception as e:
            st.error(f"Connection Error: {e}")
            return []

    @staticmethod
    def render_full_page():
        """The main UI entry point."""
        st.sidebar.divider()
        st.sidebar.subheader("📚 Documentation")

        all_docs = DocManager.get_index()

        if not all_docs:
            st.sidebar.info("No documents found.")
            return

        # 1. Selection dropdown
        # 'all_docs' is a list of dicts: [{'path': '...', 'name': '...'}, ...]
        selection = st.sidebar.selectbox(
            "Select Manual",
            options=all_docs,
            # This makes "api_design/device.md" look like "api_design ➔ device"
            format_func=lambda x: x['path'].replace(".md", "").replace("/", " ➔ "),
            key="doc_selector"
        )

        if selection:
            # 2. Extract path and render
            DocManager.render_content(selection['path'])

    @staticmethod
    def render_content(rel_path):
        """Fetches raw text and renders with a Table of Contents."""
        # URL encode the path (handles the / as %2F automatically)
        safe_path = quote(rel_path, safe='')
        url = f"{DocManager.API_BASE}/raw/{safe_path}"
        
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                content = response.text
                
                # Create Sidebar Table of Contents
                st.sidebar.markdown("---")
                st.sidebar.markdown("### 📋 Contents")
                for line in content.split('\n'):
                    if line.startswith('## '):
                        label = line.replace('## ', '').strip()
                        anchor = label.lower().replace(' ', '-')
                        st.sidebar.markdown(f"[{label}](#{anchor})")
                
                # Main Area
                st.title(f"📖 {rel_path.split('/')[-1].replace('.md', '')}")
                st.markdown(content)
            else:
                st.error(f"Failed to load: {rel_path} (Status: {response.status_code})")
        except Exception as e:
            st.error(f"Error fetching content: {e}")