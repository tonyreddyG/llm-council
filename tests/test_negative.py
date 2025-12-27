
import pytest
from fastapi.testclient import TestClient
import os
import sys
import json
from datetime import timedelta
import time

from backend.main import app
from backend import storage, auth

# Global client removed to use fixture instead

def test_login_invalid_credentials(client):
    # Attempt login without registration
    resp = client.post("/api/login", json={"username": "nonexistent", "password": "Password1!"})
    assert resp.status_code == 401
    assert "Incorrect" in resp.json()["detail"]

def test_register_invalid_email(client):
    resp = client.post("/api/register", json={
        "username": "user1",
        "email": "invalid-email-no-at-sign",
        "password": "A1b2C3d4!e"
    })
    assert resp.status_code == 400
    assert "Invalid email" in resp.json()["detail"]

def test_register_weak_password(client):
    weak_passwords = [
        "short",             # Too short
        "alllowercase1!",    # Missing uppercase
        "ALLUPPERCASE1!",    # Missing lowercase
        "NoSpecialChar123",  # Missing special
        "!StartsSpecial1",   # Starts with special
        "EndsSpecial1!",     # Ends with special
    ]
    for pw in weak_passwords:
        resp = client.post("/api/register", json={
            "username": "user1",
            "email": "user1@gmail.com",
            "password": pw
        })
        # 422 if caught by Pydantic (e.g. length), 400 if caught by manual validation
        assert resp.status_code in [400, 422]

def test_access_protected_without_auth(client):
    resp = client.get("/api/me")
    assert resp.status_code == 401
    
    resp = client.get("/api/conversations")
    assert resp.status_code == 401

def test_unauthorized_conversation_access(client):
    # Register user A
    client.post("/api/register", json={"username": "usera", "email": "a@gmail.com", "password": "UserA1!pass"})
    # Login A
    login_a = client.post("/api/login", json={"username": "usera", "password": "UserA1!pass"})
    token_a = login_a.json()["access_token"]
    
    # Register user B
    client.post("/api/register", json={"username": "userb", "email": "b@gmail.com", "password": "UserB1!pass"})
    # Login B
    login_b = client.post("/api/login", json={"username": "userb", "password": "UserB1!pass"})
    token_b = login_b.json()["access_token"]
    
    # A creates conversation
    create_resp = client.post("/api/conversations", json={}, headers={"Authorization": f"Bearer {token_a}"})
    conv_id = create_resp.json()["id"]
    
    # B tries to access A's conversation
    get_resp = client.get(f"/api/conversations/{conv_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert get_resp.status_code == 403
    
    # B tries to send message to A's conversation
    msg_resp = client.post(f"/api/conversations/{conv_id}/message", json={"content": "hello"}, headers={"Authorization": f"Bearer {token_b}"})
    assert msg_resp.status_code == 403

def test_nonexistent_conversation_access(client):
    client.post("/api/register", json={"username": "usera", "email": "a@gmail.com", "password": "UserA1!pass"})
    client.post("/api/login", json={"username": "usera", "password": "UserA1!pass"})
    
    resp = client.get("/api/conversations/nonexistent-id")
    assert resp.status_code == 404

def test_empty_message(client):
    client.post("/api/register", json={"username": "usera", "email": "a@gmail.com", "password": "UserA1!pass"})
    client.post("/api/login", json={"username": "usera", "password": "UserA1!pass"})
    create_resp = client.post("/api/conversations", json={})
    conv_id = create_resp.json()["id"]
    
    # Verify empty message is rejected (min_length=1)
    resp = client.post(f"/api/conversations/{conv_id}/message", json={"content": ""})
    assert resp.status_code == 422 # Pydantic validation error

def test_extremely_long_message(client):
    client.post("/api/register", json={"username": "usera", "email": "a@gmail.com", "password": "UserA1!pass"})
    client.post("/api/login", json={"username": "usera", "password": "UserA1!pass"})
    create_resp = client.post("/api/conversations", json={})
    conv_id = create_resp.json()["id"]
    
    # Verify extremely long message is rejected (max_length=5000)
    resp = client.post(f"/api/conversations/{conv_id}/message", json={"content": "A" * 5001})
    assert resp.status_code == 422

def test_extremely_long_password(client):
    # Check the 100 char limit in login (Pydantic max_length=100)
    resp = client.post("/api/login", json={"username": "usera", "password": "A" * 101})
    assert resp.status_code == 422

def test_dual_session_concurrent(client):
    # 1. Register a user
    username = "dualuser"
    email = "dual@gmail.com"
    password = "A1b2C3d4!dual"
    client.post("/api/register", json={"username": username, "email": email, "password": password})
    
    # 2. Login - First Session
    login1 = client.post("/api/login", json={"username": username, "password": password})
    token1 = login1.cookies["access_token"]
    
    # Wait to ensure timestamp difference
    time.sleep(1.1)
    
    # 3. Login - Second Session (should NOT invalidate first)
    login2 = client.post("/api/login", json={"username": username, "password": password})
    token2 = login2.json()["access_token"]
    
    # 4. Verify Token 1 still works
    resp1 = client.get("/api/me", headers={"Authorization": f"Bearer {token1}"})
    assert resp1.status_code == 200
    assert resp1.json()["username"] == username

    # 5. Verify Token 2 also works
    resp2 = client.get("/api/me", headers={"Authorization": f"Bearer {token2}"})
    assert resp2.status_code == 200
    assert resp2.json()["username"] == username

def test_registration_duplicate(client):
    reg_data = {
        "username": "idemuser",
        "email": "idem@gmail.com",
        "password": "A1b2C3d4!idem"
    }
    # First registration
    resp1 = client.post("/api/register", json=reg_data)
    assert resp1.status_code == 200
    
    # Second registration with same data (Should FAIL now)
    resp2 = client.post("/api/register", json=reg_data)
    assert resp2.status_code == 400
    assert "registered" in resp2.json()["detail"]
    
    # Third registration with different username, same email (Should FAIL)
    reg_data_email = reg_data.copy()
    reg_data_email["username"] = "differentuser"
    resp3 = client.post("/api/register", json=reg_data_email)
    assert resp3.status_code == 400
    assert "Email already registered" in resp3.json()["detail"]

if __name__ == "__main__":
    pytest.main([__file__])
