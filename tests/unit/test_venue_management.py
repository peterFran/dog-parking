import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

# Import the function under test
from functions.venue_management.app import (
    lambda_handler,
    create_venue,
    get_venue,
    list_venues,
    update_venue,
    delete_venue,
    get_venue_slots,
    update_venue_slots,
    validate_operating_hours,
    generate_slots_for_date,
    create_response,
)


class TestVenueManagement:
    """Test suite for venue management functionality"""

    @pytest.fixture
    def mock_table(self):
        """Create a mock DynamoDB table"""
        table = MagicMock()
        return table

    @pytest.fixture
    def sample_venue_data(self):
        """Sample venue data for testing"""
        return {
            "name": "Downtown Dog Care",
            "address": {
                "street": "123 Main St",
                "city": "New York",
                "state": "NY",
                "zip": "10001"
            },
            "capacity": 20,
            "operating_hours": {
                "monday": {"open": True, "start": "08:00", "end": "18:00"},
                "tuesday": {"open": True, "start": "08:00", "end": "18:00"},
                "wednesday": {"open": True, "start": "08:00", "end": "18:00"},
                "thursday": {"open": True, "start": "08:00", "end": "18:00"},
                "friday": {"open": True, "start": "08:00", "end": "18:00"},
                "saturday": {"open": True, "start": "09:00", "end": "17:00"},
                "sunday": {"open": False}
            },
            "services": ["daycare", "boarding", "grooming"],
            "slot_duration": 60
        }

    def test_create_venue_success(self, mock_table, sample_venue_data):
        """Test successful venue creation"""
        mock_table.put_item.return_value = None
        
        event = {
            "body": json.dumps(sample_venue_data),
            "httpMethod": "POST"
        }
        
        response = create_venue(mock_table, event)
        
        assert response["statusCode"] == 201
        body = json.loads(response["body"])
        assert body["name"] == sample_venue_data["name"]
        assert body["capacity"] == sample_venue_data["capacity"]
        assert "id" in body
        assert body["id"].startswith("venue-")
        mock_table.put_item.assert_called_once()

    def test_create_venue_missing_required_fields(self, mock_table):
        """Test venue creation with missing required fields"""
        event = {
            "body": json.dumps({"name": "Test Venue"}),
            "httpMethod": "POST"
        }
        
        response = create_venue(mock_table, event)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "Missing required field" in body["error"]

    def test_create_venue_invalid_capacity(self, mock_table, sample_venue_data):
        """Test venue creation with invalid capacity"""
        sample_venue_data["capacity"] = -5
        
        event = {
            "body": json.dumps(sample_venue_data),
            "httpMethod": "POST"
        }
        
        response = create_venue(mock_table, event)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "positive integer" in body["error"]

    def test_get_venue_success(self, mock_table):
        """Test successful venue retrieval"""
        venue_id = "venue-123"
        venue_data = {
            "id": venue_id,
            "name": "Test Venue",
            "capacity": 15
        }
        
        mock_table.get_item.return_value = {"Item": venue_data}
        
        response = get_venue(mock_table, venue_id)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["id"] == venue_id
        assert body["name"] == "Test Venue"

    def test_get_venue_not_found(self, mock_table):
        """Test venue retrieval when venue doesn't exist"""
        mock_table.get_item.return_value = {}
        
        response = get_venue(mock_table, "nonexistent-venue")
        
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert "not found" in body["error"]

    def test_list_venues_success(self, mock_table):
        """Test successful venue listing"""
        venues = [
            {"id": "venue-1", "name": "Venue 1"},
            {"id": "venue-2", "name": "Venue 2"}
        ]
        mock_table.scan.return_value = {"Items": venues}
        
        event = {"queryStringParameters": None}
        response = list_venues(mock_table, event)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert len(body["venues"]) == 2
        assert body["count"] == 2

    def test_update_venue_success(self, mock_table):
        """Test successful venue update"""
        venue_id = "venue-123"
        existing_venue = {"id": venue_id, "name": "Old Name"}
        updated_venue = {"id": venue_id, "name": "New Name"}
        
        mock_table.get_item.return_value = {"Item": existing_venue}
        mock_table.update_item.return_value = {"Attributes": updated_venue}
        
        event = {
            "body": json.dumps({"name": "New Name"}),
            "httpMethod": "PUT"
        }
        
        response = update_venue(mock_table, venue_id, event)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["name"] == "New Name"

    def test_update_venue_not_found(self, mock_table):
        """Test venue update when venue doesn't exist"""
        mock_table.get_item.return_value = {}
        
        event = {
            "body": json.dumps({"name": "New Name"}),
            "httpMethod": "PUT"
        }
        
        response = update_venue(mock_table, "nonexistent-venue", event)
        
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert "not found" in body["error"]

    def test_delete_venue_success(self, mock_table):
        """Test successful venue deletion"""
        venue_id = "venue-123"
        existing_venue = {"id": venue_id, "name": "Test Venue"}
        
        mock_table.get_item.return_value = {"Item": existing_venue}
        mock_table.delete_item.return_value = None
        
        response = delete_venue(mock_table, venue_id)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "deleted successfully" in body["message"]

    def test_validate_operating_hours_valid(self):
        """Test valid operating hours validation"""
        operating_hours = {
            "monday": {"open": True, "start": "08:00", "end": "18:00"},
            "tuesday": {"open": False}
        }
        
        assert validate_operating_hours(operating_hours) is True

    def test_validate_operating_hours_invalid_day(self):
        """Test invalid day in operating hours"""
        operating_hours = {
            "invalid_day": {"open": True, "start": "08:00", "end": "18:00"}
        }
        
        assert validate_operating_hours(operating_hours) is False

    def test_validate_operating_hours_invalid_time_format(self):
        """Test invalid time format in operating hours"""
        operating_hours = {
            "monday": {"open": True, "start": "8:00", "end": "18:00"}  # Invalid format
        }
        
        assert validate_operating_hours(operating_hours) is False

    def test_generate_slots_for_date_success(self):
        """Test successful slot generation"""
        venue = {
            "capacity": 10,
            "slot_duration": 60,
            "operating_hours": {
                "monday": {"open": True, "start": "09:00", "end": "12:00"}
            }
        }
        
        slots = generate_slots_for_date(venue, "2024-01-01")  # Assuming this is a Monday
        
        assert len(slots) == 3  # 9:00, 10:00, 11:00
        assert all(slot["total_capacity"] == 10 for slot in slots)
        assert all(slot["available_capacity"] == 10 for slot in slots)

    def test_generate_slots_for_closed_day(self):
        """Test slot generation for closed day"""
        venue = {
            "capacity": 10,
            "slot_duration": 60,
            "operating_hours": {
                "sunday": {"open": False}
            }
        }
        
        slots = generate_slots_for_date(venue, "2024-01-07")  # Assuming this is a Sunday
        
        assert len(slots) == 0

    def test_get_venue_slots_success(self, mock_table):
        """Test successful venue slots retrieval"""
        venue_id = "venue-123"
        venue_data = {
            "id": venue_id,
            "capacity": 10,
            "slot_duration": 60,
            "operating_hours": {
                "monday": {"open": True, "start": "09:00", "end": "12:00"}
            }
        }
        
        mock_table.get_item.return_value = {"Item": venue_data}
        
        event = {
            "queryStringParameters": {"date": "2024-01-01"}
        }
        
        response = get_venue_slots(mock_table, venue_id, event)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["venue_id"] == venue_id
        assert body["date"] == "2024-01-01"
        assert "slots" in body

    def test_get_venue_slots_missing_date(self, mock_table):
        """Test venue slots retrieval with missing date"""
        event = {"queryStringParameters": None}
        
        response = get_venue_slots(mock_table, "venue-123", event)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "Date parameter is required" in body["error"]

    def test_update_venue_slots_success(self, mock_table):
        """Test successful venue slots update"""
        venue_id = "venue-123"
        venue_data = {
            "id": venue_id,
            "capacity": 10,
            "available_slots": {}
        }
        
        mock_table.get_item.return_value = {"Item": venue_data}
        mock_table.update_item.return_value = None
        
        event = {
            "body": json.dumps({
                "date": "2024-01-01",
                "slot_time": "09:00",
                "available_capacity": 5
            })
        }
        
        response = update_venue_slots(mock_table, venue_id, event)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "updated successfully" in body["message"]

    def test_create_response_success(self):
        """Test response creation utility"""
        response = create_response(200, {"message": "Success"})
        
        assert response["statusCode"] == 200
        assert response["headers"]["Content-Type"] == "application/json"
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"
        body = json.loads(response["body"])
        assert body["message"] == "Success"

    def test_create_response_with_decimal(self):
        """Test response creation with decimal values"""
        from decimal import Decimal
        
        response = create_response(200, {"price": Decimal("29.99")})
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["price"] == 29.99

    @patch.dict("os.environ", {"VENUES_TABLE": "test-venues"})
    @patch("functions.venue_management.app.boto3")
    def test_lambda_handler_create_venue(self, mock_boto3, sample_venue_data):
        """Test lambda handler for venue creation"""
        mock_dynamodb = MagicMock()
        mock_table = MagicMock()
        mock_boto3.resource.return_value = mock_dynamodb
        mock_dynamodb.Table.return_value = mock_table
        mock_table.put_item.return_value = None
        
        event = {
            "httpMethod": "POST",
            "path": "/venues",
            "body": json.dumps(sample_venue_data)
        }
        
        response = lambda_handler(event, None)
        
        assert response["statusCode"] == 201
        body = json.loads(response["body"])
        assert body["name"] == sample_venue_data["name"]

    @patch.dict("os.environ", {"VENUES_TABLE": "test-venues"})
    @patch("functions.venue_management.app.boto3")
    def test_lambda_handler_get_venue(self, mock_boto3):
        """Test lambda handler for venue retrieval"""
        mock_dynamodb = MagicMock()
        mock_table = MagicMock()
        mock_boto3.resource.return_value = mock_dynamodb
        mock_dynamodb.Table.return_value = mock_table
        
        venue_data = {"id": "venue-123", "name": "Test Venue"}
        mock_table.get_item.return_value = {"Item": venue_data}
        
        event = {
            "httpMethod": "GET",
            "path": "/venues/venue-123",
            "pathParameters": {"id": "venue-123"}
        }
        
        response = lambda_handler(event, None)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["id"] == "venue-123"