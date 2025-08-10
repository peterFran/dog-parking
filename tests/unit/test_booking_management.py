import json
import boto3
from moto import mock_aws
from unittest.mock import patch
import sys
import os
from datetime import datetime, timezone
import pytest
from decimal import Decimal

# Add the test directory to the path
test_dir = os.path.dirname(__file__)
sys.path.insert(0, test_dir)

# Set up auth mocks BEFORE importing anything else
from auth_mock import setup_auth_mocks

setup_auth_mocks()

# Add the functions directory to the path
booking_management_dir = os.path.join(
    os.path.dirname(__file__), "../../functions/booking_management"
)
sys.path.insert(0, booking_management_dir)

# Remove any existing app module to avoid conflicts
if "app" in sys.modules:
    del sys.modules["app"]

from app import lambda_handler, calculate_price


@mock_aws
def test_create_booking():
    """Test creating a new booking"""
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

    # Create venues table
    dynamodb.create_table(
        TableName="venues-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    # Create bookings table
    dynamodb.create_table(
        TableName="bookings-test",
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

    # Create test data
    dogs_table = dynamodb.Table("dogs-test")
    dogs_table.put_item(
        Item={"id": "dog-123", "name": "Buddy", "owner_id": "test-user-123"}
    )

    owners_table = dynamodb.Table("owners-test")
    owners_table.put_item(
        Item={"user_id": "test-user-123", "preferences": {"notifications": True}}
    )

    venues_table = dynamodb.Table("venues-test")
    venues_table.put_item(
        Item={
            "id": "venue-123",
            "name": "Test Venue",
            "capacity": 20,
            "operating_hours": {
                "monday": {"open": True, "start": "08:00", "end": "18:00"}
            },
        }
    )

    # Test event (no owner_id needed - comes from auth)
    event = {
        "httpMethod": "POST",
        "path": "/bookings",
        "body": json.dumps(
            {
                "dog_id": "dog-123",
                "venue_id": "venue-123",
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
            "DOGS_TABLE": "dogs-test",
            "OWNERS_TABLE": "owners-test",
            "VENUES_TABLE": "venues-test",
            "BOOKINGS_TABLE": "bookings-test",
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

    # Create all tables
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

    dynamodb.create_table(
        TableName="venues-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    dynamodb.create_table(
        TableName="bookings-test",
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

    # Create test data - dog belongs to different owner
    dogs_table = dynamodb.Table("dogs-test")
    dogs_table.put_item(
        Item={"id": "dog-123", "name": "Buddy", "owner_id": "different-user"}
    )

    owners_table = dynamodb.Table("owners-test")
    owners_table.put_item(
        Item={"user_id": "test-user-123", "preferences": {"notifications": True}}
    )

    venues_table = dynamodb.Table("venues-test")
    venues_table.put_item(
        Item={
            "id": "venue-123",
            "name": "Test Venue",
            "capacity": 20,
            "operating_hours": {
                "monday": {"open": True, "start": "08:00", "end": "18:00"}
            },
        }
    )

    # Test event
    event = {
        "httpMethod": "POST",
        "path": "/bookings",
        "body": json.dumps(
            {
                "dog_id": "dog-123",
                "venue_id": "venue-123",
                "service_type": "daycare",
                "start_time": "2024-01-01T09:00:00Z",
                "end_time": "2024-01-01T17:00:00Z",
            }
        ),
    }

    with patch.dict(
        os.environ,
        {
            "DOGS_TABLE": "dogs-test",
            "OWNERS_TABLE": "owners-test",
            "VENUES_TABLE": "venues-test",
            "BOOKINGS_TABLE": "bookings-test",
        },
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 403
    body = json.loads(response["body"])
    assert "Dog does not belong to this owner" in body["error"]


@mock_aws
def test_get_booking():
    """Test getting a specific booking"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create bookings table
    dynamodb.create_table(
        TableName="bookings-test",
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

    # Create test booking
    bookings_table = dynamodb.Table("bookings-test")
    bookings_table.put_item(
        Item={
            "id": "booking-123",
            "dog_id": "dog-123",
            "owner_id": "test-user-123",
            "service_type": "daycare",
            "status": "pending",
            "price": Decimal("120.0"),
        }
    )

    # Test event
    event = {
        "httpMethod": "GET",
        "path": "/bookings/booking-123",
        "pathParameters": {"id": "booking-123"},
    }

    with patch.dict(
        os.environ,
        {
            "BOOKINGS_TABLE": "bookings-test",
            "DOGS_TABLE": "dogs-test",
            "OWNERS_TABLE": "owners-test",
            "VENUES_TABLE": "venues-test",
        },
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["id"] == "booking-123"
    assert body["service_type"] == "daycare"


@mock_aws
def test_list_bookings():
    """Test listing bookings for authenticated user"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create bookings table
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
            "id": "booking-123",
            "dog_id": "dog-123",
            "owner_id": "test-user-123",
            "service_type": "daycare",
            "status": "pending",
            "price": Decimal("120.0"),
            "start_time": "2024-01-01T09:00:00Z",
        }
    )

    # Test event (no query params needed with auth)
    event = {
        "httpMethod": "GET",
        "path": "/bookings",
    }

    with patch.dict(
        os.environ,
        {
            "BOOKINGS_TABLE": "bookings-test",
            "DOGS_TABLE": "dogs-test",
            "OWNERS_TABLE": "owners-test",
            "VENUES_TABLE": "venues-test",
        },
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "bookings" in body
    assert "count" in body
    assert body["count"] == 1
    assert body["bookings"][0]["id"] == "booking-123"


@mock_aws
def test_update_booking():
    """Test updating a booking"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create bookings table
    dynamodb.create_table(
        TableName="bookings-test",
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

    # Create test booking
    bookings_table = dynamodb.Table("bookings-test")
    bookings_table.put_item(
        Item={
            "id": "booking-123",
            "dog_id": "dog-123",
            "owner_id": "test-user-123",
            "service_type": "daycare",
            "status": "pending",
            "price": Decimal("120.0"),
        }
    )

    # Test event
    event = {
        "httpMethod": "PUT",
        "path": "/bookings/booking-123",
        "pathParameters": {"id": "booking-123"},
        "body": json.dumps({"status": "confirmed"}),
    }

    with patch.dict(
        os.environ,
        {
            "BOOKINGS_TABLE": "bookings-test",
            "DOGS_TABLE": "dogs-test",
            "OWNERS_TABLE": "owners-test",
            "VENUES_TABLE": "venues-test",
        },
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["status"] == "confirmed"


@mock_aws
def test_cancel_booking():
    """Test cancelling a booking"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create bookings table
    dynamodb.create_table(
        TableName="bookings-test",
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

    # Create test booking
    bookings_table = dynamodb.Table("bookings-test")
    bookings_table.put_item(
        Item={
            "id": "booking-123",
            "dog_id": "dog-123",
            "owner_id": "test-user-123",
            "service_type": "daycare",
            "status": "pending",
            "price": Decimal("120.0"),
        }
    )

    # Test event
    event = {
        "httpMethod": "DELETE",
        "path": "/bookings/booking-123",
        "pathParameters": {"id": "booking-123"},
    }

    with patch.dict(
        os.environ,
        {
            "BOOKINGS_TABLE": "bookings-test",
            "DOGS_TABLE": "dogs-test",
            "OWNERS_TABLE": "owners-test",
            "VENUES_TABLE": "venues-test",
        },
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["status"] == "cancelled"


def test_missing_required_fields():
    """Test booking creation with missing required fields"""
    event = {
        "httpMethod": "POST",
        "path": "/bookings",
        "body": json.dumps(
            {
                "dog_id": "dog-123",
                # Missing required fields
            }
        ),
    }

    with patch.dict(
        os.environ,
        {
            "BOOKINGS_TABLE": "bookings-test",
            "DOGS_TABLE": "dogs-test",
            "OWNERS_TABLE": "owners-test",
            "VENUES_TABLE": "venues-test",
        },
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Missing required field" in body["error"]


@mock_aws
def test_invalid_service_type():
    """Test booking creation with invalid service type"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create all tables
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

    dynamodb.create_table(
        TableName="venues-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    dynamodb.create_table(
        TableName="bookings-test",
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

    # Create test data
    dogs_table = dynamodb.Table("dogs-test")
    dogs_table.put_item(
        Item={"id": "dog-123", "name": "Buddy", "owner_id": "test-user-123"}
    )

    owners_table = dynamodb.Table("owners-test")
    owners_table.put_item(
        Item={"user_id": "test-user-123", "preferences": {"notifications": True}}
    )

    venues_table = dynamodb.Table("venues-test")
    venues_table.put_item(
        Item={
            "id": "venue-123",
            "name": "Test Venue",
            "capacity": 20,
            "operating_hours": {
                "monday": {"open": True, "start": "08:00", "end": "18:00"}
            },
        }
    )

    event = {
        "httpMethod": "POST",
        "path": "/bookings",
        "body": json.dumps(
            {
                "dog_id": "dog-123",
                "venue_id": "venue-123",
                "service_type": "invalid_service",
                "start_time": "2024-01-01T09:00:00Z",
                "end_time": "2024-01-01T17:00:00Z",
            }
        ),
    }

    with patch.dict(
        os.environ,
        {
            "DOGS_TABLE": "dogs-test",
            "OWNERS_TABLE": "owners-test",
            "VENUES_TABLE": "venues-test",
            "BOOKINGS_TABLE": "bookings-test",
        },
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid service type" in body["error"]


@mock_aws
def test_invalid_datetime():
    """Test booking creation with invalid datetime"""
    # Setup mock DynamoDB (minimal setup for validation test)
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create minimal tables
    dynamodb.create_table(
        TableName="dogs-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    dynamodb.create_table(
        TableName="owners-test",
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    dynamodb.create_table(
        TableName="venues-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    dynamodb.create_table(
        TableName="bookings-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    # Add test data so we can reach datetime validation
    dogs_table = dynamodb.Table("dogs-test")
    dogs_table.put_item(
        Item={"id": "dog-123", "name": "Buddy", "owner_id": "test-user-123"}
    )

    owners_table = dynamodb.Table("owners-test")
    owners_table.put_item(
        Item={"user_id": "test-user-123", "preferences": {"notifications": True}}
    )

    venues_table = dynamodb.Table("venues-test")
    venues_table.put_item(
        Item={
            "id": "venue-123",
            "name": "Test Venue",
            "capacity": 20,
            "operating_hours": {
                "monday": {"open": True, "start": "08:00", "end": "18:00"}
            },
        }
    )

    event = {
        "httpMethod": "POST",
        "path": "/bookings",
        "body": json.dumps(
            {
                "dog_id": "dog-123",
                "venue_id": "venue-123",
                "service_type": "daycare",
                "start_time": "invalid-datetime",
                "end_time": "2024-01-01T17:00:00Z",
            }
        ),
    }

    with patch.dict(
        os.environ,
        {
            "DOGS_TABLE": "dogs-test",
            "OWNERS_TABLE": "owners-test",
            "VENUES_TABLE": "venues-test",
            "BOOKINGS_TABLE": "bookings-test",
        },
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid datetime format" in body["error"]


@mock_aws
def test_end_time_before_start_time():
    """Test booking creation with end time before start time"""
    # Setup mock DynamoDB (minimal setup for validation test)
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create minimal tables
    dynamodb.create_table(
        TableName="dogs-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    dynamodb.create_table(
        TableName="owners-test",
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    dynamodb.create_table(
        TableName="venues-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    dynamodb.create_table(
        TableName="bookings-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    # Add test data so we can reach datetime validation
    dogs_table = dynamodb.Table("dogs-test")
    dogs_table.put_item(
        Item={"id": "dog-123", "name": "Buddy", "owner_id": "test-user-123"}
    )

    owners_table = dynamodb.Table("owners-test")
    owners_table.put_item(
        Item={"user_id": "test-user-123", "preferences": {"notifications": True}}
    )

    venues_table = dynamodb.Table("venues-test")
    venues_table.put_item(
        Item={
            "id": "venue-123",
            "name": "Test Venue",
            "capacity": 20,
            "operating_hours": {
                "monday": {"open": True, "start": "08:00", "end": "18:00"}
            },
        }
    )

    event = {
        "httpMethod": "POST",
        "path": "/bookings",
        "body": json.dumps(
            {
                "dog_id": "dog-123",
                "venue_id": "venue-123",
                "service_type": "daycare",
                "start_time": "2024-01-01T17:00:00Z",
                "end_time": "2024-01-01T09:00:00Z",
            }
        ),
    }

    with patch.dict(
        os.environ,
        {
            "DOGS_TABLE": "dogs-test",
            "OWNERS_TABLE": "owners-test",
            "VENUES_TABLE": "venues-test",
            "BOOKINGS_TABLE": "bookings-test",
        },
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Start time must be before end time" in body["error"]


def test_calculate_price():
    """Test price calculation function"""
    start_time = datetime(2024, 1, 1, 9, 0, 0)
    end_time = datetime(2024, 1, 1, 17, 0, 0)

    # Test daycare (8 hours * $15/hour)
    price = calculate_price("daycare", start_time, end_time)
    assert price == 120.0

    # Test boarding (8 hours * $45/hour)
    price = calculate_price("boarding", start_time, end_time)
    assert price == 360.0

    # Test grooming (8 hours * $60/hour)
    price = calculate_price("grooming", start_time, end_time)
    assert price == 480.0

    # Test minimum 1 hour charge
    end_time_30min = datetime(2024, 1, 1, 9, 30, 0)
    price = calculate_price("daycare", start_time, end_time_30min)
    assert price == 15.0  # 1 hour minimum


def test_method_not_allowed():
    """Test unsupported HTTP method"""
    event = {
        "httpMethod": "PATCH",
        "path": "/bookings",
        "body": json.dumps({"dog_id": "dog-123"}),
    }

    with patch.dict(
        os.environ,
        {
            "DOGS_TABLE": "dogs-test",
            "OWNERS_TABLE": "owners-test",
            "VENUES_TABLE": "venues-test",
            "BOOKINGS_TABLE": "bookings-test",
        },
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 405
    body = json.loads(response["body"])
    assert "Method not allowed" in body["error"]


def test_exception_handling():
    """Test exception handling"""
    event = {
        "httpMethod": "GET",
        "path": "/bookings",
    }

    # Don't set up environment variables to trigger exception
    response = lambda_handler(event, None)

    assert response["statusCode"] == 500
    body = json.loads(response["body"])
    assert "Internal server error" in body["error"]
