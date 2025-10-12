import json
import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from datetime import datetime, date, timedelta
from decimal import Decimal
from botocore.exceptions import ClientError

# Add the functions directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "functions"))

from slot_management.app import (
    lambda_handler,
    batch_generate_slots,
    query_availability,
    get_venue_slots_range,
    generate_slots_for_date,
    create_response
)


class TestSlotManagement:
    """Test suite for slot management functionality"""

    @pytest.fixture
    def mock_slots_table(self):
        return MagicMock()

    @pytest.fixture
    def mock_venues_table(self):
        return MagicMock()

    @pytest.fixture
    def sample_venue(self):
        return {
            "id": "venue-123",
            "name": "Test Venue",
            "capacity": 20,
            "slot_duration": 60,
            "operating_hours": {
                "monday": {"open": True, "start": "09:00", "end": "17:00"},
                "tuesday": {"open": True, "start": "09:00", "end": "17:00"},
                "wednesday": {"open": True, "start": "09:00", "end": "17:00"},
                "thursday": {"open": True, "start": "09:00", "end": "17:00"},
                "friday": {"open": True, "start": "09:00", "end": "17:00"},
                "saturday": {"open": True, "start": "10:00", "end": "16:00"},
                "sunday": {"open": False}
            }
        }

    def test_generate_slots_for_date(self, sample_venue):
        """Test slot generation for a specific date"""
        slots = generate_slots_for_date(sample_venue, "2024-01-01")  # Monday

        assert len(slots) == 8  # 09:00-17:00 = 8 hours
        assert slots[0]["time"] == "09:00"
        assert slots[-1]["time"] == "16:00"
        assert all(slot["available_capacity"] == 20 for slot in slots)

    def test_generate_slots_closed_day(self, sample_venue):
        """Test slot generation for closed day"""
        slots = generate_slots_for_date(sample_venue, "2024-01-07")  # Sunday

        assert len(slots) == 0

    def test_batch_generate_slots_success(self, mock_slots_table, mock_venues_table, sample_venue):
        """Test successful batch slot generation"""
        mock_venues_table.get_item.return_value = {"Item": sample_venue}

        # Mock batch writer
        batch_writer = MagicMock()
        mock_slots_table.batch_writer.return_value.__enter__.return_value = batch_writer

        event = {
            "httpMethod": "POST",
            "path": "/slots/batch-generate",
            "body": json.dumps({
                "venue_id": "venue-123",
                "start_date": "2024-01-01",
                "end_date": "2024-01-03"
            })
        }

        response = batch_generate_slots(mock_slots_table, mock_venues_table, event)

        assert response["statusCode"] == 201
        body = json.loads(response["body"])
        assert body["venue_id"] == "venue-123"
        assert "Slots generated successfully" in body["message"]

    def test_query_availability_success(self, mock_slots_table):
        """Test querying availability across venues"""
        mock_slots_table.query.return_value = {
            "Items": [
                {
                    "venue_id": "venue-1",
                    "slot_time": "09:00",
                    "available_capacity": 5,
                    "total_capacity": 20,
                    "date": "2024-01-01"
                },
                {
                    "venue_id": "venue-2",
                    "slot_time": "09:00",
                    "available_capacity": 10,
                    "total_capacity": 15,
                    "date": "2024-01-01"
                }
            ]
        }

        event = {
            "httpMethod": "GET",
            "path": "/slots/availability",
            "queryStringParameters": {"date": "2024-01-01"}
        }

        response = query_availability(mock_slots_table, event)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["date"] == "2024-01-01"
        assert "venue-1" in body["venues_with_availability"]
        assert "venue-2" in body["venues_with_availability"]

    def test_query_availability_missing_date(self, mock_slots_table):
        """Test availability query without date parameter"""
        event = {
            "httpMethod": "GET",
            "path": "/slots/availability",
            "queryStringParameters": None
        }

        response = query_availability(mock_slots_table, event)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "Date parameter required" in body["error"]

    def test_get_venue_slots_range(self, mock_slots_table):
        """Test getting venue slots for date range"""
        mock_slots_table.query.return_value = {
            "Items": [
                {"venue_date": "venue-123#2024-01-01", "slot_time": "09:00", "available_capacity": 20},
                {"venue_date": "venue-123#2024-01-01", "slot_time": "10:00", "available_capacity": 15}
            ]
        }

        event = {
            "httpMethod": "GET",
            "path": "/slots/venue/venue-123",
            "pathParameters": {"venue_id": "venue-123"},
            "queryStringParameters": {"start_date": "2024-01-01", "end_date": "2024-01-01"}
        }

        response = get_venue_slots_range(mock_slots_table, "venue-123", event)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["venue_id"] == "venue-123"
        assert "2024-01-01" in body["slots"]

    def test_create_response_decimal_serialization(self):
        """Test response creation with Decimal values"""
        response = create_response(200, {"capacity": Decimal("20.5")})

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["capacity"] == 20.5

    def test_batch_generate_missing_fields(self, mock_slots_table, mock_venues_table):
        """Test batch generation with missing required fields"""
        event = {
            "httpMethod": "POST",
            "path": "/slots/batch-generate",
            "body": json.dumps({"venue_id": "venue-123"})  # Missing dates
        }

        response = batch_generate_slots(mock_slots_table, mock_venues_table, event)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "Missing required fields" in body["error"]

    def test_batch_generate_venue_not_found(self, mock_slots_table, mock_venues_table):
        """Test batch generation with non-existent venue"""
        mock_venues_table.get_item.return_value = {}  # Venue not found

        event = {
            "httpMethod": "POST",
            "path": "/slots/batch-generate",
            "body": json.dumps({
                "venue_id": "non-existent",
                "start_date": "2024-01-01",
                "end_date": "2024-01-03"
            })
        }

        response = batch_generate_slots(mock_slots_table, mock_venues_table, event)

        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert "Venue not found" in body["error"]

    def test_batch_generate_invalid_date_order(self, mock_slots_table, mock_venues_table, sample_venue):
        """Test batch generation with start_date after end_date"""
        mock_venues_table.get_item.return_value = {"Item": sample_venue}

        event = {
            "httpMethod": "POST",
            "path": "/slots/batch-generate",
            "body": json.dumps({
                "venue_id": "venue-123",
                "start_date": "2024-01-10",
                "end_date": "2024-01-01"  # Before start_date
            })
        }

        response = batch_generate_slots(mock_slots_table, mock_venues_table, event)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "start_date must be before or equal to end_date" in body["error"]

    def test_batch_generate_invalid_date_format(self, mock_slots_table, mock_venues_table, sample_venue):
        """Test batch generation with invalid date format"""
        mock_venues_table.get_item.return_value = {"Item": sample_venue}

        event = {
            "httpMethod": "POST",
            "path": "/slots/batch-generate",
            "body": json.dumps({
                "venue_id": "venue-123",
                "start_date": "invalid-date",
                "end_date": "2024-01-03"
            })
        }

        response = batch_generate_slots(mock_slots_table, mock_venues_table, event)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "Invalid date format" in body["error"]

    def test_query_availability_invalid_date_format(self, mock_slots_table):
        """Test availability query with invalid date format"""
        event = {
            "httpMethod": "GET",
            "path": "/slots/availability",
            "queryStringParameters": {"date": "not-a-date"}
        }

        response = query_availability(mock_slots_table, event)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "Invalid date format" in body["error"]

    def test_get_venue_slots_range_missing_venue_id(self, mock_slots_table):
        """Test getting venue slots without venue_id"""
        event = {
            "httpMethod": "GET",
            "path": "/slots/venue/",
            "queryStringParameters": {"start_date": "2024-01-01"}
        }

        response = get_venue_slots_range(mock_slots_table, None, event)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "venue_id is required" in body["error"]

    def test_get_venue_slots_range_missing_start_date(self, mock_slots_table):
        """Test getting venue slots without start_date"""
        event = {
            "httpMethod": "GET",
            "path": "/slots/venue/venue-123",
            "queryStringParameters": {}
        }

        response = get_venue_slots_range(mock_slots_table, "venue-123", event)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "start_date parameter required" in body["error"]

    def test_lambda_handler_endpoint_not_found(self):
        """Test lambda handler with unknown endpoint"""
        event = {
            "httpMethod": "DELETE",
            "path": "/slots/unknown"
        }

        with patch.dict(os.environ, {
            "SLOTS_TABLE": "slots-test",
            "VENUES_TABLE": "venues-test",
            "AWS_DEFAULT_REGION": "us-east-1"
        }):
            response = lambda_handler(event, None)

        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert "Endpoint not found" in body["error"]

    def test_batch_generate_client_error(self, mock_slots_table, mock_venues_table, sample_venue):
        """Test batch generation with DynamoDB client error"""
        mock_venues_table.get_item.return_value = {"Item": sample_venue}
        mock_slots_table.batch_writer.side_effect = ClientError(
            {"Error": {"Code": "InternalServerError", "Message": "Test error"}},
            "BatchWriteItem"
        )

        event = {
            "httpMethod": "POST",
            "path": "/slots/batch-generate",
            "body": json.dumps({
                "venue_id": "venue-123",
                "start_date": "2024-01-01",
                "end_date": "2024-01-01"
            })
        }

        response = batch_generate_slots(mock_slots_table, mock_venues_table, event)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "Failed to generate slots" in body["error"]

    def test_query_availability_client_error(self, mock_slots_table):
        """Test availability query with DynamoDB client error"""
        mock_slots_table.query.side_effect = ClientError(
            {"Error": {"Code": "InternalServerError", "Message": "Test error"}},
            "Query"
        )

        event = {
            "httpMethod": "GET",
            "path": "/slots/availability",
            "queryStringParameters": {"date": "2024-01-01"}
        }

        response = query_availability(mock_slots_table, event)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "Failed to query availability" in body["error"]
