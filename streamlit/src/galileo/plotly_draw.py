import streamlit as st
import streamlit.components.v1 as components
# 🚀 Update: Pointing to the standardized engine that supports geometry
from src.galileo.plotly_galileo import render_standard_engine

class PlotlyDraw:

    def show_topology(self, nodes, orbits, links, topo_id, key_prefix="default"):
        """
        Refactored with Simplified Auto-Scaling.
        Maintains 1:1 Aspect Ratio and adds a dynamic buffer 
        around the largest geometric orbit.
        """
        # 1. THE HANDSHAKE
        fig = render_standard_engine(
            nodes=nodes, 
            links=links, 
            orbits=orbits, 
            template_name="Galileo Universe",
            highlight_node=st.session_state.get("hover_node")
        )

        # 🚀 SIMPLIFIED VIEWPORT SCALING
        # This ensures a square grid (circles stay circles) 
        # and adds enough padding so labels aren't cut off.
        fig.update_layout(
            yaxis=dict(
                scaleanchor="x", 
                scaleratio=1,
                autorange=True
            ),
            xaxis=dict(autorange=True),
            margin=dict(l=40, r=40, t=40, b=40), # Generous internal padding
            height=700,
            # Keeps the background clean for the Streamlit container
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )

        unique_key = f"{key_prefix}_{topo_id}_{len(nodes)}_{len(orbits)}"
        
        # 2. RENDER THE CHART
        event = st.plotly_chart(
            fig, 
            use_container_width=True, 
            on_select="rerun", 
            key=unique_key
        )
        
        # 3. HYPERLINK & NAVIGATION LOGIC
        if event and "selection" in event:
            points = event["selection"].get("points", [])
            if points:
                # Customdata is where we store the node's deep-link URL
                url = points[0].get("customdata")
                if url and url.strip():
                    import streamlit.components.v1 as components
                    js_code = f"window.open('{url}', '_blank');"
                    components.html(f"<script>{js_code}</script>", height=0)
                    st.toast(f"🚀 Navigating to: {url}")
        
        return event
        """
        Refactored to support Geometric Snapping (Square/Triangle/Rectangle).
        Ensures the 'Galileo Universe' template is the default fallback.
        """
        # 1. THE HANDSHAKE: Pass orbits into the standard engine.
        # This tells the template: "Don't draw a circle, draw the shapes in this list."
        fig = render_standard_engine(
            nodes=nodes, 
            links=links, 
            orbits=orbits, 
            template_name="Galileo Universe",
            highlight_node=st.session_state.get("hover_node")
        )

        unique_key = f"{key_prefix}_{topo_id}_{len(nodes)}_{len(orbits)}"
        
        # 2. RENDER THE CHART
        # We use on_select="rerun" to capture clicks for the URL logic
        event = st.plotly_chart(
            fig, 
            use_container_width=True, 
            on_select="rerun", 
            key=unique_key
        )
        
        # 3. HYPERLINK & NAVIGATION LOGIC
        if event and "selection" in event:
            points = event["selection"].get("points", [])
            if points:
                # Customdata is where we store the node's deep-link URL
                url = points[0].get("customdata")
                if url and url.strip():
                    # Injects JS to open URL in a new tab
                    js_code = f"window.open('{url}', '_blank');"
                    components.html(f"<script>{js_code}</script>", height=0)
                    st.toast(f"🚀 Navigating to: {url}")
        
        return event