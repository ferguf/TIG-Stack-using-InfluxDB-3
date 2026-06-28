import math
import re
import base64
import os

# --- GALILEO SDK IMPORTS ---
from src.galileo.galileo_taxonomy import (
    get_role_and_num,
    get_layout_radii,
    get_role_priority,
    CORE_ROLES,
    PRIMARY_EDGE_ROLES
)

# =============================================================================
# 1. PNG images import for templates (converted to Base64 for inline use)
# =============================================================================

def get_base64_image(image_path):
    """
    Converts a local image file to a Base64 data URI.
    Returns None if the file is not found or fails to encode.
    """
    if not os.path.exists(image_path):
        return None  
        
    try:
        with open(image_path, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode()
        return f"data:image/png;base64,{encoded_string}"
    except Exception as e:
        print(f"Error encoding image {image_path}: {e}")
        return None

# =============================================================================
# 1. HELPERS & SEQUENTIAL ENGINE
# =============================================================================

def get_node_number(name):
    """Extracts numbers from device names for deterministic sorting (e.g., 'VAR12' -> 12)."""
    nums = re.findall(r'\d+', str(name))
    return int(nums[0]) if nums else 999

def get_sequential_node_data(nodes):
    """
    Groups nodes by role and assigns sequential indices for 'Zipper' layouts.
    Handles both dict and list inputs.
    """
    if isinstance(nodes, list):
        nodes_dict = {n.get("device_name", str(i)): n for i, n in enumerate(nodes)}
    else:
        nodes_dict = nodes

    groups = {
        "VAR_LOW": [], "VAR_HIGH": [], "SDR": [], 
        "ES": [], "RR": [], "OTHER": []
    }

    for nid, attrs in nodes_dict.items():
        name = str(attrs.get("label_header", attrs.get("device_name", nid))).upper()
        role = str(attrs.get("device_role", "")).upper()
        num = get_node_number(name)
        
        search_str = f"{name} {role}"
        if "SDR" in search_str: groups["SDR"].append(nid)
        elif "ES" in search_str: groups["ES"].append(nid)
        elif "RR" in search_str: groups["RR"].append(nid)
        elif "VAR" in search_str:
            if num < 30: groups["VAR_LOW"].append(nid)
            else: groups["VAR_HIGH"].append(nid)
        else: groups["OTHER"].append(nid)

    node_data = {}
    for group_key, nids in groups.items():
        nids.sort(key=lambda x: get_node_number(nodes_dict[x].get("label_header", "")))
        for idx, nid in enumerate(nids):
            node_data[nid] = {
                "pos_idx": idx,
                "is_odd": (idx + 1) % 2 != 0,
                "pair_idx": idx // 2
            }
    return node_data

# =============================================================================
# 2. DYNAMIC REGISTRY CLASS
# =============================================================================

class LayoutRegistry:
    templates = {}
    defaults = {"INTERCITY": "Beck Classic", "POP": "Galileo Universe"}

    @classmethod
    def register(cls, name, mode="POP", desc="", is_default=False, is_nodes_only=False):
        def wrapper(func):
            mode_upper = mode.upper()
            cls.templates[name] = {
                "func": func, 
                "mode": mode_upper, 
                "desc": desc, 
                "name": name,
                "is_nodes_only": is_nodes_only 
            }
            if is_default: 
                cls.defaults[mode_upper] = name
            return func
        return wrapper

# =============================================================================
# 2. THE PRIMARY ENGINE: GALILEO UNIVERSE (Default)
# =============================================================================

@LayoutRegistry.register("Galileo Universe", mode="POP", desc="Snaps nodes to Square/Triangle/Circle orbits", is_default=True)
def apply_galileo_universe(nodes, orbits_list=[]):
    import math
    pos_cache = {}
    
    orb_map = {str(o["id"]): o for o in orbits_list} if orbits_list else {}

    for nid, attrs in nodes.items():
        oid = str(attrs.get("orbit", "O1"))
        orb = orb_map.get(oid, {"rx": 250, "ry": 250, "type": "circle"})
        
        rx, ry = float(orb.get("rx", 250)), float(orb.get("ry", orb.get("rx", 250)))
        otype = str(orb.get("type", "circle")).lower()
        
        mins = float(attrs.get("mins", 0))
        theta_rad = math.radians(90 - (mins * 6))
        cos_t, sin_t = math.cos(theta_rad), math.sin(theta_rad)

        if otype in ["square", "rectangle"]:
            scale = min(1/abs(cos_t) if cos_t != 0 else 9e9, 
                        1/abs(sin_t) if sin_t != 0 else 9e9)
            nx, ny = rx * cos_t * scale, ry * sin_t * scale

        elif otype == "triangle":
            nx, ny = rx * cos_t, ry * sin_t

        else: 
            nx, ny = rx * cos_t, ry * sin_t

        if str(attrs.get("node_type", "")).lower() == "sun":
            nx, ny = 0.0, 0.0

        pos_cache[str(nid).lower()] = (nx, ny)
        
    return pos_cache

# =============================================================================
# 3. INTERCITY TEMPLATES (Backbone)
# =============================================================================

LayoutRegistry.templates["Geographic"] = {
    "func": None, "mode": "INTERCITY", "desc": "USA Geographic Projection", "name": "Geographic"
}

@LayoutRegistry.register("Beck", mode="INTERCITY", desc="Logical Backbone (X/Y Mapping)")
def apply_beck_layout(nodes):
    pos_cache = {}
    node_iterable = nodes if isinstance(nodes, dict) else {n.get("location_name", str(i)): n for i, n in enumerate(nodes)}
    
    for nid, attrs in node_iterable.items():
        x = attrs.get("location_x", attrs.get("x", 0))
        y = attrs.get("location_y", attrs.get("y", 0))
        pos_cache[str(nid)] = (float(x), float(y))
    return pos_cache

# =============================================================================
# 4. POP TEMPLATES (Internal & Logical)
# =============================================================================

@LayoutRegistry.register("Backbone Layout", mode="BACKBONE", desc="Radar Concentric Transport", is_default=False)
def apply_backbone_layout(nodes):
    import math
    import re
    
    def _get_pop(hostname):
        h = str(hostname).strip().upper()
        if '.' in h:
            parts = h.split('.')
            if len(parts) > 1: return re.sub(r'\d+$', '', parts[1]) 
        if '-' in h:
            return re.sub(r'\d+$', '', h.split('-')[0])
        return h

    def _get_clock_xy(minute, radius):
        angle_radians = minute * (2 * math.pi / 60)
        nx = radius * math.sin(angle_radians)
        ny = radius * math.cos(angle_radians)
        return nx, ny

    pop_counts = {}
    for attrs in nodes.values():
        name = str(attrs.get("label_header", "")).upper()
        p = _get_pop(name)
        if p: pop_counts[p] = pop_counts.get(p, 0) + 1
            
    current_pop_base = max(pop_counts, key=pop_counts.get) if pop_counts else "UNKNOWN"

    local_max_gen = {r: 0 for r in CORE_ROLES}
    remote_groups = {r: [] for r in CORE_ROLES}
    remote_groups['OTHER'] = []
    local_nodes = []
    
    for nid, attrs in nodes.items():
        name = str(attrs.get("label_header", nid)).upper()
        role, num = get_role_and_num(name)
        node_pop = _get_pop(name)
        
        is_local = (current_pop_base in node_pop or node_pop in current_pop_base)
        
        if is_local:
            local_nodes.append((nid, role, num))
            if role in local_max_gen:
                local_max_gen[role] = max(local_max_gen[role], num)
        else:
            if role in remote_groups:
                remote_groups[role].append(nid)
            else:
                remote_groups['OTHER'].append(nid)

    pos_cache = {}

    for nid, role, num in local_nodes:
        if role in CORE_ROLES:
            radius, _ = get_layout_radii(role, layout_type="BACKBONE")
            max_gen = local_max_gen.get(role, 1)
            
            if num == 1: minute = 10
            elif num == 2: minute = 50
            elif num == 3: minute = 20 if max_gen > 4 else 15
            elif num == 4: minute = 40 if max_gen > 4 else 45
            elif num == 5: minute = 15
            elif num == 6: minute = 45
            else: minute = (num * 7) % 60 
                
        else:
            radius, _ = get_layout_radii(role, layout_type="BACKBONE")
            minute = (num * 11) % 60
            
        nx, ny = _get_clock_xy(minute, radius)
        pos_cache[nid.lower()] = (nx, ny)
        
    all_remote_nodes = []
    for role_key, nids in remote_groups.items():
        all_remote_nodes.extend(nids)
        
    total_remote = len(all_remote_nodes)
    if total_remote > 0:
        all_remote_nodes = sorted(all_remote_nodes)
        
        for i, nid in enumerate(all_remote_nodes):
            name = str(nodes[nid].get("label_header", nid)).upper()
            role, _ = get_role_and_num(name)
            
            _, base_radius = get_layout_radii(role, layout_type="BACKBONE")
            
            if total_remote == 1:
                minute = 30 
                current_radius = base_radius
            else:
                minute = 5 + (i * (50 / (total_remote - 1)))
                if total_remote > 10:
                    current_radius = base_radius if i % 2 == 0 else (base_radius + 30)
                else:
                    current_radius = base_radius
                
            nx, ny = _get_clock_xy(minute, current_radius)
            pos_cache[nid.lower()] = (nx, ny)
            
    return pos_cache

@LayoutRegistry.register("Edge Layout", mode="EDGE", desc="Universal Edge Distribution", is_default=False)
def apply_edge_layout(nodes):
    import math

    def _get_clock_xy(minute, radius):
        angle_radians = minute * (2 * math.pi / 60)
        nx = radius * math.sin(angle_radians)
        ny = radius * math.cos(angle_radians)
        return nx, ny

    core_nodes = []
    edge_nodes = []
    
    for nid, attrs in nodes.items():
        name = str(attrs.get("label_header", nid)).upper()
        role, num = get_role_and_num(name)
        
        if role in CORE_ROLES:
            core_nodes.append(nid)
        else:
            edge_nodes.append(nid)

    pos_cache = {}

    core_nodes = sorted(core_nodes)
    core_count = len(core_nodes)
    
    for i, nid in enumerate(core_nodes):
        name = str(nodes[nid].get("label_header", nid)).upper()
        role, _ = get_role_and_num(name)
        radius, _ = get_layout_radii(role, layout_type="EDGE")

        if core_count == 1: 
            minute = 0
        elif core_count == 2: 
            minute = 15 if i == 0 else 45
        elif core_count == 3: 
            minutes = [15, 45, 0]
            minute = minutes[i]
        elif core_count == 4:
            minutes = [10, 50, 20, 40]
            minute = minutes[i]
        else:
            span = 30
            step = span / (core_count - 1)
            minute = (45 + (i * step)) % 60
            
        nx, ny = _get_clock_xy(minute, radius)
        pos_cache[nid.lower()] = (nx, ny)
        
    edge_nodes = sorted(edge_nodes)
    edge_count = len(edge_nodes)
    
    for i, nid in enumerate(edge_nodes):
        name = str(nodes[nid].get("label_header", nid)).upper()
        role, _ = get_role_and_num(name)
        
        _, base_radius = get_layout_radii(role, layout_type="EDGE")
        
        if edge_count == 1:
            minute = 30 
            current_radius = base_radius
        else:
            minute = 5 + (i * (50 / (edge_count - 1)))
            if edge_count > 10:
                current_radius = base_radius if i % 2 == 0 else (base_radius + 30)
            else:
                current_radius = base_radius
                
        nx, ny = _get_clock_xy(minute, current_radius)
        pos_cache[nid.lower()] = (nx, ny)
        
    return pos_cache 

@LayoutRegistry.register("Circular", mode="POP", desc="Role-Based Radial Orbit Layout")
def apply_circular_layout(nodes):
    import math
    pos_cache = {}
    orbit_radii = {"O1": 150, "O2": 300, "O3": 450}
    rings = {"O1": [], "O2": [], "O3": []}
    
    for key, attrs in nodes.items():
        role = str(attrs.get("device_role", "")).upper()
        
        if "SDR" in role or "EBR" in role:
            rings["O1"].append(key)
        elif "VAR" in role or "EAR" in role or "EDGE" in role:
            rings["O2"].append(key)
        elif "ES" in role or "AR" in role:
            rings["O3"].append(key)
        else:
            rings["O3"].append(key)

    for orb_id, member_keys in rings.items():
        radius = orbit_radii[orb_id]
        total_members = len(member_keys)
        
        for i, key in enumerate(member_keys):
            angle_deg = (360.0 / total_members) * i if total_members > 0 else 0
            theta = math.radians(angle_deg - 90)
            nx = radius * math.cos(theta)
            ny = radius * math.sin(theta)
            pos_cache[str(key).lower()] = (nx, ny)
            
    return pos_cache

@LayoutRegistry.register("Pop Layout", mode="POP", desc="Internal Ellipsis", is_default=True)
def apply_pop_layout(nodes):
    import math
    import re
    
    pos_cache = {}
    debug_log = {}
    
    orbits = {
        1: {"rx": 180, "ry": 90},
        2: {"rx": 320, "ry": 180},
        3: {"rx": 480, "ry": 280}
    }

    counters = {"sdr": 0, "var_low": 0, "var_high": 0, "es": 0}

    sorted_keys = sorted(nodes.keys(), key=lambda x: get_node_number(nodes[x].get("label_header", "")))

    for nid in sorted_keys:
        attrs = nodes[nid]
        name = str(attrs.get("label_header", "")).upper()
        role = str(attrs.get("device_role", "")).upper()
        num = get_node_number(name)
        is_odd = (num % 2 != 0) 

        orb_id = 3
        minute = 30

        if "SDR" in name or "SDR" in role:
            orb_id = 1
            offset = (counters["sdr"] // 2) * 4
            minute = (35 - offset) if is_odd else (25 + offset)
            counters["sdr"] += 1

        elif "VAR" in name and num < 30:
            orb_id = 1
            offset = (counters["var_low"] // 2) * 3
            minute = (57 - offset) if is_odd else (3 + offset)
            counters["var_low"] += 1

        elif "VAR" in name and num >= 30:
            orb_id = 2
            offset = (counters["var_high"] // 2) * 3
            minute = (54 - offset) if is_odd else (6 + offset)
            counters["var_high"] += 1

        else:
            orb_id = 3
            offset = (counters["es"] // 2) * 5
            minute = (56 - offset) if is_odd else (4 + offset)
            counters["es"] += 1

        orb = orbits[orb_id]
        angle_rad = math.radians(((minute % 60) * 6) - 90)
        
        nx = orb["rx"] * math.cos(angle_rad)
        ny = -(orb["ry"] * math.sin(angle_rad))
        
        node_key = str(nid).lower()
        pos_cache[node_key] = (nx, ny)
        
        debug_log[name] = {
            "num": num,
            "side": "Right (Odd)" if is_odd else "Left (Even)",
            "orbit": orb_id,
            "clock_minute": minute,
            "coord": (round(nx, 2), round(ny, 2))
        }
        
    pos_cache["_debug"] = debug_log
    return pos_cache

@LayoutRegistry.register("Role Matrix", mode="POP", desc="Grid grouped by Role")
def apply_role_matrix_layout(nodes):
    pos_cache = {}
    debug_log = {}

    orbits = {
        1: {"hw": 180, "hh": 90},   
        2: {"hw": 320, "hh": 180},  
        3: {"hw": 480, "hh": 280}   
    }

    counters = {"SDR": 0, "VAR": 0, "ES": 0}

    sorted_keys = sorted(nodes.keys(), key=lambda x: get_node_number(nodes[x].get("label_header", "")))

    for nid in sorted_keys:
        attrs = nodes[nid]
        name = str(attrs.get("label_header", "")).upper()
        role = str(attrs.get("device_role", "OTHER")).upper()
        num = get_node_number(name)
        is_odd = (num % 2 != 0)

        if "SDR" in role:
            orb_id, inc = 3, 5
            offset = (counters["SDR"] // 2) * inc
            minute = (57 - offset) if is_odd else (3 + offset)
            counters["SDR"] += 1
            
        elif "VAR" in role:
            orb_id, inc = 1, 5
            offset = (counters["VAR"] // 2) * inc
            minute = (57 - offset) if is_odd else (3 + offset)
            counters["VAR"] += 1
            
        elif "ES" in role:
            orb_id, inc = 2, 5
            offset = (counters["ES"] // 2) * inc
            minute = (35 + offset) if is_odd else (25 - offset)
            counters["ES"] += 1

        else:
            orb_id, minute = 3, 0

        orb = orbits[orb_id]
        hw, hh, m = orb["hw"], orb["hh"], minute % 60
        
        if 52.5 <= m or m < 7.5: 
            if m >= 52.5:
                x = -hw + ((m - 52.5) / 7.5 * hw)
            else:
                x = (m / 7.5) * hw
            y = hh
        elif 7.5 <= m < 22.5: 
            x, y = hw, hh - ((m - 7.5) / 15 * (2 * hh))
        elif 22.5 <= m < 37.5: 
            x, y = hw - ((m - 22.5) / 15 * (2 * hw)), -hh
        else: 
            x, y = -hw, -hh + ((m - 37.5) / 15 * (2 * hh))

        pos_cache[str(nid).lower()] = (x, y)
        debug_log[name] = {
            "num": num, 
            "side": "Right" if (m <= 30) else "Left",
            "clock_minute": round(m, 1), 
            "coord": (round(x, 2), round(y, 2))
        }
        
    pos_cache["_debug"] = debug_log
    return pos_cache

@LayoutRegistry.register("Ring", mode="POP", desc="Single Orbit Ring with Uniform Spacing")
def apply_equal_spacing_ring_layout(nodes):
    import math
    pos_cache = {}
    debug_log = {}

    RADIUS = 400
    TOTAL_NODES = len(nodes)
    if TOTAL_NODES == 0:
        return {}

    angle_step = 360.0 / TOTAL_NODES
    role_priority = get_role_priority()
    
    categorized = {role: [] for role in role_priority}
    
    for nid, attrs in nodes.items():
        role = str(attrs.get("device_role", "OTHER")).upper()
        found_role = "OTHER"
        for r in role_priority:
            if r in role:
                found_role = r
                break
        categorized[found_role].append(nid)

    ordered_nids = []
    for role in role_priority:
        sorted_group = sorted(categorized[role], key=lambda x: get_node_number(nodes[x].get("label_header", "")))
        ordered_nids.extend(sorted_group)

    for i, nid in enumerate(ordered_nids):
        attrs = nodes[nid]
        name = str(attrs.get("label_header", "")).upper()
        
        current_angle_deg = 90 - (i * angle_step)
        current_angle_rad = math.radians(current_angle_deg)

        x = RADIUS * math.cos(current_angle_rad)
        y = RADIUS * math.sin(current_angle_rad)

        clock_min = ((90 - current_angle_deg) / 6.0) % 60

        node_key = str(nid).lower()
        pos_cache[node_key] = (x, y)
        
        debug_log[name] = {
            "num": get_node_number(name),
            "role": attrs.get("device_role", "OTHER"),
            "index": i,
            "angle_deg": round(current_angle_deg % 360, 1),
            "clock_minute": round(clock_min, 1),
            "coord": (round(x, 2), round(y, 2))
        }

    pos_cache["_debug"] = debug_log
    return pos_cache

@LayoutRegistry.register("Node Matrix", mode="POP", desc="Linear Grid by Role", is_nodes_only=True)
def apply_node_matrix_layout(nodes):
    pos_cache = {}
    debug_log = {}
    
    X_START = -500
    X_SPACING = 180
    Y_SPACING = 250
    
    role_groups = {}
    
    for nid, attrs in nodes.items():
        role = str(attrs.get("device_role", "OTHER")).upper()
        role_groups.setdefault(role, []).append(nid)

    role_priority = get_role_priority()
    
    sorted_roles = sorted(role_groups.keys(), 
                          key=lambda r: (role_priority.index(r) if r in role_priority else 99, r))
    
    for row_idx, role in enumerate(sorted_roles):
        role_nids = sorted(role_groups[role], 
                           key=lambda x: get_node_number(nodes[x].get("label_header", "")))
        
        y_pos = 500 - (row_idx * Y_SPACING)
        
        for col_idx, nid in enumerate(role_nids):
            name = str(nodes[nid].get("label_header", "")).upper()
            
            x_pos = X_START + (col_idx * X_SPACING)
            
            pos_cache[str(nid).lower()] = (x_pos, y_pos)
            
            debug_log[name] = {
                "role": role,
                "row": row_idx,
                "col": col_idx,
                "coord": (x_pos, y_pos)
            }
            
    pos_cache["_debug"] = debug_log
    return pos_cache

@LayoutRegistry.register("Beck Straight", mode="INTERCITY", desc="Direct Vector Backbone")
def apply_beck_straight(nodes):
    return apply_beck_layout(nodes)

@LayoutRegistry.register("Beck Classic", mode="INTERCITY")
def apply_beck_classic_layout(nodes):
    pos_cache = {}
    GRID_SIZE = 50 
    
    for n in nodes:
        raw_x = n.get("location_x", 0)
        raw_y = n.get("location_y", 0)
        
        snapped_x = round(raw_x / GRID_SIZE) * GRID_SIZE
        snapped_y = round(raw_y / GRID_SIZE) * GRID_SIZE
        
        name = str(n.get("location_name")).lower()
        pos_cache[name] = (snapped_x, snapped_y)
        
    return pos_cache

# =============================================================================
# 5. EXPORTS
# =============================================================================
LAYOUT_REGISTRY = LayoutRegistry.templates