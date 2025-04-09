#!/usr/bin/env python3
"""OpenAI client for generating completions using OpenAI's Responses API."""

import os
import openai
import json

def create_openai_client():
    """
    Creates and returns an OpenAI API client using the API key from secrets.json.

    Raises:
        ValueError: If the secrets.json file cannot be loaded or the 'openai_api_key' is not set.
    """
    try:
        with open("secrets.json", "r") as f:
            secrets = json.load(f)
    except Exception as e:
        raise ValueError(f"Could not load secrets.json file: {e}")

    api_key = secrets.get("openai_api_key")
    if not api_key:
        raise ValueError("OpenAI API key is not set in secrets.json. Please set the 'openai_api_key' property.")

    return openai.OpenAI(api_key=api_key)



def generate_completion(prompt: str, model: str = "o3-mini", max_output_tokens: int = 100) -> str:
    """
    Generate a completion using the OpenAI Responses API.

    Args:
        prompt (str): The prompt text to complete.
        model (str): The model to use (default: 'o3-mini').
        max_output_tokens (int): Maximum output tokens to generate (default: 100).

    Returns:
        str: The generated completion text.

    Raises:
        RuntimeError: If there is an error during the API request.
    """
    client = create_openai_client()
    try:
        # Use the /responses/create endpoint
        response = client.responses.create(
            model=model,
            max_output_tokens=max_output_tokens,
            input=prompt,  # Input should be the prompt string directly
            reasoning={
                "effort": "high"
            }
        )
        # Iterate over the output items to find the message content using attribute access
        for item in response.output:
            if hasattr(item, "type") and item.type == "message":
                if hasattr(item, "content") and item.content:
                    first_content = item.content[0]
                    if hasattr(first_content, "text"):
                        return first_content.text
        
        # Print full debug information of the response
        print("DEBUG: Full response:", response)
        raise RuntimeError("Could not find text content in OpenAI response output.")
    except Exception as e:
        raise RuntimeError(f"Error during OpenAI Responses API request: {e}")

if __name__ == "__main__":
    # Test the functionality with a sample prompt.
    test_prompt = "What is the future of AI in simple terms?"
    print("Sending test prompt to OpenAI Responses API...")
    print("Prompt: ", test_prompt)
    try:
        result = generate_completion(test_prompt, max_output_tokens=1000)
        print("Received response:")
        print(result)
    except Exception as err:
        print("Error:", err)