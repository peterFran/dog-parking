import json
import boto3
import uuid
import os
import decimal
from datetime import datetime, timezone
from botocore.exceptions import ClientError
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# DynamoDB resource will be initialized in lambda_handler
dynamodb = None


def lambda_handler(event, context):
    """
    Main Lambda handler for payment processing operations
    """
    try:
        # Initialize DynamoDB resource - use local endpoint if available
        dynamodb_kwargs = {"region_name": os.environ.get("AWS_DEFAULT_REGION", "us-east-1")}
        if os.environ.get("AWS_SAM_LOCAL"):
            dynamodb_kwargs["endpoint_url"] = "http://dynamodb-local:8000"
        dynamodb = boto3.resource("dynamodb", **dynamodb_kwargs)
        
        # Get environment variables
        payments_table_name = os.environ.get("PAYMENTS_TABLE")
        bookings_table_name = os.environ.get("BOOKINGS_TABLE")

        payments_table = dynamodb.Table(payments_table_name)
        bookings_table = dynamodb.Table(bookings_table_name)

        # Log the incoming event
        logger.info(f"Received event: {json.dumps(event)}")

        # Get HTTP method and path
        http_method = event.get("httpMethod")
        path = event.get("path", "")
        path_parameters = event.get("pathParameters") or {}

        # Route to appropriate handler
        if http_method == "GET":
            if path_parameters.get("id"):
                return get_payment(payments_table, path_parameters["id"])
            else:
                return list_payments(payments_table, event)
        elif http_method == "POST":
            return process_payment(payments_table, bookings_table, event)
        else:
            return create_response(405, {"error": "Method not allowed"})

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return create_response(500, {"error": "Internal server error"})


def get_payment(table, payment_id):
    """Get a specific payment by ID"""
    try:
        response = table.get_item(Key={"id": payment_id})

        if "Item" not in response:
            return create_response(404, {"error": "Payment not found"})

        return create_response(200, response["Item"])

    except ClientError as e:
        logger.error(f"Error getting payment: {str(e)}")
        return create_response(500, {"error": "Failed to get payment"})


def list_payments(table, event):
    """List all payments for a specific booking"""
    try:
        # Get query parameters
        query_params = event.get("queryStringParameters") or {}
        booking_id = query_params.get("booking_id")

        if not booking_id:
            return create_response(400, {"error": "booking_id is required"})

        # Query using GSI
        from boto3.dynamodb.conditions import Key
        response = table.query(
            IndexName="booking-index",
            KeyConditionExpression=Key("booking_id").eq(booking_id)
        )

        payments = response.get("Items", [])

        return create_response(200, {"payments": payments, "count": len(payments)})

    except ClientError as e:
        logger.error(f"Error listing payments: {str(e)}")
        return create_response(500, {"error": "Failed to list payments"})


def process_payment(payments_table, bookings_table, event):
    """Process a new payment"""
    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))

        # Validate required fields
        required_fields = ["booking_id", "amount", "payment_method", "payment_token"]
        for field in required_fields:
            if field not in body:
                return create_response(
                    400, {"error": f"Missing required field: {field}"}
                )

        # Verify booking exists
        booking_response = bookings_table.get_item(Key={"id": body["booking_id"]})
        if "Item" not in booking_response:
            return create_response(404, {"error": "Booking not found"})

        booking = booking_response["Item"]

        # Validate payment amount matches booking price
        if decimal.Decimal(str(body["amount"])) != decimal.Decimal(str(booking["price"])):
            return create_response(
                400,
                {
                    "error": "Payment amount does not match booking price",
                    "expected": float(booking["price"]),
                    "provided": body["amount"],
                },
            )

        # Validate payment method
        valid_methods = ["credit_card", "debit_card", "paypal", "bank_transfer"]
        if body["payment_method"] not in valid_methods:
            return create_response(
                400,
                {"error": f"Invalid payment method. Must be one of: {valid_methods}"},
            )

        # Process payment (simulated - in real app, integrate with Stripe, PayPal, etc.)
        payment_result = simulate_payment_processing(
            body["payment_token"], body["amount"]
        )

        if not payment_result["success"]:
            return create_response(
                400,
                {
                    "error": "Payment processing failed",
                    "reason": payment_result["error"],
                },
            )

        # Create payment record
        payment_id = f"payment-{uuid.uuid4()}"
        now = datetime.now(timezone.utc).isoformat()

        payment_item = {
            "id": payment_id,
            "booking_id": body["booking_id"],
            "amount": decimal.Decimal(str(body["amount"])),
            "payment_method": body["payment_method"],
            "transaction_id": payment_result["transaction_id"],
            "status": "completed",
            "processed_at": now,
            "created_at": now,
            "updated_at": now,
        }

        payments_table.put_item(Item=payment_item)

        # Update booking status to confirmed
        bookings_table.update_item(
            Key={"id": body["booking_id"]},
            UpdateExpression="SET #status = :status, payment_id = :payment_id, updated_at = :updated_at",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": "confirmed",
                ":payment_id": payment_id,
                ":updated_at": now,
            },
        )

        logger.info(
            f"Processed payment: {payment_id} for booking: {body['booking_id']}"
        )
        return create_response(201, payment_item)

    except json.JSONDecodeError:
        return create_response(400, {"error": "Invalid JSON in request body"})
    except ValueError as e:
        return create_response(400, {"error": str(e)})
    except ClientError as e:
        logger.error(f"Error processing payment: {str(e)}")
        return create_response(500, {"error": "Failed to process payment"})


def simulate_payment_processing(payment_token, amount):
    """Simulate payment processing (replace with real payment gateway)"""
    # In a real application, integrate with:
    # - Stripe: https://stripe.com/docs/api
    # - PayPal: https://developer.paypal.com/docs/api/
    # - Square: https://developer.squareup.com/docs/payments-api

    # Simulate different scenarios based on payment token
    if payment_token == "test_decline":
        return {"success": False, "error": "Card declined"}
    elif payment_token == "test_insufficient_funds":
        return {"success": False, "error": "Insufficient funds"}
    elif payment_token == "test_invalid_card":
        return {"success": False, "error": "Invalid card number"}
    else:
        # Successful payment
        return {
            "success": True,
            "transaction_id": f"txn_{uuid.uuid4()}",
            "amount": amount,
            "currency": "USD",
        }


def create_response(status_code, body):
    """Create a standardized API response"""
    def default_serializer(o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        },
        "body": json.dumps(body, default=default_serializer) if body else "",
    }
