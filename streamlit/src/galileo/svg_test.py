import sys
import os

# 1. Get the absolute path of the directory containing svg_test.py
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Go up TWO levels: topology -> pages -> streamlit
# Change this to '..' if 'src' is inside 'pages', but '..', '..' if 'src' is in 'streamlit'
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))

# 3. Add to path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print(f"DEBUG: Python is looking for 'src' in: {project_root}")

# 4. Now attempt the import
try:
    from svg_galileo import render_galileo
    print("SUCCESS: Module 'src' found!")
except ModuleNotFoundError:
    print("FAILURE: 'src' not found. Check if 'src' is actually in the folder printed above.")
    sys.exit()

# --- Your test code continues below ---