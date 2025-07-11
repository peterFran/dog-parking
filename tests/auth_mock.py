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
        # args[1] should be the event
        if len(args) >= 2:
            event = args[1] if isinstance(args[1], dict) else args[0]
            if isinstance(event, dict):
                # Only add auth_claims if they don't already exist
                if 'auth_claims' not in event:
                    event['auth_claims'] = {
                        'user_id': 'test-user-123',
                        'email_verified': True,
                        'provider': 'google.com'
                    }
        return handler_func(*args, **kwargs)
    return wrapper

def mock_optional_auth(handler_func):
    """Mock optional_auth decorator"""
    @wraps(handler_func)
    def wrapper(*args, **kwargs):
        if len(args) >= 2:
            event = args[1] if isinstance(args[1], dict) else args[0]
            if isinstance(event, dict) and 'auth_claims' not in event:
                event['auth_claims'] = {
                    'user_id': 'test-user-123',
                    'email_verified': True,
                    'provider': 'google.com'
                }
        return handler_func(*args, **kwargs)
    return wrapper

def mock_get_user_id_from_event(event):
    """Mock get_user_id_from_event function"""
    claims = event.get('auth_claims', {})
    return claims.get('user_id', 'test-user-123')

def mock_is_user_verified(event):
    """Mock is_user_verified function"""
    claims = event.get('auth_claims', {})
    return claims.get('email_verified', True)

def setup_auth_mocks():
    """Set up all auth mocks before importing app modules"""
    # Create the mock auth module
    mock_auth_module = MagicMock()
    mock_auth_module.require_auth = mock_require_auth
    mock_auth_module.optional_auth = mock_optional_auth
    mock_auth_module.get_user_id_from_event = mock_get_user_id_from_event
    mock_auth_module.is_user_verified = mock_is_user_verified
    
    # Mock the auth module at the top level
    sys.modules['auth'] = mock_auth_module
    sys.modules['auth.app'] = mock_auth_module
    
    return mock_auth_module