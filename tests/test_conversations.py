import pytest
from unittest.mock import patch, AsyncMock
from backend import storage

# Mock responses for the council
MOCK_STAGE1_RESPONSES = {
    "google/gemini-2.5-flash": {"content": "Gemini response"},
    "openai/gpt-4o": {"content": "GPT-4o response"},
    "anthropic/claude-3.5-sonnet": {"content": "Claude response"}
}

MOCK_STAGE2_RANKINGS = {
    "google/gemini-2.5-flash": {"content": "FINAL RANKING:\n1. Response B\n2. Response A\n3. Response C"},
    "openai/gpt-4o": {"content": "FINAL RANKING:\n1. Response B\n2. Response C\n3. Response A"},
    "anthropic/claude-3.5-sonnet": {"content": "FINAL RANKING:\n1. Response A\n2. Response B\n3. Response C"}
}

MOCK_CHAIRMAN_RESPONSE = {"content": "Final synthesized answer based on all inputs."}

@pytest.fixture
def auth_headers(client):
    """Register a user and return auth headers."""
    # Try registering, ignore 400 (likely already exists)
    resp = client.post("/api/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "Test@Pass123"
    })
    if resp.status_code != 200:
        print(f"Registration failed with {resp.status_code}: {resp.text}")
        
    resp = client.post("/api/login", json={
        "username": "testuser",
        "password": "Test@Pass123"
    })
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        pytest.fail(f"Login failed: {resp.text}")
        
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_create_conversation(client, auth_headers):
    resp = client.post("/api/conversations", json={}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert data["title"] == "New Conversation"
    assert data["messages"] == []

@patch("backend.council.query_models_parallel")
@patch("backend.council.query_model")
def test_send_message_flow(mock_query_model, mock_query_parallel, client, auth_headers):
    # Setup mocks
    mock_query_parallel.side_effect = [
        MOCK_STAGE1_RESPONSES, # Stage 1 calls
        MOCK_STAGE2_RANKINGS   # Stage 2 calls
    ]
    mock_query_model.return_value = MOCK_CHAIRMAN_RESPONSE # Stage 3 call (and title gen)
    
    # Create conversation
    create_resp = client.post("/api/conversations", json={}, headers=auth_headers)
    conv_id = create_resp.json()["id"]
    
    # Send message
    resp = client.post(
        f"/api/conversations/{conv_id}/message", 
        json={"content": "Hello world"}, 
        headers=auth_headers
    )
    
    assert resp.status_code == 200
    data = resp.json()
    
    # Verify structure
    assert "stage1" in data
    assert len(data["stage1"]) > 0
    assert "stage2" in data
    assert "stage3" in data
    assert data["stage3"]["response"] == "Final synthesized answer based on all inputs."
    
    # Verify persistence
    conv_resp = client.get(f"/api/conversations/{conv_id}", headers=auth_headers)
    conv_data = conv_resp.json()
    assert len(conv_data["messages"]) == 2 # User + Assistant
    assert conv_data["messages"][0]["role"] == "user"
    assert conv_data["messages"][1]["role"] == "assistant"

def test_list_conversations_empty(client, auth_headers):
    resp = client.get("/api/conversations", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []

def test_get_nonexistent_conversation(client, auth_headers):
    resp = client.get("/api/conversations/nonexistent-id", headers=auth_headers)
    assert resp.status_code == 404
