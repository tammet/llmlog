#!/usr/bin/env python3
"""Google client for generating completions using Google's AI Studio API."""

import os
import google.generativeai as genai
import json

def configure_google_api_key():
    """
    Configures the Google AI Studio API key from secrets.json.

    Raises:
        ValueError: If the secrets.json file cannot be loaded or the 'google_api_key' is not set.
    """
    try:
        with open("secrets.json", "r") as f:
            secrets = json.load(f)
    except Exception as e:
        raise ValueError(f"Could not load secrets.json file: {e}")

    api_key = secrets.get("google_ai_studio_api_key")
    if not api_key:
        raise ValueError("Google AI Studio API key is not set in secrets.json. Please set the 'google_ai_studio_api_key' property.")

    genai.configure(api_key=api_key)


def generate_completion(prompt: str, model: str = "gemini-1.5-flash-latest", max_output_tokens: int = 100) -> str:
    """
    Generate a completion using the Google AI Studio API.

    Args:
        prompt (str): The prompt text to complete.
        model (str): The model to use (default: 'gemini-1.5-flash-latest').
        max_output_tokens (int): Maximum output tokens to generate (default: 100).

    Returns:
        str: The generated completion text.

    Raises:
        RuntimeError: If there is an error during the API request.
    """
    configure_google_api_key()  # Configure the API key first
    try:
        # Create the generative model instance
        gen_model = genai.GenerativeModel(model)
        
        # Define generation configuration
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=max_output_tokens
        )

        # Generate content
        response = gen_model.generate_content(
            prompt,
            generation_config=generation_config
        )

        # Check if the response has text
        if response.text:
             return response.text
        else:
            # Handle cases where the response might be blocked or empty
            # You might want to inspect response.prompt_feedback or response.candidates
            print("DEBUG: Full response:", response) 
            raise RuntimeError("Could not find text content in Google AI Studio response. The prompt might have been blocked.")

    except Exception as e:
        # Catch potential exceptions during API call or response processing
        raise RuntimeError(f"Error during Google AI Studio API request: {e}")

if __name__ == "__main__":
    # Test the functionality with a sample prompt.
    test_prompt = "What is the future of AI in simple terms?"
    print("Sending test prompt to Google AI Studio API...")
    print("Prompt: ", test_prompt)
    try:
        result = generate_completion(test_prompt, max_output_tokens=100)
        print("Received response:")
        print(result)
    except Exception as err:
        print("Error:", err)