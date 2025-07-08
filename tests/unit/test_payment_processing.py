import json
import boto3
from moto import mock_aws
from unittest.mock import patch
from decimal import Decimal
import sys
import os

# Add the functions directory to the path  
payment_processing_dir = os.path.join(os.path.dirname(__file__), "../../functions/payment_processing")
sys.path.insert(0, payment_processing_dir)

# Remove any existing app module to avoid conflicts
if 'app' in sys.modules:
    del sys.modules['app']

from app import lambda_handler, simulate_payment_processing


@mock_aws
def test_process_payment_success():
    """Test successful payment processing"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create mock tables
    dynamodb.create_table(
        TableName="payments-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "booking_id", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "booking-index",
                "KeySchema": [{"AttributeName": "booking_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    dynamodb.create_table(
        TableName="bookings-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    # Create test booking
    bookings_table = dynamodb.Table("bookings-test")
    bookings_table.put_item(
        Item={"id": "booking-123", "price": Decimal("45.00"), "status": "pending"}
    )

    # Test event
    event = {
        "httpMethod": "POST",
        "path": "/payments",
        "body": json.dumps(
            {
                "booking_id": "booking-123",
                "amount": 45.00,
                "payment_method": "credit_card",
                "payment_token": "test_success",
            }
        ),
    }

    with patch.dict(
        os.environ,
        {"PAYMENTS_TABLE": "payments-test", "BOOKINGS_TABLE": "bookings-test"},
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert body["booking_id"] == "booking-123"
    assert float(body["amount"]) == 45.00
    assert body["status"] == "completed"
    assert "transaction_id" in body
    assert "id" in body


@mock_aws
def test_process_payment_declined():
    """Test declined payment processing"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    dynamodb.create_table(
        TableName="payments-test",
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

    # Create test booking
    bookings_table = dynamodb.Table("bookings-test")
    bookings_table.put_item(
        Item={"id": "booking-123", "price": Decimal("45.00"), "status": "pending"}
    )

    # Test event with decline token
    event = {
        "httpMethod": "POST",
        "path": "/payments",
        "body": json.dumps(
            {
                "booking_id": "booking-123",
                "amount": 45.00,
                "payment_method": "credit_card",
                "payment_token": "test_decline",
            }
        ),
    }

    with patch.dict(
        os.environ,
        {"PAYMENTS_TABLE": "payments-test", "BOOKINGS_TABLE": "bookings-test"},
    ):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Payment processing failed" in body["error"]
    assert "Card declined" in body["reason"]


@mock_aws 
def test_get_payment():
    """Test getting payment details"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    dynamodb.create_table(
        TableName="payments-test",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    # Create test payment
    test_payment = {
        "id": "payment-123",
        "booking_id": "booking-123",
        "amount": Decimal("45.00"),
        "status": "completed",
    }
    payments_table = dynamodb.Table("payments-test")
    payments_table.put_item(Item=test_payment)

    # Test event
    event = {
        "httpMethod": "GET",
        "path": "/payments/payment-123",
        "pathParameters": {"id": "payment-123"},
    }

    with patch.dict(os.environ, {"PAYMENTS_TABLE": "payments-test"}):
        response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["id"] == "payment-123"
    assert float(body["amount"]) == 45.00
    assert body["status"] == "completed"


def test_simulate_payment_processing():
    """Test payment simulation logic"""
    # Test successful payment
    result = simulate_payment_processing("test_success", 45.00)
    assert result["success"] is True
    assert "transaction_id" in result

    # Test declined payment
    result = simulate_payment_processing("test_decline", 45.00)
    assert result["success"] is False
    assert result["error"] == "Card declined"

    # Test insufficient funds
    result = simulate_payment_processing("test_insufficient_funds", 45.00)
    assert result["success"] is False
    assert result["error"] == "Insufficient funds"

    # Test invalid card
    result = simulate_payment_processing("test_invalid_card", 45.00)
    assert result["success"] is False
    assert result["error"] == "Invalid card number"