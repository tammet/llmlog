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

# --- Analysis Logic --- 

def make_counts_structure(config_ids, var_range, cl_len_range, horn_flags):
    """Creates the nested dictionary structure for storing analysis counts."""
    counts = OrderedDict()
    for config_id in config_ids:
        config_counts = OrderedDict()
        for varnr in var_range:
            cllendata = OrderedDict()
            for cllen in cl_len_range:
                horndata = OrderedDict()
                for hornflag in horn_flags:
                    # [total_problems, correct_satisfiable, correct_contradiction, unclear_answers]
                    lst = [0, 0, 0, 0]
                    horndata[hornflag] = lst
                cllendata[cllen] = horndata
            config_counts[varnr] = cllendata
        counts[config_id] = config_counts
    return counts

def calculate_stats(all_results, counts_structure):
    """Populates the counts_structure based on the loaded results."""
    for config_id, results_list in all_results.items():
        if config_id not in counts_structure:
            print(f"Warning: Config ID '{config_id}' found in results but not expected in counts structure. Skipping.", file=sys.stderr)
            continue
            
        config_counts = counts_structure[config_id]
        
        for result in results_list:
            try:
                # Extract data using keys
                # Assuming problem_metadata: [id1, id2, num_vars, num_clauses, expected_result(0/1)]
                if len(result['problem_metadata']) < 5:
                    print(f"Warning: Skipping result due to short problem_metadata: {result.get('problem_id_str')}", file=sys.stderr)
                    continue
                    
                maxvars = int(result['problem_metadata'][2])
                expected_answer = int(result['problem_metadata'][4]) # 0 for contradiction, 1 for satisfiable
                parsed_result = result.get('parsed_result') # Can be None if error occurred
                
                # Get the fields added in the prerequisite step
                maxlen = int(result['max_clause_length']) 
                hornflag = int(result['is_horn'])         

                # Check if the extracted values fall within our expected ranges
                if maxvars not in config_counts or maxlen not in config_counts[maxvars] or hornflag not in config_counts[maxvars][maxlen]:
                    # print(f"Warning: Skipping result with out-of-range parameters (maxvars={maxvars}, maxlen={maxlen}, hornflag={hornflag}): {result.get('problem_id_str')}", file=sys.stderr)
                    continue # Skip if keys don't exist (outside defined ranges)
                    
                # Access the specific list for this combination
                lst = config_counts[maxvars][maxlen][hornflag]

                # Increment total problem count
                lst[0] += 1

                # Check correctness
                if parsed_result == 2: # Unclear answer
                    lst[3] += 1
                elif parsed_result == expected_answer: # Correct answer
                    if expected_answer == 1: # Satisfiable
                        lst[1] += 1
                    else: # Contradiction (expected_answer == 0)
                        lst[2] += 1
                # Else: Incorrect answer (parsed_result is 0 or 1 but not matching expected_answer) - no specific counter, but included in total count.

            except (KeyError, IndexError, TypeError, ValueError) as e:
                 print(f"\nWarning: Skipping result due to data error ({type(e).__name__}: {e}) in record: {result.get('problem_id_str', 'N/A')}")

# --- Output Formatting --- 

def print_detailed_stats(counts_structure, var_range, cl_len_range, horn_flags):
    """Prints the detailed counts per category."""
    print("Config ID | MaxVars | MaxLen | Horn | [Total, CorrectSat, CorrectUnsat, Unclear]")
    print("-" * 80)
    for config_id, config_counts in counts_structure.items():
        print(f"{config_id}:")
        for varnr in var_range:
            if varnr not in config_counts: continue
            vardata = config_counts[varnr]
            for cllen in cl_len_range:
                if cllen not in vardata: continue
                lendata = vardata[cllen]
                for hornflag in horn_flags:
                    if hornflag not in lendata: continue
                    stats_list = lendata[hornflag]
                    if stats_list[0] > 0: # Only print if there are problems in this category
                       print(f"  - {varnr: <7} | {cllen: <6} | {hornflag: <4} | {stats_list}")
        print("-" * 80)

def print_correctness_percentages(counts_structure, var_range, cl_len_range, horn_flags):
    """Prints the correctness percentages per category."""
    print("Config ID | MaxVars | MaxLen | Horn | Correctness % ( (CorrectSat+CorrectUnsat) / Total )")
    print("-" * 80)
    for config_id, config_counts in counts_structure.items():
        print(f"{config_id}:")
        stopflag = False
        for varnr in var_range:
            if stopflag or varnr not in config_counts: continue
            vardata = config_counts[varnr]
            print(f"  Var {varnr}:")
            for cllen in cl_len_range:
                if cllen not in vardata: continue
                lendata = vardata[cllen]
                print(f"    Len {cllen}:", end="")
                for hornflag in horn_flags:
                    if hornflag not in lendata: continue
                    horndata = lendata[hornflag]
                    total = horndata[0]
                    correct_sat = horndata[1]
                    correct_unsat = horndata[2]
                    
                    if total == 0:
                        # If no problems were processed for this specific combo for *this config*,
                        # we might want to indicate that differently than 0.00%. 
                        # However, the original script seemed to stop processing further ranges 
                        # if a zero count was encountered. We'll keep it simple for now.
                        percentage = 0.0 
                        # stopflag = True # Uncomment if you want behavior identical to original script's stopping
                    else:
                        percentage = ((correct_sat + correct_unsat) / total) * 100
                    
                    horn_label = "Horn" if hornflag == 1 else "Gen "
                    print(f" {horn_label} {percentage:5.2f}%", end="")
                print() # Newline after processing horn flags for a clause length
            # print() # Newline after processing clause lengths for a var number
        print("-" * 80)

# --- Main Execution --- 

def main():
    parser = argparse.ArgumentParser(description="Analyze logic evaluation results from JSONL files.")
    parser.add_argument("results_dir", nargs='?', default=DEFAULT_RESULTS_DIR,
                        help=f"Directory containing the result JSONL files (default: {DEFAULT_RESULTS_DIR})")
    args = parser.parse_args()

    if not os.path.isdir(args.results_dir):
        show_error(f"Specified results directory does not exist or is not a directory: {args.results_dir}")

    # 1. Load Data
    all_results_data = load_results_data(args.results_dir)
    config_ids = sorted(list(all_results_data.keys())) # Sort for consistent output order
    print(f"\nLoaded data for {len(config_ids)} configurations: {config_ids}")

    # 2. Initialize Count Structure
    counts = make_counts_structure(config_ids, VARNR_RANGE, CL_LEN_RANGE, HORN_FLAGS)
    
    # 3. Calculate Stats
    calculate_stats(all_results_data, counts)
    
    # 4. Print Results
    print("\n===== Detailed Counts =====")
    print_detailed_stats(counts, VARNR_RANGE, CL_LEN_RANGE, HORN_FLAGS)
    
    print("\n===== Correctness Percentages =====")
    print_correctness_percentages(counts, VARNR_RANGE, CL_LEN_RANGE, HORN_FLAGS)
    
    # --- Proof depth analysis omitted as 'proof' data is not currently collected --- 

if __name__ == "__main__":
    main() 