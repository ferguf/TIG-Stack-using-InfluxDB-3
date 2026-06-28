import json
import uuid
import os
import random
from collections import defaultdict

# --- 1. CONFIGURATION AND DEFAULTS ---

VISUAL_DEFAULTS = {
    "galaxy": {"size": "xxl", "color": "random"},
    "star_system": {"size": "xxl", "color": "yellow"},
    "planet": {"size": "m", "color": "random"},
    "moon": {"size": "xs", "color": "random"},
    "asteroid_belt": {"size": "l", "color": "gray"} 
}

LINK_DEFAULTS = {
    "size": "s", 
    "color": "white",
    "style": "solid",
    "link_type": "line"
}

# --- GLOBAL CONFIGURATION (Will be prompted for in main_builder) ---
GLOBAL_CONFIG = {
    "visual_mode": "2D",
    "angle_mode": "360_deg"
}
# -------------------------------------------------------------------

DEFAULT_VISIBILITY = "true" 
RANDOM_COLORS = ["red", "green", "blue", "cyan", "magenta", "yellow"]
RANDOM_LINK_COLORS = ["red", "blue", "green", "orange"]
LINK_STYLES = ["solid", "dash", "double-dash"]
ORBIT_BASE_VALUE = 100 # Suggested starting radius for the first orbit
ORBIT_SPACING_INCREMENT = 30 # Conceptual tier spacing

ALL_LINKS = []

# --- 2. DATA STRUCTURE GENERATORS ---

def get_random_color(link=False):
    """Selects a random color from the predefined list."""
    global RANDOM_COLORS
    global RANDOM_LINK_COLORS
    
    if link:
        return random.choice(RANDOM_LINK_COLORS)
    return random.choice(RANDOM_COLORS)

def create_link(id_a, id_b, link_type="line", size=LINK_DEFAULTS["size"], color=get_random_color(link=True), style=random.choice(LINK_STYLES)):
    """Creates a dictionary for a Link."""
    # Note: LINK_DEFAULTS must be defined at the top of the script
    return {
        "id_a": id_a,
        "id_b": id_b,
        "link_type": link_type, # 'line', 'arc', or 'influence'
        "color": color,
        "size": size,
        "style": style
    }

# --- Link Generation Logic (Must be defined after create_link) ---

def generate_orbital_links(planets_in_orbit):
    """Generates 'arc' links connecting all planets in a shared orbit."""
    global ALL_LINKS
    if len(planets_in_orbit) > 1:
        planet_ids = [p['id'] for p in planets_in_orbit]
        
        for i in range(len(planet_ids)):
            id_a = planet_ids[i]
            id_b = planet_ids[(i + 1) % len(planet_ids)]
            
            link = create_link(
                id_a=id_a,
                id_b=id_b,
                link_type='arc', # Type arc for orbital links
                size='xs',
                color=get_random_color(link=True),
                style='dash'
            )
            ALL_LINKS.append(link)

def generate_p2p_links(source_id, target_id):
    """Generates a point-to-point link (line)."""
    global ALL_LINKS
    link = create_link(
        id_a=source_id,
        id_b=target_id,
        link_type='line',
        size='s',
        color=get_random_color(link=True),
        style='solid'
    )
    ALL_LINKS.append(link)


def get_random_color(link=False):
    """Selects a random color from the predefined list."""
    if link:
        return random.choice(RANDOM_LINK_COLORS)
    return random.choice(RANDOM_COLORS)

# --- Orbit Structure ---
def create_orbit_structure(shape, radius_params, direction, speed_sec, axis_clock=None):
    """Creates the complex orbit definition structure."""
    orbit = {
        "shape": shape,
        "radius_params": [float(r) for r in radius_params],
        "direction": direction,
        "speed_sec": float(speed_sec)
    }
    # Only include axis if in 3D mode
    if GLOBAL_CONFIG["visual_mode"] == "3D" and axis_clock is not None:
        orbit["axis_clock"] = float(axis_clock)
    return orbit

# --- Object Creation (Updated with ORBIT STRUCTURE) ---

def create_moon(name, object_id, orbit_structure, drawing_offset_angle, is_visible):
    """Creates a dictionary for a Moon."""
    defaults = VISUAL_DEFAULTS["moon"]
    return {
        "id": object_id,
        "name": name,
        "type": "Moon",
        "orbit_definition": orbit_structure, # NEW FIELD
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
        "orbit_definition": orbit_structure, # NEW FIELD
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
        "orbit_definition": orbit_structure, # NEW FIELD
        "drawing_offset_angle": 0.0, # Belts don't need individual offsets
        "size": defaults["size"],
        "color": defaults["color"],
        "visible": DEFAULT_VISIBILITY,
        "url": f"https://model.com/belt/{object_id}"
    }

# (The rest of the creation functions remain largely the same, but StarSystem now tracks axis)

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

def create_galaxy(name, object_id, starting_offset_angle):
    # ... (unchanged) ...
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
        "visualization_config": GLOBAL_CONFIG # ATTACH GLOBAL CONFIG HERE
    }

# --- Link Generation Logic (Unchanged) ---
# ... (all link creation and generation functions: create_link, generate_orbital_links, generate_p2p_links) ...
def generate_orbital_links(planets_in_orbit):
    """Generates 'arc' links connecting all planets in a shared orbit."""
    global ALL_LINKS
    if len(planets_in_orbit) > 1:
        # Link all planets in a cycle (P1->P2->...->PN->P1)
        planet_ids = [p['id'] for p in planets_in_orbit]
        
        for i in range(len(planet_ids)):
            id_a = planet_ids[i]
            # Wrap around to the first planet
            id_b = planet_ids[(i + 1) % len(planet_ids)]
            
            link = create_link(
                id_a=id_a,
                id_b=id_b,
                link_type='arc', # Type arc for orbital links
                size='xs', # Fixed size for orbital links
                color=get_random_color(link=True),
                style='dash' # Fixed style for orbital links
            )
            ALL_LINKS.append(link)

def generate_p2p_links(source_id, target_id):
    """Generates a point-to-point link (line)."""
    global ALL_LINKS
    link = create_link(
        id_a=source_id,
        id_b=target_id,
        link_type='line',
        size='s',
        color=get_random_color(link=True),
        style='solid'
    )
    ALL_LINKS.append(link)

# --- 3. DYNAMIC GENERATION LOGIC / HELPER FUNCTIONS ---

def get_input(prompt, default=None):
    # ... (unchanged) ...
    if default is not None:
        return input(f"{prompt} (Default: {default}): ").strip() or default
    return input(f"{prompt}: ").strip()

def get_int_input(prompt, min_val=0, max_val=999):
    # ... (unchanged) ...
    while True:
        try:
            value = int(input(f"{prompt} (Min: {min_val}): ").strip())
            if min_val <= value <= max_val:
                return value
            else:
                print(f"  ❌ Please enter a number between {min_val} and {max_val}.")
        except ValueError:
            print("  ❌ Invalid input. Please enter a whole number.")

def get_float_input(prompt, default=None):
    """Helper to get and validate a float input."""
    while True:
        try:
            value_str = get_input(prompt, default=default)
            return float(value_str)
        except ValueError:
            print("  ❌ Invalid input. Please enter a number.")

def get_orbit_config_input(tier):
    """Prompts the user for the complex orbit definition based on the new requirements."""
    print(f"\n  --- Configuring Orbit Tier {tier} Shape and Dynamics ---")
    
    # 1. Shape Input
    valid_shapes = ["circle", "ellipse", "square", "rectangle", "pentagon", "hexagon", "heptagon", "octagon", "nonagon", "decagon", "triangle"]
    shape = ""
    while shape not in valid_shapes:
        shape = get_input("  Orbit Shape (e.g., circle, ellipse, triangle, rectangle, pentagon): ").lower()
        if shape not in valid_shapes:
            print(f"  ❌ Invalid shape. Choose one of: {', '.join(valid_shapes)}")
            
    # 2. Radius Parameters Input
    radius_params = []
    if shape in ["circle", "square", "pentagon", "hexagon", "heptagon", "octagon", "nonagon", "decagon", "rectangle"]:
        # Single radius/side length
        radius = get_float_input(f"  Radius/Side Length (e.g., {ORBIT_BASE_VALUE + (tier-1)*ORBIT_SPACING_INCREMENT})", default=ORBIT_BASE_VALUE + (tier-1)*ORBIT_SPACING_INCREMENT)
        radius_params.append(radius)
    elif shape in ["ellipse", "rectangle"]:
        # Two radii (width, height)
        r1 = get_float_input(f"  Width Radius (e.g., {ORBIT_BASE_VALUE + (tier-1)*ORBIT_SPACING_INCREMENT})", default=ORBIT_BASE_VALUE + (tier-1)*ORBIT_SPACING_INCREMENT)
        r2 = get_float_input("  Height Radius", default=r1 * 0.5)
        radius_params.extend([r1, r2])
    elif shape == "triangle":
        # Three sides (base, left, right)
        r1 = get_float_input("  Side 1 (Base length)", default=100)
        r2 = get_float_input("  Side 2 (Left length)", default=100)
        r3 = get_float_input("  Side 3 (Right length)", default=100)
        radius_params.extend([r1, r2, r3])

    # 3. Direction and Speed Input
    direction = get_input("  Orbit Direction (clockwise/anticlockwise)", default='clockwise')
    speed_sec = get_float_input("  Orbital Speed (seconds per full orbit, 0 for static)", default=3.0)
    
    # 4. Axis Input (3D Mode only)
    axis_clock = None
    if GLOBAL_CONFIG["visual_mode"] == "3D":
        axis_clock = get_float_input("  Orbit Axis (0-60 mins clock) to define plane tilt", default=0.0)
    
    return create_orbit_structure(shape, radius_params, direction, speed_sec, axis_clock)

# ... (process_orbital_group remains the same, as it only uses drawing_offset_angle) ...

def build_moons_procedural(planet_id, planet_name):
    # ... (Simplified moon orbit config for now: always circle radius 0.5) ...
    # Moons will always be a small circle orbit for simplicity in this complex update
    moon_orbit_structure = create_orbit_structure(
        shape="circle", 
        radius_params=[0.5], 
        direction="clockwise", 
        speed_sec=0.5
    )

    print(f"\n  --- Moons for {planet_name} ---")
    num_moons = get_int_input("  How many Moons does this planet have?", min_val=0)
    
    # ... (rest of moon generation) ...
    
    moons_raw = []
    for i in range(1, num_moons + 1):
        moon_id = str(uuid.uuid4())
        moons_raw.append({
            'name': f"Moon-{planet_name}-{i}",
            'id': moon_id,
            'orbit_definition': moon_orbit_structure, # USE STRUCTURE
            'is_visible': DEFAULT_VISIBILITY
        })
        # Generate P2P link (Line) from Planet to Moon
        generate_p2p_links(planet_id, moon_id)

    # ... (rest of moon processing) ...
    # The 'orbital_value' used by process_orbital_group is no longer needed, 
    # but we reuse the raw structure to pass the calculated angle
    
    moons_with_angles = process_orbital_group(moons_raw, 0.0) # 0.0 is the starting offset

    final_moons = [
        create_moon(m['name'], m['id'], m['orbit_definition'], m['drawing_offset_angle'], m['is_visible'])
        for m in moons_with_angles
    ]
    return final_moons


def build_star_system_procedural(star_index, star_id):
    """Generates the planets, belts, and links for a single star system."""
    
    print(f"\n=======================================================")
    print(f"     BUILDING STAR SYSTEM {star_index}")
    print(f"=======================================================")

    # --- NEW: Star System Axis ---
    system_axis_clock = None
    if GLOBAL_CONFIG["visual_mode"] == "3D":
        system_axis_clock = get_float_input("  Star System Orbital Plane Axis (0-60 mins clock)", default=0.0)
    
    # ... (rest of config inputs: num_orbits, visibility, moons_required, link_orbit) ...
    num_orbits = get_int_input("Number of distinct orbit tiers (e.g., 3)?")
    planet_visibility = get_input("Should ALL planets in this system be visible? (y/n)", default='y').lower() == 'y'
    moons_required = get_input("Does the first planet in each orbit have moons? (y/n)", default='y').lower() == 'y'
    link_orbit = get_input("Link all planets in an orbit with an arc? (y/n)", default='y').lower() == 'y'
    num_stars = get_int_input("Number of Stars in this Star System (1 for single, 2 for binary)?", min_val=1, max_val=2)
    
    # 2. Collect Orbit and Planet configurations
    orbit_config_list = [] # Stores: [orbit_structure, num_planets, has_belt_after]
    print("\nEnter the configuration for each orbit tier:")
    for orbit_tier in range(1, num_orbits + 1):
        orbit_structure = get_orbit_config_input(orbit_tier)
        num_planets = get_int_input(f"  Orbit {orbit_tier}: Number of nodes/planets?")
        
        has_belt_after = False
        if orbit_tier < num_orbits:
            has_belt_after = get_input(f"  Include Asteroid Belt after Orbit {orbit_tier}? (y/n)", default='n').lower() == 'y'

        orbit_config_list.append([orbit_structure, num_planets, has_belt_after])

    # 3. Generate Planets and Belts
    all_objects = []
    planet_counter = 1
    system_starting_offset = 0.0

    for tier, config in enumerate(orbit_config_list):
        orbit_structure = config[0]
        num_planets_in_orbit = config[1]
        has_belt_after = config[2]
        
        current_orbit_offset = system_starting_offset 

        planets_in_orbit_raw = []
        
        # ... (planet generation, linking to star, moon check) ...
        for i in range(num_planets_in_orbit):
            planet_id = str(uuid.uuid4())
            planet_name = f"Planet-S{star_index}-P{planet_counter}"
            has_moons = moons_required and (i == 0)

            planets_in_orbit_raw.append({
                'name': planet_name,
                'id': planet_id,
                'orbit_definition': orbit_structure, # PASS STRUCTURE
                'has_moons': has_moons,
                'is_visible': planet_visibility,
            })
            planet_counter += 1
            generate_p2p_links(star_id, planet_id)

        # Apply spacing logic
        planets_with_angles = process_orbital_group(planets_in_orbit_raw, current_orbit_offset)
        
        # Orbital arc links
        if link_orbit:
            generate_orbital_links(planets_with_angles)

        # Create final planet objects and attach moons
        for raw_p in planets_with_angles:
            final_planet = create_planet(
                raw_p['name'], 
                raw_p['id'], 
                raw_p['orbit_definition'], 
                raw_p['drawing_offset_angle'], 
                raw_p['is_visible']
            )
            if raw_p['has_moons']:
                final_planet['moons'] = build_moons_procedural(raw_p['id'], raw_p['name'])
            
            all_objects.append(final_planet)

        # --- NEW: Generate Asteroid Belt ---
        if has_belt_after:
            belt_id = str(uuid.uuid4())
            belt_name = f"Belt-S{star_index}-B{tier+1}"
            
            # The belt's orbit structure: circle with a radius slightly larger than the current orbit
            # Use the first radius parameter of the next orbit, or just add the spacing increment
            belt_radius = orbit_structure["radius_params"][0] + (ORBIT_SPACING_INCREMENT / 2)
            
            belt_orbit = create_orbit_structure(
                shape="circle", 
                radius_params=[belt_radius], 
                direction="clockwise", 
                speed_sec=0.0
            )
            
            new_belt = create_asteroid_belt(belt_name, belt_id, belt_orbit)
            all_objects.append(new_belt) 
            
            # Link the belt (Ring Link)
            ALL_LINKS.append(create_link(id_a=belt_id, id_b=belt_id, link_type='arc', size='m', color='gray', style='double-dash'))

    # --- Binary Stars ---
    if num_stars == 2:
        star_b_id = str(uuid.uuid4())
        star_b_name = f"StarSystem-{star_index}-B"
        star_b_obj = {
            "id": star_b_id,
            "name": star_b_name,
            "type": "Star",
            "size": "l",
            "color": get_random_color(),
            "url": f"https://model.com/star/{star_b_id}"
        }
        all_objects.append(star_b_obj) 
        generate_p2p_links(star_id, star_b_id)

    # --- Star/Moon Influence Links ---
    all_moons = [obj for p in all_objects if p['type'] == 'Planet' for obj in p.get('moons', [])]

    for moon in all_moons:
        ALL_LINKS.append(create_link(id_a=star_id, id_b=moon['id'], link_type='influence', size='xs', color='cyan', style='dash'))

    return all_objects, system_axis_clock

def main_builder():
    """Main function to build the entire Galaxy model."""
    global ALL_LINKS 
    global GLOBAL_CONFIG
    ALL_LINKS = [] 
    
    print("="*50)
    print(" COSMIC MODEL BUILDER: ORBITAL MECHANICS & 3D CONFIG ")
    print("="*50)
    
    # --- GLOBAL CONFIGURATION INPUT ---
    print("\n--- GLOBAL VISUALIZATION SETTINGS ---")
    GLOBAL_CONFIG["visual_mode"] = get_input("Visualization Mode (2D/3D)", default='2D').upper()
    GLOBAL_CONFIG["angle_mode"] = get_input("Angle Mode (360_deg/60_clock)", default='360_deg').lower()

    # 1. Define the Galaxy
    galaxy_id = str(uuid.uuid4())
    galaxy_name = "The Procedural Galaxy"
    galaxy_model = create_galaxy(galaxy_name, galaxy_id, starting_offset_angle=0.0)

    # 2. Get number of star systems
    num_systems = get_int_input("How many Star Systems/Grids should be generated?")
    
    print("\nStarting generation of star systems...")

    # 3. Generate Star Systems
    star_systems_list = []
    system_spacing_increment = 360.0 / num_systems
    
    for i in range(1, num_systems + 1):
        star_id = str(uuid.uuid4())
        system_angle = 0.0 + ((i - 1) * system_spacing_increment)
        
        # Generate planets and get the system axis
        star_system_objects, system_axis_clock = build_star_system_procedural(i, star_id)
        
        # Create the star system object
        star_system = create_star_system(i, star_id, system_angle, f"Grid-{i}", system_axis_clock)
        star_system['planets'] = star_system_objects # Planets/Belts/Stars-B are stored here
        
        generate_p2p_links(galaxy_id, star_id)
        star_systems_list.append(star_system)

    galaxy_model['constellations'] = star_systems_list
    galaxy_model['links'] = ALL_LINKS

    return galaxy_model

# --- 4. EXECUTION AND OUTPUT ---

if __name__ == "__main__":
    
    final_model = main_builder()
    
    output_filename = f"{final_model.get('name', 'Cosmic_Model').replace(' ', '_')}_orbital_3d.json"
    
    # Write to JSON file
    try:
        with open(output_filename, 'w') as f:
            json.dump(final_model, f, indent=4)
        
        print("\n" + "="*50)
        print("✅ MODEL CREATION SUCCESSFUL!")
        print(f"File saved to: **{os.path.abspath(output_filename)}**")
        print(f"Model generated with {len(final_model['constellations'])} star systems and {len(final_model['links'])} links.")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ ERROR saving JSON file: {e}")