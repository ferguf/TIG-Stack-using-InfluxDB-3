# config_and_utils.py

import random

# --- 1. GLOBAL CONFIGURATION AND DEFAULTS ---

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

RANDOM_COLORS = ["red", "green", "blue", "cyan", "magenta", "yellow", "orange", "purple"]
RANDOM_LINK_COLORS = ["red", "blue", "green", "orange", "white", "cyan"]
LINK_STYLES = ["solid", "dash", "double-dash"]

DEFAULT_VISIBILITY = "true" 
ORBIT_BASE_VALUE = 100 
ORBIT_SPACING_INCREMENT = 30 

# GLOBAL state tracking (needs to be initialized in builder_engine)
ALL_LINKS = [] 
GLOBAL_CONFIG = {
    "visual_mode": "2D",
    "angle_mode": "360_deg"
}

# --- 2. UTILITY FUNCTIONS ---

def get_random_color(link=False):
    """Selects a random color for objects or links."""
    if link:
        return random.choice(RANDOM_LINK_COLORS)
    return random.choice(RANDOM_COLORS)

def get_input(prompt, default=None):
    """Helper to get and validate string input."""
    if default is not None:
        return input(f"{prompt} (Default: {default}): ").strip() or default
    return input(f"{prompt}: ").strip()

def get_int_input(prompt, min_val=0, max_val=999):
    """Helper to get and validate integer input."""
    while True:
        try:
            value = int(get_input(f"{prompt} (Min: {min_val})", default=min_val).strip())
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