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
    Main Lambda handler for booking management operations
    """
    try:
        # Initialize DynamoDB resource - use local endpoint if available
        dynamodb_kwargs = {"region_name": os.environ.get("AWS_DEFAULT_REGION", "us-east-1")}
        if os.environ.get("AWS_SAM_LOCAL"):
            dynamodb_kwargs["endpoint_url"] = "http://dynamodb-local:8000"
        dynamodb = boto3.resource("dynamodb", **dynamodb_kwargs)
        
        # Get environment variables
        bookings_table_name = os.environ.get("BOOKINGS_TABLE")
        dogs_table_name = os.environ.get("DOGS_TABLE")
        owners_table_name = os.environ.get("OWNERS_TABLE")

        bookings_table = dynamodb.Table(bookings_table_name)
        dogs_table = dynamodb.Table(dogs_table_name)
        owners_table = dynamodb.Table(owners_table_name)

        # Log the incoming event
        logger.info(f"Received event: {json.dumps(event)}")

        # Get HTTP method and path
        http_method = event.get("httpMethod")
        path = event.get("path", "")
        path_parameters = event.get("pathParameters") or {}

        # Route to appropriate handler
        if http_method == "GET":
            if path_parameters.get("id"):
                return get_booking(bookings_table, path_parameters["id"])
            else:
                return list_bookings(bookings_table, event)
        elif http_method == "POST":
            return create_booking(bookings_table, dogs_table, owners_table, event)
        elif http_method == "PUT":
            return update_booking(bookings_table, path_parameters["id"], event)
        elif http_method == "DELETE":
            return cancel_booking(bookings_table, path_parameters["id"])
        else:
            return create_response(405, {"error": "Method not allowed"})

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return create_response(500, {"error": "Internal server error"})


def get_booking(table, booking_id):
    """Get a specific booking by ID"""
    try:
        response = table.get_item(Key={"id": booking_id})

        if "Item" not in response:
            return create_response(404, {"error": "Booking not found"})

        return create_response(200, response["Item"])

    except ClientError as e:
        logger.error(f"Error getting booking: {str(e)}")
        return create_response(500, {"error": "Failed to get booking"})


def list_bookings(table, event):
    """List all bookings for a specific owner"""
    try:
        # Get query parameters
        query_params = event.get("queryStringParameters") or {}
        owner_id = query_params.get("owner_id")

        if not owner_id:
            return create_response(400, {"error": "owner_id is required"})

        # Query using GSI
        from boto3.dynamodb.conditions import Key
        response = table.query(
            IndexName="owner-time-index",
            KeyConditionExpression=Key("owner_id").eq(owner_id),
            ScanIndexForward=False,  # Sort by start_time descending
        )

        bookings = response.get("Items", [])

        return create_response(200, {"bookings": bookings, "count": len(bookings)})

    except ClientError as e:
        logger.error(f"Error listing bookings: {str(e)}")
        return create_response(500, {"error": "Failed to list bookings"})


def create_booking(bookings_table, dogs_table, owners_table, event):
    """Create a new booking"""
    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))

        # Validate required fields
        required_fields = [
            "dog_id",
            "owner_id",
            "service_type",
            "start_time",
            "end_time",
        ]
        for field in required_fields:
            if field not in body:
                return create_response(
                    400, {"error": f"Missing required field: {field}"}
                )

        # Verify dog exists and belongs to owner
        dog_response = dogs_table.get_item(Key={"id": body["dog_id"]})
        if "Item" not in dog_response:
            return create_response(404, {"error": "Dog not found"})

        dog = dog_response["Item"]
        if dog["owner_id"] != body["owner_id"]:
            return create_response(403, {"error": "Dog does not belong to this owner"})

        # Verify owner exists
        owner_response = owners_table.get_item(Key={"id": body["owner_id"]})
        if "Item" not in owner_response:
            return create_response(404, {"error": "Owner not found"})

        # Validate service type
        valid_services = ["daycare", "boarding", "grooming", "walking", "training"]
        if body["service_type"] not in valid_services:
            return create_response(
                400,
                {"error": f"Invalid service type. Must be one of: {valid_services}"},
            )

        # Validate datetime format
        try:
            start_time = datetime.fromisoformat(
                body["start_time"].replace("Z", "+00:00")
            )
            end_time = datetime.fromisoformat(body["end_time"].replace("Z", "+00:00"))
        except ValueError:
            return create_response(
                400, {"error": "Invalid datetime format. Use ISO format."}
            )

        if start_time >= end_time:
            return create_response(400, {"error": "Start time must be before end time"})

        # Calculate price based on service type and duration
        price = calculate_price(body["service_type"], start_time, end_time)

        # Create booking record
        booking_id = f"booking-{uuid.uuid4()}"
        now = datetime.now(timezone.utc).isoformat()

        booking_item = {
            "id": booking_id,
            "dog_id": body["dog_id"],
            "owner_id": body["owner_id"],
            "service_type": body["service_type"],
            "start_time": body["start_time"],
            "end_time": body["end_time"],
            "status": "pending",
            "price": decimal.Decimal(str(price)),
            "special_instructions": body.get("special_instructions", ""),
            "created_at": now,
            "updated_at": now,
        }

        bookings_table.put_item(Item=booking_item)

        logger.info(f"Created booking: {booking_id}")
        return create_response(201, booking_item)

    except json.JSONDecodeError:
        return create_response(400, {"error": "Invalid JSON in request body"})
    except ClientError as e:
        logger.error(f"Error creating booking: {str(e)}")
        return create_response(500, {"error": "Failed to create booking"})


def update_booking(table, booking_id, event):
    """Update an existing booking"""
    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))

        # Check if booking exists
        existing_booking = table.get_item(Key={"id": booking_id})
        if "Item" not in existing_booking:
            return create_response(404, {"error": "Booking not found"})

        # Build update expression
        update_expression = "SET updated_at = :updated_at"
        expression_values = {":updated_at": datetime.now(timezone.utc).isoformat()}

        # Update allowed fields
        allowed_fields = [
            "service_type",
            "start_time",
            "end_time",
            "status",
            "special_instructions",
        ]
        for field in allowed_fields:
            if field in body:
                update_expression += f", {field} = :{field}"
                expression_values[f":{field}"] = body[field]

        # Update the item
        response = table.update_item(
            Key={"id": booking_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ReturnValues="ALL_NEW",
        )

        logger.info(f"Updated booking: {booking_id}")
        return create_response(200, response["Attributes"])

    except json.JSONDecodeError:
        return create_response(400, {"error": "Invalid JSON in request body"})
    except ClientError as e:
        logger.error(f"Error updating booking: {str(e)}")
        return create_response(500, {"error": "Failed to update booking"})


def cancel_booking(table, booking_id):
    """Cancel a booking"""
    try:
        # Check if booking exists
        existing_booking = table.get_item(Key={"id": booking_id})
        if "Item" not in existing_booking:
            return create_response(404, {"error": "Booking not found"})

        # Update status to cancelled
        response = table.update_item(
            Key={"id": booking_id},
            UpdateExpression="SET #status = :status, updated_at = :updated_at",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": "cancelled",
                ":updated_at": datetime.now(timezone.utc).isoformat(),
            },
            ReturnValues="ALL_NEW",
        )

        logger.info(f"Cancelled booking: {booking_id}")
        return create_response(200, response["Attributes"])

    except ClientError as e:
        logger.error(f"Error cancelling booking: {str(e)}")
        return create_response(500, {"error": "Failed to cancel booking"})


def calculate_price(service_type, start_time, end_time):
    """Calculate price based on service type and duration"""
    # Price per hour for different services
    hourly_rates = {
        "daycare": 15.00,
        "boarding": 45.00,
        "grooming": 60.00,
        "walking": 25.00,
        "training": 75.00,
    }

    # Calculate duration in hours
    duration = (end_time - start_time).total_seconds() / 3600

    # Minimum 1 hour charge
    if duration < 1:
        duration = 1

    rate = hourly_rates.get(service_type, 30.00)  # Default rate
    return round(rate * duration, 2)


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
