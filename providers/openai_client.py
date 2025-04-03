#!/usr/bin/env python3
"""OpenAI client for generating completions using OpenAI's Responses API."""

import os
import openai
import json

# Load the API key from secrets.json
try:
    with open("secrets.json", "r") as f:
        secrets = json.load(f)
except Exception as e:
    raise ValueError(f"Could not load secrets.json file: {e}")

api_key = secrets.get("openai_api_key")
if not api_key:
    raise ValueError("OpenAI API key is not set in secrets.json. Please set the 'openai_api_key' property.")
openai.api_key = api_key

def generate_completion(prompt: str, **kwargs) -> str:
    """Generate a completion using OpenAI's responses API.

    Args:
        prompt (str): The prompt to send to the model. If no 'input' is provided in kwargs, this prompt is wrapped in a single message with role 'user'.
        **kwargs: Additional parameters including:
            - model (str): The model name to use. (Required)
            - input (list): Optional list of message objects (each a dict with 'role' and 'content').

    Returns:
        str: The generated completion text.
    """
    model = kwargs.get("model")
    if not model:
        raise ValueError("Model name must be provided in kwargs.")
    input_payload = kwargs.get("input")
    if not input_payload:
        input_payload = [{"role": "user", "content": prompt}]
    
    try:
        response = openai.responses.create(
            model=model,
            input=input_payload
        )
        # Extract and return the generated text from the response using the new API attribute
        return response.output_text.strip()
    except Exception as e:
        raise RuntimeError(f"OpenAI API call failed: {e}")

# Added test block similar to anthropic_client
if __name__ == "__main__":
    test_prompt = "What is the future of OpenAI in simple terms?"
    print("Sending test prompt to OpenAI API...")
    print("Prompt: ", test_prompt)
    try:
        result = generate_completion(test_prompt, model="gpt-3.5-turbo")
        print("Received response:")
        print(result)
    except Exception as err:
        print("Error:", err)