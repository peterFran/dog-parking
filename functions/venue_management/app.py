import json
import boto3
import uuid
import os
import decimal
from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError
from pydantic import ValidationError
import logging
import sys

sys.path.append("/opt/python")
from models import (
    VenueRequest,
    VenueResponse,
    VenueListResponse,
    ErrorResponse,
)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# DynamoDB resource will be initialized in lambda_handler
dynamodb = None


def lambda_handler(event, context):
    """
    Main Lambda handler for venue management operations
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
        venues_table_name = os.environ.get("VENUES_TABLE")
        venues_table = dynamodb.Table(venues_table_name)

        # Log the incoming event
        logger.info(f"Received event: {json.dumps(event)}")

        # Get HTTP method and path
        http_method = event.get("httpMethod")
        path = event.get("path", "")
        path_parameters = event.get("pathParameters") or {}

        # Route to appropriate handler
        if "/venues" in path:
            if http_method == "GET":
                if path_parameters.get("id"):
                    return get_venue(venues_table, path_parameters["id"])
                else:
                    return list_venues(venues_table, event)
            elif http_method == "POST":
                return create_venue(venues_table, dynamodb, event)
            elif http_method == "PUT":
                return update_venue(venues_table, path_parameters["id"], event)
            elif http_method == "DELETE":
                return delete_venue(venues_table, path_parameters["id"])
        else:
            return create_response(404, {"error": "Endpoint not found"})

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return create_response(500, {"error": "Internal server error"})


def create_venue(table, dynamodb, event):
    """Create a new venue"""
    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))

        # Validate with Pydantic model - replaces all manual validation!
        try:
            venue_request = VenueRequest(**body)
        except ValidationError as e:
            logger.warning(f"Validation error: {e.errors()}")
            return create_response(422, {"errors": e.errors()})

        # Create venue record
        venue_id = f"venue-{uuid.uuid4()}"
        now = datetime.now(timezone.utc).isoformat()

        venue_item = {
            "id": venue_id,
            "name": venue_request.name,
            "address": venue_request.address,
            "capacity": venue_request.capacity,
            "operating_hours": venue_request.operating_hours.model_dump(),
            "services": [s.value for s in venue_request.services] if venue_request.services else ["daycare"],
            "slot_duration": venue_request.slot_duration,
            "created_at": now,
            "updated_at": now,
        }

        # Save venue first
        table.put_item(Item=venue_item)

        # Auto-generate slots for next 30 days
        try:
            slots_table = dynamodb.Table(os.environ.get("SLOTS_TABLE"))
            auto_generate_initial_slots(venue_id, venue_item, slots_table)
        except Exception as e:
            logger.warning(f"Failed to auto-generate slots: {str(e)}")

        logger.info(f"Created venue: {venue_id}")
        return create_response(201, venue_item)

    except json.JSONDecodeError:
        return create_response(400, {"error": "Invalid JSON in request body"})
    except ClientError as e:
        logger.error(f"Error creating venue: {str(e)}")
        return create_response(500, {"error": "Failed to create venue"})


def get_venue(table, venue_id):
    """Get venue by ID"""
    try:
        response = table.get_item(Key={"id": venue_id})

        if "Item" not in response:
            return create_response(404, {"error": "Venue not found"})

        return create_response(200, response["Item"])

    except ClientError as e:
        logger.error(f"Error getting venue: {str(e)}")
        return create_response(500, {"error": "Failed to get venue"})


def list_venues(table, event):
    """List all venues"""
    try:
        # Get query parameters
        query_params = event.get("queryStringParameters") or {}
        limit = int(query_params.get("limit", 50))

        # Scan table for venues
        response = table.scan(Limit=limit)

        venues = response.get("Items", [])

        return create_response(200, {"venues": venues, "count": len(venues)})

    except ClientError as e:
        logger.error(f"Error listing venues: {str(e)}")
        return create_response(500, {"error": "Failed to list venues"})


def update_venue(table, venue_id, event):
    """Update venue"""
    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))

        # Check if venue exists
        existing_venue = table.get_item(Key={"id": venue_id})
        if "Item" not in existing_venue:
            return create_response(404, {"error": "Venue not found"})

        # Build update expression
        update_expression = "SET updated_at = :updated_at"
        expression_values = {":updated_at": datetime.now(timezone.utc).isoformat()}

        # Update allowed fields
        allowed_fields = [
            "name",
            "address",
            "capacity",
            "operating_hours",
            "services",
            "slot_duration",
        ]
        expression_names = {}

        for field in allowed_fields:
            if field in body:
                if field == "name":
                    # 'name' is a reserved keyword in DynamoDB
                    update_expression += f", #name = :name"
                    expression_names["#name"] = "name"
                    expression_values[":name"] = body[field]
                elif field == "capacity":
                    if not isinstance(body[field], int) or body[field] < 1:
                        return create_response(
                            400, {"error": "Capacity must be a positive integer"}
                        )
                    update_expression += f", capacity = :capacity"
                    expression_values[":capacity"] = body[field]
                elif field == "operating_hours":
                    if not validate_operating_hours(body[field]):
                        return create_response(
                            400, {"error": "Invalid operating hours format"}
                        )
                    update_expression += f", operating_hours = :operating_hours"
                    expression_values[":operating_hours"] = body[field]
                else:
                    update_expression += f", {field} = :{field}"
                    expression_values[f":{field}"] = body[field]

        # Update the item
        update_params = {
            "Key": {"id": venue_id},
            "UpdateExpression": update_expression,
            "ExpressionAttributeValues": expression_values,
            "ReturnValues": "ALL_NEW",
        }
        if expression_names:
            update_params["ExpressionAttributeNames"] = expression_names

        response = table.update_item(**update_params)

        logger.info(f"Updated venue: {venue_id}")
        return create_response(200, response["Attributes"])

    except json.JSONDecodeError:
        return create_response(400, {"error": "Invalid JSON in request body"})
    except ClientError as e:
        logger.error(f"Error updating venue: {str(e)}")
        return create_response(500, {"error": "Failed to update venue"})


def delete_venue(table, venue_id):
    """Delete venue"""
    try:
        # Check if venue exists
        existing_venue = table.get_item(Key={"id": venue_id})
        if "Item" not in existing_venue:
            return create_response(404, {"error": "Venue not found"})

        # Delete the venue
        table.delete_item(Key={"id": venue_id})

        logger.info(f"Deleted venue: {venue_id}")
        return create_response(200, {"message": "Venue deleted successfully"})

    except ClientError as e:
        logger.error(f"Error deleting venue: {str(e)}")
        return create_response(500, {"error": "Failed to delete venue"})


def auto_generate_initial_slots(venue_id, venue_data, slots_table):
    """Automatically generate slots for new venues (next 30 days)"""
    from datetime import date

    start_date = date.today()
    end_date = start_date + timedelta(days=30)

    slots_created = 0
    current_date = start_date

    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        day_slots = generate_slots_for_date_helper(venue_data, date_str)

        with slots_table.batch_writer() as batch:
            for slot in day_slots:
                batch.put_item(Item={
                    "venue_date": f"{venue_id}#{date_str}",
                    "slot_time": slot["time"],
                    "venue_id": venue_id,
                    "date": date_str,
                    "available_capacity": slot["available_capacity"],
                    "total_capacity": slot["total_capacity"],
                    "booked_count": 0,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "ttl": int((current_date + timedelta(days=90)).timestamp())
                })
                slots_created += 1

        current_date += timedelta(days=1)

    logger.info(f"Auto-generated {slots_created} slots for venue {venue_id}")
    return slots_created


def generate_slots_for_date_helper(venue, date_str):
    """Helper to generate slot data for a specific date"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        day_of_week = date_obj.strftime("%A").lower()

        operating_hours = venue.get("operating_hours", {})
        if day_of_week not in operating_hours:
            return []

        day_hours = operating_hours[day_of_week]
        if not day_hours.get("open", True):
            return []

        start_time = datetime.strptime(day_hours["start"], "%H:%M").time()
        end_time = datetime.strptime(day_hours["end"], "%H:%M").time()
        slot_duration = timedelta(minutes=int(venue.get("slot_duration", 60)))

        slots = []
        current_time = datetime.combine(date_obj, start_time)
        end_datetime = datetime.combine(date_obj, end_time)

        while current_time < end_datetime:
            slots.append({
                "time": current_time.strftime("%H:%M"),
                "available_capacity": venue["capacity"],
                "total_capacity": venue["capacity"]
            })
            current_time += slot_duration

        return slots
    except (ValueError, KeyError):
        return []


def validate_operating_hours(operating_hours):
    """Validate operating hours format"""
    if not isinstance(operating_hours, dict):
        return False

    valid_days = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]

    for day, hours in operating_hours.items():
        if day not in valid_days:
            return False

        if not isinstance(hours, dict):
            return False

        # Check if day is closed
        if not hours.get("open", True):
            continue

        # Validate time format
        if "start" not in hours or "end" not in hours:
            return False

        try:
            datetime.strptime(hours["start"], "%H:%M")
            datetime.strptime(hours["end"], "%H:%M")
        except ValueError:
            return False

    return True


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
