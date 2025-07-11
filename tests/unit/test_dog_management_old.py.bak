import json
import boto3
from moto import mock_aws
from unittest.mock import patch
import sys
import os
import pytest
from decimal import Decimal

# Add the functions directory to the path
dog_management_dir = os.path.join(
    os.path.dirname(__file__), "../../functions/dog_management"
)
sys.path.insert(0, dog_management_dir)

# Remove any existing app module to avoid conflicts
if "app" in sys.modules:
    del sys.modules["app"]

from app import lambda_handler


def test_create_dog(mock_env, dynamodb_setup):
    """Test creating a new dog"""
    # Create a test owner
    owners_table = dynamodb_setup.Table("owners-test")
    owners_table.put_item(Item={"id": "owner-123", "name": "Test Owner"})

    # Test event
    event = {
        "httpMethod": "POST",
        "path": "/dogs",
        "body": json.dumps(
            {
                "name": "Buddy",
                "breed": "Golden Retriever",
                "age": 3,
                "size": "large",
                "owner_id": "owner-123",
                "vaccination_status": "up-to-date",
                "special_needs": ["medication"],
                "emergency_contact": "+1234567890",
            }
        ),
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert body["name"] == "Buddy"
    assert body["breed"] == "Golden Retriever"
    assert body["age"] == 3
    assert body["size"] == "large"
    assert body["owner_id"] == "owner-123"
    assert "id" in body


def test_create_dog_invalid_owner(mock_env, dynamodb_setup):
    """Test creating a dog with invalid owner"""
    event = {
        "httpMethod": "POST",
        "path": "/dogs",
        "body": json.dumps(
            {
                "name": "Buddy",
                "breed": "Golden Retriever",
                "age": 3,
                "size": "large",
                "owner_id": "invalid-owner",
            }
        ),
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "Owner not found" in body["error"]


def test_create_dog_missing_fields(mock_env, dynamodb_setup):
    """Test creating a dog with missing required fields"""
    event = {
        "httpMethod": "POST",
        "path": "/dogs",
        "body": json.dumps(
            {
                "name": "Buddy",
                # Missing required fields
            }
        ),
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Missing required field" in body["error"]


def test_get_dog(mock_env, dynamodb_setup):
    """Test getting a specific dog"""
    # Create test dog
    dogs_table = dynamodb_setup.Table("dogs-test")
    dogs_table.put_item(
        Item={
            "id": "dog-123",
            "name": "Buddy",
            "breed": "Golden Retriever",
            "age": 3,
            "size": "large",
            "owner_id": "owner-123",
        }
    )

    event = {
        "httpMethod": "GET",
        "path": "/dogs/dog-123",
        "pathParameters": {"id": "dog-123"},
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["id"] == "dog-123"
    assert body["name"] == "Buddy"


def test_get_dog_not_found(mock_env, dynamodb_setup):
    """Test getting a non-existent dog"""
    event = {
        "httpMethod": "GET",
        "path": "/dogs/non-existent",
        "pathParameters": {"id": "non-existent"},
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "Dog not found" in body["error"]


def test_list_dogs(mock_env, dynamodb_setup):
    """Test listing dogs for an owner"""
    # Create test dogs
    dogs_table = dynamodb_setup.Table("dogs-test")
    dogs_table.put_item(
        Item={
            "id": "dog-123",
            "name": "Buddy",
            "breed": "Golden Retriever",
            "owner_id": "owner-123",
        }
    )
    dogs_table.put_item(
        Item={
            "id": "dog-456",
            "name": "Max",
            "breed": "German Shepherd",
            "owner_id": "owner-123",
        }
    )

    event = {
        "httpMethod": "GET",
        "path": "/dogs",
        "queryStringParameters": {"owner_id": "owner-123"},
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "dogs" in body
    assert "count" in body
    assert body["count"] == 2
    assert len(body["dogs"]) == 2


def test_list_dogs_missing_owner_id(mock_env, dynamodb_setup):
    """Test listing dogs without owner_id"""
    event = {
        "httpMethod": "GET",
        "path": "/dogs",
        "queryStringParameters": None,
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "owner_id is required" in body["error"]


def test_update_dog(mock_env, dynamodb_setup):
    """Test updating a dog"""
    # Create test dog
    dogs_table = dynamodb_setup.Table("dogs-test")
    dogs_table.put_item(
        Item={
            "id": "dog-123",
            "name": "Buddy",
            "breed": "Golden Retriever",
            "age": 3,
            "size": "large",
            "owner_id": "owner-123",
        }
    )

    event = {
        "httpMethod": "PUT",
        "path": "/dogs/dog-123",
        "pathParameters": {"id": "dog-123"},
        "body": json.dumps({"name": "Buddy Jr.", "age": 4}),
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["name"] == "Buddy Jr."
    assert body["age"] == 4


def test_update_dog_not_found(mock_env, dynamodb_setup):
    """Test updating a non-existent dog"""
    event = {
        "httpMethod": "PUT",
        "path": "/dogs/non-existent",
        "pathParameters": {"id": "non-existent"},
        "body": json.dumps({"name": "Updated Name"}),
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "Dog not found" in body["error"]


def test_delete_dog(mock_env, dynamodb_setup):
    """Test deleting a dog"""
    # Create test dog
    dogs_table = dynamodb_setup.Table("dogs-test")
    dogs_table.put_item(
        Item={
            "id": "dog-123",
            "name": "Buddy",
            "breed": "Golden Retriever",
            "age": 3,
            "size": "large",
            "owner_id": "owner-123",
        }
    )

    event = {
        "httpMethod": "DELETE",
        "path": "/dogs/dog-123",
        "pathParameters": {"id": "dog-123"},
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 204
    assert response["body"] == ""


def test_delete_dog_not_found(mock_env, dynamodb_setup):
    """Test deleting a non-existent dog"""
    event = {
        "httpMethod": "DELETE",
        "path": "/dogs/non-existent",
        "pathParameters": {"id": "non-existent"},
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "Dog not found" in body["error"]


def test_invalid_json(mock_env, dynamodb_setup):
    """Test handling invalid JSON"""
    event = {
        "httpMethod": "POST",
        "path": "/dogs",
        "body": "invalid json",
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid JSON" in body["error"]


def test_invalid_http_method(mock_env, dynamodb_setup):
    """Test handling invalid HTTP method"""
    event = {
        "httpMethod": "PATCH",
        "path": "/dogs/dog-123",
        "pathParameters": {"id": "dog-123"},
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 405
    body = json.loads(response["body"])
    assert "Method not allowed" in body["error"]


def test_invalid_size(mock_env, dynamodb_setup):
    """Test creating a dog with invalid size"""
    # Create a test owner
    owners_table = dynamodb_setup.Table("owners-test")
    owners_table.put_item(Item={"id": "owner-123", "name": "Test Owner"})

    event = {
        "httpMethod": "POST",
        "path": "/dogs",
        "body": json.dumps(
            {
                "name": "Buddy",
                "breed": "Golden Retriever",
                "age": 3,
                "size": "invalid-size",
                "owner_id": "owner-123",
            }
        ),
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid size" in body["error"]


def test_invalid_age(mock_env, dynamodb_setup):
    """Test creating a dog with invalid age"""
    # Create a test owner
    owners_table = dynamodb_setup.Table("owners-test")
    owners_table.put_item(Item={"id": "owner-123", "name": "Test Owner"})

    event = {
        "httpMethod": "POST",
        "path": "/dogs",
        "body": json.dumps(
            {
                "name": "Buddy",
                "breed": "Golden Retriever",
                "age": -1,
                "size": "large",
                "owner_id": "owner-123",
            }
        ),
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Age must be positive integer" in body["error"]
