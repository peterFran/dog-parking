import json
import boto3
import uuid
import os
import decimal
from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError
import logging
import sys

sys.path.append("/opt/python")
from auth import require_auth, optional_auth, get_user_id_from_event

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# DynamoDB resource will be initialized in lambda_handler


def lambda_handler(event, context):
    """
    Main Lambda handler for booking management operations
    """
    try:
        # Initialize DynamoDB resource - use local endpoint if available
        dynamodb_kwargs = {
            "region_name": os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        }
        if os.environ.get("AWS_SAM_LOCAL"):
            dynamodb_kwargs["endpoint_url"] = "http://dynamodb-local:8000"
        dynamodb = boto3.resource("dynamodb", **dynamodb_kwargs)

        # Get environment variables
        bookings_table_name = os.environ.get("BOOKINGS_TABLE")
        dogs_table_name = os.environ.get("DOGS_TABLE")
        owners_table_name = os.environ.get("OWNERS_TABLE")
        venues_table_name = os.environ.get("VENUES_TABLE")
        slots_table_name = os.environ.get("SLOTS_TABLE")

        bookings_table = dynamodb.Table(bookings_table_name)
        dogs_table = dynamodb.Table(dogs_table_name)
        owners_table = dynamodb.Table(owners_table_name)
        venues_table = dynamodb.Table(venues_table_name)
        slots_table = dynamodb.Table(slots_table_name)

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
            return create_booking_with_auth(
                bookings_table, dogs_table, owners_table, venues_table, slots_table, event
            )
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


@require_auth
def list_bookings(table, event):
    """List all bookings for authenticated user"""
    try:
        # Get owner ID from auth claims
        owner_id = get_user_id_from_event(event)

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


@require_auth
def create_booking_with_auth(
    bookings_table, dogs_table, owners_table, venues_table, slots_table, event
):
    """Create a new booking with authentication"""
    try:
        # Get user ID from auth claims
        user_id = get_user_id_from_event(event)

        # Parse request body
        body = json.loads(event.get("body", "{}"))

        # Validate required fields (owner_id not needed - comes from auth)
        required_fields = [
            "dog_id",
            "venue_id",
            "service_type",
            "start_time",
            "end_time",
        ]
        for field in required_fields:
            if field not in body:
                return create_response(
                    400, {"error": f"Missing required field: {field}"}
                )

        # Verify dog exists and belongs to authenticated user
        dog_response = dogs_table.get_item(Key={"id": body["dog_id"]})
        if "Item" not in dog_response:
            return create_response(404, {"error": "Dog not found"})

        dog = dog_response["Item"]
        if dog["owner_id"] != user_id:
            return create_response(403, {"error": "Dog does not belong to this owner"})

        # Verify owner profile exists (new schema)
        owner_response = owners_table.get_item(Key={"user_id": user_id})
        if "Item" not in owner_response:
            return create_response(404, {"error": "Owner profile not found"})

        # Verify venue exists
        venue_response = venues_table.get_item(Key={"id": body["venue_id"]})
        if "Item" not in venue_response:
            return create_response(404, {"error": "Venue not found"})

        venue = venue_response["Item"]

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

        # Reserve slot capacity atomically
        try:
            reserve_result = reserve_slot_capacity(slots_table, body["venue_id"], start_time, end_time)
            if not reserve_result["success"]:
                return create_response(400, {"error": reserve_result["message"]})
        except ClientError as e:
            logger.error(f"Failed to reserve capacity: {str(e)}")
            return create_response(500, {"error": "Booking failed - capacity unavailable"})

        # Calculate price based on service type and duration
        price = calculate_price(body["service_type"], start_time, end_time)

        # Create booking record
        booking_id = f"booking-{uuid.uuid4()}"
        now = datetime.now(timezone.utc).isoformat()

        booking_item = {
            "id": booking_id,
            "dog_id": body["dog_id"],
            "owner_id": user_id,  # Use authenticated user ID
            "venue_id": body["venue_id"],
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
        expression_names = {}

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
                if field == "status":
                    # Handle reserved keyword
                    update_expression += f", #status = :status"
                    expression_names["#status"] = "status"
                    expression_values[":status"] = body[field]
                else:
                    update_expression += f", {field} = :{field}"
                    expression_values[f":{field}"] = body[field]

        # Update the item
        kwargs = {
            "Key": {"id": booking_id},
            "UpdateExpression": update_expression,
            "ExpressionAttributeValues": expression_values,
            "ReturnValues": "ALL_NEW",
        }
        if expression_names:
            kwargs["ExpressionAttributeNames"] = expression_names

        response = table.update_item(**kwargs)

        logger.info(f"Updated booking: {booking_id}")
        return create_response(200, response["Attributes"])

    except json.JSONDecodeError:
        return create_response(400, {"error": "Invalid JSON in request body"})
    except ClientError as e:
        logger.error(f"Error updating booking: {str(e)}")
        return create_response(500, {"error": "Failed to update booking"})


def cancel_booking(table, booking_id):
    """Cancel a booking and release slot capacity"""
    try:
        # Get booking details first
        existing_booking = table.get_item(Key={"id": booking_id})
        if "Item" not in existing_booking:
            return create_response(404, {"error": "Booking not found"})

        booking = existing_booking["Item"]

        # Release slot capacity
        try:
            dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
            if os.environ.get("AWS_SAM_LOCAL"):
                dynamodb = boto3.resource("dynamodb", region_name="us-east-1", endpoint_url="http://dynamodb-local:8000")
            slots_table = dynamodb.Table(os.environ.get("SLOTS_TABLE"))
            release_slot_capacity(
                slots_table,
                booking["venue_id"],
                datetime.fromisoformat(booking["start_time"].replace("Z", "+00:00")),
                datetime.fromisoformat(booking["end_time"].replace("Z", "+00:00"))
            )
        except Exception as e:
            logger.warning(f"Failed to release capacity: {str(e)}")

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


def reserve_slot_capacity(slots_table, venue_id, start_time, end_time):
    """
    Atomically decrement available capacity for booking time slots.
    Rolls back on failure to maintain consistency.
    """
    date_str = start_time.strftime("%Y-%m-%d")
    slot_duration = timedelta(hours=1)

    reserved_slots = []
    current_time = start_time

    try:
        while current_time < end_time:
            slot_time_str = current_time.strftime("%H:%M")
            venue_date_key = f"{venue_id}#{date_str}"

            # Atomic decrement with condition
            try:
                slots_table.update_item(
                    Key={
                        "venue_date": venue_date_key,
                        "slot_time": slot_time_str
                    },
                    UpdateExpression="SET available_capacity = available_capacity - :dec, booked_count = booked_count + :inc",
                    ConditionExpression="available_capacity >= :dec",
                    ExpressionAttributeValues={
                        ":dec": 1,
                        ":inc": 1
                    },
                    ReturnValues="UPDATED_NEW"
                )

                reserved_slots.append({
                    "venue_date": venue_date_key,
                    "slot_time": slot_time_str
                })

            except ClientError as e:
                if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                    # Rollback previously reserved slots
                    rollback_reserved_slots(slots_table, reserved_slots)
                    return {
                        "success": False,
                        "message": f"No availability at {slot_time_str} on {date_str}"
                    }
                else:
                    raise

            current_time += slot_duration

        return {
            "success": True,
            "message": "Capacity reserved successfully",
            "reserved_slots": reserved_slots
        }

    except Exception as e:
        # Rollback on any error
        rollback_reserved_slots(slots_table, reserved_slots)
        raise


def rollback_reserved_slots(slots_table, reserved_slots):
    """Rollback capacity reservations if booking fails"""
    for slot in reserved_slots:
        try:
            slots_table.update_item(
                Key={
                    "venue_date": slot["venue_date"],
                    "slot_time": slot["slot_time"]
                },
                UpdateExpression="SET available_capacity = available_capacity + :inc, booked_count = booked_count - :dec",
                ExpressionAttributeValues={
                    ":inc": 1,
                    ":dec": 1
                }
            )
        except ClientError as e:
            logger.error(f"Rollback failed for slot {slot}: {str(e)}")


def release_slot_capacity(slots_table, venue_id, start_time, end_time):
    """Release slot capacity when booking is cancelled"""
    date_str = start_time.strftime("%Y-%m-%d")
    slot_duration = timedelta(hours=1)
    current_time = start_time

    while current_time < end_time:
        slot_time_str = current_time.strftime("%H:%M")
        try:
            slots_table.update_item(
                Key={
                    "venue_date": f"{venue_id}#{date_str}",
                    "slot_time": slot_time_str
                },
                UpdateExpression="SET available_capacity = available_capacity + :inc, booked_count = booked_count - :dec",
                ConditionExpression="booked_count > :zero",
                ExpressionAttributeValues={
                    ":inc": 1,
                    ":dec": 1,
                    ":zero": 0
                }
            )
        except ClientError as e:
            logger.error(f"Failed to release slot {slot_time_str}: {str(e)}")

        current_time += slot_duration


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
