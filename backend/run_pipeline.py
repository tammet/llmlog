#!/usr/bin/env python3
"""
Run Pipeline for LLM Workflow

This script runs the entire workflow:
  1) makeproblems.py generates a problem set.
  2) askllm.py uses the problem set to ask LLMs to solve the problems.
  3) analyze.py checks the LLM results and provides an analysis.

Usage:
    python3 run_pipeline.py
"""

import subprocess
import sys

def run_script(script_name):
    print(f"Running {script_name}...")
    result = subprocess.run(["python3", script_name], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running {script_name}: {result.stderr}")
        sys.exit(result.returncode)
    else:
        print(f"Output from {script_name}:\n{result.stdout}\n")
    return result.stdout

def main():
    # Step 1: Generate Problem Set
    print("Step 1: Generating problem set...")
    makeproblems_output = run_script("makeproblems.py")
    
    # Step 2: Ask LLM using the problem set
    print("Step 2: Asking LLM to solve the problems...")
    askllm_output = run_script("askllm.py")
    
    # Step 3: Analyze LLM results
    print("Step 3: Analyzing results...")
    analyze_output = run_script("analyze.py")
    
    print("Pipeline completed successfully.")

if __name__ == "__main__":
    main() 