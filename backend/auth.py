"""Authentication logic for LLM Council."""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import os
import hashlib
import secrets
import base64
import re
from . import storage

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_WINDOW_HOURS = 24

# No passlib - using built-in hashlib instead
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def validate_password_complexity(password: str):
    """Validate password complexity requirements."""
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
    
    if not re.search(r"[A-Z]", password):
        raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter")
    
    if not re.search(r"[a-z]", password):
        raise HTTPException(status_code=400, detail="Password must contain at least one lowercase letter")
        
    if not re.search(r"\d", password):
        raise HTTPException(status_code=400, detail="Password must contain at least one number")
    
    # Check for restricted characters FIRST (before checking special char requirement)
    if not re.match(r"^[A-Za-z\d!@#%()\-_+]*$", password):
        raise HTTPException(status_code=400, detail="Password contains restricted characters. Use only !@#%()-_+")
        
    # Check for at least one special character
    if not re.search(r"[!@#%()\-_+]", password):
        raise HTTPException(status_code=400, detail="Password must contain at least one special character (!@#%()-_+)")
    
    # Password cannot start or end with special character
    if re.match(r"^[!@#%()\-_+]", password) or re.search(r"[!@#%()\-_+]$", password):
        raise HTTPException(status_code=400, detail="Password cannot start or end with a special character")


def get_password_hash(password: str) -> str:
    """Hash password using PBKDF2-SHA256 (built-in, no external libs)."""
    # Generate a random salt
    salt = secrets.token_bytes(32)
    # Hash the password with PBKDF2
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    # Combine salt and hash, encode as base64 for storage
    storage_format = base64.b64encode(salt + pwd_hash).decode('utf-8')
    return f"pbkdf2:sha256:100000${storage_format}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash using PBKDF2-SHA256."""
    try:
        # Parse the stored format
        if not hashed_password.startswith("pbkdf2:sha256:100000$"):
            return False
        
        stored = hashed_password.split('$')[1]
        decoded = base64.b64decode(stored)
        
        # Extract salt (first 32 bytes) and hash (remaining bytes)
        salt = decoded[:32]
        stored_hash = decoded[32:]
        
        # Hash the provided password with the same salt
        pwd_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, 100000)
        
        # Constant-time comparison
        return secrets.compare_digest(pwd_hash, stored_hash)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    # Ensure initial_login is present as an integer
    if "initial_login" not in to_encode:
        import time
        to_encode["initial_login"] = int(time.time())
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user_from_token(token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        initial_login: float = payload.get("initial_login")
        
        if username is None or initial_login is None:
            raise credentials_exception
            
        # Check hard 24h limit
        login_time = datetime.fromtimestamp(initial_login)
        if datetime.utcnow() - login_time > timedelta(hours=REFRESH_WINDOW_HOURS):
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired (24h limit)",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Fetch full user data from storage to get email and other fields
        user = storage.get_user(username)
        if not user:
             raise credentials_exception
             
        # Add token-specific data to the user object
        user_data = user.copy()
        user_data["initial_login"] = initial_login
        
        # Remove sensitive data
        if "hashed_password" in user_data:
            del user_data["hashed_password"]
            
        return user_data
        
    except JWTError:
        raise credentials_exception


async def get_current_user(request: Request):
    token = None
    
    # Prefer Authorization header for easier testing and flexibility
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    
    # Fallback to cookie
    if not token:
        token = request.cookies.get("access_token")
        
    if not token:
          raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    # Remove "Bearer " prefix if it was somehow in the cookie (rare but happens in some manual tests)
    if token.startswith("Bearer "):
        token = token.split(" ")[1]
        
    return await get_current_user_from_token(token)
