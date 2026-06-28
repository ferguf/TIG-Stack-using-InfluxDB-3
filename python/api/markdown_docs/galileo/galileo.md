
---

# 🚀 Galileo Topology Engine Documentation

The Galileo Engine is a geometric network visualization framework built on Plotly and Streamlit. It uses a **Centric-Orbit** model where nodes are snapped to absolute mathematical perimeters of specific shapes (Circles, Squares, Triangles).

## 1. Core Concepts

* **The Sun**: A node with `node_type: "sun"` is forced to the absolute center .
* **Orbits**: Geometric "tracks" defined by a radius (`rx`/`ry`) and a shape type.
* **Snapping**: Unlike standard layouts, nodes use a "Minute" system (0-60) to snap to the perimeter of the orbit shape.
* **The Minute System**:
* `0`: North (Top)
* `15`: East (Right)
* `30`: South (Bottom)
* `45`: West (Left)



---

## 2. Data Structure Reference

### Orbits (`galaxy_orbits`)

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `id` | string | **Req** | Unique ID referenced by nodes. |
| `type` | string | `circle` | `circle`, `square`, `rectangle`, `triangle`. |
| `rx` | int | 150 | Horizontal radius from center. |
| `ry` | int | `rx` | Vertical radius (creates ovals/rectangles). |
| `mins` | float | 0 | Rotation of the orbit itself (0-60). |
| `style` | string | `solid` | `solid`, `dash`, `dot`. |
| `color` | string | `white` | Border color of the orbit track. |

### Nodes (`galaxy_nodes`)

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `node_type` | string | `planet` | `sun` (center) or `planet` (on orbit). |
| `orbit` | string | `O1` | The Orbit ID to snap to. |
| `mins` | float | 0 | Position on the track (0-60). |
| `label_header` | string | ID | Display name under the node. |
| `colors` | list | `[7, 8]` | `[Outer, Inner]` color IDs from `NODE_COLORS`. |
| `url` | string | `""` | Hyperlink for click-redirection. |

### Links (`galaxy_links`)

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `source` | string | **Req** | Starting Node ID. |
| `target` | string | **Req** | Ending Node ID. |
| `type` | string | `line` | `line` (straight) or `arc` (curved). |
| `bend` | float | 0.2 | Curve intensity (Positive: Clockwise, Negative: CCW). |
| `style` | string | `solid` | `solid`, `dash`, `dot`. |
| `url` | string | `""` | Hyperlink for link-click redirection. |

---

## 3. Example Use Cases

### Use Case A: Hub and Spoke (Standard Circle)

Perfect for a central data center connecting to multiple remote branches.

```python
orbits = [{"id": "DC_RING", "type": "circle", "rx": 200}]
nodes = {
    "HUB": {"node_type": "sun", "label_header": "CORE-DC"},
    "SITE-1": {"orbit": "DC_RING", "mins": 0, "label_header": "Site North"},
    "SITE-2": {"orbit": "DC_RING", "mins": 20, "label_header": "Site SE"},
    "SITE-3": {"orbit": "DC_RING", "mins": 40, "label_header": "Site SW"}
}
links = [
    {"source": "HUB", "target": "SITE-1", "type": "line"},
    {"source": "HUB", "target": "SITE-2", "type": "line"},
    {"source": "HUB", "target": "SITE-3", "type": "line"}
]

```

### Use Case B: Redundant Ring (Triangle with Arcs)

Demonstrates redundant paths where straight lines would overlap. Use `arc` with `bend` to separate "Primary" and "Secondary" paths.

```python
orbits = [{"id": "TRI", "type": "triangle", "rx": 200}]
nodes = {
    "R1": {"orbit": "TRI", "mins": 0, "label_header": "Router 1"},
    "R2": {"orbit": "TRI", "mins": 20, "label_header": "Router 2"},
    "R3": {"orbit": "TRI", "mins": 40, "label_header": "Router 3"}
}
links = [
    # Primary Ring (Clockwise Bend)
    {"source": "R1", "target": "R2", "type": "arc", "bend": 0.2, "colors": [5,5]},
    {"source": "R2", "target": "R3", "type": "arc", "bend": 0.2, "colors": [5,5]},
    {"source": "R3", "target": "R1", "type": "arc", "bend": 0.2, "colors": [5,5]},
    # Secondary Ring (Counter-Clockwise Bend, Dashed)
    {"source": "R1", "target": "R2", "type": "arc", "bend": -0.2, "style": "dash", "colors": [1,1]},
]

```

### Use Case C: Data Center Rack (Square Absolute Snap)

Uses a square orbit to represent a rack or a building boundary.

```python
orbits = [{"id": "RACK", "type": "square", "rx": 250}]
nodes = {
    # Corner Snapping (7.5, 22.5, 37.5, 52.5)
    "TOP_L": {"orbit": "RACK", "mins": 52.5, "label_header": "Corner NW"},
    "TOP_R": {"orbit": "RACK", "mins": 7.5, "label_header": "Corner NE"},
    # Edge Snapping (0, 15, 30, 45)
    "MID_T": {"orbit": "RACK", "mins": 0, "label_header": "Top Middle"}
}
links = [
    {"source": "TOP_L", "target": "TOP_R", "type": "line"}
]

```

---

## 4. Implementation Helper (UI Class)

To render these in Streamlit and handle the debugging:

```python
# Render the chart
self.drawer.show_topology(nodes, orbits, links, "my_topo_id", key_prefix="unique_chart_1")

# Show raw data inspection (Toggleable)
UI.display_topology_debug(nodes, orbits, links, key_prefix="debug_chart_1")

```

---

## 5. Color Palette Reference (`NODE_COLORS`)

| ID | Color | Usage Suggestion |
| --- | --- | --- |
| `1, 2` | Red | Critical / Down / Core |
| `3, 4` | Amber | Warning / Distribution |
| `5, 6` | Green | Online / Access |
| `7, 8` | Blue | Management / Info |

---

Would you like me to add a section on how to dynamically generate these JSON structures from a SQL database or a CSV file?