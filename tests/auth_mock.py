"""
Comprehensive mock authentication system for testing
"""

import sys
from unittest.mock import MagicMock, patch
from functools import wraps


# Mock authentication functions
def mock_require_auth(handler_func):
    """Mock require_auth decorator that adds test user claims"""

    @wraps(handler_func)
    def wrapper(*args, **kwargs):
        # Find the event in arguments - look through all arguments to find the Lambda event
        event = None
        for arg in args:
            if isinstance(arg, dict) and ('httpMethod' in arg or 'requestContext' in arg or 'headers' in arg or 'auth_claims' in arg):
                event = arg
                break
        
        if event and isinstance(event, dict):
            # Only add auth_claims if they don't already exist
            if "auth_claims" not in event:
                event["auth_claims"] = {
                    "user_id": "test-user-123",
                    "email_verified": True,
                    "provider": "google.com",
                }
        
        return handler_func(*args, **kwargs)

    return wrapper


def mock_optional_auth(handler_func):
    """Mock optional_auth decorator"""

    @wraps(handler_func)
    def wrapper(*args, **kwargs):
        # Find the event in arguments - look through all arguments to find the Lambda event
        event = None
        for arg in args:
            if isinstance(arg, dict) and ('httpMethod' in arg or 'requestContext' in arg or 'headers' in arg or 'auth_claims' in arg):
                event = arg
                break
        
        if event and isinstance(event, dict) and "auth_claims" not in event:
            event["auth_claims"] = {
                "user_id": "test-user-123",
                "email_verified": True,
                "provider": "google.com",
            }
        
        return handler_func(*args, **kwargs)

    return wrapper


def mock_get_user_id_from_event(event):
    """Mock get_user_id_from_event function"""
    claims = event.get("auth_claims", {})
    return claims.get("user_id", "test-user-123")


def mock_is_user_verified(event):
    """Mock is_user_verified function"""
    claims = event.get("auth_claims", {})
    return claims.get("email_verified", True)


def setup_auth_mocks():
    """Set up all auth mocks before importing app modules"""
    # Create the mock auth module
    mock_auth_module = MagicMock()
    mock_auth_module.require_auth = mock_require_auth
    mock_auth_module.optional_auth = mock_optional_auth
    mock_auth_module.get_user_id_from_event = mock_get_user_id_from_event
    mock_auth_module.is_user_verified = mock_is_user_verified

    # Mock the auth module at the top level
    sys.modules["auth"] = mock_auth_module
    sys.modules["auth.app"] = mock_auth_module

    return mock_auth_module
