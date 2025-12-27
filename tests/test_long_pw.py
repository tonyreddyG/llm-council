
def test_long_password(client):
    # Registration with 100 char password
    payload = {
        "username": "longpwuser",
        "email": "long@gmail.com",
        "password": "A" * 100
    }
    print(f"Testing registration with 100 char password...")
    resp = client.post("/api/register", json=payload)
    print(f"Status: {resp.status_code}")
    print(f"Detail: {resp.json().get('detail')}")
    
    # Login with 100 char password
    payload_login = {
        "username": "diaguser",
        "password": "B" * 100
    }
    print(f"\nTesting login with 100 char password...")
    resp_login = client.post("/api/login", json=payload_login)
    print(f"Status: {resp_login.status_code}")
    print(f"Detail: {resp_login.json().get('detail')}")
