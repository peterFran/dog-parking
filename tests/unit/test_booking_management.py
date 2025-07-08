import json
import boto3
from moto import mock_aws
from unittest.mock import patch
import sys
import os
from datetime import datetime, timezone

# Add the functions directory to the path
booking_management_dir = os.path.join(os.path.dirname(__file__), "../../functions/booking_management")
sys.path.insert(0, booking_management_dir)

# Remove any existing app module to avoid conflicts
if 'app' in sys.modules:
    del sys.modules['app']

from app import lambda_handler, calculate_price


@mock_aws
def test_create_booking():
    """Test creating a new booking"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create mock tables
    dynamodb.create_table(
        TableName="bookings-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "owner_id", "AttributeType": "S"},
            {"AttributeName": "start_time", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "owner-time-index",
                "KeySchema": [
                    {"AttributeName": "owner_id", "KeyType": "HASH"},
                    {"AttributeName": "start_time", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )

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

    # Create test data
    dogs_table = dynamodb.Table("dogs-test")
    dogs_table.put_item(
        Item={"id": "dog-123", "name": "Buddy", "owner_id": "owner-123"}
    )

    owners_table = dynamodb.Table("owners-test")
    owners_table.put_item(Item={"id": "owner-123", "name": "John Doe"})

    # Test event
    event = {
        "httpMethod": "POST",
        "path": "/bookings",
        "body": json.dumps(
            {
                "dog_id": "dog-123",
                "owner_id": "owner-123",
                "service_type": "daycare",
                "start_time": "2024-01-01T09:00:00Z",
                "end_time": "2024-01-01T17:00:00Z",
                "special_instructions": "Feed at 12pm",
            }
        ),
    }

    with patch.dict(
        os.environ,
        {
            "BOOKINGS_TABLE": "bookings-test",
            "DOGS_TABLE": "dogs-test",
            "OWNERS_TABLE": "owners-test",
        },
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert body["dog_id"] == "dog-123"
    assert body["service_type"] == "daycare"
    assert body["status"] == "pending"
    assert float(body["price"]) == 120.0  # 8 hours * $15/hour
    assert "id" in body


@mock_aws
def test_create_booking_invalid_dog_owner():
    """Test creating booking with dog that doesn't belong to owner"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    dynamodb.create_table(
        TableName="bookings-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

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

    # Create test data - dog belongs to different owner
    dogs_table = dynamodb.Table("dogs-test")
    dogs_table.put_item(
        Item={
            "id": "dog-123",
            "name": "Buddy",
            "owner_id": "owner-456",  # Different owner
        }
    )

    owners_table = dynamodb.Table("owners-test")
    owners_table.put_item(Item={"id": "owner-123", "name": "John Doe"})

    # Test event
    event = {
        "httpMethod": "POST",
        "path": "/bookings",
        "body": json.dumps(
            {
                "dog_id": "dog-123",
                "owner_id": "owner-123",
                "service_type": "daycare",
                "start_time": "2024-01-01T09:00:00Z",
                "end_time": "2024-01-01T17:00:00Z",
            }
        ),
    }

    with patch.dict(
        os.environ,
        {
            "BOOKINGS_TABLE": "bookings-test",
            "DOGS_TABLE": "dogs-test",
            "OWNERS_TABLE": "owners-test",
        },
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 403
    body = json.loads(response["body"])
    assert "does not belong to this owner" in body["error"]


@mock_aws
def test_list_bookings():
    """Test listing bookings for an owner"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    dynamodb.create_table(
        TableName="bookings-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "owner_id", "AttributeType": "S"},
            {"AttributeName": "start_time", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "owner-time-index",
                "KeySchema": [
                    {"AttributeName": "owner_id", "KeyType": "HASH"},
                    {"AttributeName": "start_time", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # Create test bookings
    bookings_table = dynamodb.Table("bookings-test")
    bookings_table.put_item(
        Item={
            "id": "booking-1",
            "owner_id": "owner-123",
            "service_type": "daycare",
            "start_time": "2024-01-01T09:00:00Z",
        }
    )

    bookings_table.put_item(
        Item={
            "id": "booking-2",
            "owner_id": "owner-123",
            "service_type": "boarding",
            "start_time": "2024-01-02T09:00:00Z",
        }
    )

    # Test event
    event = {
        "httpMethod": "GET",
        "path": "/bookings",
        "queryStringParameters": {"owner_id": "owner-123"},
    }

    with patch.dict(os.environ, {"BOOKINGS_TABLE": "bookings-test"}):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["count"] == 2
    assert len(body["bookings"]) == 2


@mock_aws
def test_update_booking():
    """Test updating a booking"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    dynamodb.create_table(
        TableName="bookings-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    # Create test booking
    bookings_table = dynamodb.Table("bookings-test")
    bookings_table.put_item(
        Item={"id": "booking-123", "dog_id": "dog-123", "status": "pending"}
    )

    # Test event
    event = {
        "httpMethod": "PUT",
        "path": "/bookings/booking-123",
        "pathParameters": {"id": "booking-123"},
        "body": json.dumps(
            {"status": "confirmed", "special_instructions": "Updated instructions"}
        ),
    }

    with patch.dict(os.environ, {"BOOKINGS_TABLE": "bookings-test"}):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["status"] == "confirmed"
    assert body["special_instructions"] == "Updated instructions"


@mock_aws
def test_cancel_booking():
    """Test cancelling a booking"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    dynamodb.create_table(
        TableName="bookings-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    # Create test booking
    bookings_table = dynamodb.Table("bookings-test")
    bookings_table.put_item(
        Item={"id": "booking-123", "dog_id": "dog-123", "status": "pending"}
    )

    # Test event
    event = {
        "httpMethod": "DELETE",
        "path": "/bookings/booking-123",
        "pathParameters": {"id": "booking-123"},
    }

    with patch.dict(os.environ, {"BOOKINGS_TABLE": "bookings-test"}):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["status"] == "cancelled"


def test_calculate_price():
    """Test price calculation logic"""
    from datetime import datetime, timezone

    start_time = datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
    end_time = datetime(2024, 1, 1, 17, 0, 0, tzinfo=timezone.utc)

    # Test daycare pricing
    price = calculate_price("daycare", start_time, end_time)
    assert price == 120.0  # 8 hours * $15/hour

    # Test boarding pricing
    price = calculate_price("boarding", start_time, end_time)
    assert price == 360.0  # 8 hours * $45/hour

    # Test minimum 1 hour charge
    end_time_short = datetime(2024, 1, 1, 9, 30, 0, tzinfo=timezone.utc)
    price = calculate_price("daycare", start_time, end_time_short)
    assert price == 15.0  # Minimum 1 hour


def test_invalid_service_type():
    """Test booking with invalid service type"""
    event = {
        "httpMethod": "POST",
        "path": "/bookings",
        "body": json.dumps(
            {
                "dog_id": "dog-123",
                "owner_id": "owner-123",
                "service_type": "invalid_service",
                "start_time": "2024-01-01T09:00:00Z",
                "end_time": "2024-01-01T17:00:00Z",
            }
        ),
    }

    with patch.dict(
        os.environ,
        {
            "BOOKINGS_TABLE": "bookings-test",
            "DOGS_TABLE": "dogs-test",
            "OWNERS_TABLE": "owners-test",
        },
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid service type" in body["error"]


def test_invalid_datetime():
    """Test booking with invalid datetime format"""
    event = {
        "httpMethod": "POST",
        "path": "/bookings",
        "body": json.dumps(
            {
                "dog_id": "dog-123",
                "owner_id": "owner-123",
                "service_type": "daycare",
                "start_time": "invalid-datetime",
                "end_time": "2024-01-01T17:00:00Z",
            }
        ),
    }

    with patch.dict(
        os.environ,
        {
            "BOOKINGS_TABLE": "bookings-test",
            "DOGS_TABLE": "dogs-test",
            "OWNERS_TABLE": "owners-test",
        },
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid datetime format" in body["error"]


def test_end_time_before_start_time():
    """Test booking with end time before start time"""
    event = {
        "httpMethod": "POST",
        "path": "/bookings",
        "body": json.dumps(
            {
                "dog_id": "dog-123",
                "owner_id": "owner-123",
                "service_type": "daycare",
                "start_time": "2024-01-01T17:00:00Z",
                "end_time": "2024-01-01T09:00:00Z",
            }
        ),
    }

    with patch.dict(
        os.environ,
        {
            "BOOKINGS_TABLE": "bookings-test",
            "DOGS_TABLE": "dogs-test",
            "OWNERS_TABLE": "owners-test",
        },
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Start time must be before end time" in body["error"]