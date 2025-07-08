import json
import boto3
from moto import mock_aws
from unittest.mock import patch
import sys
import os
from datetime import datetime, timezone
import pytest
from decimal import Decimal

# Add the functions directory to the path
booking_management_dir = os.path.join(
    os.path.dirname(__file__), "../../functions/booking_management"
)
sys.path.insert(0, booking_management_dir)

# Remove any existing app module to avoid conflicts
if "app" in sys.modules:
    del sys.modules["app"]

from app import lambda_handler, calculate_price


def test_create_booking(mock_env, dynamodb_setup):
    """Test creating a new booking"""
    # Create test data
    dogs_table = dynamodb_setup.Table("dogs-test")
    dogs_table.put_item(
        Item={"id": "dog-123", "name": "Buddy", "owner_id": "owner-123"}
    )

    owners_table = dynamodb_setup.Table("owners-test")
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

    response = lambda_handler(event, None)

    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert body["dog_id"] == "dog-123"
    assert body["service_type"] == "daycare"
    assert body["status"] == "pending"
    assert float(body["price"]) == 120.0  # 8 hours * $15/hour
    assert "id" in body


def test_create_booking_invalid_dog_owner(mock_env, dynamodb_setup):
    """Test creating booking with dog that doesn't belong to owner"""
    # Create test data
    dogs_table = dynamodb_setup.Table("dogs-test")
    dogs_table.put_item(
        Item={"id": "dog-123", "name": "Buddy", "owner_id": "owner-123"}
    )

    owners_table = dynamodb_setup.Table("owners-test")
    owners_table.put_item(Item={"id": "owner-123", "name": "John Doe"})
    owners_table.put_item(Item={"id": "owner-456", "name": "Jane Doe"})

    # Test event with different owner
    event = {
        "httpMethod": "POST",
        "path": "/bookings",
        "body": json.dumps(
            {
                "dog_id": "dog-123",
                "owner_id": "owner-456",  # Different owner
                "service_type": "daycare",
                "start_time": "2024-01-01T09:00:00Z",
                "end_time": "2024-01-01T17:00:00Z",
            }
        ),
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 403
    body = json.loads(response["body"])
    assert "Dog does not belong to this owner" in body["error"]


def test_get_booking(mock_env, dynamodb_setup):
    """Test getting a specific booking"""
    # Create test booking
    bookings_table = dynamodb_setup.Table("bookings-test")
    bookings_table.put_item(
        Item={
            "id": "booking-123",
            "dog_id": "dog-123",
            "owner_id": "owner-123",
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

    response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["id"] == "booking-123"
    assert body["service_type"] == "daycare"


def test_list_bookings(mock_env, dynamodb_setup):
    """Test listing bookings for an owner"""
    # Create test bookings
    bookings_table = dynamodb_setup.Table("bookings-test")
    bookings_table.put_item(
        Item={
            "id": "booking-123",
            "dog_id": "dog-123",
            "owner_id": "owner-123",
            "service_type": "daycare",
            "status": "pending",
            "price": Decimal("120.0"),
            "start_time": "2024-01-01T09:00:00Z",
        }
    )

    # Test event
    event = {
        "httpMethod": "GET",
        "path": "/bookings",
        "queryStringParameters": {"owner_id": "owner-123"},
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "bookings" in body
    assert "count" in body
    assert body["count"] == 1
    assert body["bookings"][0]["id"] == "booking-123"


def test_update_booking(mock_env, dynamodb_setup):
    """Test updating a booking"""
    # Create test booking
    bookings_table = dynamodb_setup.Table("bookings-test")
    bookings_table.put_item(
        Item={
            "id": "booking-123",
            "dog_id": "dog-123",
            "owner_id": "owner-123",
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

    response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["status"] == "confirmed"


def test_cancel_booking(mock_env, dynamodb_setup):
    """Test cancelling a booking"""
    # Create test booking
    bookings_table = dynamodb_setup.Table("bookings-test")
    bookings_table.put_item(
        Item={
            "id": "booking-123",
            "dog_id": "dog-123",
            "owner_id": "owner-123",
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

    response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["status"] == "cancelled"


def test_missing_required_fields(mock_env, dynamodb_setup):
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

    response = lambda_handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Missing required field" in body["error"]


def test_invalid_service_type(mock_env, dynamodb_setup):
    """Test booking creation with invalid service type"""
    # Create test data
    dogs_table = dynamodb_setup.Table("dogs-test")
    dogs_table.put_item(
        Item={"id": "dog-123", "name": "Buddy", "owner_id": "owner-123"}
    )

    owners_table = dynamodb_setup.Table("owners-test")
    owners_table.put_item(Item={"id": "owner-123", "name": "John Doe"})

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

    response = lambda_handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid service type" in body["error"]


def test_invalid_datetime(mock_env, dynamodb_setup):
    """Test booking creation with invalid datetime"""
    # Create test data
    dogs_table = dynamodb_setup.Table("dogs-test")
    dogs_table.put_item(
        Item={"id": "dog-123", "name": "Buddy", "owner_id": "owner-123"}
    )

    owners_table = dynamodb_setup.Table("owners-test")
    owners_table.put_item(Item={"id": "owner-123", "name": "John Doe"})

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

    response = lambda_handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid datetime format" in body["error"]


def test_end_time_before_start_time(mock_env, dynamodb_setup):
    """Test booking creation with end time before start time"""
    # Create test data
    dogs_table = dynamodb_setup.Table("dogs-test")
    dogs_table.put_item(
        Item={"id": "dog-123", "name": "Buddy", "owner_id": "owner-123"}
    )

    owners_table = dynamodb_setup.Table("owners-test")
    owners_table.put_item(Item={"id": "owner-123", "name": "John Doe"})

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
