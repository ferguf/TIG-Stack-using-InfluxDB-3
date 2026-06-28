__Topology_VERSION__ = "0.2.0"
print(f"[galileo] Loaded {__Topology_VERSION__}")

import streamlit as st
from src.galileo import svg_galileo

def main():
    st.set_page_config(page_title="Galileo", layout="wide")
    st.title("🌌 Galileo Topology")

    galaxy_nodes = {
        0: {  # Sun node
            "radius": 0,
            "angle": 0,
            "colors": [5, 1],  # outer = red opaque, inner = red solid
            "label_header": "Sun",
            "label_body": "Central hub",
            "visible": False,
            "size_outer": 25,
            "size_inner": 15,
        },
        1: {
            "radius": 150,
            "angle": 320,
            "colors": [6, 2],  # outer = amber opaque, inner = amber solid
            "label_header": "VAR1.DEN1",
            "label_body": "",
            "visible": True,
        },
        2: {
            "radius": 150,
            "angle": 320,
            "colors": [8, 4],  # outer = blue opaque, inner = blue solid
            "label_header": "VAR4.DEN1",
            "label_body": "",
            "visible": True,
        },
        3: {
            "radius": 150,
            "angle": 280,
            "colors": [8, 4],  # outer = blue opaque, inner = blue solid
            "label_header": "VAR1.DEN1",
            "label_body": "",
            "visible": True,
        },
        4: {
            "radius": 150,
            "angle": 240,
            "colors": [8, 4],  # outer = blue opaque, inner = blue solid
            "label_header": "VAR2.DEN1",
            "label_body": "",
            "visible": True,
        },
        5: {
            "radius": 150,
            "angle": 200,
            "colors": [8, 4],  # outer = blue opaque, inner = blue solid
            "label_header": "VAR3.DEN1",
            "label_body": "",
            "visible": True,
        },

        7: {
            "radius": 150,
            "angle": 60,
            "colors": [8, 4],  # outer = blue opaque, inner = blue solid
            "label_header": "SDR1.DEN1",
            "label_body": "",
            "visible": True,
        },
        8: {
            "radius": 150,
            "angle": 120,
            "colors": [8, 4],  # outer = blue opaque, inner = blue solid
            "label_header": "SDR2.DEN1",
            "label_body": "Juniper MX10004",
            "visible": True,
        },
    }

    galaxy_arcs = [
        {
            "source": 1,
            "target": 7,
            "colors": [6, 2],  # amber opaque outer, amber solid inner
            "label_header": "Alpha ↔ Beta",
            "label_body": "Shared bus",
            "url": "https://arc1",
            "size": "M",
            "type": "dash",
            "visible": True,
        },
        {
            "source": 8,
            "target": 1,
            "colors": [3, 8],  # amber opaque outer, amber solid inner
            "label_header": "Alpha ↔ Beta",
            "label_body": "Shared bus",
            "url": "https://arc1",
            "size": "M",
            "type": "dash",
            "visible": True,
        },


    ]

    galaxy_links = [
        {   "source": 1,
            "target": 7,
            "colors": [3, 6],  # blue opaque outer, blue solid inner
            "label_header": "Alpha → Gamma",
            "label_body": "Cross-ring sync",
            "url": "https://link1",
            "size": "L",
            "type": "solid",
            "visible": True,
        },
        {
            "source": 1,
            "target": 8,
            "colors": [8, 4],  # blue opaque outer, blue solid inner
            "label_header": "Alpha → Gamma",
            "label_body": "Cross-ring sync",
            "url": "https://link1",
            "size": "L",
            "type": "solid",
            "visible": True,
        },
        {
            "source": 2,
            "target": 7,
            "colors": [8, 4],  # blue opaque outer, blue solid inner
            "label_header": "Alpha → Gamma",
            "label_body": "Cross-ring sync",
            "url": "https://link1",
            "size": "L",
            "type": "solid",
            "visible": True,
        },
        {
            "source": 2,
            "target": 8,
            "colors": [8, 4],  # blue opaque outer, blue solid inner
            "label_header": "Alpha → Gamma",
            "label_body": "Cross-ring sync",
            "url": "https://link1",
            "size": "L",
            "type": "solid",
            "visible": True,
        },
        {
            "source": 3,
            "target": 7,
            "colors": [3, 6],  # blue opaque outer, blue solid inner
            "label_header": "Alpha → Gamma",
            "label_body": "Cross-ring sync",
            "url": "https://link1",
            "size": "L",
            "type": "solid",
            "visible": True,
        },
        {   "source": 3,
            "target": 8,
            "colors": [3, 6],  # blue opaque outer, blue solid inner
            "label_header": "Alpha → Gamma",
            "label_body": "Cross-ring sync",
            "url": "https://link1",
            "size": "L",
            "type": "solid",
            "visible": True,
        },
        {   "source": 4,
            "target": 8,
            "colors": [3, 6],  # blue opaque outer, blue solid inner
            "label_header": "Alpha → Gamma",
            "label_body": "Cross-ring sync",
            "url": "https://link1",
            "size": "L",
            "type": "solid",
            "visible": True,
        },
        {   "source": 4,
            "target": 8,
            "colors": [3, 6],  # blue opaque outer, blue solid inner
            "label_header": "Alpha → Gamma",
            "label_body": "Cross-ring sync",
            "url": "https://link1",
            "size": "L",
            "type": "solid",
            "visible": True,
        },
        {   "source": 5,
            "target": 7,
            "colors": [3, 6],  # blue opaque outer, blue solid inner
            "label_header": "Alpha → Gamma",
            "label_body": "Cross-ring sync",
            "url": "https://link1",
            "size": "L",
            "type": "solid",
            "visible": True,
        },
        {   "source": 5,
            "target": 8,
            "colors": [3, 6],  # blue opaque outer, blue solid inner
            "label_header": "Alpha → Gamma",
            "label_body": "Cross-ring sync",
            "url": "https://link1",
            "size": "L",
            "type": "solid",
            "visible": True,
        },
        {   "source": 7,
            "target": 8,
            "colors": [3, 6],  # blue opaque outer, blue solid inner
            "label_header": "Alpha → Gamma",
            "label_body": "Cross-ring sync",
            "url": "https://link1",
            "size": "L",
            "type": "solid",
            "visible": True,
        },
    ]

    galaxy_nodes_1 = {
        0: {  # Sun node
            "radius": 0,
            "angle": 0,
            "colors": [5, 1],  # outer = red opaque, inner = red solid
            "label_header": "Sun",
            "label_body": "Central hub",
            "visible": False,
            "size_outer": 25,
            "size_inner": 15,
        },
        1: {
            "radius": 150,
            "angle": 320,
            "colors": [6, 2],  # outer = amber opaque, inner = amber solid
            "label_header": "VAR1.DEN1",
            "label_body": "Juniper MX10004",
            "visible": True,
        },
        2: {
            "radius": 150,
            "angle": 320,
            "colors": [8, 4],  # outer = blue opaque, inner = blue solid
            "label_header": "VAR4.DEN1",
            "label_body": "Juniper MX10004",
            "visible": True,
        },
        3: {
            "radius": 150,
            "angle": 280,
            "colors": [8, 4],  # outer = blue opaque, inner = blue solid
            "label_header": "VAR1.DEN1",
            "label_body": "Juniper MX10004",
            "visible": True,
        },
        4: {
            "radius": 150,
            "angle": 240,
            "colors": [8, 4],  # outer = blue opaque, inner = blue solid
            "label_header": "VAR2.DEN1",
            "label_body": "Juniper MX10004",
            "visible": True,
        },
        5: {
            "radius": 150,
            "angle": 200,
            "colors": [8, 4],  # outer = blue opaque, inner = blue solid
            "label_header": "VAR3.DEN1",
            "label_body": "Juniper MX10004",
            "visible": True,
        },

        7: {
            "radius": 150,
            "angle": 60,
            "colors": [8, 4],  # outer = blue opaque, inner = blue solid
            "label_header": "SDR1.DEN1",
            "label_body": "Juniper MX10004",
            "visible": True,
        },
        8: {
            "radius": 150,
            "angle": 0,
            "colors": [8, 4],  # outer = blue opaque, inner = blue solid
            "label_header": "SDR2.DEN1",
            "label_body": "Juniper MX10004",
            "visible": True,
        },
    }

    galaxy_arcs_1 = [
        {
            "source": 7,
            "target": 8,
            "colors": [7, 2],  # amber opaque outer, amber solid inner
            "label_header": "Alpha ↔ Beta",
            "label_body": "Shared bus",
            "url": "https://arc1",
            "size": "M",
            "type": "dash",
            "visible": True,
        },
        {
            "source": 7,
            "target": 5,
            "colors": [3, 8],  # amber opaque outer, amber solid inner
            "label_header": "Alpha ↔ Beta",
            "label_body": "Shared bus",
            "url": "https://arc1",
            "size": "M",
            "type": "solid",
            "visible": True,
        },
        {
            "source": 5,
            "target": 4,
            "colors": [1, 5],  # amber opaque outer, amber solid inner
            "label_header": "Alpha ↔ Beta",
            "label_body": "Shared bus",
            "url": "https://arc1",
            "size": "M",
            "type": "Solid",
            "visible": True,
        },
        {
            "source": 4,
            "target": 3,
            "colors": [7, 2],  # amber opaque outer, amber solid inner
            "label_header": "Alpha ↔ Beta",
            "label_body": "Shared bus",
            "url": "https://arc1",
            "size": "M",
            "type": "solid",
            "visible": True,
        },
        {
            "source": 3,
            "target": 2,
            "colors": [7, 2],  # amber opaque outer, amber solid inner
            "label_header": "Alpha ↔ Beta",
            "label_body": "Shared bus",
            "url": "https://arc1",
            "size": "M",
            "type": "solid",
            "visible": True,
        },
        {
            "source": 4,
            "target": 3,
            "colors": [7, 2],  # amber opaque outer, amber solid inner
            "label_header": "Alpha ↔ Beta",
            "label_body": "Shared bus",
            "url": "https://arc1",
            "size": "M",
            "type": "solid",
            "visible": True,
        },
        {
            "source": 2,
            "target": 7,
            "colors": [7, 2],  # amber opaque outer, amber solid inner
            "label_header": "Alpha ↔ Beta",
            "label_body": "Shared bus",
            "url": "https://arc1",
            "size": "M",
            "type": "solid",
            "visible": True,
        },

    ]

    galaxy_links_1 = [

    ]


    galaxy_nodes_2 = {
        0: {  # Sun node
            "radius": 0,
            "angle": 0,
            "colors": [5, 1],  # outer = red opaque, inner = red solid
            "label_header": "Sun",
            "label_body": "Central hub",
            "visible": True,
            "size_outer": 25,
            "size_inner": 15,
        },
        1: {
            "radius": 280,
            "angle": 350,
            "colors": [6, 2],  # outer = amber opaque, inner = amber solid
            "label_header": "DEN1",
            "label_body": "4",
            "visible": True,
        },
        2: {
            "radius": 280,
            "angle": 300,
            "colors": [8, 4],  # outer = blue opaque, inner = blue solid
            "label_header": "SFO1",
            "label_body": "",
            "visible": True,
        },
        3: {
            "radius": 280,
            "angle": 250,
            "colors": [8, 4],  # outer = blue opaque, inner = blue solid
            "label_header": "DAL1",
            "label_body": "",
            "visible": True,
        },
        4: {
            "radius": 280,
            "angle": 200,
            "colors": [8, 4],  # outer = blue opaque, inner = blue solid
            "label_header": "NYC1",
            "label_body": "",
            "visible": True,
        },
        5: {
            "radius": 280,
            "angle": 150,
            "colors": [8, 4],  # outer = blue opaque, inner = blue solid
            "label_header": "CHI1",
            "label_body": "",
            "visible": True,
        },

        7: {
            "radius": 280,
            "angle": 100,
            "colors": [8, 4],  # outer = blue opaque, inner = blue solid
            "label_header": "HOU1",
            "label_body": "",
            "visible": True,
        },
        8: {
            "radius": 280,
            "angle": 50,
            "colors": [8, 4],  # outer = blue opaque, inner = blue solid
            "label_header": "ATL1",
            "label_body": "",
            "visible": True,
        },
        12: {
            "radius": 150,
            "angle": 320,
            "colors": [6, 2],  # outer = amber opaque, inner = amber solid
            "label_header": "NSH1",
            "label_body": "",
            "visible": True,
        },
        13: {
            "radius": 150,
            "angle": 300,
            "colors": [8, 4],  # outer = blue opaque, inner = blue solid
            "label_header": "SJO1",
            "label_body": "",
            "visible": True,
        },
        14: {
            "radius": 150,
            "angle": 80,
            "colors": [8, 4],  # outer = blue opaque, inner = blue solid
            "label_header": "PHX1",
            "label_body": "",
            "visible": True,
        },
        15: {
            "radius": 150,
            "angle":240,
            "colors": [8, 4],  # outer = blue opaque, inner = blue solid
            "label_header": "LVS1",
            "label_body": "",
            "visible": True,
        },
        16: {
            "radius": 150,
            "angle":20,
            "colors": [8, 4],  # outer = blue opaque, inner = blue solid
            "label_header": "WDC1",
            "label_body": "",
            "visible": True,
        },
        17: {
            "radius": 150,
            "angle": 260,
            "colors": [8, 4],  # outer = blue opaque, inner = blue solid
            "label_header": "TUS1",
            "label_body": "280",
            "visible": True,
        },
        18: {
            "radius": 150,
            "angle": 290,
            "colors": [8, 4],  # outer = blue opaque, inner = blue solid
            "label_header": "SGD1",
            "label_body": "280",
            "visible": True,
        },
    }

    galaxy_arcs_2 = [
        {
            "source": 7,
            "target": 8,
            "colors": [7, 2],  # amber opaque outer, amber solid inner
            "label_header": "Alpha ↔ Beta",
            "label_body": "Shared bus",
            "url": "https://arc1",
            "size": "M",
            "type": "dash",
            "visible": True,
        },
        {
            "source": 7,
            "target": 5,
            "colors": [3, 8],  # amber opaque outer, amber solid inner
            "label_header": "Alpha ↔ Beta",
            "label_body": "Shared bus",
            "url": "https://arc1",
            "size": "M",
            "type": "solid",
            "visible": True,
        },
        {
            "source": 5,
            "target": 4,
            "colors": [1, 5],  # amber opaque outer, amber solid inner
            "label_header": "Alpha ↔ Beta",
            "label_body": "Shared bus",
            "url": "https://arc1",
            "size": "M",
            "type": "Solid",
            "visible": True,
        },
        {
            "source": 4,
            "target": 3,
            "colors": [7, 2],  # amber opaque outer, amber solid inner
            "label_header": "Alpha ↔ Beta",
            "label_body": "Shared bus",
            "url": "https://arc1",
            "size": "M",
            "type": "solid",
            "visible": True,
        },
        {
            "source": 3,
            "target": 2,
            "colors": [7, 2],  # amber opaque outer, amber solid inner
            "label_header": "Alpha ↔ Beta",
            "label_body": "Shared bus",
            "url": "https://arc1",
            "size": "M",
            "type": "solid",
            "visible": True,
        },
        {
            "source": 4,
            "target": 3,
            "colors": [7, 2],  # amber opaque outer, amber solid inner
            "label_header": "Alpha ↔ Beta",
            "label_body": "Shared bus",
            "url": "https://arc1",
            "size": "M",
            "type": "solid",
            "visible": True,
        },
        {
            "source": 2,
            "target": 7,
            "colors": [7, 2],  # amber opaque outer, amber solid inner
            "label_header": "Alpha ↔ Beta",
            "label_body": "Shared bus",
            "url": "https://arc1",
            "size": "M",
            "type": "solid",
            "visible": True,
        },

    ]

    galaxy_links_2 = [
        {
            "source": 1,
            "target": 7,
            "colors": [3, 6],  # blue opaque outer, blue solid inner
            "label_header": "Alpha → Gamma",
            "label_body": "Cross-ring sync",
            "url": "https://link1",
            "size": "L",
            "type": "solid",
            "visible": True,
        },
        {
            "source": 13,
            "target": 14,
            "colors": [3, 6],  # blue opaque outer, blue solid inner
            "label_header": "Alpha → Gamma",
            "label_body": "Cross-ring sync",
            "url": "https://link1",
            "size": "L",
            "type": "solid",
            "visible": True,
        },
        ]

    svg_string = svg_galileo.render_galileo(galaxy_nodes_2, galaxy_arcs_2, galaxy_links_2)
    st.markdown(svg_string, unsafe_allow_html=True)
    svg_string = svg_galileo.render_galileo(galaxy_nodes, galaxy_arcs, galaxy_links)
    st.markdown(svg_string, unsafe_allow_html=True)
    svg_string = svg_galileo.render_galileo(galaxy_nodes_1, galaxy_arcs_1, galaxy_links_1)
    st.markdown(svg_string, unsafe_allow_html=True)

if __name__ == "__main__":
    main()