import pytest
from backend import auth

def test_case_insensitive_duplicate_registration(client):
    """Ensure we cannot register 'User1' if 'user1' exists."""
    # 1. Register user1
    resp = client.post("/api/register", json={
        "username": "user1",
        "email": "user1@example.com",
        "password": "Password123!a"
    })
    assert resp.status_code == 200
    
    # 2. Register User1 (different case)
    resp = client.post("/api/register", json={
        "username": "User1",
        "email": "user1_diff@example.com",
        "password": "Password123!a"
    })
    
    # ...
    
def test_change_password(client):
    # 1. Register and Login
    client.post("/api/register", json={
        "username": "pwuser",
        "email": "pw@ex.com",
        "password": "OldPassword1!a"
    })
    login_resp = client.post("/api/login", json={
        "username": "pwuser",
        "password": "OldPassword1!a"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Change PW with wrong old PW
    resp = client.post("/api/change-password", json={
        "old_password": "WrongPassword!a",
        "new_password": "NewPassword1!a"
    }, headers=headers)
    assert resp.status_code == 400
    assert "Incorrect old password" in resp.json()["detail"]
    
    # 3. Change PW successfully
    resp = client.post("/api/change-password", json={
        "old_password": "OldPassword1!a",
        "new_password": "NewPassword1!a"
    }, headers=headers)
    assert resp.status_code == 200
    
    # 4. Login with old PW fails
    resp = client.post("/api/login", json={
        "username": "pwuser",
        "password": "OldPassword1!a"
    })
    assert resp.status_code == 401
    
    # 5. Login with new PW succeeds
    resp = client.post("/api/login", json={
        "username": "pwuser",
        "password": "NewPassword1!a"
    })
    assert resp.status_code == 200

def test_change_username(client):
    # 1. Register userA and userB
    client.post("/api/register", json={"username": "userA", "email": "a@ex.com", "password": "Password1!a"})
    client.post("/api/register", json={"username": "userB", "email": "b@ex.com", "password": "Password1!a"})
    
    # Login as userA
    login_resp = client.post("/api/login", json={"username": "userA", "password": "Password1!a"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # ...
    
    # 4. Success change to userC
    print("DEBUG: Calling change-username to userC")
    resp = client.post("/api/change-username", json={"new_username": "userC"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "userC"
    
    # 5. Verify via /me using the NEW token (cookie) or just get new token
    # The endpoint returns a new cookie, but TestClient handles cookies automatically if we use the session or extract it.
    # However, for simplicity let's just try logging in with new username.
    print("DEBUG: Logging in as userC")
    resp = client.post("/api/login", json={"username": "userC", "password": "Password1!a"})
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        from backend import storage
        print(f"DEBUG USERS: {storage._read_users()}")
    assert resp.status_code == 200
    
    resp = client.post("/api/login", json={"username": "userA", "password": "Password1!a"})
    assert resp.status_code == 401

def test_delete_account(client):
    # 1. Register and Login
    client.post("/api/register", json={"username": "deluser", "email": "del@ex.com", "password": "Password1!a"})
    login_resp = client.post("/api/login", json={"username": "deluser", "password": "Password1!a"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Delete
    resp = client.delete("/api/me", headers=headers)
    assert resp.status_code == 200
    
    # 3. Try Login
    resp = client.post("/api/login", json={"username": "deluser", "password": "Password1!"})
    assert resp.status_code == 401
