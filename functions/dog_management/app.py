import json
import boto3
import uuid
import os
import decimal
from datetime import datetime, timezone
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

        # Validate required fields (no longer need owner_id from body)
        required_fields = ["name", "breed", "age", "size"]
        for field in required_fields:
            if field not in body:
                return create_response(
                    400, {"error": f"Missing required field: {field}"}
                )

        # Verify user profile exists
        owner_response = owners_table.get_item(Key={"user_id": user_id})
        if "Item" not in owner_response:
            return create_response(
                400, {"error": "Please complete profile registration first"}
            )

        # Validate age
        if not isinstance(body["age"], int) or body["age"] < 0:
            return create_response(400, {"error": "Age must be positive integer"})

        # Validate size
        valid_sizes = ["small", "medium", "large"]
        if body["size"] not in valid_sizes:
            return create_response(
                400, {"error": f"Invalid size. Must be one of: {valid_sizes}"}
            )

        # Create dog record
        dog_id = f"dog-{uuid.uuid4()}"
        now = datetime.now(timezone.utc).isoformat()

        dog_item = {
            "id": dog_id,
            "name": body["name"],
            "breed": body["breed"],
            "age": int(body["age"]),
            "size": body["size"],
            "owner_id": user_id,  # Use authenticated user_id
            "vaccination_status": body.get("vaccination_status", "unknown"),
            "special_needs": body.get("special_needs", []),
            "emergency_contact": body.get("emergency_contact", ""),
            "created_at": now,
            "updated_at": now,
        }

        dogs_table.put_item(Item=dog_item)

        logger.info(f"Created dog: {dog_id} for user: {user_id}")
        return create_response(201, dog_item)

    except json.JSONDecodeError:
        return create_response(400, {"error": "Invalid JSON in request body"})
    except ValueError as e:
        return create_response(400, {"error": str(e)})
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
            "emergency_contact",
        ]
        for field in allowed_fields:
            if field in body:
                if field == "name":
                    # Handle reserved keyword
                    update_expression += f", #name = :name"
                    expression_names["#name"] = "name"
                    expression_values[":name"] = body[field]
                elif field == "size":
                    # Handle reserved keyword
                    update_expression += f", #size = :size"
                    expression_names["#size"] = "size"
                    expression_values[":size"] = body[field]
                else:
                    update_expression += f", {field} = :{field}"
                    expression_values[f":{field}"] = body[field]

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


# def create_response(status_code, body):
#     """Create a standardized API response"""
#     return {
#         "statusCode": status_code,
#         "headers": {
#             "Content-Type": "application/json",
#             "Access-Control-Allow-Origin": "*",
#             "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
#             "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
#         },
#         "body": json.dumps(body) if body else "",
#     }


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
