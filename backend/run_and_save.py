#!/usr/bin/env python3
"""
Script to run a prompt against multiple LLM providers using provider_manager
and save each response to a separate file.
"""

import os
import sys
import datetime

# Add the parent directory (project root) to the Python path
# to allow importing 'providers' from the sibling directory.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from providers.provider_manager import generate_completion
except ImportError:
    print("Error: Could not import 'generate_completion' from 'providers.provider_manager'.")
    print("Ensure the script is run from the 'backend' directory or the project root is in PYTHONPATH.")
    sys.exit(1)

# --- Configuration ---
PROVIDERS_TO_RUN = ["anthropic", "openai", "google"]
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "responses")
# --- End Configuration ---

def ensure_dir(directory_path: str):
    """Creates a directory if it doesn't exist."""
    os.makedirs(directory_path, exist_ok=True)

def run_and_save_responses(prompt: str, output_dir: str = DEFAULT_OUTPUT_DIR, **kwargs):
    """
    Sends a prompt to multiple providers and saves their responses to files.

    Args:
        prompt (str): The prompt to send to each provider.
        output_dir (str): The directory to save response files.
        **kwargs: Additional arguments to pass to generate_completion (e.g., max_tokens).
    """
    ensure_dir(output_dir)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"Running prompt on providers: {', '.join(PROVIDERS_TO_RUN)}")
    print(f"Saving responses to: {os.path.abspath(output_dir)}")
    print("-" * 30)
    print(f'Prompt: "{prompt}"')
    print(f"Arguments: {kwargs}")
    print("-" * 30)

    results = {}

    for provider in PROVIDERS_TO_RUN:
        print(f"--- Querying {provider.capitalize()} ---")
        output_filename = f"{timestamp}_{provider}_response.txt"
        output_filepath = os.path.join(output_dir, output_filename)
        content_to_save = ""
        status = "error"

        try:
            # Generate completion using the provider manager
            response = generate_completion(provider, prompt, **kwargs)
            content_to_save = response
            status = "success"
            print(f"Success. Response saved to {output_filename}")
            results[provider] = {"status": status, "response": response, "file": output_filepath}

        except (ValueError, ImportError, RuntimeError) as e:
            # Catch specific errors from provider_manager or client calls
            error_message = f"Error querying {provider}: {type(e).__name__} - {e}"
            content_to_save = error_message
            status = "error"
            print(error_message)
            results[provider] = {"status": status, "message": str(e), "file": output_filepath}
        except Exception as e:
            # Catch any other unexpected errors
            error_message = f"An unexpected error occurred with {provider}: {type(e).__name__} - {e}"
            content_to_save = error_message
            status = "error"
            print(error_message)
            results[provider] = {"status": status, "message": str(e), "file": output_filepath}
        finally:
            # Save the response or error message to the file
            try:
                with open(output_filepath, "w", encoding="utf-8") as f:
                    # Use a single triple-quoted f-string for multi-line content
                    file_content = f"""--- Prompt ---
{prompt}

--- Provider ---
{provider}

--- Timestamp ---
{timestamp}

--- Arguments ---
{kwargs}

--- Status ---
{status}

--- Output ---
{content_to_save}
"""
                    f.write(file_content)
            except IOError as io_err:
                print(f"ERROR: Could not write to file {output_filepath}: {io_err}")
                if provider in results:
                     results[provider]["file_status"] = f"Failed to write: {io_err}" # Add write error info

        print("-" * 30)

    print("Processing complete.")
    return results

if __name__ == "__main__":
    # Example Usage:
    example_prompt = "Summarize the main benefits of using version control systems like Git."

    # Arguments to pass to the providers (filtered by provider_manager)
    # Use reasonable defaults that most providers might accept
    common_args = {
        "max_tokens": 150,         # For Anthropic
        "max_output_tokens": 1500   # For Google & OpenAI
        # Add other potential arguments like 'temperature' if needed
    }

    run_and_save_responses(example_prompt, **common_args)

    # Example with a different output directory:
    # custom_output_dir = os.path.join(os.path.dirname(__file__), "custom_runs")
    # run_and_save_responses("Explain REST APIs simply.", output_dir=custom_output_dir, max_tokens=100, max_output_tokens=100) 