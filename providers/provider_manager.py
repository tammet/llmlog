# providers/provider_manager.py

import inspect # Import inspect module

# Import provider-specific functions at the top level
from .anthropic_client import generate_completion as anthropic_generate_completion
from .openai_client import generate_completion as openai_generate_completion
from .google_client import generate_completion as google_generate_completion

# Create a dispatch dictionary mapping provider names to functions
PROVIDER_MAP = {
    "anthropic": anthropic_generate_completion,
    "openai": openai_generate_completion,
    "google": google_generate_completion,
    # Add other providers here as needed
}

def generate_completion(provider: str, prompt: str, **kwargs) -> str:
    """
    Generate a completion using the specified provider.

    Args:
        provider (str): The provider name (e.g., 'anthropic', 'openai', 'google').
        prompt (str): The prompt text to complete.
        **kwargs: Additional arguments to pass to the provider-specific function
                  (e.g., max_tokens, max_output_tokens).

    Returns:
        str: The generated completion text.

    Raises:
        ValueError: If the provider is unknown.
        ImportError: If a provider's module cannot be imported.
        RuntimeError: If there's an error during the API call for a provider.
    """
    provider = provider.lower()
    generate_func = PROVIDER_MAP.get(provider)

    if generate_func:
        # Inspect the target function's signature
        sig = inspect.signature(generate_func)
        valid_kwargs = sig.parameters.keys()

        # Filter kwargs to only include those accepted by the target function
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_kwargs}

        # Call the selected provider's function with the prompt and filtered args
        return generate_func(prompt, **filtered_kwargs)
    else:
        raise ValueError(f"Unknown or unsupported provider: {provider}. Available: {list(PROVIDER_MAP.keys())}")


if __name__ == "__main__":
    # Test the provider manager with multiple providers
    test_prompt = "Explain the concept of cloud computing in one sentence."
    providers_to_test = ["anthropic", "openai", "google"]
    # Common arguments - note that providers might ignore irrelevant ones
    common_args = {"max_tokens": 1500, "max_output_tokens": 1500}

    print(f"Testing prompt: \"{test_prompt}\"")
    print("-" * 30)

    for provider_name in providers_to_test:
        print(f"--- Using {provider_name.capitalize()} provider ---")
        try:
            response = generate_completion(provider_name, test_prompt, **common_args)
            print("Response:")
            print(response)
        except ValueError as ve:
            print(f"Configuration Error: {ve}")
        except ImportError as ie:
            print(f"Import Error: Could not import module for {provider_name}. {ie}")
        except RuntimeError as re:
            print(f"API Error: {re}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        print("-" * 30)

    # Test with an unknown provider
    print("--- Testing Unknown Provider ---")
    try:
        generate_completion("unknown_provider", test_prompt)
    except ValueError as e:
        print(f"Caught expected error: {e}")
    print("-" * 30) 