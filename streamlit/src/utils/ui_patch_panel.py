import streamlit as st
import pandas as pd

def render_fdp_port_editor(selection):
    """
    Specific editor for FDPs using GET /patchPanels/device/{id} 
    and PUT /patchPanels/port/{panel_port_id}.
    """
    from src.utils.api_patch_panel import get_patch_panel, update_panel_port # Lazy Import
    
    panel_id = selection['device_id']
    st.subheader(f"🔌 FDP Port Configuration: {selection['device_name']}")
    
    # 1. Fetch detailed port map specifically for Patch Panels
    panel_details = get_patch_panel(panel_id)
    
    if panel_details and "ports" in panel_details:
        df_ports = pd.DataFrame(panel_details["ports"])
        
        # 2. Use Data Editor for granular port updates
        # We disable ID columns to prevent accidental database corruption
        edited_df = st.data_editor(
            df_ports,
            key=f"fdp_editor_{panel_id}",
            disabled=["panel_port_id", "device_id"],
            hide_index=True,
            use_container_width=True
        )

        if st.button("💾 Save FDP Port Changes", type="primary"):
            success_count = 0
            for _, row in edited_df.iterrows():
                # API Call: PUT /patchPanels/port/{panel_port_id}
                if update_panel_port(row['panel_port_id'], row.to_dict()):
                    success_count += 1
            
            if success_count > 0:
                st.success(f"✅ Updated {success_count} ports.")
                st.rerun()
    else:
        st.info("No port data found for this FDP.")

def render_fdp_admin_controls(selection):
    """Handles the DELETE /patchPanels/device/{id} logic."""
    from src.utils.api_patch_panel import delete_patch_panel # Lazy Import
    
    st.divider()
    with st.expander("🚨 Danger Zone"):
        st.error(f"Deleting `{selection['device_name']}` will remove all associated port records.")
        confirm = st.text_input("Type the device name to confirm", key=f"del_conf_{selection['device_id']}")
        
        if st.button("🗑️ Delete Patch Panel", type="primary", use_container_width=True):
            if confirm == selection['device_name']:
                # API Call: DELETE /patchPanels/device/{device_id}
                if delete_patch_panel(selection['device_id']):
                    st.success("Patch Panel Deleted.")
                    st.rerun()
            else:
                st.warning("Confirmation name does not match.")