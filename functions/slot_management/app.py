import json
import boto3
import os
import decimal
from datetime import datetime, timezone, timedelta, date
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from pydantic import ValidationError
import logging
import sys

sys.path.append("/opt/python")
from models import (
    SlotBatchGenerateRequest,
    SlotBatchGenerateResponse,
    SlotAvailabilityResponse,
    ErrorResponse,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Lambda handler for slot management operations"""
    try:
        # Initialize DynamoDB
        dynamodb_kwargs = {"region_name": os.environ.get("AWS_DEFAULT_REGION", "us-east-1")}
        if os.environ.get("AWS_SAM_LOCAL"):
            dynamodb_kwargs["endpoint_url"] = "http://dynamodb-local:8000"
        dynamodb = boto3.resource("dynamodb", **dynamodb_kwargs)

        slots_table = dynamodb.Table(os.environ.get("SLOTS_TABLE"))
        venues_table = dynamodb.Table(os.environ.get("VENUES_TABLE"))

        http_method = event.get("httpMethod")
        path = event.get("path", "")

        # Route handlers
        if "/slots/batch-generate" in path and http_method == "POST":
            return batch_generate_slots(slots_table, venues_table, event)
        elif "/slots/availability" in path and http_method == "GET":
            return query_availability(slots_table, event)
        elif "/slots/venue/" in path and http_method == "GET":
            venue_id = event.get("pathParameters", {}).get("venue_id")
            return get_venue_slots_range(slots_table, venue_id, event)
        else:
            return create_response(404, {"error": "Endpoint not found"})

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return create_response(500, {"error": "Internal server error"})


def batch_generate_slots(slots_table, venues_table, event):
    """
    Generate slots for a venue for a date range
    POST /slots/batch-generate
    Body: {venue_id, start_date, end_date}
    """
    try:
        body = json.loads(event.get("body", "{}"))

        # Validate with Pydantic model
        try:
            slot_request = SlotBatchGenerateRequest(**body)
        except ValidationError as e:
            logger.warning(f"Validation error: {e.errors()}")
            # Format Pydantic errors into a simple error message for backward compatibility
            error_messages = []
            for error in e.errors():
                field = error['loc'][0] if error['loc'] else 'field'
                msg = error['msg']
                error_messages.append(f"{field}: {msg}")
            return create_response(422, {"error": "; ".join(error_messages)})

        venue_id = slot_request.venue_id
        # Pydantic already parsed these as date objects
        start_date = slot_request.start_date
        end_date = slot_request.end_date

        # Get venue details
        venue_response = venues_table.get_item(Key={"id": venue_id})
        if "Item" not in venue_response:
            return create_response(404, {"error": "Venue not found"})

        venue = venue_response["Item"]

        if start_date > end_date:
            return create_response(400, {"error": "start_date must be before or equal to end_date"})

        # Generate slots for date range
        slots_created = 0
        current_date = start_date

        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            day_slots = generate_slots_for_date(venue, date_str)

            # Batch write slots (DynamoDB batch limit is 25)
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
                        "ttl": int(datetime.combine(current_date + timedelta(days=90), datetime.min.time()).replace(tzinfo=timezone.utc).timestamp())
                    })
                    slots_created += 1

            current_date += timedelta(days=1)

        logger.info(f"Generated {slots_created} slots for venue {venue_id}")
        return create_response(201, {
            "message": "Slots generated successfully",
            "venue_id": venue_id,
            "date_range": {"start": start_date.strftime("%Y-%m-%d"), "end": end_date.strftime("%Y-%m-%d")},
            "slots_created": slots_created
        })

    except ValueError as e:
        return create_response(400, {"error": f"Invalid date format: {str(e)}"})
    except ClientError as e:
        logger.error(f"DynamoDB error: {str(e)}")
        return create_response(500, {"error": "Failed to generate slots"})


def query_availability(slots_table, event):
    """
    Query slots across multiple venues by date
    GET /slots/availability?date=2024-01-01&service_type=daycare
    """
    try:
        params = event.get("queryStringParameters") or {}
        date_str = params.get("date")

        if not date_str:
            return create_response(400, {"error": "Date parameter required"})

        # Validate date format
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return create_response(400, {"error": "Invalid date format. Use YYYY-MM-DD"})

        # Query GSI: date-venue-index
        response = slots_table.query(
            IndexName="date-venue-index",
            KeyConditionExpression=Key("date").eq(date_str),
            FilterExpression="available_capacity > :zero",
            ExpressionAttributeValues={":zero": 0}
        )

        slots = response.get("Items", [])

        # Group by venue
        venues_availability = {}
        for slot in slots:
            venue_id = slot["venue_id"]
            if venue_id not in venues_availability:
                venues_availability[venue_id] = []
            venues_availability[venue_id].append({
                "time": slot["slot_time"],
                "available": slot["available_capacity"],
                "total": slot["total_capacity"]
            })

        return create_response(200, {
            "date": date_str,
            "venues_with_availability": venues_availability,
            "total_venues": len(venues_availability)
        })

    except ClientError as e:
        logger.error(f"Query error: {str(e)}")
        return create_response(500, {"error": "Failed to query availability"})


def get_venue_slots_range(slots_table, venue_id, event):
    """
    Get all slots for a venue in a date range
    GET /slots/venue/{venue_id}?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
    """
    try:
        if not venue_id:
            return create_response(400, {"error": "venue_id is required"})

        params = event.get("queryStringParameters") or {}
        start_date = params.get("start_date")
        end_date = params.get("end_date", start_date)

        if not start_date:
            return create_response(400, {"error": "start_date parameter required"})

        # Query by venue_date composite key
        slots_by_date = {}
        current = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()

        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            response = slots_table.query(
                KeyConditionExpression=Key("venue_date").eq(f"{venue_id}#{date_str}")
            )
            slots_by_date[date_str] = response.get("Items", [])
            current += timedelta(days=1)

        return create_response(200, {
            "venue_id": venue_id,
            "date_range": {"start": start_date, "end": end_date},
            "slots": slots_by_date
        })

    except ValueError as e:
        return create_response(400, {"error": f"Invalid date format: {str(e)}"})
    except ClientError as e:
        logger.error(f"Query error: {str(e)}")
        return create_response(500, {"error": "Failed to get slots"})


def generate_slots_for_date(venue, date_str):
    """Generate slot data for a specific date based on venue operating hours"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        day_of_week = date_obj.strftime("%A").lower()

        operating_hours = venue.get("operating_hours", {})
        if day_of_week not in operating_hours:
            return []

        day_hours = operating_hours[day_of_week]
        if not day_hours.get("open", True):
            return []

        # Parse times
        start_time = datetime.strptime(day_hours["start"], "%H:%M").time()
        end_time = datetime.strptime(day_hours["end"], "%H:%M").time()
        slot_duration = timedelta(minutes=int(venue.get("slot_duration", 60)))

        # Generate slots
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

    except (ValueError, KeyError) as e:
        logger.error(f"Error generating slots for {date_str}: {str(e)}")
        return []


def create_response(status_code, body):
    """Create standardized API response"""
    def serializer(o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,Authorization"
        },
        "body": json.dumps(body, default=serializer)
    }
