import json
import boto3
import uuid
import os
import decimal
from datetime import datetime, timezone
from botocore.exceptions import ClientError
import logging
import re

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# DynamoDB resource will be initialized in lambda_handler
dynamodb = None


def lambda_handler(event, context):
    """
    Main Lambda handler for owner management operations
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
        owners_table_name = os.environ.get("OWNERS_TABLE")
        owners_table = dynamodb.Table(owners_table_name)

        # Log the incoming event
        logger.info(f"Received event: {json.dumps(event)}")

        # Get HTTP method and path
        http_method = event.get("httpMethod")
        path = event.get("path", "")
        path_parameters = event.get("pathParameters") or {}

        # Route to appropriate handler
        if path.endswith("/profile"):
            if http_method == "GET":
                return get_owner_profile(owners_table, event)
            elif http_method == "PUT":
                return update_owner_profile(owners_table, event)
        elif path.endswith("/register"):
            if http_method == "POST":
                return register_owner(owners_table, event)
        else:
            return create_response(404, {"error": "Endpoint not found"})

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return create_response(500, {"error": "Internal server error"})


def get_owner_profile(table, event):
    """Get owner profile by ID"""
    try:
        # In a real app, you'd get owner_id from JWT token
        # For now, we'll use query parameter
        query_params = event.get("queryStringParameters") or {}
        owner_id = query_params.get("owner_id")

        if not owner_id:
            return create_response(400, {"error": "owner_id is required"})

        response = table.get_item(Key={"id": owner_id})

        if "Item" not in response:
            return create_response(404, {"error": "Owner not found"})

        # Remove sensitive information if needed
        owner_data = response["Item"]
        return create_response(200, owner_data)

    except ClientError as e:
        logger.error(f"Error getting owner: {str(e)}")
        return create_response(500, {"error": "Failed to get owner"})


def update_owner_profile(table, event):
    """Update owner profile"""
    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))

        # In a real app, you'd get owner_id from JWT token
        query_params = event.get("queryStringParameters") or {}
        owner_id = query_params.get("owner_id")

        if not owner_id:
            return create_response(400, {"error": "owner_id is required"})

        # Check if owner exists
        existing_owner = table.get_item(Key={"id": owner_id})
        if "Item" not in existing_owner:
            return create_response(404, {"error": "Owner not found"})

        # Build update expression
        update_expression = "SET updated_at = :updated_at"
        expression_values = {":updated_at": datetime.now(timezone.utc).isoformat()}

        # Update allowed fields
        allowed_fields = ["name", "phone", "address"]
        expression_names = {}
        for field in allowed_fields:
            if field in body:
                if field == "name":
                    # 'name' is a reserved keyword in DynamoDB
                    update_expression += f", #name = :name"
                    expression_names["#name"] = "name"
                    expression_values[":name"] = body[field]
                else:
                    update_expression += f", {field} = :{field}"
                    expression_values[f":{field}"] = body[field]

        # Update the item
        update_params = {
            "Key": {"id": owner_id},
            "UpdateExpression": update_expression,
            "ExpressionAttributeValues": expression_values,
            "ReturnValues": "ALL_NEW",
        }
        if expression_names:
            update_params["ExpressionAttributeNames"] = expression_names

        response = table.update_item(**update_params)

        logger.info(f"Updated owner: {owner_id}")
        return create_response(200, response["Attributes"])

    except json.JSONDecodeError:
        return create_response(400, {"error": "Invalid JSON in request body"})
    except ClientError as e:
        logger.error(f"Error updating owner: {str(e)}")
        return create_response(500, {"error": "Failed to update owner"})


def register_owner(table, event):
    """Register a new owner"""
    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))

        # Validate required fields
        required_fields = ["name", "email", "phone"]
        for field in required_fields:
            if field not in body:
                return create_response(
                    400, {"error": f"Missing required field: {field}"}
                )

        # Validate email format
        if not validate_email(body["email"]):
            return create_response(400, {"error": "Invalid email format"})

        # Check if email already exists
        from boto3.dynamodb.conditions import Key

        existing_owner = table.query(
            IndexName="email-index",
            KeyConditionExpression=Key("email").eq(body["email"]),
        )

        if existing_owner.get("Items"):
            return create_response(400, {"error": "Email already registered"})

        # Create owner record
        owner_id = f"owner-{uuid.uuid4()}"
        now = datetime.now(timezone.utc).isoformat()

        owner_item = {
            "id": owner_id,
            "name": body["name"],
            "email": body["email"],
            "phone": body["phone"],
            "address": body.get("address", {}),
            "dogs": [],
            "created_at": now,
            "updated_at": now,
        }

        table.put_item(Item=owner_item)

        logger.info(f"Created owner: {owner_id}")
        return create_response(201, owner_item)

    except json.JSONDecodeError:
        return create_response(400, {"error": "Invalid JSON in request body"})
    except ClientError as e:
        logger.error(f"Error registering owner: {str(e)}")
        return create_response(500, {"error": "Failed to register owner"})


def validate_email(email):
    """Validate email format"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


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
