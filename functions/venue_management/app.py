import json
import boto3
import uuid
import os
import decimal
from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError
import logging

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
        if "/venues/" in path and "/slots" in path:
            venue_id = path_parameters.get("id")
            if http_method == "GET":
                return get_venue_slots(venues_table, venue_id, event)
            elif http_method == "POST":
                return update_venue_slots(venues_table, venue_id, event)
        elif "/venues" in path:
            if http_method == "GET":
                if path_parameters.get("id"):
                    return get_venue(venues_table, path_parameters["id"])
                else:
                    return list_venues(venues_table, event)
            elif http_method == "POST":
                return create_venue(venues_table, event)
            elif http_method == "PUT":
                return update_venue(venues_table, path_parameters["id"], event)
            elif http_method == "DELETE":
                return delete_venue(venues_table, path_parameters["id"])
        else:
            return create_response(404, {"error": "Endpoint not found"})

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return create_response(500, {"error": "Internal server error"})


def create_venue(table, event):
    """Create a new venue"""
    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))

        # Validate required fields
        required_fields = ["name", "address", "capacity", "operating_hours"]
        for field in required_fields:
            if field not in body:
                return create_response(
                    400, {"error": f"Missing required field: {field}"}
                )

        # Validate capacity
        if not isinstance(body["capacity"], int) or body["capacity"] < 1:
            return create_response(400, {"error": "Capacity must be a positive integer"})

        # Validate operating hours
        if not validate_operating_hours(body["operating_hours"]):
            return create_response(400, {"error": "Invalid operating hours format"})

        # Create venue record
        venue_id = f"venue-{uuid.uuid4()}"
        now = datetime.now(timezone.utc).isoformat()

        venue_item = {
            "id": venue_id,
            "name": body["name"],
            "address": body["address"],
            "capacity": body["capacity"],
            "operating_hours": body["operating_hours"],
            "services": body.get("services", ["daycare"]),
            "slot_duration": body.get("slot_duration", 60),  # Default 60 minutes
            "available_slots": {},  # Will be populated when slots are generated
            "created_at": now,
            "updated_at": now,
        }

        table.put_item(Item=venue_item)

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
        
        return create_response(200, {
            "venues": venues,
            "count": len(venues)
        })

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
        allowed_fields = ["name", "address", "capacity", "operating_hours", "services", "slot_duration"]
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
                        return create_response(400, {"error": "Capacity must be a positive integer"})
                    update_expression += f", capacity = :capacity"
                    expression_values[":capacity"] = body[field]
                elif field == "operating_hours":
                    if not validate_operating_hours(body[field]):
                        return create_response(400, {"error": "Invalid operating hours format"})
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


def get_venue_slots(table, venue_id, event):
    """Get available slots for a venue"""
    try:
        # Get query parameters
        query_params = event.get("queryStringParameters") or {}
        date_str = query_params.get("date")  # Format: YYYY-MM-DD
        
        if not date_str:
            return create_response(400, {"error": "Date parameter is required"})

        # Get venue
        venue_response = table.get_item(Key={"id": venue_id})
        if "Item" not in venue_response:
            return create_response(404, {"error": "Venue not found"})

        venue = venue_response["Item"]
        
        # Generate slots for the requested date
        slots = generate_slots_for_date(venue, date_str)
        
        return create_response(200, {
            "venue_id": venue_id,
            "date": date_str,
            "slots": slots
        })

    except ValueError as e:
        return create_response(400, {"error": f"Invalid date format: {str(e)}"})
    except ClientError as e:
        logger.error(f"Error getting venue slots: {str(e)}")
        return create_response(500, {"error": "Failed to get venue slots"})


def update_venue_slots(table, venue_id, event):
    """Update slot availability for a venue"""
    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))
        
        # Validate required fields
        required_fields = ["date", "slot_time", "available_capacity"]
        for field in required_fields:
            if field not in body:
                return create_response(
                    400, {"error": f"Missing required field: {field}"}
                )

        # Get venue
        venue_response = table.get_item(Key={"id": venue_id})
        if "Item" not in venue_response:
            return create_response(404, {"error": "Venue not found"})

        venue = venue_response["Item"]
        
        # Update slot availability
        date_str = body["date"]
        slot_time = body["slot_time"]
        available_capacity = body["available_capacity"]
        
        # Initialize available_slots if not exists
        if "available_slots" not in venue:
            venue["available_slots"] = {}
        
        # Initialize date if not exists
        if date_str not in venue["available_slots"]:
            venue["available_slots"][date_str] = {}
        
        # Update the specific slot
        venue["available_slots"][date_str][slot_time] = available_capacity
        
        # Update the venue in database
        table.update_item(
            Key={"id": venue_id},
            UpdateExpression="SET available_slots = :slots, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":slots": venue["available_slots"],
                ":updated_at": datetime.now(timezone.utc).isoformat()
            }
        )

        logger.info(f"Updated slots for venue: {venue_id}")
        return create_response(200, {
            "message": "Slot availability updated successfully",
            "venue_id": venue_id,
            "date": date_str,
            "slot_time": slot_time,
            "available_capacity": available_capacity
        })

    except json.JSONDecodeError:
        return create_response(400, {"error": "Invalid JSON in request body"})
    except ClientError as e:
        logger.error(f"Error updating venue slots: {str(e)}")
        return create_response(500, {"error": "Failed to update venue slots"})


def generate_slots_for_date(venue, date_str):
    """Generate time slots for a specific date based on venue operating hours"""
    try:
        # Parse date
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        day_of_week = date_obj.strftime("%A").lower()
        
        # Get operating hours for the day
        operating_hours = venue["operating_hours"]
        if day_of_week not in operating_hours:
            return []
        
        day_hours = operating_hours[day_of_week]
        if not day_hours.get("open", True):
            return []
        
        # Parse times
        start_time = datetime.strptime(day_hours["start"], "%H:%M").time()
        end_time = datetime.strptime(day_hours["end"], "%H:%M").time()
        
        # Generate slots
        slots = []
        slot_duration = timedelta(minutes=venue.get("slot_duration", 60))
        
        current_time = datetime.combine(date_obj, start_time)
        end_datetime = datetime.combine(date_obj, end_time)
        
        while current_time < end_datetime:
            slot_time_str = current_time.strftime("%H:%M")
            
            # Check if slot is in available_slots, otherwise use venue capacity
            available_capacity = venue["capacity"]
            if "available_slots" in venue:
                if date_str in venue["available_slots"]:
                    if slot_time_str in venue["available_slots"][date_str]:
                        available_capacity = venue["available_slots"][date_str][slot_time_str]
            
            slots.append({
                "time": slot_time_str,
                "available_capacity": available_capacity,
                "total_capacity": venue["capacity"]
            })
            
            current_time += slot_duration
        
        return slots
        
    except ValueError as e:
        raise ValueError(f"Invalid date or time format: {str(e)}")


def validate_operating_hours(operating_hours):
    """Validate operating hours format"""
    if not isinstance(operating_hours, dict):
        return False
    
    valid_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    
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