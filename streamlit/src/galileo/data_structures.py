# data_structures.py

from .config_and_utils import VISUAL_DEFAULTS, LINK_DEFAULTS, get_random_color, DEFAULT_VISIBILITY

# --- 1. LINK STRUCTURES ---
    
def create_link(id_a, id_b, link_type="line", size=LINK_DEFAULTS["size"], color=get_random_color(link=True), style=None):
    """Creates a dictionary for a Link."""
    if style is None:
        style = LINK_DEFAULTS["style"]
    
    # Handle the 'info' structure for descriptive purposes
    if id_a is None and id_b is None and link_type == "info":
        return {"info": color} # color argument is repurposed as the info string
    
    return {
        "id_a": id_a,
        "id_b": id_b,
        "link_type": link_type, # 'line', 'arc', 'influence', or 'info'
        "color": color,
        "size": size,
        "style": style
    }


def create_info_link(description):
    """Creates a metadata object for the links array."""
    # Special call to create_link to insert an 'info' object
    return create_link(None, None, link_type="info", color=description)


# --- 2. ORBIT STRUCTURE ---

def create_orbit_structure(shape, radius_params, direction, speed_sec, axis_clock=None, visual_mode="2D"):
    """Creates the complex orbit definition structure."""
    orbit = {
        "shape": shape,
        "radius_params": [float(r) for r in radius_params],
        "direction": direction,
        "speed_sec": float(speed_sec)
    }
    if visual_mode == "3D" and axis_clock is not None:
        orbit["axis_clock"] = float(axis_clock)
    return orbit


# --- 3. OBJECT STRUCTURES ---

def create_moon(name, object_id, orbit_structure, drawing_offset_angle, is_visible):
    """Creates a dictionary for a Moon."""
    defaults = VISUAL_DEFAULTS["moon"]
    return {
        "id": object_id,
        "name": name,
        "type": "Moon",
        "orbit_definition": orbit_structure,
        "drawing_offset_angle": float(drawing_offset_angle),
        "size": defaults["size"],
        "color": get_random_color(),
        "visible": is_visible,
        "url": f"https://model.com/moon/{object_id}" 
    }

def create_planet(name, object_id, orbit_structure, drawing_offset_angle, is_visible):
    """Creates a dictionary for a Planet."""
    defaults = VISUAL_DEFAULTS["planet"]
    return {
        "id": object_id,
        "name": name,
        "type": "Planet",
        "orbit_definition": orbit_structure,
        "drawing_offset_angle": float(drawing_offset_angle),
        "size": defaults["size"],
        "color": get_random_color(),
        "visible": is_visible,
        "moons": [],
        "url": f"https://model.com/planet/{object_id}"
    }

def create_asteroid_belt(name, object_id, orbit_structure):
    """Creates a dictionary for an Asteroid Belt."""
    defaults = VISUAL_DEFAULTS["asteroid_belt"]
    return {
        "id": object_id,
        "name": name,
        "type": "AsteroidBelt",
        "orbit_definition": orbit_structure,
        "drawing_offset_angle": 0.0,
        "size": defaults["size"],
        "color": defaults["color"],
        "visible": DEFAULT_VISIBILITY,
        "url": f"https://model.com/belt/{object_id}"
    }

def create_star_system(index, object_id, starting_offset_angle, star_grid, system_axis_clock=None):
    """Creates a dictionary for a Star System (Star and its planets)."""
    defaults = VISUAL_DEFAULTS["star_system"]
    star_system = {
        "id": object_id,
        "name": f"StarSystem-{index}",
        "type": "StarSystem",
        "grid_location": star_grid,
        "starting_offset_angle": float(starting_offset_angle),
        "size": defaults["size"],
        "color": defaults["color"],
        "visible": DEFAULT_VISIBILITY,
        "planets": [],
        "url": f"https://model.com/star/{object_id}"
    }
    if system_axis_clock is not None:
        star_system["system_axis_clock"] = float(system_axis_clock)
    return star_system

def create_galaxy(name, object_id, starting_offset_angle, global_config):
    """Creates the root dictionary for a Galaxy."""
    return {
        "id": object_id,
        "name": name,
        "type": "Galaxy",
        "starting_offset_angle": float(starting_offset_angle),
        "constellations": [],
        "size": VISUAL_DEFAULTS["galaxy"]["size"],
        "color": VISUAL_DEFAULTS["galaxy"]["color"],
        "visible": DEFAULT_VISIBILITY,
        "url": f"https://model.com/galaxy/{object_id}",
        "visualization_config": global_config 
    }