
import os
from tabulate import tabulate

def count_lines_in_file(filepath):
    """
    Counts the non-empty lines in a given file.
    Skips files that are not readable (e.g., binaries, permission errors).
    """
    try:
        count = 0
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                # Count non-empty lines after stripping whitespace
                if line.strip():
                    count += 1
        return count
    except UnicodeDecodeError:
        # Ignore files that are likely binaries or non-text files
        return 0
    except IOError as e:
        # Handle permission denied or other IO errors
        print(f"⚠️ Warning: Could not read file {filepath}. Skipping. Error: {e}")
        return 0

def analyze_directory(root_dir):
    """
    Recursively analyzes the directory structure to count files and lines.
    
    Returns:
        tuple: (
            directory_stats: dictionary of {dir_path: {'file_count': int, 'line_count': int}},
            grand_total_files: int,
            grand_total_lines: int
        )
    """
    directory_stats = {}
    grand_total_files = 0
    grand_total_lines = 0

    print(f"🔍 Analyzing directory: {root_dir}...")
    
    # os.walk traverses the directory tree depth-first
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Initialize counts for the current subdirectory
        current_dir_files = 0
        current_dir_lines = 0
        
        # Process each file in the current directory
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            
            # Skip hidden files and directories (optional, but common for code analysis)
            if filename.startswith('.'):
                continue
            
            # Count lines of code in the file
            lines = count_lines_in_file(filepath)
            
            # Update directory and grand totals
            current_dir_files += 1
            current_dir_lines += lines
            
            grand_total_files += 1
            grand_total_lines += lines
            
        # Store results for the current directory if it contains files
        if current_dir_files > 0:
            directory_stats[dirpath] = {
                'file_count': current_dir_files,
                'line_count': current_dir_lines
            }
            
    return directory_stats, grand_total_files, grand_total_lines

def display_results(stats, total_files, total_lines):
    """
    Formats and prints the analysis results in a clear table format.
    """
    if not stats and total_files == 0:
        print("\n**No files containing readable code were found in the specified directory.**")
        return

    # --- Directory Analysis Table ---
    
    # Prepare data for the subdirectory table
    table_data = []
    headers = ["Subdirectory Path", "Files", "Lines of Code (LOC)"]

    for path, data in stats.items():
        # Shorten path to be relative to the starting directory
        relative_path = os.path.relpath(path, start_directory)
        
        # If the path is just '.', show the directory name
        if relative_path == '.':
            display_path = start_directory
        else:
            display_path = relative_path
            
        table_data.append([
            display_path, 
            data['file_count'], 
            data['line_count']
        ])

    print("\n" + "="*80)
    print("## 📊 Subdirectory Analysis")
    print("="*80)
    
    # Sort by directory path for consistent output
    table_data.sort(key=lambda x: x[0])
    
    print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
    
    # --- Overall Totals ---
    print("\n" + "#"*80)
    print("## 🚀 Grand Totals")
    print("#"*80)
    print(f"| **Total Files Analyzed:** | **{total_files:,}** |")
    print(f"| **Total Lines of Code (LOC):** | **{total_lines:,}** |")
    print("-" * 80)


if __name__ == "__main__":
    
    # --- Setup and Execution ---
    
    # Prompt the user for the starting directory
    start_directory = input("Enter the starting directory path (e.g., C:\\Projects\\MyRepo or /home/user/code): ").strip()
    
    # Check if the path exists
    if not os.path.isdir(start_directory):
        print(f"\n❌ Error: Directory not found at path: {start_directory}")
    else:
        try:
            # Run the analysis
            dir_stats, total_files, total_lines = analyze_directory(start_directory)
            
            # Display the results
            display_results(dir_stats, total_files, total_lines)
            
        except Exception as e:
            print(f"\n❌ An unexpected error occurred during analysis: {e}")