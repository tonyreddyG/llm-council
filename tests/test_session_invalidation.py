
import pytest
from fastapi.testclient import TestClient
from datetime import timedelta
import os
import sys
import time

from backend.main import app
from backend import storage, auth

# Global client removed to use fixture instead

def test_session_invalidation(client):
    # 1. Register a user
    username = "sessiontest"
    email = "sessiontest@gmail.com"
    password = "A1b2C3d4!e5"
    
    reg_resp = client.post("/api/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    assert reg_resp.status_code == 200
    
    # 2. Login - First Session (Token 1)
    login1_resp = client.post("/api/login", json={
        "username": username,
        "password": password
    })
    assert login1_resp.status_code == 200
    token1 = login1_resp.cookies["access_token"]
    
    # Verify Token 1 works
    me1_resp = client.get("/api/me", headers={"Authorization": f"Bearer {token1}"})
    assert me1_resp.status_code == 200
    assert me1_resp.json()["username"] == username
    
    # Wait a second to ensure timestamp difference
    time.sleep(1.1)
    
    # 3. Login - Second Session (Token 2)
    login2_resp = client.post("/api/login", json={
        "username": username,
        "password": password
    })
    assert login2_resp.status_code == 200
    token2 = login2_resp.json()["access_token"]
    
    # Verify Token 2 works
    me2_resp = client.get("/api/me", headers={"Authorization": f"Bearer {token2}"})
    assert me2_resp.status_code == 200
    assert me2_resp.json()["username"] == username
    
    # 4. Verify Token 1 is still VALID (Concurrent Sessions)
    me1_valid_resp = client.get("/api/me", headers={"Authorization": f"Bearer {token1}"})
    assert me1_valid_resp.status_code == 200
    assert me1_valid_resp.json()["username"] == username
    
    print("Concurrent sessions test passed!")

if __name__ == "__main__":
    # Note: Hand-running this will fail without the fixture
    print("Run with: pytest " + __file__)
