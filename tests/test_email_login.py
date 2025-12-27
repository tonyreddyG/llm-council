
import pytest
from fastapi.testclient import TestClient
from backend.main import app

def test_login_by_username_and_email(client):
    # 1. Register a user
    username = "emailuser"
    email = "emailuser@example.com"
    password = "A1b2C3d4!email"
    
    reg_resp = client.post("/api/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    assert reg_resp.status_code == 200
    
    # 2. Login by Username
    login_user = client.post("/api/login", json={
        "username": username,
        "password": password
    })
    assert login_user.status_code == 200
    assert "access_token" in login_user.json()
    
    # 3. Login by Email
    login_email = client.post("/api/login", json={
        "username": email,
        "password": password
    })
    assert login_email.status_code == 200
    assert "access_token" in login_email.json()
    
    # 4. Login with wrong email
    login_bad_email = client.post("/api/login", json={
        "username": "wrong@example.com",
        "password": password
    })
    assert login_bad_email.status_code == 401
    
    # 5. Login with wrong password
    login_bad_pass = client.post("/api/login", json={
        "username": email,
        "password": "WrongPassword1!"
    })
    assert login_bad_pass.status_code == 401
