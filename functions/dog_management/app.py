import json
import boto3
import uuid
import os
import decimal
from datetime import datetime, timezone, date
from botocore.exceptions import ClientError
from pydantic import ValidationError
import logging
import sys

sys.path.append("/opt/python")
from auth import require_auth, optional_auth, get_user_id_from_event
from models import (
    DogRequest,
    DogResponse,
    DogListResponse,
    ErrorResponse,
)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# DynamoDB resource will be initialized in lambda_handler


def lambda_handler(event, context):
    """
    Main Lambda handler for dog management operations
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
        dogs_table_name = os.environ.get("DOGS_TABLE")
        owners_table_name = os.environ.get("OWNERS_TABLE")

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
                return get_dog(dogs_table, path_parameters["id"], event)
            else:
                return list_dogs(dogs_table, event)
        elif http_method == "POST":
            return create_dog(dogs_table, owners_table, event)
        elif http_method == "PUT":
            return update_dog(dogs_table, path_parameters["id"], event)
        elif http_method == "DELETE":
            return delete_dog(dogs_table, path_parameters["id"], event)
        else:
            return create_response(405, {"error": "Method not allowed"})

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return create_response(500, {"error": "Internal server error"})


@require_auth
def get_dog(table, dog_id, event):
    """Get a specific dog by ID (owner verification)"""
    try:
        # Get user_id from authenticated claims
        user_id = get_user_id_from_event(event)

        if not user_id:
            return create_response(401, {"error": "Authentication required"})

        response = table.get_item(Key={"id": dog_id})

        if "Item" not in response:
            return create_response(404, {"error": "Dog not found"})

        dog = response["Item"]

        # Verify ownership
        if dog.get("owner_id") != user_id:
            return create_response(403, {"error": "Access denied - not your dog"})

        return create_response(200, dog)

    except ClientError as e:
        logger.error(f"Error getting dog: {str(e)}")
        return create_response(500, {"error": "Failed to get dog"})


@require_auth
def list_dogs(table, event):
    """List all dogs for authenticated user"""
    try:
        # Get user_id from authenticated claims
        user_id = get_user_id_from_event(event)

        if not user_id:
            return create_response(401, {"error": "Authentication required"})

        # Query using GSI with user_id
        from boto3.dynamodb.conditions import Key

        response = table.query(
            IndexName="owner-index", KeyConditionExpression=Key("owner_id").eq(user_id)
        )

        dogs = response.get("Items", [])

        return create_response(200, {"dogs": dogs, "count": len(dogs)})

    except ClientError as e:
        logger.error(f"Error listing dogs: {str(e)}")
        return create_response(500, {"error": "Failed to list dogs"})


@require_auth
def create_dog(dogs_table, owners_table, event):
    """Create a new dog for authenticated user"""
    try:
        # Get user_id from authenticated claims
        user_id = get_user_id_from_event(event)

        if not user_id:
            return create_response(401, {"error": "Authentication required"})

        # Parse request body
        body = json.loads(event.get("body", "{}"))

        # Validate with Pydantic model - replaces all manual validation!
        try:
            dog_request = DogRequest(**body)
        except ValidationError as e:
            logger.warning(f"Validation error: {e.errors()}")
            # Format Pydantic errors into a simple error message for backward compatibility
            error_messages = []
            for error in e.errors():
                field = error['loc'][0] if error['loc'] else 'field'
                msg = error['msg']
                error_messages.append(f"{field}: {msg}")
            return create_response(422, {"error": "; ".join(error_messages)})

        # Verify user profile exists
        owner_response = owners_table.get_item(Key={"user_id": user_id})
        if "Item" not in owner_response:
            return create_response(
                400, {"error": "Please complete profile registration first"}
            )

        # Check if birth date is in the future
        if dog_request.date_of_birth > date.today():
            return create_response(400, {"error": "Birth date cannot be in the future"})

        # Calculate age from date_of_birth
        today = datetime.now(timezone.utc).date()
        birth_date = dog_request.date_of_birth
        age_months = (today.year - birth_date.year) * 12 + (today.month - birth_date.month)

        if age_months < 12:
            calculated_age = f"{age_months} months" if age_months != 1 else "1 month"
        else:
            years = age_months // 12
            remaining_months = age_months % 12
            if remaining_months == 0:
                calculated_age = f"{years} year{'s' if years != 1 else ''}"
            else:
                calculated_age = f"{years} year{'s' if years != 1 else ''}, {remaining_months} month{'s' if remaining_months != 1 else ''}"

        # Create dog record
        dog_id = f"dog-{uuid.uuid4()}"
        now = datetime.now(timezone.utc).isoformat()

        dog_item = {
            "id": dog_id,
            "name": dog_request.name,
            "breed": dog_request.breed,
            "date_of_birth": dog_request.date_of_birth.isoformat(),
            "age": calculated_age,
            "size": dog_request.size.value,  # Enum value
            "vaccination_status": dog_request.vaccination_status.value,  # Enum value
            "microchipped": dog_request.microchipped,
            "special_needs": dog_request.special_needs,
            "medical_notes": dog_request.medical_notes,
            "behavior_notes": dog_request.behavior_notes,
            "favorite_activities": dog_request.favorite_activities,
            "owner_id": user_id,
            "created_at": now,
            "updated_at": now,
        }

        dogs_table.put_item(Item=dog_item)

        logger.info(f"Created dog: {dog_id} for user: {user_id}")
        return create_response(201, dog_item)

    except json.JSONDecodeError:
        return create_response(400, {"error": "Invalid JSON in request body"})
    except ClientError as e:
        logger.error(f"Error creating dog: {str(e)}")
        return create_response(500, {"error": "Failed to create dog"})


@require_auth
def update_dog(table, dog_id, event):
    """Update an existing dog (owner verification)"""
    try:
        # Get user_id from authenticated claims
        user_id = get_user_id_from_event(event)

        if not user_id:
            return create_response(401, {"error": "Authentication required"})

        # Parse request body
        body = json.loads(event.get("body", "{}"))

        # Check if dog exists and verify ownership
        existing_dog = table.get_item(Key={"id": dog_id})
        if "Item" not in existing_dog:
            return create_response(404, {"error": "Dog not found"})

        dog = existing_dog["Item"]
        if dog.get("owner_id") != user_id:
            return create_response(403, {"error": "Access denied - not your dog"})

        # Build update expression
        update_expression = "SET updated_at = :updated_at"
        expression_values = {":updated_at": datetime.now(timezone.utc).isoformat()}
        expression_names = {}

        # Update allowed fields
        allowed_fields = [
            "name",
            "breed",
            "age",
            "size",
            "vaccination_status",
            "special_needs",
            "medical_notes",
            "behavior_notes",
            "favorite_activities",
            "microchipped",
        ]
        for field in allowed_fields:
            if field in body:
                value = body[field]
                # Handle enum fields
                if field in ["size", "vaccination_status"]:
                    # Validate enum values
                    if field == "size":
                        valid_sizes = ["SMALL", "MEDIUM", "LARGE", "XLARGE"]
                        if value not in valid_sizes:
                            return create_response(400, {"error": f"Invalid size. Must be one of: {valid_sizes}"})
                    elif field == "vaccination_status":
                        valid_statuses = ["VACCINATED", "NOT_VACCINATED"]
                        if value not in valid_statuses:
                            return create_response(400, {"error": f"Invalid vaccination_status. Must be one of: {valid_statuses}"})

                if field == "name":
                    # Handle reserved keyword
                    update_expression += f", #name = :name"
                    expression_names["#name"] = "name"
                    expression_values[":name"] = value
                elif field == "size":
                    # Handle reserved keyword
                    update_expression += f", #size = :size"
                    expression_names["#size"] = "size"
                    expression_values[":size"] = value
                else:
                    update_expression += f", {field} = :{field}"
                    expression_values[f":{field}"] = value

        # Update the item
        kwargs = {
            "Key": {"id": dog_id},
            "UpdateExpression": update_expression,
            "ExpressionAttributeValues": expression_values,
            "ReturnValues": "ALL_NEW",
        }
        if expression_names:
            kwargs["ExpressionAttributeNames"] = expression_names

        response = table.update_item(**kwargs)

        logger.info(f"Updated dog: {dog_id}")
        return create_response(200, response["Attributes"])

    except json.JSONDecodeError:
        return create_response(400, {"error": "Invalid JSON in request body"})
    except ClientError as e:
        logger.error(f"Error updating dog: {str(e)}")
        return create_response(500, {"error": "Failed to update dog"})


@require_auth
def delete_dog(table, dog_id, event):
    """Delete a dog (owner verification)"""
    try:
        # Get user_id from authenticated claims
        user_id = get_user_id_from_event(event)

        if not user_id:
            return create_response(401, {"error": "Authentication required"})

        # Check if dog exists and verify ownership
        existing_dog = table.get_item(Key={"id": dog_id})
        if "Item" not in existing_dog:
            return create_response(404, {"error": "Dog not found"})

        dog = existing_dog["Item"]
        if dog.get("owner_id") != user_id:
            return create_response(403, {"error": "Access denied - not your dog"})

        # Delete the dog
        table.delete_item(Key={"id": dog_id})

        logger.info(f"Deleted dog: {dog_id} by user: {user_id}")
        return create_response(204, {})

    except ClientError as e:
        logger.error(f"Error deleting dog: {str(e)}")
        return create_response(500, {"error": "Failed to delete dog"})


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
