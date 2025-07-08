import json
import boto3
from moto import mock_aws
from unittest.mock import patch
import sys
import os

# Add the functions directory to the path
dog_management_dir = os.path.join(
    os.path.dirname(__file__), "../../functions/dog_management"
)
sys.path.insert(0, dog_management_dir)

# Remove any existing app module to avoid conflicts
if "app" in sys.modules:
    del sys.modules["app"]

from app import lambda_handler


@mock_aws
def test_create_dog_simple():
    """Test creating a new dog - simplified version"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create simple mock tables
    dynamodb.create_table(
        TableName="dogs-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    dynamodb.create_table(
        TableName="owners-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    # Create a test owner
    owners_table = dynamodb.Table("owners-test")
    owners_table.put_item(Item={"id": "owner-123", "name": "Test Owner"})

    # Test event
    event = {
        "httpMethod": "POST",
        "path": "/dogs",
        "body": json.dumps(
            {
                "name": "Buddy",
                "breed": "Golden Retriever",
                "age": 3,
                "size": "large",
                "owner_id": "owner-123",
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
    assert "id" in body


def test_calculate_simple():
    """Simple test that doesn't require AWS"""
    assert 2 + 2 == 4
