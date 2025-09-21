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
dog_management_dir = os.path.join(
    os.path.dirname(__file__), "../../functions/dog_management"
)
sys.path.insert(0, dog_management_dir)

# Remove any existing app module to avoid conflicts
if "app" in sys.modules:
    del sys.modules["app"]

# Now import the app module
from app import lambda_handler


@mock_aws
def test_create_dog():
    """Test creating a new dog with auth"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create dogs table
    dynamodb.create_table(
        TableName="dogs-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "owner_id", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "owner-index",
                "KeySchema": [{"AttributeName": "owner_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # Create owners table
    dynamodb.create_table(
        TableName="owners-test",
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    # Create a test owner profile
    owners_table = dynamodb.Table("owners-test")
    owners_table.put_item(
        Item={"user_id": "test-user-123", "preferences": {"notifications": True}}
    )

    # Test event (no owner_id needed - comes from auth)
    event = {
        "httpMethod": "POST",
        "path": "/dogs",
        "body": json.dumps(
            {
                "name": "Buddy",
                "breed": "Golden Retriever",
                "date_of_birth": "2021-01-15",
                "size": "LARGE",
                "vaccination_status": "VACCINATED",
                "microchipped": True,
                "special_needs": ["medication"],
                "medical_notes": "Takes medication twice daily",
                "behavior_notes": "Friendly with other dogs",
                "favorite_activities": "fetch, swimming",
            }
        ),
    }

    with patch.dict(
        os.environ, {"DOGS_TABLE": "dogs-test", "OWNERS_TABLE": "owners-test"}
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert body["name"] == "Buddy"
    assert body["breed"] == "Golden Retriever"
    assert body["owner_id"] == "test-user-123"  # From auth
    assert "id" in body
    assert body["id"].startswith("dog-")


@mock_aws
def test_create_dog_no_profile():
    """Test creating dog without owner profile"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create dogs table
    dynamodb.create_table(
        TableName="dogs-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "owner_id", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "owner-index",
                "KeySchema": [{"AttributeName": "owner_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # Create owners table (empty)
    dynamodb.create_table(
        TableName="owners-test",
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    event = {
        "httpMethod": "POST",
        "path": "/dogs",
        "body": json.dumps(
            {
                "name": "Buddy",
                "breed": "Labrador",
                "date_of_birth": "2022-06-10",
                "size": "MEDIUM",
                "vaccination_status": "NOT_VACCINATED"
            }
        ),
    }

    with patch.dict(
        os.environ, {"DOGS_TABLE": "dogs-test", "OWNERS_TABLE": "owners-test"}
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Please complete profile registration first" in body["error"]


@mock_aws
def test_list_dogs():
    """Test listing dogs for authenticated user"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create dogs table
    dynamodb.create_table(
        TableName="dogs-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "owner_id", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "owner-index",
                "KeySchema": [{"AttributeName": "owner_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # Create owners table
    dynamodb.create_table(
        TableName="owners-test",
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    # Add test dogs
    dogs_table = dynamodb.Table("dogs-test")
    dogs_table.put_item(
        Item={
            "id": "dog-1",
            "name": "Buddy",
            "owner_id": "test-user-123",
            "breed": "Labrador",
        }
    )
    dogs_table.put_item(
        Item={
            "id": "dog-2",
            "name": "Max",
            "owner_id": "test-user-123",
            "breed": "German Shepherd",
        }
    )

    event = {
        "httpMethod": "GET",
        "path": "/dogs",
    }

    with patch.dict(
        os.environ, {"DOGS_TABLE": "dogs-test", "OWNERS_TABLE": "owners-test"}
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["count"] == 2
    assert len(body["dogs"]) == 2


@mock_aws
def test_get_dog():
    """Test getting specific dog"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create owners table
    dynamodb.create_table(
        TableName="owners-test",
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    # Create dogs table
    dynamodb.create_table(
        TableName="dogs-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "owner_id", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "owner-index",
                "KeySchema": [{"AttributeName": "owner_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # Add test dog
    dogs_table = dynamodb.Table("dogs-test")
    dogs_table.put_item(
        Item={
            "id": "dog-123",
            "name": "Buddy",
            "owner_id": "test-user-123",
            "breed": "Labrador",
        }
    )

    event = {
        "httpMethod": "GET",
        "path": "/dogs/dog-123",
        "pathParameters": {"id": "dog-123"},
    }

    with patch.dict(
        os.environ, {"DOGS_TABLE": "dogs-test", "OWNERS_TABLE": "owners-test"}
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["name"] == "Buddy"
    assert body["owner_id"] == "test-user-123"


@mock_aws
def test_get_dog_access_denied():
    """Test getting dog that doesn't belong to user"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create owners table
    dynamodb.create_table(
        TableName="owners-test",
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    # Create dogs table
    dynamodb.create_table(
        TableName="dogs-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "owner_id", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "owner-index",
                "KeySchema": [{"AttributeName": "owner_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # Add dog belonging to different user
    dogs_table = dynamodb.Table("dogs-test")
    dogs_table.put_item(
        Item={
            "id": "dog-123",
            "name": "Buddy",
            "owner_id": "different-user",
            "breed": "Labrador",
        }
    )

    event = {
        "httpMethod": "GET",
        "path": "/dogs/dog-123",
        "pathParameters": {"id": "dog-123"},
    }

    with patch.dict(
        os.environ, {"DOGS_TABLE": "dogs-test", "OWNERS_TABLE": "owners-test"}
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 403
    body = json.loads(response["body"])
    assert "Access denied" in body["error"]


@mock_aws
def test_update_dog():
    """Test updating dog"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create owners table
    dynamodb.create_table(
        TableName="owners-test",
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    # Create dogs table
    dynamodb.create_table(
        TableName="dogs-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "owner_id", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "owner-index",
                "KeySchema": [{"AttributeName": "owner_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # Add test dog
    dogs_table = dynamodb.Table("dogs-test")
    dogs_table.put_item(
        Item={
            "id": "dog-123",
            "name": "Buddy",
            "owner_id": "test-user-123",
            "breed": "Labrador",
            "age": 2,
        }
    )

    event = {
        "httpMethod": "PUT",
        "path": "/dogs/dog-123",
        "pathParameters": {"id": "dog-123"},
        "body": json.dumps({"vaccination_status": "VACCINATED", "medical_notes": "Updated medical information"}),
    }

    with patch.dict(
        os.environ, {"DOGS_TABLE": "dogs-test", "OWNERS_TABLE": "owners-test"}
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["vaccination_status"] == "VACCINATED"
    assert body["medical_notes"] == "Updated medical information"


@mock_aws
def test_delete_dog():
    """Test deleting dog"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create dogs table
    dynamodb.create_table(
        TableName="dogs-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "owner_id", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "owner-index",
                "KeySchema": [{"AttributeName": "owner_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # Add test dog
    dogs_table = dynamodb.Table("dogs-test")
    dogs_table.put_item(
        Item={
            "id": "dog-123",
            "name": "Buddy",
            "owner_id": "test-user-123",
            "breed": "Labrador",
        }
    )

    event = {
        "httpMethod": "DELETE",
        "path": "/dogs/dog-123",
        "pathParameters": {"id": "dog-123"},
    }

    with patch.dict(
        os.environ, {"DOGS_TABLE": "dogs-test", "OWNERS_TABLE": "owners-test"}
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 204


@mock_aws
def test_invalid_size():
    """Test creating dog with invalid size"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create tables
    dynamodb.create_table(
        TableName="dogs-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "owner_id", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "owner-index",
                "KeySchema": [{"AttributeName": "owner_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    dynamodb.create_table(
        TableName="owners-test",
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    # Create owner profile
    owners_table = dynamodb.Table("owners-test")
    owners_table.put_item(
        Item={"user_id": "test-user-123", "preferences": {"notifications": True}}
    )

    event = {
        "httpMethod": "POST",
        "path": "/dogs",
        "body": json.dumps(
            {
                "name": "Buddy",
                "breed": "Labrador",
                "date_of_birth": "2022-03-15",
                "size": "GIGANTIC",  # Invalid size
                "vaccination_status": "VACCINATED",
            }
        ),
    }

    with patch.dict(
        os.environ, {"DOGS_TABLE": "dogs-test", "OWNERS_TABLE": "owners-test"}
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid size" in body["error"]


def test_invalid_json():
    """Test with invalid JSON"""
    event = {"httpMethod": "POST", "path": "/dogs", "body": "invalid json"}

    with patch.dict(
        os.environ, {"DOGS_TABLE": "dogs-test", "OWNERS_TABLE": "owners-test"}
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid JSON" in body["error"]


def test_method_not_allowed():
    """Test unsupported HTTP method"""
    event = {
        "httpMethod": "PATCH",
        "path": "/dogs",
        "body": json.dumps({"name": "Test"}),
    }

    with patch.dict(
        os.environ, {"DOGS_TABLE": "dogs-test", "OWNERS_TABLE": "owners-test"}
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 405
    body = json.loads(response["body"])
    assert "Method not allowed" in body["error"]


@mock_aws
def test_exception_handling():
    """Test exception handling"""
    event = {
        "httpMethod": "GET",
        "path": "/dogs",
    }

    # Don't set up environment variables to trigger exception
    response = lambda_handler(event, None)

    assert response["statusCode"] == 500
    body = json.loads(response["body"])
    assert "Internal server error" in body["error"]
