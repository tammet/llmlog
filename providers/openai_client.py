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



def generate_completion(prompt: str, model: str = "gpt-3.5-turbo", max_tokens: int = 4096) -> str:
    """
    Generate a completion using the OpenAI Chat Completions API.

    Args:
        prompt (str): The prompt text to complete.
        model (str): The model to use (default: 'gpt-3.5-turbo').
        max_tokens (int): Maximum tokens to generate in the completion (default: 4096).

    Returns:
        str: The generated completion text.

    Raises:
        RuntimeError: If there is an error during the API request or parsing the response.
    """
    client = create_openai_client()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant solving logic problems."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
        )
        
        if response.choices and response.choices[0].message and response.choices[0].message.content:
            completion_text = response.choices[0].message.content.strip()
            return completion_text
        else:
            print("DEBUG: Full response:", response)
            raise RuntimeError("Could not find message content in OpenAI ChatCompletion response.")

    except openai.APIError as api_err:
         raise RuntimeError(f"OpenAI API Error: {api_err}")
    except Exception as e:
        print("DEBUG: Unexpected error during OpenAI call:", e)
        print("DEBUG: Full response object:", response if 'response' in locals() else 'N/A')
        raise RuntimeError(f"Error during OpenAI Chat Completions API request: {e}")

if __name__ == "__main__":
    # Test the functionality with a sample prompt.
    test_prompt = "What is the future of AI in simple terms?"
    print("Sending test prompt to OpenAI Chat Completions API...")
    print("Prompt: ", test_prompt)
    try:
        result = generate_completion(test_prompt, max_tokens=150)
        print("Received response:")
        print(result)
    except Exception as err:
        print("Error:", err)