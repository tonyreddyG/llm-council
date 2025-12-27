"""OpenRouter API client for making LLM requests."""

import httpx
from typing import List, Dict, Any, Optional
from .config import OPENROUTER_API_KEY, OPENROUTER_API_URL


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0,
    api_key: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Query a single model via OpenRouter API.

    Args:
        model: OpenRouter model identifier (e.g., "openai/gpt-4o")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds
        api_key: Optional user-specific API key (falls back to system default)

    Returns:
        Response dict with 'content' and optional 'reasoning_details', or None if failed
    """
    key_to_use = api_key if api_key else OPENROUTER_API_KEY
    headers = {
        "Authorization": f"Bearer {key_to_use}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            message = data['choices'][0]['message']

            return {
                'content': message.get('content'),
                'reasoning_details': message.get('reasoning_details')
            }

    except Exception as e:
        print(f"Error querying model {model}: {e}")
        return None


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]],
    api_key: Optional[str] = None
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Query multiple models in parallel.

    Args:
        models: List of OpenRouter model identifiers
        messages: List of message dicts to send to each model
        api_key: Optional user-specific API key (falls back to system default)

    Returns:
        Dict mapping model identifier to response dict (or None if failed)
    """
    import asyncio

    # Create tasks for all models
    tasks = [query_model(model, messages, api_key=api_key) for model in models]

    # Wait for all to complete
    responses = await asyncio.gather(*tasks)

    # Map models to their responses
    return {model: response for model, response in zip(models, responses)}

async def get_available_models(api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch the list of available models from OpenRouter.
    
    Args:
        api_key: Optional API key to use for the request
        
    Returns:
        List of model objects
    """
    url = "https://openrouter.ai/api/v1/models"
    key_to_use = api_key if api_key else OPENROUTER_API_KEY
    
    headers = {
        "Authorization": f"Bearer {key_to_use}",
        "Content-Type": "application/json",
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            models = data.get("data", [])
            print(f"Successfully fetched {len(models)} models from OpenRouter")
            return models
    except httpx.HTTPStatusError as e:
        print(f"HTTP error fetching models: {e.response.status_code} - {e.response.text}")
        return []
    except Exception as e:
        print(f"Error fetching models: {type(e).__name__}: {e}")
        return []
