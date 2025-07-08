import pytest
import os


@pytest.fixture
def mock_env():
    """Mock environment variables for testing"""
    env_vars = {
        "DOGS_TABLE": "dogs-test",
        "OWNERS_TABLE": "owners-test",
        "BOOKINGS_TABLE": "bookings-test",
        "PAYMENTS_TABLE": "payments-test",
        "ENVIRONMENT": "test",
    }

    for key, value in env_vars.items():
        os.environ[key] = value

    yield env_vars

    # Cleanup
    for key in env_vars.keys():
        if key in os.environ:
            del os.environ[key]
