"""
Mock authentication module for testing
"""
from functools import wraps


def require_auth(handler_func):
    """Mock require_auth decorator for testing"""
    @wraps(handler_func)
    def wrapper(event, context):
        # Add mock auth claims to event
        event['auth_claims'] = {
            'user_id': 'test-user-123',
            'email_verified': True,
            'provider': 'google.com'
        }
        return handler_func(event, context)
    return wrapper


def optional_auth(handler_func):
    """Mock optional_auth decorator for testing"""
    @wraps(handler_func)
    def wrapper(event, context):
        # Add mock auth claims to event if not present
        if 'auth_claims' not in event:
            event['auth_claims'] = {
                'user_id': 'test-user-123',
                'email_verified': True,
                'provider': 'google.com'
            }
        return handler_func(event, context)
    return wrapper


def get_user_id_from_event(event):
    """Mock get_user_id_from_event for testing"""
    claims = event.get('auth_claims', {})
    return claims.get('user_id', 'test-user-123')


def is_user_verified(event):
    """Mock is_user_verified for testing"""
    claims = event.get('auth_claims', {})
    return claims.get('email_verified', True)