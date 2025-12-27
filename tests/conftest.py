import os
import sys
import shutil
import tempfile
import pytest

# Add project root to path to ensure backend is discoverable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import storage

@pytest.fixture(scope="session", autouse=True)
def test_environment():
    """
    Setup a clean, temporary test environment for the duration of the test session.
    Automatically redirects all storage operations to a directory under tests/.
    """
    # Create a directory for test data under tests/
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_runtime_dir = os.path.join(project_root, "tests", "test_data_session")
    
    # Ensure it exists and is clean
    if os.path.exists(test_runtime_dir):
        shutil.rmtree(test_runtime_dir)
    os.makedirs(test_runtime_dir, exist_ok=True)
    
    test_data_dir = os.path.join(test_runtime_dir, "conversations")
    test_users_file = os.path.join(test_runtime_dir, "users.json")
    
    os.makedirs(test_data_dir, exist_ok=True)
    
    # Initialize users file
    with open(test_users_file, 'w') as f:
        f.write("{}")
    
    storage.configure_storage(data_dir=test_data_dir, users_file=test_users_file)
    print(f"DEBUG: conftest configured runtime at: {test_runtime_dir}")
    
    yield test_runtime_dir
    
    # Clean up after the session
    if os.path.exists(test_runtime_dir):
        shutil.rmtree(test_runtime_dir)

@pytest.fixture(autouse=True)
def clean_storage():
    """
    Ensure each test starts with empty users and no conversations.
    """
    # Clear users
    if os.path.exists(storage.USERS_FILE):
        with open(storage.USERS_FILE, 'w') as f:
            f.write("{}")
    
    # Clear conversations
    if os.path.exists(storage.DATA_DIR):
        for filename in os.listdir(storage.DATA_DIR):
            file_path = os.path.join(storage.DATA_DIR, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
    
    yield

@pytest.fixture
def client():
    """Provides a fresh TestClient for each test."""
    from fastapi.testclient import TestClient
    from backend.main import app
    return TestClient(app)

@pytest.fixture
def anyio_backend():
    return 'asyncio'
