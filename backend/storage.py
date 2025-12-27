"""JSON-based storage for conversations."""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import threading
import time

from . import config

DATA_DIR = config.DATA_DIR
USERS_FILE = config.USERS_FILE

# Lock for user operations to prevent race conditions
user_lock = threading.Lock()


def configure_storage(data_dir: Optional[str] = None, users_file: Optional[str] = None):
    """Dynamically reconfigure storage paths (primarily for testing)."""
    global DATA_DIR, USERS_FILE
    if data_dir:
        DATA_DIR = data_dir
    if users_file:
        USERS_FILE = users_file


def ensure_data_dir():
    """Ensure the data directory exists."""
    # Create the base directory if it doesn't exist
    data_dir_path = Path(DATA_DIR)
    if not data_dir_path.parent.exists():
        data_dir_path.parent.mkdir(parents=True, exist_ok=True)
    
    data_dir_path.mkdir(parents=True, exist_ok=True)
    
    # Create users file if it doesn't exist
    if not os.path.exists(USERS_FILE):
        # Also ensure parent directory for USERS_FILE exists
        Path(USERS_FILE).parent.mkdir(parents=True, exist_ok=True)
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)


def _read_users() -> Dict[str, Any]:
    """Helper to read all users."""
    ensure_data_dir()
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r') as f:
        return json.load(f)


def _write_users(users: Dict[str, Any]):
    """Helper to write all users."""
    ensure_data_dir()
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)


def get_conversation_path(conversation_id: str) -> str:
    """Get the file path for a conversation."""
    return os.path.join(DATA_DIR, f"{conversation_id}.json")



def create_conversation(conversation_id: str, user_id: str) -> Dict[str, Any]:
    """
    Create a new conversation.

    Args:
        conversation_id: Unique identifier for the conversation
        user_id: ID of the user creating the conversation

    Returns:
        New conversation dict
    """
    ensure_data_dir()

    conversation = {
        "id": conversation_id,
        "user_id": user_id,
        "created_at": datetime.utcnow().isoformat(),
        "title": "New Conversation",
        "messages": []
    }

    # Save to file
    path = get_conversation_path(conversation_id)
    with open(path, 'w') as f:
        json.dump(conversation, f, indent=2)

    return conversation


def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a conversation from storage.

    Args:
        conversation_id: Unique identifier for the conversation

    Returns:
        Conversation dict or None if not found
    """
    path = get_conversation_path(conversation_id)

    if not os.path.exists(path):
        return None

    with open(path, 'r') as f:
        return json.load(f)


def save_conversation(conversation: Dict[str, Any]):
    """
    Save a conversation to storage.

    Args:
        conversation: Conversation dict to save
    """
    ensure_data_dir()

    path = get_conversation_path(conversation['id'])
    with open(path, 'w') as f:
        json.dump(conversation, f, indent=2)



def list_conversations(user_id: str) -> List[Dict[str, Any]]:
    """
    List all conversations for a specific user (metadata only).

    Args:
        user_id: ID of the user to list conversations for

    Returns:
        List of conversation metadata dicts
    """
    ensure_data_dir()

    conversations = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.json'):
            path = os.path.join(DATA_DIR, filename)
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    
                    # Filter by user_id
                    if data.get("user_id") != user_id:
                        continue
                        
                    # Return metadata only
                    conversations.append({
                        "id": data["id"],
                        "created_at": data["created_at"],
                        "title": data.get("title", "New Conversation"),
                        "message_count": len(data["messages"])
                    })
            except Exception:
                continue  # Skip unreadable files

    # Sort by creation time, newest first
    conversations.sort(key=lambda x: x["created_at"], reverse=True)

    return conversations


def add_user_message(conversation_id: str, content: str):
    """
    Add a user message to a conversation.

    Args:
        conversation_id: Conversation identifier
        content: User message content
    """
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    conversation["messages"].append({
        "role": "user",
        "content": content
    })

    save_conversation(conversation)


def add_assistant_message(
    conversation_id: str,
    stage1: List[Dict[str, Any]],
    stage2: List[Dict[str, Any]],
    stage3: Dict[str, Any]
):
    """
    Add an assistant message with all 3 stages to a conversation.

    Args:
        conversation_id: Conversation identifier
        stage1: List of individual model responses
        stage2: List of model rankings
        stage3: Final synthesized response
    """
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    conversation["messages"].append({
        "role": "assistant",
        "stage1": stage1,
        "stage2": stage2,
        "stage3": stage3
    })

    save_conversation(conversation)


def update_conversation_title(conversation_id: str, title: str):
    """
    Update the title of a conversation.

    Args:
        conversation_id: Conversation identifier
        title: New title for the conversation
    """
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    conversation["title"] = title
    save_conversation(conversation)


def delete_conversation(conversation_id: str):
    """Delete a conversation file."""
    import os
    filepath = os.path.join(DATA_DIR, f"{conversation_id}.json")
    if os.path.exists(filepath):
        os.remove(filepath)
    else:
        raise ValueError(f"Conversation {conversation_id} not found")


def get_user(username: str) -> Optional[Dict[str, Any]]:
    """Get a user by username."""
    with user_lock:
        users = _read_users()
        return users.get(username)


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get a user by email."""
    with user_lock:
        users = _read_users()
        for user in users.values():
            if user.get("email") == email:
                return user
    return None


def create_user(username: str, email: str, password_hash: str) -> Dict[str, Any]:
    """Create a new user with email."""
    with user_lock:
        users = _read_users()
            
        if username in users:
            raise ValueError("Username already exists")
        
        # Case insensitive check for username
        for u in users.keys():
            if u.lower() == username.lower():
                raise ValueError("Username already exists")
            
        # Check email uniqueness
        for user in users.values():
            if user.get("email") == email:
                 raise ValueError("Email already registered")
            
        users[username] = {
            "username": username,
            "email": email,
            "hashed_password": password_hash,
            "created_at": datetime.utcnow().isoformat(),
            "last_login_at": int(time.time())
        }
        
        _write_users(users)
            
    return users[username]


def update_user_last_login(username: str, timestamp: Optional[float] = None):
    """Update the last_login_at timestamp for a user."""
    if timestamp is None:
        timestamp = int(time.time())
    else:
        timestamp = int(timestamp)
        
    with user_lock:
        users = _read_users()
            
        if username in users:
            users[username]["last_login_at"] = timestamp
            _write_users(users)


def update_user_password(username: str, new_password_hash: str):
    """Update a user's password."""
    with user_lock:
        users = _read_users()
        if username not in users:
            raise ValueError("User not found")
        
        users[username]["hashed_password"] = new_password_hash
        _write_users(users)


def update_user_username(old_username: str, new_username: str) -> Dict[str, Any]:
    """
    Update a user's username.
    This requires updating the user record AND all conversations owned by this user.
    """
    with user_lock:
        users = _read_users()
        
        if old_username not in users:
            print(f"DEBUG: usage logic - User {old_username} not found in users: {list(users.keys())}")
            raise ValueError("User not found")
            
        if new_username in users:
            raise ValueError("New username already taken")
            
        # Case insensitive check
        for u in users.keys():
            if u.lower() == new_username.lower() and u != old_username:
                raise ValueError("New username already taken")
                
        # 1. Create new user record copy
        user_data = users[old_username].copy()
        user_data["username"] = new_username
        
        # 2. Add new user, remove old user
        print(f"DEBUG: updating users list. Adding {new_username}, Removing {old_username}")
        users[new_username] = user_data
        del users[old_username]
        
        _write_users(users)
        print("DEBUG: _write_users called")
        
    # 3. Update all conversations (separate lock/operation might be safer but strict consistency is hard with files)
    # We do this OUTSIDE the user_lock to avoid holding it too long, but techically a race could happen if user creates convo NOW.
    # Given the scale, this is acceptable.
    _update_conversations_user_id(old_username, new_username)
    
    return user_data


def delete_user(username: str):
    """
    Delete a user and all their conversations.
    """
    with user_lock:
        users = _read_users()
        if username in users:
            del users[username]
            _write_users(users)
            
    # Delete conversations
    ensure_data_dir()
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.json'):
            path = os.path.join(DATA_DIR, filename)
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                
                if data.get("user_id") == username:
                    # Close file before deleting
                    pass 
                else:
                    continue
                    
                # Re-check and delete
                os.remove(path)
            except Exception:
                continue


def _update_conversations_user_id(old_user_id: str, new_user_id: str):
    """Helper to update user_id in all conversations."""
    ensure_data_dir()
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.json'):
            path = os.path.join(DATA_DIR, filename)
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                
                if data.get("user_id") == old_user_id:
                    data["user_id"] = new_user_id
                    with open(path, 'w') as f:
                        json.dump(data, f, indent=2)
            except Exception:
                continue


def update_user_preferences(username: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update user preferences (models, api_key, etc).
    
    Args:
        username: The username to update
        preferences: Dict of preferences to merge/set
        
    Returns:
        Updated user dict
    """
    with user_lock:
        users = _read_users()
        if username not in users:
            raise ValueError("User not found")
        
        user = users[username]
        
        # Update allowed fields
        allowed_fields = ["council_models", "chairman_model", "openrouter_api_key"]
        
        for field in allowed_fields:
            if field in preferences:
                user[field] = preferences[field]
                
        _write_users(users)
        return user
