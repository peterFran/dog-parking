import pytest
import os
import boto3
from moto import mock_aws


@pytest.fixture
def mock_env():
    """Mock environment variables for testing"""
    env_vars = {
        "DOGS_TABLE": "dogs-test",
        "OWNERS_TABLE": "owners-test",
        "BOOKINGS_TABLE": "bookings-test",
        "ENVIRONMENT": "test",
        "AWS_ACCESS_KEY_ID": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing",
        "AWS_SECURITY_TOKEN": "testing",
        "AWS_SESSION_TOKEN": "testing",
        "AWS_DEFAULT_REGION": "us-east-1",
    }

    for key, value in env_vars.items():
        os.environ[key] = value

    yield env_vars

    # Cleanup
    for key in env_vars.keys():
        if key in os.environ:
            del os.environ[key]


@pytest.fixture
def aws_credentials():
    """Mock AWS credentials for testing"""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture
def dynamodb_setup(aws_credentials):
    """Set up mock DynamoDB for testing"""
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        
        # Create test tables
        tables = {
            "dogs-test": {
                "KeySchema": [{"AttributeName": "id", "KeyType": "HASH"}],
                "AttributeDefinitions": [
                    {"AttributeName": "id", "AttributeType": "S"},
                    {"AttributeName": "owner_id", "AttributeType": "S"},
                ],
                "GlobalSecondaryIndexes": [
                    {
                        "IndexName": "owner-index",
                        "KeySchema": [{"AttributeName": "owner_id", "KeyType": "HASH"}],
                        "Projection": {"ProjectionType": "ALL"},
                    }
                ],
            },
            "owners-test": {
                "KeySchema": [{"AttributeName": "id", "KeyType": "HASH"}],
                "AttributeDefinitions": [
                    {"AttributeName": "id", "AttributeType": "S"},
                    {"AttributeName": "email", "AttributeType": "S"},
                ],
                "GlobalSecondaryIndexes": [
                    {
                        "IndexName": "email-index",
                        "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
                        "Projection": {"ProjectionType": "ALL"},
                    }
                ],
            },
            "bookings-test": {
                "KeySchema": [{"AttributeName": "id", "KeyType": "HASH"}],
                "AttributeDefinitions": [
                    {"AttributeName": "id", "AttributeType": "S"},
                    {"AttributeName": "owner_id", "AttributeType": "S"},
                    {"AttributeName": "start_time", "AttributeType": "S"},
                ],
                "GlobalSecondaryIndexes": [
                    {
                        "IndexName": "owner-time-index",
                        "KeySchema": [
                            {"AttributeName": "owner_id", "KeyType": "HASH"},
                            {"AttributeName": "start_time", "KeyType": "RANGE"},
                        ],
                        "Projection": {"ProjectionType": "ALL"},
                    }
                ],
            },
        }
        
        for table_name, table_config in tables.items():
            dynamodb.create_table(
                TableName=table_name,
                KeySchema=table_config["KeySchema"],
                AttributeDefinitions=table_config["AttributeDefinitions"],
                GlobalSecondaryIndexes=table_config.get("GlobalSecondaryIndexes", []),
                BillingMode="PAY_PER_REQUEST",
            )
        
        yield dynamodb
