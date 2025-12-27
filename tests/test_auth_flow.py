
import pytest
import os
import sys
import time
from fastapi.testclient import TestClient
from datetime import timedelta

from backend.main import app
from backend import storage, auth

# Global client removed to use fixture instead

def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "LLM Council API"}

def _register_and_login_user(client, prefix="testuser"):
    ts = int(time.time() * 1000) # Use ms for better unique
    username = f"{prefix}_{ts}"
    email = f"{prefix}_{ts}@gmail.com"
    password = "Strong!Pass1"

    # 1. Register
    reg_resp = client.post("/api/register", json={"username": username, "email": email, "password": password})
    assert reg_resp.status_code == 200
    
    # 2. Login
    login_resp = client.post("/api/login", json={"username": username, "password": password})
    assert login_resp.status_code == 200
    return username, login_resp.json()["access_token"], login_resp.cookies["access_token"]

def test_register_and_login(client):
    username, token, cookie = _register_and_login_user(client, "reglog")
    assert token is not None
    assert cookie is not None

def test_protected_route_access(client):
    username, token, cookie = _register_and_login_user(client, "protected")
    
    # Access with header
    resp = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == username

def test_isolation(client):
    ts = int(time.time())
    # User A
    user_a = f"usera_{ts}"
    email_a = f"a_{ts}@gmail.com"
    pw = "Strong!Pass1"
    client.post("/api/register", json={"username": user_a, "email": email_a, "password": pw})
    login_a = client.post("/api/login", json={"username": user_a, "password": pw})
    token_a = login_a.json()["access_token"]
    
    # User B
    user_b = f"userb_{ts}"
    email_b = f"b_{ts}@gmail.com"
    client.post("/api/register", json={"username": user_b, "email": email_b, "password": pw})
    login_b = client.post("/api/login", json={"username": user_b, "password": pw})
    token_b = login_b.json()["access_token"]

    # A creates conversation
    create_resp = client.post("/api/conversations", json={}, headers={"Authorization": f"Bearer {token_a}"})
    assert create_resp.status_code == 200
    conv_id = create_resp.json()["id"]
    
    # A sees it
    list_a = client.get("/api/conversations", headers={"Authorization": f"Bearer {token_a}"})
    ids_a = [c["id"] for c in list_a.json()]
    assert conv_id in ids_a
    
    # B should NOT see it
    list_b = client.get("/api/conversations", headers={"Authorization": f"Bearer {token_b}"})
    ids_b = [c["id"] for c in list_b.json()]
    assert conv_id not in ids_b
    
    # B tries to access directly
    get_b = client.get(f"/api/conversations/{conv_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert get_b.status_code == 403

def test_token_format(client):
    token = auth.create_access_token({"sub": "test", "initial_login": int(time.time())})
    decoded = auth.jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
    assert decoded["sub"] == "test"
