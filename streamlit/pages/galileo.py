import streamlit as st
from galileo import svg_galileo


def main():
    st.set_page_config(page_title="Galileo", layout="wide")
    st.title("🌌 Galileo Topology")

    galaxy_nodes = {
        1: {"r": 150, "angle": 0, "label": "Alpha", "color": "#22c55e", "emoji": "⭐"},
        2: {"r": 150, "angle": 120, "label": "Beta", "color": "#f59e0b"},
        3: {"r": 150, "angle": 240, "label": "Gamma", "color": "#3b82f6", "emoji": "🛠️"},
        4: {"r": 250, "angle": 45, "label": "Delta", "color": "#22c55e", "emoji": "🪨"},
    }



def main():
    st.set_page_config(page_title="Galileo", layout="wide")
    st.title("🌌 Galileo Topology")

    svg_string = svg_galileo.render_galileo()
    st.markdown(svg_string, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
