from fastapi import APIRouter, HTTPException, Depends, Response, status, Request
from .. import storage, auth
from ..schemas import UserLogin, UserRegister, ChangePasswordRequest, ChangeUsernameRequest
import time

router = APIRouter(prefix="/api", tags=["auth"])

@router.post("/register")
async def register(user: UserRegister):
    try:
        # Validate email format (basic check)
        if "@" not in user.email or "." not in user.email:
             raise HTTPException(status_code=400, detail="Invalid email format.")

        # Validate password
        auth.validate_password_complexity(user.password)

        # Check if username exists
        if storage.get_user(user.username):
            print(f"Username {user.username} already taken")
            raise HTTPException(status_code=400, detail="Username already registered")
            
        # Check if email exists
        if storage.get_user_by_email(user.email):
            print(f"Email {user.email} already taken")
            raise HTTPException(status_code=400, detail="Email already registered")
        
        print(f"Creating new user: {user.username}")
        hashed_password = auth.get_password_hash(user.password)
        storage.create_user(user.username, user.email, hashed_password)
        return {"message": "User registered successfully"}
    except HTTPException:
        print(f"HTTP Error during registration")
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login")
async def login(user_data: UserLogin, response: Response):
    # Try to find user by username first
    db_user = storage.get_user(user_data.username)
    
    # If not found by username, try by email
    if not db_user:
        db_user = storage.get_user_by_email(user_data.username)
        
    if not db_user or not auth.verify_password(user_data.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username, email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Use a unified integer timestamp for consistency
    login_ts = int(time.time())
    
    # Update last_login_at in storage
    storage.update_user_last_login(db_user["username"], timestamp=login_ts)
    
    access_token = auth.create_access_token(
        data={"sub": db_user["username"], "initial_login": login_ts}
    )
    
    # Set HttpOnly cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=3600 * 24,  # 24 hours
        samesite="lax",
        secure=False
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_me(current_user: dict = Depends(auth.get_current_user)):
    return current_user


@router.post("/refresh")
async def refresh_token(response: Response, current_user: dict = Depends(auth.get_current_user)):
    # Create new token with same initial_login to preserve session
    new_token = auth.create_access_token(
        data={"sub": current_user["username"], "initial_login": current_user["initial_login"]}
    )
    
    response.set_cookie(
        key="access_token",
        value=new_token,
        httponly=True,
        max_age=3600 * 24,
        samesite="lax",
        secure=False
    )
    
    return {"status": "refreshed"}


@router.post("/change-password")
async def change_password(request: ChangePasswordRequest, current_user: dict = Depends(auth.get_current_user)):
    username = current_user["username"]
    
    # Fetch full user record to get the hashed password
    user_record = storage.get_user(username)
    if not user_record:
        raise HTTPException(status_code=404, detail="User not found")

    # 1. Verify old password
    if not auth.verify_password(request.old_password, user_record["hashed_password"]):
        raise HTTPException(
            status_code=400,
            detail="Incorrect old password"
        )
        
    # 2. Validate new password complexity
    auth.validate_password_complexity(request.new_password)
    
    # 3. Update password
    new_hash = auth.get_password_hash(request.new_password)
    try:
        storage.update_user_password(current_user["username"], new_hash)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    return {"message": "Password updated successfully"}


@router.post("/change-username")
async def change_username(
    request: ChangeUsernameRequest, 
    response: Response,
    current_user: dict = Depends(auth.get_current_user)
):
    print(f"DEBUG: change_username endpoint called with {request.new_username}")
    old_username = current_user["username"]
    new_username = request.new_username
    
    if old_username == new_username:
         raise HTTPException(status_code=400, detail="New username must be different")
    
    try:
        # Update username in storage (and all linked conversations)
        new_user_data = storage.update_user_username(old_username, new_username)
        
        # Issue new token with new username to prevent immediate logout/auth error
        # Preserve initial login time
        access_token = auth.create_access_token(
            data={"sub": new_username, "initial_login": current_user["initial_login"]}
        )
        
        # Set new cookie
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=3600 * 24,
            samesite="lax",
            secure=False
        )
        
        return {"message": "Username updated successfully", "username": new_username}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/me")
async def delete_account(response: Response, current_user: dict = Depends(auth.get_current_user)):
    try:
        storage.delete_user(current_user["username"])
        
        # Clear cookie
        response.delete_cookie("access_token")
        
        return {"message": "Account deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete account")


@router.get("/models")
async def get_models(
    api_key: str = None, 
    current_user: dict = Depends(auth.get_current_user)
):
    """
    Get available models from OpenRouter.
    Uses user's API key if available, otherwise strict public list or system key.
    We prefer the system key for fetching the public list to ensure reliability 
    if the user hasn't set one.
    """
    from .. import openrouter
    
    # Check if user has a custom key
    user_key = current_user.get("openrouter_api_key")
    
    # If passed in query param (for testing/setup before saving), use that
    # Otherwise use user's saved key, or default to system key
    key_to_use = api_key or user_key
    
    models = await openrouter.get_available_models(key_to_use)
    return {"data": models}


@router.get("/user/preferences")
async def get_user_preferences(current_user: dict = Depends(auth.get_current_user)):
    """Get current user preferences (masking critical data)."""
    username = current_user["username"]
    user = storage.get_user(username)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Mask API key
    api_key = user.get("openrouter_api_key")
    masked_key = None
    if api_key and len(api_key) > 8:
        masked_key = f"{api_key[:6]}...{api_key[-4:]}"
    elif api_key:
        masked_key = "********"
        
    return {
        "council_models": user.get("council_models"),
        "chairman_model": user.get("chairman_model"),
        "has_api_key": bool(api_key),
        "masked_api_key": masked_key
    }


@router.put("/user/preferences")
async def update_preferences(
    request: Request, 
    current_user: dict = Depends(auth.get_current_user)
):
    """Update user preferences."""
    data = await request.json()
    username = current_user["username"]
    
    try:
        updated_user = storage.update_user_preferences(username, data)
        return {"message": "Preferences updated successfully", "preferences": {
            "council_models": updated_user.get("council_models"),
            "chairman_model": updated_user.get("chairman_model"),
            "has_api_key": bool(updated_user.get("openrouter_api_key"))
        }}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
