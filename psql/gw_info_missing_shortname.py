import pandas as pd
import os
import traceback
import difflib

def match_missing_short_names(missing_file_path: str, gwinfo_file_path: str, output_file_path: str, unmatched_file_path: str, missing_match_col: str, gwinfo_search_cols: list):
    """
    Reads the missing short names file and the gwinfo file. 
    Explodes overloaded columns to find exact matches, outputs a file with the matched 'found_name',
    and generates a separate file containing all unmatched records with a 'best fit' fuzzy match suggestion.
    """
    try:
        if missing_file_path.lower().endswith('.xlsx'):
            df_missing = pd.read_excel(missing_file_path)
        else:
            df_missing = pd.read_csv(missing_file_path)
            
        if gwinfo_file_path.lower().endswith('.xlsx'):
            df_gwinfo = pd.read_excel(gwinfo_file_path)
        else:
            df_gwinfo = pd.read_csv(gwinfo_file_path)
    except Exception as e:
        print(f"CRITICAL ERROR loading files:\n{traceback.format_exc()}")
        return

    # CLEANUP 1: Strip invisible whitespace from column headers
    df_missing.columns = df_missing.columns.str.strip()
    df_gwinfo.columns = df_gwinfo.columns.str.strip()

    if missing_match_col not in df_missing.columns:
        print(f"Error: Match column '{missing_match_col}' not found in {os.path.basename(missing_file_path)}")
        return

    # CLEANUP 2: Filter out the '---' dashed line from the missing file data
    df_missing = df_missing[~df_missing[missing_match_col].astype(str).str.contains('---')]
    df_missing[missing_match_col] = df_missing[missing_match_col].astype(str).str.strip()

    # --- ADVANCED MATCHING: Handling the overloaded columns ---
    
    for col in gwinfo_search_cols:
        if col not in df_gwinfo.columns:
            print(f"Warning: Expected column '{col}' not found in gwinfo file. Skipping this column.")
            df_gwinfo[col] = ''
        else:
            df_gwinfo[col] = df_gwinfo[col].fillna('').astype(str)

    # Combine target columns into a single string, then EXPLODE into a new column called 'found_name'
    df_gwinfo['temp_all_aliases'] = df_gwinfo[gwinfo_search_cols].agg(','.join, axis=1)

    df_gwinfo_exploded = df_gwinfo.assign(
        found_name=df_gwinfo['temp_all_aliases'].str.split(',')
    ).explode('found_name')

    # Clean up the new 'found_name' column
    df_gwinfo_exploded['found_name'] = df_gwinfo_exploded['found_name'].str.strip()
    df_gwinfo_exploded = df_gwinfo_exploded[df_gwinfo_exploded['found_name'] != '']

    # --- PERFORM THE EXACT MERGE ---
    try:
        matched_df = pd.merge(
            df_missing, 
            df_gwinfo_exploded, 
            left_on=missing_match_col, 
            right_on='found_name', 
            how='inner'
        )

        # Clean up temporary helper columns and drop duplicates
        matched_df = matched_df.drop(columns=['temp_all_aliases'])
        matched_df = matched_df.drop_duplicates()

        # Save MATCHED records
        matched_df.to_csv(output_file_path, index=False)
        
        # --- PROCESS UNMATCHED RECORDS & FUZZY MATCHING ---
        # Filter the original missing dataframe to only include rows NOT present in the matched dataframe
        unmatched_df = df_missing[~df_missing[missing_match_col].isin(matched_df[missing_match_col])].copy()
        
        # Create a unique list of all possible clean aliases from the gwinfo file to check against
        valid_aliases = df_gwinfo_exploded['found_name'].unique().tolist()

        print("Running best-fit analysis on unmatched records...")
        
        # Helper function to find the closest match
        def get_best_fit(missing_name):
            # n=1 returns the single best match. 
            # cutoff=0.7 requires at least 70% similarity (e.g., bsa3 and bsa1 are 75% similar)
            matches = difflib.get_close_matches(str(missing_name), valid_aliases, n=1, cutoff=0.7)
            return matches[0] if matches else "No close match"

        # Apply the fuzzy logic to create a suggestion column
        unmatched_df['suggested_best_match'] = unmatched_df[missing_match_col].apply(get_best_fit)

        # Save UNMATCHED records with suggestions
        unmatched_df.to_csv(unmatched_file_path, index=False)

        # Print detailed execution results
        print(f"Total missing records evaluated: {len(df_missing)}")
        print(f"Success: {len(matched_df)} exact matches exported to:\n -> {os.path.abspath(output_file_path)}")
        print(f"Pending: {len(unmatched_df)} unmatched records (with best-fit suggestions) exported to:\n -> {os.path.abspath(unmatched_file_path)}")

    except Exception as e:
        print(f"CRITICAL ERROR during merge or save:\n{traceback.format_exc()}")

def execute_matching_job():
    """
    Sets up the local file paths, defines the overloaded join columns, 
    verifies files, and executes the matching process.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    file_missing = os.path.join(script_dir, "missing_short_name.csv")
    file_gwinfo = os.path.join(script_dir, "gwinfo.xlsx")
    file_output_matched = os.path.join(script_dir, "gw-info_missing.csv")
    file_output_unmatched = os.path.join(script_dir, "gw-info_unmatched.csv")

    # The exact column in the missing file
    missing_key = "short_name_missing"
    
    # A list of the overloaded columns in the gwinfo file to search through
    gwinfo_columns_to_search = [
        "fT_names", 
        "ctl_names", 
        "qwest_names", 
        "savvis_names"
    ]

    print("--- File Path Verification ---")
    print(f"Missing File: {file_missing}")
    print(f"GW Info File:   {file_gwinfo}")
    
    for file_path, name_label in [(file_missing, "Missing"), (file_gwinfo, "GW Info")]:
        if not os.path.exists(file_path):
            print(f"\n[!] CRITICAL ERROR: {name_label} file NOT FOUND.")
            return 

    print("\n" + "="*50)
    print(f"Starting matching job...")
    print(f"Targeting missing key: '{missing_key}'")
    print(f"Scanning gwinfo columns: {gwinfo_columns_to_search}")
    
    try:
        match_missing_short_names(
            missing_file_path=file_missing,
            gwinfo_file_path=file_gwinfo,
            output_file_path=file_output_matched,
            unmatched_file_path=file_output_unmatched,
            missing_match_col=missing_key,
            gwinfo_search_cols=gwinfo_columns_to_search
        )
    except Exception as e:
         print(f"Job failed to execute:\n{traceback.format_exc()}")

if __name__ == "__main__":
    execute_matching_job()