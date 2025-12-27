
import sys
import os

# Add project root to path
sys.path.insert(0, os.getcwd())

try:
    from backend import storage
    print("Storage imported successfully")
    print(f"Has update_user_preferences: {hasattr(storage, 'update_user_preferences')}")
except Exception as e:
    print(f"Error importing storage: {e}")
    import traceback
    traceback.print_exc()
