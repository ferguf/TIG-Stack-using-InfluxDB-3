# --- 2. DATA STRUCTURE GENERATORS (Revised for Simple IDs) ---

# IDs are now passed from the calling function, they are not generated here.
# Example: parent_id = "s1-p1"

def create_moon(name, object_id, orbit_structure, drawing_offset_angle, is_visible):
    """Creates a dictionary for a Moon."""
    # ... (rest of function body)
    return {
        "id": object_id, # e.g., "s1-p1-m1"
        "name": name,
        "type": "Moon",
        "orbital_value": orbit_structure, 
        # ... (rest of moon properties)
        "url": f"https://model.com/moon/{object_id}" 
    }

def create_planet(name, object_id, orbit_structure, drawing_offset_angle, is_visible):
    """Creates a dictionary for a Planet."""
    # ... (rest of function body)
    return {
        "id": object_id, # e.g., "s1-p1"
        "name": name,
        "type": "Planet",
        "orbital_value": orbit_structure, 
        # ... (rest of planet properties)
        "moons": [],
        "url": f"https://model.com/planet/{object_id}"
    }

def create_star_system(index, object_id, starting_offset_angle, star_grid, system_axis_clock=None):
    """Creates a dictionary for a Star System (Star and its planets)."""
    # ... (rest of function body)
    star_system = {
        "id": object_id, # e.g., "s1"
        "name": f"StarSystem-{index}",
        "type": "StarSystem",
        # ... (rest of star system properties)
        "planets": [],
        "url": f"https://model.com/star/{object_id}"
    }
    return star_system

def create_galaxy(name, object_id, starting_offset_angle):
    """Creates the root dictionary for a Galaxy."""
    # The Galaxy ID can remain a simple fixed string or UUID if desired, but we'll use a fixed string here.
    return {
        "id": object_id, # e.g., "g0"
        "name": name,
        # ... (rest of galaxy properties)
    }

# --- 3. DYNAMIC GENERATION LOGIC / HELPER FUNCTIONS (Revised for ID generation) ---

def build_moons_procedural(planet_id, planet_name):
    """Asks for moon count and generates moon objects for a single planet."""
    # ... (input logic)
    
    moons_raw = []
    for i in range(1, num_moons + 1):
        # NEW ID SCHEMA: Parent ID + -m + counter
        moon_id = f"{planet_id}-m{i}" 

        moons_raw.append({
            'name': f"Moon-{planet_name}-{i}",
            'id': moon_id,
            # ... (rest of moon properties for processing)
        })
        # Generate P2P link (Line) from Planet to Moon (This is disallowed by previous constraint)
        # We will not generate a P2P link here as per the last constraint.
        
        # NOTE: If Star->Moon Influence links are desired, they must be generated 
        # later in build_star_system_procedural where the Star ID is known.

    # ... (rest of moon processing)

    final_moons = [
        create_moon(m['name'], m['id'], m['orbit_definition'], m['drawing_offset_angle'], m['is_visible'])
        for m in moons_with_angles
    ]
    return final_moons


def build_star_system_procedural(star_index, star_id):
    """Generates the planets, belts, and links for a single star system."""
    # ... (input logic)
    
    planet_counter = 1
    # ...
    
    for tier, config in enumerate(orbit_config_list):
        # ...
        for i in range(num_planets_in_orbit):
            # NEW ID SCHEMA: Star ID + -p + planet_counter
            planet_id = f"{star_id}-p{planet_counter}" 
            planet_name = f"Planet-S{star_index}-P{planet_counter}"
            
            # ... (append to planets_in_orbit_raw)
            planet_counter += 1
            
            # Generate P2P link (Line) from Star to Planet
            generate_p2p_links(star_id, planet_id) 

        # ... (asteroid belt generation)
        if has_belt_after:
            # NEW ID SCHEMA: Star ID + -b + tier index
            belt_id = f"{star_id}-b{tier+1}"
            belt_name = f"Belt-S{star_index}-B{tier+1}"
            
            # ... (create and link belt)

    # --- Binary Stars ---
    if num_stars == 2:
        # NEW ID SCHEMA: Star ID + -s2
        star_b_id = f"{star_id}-s2"
        star_b_name = f"StarSystem-{star_index}-B"
        
        # ... (create star_b_obj and link stars)

    # --- Star/Moon Influence Links ---
    # ... (logic remains the same, but uses the new IDs which are now sequential)

    return all_objects, system_axis_clock


def main_builder():
    """Main function to build the entire Galaxy model."""
    # ...
    
    # 1. Define the Galaxy
    galaxy_id = "g0" # Fixed ID for root
    galaxy_model = create_galaxy(galaxy_name, galaxy_id, starting_offset_angle=0.0)

    # ... (input for num_systems)
    
    for i in range(1, num_systems + 1):
        # NEW ID SCHEMA: s + index
        star_id = f"s{i}"
        
        # ... (call build_star_system_procedural)
        
        # Create the star system object
        star_system = create_star_system(i, star_id, system_angle, f"Grid-{i}", system_axis_clock)
        
        # Generate P2P link (Line) from Galaxy to Star System
        generate_p2p_links(galaxy_id, star_id)
        # ...

    return galaxy_model