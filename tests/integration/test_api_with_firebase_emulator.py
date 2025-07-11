#!/usr/bin/env python3
"""
Integration tests using Firebase Auth emulator for authentication
"""

import json
import pytest
import requests
import os
import time
from datetime import datetime, timezone


class FirebaseEmulatorAuth:
    """Helper class for Firebase Auth emulator operations"""
    
    def __init__(self):
        self.emulator_host = os.environ.get('FIREBASE_AUTH_EMULATOR_HOST', 'localhost:9099')
        self.project_id = 'demo-dog-care'
        self.api_key = 'fake-api-key'  # Emulator accepts any API key
    
    def create_test_user(self, email="test@example.com", password="password123", email_verified=True):
        """Create a test user in Firebase emulator"""
        url = f"http://{self.emulator_host}/identitytoolkit.googleapis.com/v1/accounts:signUp?key={self.api_key}"
        
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Failed to create user: {response.text}")
        
        user_data = response.json()
        
        # Set email verification status if needed
        if email_verified:
            self.verify_user_email(user_data['localId'])
        
        return user_data
    
    def verify_user_email(self, local_id):
        """Mark user email as verified in emulator"""
        url = f"http://{self.emulator_host}/identitytoolkit.googleapis.com/v1/accounts:update?key={self.api_key}"
        
        payload = {
            "localId": local_id,
            "emailVerified": True
        }
        
        response = requests.post(url, json=payload)
        return response.json()
    
    def sign_in_user(self, email, password):
        """Sign in user and get ID token"""
        url = f"http://{self.emulator_host}/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}"
        
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Failed to sign in: {response.text}")
        
        return response.json().get('idToken')
    
    def delete_user(self, id_token):
        """Delete user from emulator"""
        url = f"http://{self.emulator_host}/identitytoolkit.googleapis.com/v1/accounts:delete?key={self.api_key}"
        
        payload = {
            "idToken": id_token
        }
        
        response = requests.post(url, json=payload)
        return response.status_code == 200


def is_firebase_emulator_running():
    """Check if Firebase Auth emulator is running"""
    try:
        emulator_host = os.environ.get('FIREBASE_AUTH_EMULATOR_HOST', 'localhost:9099')
        response = requests.get(f"http://{emulator_host}/", timeout=2)
        return True
    except requests.exceptions.RequestException:
        return False


def is_api_available():
    """Check if the API is available for integration testing"""
    api_base_url = os.environ.get("API_BASE_URL", "http://127.0.0.1:3000")
    
    try:
        # Try venues endpoint (public)
        response = requests.get(f"{api_base_url}/venues", timeout=2)
        return True
    except requests.exceptions.RequestException:
        return False


# Skip all tests if emulator or API is not available
pytestmark = pytest.mark.skipif(
    not is_firebase_emulator_running() or not is_api_available(),
    reason="Firebase Auth emulator or API not available. Start with: firebase emulators:start --only auth"
)


class TestAPIWithFirebaseEmulator:
    """
    Integration tests using Firebase Auth emulator
    
    Prerequisites:
    1. Firebase emulator running: firebase emulators:start --only auth
    2. API running locally: sam local start-api
    3. Environment variables:
       - FIREBASE_AUTH_EMULATOR_HOST=localhost:9099
       - API_BASE_URL=http://127.0.0.1:3000
    """
    
    @classmethod
    def setup_class(cls):
        """Setup test class with Firebase emulator auth"""
        cls.firebase_auth = FirebaseEmulatorAuth()
        cls.api_base_url = os.environ.get("API_BASE_URL", "http://127.0.0.1:3000")
        cls.test_data = {}
        
        # Create test user
        cls.test_email = f"test_{int(time.time())}@example.com"
        cls.test_password = "password123"
        
        print(f"Creating test user: {cls.test_email}")
        cls.user_data = cls.firebase_auth.create_test_user(
            email=cls.test_email,
            password=cls.test_password,
            email_verified=True
        )
        
        # Get auth token
        cls.auth_token = cls.firebase_auth.sign_in_user(cls.test_email, cls.test_password)
        
        # Set up headers
        cls.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cls.auth_token}"
        }
        
        print(f"Auth token obtained: {cls.auth_token[:20]}...")
    
    @classmethod
    def teardown_class(cls):
        """Clean up test user"""
        try:
            cls.firebase_auth.delete_user(cls.auth_token)
            print(f"Cleaned up test user: {cls.test_email}")
        except Exception as e:
            print(f"Warning: Could not clean up test user: {e}")
    
    def test_01_auth_required_endpoints_reject_unauthenticated(self):
        """Test that protected endpoints require authentication"""
        endpoints = [
            "/owners/register",
            "/owners/profile", 
            "/dogs",
            "/bookings"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{self.api_base_url}{endpoint}")
            assert response.status_code == 401, f"Endpoint {endpoint} should require auth"
            data = response.json()
            assert "Missing authentication token" in data.get("error", "")
    
    def test_02_register_owner_profile(self):
        """Test owner profile registration with auth"""
        owner_data = {
            "preferences": {
                "notifications": True,
                "marketing_emails": False,
                "preferred_communication": "email"
            }
        }
        
        response = requests.post(
            f"{self.api_base_url}/owners/register",
            json=owner_data,
            headers=self.headers
        )
        
        print(f"Owner registration response: {response.status_code}")
        print(f"Response body: {response.text}")
        
        assert response.status_code == 201
        data = response.json()
        assert "user_id" in data
        assert data["preferences"]["notifications"] == True
        
        # Store for subsequent tests
        self.test_data["user_id"] = data["user_id"]
    
    def test_03_get_owner_profile(self):
        """Test getting owner profile"""
        response = requests.get(
            f"{self.api_base_url}/owners/profile",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "preferences" in data
    
    def test_04_create_dog(self):
        """Test creating a dog with authentication"""
        dog_data = {
            "name": "Firebase Test Dog",
            "breed": "Emulator Retriever",
            "age": 3,
            "size": "medium",
            "vaccination_status": "up-to-date",
            "special_needs": ["testing"],
            "emergency_contact": "+1234567890"
        }
        
        response = requests.post(
            f"{self.api_base_url}/dogs",
            json=dog_data,
            headers=self.headers
        )
        
        print(f"Dog creation response: {response.status_code}")
        print(f"Response body: {response.text}")
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == dog_data["name"]
        assert "id" in data
        
        # Store for subsequent tests
        self.test_data["dog_id"] = data["id"]
    
    def test_05_list_dogs(self):
        """Test listing dogs for authenticated user"""
        response = requests.get(
            f"{self.api_base_url}/dogs",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "dogs" in data
        assert "count" in data
        assert data["count"] >= 1
        
        # Check that our test dog is in the list
        dog_ids = [dog["id"] for dog in data["dogs"]]
        assert self.test_data["dog_id"] in dog_ids
    
    def test_06_get_specific_dog(self):
        """Test getting specific dog details"""
        if "dog_id" not in self.test_data:
            pytest.skip("Dog creation test must pass first")
        
        response = requests.get(
            f"{self.api_base_url}/dogs/{self.test_data['dog_id']}",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == self.test_data["dog_id"]
        assert data["name"] == "Firebase Test Dog"
    
    def test_07_create_booking(self):
        """Test creating a booking with authentication"""
        if "dog_id" not in self.test_data:
            pytest.skip("Dog creation test must pass first")
        
        # First, get available venues
        venues_response = requests.get(f"{self.api_base_url}/venues")
        
        if venues_response.status_code != 200:
            pytest.skip("No venues available for booking test")
        
        venues_data = venues_response.json()
        if not venues_data.get("venues"):
            pytest.skip("No venues available for booking test")
        
        venue_id = venues_data["venues"][0]["id"]
        
        # Create booking for tomorrow
        start_time = datetime.now(timezone.utc).replace(
            hour=9, minute=0, second=0, microsecond=0
        )
        start_time = start_time.replace(day=start_time.day + 1)  # Tomorrow
        end_time = start_time.replace(hour=17)  # 5 PM
        
        booking_data = {
            "dog_id": self.test_data["dog_id"],
            "venue_id": venue_id,
            "service_type": "daycare",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "special_instructions": "Firebase emulator test booking"
        }
        
        response = requests.post(
            f"{self.api_base_url}/bookings",
            json=booking_data,
            headers=self.headers
        )
        
        print(f"Booking creation response: {response.status_code}")
        print(f"Response body: {response.text}")
        
        assert response.status_code == 201
        data = response.json()
        assert data["dog_id"] == booking_data["dog_id"]
        assert data["service_type"] == "daycare"
        assert data["status"] == "pending"
        assert "id" in data
        
        # Store for subsequent tests
        self.test_data["booking_id"] = data["id"]
    
    def test_08_list_bookings(self):
        """Test listing bookings for authenticated user"""
        response = requests.get(
            f"{self.api_base_url}/bookings",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "bookings" in data
        assert "count" in data
        
        if "booking_id" in self.test_data:
            booking_ids = [booking["id"] for booking in data["bookings"]]
            assert self.test_data["booking_id"] in booking_ids
    
    def test_09_unauthorized_access_to_other_users_data(self):
        """Test that users cannot access other users' data"""
        # Create second user
        second_email = f"test2_{int(time.time())}@example.com"
        second_user = self.firebase_auth.create_test_user(
            email=second_email,
            password="password123",
            email_verified=True
        )
        second_token = self.firebase_auth.sign_in_user(second_email, "password123")
        
        second_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {second_token}"
        }
        
        # Try to access first user's dog with second user's token
        if "dog_id" in self.test_data:
            response = requests.get(
                f"{self.api_base_url}/dogs/{self.test_data['dog_id']}",
                headers=second_headers
            )
            
            assert response.status_code == 403  # Should be forbidden
            data = response.json()
            assert "Access denied" in data.get("error", "")
        
        # Clean up second user
        self.firebase_auth.delete_user(second_token)
    
    def test_10_venues_public_access(self):
        """Test that venues are accessible without authentication"""
        response = requests.get(f"{self.api_base_url}/venues")
        
        # Should work without auth token
        assert response.status_code == 200
        data = response.json()
        assert "venues" in data


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])