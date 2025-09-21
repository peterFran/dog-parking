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

from app import lambda_handler


@mock_aws
def test_create_dog_simple():
    """Test creating a new dog - simplified version with auth"""
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

    # Create owners table with new schema
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
                "date_of_birth": "2021-06-15",
                "size": "LARGE",
                "vaccination_status": "VACCINATED",
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


def test_calculate_simple():
    """Simple test that doesn't require AWS"""
    assert 2 + 2 == 4
