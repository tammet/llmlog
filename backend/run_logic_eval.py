#!/usr/bin/env python3
"""
Script to run propositional logic problems from a file against multiple LLM providers
using provider_manager, evaluate correctness, and save detailed results per provider.
"""

import os
import sys
import json
import datetime
import argparse
import traceback

# --- Path Setup --- 
# Add the parent directory (project root) to the Python path
# to allow importing 'providers' from the sibling directory.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from providers.provider_manager import generate_completion
except ImportError as e:
    print(f"Error: Could not import 'generate_completion' from 'providers.provider_manager': {e}")
    print("Ensure the script is run from the 'backend' directory or the project root is in PYTHONPATH.")
    sys.exit(1)

# --- Configuration ---
PROVIDERS_TO_RUN = ["anthropic", "openai", "google"]
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "logic_results")
# Set a reasonable default token limit for logic problems
DEFAULT_ARGS = {
    "max_tokens": 300,
    "max_output_tokens": 300,
    "temperature": 0 # For deterministic results if provider supports it
}
# --- End Configuration ---

# --- Helper Functions (Adapted from askllm.py) ---

def makeprompt_v1(problem):
    """Formats the prompt for the logic problem (version 1 from askllm.py)."""
    # Problem format expected: [id1, id2, num_vars, num_clauses, expected_result(0/1), [[clause1], [clause2], ...]]
    if len(problem) < 6 or not isinstance(problem[5], list):
        raise ValueError("Invalid problem format: expected list of length >= 6 with list at index 5")
    clauses = problem[5]
    prefix = "Your task is to solve a problem in propositional logic.\n"
    prefix += "You will get a list of statements and have to determine whether the statements form a logical contradiction or not.\n"
    prefix += "If the statements form a contradiction, the last word of your answer should be 'contradiction'.\n"
    prefix += "If the statements do not form a contradiction, the last word should be 'satisfiable'.\n" # Simplified instruction

    details = "Propositional variables are represented as 'pN' where N is a number. They are either true or false.\n"
    details += "'X or Y' means that X is true or Y is true or both X and Y are true.\n"
    details += "All the given statements are implicitly connected with 'and': they are all claimed to be true.\n"
    
    example = "Two examples:\n"
    example += "Example 1. Statements: p1 is true. p1 is false or p2 is true. p2 is false. Answer: contradiction.\n"
    example += "Example 2. Statements: p1 is true. p1 is true or p2 is true. p2 is false. Answer: satisfiable.\n"

    statements = "Statements:\n"
    for clause in clauses:
        statement = ""
        for var in clause:
            if not isinstance(var, int) or var == 0:
                 raise ValueError(f"Invalid variable in clause: {var}")
            if var > 0: s = f"p{var} is true"
            else: s = f"p{abs(var)} is false" # Use abs() for clarity
            if statement: statement += " or " + s
            else: statement = s
        statement = statement + ".\n"
        statements = statements + statement

    final = "\nPlease think step by step and answer whether the given statements form a logical contradiction or are satisfiable.\n"
    final += "Ensure your final answer ends with either 'contradiction' or 'satisfiable'."

    prompt = prefix + details + example + statements + final
    return prompt

def parse_result(txt):
    """Parses the LLM text response into 0 (contradiction), 1 (satisfiable), 2 (other/unknown)."""
    if not txt: return 2 # Handle empty response
    # Normalize: remove common punctuation, convert to lower, handle newlines
    txt = txt.replace(".", "").replace(",", " ").replace(":", " ").replace("*", "").replace("'", "").replace("\n", " ").replace("\r", " ")
    txt = txt.strip().lower()
    sp = txt.split()
    if not sp: return 2 # Handle empty after normalization
    
    # Check the last word first, cleaning potential trailing punctuation
    last_word = sp[-1]
    cleaned_last_word = ''.join(filter(str.isalnum, last_word))

    if cleaned_last_word in ["contradiction", "contradictory", "false"]:
        return 0
    elif cleaned_last_word in ["satisfiable", "satisfied", "true"]:
        return 1
    else:
        # Fallback: Check if keywords appear anywhere in the normalized text
        # Prioritize contradiction keywords
        if "contradiction" in txt or "contradictory" in txt:
            return 0
        if "satisfiable" in txt or "satisfied" in txt:
            return 1
        # Consider 'unknown' or 'uncertain' as *not* satisfiable (closer to 'other' for this task)
        # if cleaned_last_word in ["unknown", "uncertain"]: return 1 # Original askllm logic mapped unknown to 1
        
        return 2 # Could not determine result

def ensure_dir(directory_path: str):
    """Creates a directory if it doesn't exist."""
    os.makedirs(directory_path, exist_ok=True)

# --- Main Evaluation Logic ---

def run_logic_evaluation(problem_filepath: str, output_dir: str, max_rows: int, provider_args: dict):
    """
    Runs logic problems from a file against providers, evaluates, and saves results.
    """
    ensure_dir(output_dir)
    run_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    stats = {provider: {'processed': 0, 'correct': 0, 'errors': 0, 'unknown': 0} for provider in PROVIDERS_TO_RUN}
    total_problems_attempted = 0 # Count problems read and attempted

    print(f"Starting logic evaluation run: {run_timestamp}")
    print(f"Problem file: {problem_filepath}")
    print(f"Output directory: {os.path.abspath(output_dir)}")
    print(f"Max problems to process: {max_rows if max_rows > 0 else 'All'}")
    print(f"Providers: {PROVIDERS_TO_RUN}")
    print(f"Base provider args: {provider_args}")
    print("-" * 50)

    try:
        with open(problem_filepath, "r", encoding="utf-8") as f:
            row_count = 0
            processed_valid_problems = 0 # Count problems passing initial validation
            
            for line in f:
                row_count += 1
                if row_count == 1:  # Skip header row
                    print("Skipping header row...")
                    continue
                
                line = line.strip()
                if not line: continue # Skip empty lines

                # Check max_rows limit *after* skipping header/empty lines
                if max_rows > 0 and processed_valid_problems >= max_rows:
                    print(f"Reached max_rows limit ({max_rows}). Stopping.")
                    break
                    
                total_problems_attempted += 1 # Increment for each non-empty, non-header line read

                try:
                    problem = json.loads(line)
                    # Basic validation of problem structure
                    if not isinstance(problem, list) or len(problem) < 6 or not isinstance(problem[5], list):
                       print(f"Warning: Skipping malformed problem structure at line {row_count}: {line[:100]}...")
                       continue
                    # Ensure expected answer is valid (0 or 1)
                    expected_answer = int(problem[4])
                    if expected_answer not in [0, 1]:
                        print(f"Warning: Skipping problem with invalid expected answer ({expected_answer}) at line {row_count}.")
                        continue
                        
                    problem_id_str = f"L{row_count}_P{processed_valid_problems + 1}" # Unique ID based on valid problems

                except (json.JSONDecodeError, IndexError, TypeError, ValueError) as json_err:
                    print(f"Warning: Skipping invalid JSON or data format at line {row_count}: {json_err}")
                    continue # Skip to next line

                # Only increment if problem passes validation
                processed_valid_problems += 1
                print(f"\n--- Processing Problem {processed_valid_problems} (Line {row_count}) ---")
                
                # Try generating prompt outside the provider loop
                try:
                    prompt = makeprompt_v1(problem)
                    prompt_generated = True
                except ValueError as prompt_err:
                    print(f"  Error creating prompt: {prompt_err}")
                    prompt = None
                    prompt_generated = False
                    # We'll still create result files indicating the prompt error

                # Process this problem for all providers
                for provider in PROVIDERS_TO_RUN:
                    if prompt_generated:
                        print(f"  Querying {provider.capitalize()}...")
                    else:
                        print(f"  Skipping {provider.capitalize()} due to prompt generation error.")

                    stats[provider]['processed'] += 1 # Count an attempt for this provider
                    
                    output_filename = f"{run_timestamp}_{problem_id_str}_{provider}_result.json"
                    output_filepath = os.path.join(output_dir, output_filename)
                    
                    # Initialize result structure
                    result_data = {
                        "run_timestamp": run_timestamp,
                        "problem_file": os.path.basename(problem_filepath),
                        "problem_line": row_count,
                        "problem_id_str": problem_id_str,
                        "problem_metadata": problem[:5], # First 5 elements (ids, counts, expected)
                        "provider": provider,
                        "prompt_generated": prompt_generated,
                        "provider_args": provider_args,
                        "expected_answer": expected_answer, 
                        "status": "error", # Default to error
                        "raw_response": None,
                        "parsed_result": None,
                        "is_correct": None,
                        "error_message": None,
                        "traceback": None
                    }
                    
                    # Only attempt API call if prompt was generated
                    if prompt_generated:
                        try:
                            # Generate completion using the provider manager
                            raw_response = generate_completion(provider, prompt, **provider_args)
                            result_data["raw_response"] = raw_response
                            
                            # Parse the result
                            parsed_result = parse_result(raw_response)
                            result_data["parsed_result"] = parsed_result
                            
                            # Evaluate correctness (parsed_result can be 0, 1, or 2)
                            if parsed_result == expected_answer:
                                is_correct = True
                                stats[provider]['correct'] += 1
                                print(f"    -> Correct (Expected: {expected_answer}, Got: {parsed_result})")
                            elif parsed_result == 2:
                                is_correct = False # Treat 'unknown' as incorrect for accuracy calculation
                                stats[provider]['unknown'] += 1
                                print(f"    -> Unknown Output (Expected: {expected_answer}, Got: {parsed_result})")
                            else: # Parsed result is 0 or 1, but doesn't match expected
                                is_correct = False
                                print(f"    -> Incorrect (Expected: {expected_answer}, Got: {parsed_result})")

                            result_data["is_correct"] = is_correct
                            result_data["status"] = "success"

                        except (ValueError, ImportError, RuntimeError) as api_err:
                            error_message = f"API/Config Error: {type(api_err).__name__} - {api_err}"
                            print(f"    -> {error_message}")
                            result_data["error_message"] = error_message
                            result_data["traceback"] = traceback.format_exc(limit=10) # Limit traceback length
                            stats[provider]['errors'] += 1
                        except Exception as e:
                            error_message = f"Unexpected Error during API call/parsing: {type(e).__name__} - {e}"
                            print(f"    -> {error_message}")
                            result_data["error_message"] = error_message
                            result_data["traceback"] = traceback.format_exc(limit=10)
                            stats[provider]['errors'] += 1
                    else:
                        # Prompt error occurred before this provider loop
                        result_data["status"] = "error"
                        result_data["error_message"] = "Skipped due to prompt generation error."
                        stats[provider]['errors'] += 1

                    # Save the detailed result to a JSON file regardless of success/error
                    try:
                        with open(output_filepath, "w", encoding="utf-8") as rf:
                            # Exclude the full prompt from JSON to keep files smaller?
                            # result_data_to_save = {k: v for k, v in result_data.items() if k != 'prompt'} 
                            # For now, include everything:
                            result_data_to_save = result_data
                            json.dump(result_data_to_save, rf, indent=2)
                    except IOError as io_err:
                        print(f"    ERROR: Could not write result file {output_filepath}: {io_err}")
                        # Log this failure, maybe update stats?

    except FileNotFoundError:
        print(f"Error: Problem file not found at {problem_filepath}")
        sys.exit(1)
    except Exception as file_err:
        print(f"Critical Error reading problem file or during processing: {file_err}")
        traceback.print_exc()
        sys.exit(1)
    
    print("-" * 50)
    print("Evaluation run finished.")
    return stats, processed_valid_problems # Return stats based on valid processed problems

# --- Summary and Execution ---

def print_summary(stats, total_valid_problems):
    print("\n===== Evaluation Summary =====")
    print(f"Total valid problems processed: {total_valid_problems}")
    if total_valid_problems == 0:
        print("No problems were processed.")
        return

    print("-" * 30)
    for provider, data in stats.items():
        processed = data['processed']
        # Ensure processed count matches total_valid_problems if no errors occurred before loop
        # Note: processed can be higher if errors happened *during* the provider loop for some problems
        correct = data['correct']
        errors = data['errors']
        unknown = data['unknown']
        
        # Calculate accuracy based on problems that didn't result in an error or unknown output
        attempted_for_accuracy = processed - errors - unknown 
        accuracy = (correct / attempted_for_accuracy * 100) if attempted_for_accuracy > 0 else 0
        
        print(f"Provider: {provider.capitalize()}")
        print(f"  Problems Attempted: {processed}") # This count might differ per provider if errors occur
        print(f"  Correct Answers:    {correct}")
        print(f"  Incorrect Answers:  {attempted_for_accuracy - correct}")
        print(f"  Unknown Outputs:    {unknown}")
        print(f"  Errors Encountered: {errors}")
        print(f"  Accuracy (Correct / (Attempted - Errors - Unknown)): {accuracy:.2f}%")
        print("-" * 30)

def main():
    parser = argparse.ArgumentParser(description="Run logic problems against LLM providers and save results.")
    parser.add_argument("problem_file", help="Path to the JSON-lines problem file.")
    parser.add_argument("-o", "--output-dir", default=DEFAULT_OUTPUT_DIR, 
                        help=f"Directory to save result JSON files (default: {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("-n", "--max-rows", type=int, default=0, 
                        help="Maximum number of problems to process from the file (0 for all, default: 0)")
    parser.add_argument("-t", "--max-tokens", type=int, default=None,
                        help=f"Override default max_tokens/max_output_tokens for providers (default: {DEFAULT_ARGS['max_tokens']})")
    # Add other potential arguments like temperature?
    # parser.add_argument("--temperature", type=float, default=DEFAULT_ARGS['temperature'], help="Set generation temperature")

    args = parser.parse_args()

    # Prepare provider arguments, overriding defaults if specified
    provider_args = DEFAULT_ARGS.copy()
    if args.max_tokens is not None:
        provider_args["max_tokens"] = args.max_tokens
        provider_args["max_output_tokens"] = args.max_tokens
    # if args.temperature is not None:
    #     provider_args["temperature"] = args.temperature

    # Run the evaluation
    stats, total_processed = run_logic_evaluation(
        problem_filepath=args.problem_file,
        output_dir=args.output_dir,
        max_rows=args.max_rows,
        provider_args=provider_args
    )

    # Print the summary
    print_summary(stats, total_processed)

if __name__ == "__main__":
    main() 