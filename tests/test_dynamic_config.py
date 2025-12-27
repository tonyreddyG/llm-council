
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from backend import council, storage, openrouter, config

# Mock available models response
MOCK_MODELS_RESPONSE = {
    "data": [
        {"id": "model/a", "name": "Model A", "pricing": {"input": "0", "output": "0"}},
        {"id": "model/b", "name": "Model B", "pricing": {"input": "0", "output": "0"}},
        {"id": "paid/c", "name": "Paid Model C", "pricing": {"input": "1", "output": "1"}}
    ]
}

@pytest.mark.asyncio
async def test_get_available_models_default():
    """Test fetching models uses default key if none provided."""
    # Patch httpx.AsyncClient to return a properly mocked client
    with patch("backend.config.OPENROUTER_API_KEY", "sk-system-default"), \
         patch("backend.openrouter.OPENROUTER_API_KEY", "sk-system-default"), \
         patch("httpx.AsyncClient") as mock_client_cls:
        
        # Create mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=MOCK_MODELS_RESPONSE)
        mock_response.raise_for_status = MagicMock()
        
        # Create mock client
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        # Make AsyncClient() return our mock client
        mock_client_cls.return_value = mock_client
        
        models = await openrouter.get_available_models(api_key=None)
        
        assert len(models) == 3
        assert models[0]['id'] == 'model/a'
        
        # Verify the call was made with correct headers
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        headers = call_args[1]['headers']
        assert headers['Authorization'] == "Bearer sk-system-default"

@pytest.mark.asyncio
async def test_get_available_models_custom_key():
    """Test fetching models uses custom key."""
    custom_key = "sk-custom-123"
    with patch("httpx.AsyncClient") as mock_client_cls:
        # Create mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=MOCK_MODELS_RESPONSE)
        mock_response.raise_for_status = MagicMock()
        
        # Create mock client
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        mock_client_cls.return_value = mock_client
        
        models = await openrouter.get_available_models(api_key=custom_key)
        
        assert len(models) == 3
        
        call_args = mock_client.get.call_args
        headers = call_args[1]['headers']
        assert headers['Authorization'] == f"Bearer {custom_key}"

def test_user_preference_storage(clean_storage):
    """Test saving and retrieving user preferences."""
    # Create user
    storage.create_user("pref_user", "pref@test.com", "hash")
    
    # Update prefs
    prefs = {
        "council_models": ["model/a", "model/b"],
        "chairman_model": "model/b",
        "openrouter_api_key": "sk-user-key"
    }
    
    updated_user = storage.update_user_preferences("pref_user", prefs)
    
    assert updated_user["council_models"] == ["model/a", "model/b"]
    assert updated_user["chairman_model"] == "model/b"
    assert updated_user["openrouter_api_key"] == "sk-user-key"
    
    # Verify persistence
    loaded_user = storage.get_user("pref_user")
    assert loaded_user["openrouter_api_key"] == "sk-user-key"

@pytest.mark.asyncio
async def test_council_uses_custom_models():
    """Test that council logic respects passed model lists."""
    
    # Mock query_models_parallel and query_model
    with patch("backend.council.query_models_parallel", new_callable=AsyncMock) as mock_parallel, \
         patch("backend.council.query_model", new_callable=AsyncMock) as mock_single:
         
        # Setup mocks
        mock_parallel.return_value = {
            "custom/model-1": {"content": "Resp 1"},
            "custom/model-2": {"content": "Resp 2"}
        }
        mock_single.return_value = {"content": "Final Answer"}
        
        user_query = "Hello"
        custom_council = ["custom/model-1", "custom/model-2"]
        custom_chair = "custom/chair"
        custom_key = "sk-run-key"
        
        await council.run_full_council(
            user_query,
            council_models=custom_council,
            chairman_model=custom_chair,
            api_key=custom_key
        )
        
        # Verify Stage 1 used custom council
        mock_parallel.assert_any_call(custom_council, [{"role": "user", "content": user_query}], api_key=custom_key)
        
        # Verify Stage 3 used custom chair
        # Check calls to find chairman usage
        calls = mock_single.call_args_list
        chairman_called = False
        for call in calls:
            args, kwargs = call
            if args[0] == custom_chair and kwargs.get('api_key') == custom_key:
                chairman_called = True
                break
        
        assert chairman_called, "Chairman model was not queried with custom key"

