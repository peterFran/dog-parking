import json
import boto3
from moto import mock_aws
from unittest.mock import patch
import sys
import os

# Add the test directory to the path
test_dir = os.path.dirname(__file__)
sys.path.insert(0, test_dir)

# Set up auth mocks BEFORE importing anything else
from auth_mock import setup_auth_mocks
setup_auth_mocks()

# Add the functions directory to the path
owner_management_dir = os.path.join(
    os.path.dirname(__file__), "../../functions/owner_management"
)
sys.path.insert(0, owner_management_dir)

# Remove any existing app module to avoid conflicts
if "app" in sys.modules:
    del sys.modules["app"]

# Now import the app module
from app import lambda_handler


@mock_aws
def test_register_owner():
    """Test registering a new owner profile (claims-based)"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create mock table with new schema
    dynamodb.create_table(
        TableName="owners-test",
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # Test event with preferences (no PII)
    event = {
        "httpMethod": "POST",
        "path": "/owners/register",
        "body": json.dumps(
            {
                "preferences": {
                    "notifications": True,
                    "marketing_emails": False,
                    "preferred_communication": "email"
                }
            }
        ),
    }

    with patch.dict(os.environ, {"OWNERS_TABLE": "owners-test"}):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert body["message"] == "Profile created successfully"
    assert body["user_id"] == "test-user-123"
    assert "preferences" in body


@mock_aws
def test_register_owner_duplicate_profile():
    """Test registering owner profile when one already exists"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create mock table
    dynamodb.create_table(
        TableName="owners-test",
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # Create existing owner profile
    owners_table = dynamodb.Table("owners-test")
    owners_table.put_item(
        Item={
            "user_id": "test-user-123",
            "preferences": {"notifications": True},
        }
    )

    # Test event with duplicate user
    event = {
        "httpMethod": "POST",
        "path": "/owners/register",
        "body": json.dumps(
            {"preferences": {"notifications": False}}
        ),
    }

    with patch.dict(os.environ, {"OWNERS_TABLE": "owners-test"}):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Profile already exists" in body["error"]


@mock_aws
def test_get_owner_profile():
    """Test getting owner profile"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create mock table
    dynamodb.create_table(
        TableName="owners-test",
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    # Create test owner profile
    test_owner = {
        "user_id": "test-user-123",
        "preferences": {
            "notifications": True,
            "marketing_emails": False
        },
    }
    owners_table = dynamodb.Table("owners-test")
    owners_table.put_item(Item=test_owner)

    # Test event (no query params needed with auth)
    event = {
        "httpMethod": "GET",
        "path": "/owners/profile",
    }

    with patch.dict(os.environ, {"OWNERS_TABLE": "owners-test"}):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["user_id"] == "test-user-123"
    assert "preferences" in body


@mock_aws
def test_update_owner_profile():
    """Test updating owner profile"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create mock table
    dynamodb.create_table(
        TableName="owners-test",
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    # Create test owner profile
    test_owner = {
        "user_id": "test-user-123",
        "preferences": {
            "notifications": True,
            "marketing_emails": False
        },
    }
    owners_table = dynamodb.Table("owners-test")
    owners_table.put_item(Item=test_owner)

    # Test event
    event = {
        "httpMethod": "PUT",
        "path": "/owners/profile",
        "body": json.dumps({
            "preferences": {
                "notifications": False,
                "marketing_emails": True
            }
        }),
    }

    with patch.dict(os.environ, {"OWNERS_TABLE": "owners-test"}):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["user_id"] == "test-user-123"
    assert body["preferences"]["notifications"] == False
    assert body["preferences"]["marketing_emails"] == True


@mock_aws
def test_get_profile_creates_if_not_exists():
    """Test getting profile creates one if it doesn't exist"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create mock table (empty)
    dynamodb.create_table(
        TableName="owners-test",
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    event = {
        "httpMethod": "GET",
        "path": "/owners/profile",
    }

    with patch.dict(os.environ, {"OWNERS_TABLE": "owners-test"}):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["user_id"] == "test-user-123"
    assert "preferences" in body


def test_invalid_json():
    """Test with invalid JSON in request body"""
    event = {"httpMethod": "POST", "path": "/owners/register", "body": "invalid json"}

    with patch.dict(os.environ, {"OWNERS_TABLE": "owners-test"}):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid JSON" in body["error"]


def test_unsupported_endpoint():
    """Test unsupported endpoint"""
    event = {
        "httpMethod": "GET",
        "path": "/owners/unsupported",
        "queryStringParameters": {},
    }

    with patch.dict(os.environ, {"OWNERS_TABLE": "owners-test"}):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "Endpoint not found" in body["error"]



def test_exception_handling():
    """Test exception handling"""
    event = {
        "httpMethod": "GET",
        "path": "/owners/profile",
    }

    # Don't set up environment variables to trigger exception
    response = lambda_handler(event, None)

    assert response["statusCode"] == 500
    body = json.loads(response["body"])
    assert "Internal server error" in body["error"]


@mock_aws  
def test_unverified_email():
    """Test registration with unverified email"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    dynamodb.create_table(
        TableName="owners-test",
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    event = {
        "httpMethod": "POST",
        "path": "/owners/register",
        "body": json.dumps({"preferences": {"notifications": True}}),
        "auth_claims": {
            "user_id": "test-user-123",
            "email_verified": False,  # Unverified
            "provider": "google.com"
        }
    }

    # Mock is_user_verified to return False (handled by auth_claims)
    with patch.dict(os.environ, {"OWNERS_TABLE": "owners-test"}):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Email verification required" in body["error"]