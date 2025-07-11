import json
import boto3
import uuid
import os
import decimal
from datetime import datetime, timezone
from botocore.exceptions import ClientError
import logging
import re
import sys

sys.path.append("/opt/python")
from auth import require_auth, optional_auth, get_user_id_from_event, is_user_verified

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# DynamoDB resource will be initialized in lambda_handler


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


@require_auth
def get_owner_profile(table, event):
    """Get owner profile by user claims (no PII stored)"""
    try:
        # Get user_id from authenticated claims
        user_id = get_user_id_from_event(event)

        if not user_id:
            return create_response(401, {"error": "Authentication required"})

        # Get user preferences/profile (non-PII data)
        response = table.get_item(Key={"user_id": user_id})

        if "Item" not in response:
            # Create basic profile if doesn't exist
            profile_data = {
                "user_id": user_id,
                "preferences": {"notifications": True, "marketing_emails": False},
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            table.put_item(Item=profile_data)
            return create_response(200, profile_data)

        profile_data = response["Item"]
        return create_response(200, profile_data)

    except ClientError as e:
        logger.error(f"Error getting owner profile: {str(e)}")
        return create_response(500, {"error": "Failed to get owner profile"})


@require_auth
def update_owner_profile(table, event):
    """Update owner profile (non-PII preferences only)"""
    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))

        # Get user_id from authenticated claims
        user_id = get_user_id_from_event(event)

        if not user_id:
            return create_response(401, {"error": "Authentication required"})

        # Check if profile exists
        existing_profile = table.get_item(Key={"user_id": user_id})

        # Build update expression
        update_expression = "SET updated_at = :updated_at"
        expression_values = {":updated_at": datetime.now(timezone.utc).isoformat()}

        # Update allowed fields (only non-PII preferences)
        allowed_fields = ["preferences", "notification_settings"]

        for field in allowed_fields:
            if field in body:
                update_expression += f", {field} = :{field}"
                expression_values[f":{field}"] = body[field]

        # If profile doesn't exist, create it
        if "Item" not in existing_profile:
            profile_data = {
                "user_id": user_id,
                "preferences": body.get(
                    "preferences", {"notifications": True, "marketing_emails": False}
                ),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            table.put_item(Item=profile_data)
            return create_response(200, profile_data)

        # Update existing profile
        response = table.update_item(
            Key={"user_id": user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ReturnValues="ALL_NEW",
        )

        logger.info(f"Updated owner profile: {user_id}")
        return create_response(200, response["Attributes"])

    except json.JSONDecodeError:
        return create_response(400, {"error": "Invalid JSON in request body"})
    except ClientError as e:
        logger.error(f"Error updating owner profile: {str(e)}")
        return create_response(500, {"error": "Failed to update owner profile"})


@require_auth
def register_owner(table, event):
    """Register owner profile (claims-based, no PII storage)"""
    try:
        # Get user_id from authenticated claims
        user_id = get_user_id_from_event(event)

        if not user_id:
            return create_response(401, {"error": "Authentication required"})

        # Verify user's email is verified
        if not is_user_verified(event):
            return create_response(400, {"error": "Email verification required"})

        # Parse request body for preferences
        body = json.loads(event.get("body", "{}"))

        # Check if profile already exists
        existing_profile = table.get_item(Key={"user_id": user_id})

        if "Item" in existing_profile:
            return create_response(400, {"error": "Profile already exists"})

        # Create owner profile record (no PII)
        now = datetime.now(timezone.utc).isoformat()

        owner_profile = {
            "user_id": user_id,  # Google user ID (not PII)
            "preferences": body.get(
                "preferences",
                {
                    "notifications": True,
                    "marketing_emails": False,
                    "preferred_communication": "email",
                },
            ),
            "registration_complete": True,
            "created_at": now,
            "updated_at": now,
        }

        table.put_item(Item=owner_profile)

        logger.info(f"Created owner profile: {user_id}")
        return create_response(
            201,
            {
                "message": "Profile created successfully",
                "user_id": user_id,
                "preferences": owner_profile["preferences"],
            },
        )

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
