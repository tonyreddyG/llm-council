from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# --- Auth Models ---

class UserLogin(BaseModel):
    username: str
    password: str = Field(..., max_length=100)

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=8, max_length=20)

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=100)

class ChangeUsernameRequest(BaseModel):
    new_username: str = Field(..., min_length=3, max_length=50)

# --- Conversation Models ---

class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    pass


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation."""
    content: str = Field(..., min_length=1, max_length=5000)


class ConversationMetadata(BaseModel):
    """Conversation metadata for list view."""
    id: str
    created_at: str
    title: str
    message_count: int


class Conversation(BaseModel):
    """Full conversation with all messages."""
    id: str
    created_at: str
    title: str
    messages: List[Dict[str, Any]]
