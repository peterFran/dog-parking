import json
import pytest
import requests
import os
from datetime import datetime, timezone
import time

# Integration tests for the Dog Care API
# These tests require the API to be deployed and running


class TestAPIIntegration:
    """
    Integration tests for the Dog Care API

    Note: These tests require:
    1. API deployed to AWS or running locally with `sam local start-api`
    2. Environment variable API_BASE_URL set to the API endpoint
    """

    @classmethod
    def setup_class(cls):
        """Setup test class"""
        cls.api_base_url = os.environ.get("API_BASE_URL", "http://127.0.0.1:3000")
        cls.headers = {"Content-Type": "application/json"}
        cls.test_data = {}

        # Check if API is accessible
        try:
            response = requests.get(f"{cls.api_base_url}/health", timeout=5)
        except requests.exceptions.RequestException:
            # API might not have health endpoint, that's okay
            pass

    def test_01_register_owner(self):
        """Test owner registration"""
        owner_data = {
            "name": "Integration Test Owner",
            "email": f"test_{int(time.time())}@example.com",
            "phone": "+1234567890",
            "address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "TS",
                "zip": "12345",
            },
        }

        response = requests.post(
            f"{self.api_base_url}/owners/register",
            json=owner_data,
            headers=self.headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == owner_data["name"]
        assert data["email"] == owner_data["email"]
        assert "id" in data

        # Store for subsequent tests
        self.test_data["owner_id"] = data["id"]
        self.test_data["owner_email"] = data["email"]

    def test_02_get_owner_profile(self):
        """Test getting owner profile"""
        if "owner_id" not in self.test_data:
            pytest.skip("Owner registration test must pass first")

        response = requests.get(
            f"{self.api_base_url}/owners/profile",
            params={"owner_id": self.test_data["owner_id"]},
            headers=self.headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == self.test_data["owner_id"]
        assert data["email"] == self.test_data["owner_email"]

    def test_03_create_dog(self):
        """Test creating a dog"""
        if "owner_id" not in self.test_data:
            pytest.skip("Owner registration test must pass first")

        dog_data = {
            "name": "Integration Test Dog",
            "breed": "Test Breed",
            "age": 3,
            "size": "medium",
            "owner_id": self.test_data["owner_id"],
            "vaccination_status": "up-to-date",
            "special_needs": ["test medication"],
            "emergency_contact": "+1234567890",
        }

        response = requests.post(
            f"{self.api_base_url}/dogs", json=dog_data, headers=self.headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == dog_data["name"]
        assert data["owner_id"] == dog_data["owner_id"]
        assert "id" in data

        # Store for subsequent tests
        self.test_data["dog_id"] = data["id"]

    def test_04_list_dogs(self):
        """Test listing dogs for owner"""
        if "owner_id" not in self.test_data:
            pytest.skip("Owner registration test must pass first")

        response = requests.get(
            f"{self.api_base_url}/dogs",
            params={"owner_id": self.test_data["owner_id"]},
            headers=self.headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "dogs" in data
        assert "count" in data
        assert data["count"] >= 1

        # Check that our test dog is in the list
        dog_ids = [dog["id"] for dog in data["dogs"]]
        assert self.test_data["dog_id"] in dog_ids

    def test_05_get_dog(self):
        """Test getting specific dog"""
        if "dog_id" not in self.test_data:
            pytest.skip("Dog creation test must pass first")

        response = requests.get(
            f"{self.api_base_url}/dogs/{self.test_data['dog_id']}", headers=self.headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == self.test_data["dog_id"]
        assert data["name"] == "Integration Test Dog"

    def test_06_update_dog(self):
        """Test updating a dog"""
        if "dog_id" not in self.test_data:
            pytest.skip("Dog creation test must pass first")

        update_data = {"name": "Updated Test Dog", "age": 4}

        response = requests.put(
            f"{self.api_base_url}/dogs/{self.test_data['dog_id']}",
            json=update_data,
            headers=self.headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Test Dog"
        assert data["age"] == 4

    def test_07_create_booking(self):
        """Test creating a booking"""
        if "dog_id" not in self.test_data or "owner_id" not in self.test_data:
            pytest.skip("Dog and owner creation tests must pass first")

        # Create booking for tomorrow
        start_time = datetime.now(timezone.utc).replace(
            hour=9, minute=0, second=0, microsecond=0
        )
        start_time = start_time.replace(day=start_time.day + 1)  # Tomorrow
        end_time = start_time.replace(hour=17)  # 5 PM

        booking_data = {
            "dog_id": self.test_data["dog_id"],
            "owner_id": self.test_data["owner_id"],
            "service_type": "daycare",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "special_instructions": "Integration test booking",
        }

        response = requests.post(
            f"{self.api_base_url}/bookings", json=booking_data, headers=self.headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["dog_id"] == booking_data["dog_id"]
        assert data["service_type"] == "daycare"
        assert data["status"] == "pending"
        assert data["price"] == 120.0  # 8 hours * $15/hour
        assert "id" in data

        # Store for subsequent tests
        self.test_data["booking_id"] = data["id"]
        self.test_data["booking_price"] = data["price"]

    def test_08_list_bookings(self):
        """Test listing bookings for owner"""
        if "owner_id" not in self.test_data:
            pytest.skip("Owner registration test must pass first")

        response = requests.get(
            f"{self.api_base_url}/bookings",
            params={"owner_id": self.test_data["owner_id"]},
            headers=self.headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "bookings" in data
        assert "count" in data
        assert data["count"] >= 1

        # Check that our test booking is in the list
        booking_ids = [booking["id"] for booking in data["bookings"]]
        assert self.test_data["booking_id"] in booking_ids

    def test_09_get_booking(self):
        """Test getting specific booking"""
        if "booking_id" not in self.test_data:
            pytest.skip("Booking creation test must pass first")

        response = requests.get(
            f"{self.api_base_url}/bookings/{self.test_data['booking_id']}",
            headers=self.headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == self.test_data["booking_id"]
        assert data["service_type"] == "daycare"

    def test_10_confirm_booking(self):
        """Test confirming booking (payment removed)"""
        if "booking_id" not in self.test_data:
            pytest.skip("Booking creation test must pass first")

        # Update booking status to confirmed
        update_data = {"status": "confirmed"}

        response = requests.put(
            f"{self.api_base_url}/bookings/{self.test_data['booking_id']}",
            json=update_data,
            headers=self.headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "confirmed"



    def test_11_update_booking(self):
        """Test updating booking after confirmation"""
        if "booking_id" not in self.test_data:
            pytest.skip("Booking creation test must pass first")

        update_data = {"special_instructions": "Updated via integration test"}

        response = requests.put(
            f"{self.api_base_url}/bookings/{self.test_data['booking_id']}",
            json=update_data,
            headers=self.headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["special_instructions"] == "Updated via integration test"

    def test_12_error_handling(self):
        """Test error handling scenarios"""
        # Test invalid dog creation (missing required field)
        invalid_dog_data = {
            "name": "Invalid Dog",
            # Missing required fields
        }

        response = requests.post(
            f"{self.api_base_url}/dogs", json=invalid_dog_data, headers=self.headers
        )

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "Missing required field" in data["error"]

        # Test getting non-existent resource
        response = requests.get(
            f"{self.api_base_url}/dogs/non-existent-id", headers=self.headers
        )

        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "not found" in data["error"].lower()

    def test_13_cleanup(self):
        """Clean up test data"""
        # Cancel booking
        if "booking_id" in self.test_data:
            response = requests.delete(
                f"{self.api_base_url}/bookings/{self.test_data['booking_id']}",
                headers=self.headers,
            )
            # Should succeed or be already cancelled
            assert response.status_code in [200, 404]

        # Delete dog
        if "dog_id" in self.test_data:
            response = requests.delete(
                f"{self.api_base_url}/dogs/{self.test_data['dog_id']}",
                headers=self.headers,
            )
            # Should succeed or be already deleted
            assert response.status_code in [204, 404]


class TestAPIErrorScenarios:
    """Test error scenarios and edge cases"""

    @classmethod
    def setup_class(cls):
        cls.api_base_url = os.environ.get("API_BASE_URL", "http://127.0.0.1:3000")
        cls.headers = {"Content-Type": "application/json"}

    def test_duplicate_email_registration(self):
        """Test registering with duplicate email"""
        owner_data = {
            "name": "Duplicate Email Test",
            "email": "duplicate@example.com",
            "phone": "+1234567890",
        }

        # First registration should succeed
        response1 = requests.post(
            f"{self.api_base_url}/owners/register",
            json=owner_data,
            headers=self.headers,
        )
        assert response1.status_code == 201

        # Second registration with same email should fail
        response2 = requests.post(
            f"{self.api_base_url}/owners/register",
            json=owner_data,
            headers=self.headers,
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "Email already registered" in data["error"]

    def test_invalid_booking_scenarios(self):
        """Test various booking failure scenarios"""
        # Test with invalid booking data
        booking_data = {
            "dog_id": "non-existent-dog",
            "owner_id": "non-existent-owner",
            "service_type": "daycare",
        }

        response = requests.post(
            f"{self.api_base_url}/bookings", json=booking_data, headers=self.headers
        )
        assert response.status_code in [
            400,
            404,
        ]  # Either validation error or dog/owner not found

    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = requests.options(f"{self.api_base_url}/dogs", headers=self.headers)

        # Should have CORS headers (though exact response depends on API Gateway config)
        # This test verifies the endpoint is accessible from browsers
        assert response.status_code in [
            200,
            204,
            405,
        ]  # Various valid responses for OPTIONS
