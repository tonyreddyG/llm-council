import urllib.request
import urllib.error
import urllib.parse
import json
import sys

BASE_URL = "http://localhost:8001/api"
TEST_USER = "testuser_dup_urllib"
TEST_EMAIL = "testuser_dup_urllib@example.com"
TEST_PASS = "TestPass123!@#a"

def register_user(username, email, password):
    print(f"Registering user: {username}, {email}")
    url = f"{BASE_URL}/register"
    data = json.dumps({
        "username": username,
        "email": email,
        "password": password
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers={
        'Content-Type': 'application/json'
    }, method='POST')
    
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except urllib.error.URLError as e:
        print(f"Error: Could not connect to backend. {e}")
        sys.exit(1)

def main():
    print("--- Reproduction Script (urllib) ---")
    
    # 2. Register first time
    status1, text1 = register_user(TEST_USER, TEST_EMAIL, TEST_PASS)
    print(f"First registration: Status {status1}")
    print(f"Response: {text1}")
    
    if status1 == 200:
        print("-> Success (Expected)")
    elif status1 == 400 and "already registered" in text1:
         print("-> User already exists from previous run.")
    else:
        print(f"-> Unexpected status: {status1}")

    # 3. Register SAME user again
    print("\nAttempting Duplicate Registration...")
    status2, text2 = register_user(TEST_USER, TEST_EMAIL, "NewPass456!@#b")
    print(f"Second registration: Status {status2}")
    print(f"Response: {text2}")

    if status2 == 200:
        print("FAIL: Duplicate registration SUCCEEDED! (This is the bug)")
    elif status2 == 400:
        print("PASS: Duplicate registration rejected.")
    else:
        print(f"-> Unexpected status: {status2}")

if __name__ == "__main__":
    main()
