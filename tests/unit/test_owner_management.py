import json
import boto3
from moto import mock_aws
from unittest.mock import patch
import sys
import os

# Add the functions directory to the path
owner_management_dir = os.path.join(
    os.path.dirname(__file__), "../../functions/owner_management"
)
sys.path.insert(0, owner_management_dir)

# Remove any existing app module to avoid conflicts
if "app" in sys.modules:
    del sys.modules["app"]

from app import lambda_handler


@mock_aws
def test_register_owner():
    """Test registering a new owner"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create mock table
    dynamodb.create_table(
        TableName="owners-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "email", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "email-index",
                "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # Test event
    event = {
        "httpMethod": "POST",
        "path": "/owners/register",
        "body": json.dumps(
            {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+1234567890",
                "address": {
                    "street": "123 Main St",
                    "city": "Anytown",
                    "state": "CA",
                    "zip": "12345",
                },
            }
        ),
    }

    with patch.dict(os.environ, {"OWNERS_TABLE": "owners-test"}):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert body["name"] == "John Doe"
    assert body["email"] == "john@example.com"
    assert "id" in body
    assert body["id"].startswith("owner-")


@mock_aws
def test_register_owner_duplicate_email():
    """Test registering owner with duplicate email"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create mock table
    dynamodb.create_table(
        TableName="owners-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "email", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "email-index",
                "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # Create existing owner
    owners_table = dynamodb.Table("owners-test")
    owners_table.put_item(
        Item={
            "id": "owner-existing",
            "name": "Existing Owner",
            "email": "john@example.com",
        }
    )

    # Test event with duplicate email
    event = {
        "httpMethod": "POST",
        "path": "/owners/register",
        "body": json.dumps(
            {"name": "John Doe", "email": "john@example.com", "phone": "+1234567890"}
        ),
    }

    with patch.dict(os.environ, {"OWNERS_TABLE": "owners-test"}):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Email already registered" in body["error"]


@mock_aws
def test_get_owner_profile():
    """Test getting owner profile"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create mock table
    dynamodb.create_table(
        TableName="owners-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    # Create test owner
    test_owner = {
        "id": "owner-123",
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1234567890",
    }
    owners_table = dynamodb.Table("owners-test")
    owners_table.put_item(Item=test_owner)

    # Test event
    event = {
        "httpMethod": "GET",
        "path": "/owners/profile",
        "queryStringParameters": {"owner_id": "owner-123"},
    }

    with patch.dict(os.environ, {"OWNERS_TABLE": "owners-test"}):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["name"] == "John Doe"
    assert body["email"] == "john@example.com"


@mock_aws
def test_update_owner_profile():
    """Test updating owner profile"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create mock table
    dynamodb.create_table(
        TableName="owners-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    # Create test owner
    test_owner = {
        "id": "owner-123",
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1234567890",
    }
    owners_table = dynamodb.Table("owners-test")
    owners_table.put_item(Item=test_owner)

    # Test event
    event = {
        "httpMethod": "PUT",
        "path": "/owners/profile",
        "queryStringParameters": {"owner_id": "owner-123"},
        "body": json.dumps({"name": "John Smith", "phone": "+0987654321"}),
    }

    with patch.dict(os.environ, {"OWNERS_TABLE": "owners-test"}):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["name"] == "John Smith"
    assert body["phone"] == "+0987654321"


@mock_aws
def test_invalid_email():
    """Test registration with invalid email"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create mock table
    dynamodb.create_table(
        TableName="owners-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    event = {
        "httpMethod": "POST",
        "path": "/owners/register",
        "body": json.dumps(
            {"name": "John Doe", "email": "invalid-email", "phone": "+1234567890"}
        ),
    }

    with patch.dict(os.environ, {"OWNERS_TABLE": "owners-test"}):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid email format" in body["error"]


@mock_aws
def test_missing_required_field():
    """Test registration with missing required field"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create mock table
    dynamodb.create_table(
        TableName="owners-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    event = {
        "httpMethod": "POST",
        "path": "/owners/register",
        "body": json.dumps(
            {
                "name": "John Doe",
                # Missing email and phone
            }
        ),
    }

    with patch.dict(os.environ, {"OWNERS_TABLE": "owners-test"}):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Missing required field" in body["error"]


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
