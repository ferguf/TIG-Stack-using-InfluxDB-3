import re

# =============================================================================
# 1. UNIVERSAL NETWORK TAXONOMY
# Add new networks (AS209, Metro) here. The UI and renderers will automatically adapt.
# Tuples e.g., ("SDR", "SDR") represent strict topological link rules for the UI.
# =============================================================================

NETWORK_CONSTRUCTS = {
    "AS3549": {
        "Backbone": [("SDR", "SDR"), ("SDR", "SCR"), ("SCR", "CR"), ("SDR", "CR")],
        "Digital Edge": ["VAR", "ES"],
        "Legacy Edge": ["ER", "AR"],
        "Legacy GBLX Edge": ["ESP", "PR"],
        "Voice": ["EVCR"],
        "Vyvx": ["VPE"],
        "Other": [] 
    },
    "AS3356": {
        "Backbone": [("EBR", "EBR")],
        "Digital Edge": ["EAR", "EDGE", "BEAR", "BAR"],
        "Legacy Edge": ["PR", "AR"],
        "DDOS MSR": ["MSR"],
        "Route Reflectors": ["SRR", "RR", "ERR"],
        "Other": [] 
    }
}

# Automatically flatten the taxonomy to generate all known valid roles
ALL_VALID_ROLES = set()
for network, tiers in NETWORK_CONSTRUCTS.items():
    for roles in tiers.values():
        for item in roles:
            if isinstance(item, tuple):
                ALL_VALID_ROLES.update(item)
            else:
                ALL_VALID_ROLES.add(item)
ALL_VALID_ROLES.update(['AR', 'ER', 'PR', 'VAR', 'ES']) # Fallback safety net

# =============================================================================
# 2. ROLE CLASSIFICATIONS (For Math & Layout Engine)
# =============================================================================

CORE_ROLES = {'SDR', 'SCR', 'CR', 'EBR', 'SRR', 'RR', 'ERR'}
PRIMARY_EDGE_ROLES = {'VAR', 'ES', 'EAR', 'EDGE', 'BEAR', 'BAR'}

# =============================================================================
# 3. UNIFIED ICON MAPPING
# =============================================================================

ICON_MAP = {
    "SDR": "templates/png/SDR.png", "SCR": "templates/png/SCR.png", "CR": "templates/png/CR.png",
    "VAR": "templates/png/VAR.png", "ES": "templates/png/ES.png",
    "ER": "templates/png/ER.png", "AR": "templates/png/AR.png", 
    "ESP": "templates/png/ESP.png", "PR": "templates/png/PR.png",
    "EVCR": "templates/png/EVCR.png", "VPE": "templates/png/VPE.png",
    "EDGE": "templates/png/EDGE.png", "RR": "templates/png/RR.png",
    "EBR": "templates/png/EBR.png", "EAR": "templates/png/EAR.png", 
    "BEAR": "templates/png/EAR.png", "SRR": "templates/png/RR.png", "ERR": "templates/png/RR.png",
    "BAR": "templates/png/EAR.png", "MSR": "templates/png/OTHER.png", "MAR": "templates/png/OTHER.png"
}

# =============================================================================
# 4. UNIVERSAL PARSING METHODS
# =============================================================================

def extract_role(hostname: str) -> str:
    """
    Safely extracts device roles from hostnames against the known taxonomy.
    Dynamically handles standard (ROLE.CITY) and legacy (CITY-ROLE) naming conventions.
    """
    import re
    h = str(hostname).upper().strip()
    
    # 1. Tokenize the hostname by dots and dashes
    parts = re.split(r'[\.-]', h)
    
    # 2. Check every chunk to see if it starts with a known valid role
    for part in parts:
        match = re.match(r'^([A-Z]+)', part)
        if match:
            alpha_chunk = match.group(1)
            if alpha_chunk in ALL_VALID_ROLES:
                return alpha_chunk
                
    # 3. Fallback: Check if any valid role exists as a substring anywhere in the hostname
    # We sort by length descending so 'BEAR' matches before 'AR'
    for role in sorted(list(ALL_VALID_ROLES), key=len, reverse=True):
        if role in h:
            return role
            
    return "OTHER"

def get_role_and_num(hostname: str):
    """Returns a tuple (ROLE, NUMBER) for deterministic sequential ordering."""
    h = str(hostname).upper().strip()
    parts = re.split(r'[\.-]', h)
    for part in parts:
        match = re.match(r'^([A-Z]+)(\d*)', part)
        if match:
            role_str = match.group(1)
            if role_str in ALL_VALID_ROLES:
                num = int(match.group(2)) if match.group(2) else 1
                return role_str, num
    return "OTHER", 1

# =============================================================================
# 5. LAYOUT TIERING MATH (Replaces hardcoded orbit radii in templates)
# =============================================================================

def get_layout_radii(role: str, layout_type: str = "BACKBONE"):
    """Returns (Local_Radius, Remote_Radius) dynamically based on role significance."""
    role = role.upper()
    
    if layout_type == "BACKBONE":
        if role in ['SDR', 'EBR']: return 180, 500 
        elif role in ['SCR', 'SRR', 'RR']: return 280, 550
        elif role in ['CR', 'ERR']: return 380, 600
        elif role in CORE_ROLES: return 180, 500
        else: return 420, 500
        
    elif layout_type == "EDGE":
        if role in CORE_ROLES: return 180, 180
        elif role in PRIMARY_EDGE_ROLES: return 480, 480
        else: return 580, 580
        
    return 200, 500

def get_role_priority():
    """Returns the visual drawing/sorting order for grid and ring layouts."""
    return ["SDR", "EBR", "VAR", "EAR", "EDGE", "ES", "SCR", "CR", "RR", "OTHER"]