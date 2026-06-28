import streamlit as st
from src.utils.doc_manager import DocManager

def show_documentation_router():
    st.title("📖 Route Vision Knowledge Base")

    # 1. Fetch the index from FastAPI
    all_docs = DocManager.get_index()
    
    if not all_docs:
        st.warning("No documents found on the server.")
        return

    # 2. Sidebar Search and Selection
    st.sidebar.header("Navigation")
    
    # Search filter
    search_query = st.sidebar.text_input("🔍 Search documents...", "").lower()
    filtered_docs = [d for d in all_docs if search_query in d['path'].lower()]

    if not filtered_docs:
        st.sidebar.info("No matching files found.")
        return

    # Selection dropdown (formatted to show folder structure)
    selected_doc = st.sidebar.selectbox(
        "Select a Manual",
        options=filtered_docs,
        format_func=lambda x: x['path'].replace("/", " ➔ "),
        key="doc_selector"
    )

    # 3. Content Area
    st.caption(f"Last updated: {selected_doc.get('timestamp_str', 'Recent')}")
    st.divider()
    
    # Use the Manager to fetch and render the content
    DocManager.render_content(selected_doc['path'])

if __name__ == "__main__":
    show_documentation_router()