#!/usr/bin/env python3
"""
Analyzes results from logic evaluation runs stored in JSONL files.

Reads files from a specified directory (e.g., logic_results),
parses the JSON data, and calculates statistics per configuration.
"""

import os
import sys
import json
import argparse
import glob
from collections import OrderedDict

# --- Configuration --- 
# These ranges should match the problem generation script
# Or potentially be loaded from a config or passed as args later
VARNR_RANGE = list(range(3, 16)) # Example: 3 to 15 variables
CL_LEN_RANGE = [3, 4]            # Example: Max clause lengths 3 and 4
HORN_FLAGS = [0, 1]              # 0 for general, 1 for Horn clauses

DEFAULT_RESULTS_DIR = os.path.join(os.path.dirname(__file__), "logic_results")

# --- Helper Functions --- 

def show_error(message):
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)

def extract_config_id(filename):
    """Extracts the config_id from filenames like YYYYMMDD_HHMMSS_config_id_results.jsonl"""
    base = os.path.basename(filename)
    parts = base.split('_')
    if len(parts) >= 4 and parts[-1] == 'results.jsonl':
        # Assuming format YYYYMMDD_HHMMSS_config_id_results.jsonl
        # Or potentially YYYYMMDD_HHMMSS_part1_part2_config_id_results.jsonl
        return "_".join(parts[2:-1])
    else:
        print(f"Warning: Could not extract config_id from filename format: {base}", file=sys.stderr)
        return None # Or handle error differently

# --- Data Loading --- 

def load_results_data(results_dir):
    """Loads all *.jsonl results from the specified directory into a dict keyed by config_id."""
    all_results = {}
    file_pattern = os.path.join(results_dir, "*_results.jsonl")
    result_files = glob.glob(file_pattern)

    if not result_files:
        show_error(f"No result files found matching '{file_pattern}'. Ensure run_logic_eval.py has produced output.")

    print(f"Found {len(result_files)} result files in {results_dir}")

    for filepath in result_files:
        config_id = extract_config_id(filepath)
        if not config_id:
            continue # Skip files with unexpected names
        
        if config_id not in all_results:
            all_results[config_id] = []
        
        print(f"  Loading {os.path.basename(filepath)} (config: {config_id})...", end='')
        loaded_count = 0
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f):
                    line = line.strip()
                    if not line: continue
                    try:
                        result_obj = json.loads(line)
                        # *** Prerequisite Check ***
                        # Ensure the necessary fields for analysis exist. 
                        # This script relies on run_logic_eval.py adding these fields.
                        if 'max_clause_length' not in result_obj or 'is_horn' not in result_obj:
                             print(f"\nWarning: Skipping line {line_num+1} in {filepath} - missing 'max_clause_length' or 'is_horn' key.")
                             print("  Ensure run_logic_eval.py is updated to include these fields.")
                             continue # Skip this record if essential data is missing
                             
                        all_results[config_id].append(result_obj)
                        loaded_count += 1
                    except json.JSONDecodeError as json_err:
                        print(f"\nWarning: Skipping invalid JSON at line {line_num+1} in {filepath}: {json_err}")
                    except KeyError as key_err:
                         print(f"\nWarning: Skipping record at line {line_num+1} in {filepath} due to missing key: {key_err}")
            print(f" loaded {loaded_count} records.")

        except IOError as io_err:
            print(f"\nWarning: Could not read file {filepath}: {io_err}")
        except Exception as e:
            print(f"\nWarning: An unexpected error occurred reading {filepath}: {e}")
            
    if not all_results:
        show_error("No valid result data could be loaded.")
        
    return all_results

# --- Analysis Logic (Placeholder - To be implemented) ---

def make_counts_structure(config_ids, var_range, cl_len_range, horn_flags):
    """Creates the nested dictionary structure for storing analysis counts."""
    # To be implemented
    pass

def calculate_stats(all_results, counts_structure):
    """Populates the counts_structure based on the loaded results."""
    # To be implemented
    pass

# --- Output Formatting (Placeholder - To be implemented) ---

def print_detailed_stats(counts_structure):
    """Prints the detailed counts per category."""
    # To be implemented
    pass

def print_correctness_percentages(counts_structure):
    """Prints the correctness percentages per category."""
    # To be implemented
    pass

# --- Main Execution --- 

def main():
    parser = argparse.ArgumentParser(description="Analyze logic evaluation results from JSONL files.")
    parser.add_argument("results_dir", nargs='?', default=DEFAULT_RESULTS_DIR,
                        help=f"Directory containing the result JSONL files (default: {DEFAULT_RESULTS_DIR})")
    # Add other arguments later if needed (e.g., for ranges)
    args = parser.parse_args()

    if not os.path.isdir(args.results_dir):
        show_error(f"Specified results directory does not exist or is not a directory: {args.results_dir}")

    # 1. Load Data
    all_results_data = load_results_data(args.results_dir)
    config_ids = list(all_results_data.keys())
    print(f"\nLoaded data for {len(config_ids)} configurations: {config_ids}")

    # --- Placeholder Calls --- 
    print("\nAnalysis logic not yet implemented.")
    # counts = make_counts_structure(config_ids, VARNR_RANGE, CL_LEN_RANGE, HORN_FLAGS)
    # calculate_stats(all_results_data, counts)
    # print("\n===== Detailed Counts =====")
    # print_detailed_stats(counts)
    # print("\n===== Correctness Percentages =====")
    # print_correctness_percentages(counts)
    # -----------------------

if __name__ == "__main__":
    main() 