# builder_engine.py

import json
import os
import random

# Import everything needed from our new modules
from .config_and_utils import (
    GLOBAL_CONFIG, ALL_LINKS, ORBIT_BASE_VALUE, ORBIT_SPACING_INCREMENT, 
    get_input, get_int_input, get_float_input, get_random_color
)
from .data_structures import (
    create_moon, create_planet, create_asteroid_belt, create_star_system, create_galaxy, 
    create_orbit_structure, create_link, create_info_link
)

# --- GLOBAL LINK FUNCTIONS (MUST append to ALL_LINKS list) ---

def generate_orbital_links(planets_in_orbit, link_type='arc', color='orange'):
    """Generates links connecting all planets in a shared orbit cyclically."""
    if len(planets_in_orbit) > 1:
        planet_ids = [p['id'] for p in planets_in_orbit]
        
        for i in range(len(planet_ids)):
            id_a = planet_ids[i]
            id_b = planet_ids[(i + 1) % len(planet_ids)]
            
            link = create_link(
                id_a=id_a,
                id_b=id_b,
                link_type=link_type,
                size='xs',
                color=color,
                style='dash'
            )
            ALL_LINKS.append(link)

def generate_p2p_links(source_id, target_id):
    """Generates a point-to-point link (line)."""
    link = create_link(
        id_a=source_id,
        id_b=target_id,
        link_type='line',
        size='s',
        color=get_random_color(link=True),
        style='solid'
    )
    ALL_LINKS.append(link)

# --- INPUT AND PROCESSING LOGIC ---

def get_orbit_config_input(tier):
    """Prompts the user for the complex orbit definition."""
    # ... (Implementation remains as in the previous step)
    
    print(f"\n  --- Configuring Orbit Tier {tier} Shape and Dynamics ---")
    
    valid_shapes = ["circle", "ellipse", "square", "rectangle", "pentagon", "hexagon", "heptagon", "octagon", "nonagon", "decagon", "triangle"]
    shape = ""
    while shape not in valid_shapes:
        shape = get_input("  Orbit Shape (e.g., circle, ellipse, triangle, rectangle, pentagon): ").lower()
        if shape not in valid_shapes:
            print(f"  ❌ Invalid shape. Choose one of: {', '.join(valid_shapes)}")
            
    # Radius Parameters Input
    radius_params = []
    default_radius = ORBIT_BASE_VALUE + (tier-1)*ORBIT_SPACING_INCREMENT
    
    if shape in ["circle", "square", "pentagon", "hexagon", "heptagon", "octagon", "nonagon", "decagon"]:
        radius = get_float_input(f"  Radius/Side Length (e.g., {default_radius})", default=default_radius)
        radius_params.append(radius)
    elif shape == "ellipse" or shape == "rectangle":
        r1 = get_float_input(f"  Width Radius (e.g., {default_radius})", default=default_radius)
        r2 = get_float_input("  Height Radius", default=r1 * 0.5)
        radius_params.extend([r1, r2])
    elif shape == "triangle":
        r1 = get_float_input("  Side 1 (Base length)", default=default_radius)
        r2 = get_float_input("  Side 2 (Left length)", default=default_radius)
        r3 = get_float_input("  Side 3 (Right length)", default=default_radius)
        radius_params.extend([r1, r2, r3])

    direction = get_input("  Orbit Direction (clockwise/anticlockwise)", default='clockwise')
    speed_sec = get_float_input("  Orbital Speed (seconds per full orbit, 0 for static)", default=3.0)
    
    axis_clock = None
    if GLOBAL_CONFIG["visual_mode"] == "3D":
        axis_clock = get_float_input("  Orbit Axis (0-60 mins clock) to define plane tilt", default=0.0)
    
    return create_orbit_structure(shape, radius_params, direction, speed_sec, axis_clock, GLOBAL_CONFIG["visual_mode"])


def process_orbital_group(objects_raw, starting_offset):
    """Calculates even angular spacing for a group of objects."""
    num_objects = len(objects_raw)
    if num_objects == 0:
        return []

    angular_increment = 360.0 / num_objects
    
    for i, obj in enumerate(objects_raw):
        obj['drawing_offset_angle'] = starting_offset + (i * angular_increment)
    
    return objects_raw


def build_moons_procedural(planet_id, planet_name):
    """Builds moons for a given planet using the new simple ID schema."""
    
    moon_orbit_structure = create_orbit_structure(shape="circle", radius_params=[25.0], direction="anticlockwise", speed_sec=0.5)

    print(f"\n  --- Moons for {planet_name} ---")
    num_moons = get_int_input("  How many Moons does this planet have?", min_val=0)
    
    moons_raw = []
    for i in range(1, num_moons + 1):
        # NEW ID SCHEMA: Parent ID + -m + counter
        moon_id = f"{planet_id}-m{i}" 

        moons_raw.append({
            'name': f"Moon-{planet_name}-{i}",
            'id': moon_id,
            'orbit_definition': moon_orbit_structure,
            'is_visible': get_input("  Moon visibility? (true/false)", default='true'),
        })
        
        # P2P Planet to Moon link is deliberately skipped (structural/info relationship)

    moons_with_angles = process_orbital_group(moons_raw, 0.0) # Moons start offset 0.0

    final_moons = [
        create_moon(m['name'], m['id'], m['orbit_definition'], m['drawing_offset_angle'], m['is_visible'])
        for m in moons_with_angles
    ]
    return final_moons


def build_star_system_procedural(star_index, star_id):
    """Generates the planets, belts, and links for a single star system."""
    
    print(f"\n=======================================================")
    print(f"     BUILDING STAR SYSTEM {star_id}")
    print(f"=======================================================")

    # --- INPUTS ---
    system_axis_clock = None
    if GLOBAL_CONFIG["visual_mode"] == "3D":
        system_axis_clock = get_float_input("  Star System Orbital Plane Axis (0-60 mins clock)", default=0.0)
    
    num_orbits = get_int_input("Number of distinct orbit tiers (e.g., 3)?")
    planet_visibility = get_input("Should ALL planets in this system be visible? (y/n)", default='y').lower() == 'y'
    moons_required = get_input("Does the first planet in each orbit have moons? (y/n)", default='y').lower() == 'y'
    link_orbit = get_input("Link all planets in an orbit with an arc? (y/n)", default='y').lower() == 'y'
    num_stars = get_int_input("Number of Stars in this Star System (1 for single, 2 for binary)?", min_val=1, max_val=2)
    
    # 2. Collect Orbit and Planet configurations
    orbit_config_list = []
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
    global_planet_counter = 1
    system_starting_offset = 0.0 # Can be prompted for in advanced versions

    for tier, config in enumerate(orbit_config_list):
        orbit_structure = config[0]
        num_planets_in_orbit = config[1]
        has_belt_after = config[2]
        
        planets_in_orbit_raw = []
        
        for i in range(num_planets_in_orbit):
            # NEW ID SCHEMA: Star ID + -p + planet_counter
            planet_id = f"{star_id}-p{global_planet_counter}"
            planet_name = f"Planet-S{star_index}-P{global_planet_counter}"
            has_moons = moons_required and (i == 0) # Only the first planet gets moons

            planets_in_orbit_raw.append({
                'name': planet_name,
                'id': planet_id,
                'orbit_definition': orbit_structure,
                'has_moons': has_moons,
                'is_visible': planet_visibility,
            })
            global_planet_counter += 1
            
            # Link Star to Planet
            generate_p2p_links(star_id, planet_id)

        planets_with_angles = process_orbital_group(planets_in_orbit_raw, system_starting_offset)
        
        if link_orbit:
            # Add info link for organization
            ALL_LINKS.append(create_info_link(f"Orbital Arc Links (Orbit {tier+1})"))
            generate_orbital_links(planets_with_angles)

        for raw_p in planets_with_angles:
            final_planet = create_planet(
                raw_p['name'], raw_p['id'], raw_p['orbit_definition'], 
                raw_p['drawing_offset_angle'], raw_p['is_visible']
            )
            if raw_p['has_moons']:
                final_planet['moons'] = build_moons_procedural(raw_p['id'], raw_p['name'])
            
            all_objects.append(final_planet)

        # --- Generate Asteroid Belt ---
        if has_belt_after:
            belt_id = f"{star_id}-b{tier+1}"
            belt_name = f"Belt-S{star_index}-B{tier+1}"
            
            belt_radius = orbit_structure["radius_params"][0] + (ORBIT_SPACING_INCREMENT / 2)
            
            belt_orbit = create_orbit_structure(shape="circle", radius_params=[belt_radius], direction="clockwise", speed_sec=0.0)
            
            new_belt = create_asteroid_belt(belt_name, belt_id, belt_orbit)
            all_objects.append(new_belt) 
            
            # Link the belt (Ring Link)
            ALL_LINKS.append(create_link(id_a=belt_id, id_b=belt_id, link_type='arc', size='m', color='gray', style='double-dash'))

    # --- Binary Stars ---
    if num_stars == 2:
        star_b_id = f"{star_id}-s2"
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
        generate_p2p_links(star_id, star_b_id) # Link Star A to Star B

    # --- Star/Moon Influence Links ---
    all_moons = [obj for p in all_objects if p['type'] == 'Planet' for obj in p.get('moons', [])]

    if all_moons:
        ALL_LINKS.append(create_info_link("Influence Links: Star to Moons"))
        for moon in all_moons:
            ALL_LINKS.append(create_link(id_a=star_id, id_b=moon['id'], link_type='influence', size='xs', color='cyan', style='dash'))

    return all_objects, system_axis_clock


def main_builder():
    """Main function to build the entire Galaxy model."""
    
    # 1. Reset Global State for a clean run
    ALL_LINKS.clear()
    
    print("="*50)
    print(" COSMIC FORGE MODEL BUILDER ")
    print("="*50)
    
    # --- GLOBAL CONFIGURATION INPUT ---
    print("\n--- GLOBAL VISUALIZATION SETTINGS ---")
    GLOBAL_CONFIG["visual_mode"] = get_input("Visualization Mode (2D/3D)", default='2D').upper()
    GLOBAL_CONFIG["angle_mode"] = get_input("Angle Mode (360_deg/60_clock)", default='360_deg').lower()

    # 1. Define the Galaxy
    galaxy_id = "g0"
    galaxy_name = get_input("Galaxy Name", default="The Cosmic Forge Galaxy")
    
    # 2. Get number of star systems
    num_systems = get_int_input("How many Star Systems/Grids should be generated?")
    
    print("\nStarting generation of star systems...")

    # 3. Generate Star Systems
    star_systems_list = []
    system_spacing_increment = 360.0 / num_systems
    
    ALL_LINKS.append(create_info_link("Global P2P Links: Galaxy to Star Systems"))
    
    for i in range(1, num_systems + 1):
        # NEW ID SCHEMA: s + index
        star_id = f"s{i}"
        system_angle = 0.0 + ((i - 1) * system_spacing_increment)
        
        star_system_objects, system_axis_clock = build_star_system_procedural(i, star_id)
        
        star_system = create_star_system(i, star_id, system_angle, f"Grid-{i}", system_axis_clock)
        star_system['planets'] = star_system_objects 
        
        generate_p2p_links(galaxy_id, star_id)
        star_systems_list.append(star_system)

    galaxy_model = create_galaxy(galaxy_name, galaxy_id, starting_offset_angle=0.0, global_config=GLOBAL_CONFIG)
    galaxy_model['constellations'] = star_systems_list
    galaxy_model['links'] = ALL_LINKS

    return galaxy_model

# --- 4. EXECUTION AND OUTPUT ---
# This section assumes builder_engine.py is the main script executed

if __name__ == "__main__":
    
    final_model = main_builder()
    
    output_filename = f"{final_model.get('name', 'Cosmic_Model').replace(' ', '_')}_model.json"
    
    # Write to JSON file
    try:
        # Check if the modules are being run correctly from a package structure
        if not os.path.exists("./__init__.py"):
             print("\n⚠️ WARNING: Consider structuring files into a Python package (e.g., placing them in a directory with an empty __init__.py).")
             
        with open(output_filename, 'w') as f:
            json.dump(final_model, f, indent=4)
        
        print("\n" + "="*50)
        print("✅ MODEL CREATION SUCCESSFUL!")
        print(f"File saved to: **{os.path.abspath(output_filename)}**")
        print(f"Model generated with {len(final_model['constellations'])} star systems and {len(final_model['links'])} links.")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ ERROR saving JSON file: {e}")