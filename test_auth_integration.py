#!/usr/bin/env python3
"""
Integration test script for the Dog Care API with Google Authentication

This script demonstrates how to use the API with Firebase authentication.
For now, it includes placeholder functions for getting auth tokens.
"""

import requests
import json
import os
from datetime import datetime, timezone

# API Base URL - will be set after deployment
API_BASE_URL = "https://YOUR_API_GATEWAY_URL/dev"


def get_firebase_token():
    """
    Get Firebase authentication token.

    In a real application, this would involve:
    1. User login via Firebase SDK
    2. Getting the ID token from Firebase
    3. Using that token for API calls

    For testing, you can:
    1. Use Firebase Admin SDK to create custom tokens
    2. Use Firebase Auth emulator for development
    3. Create test tokens using Firebase console
    """
    # Placeholder - replace with actual token acquisition
    token = os.environ.get("FIREBASE_TEST_TOKEN", "")

    if not token:
        print("❌ No Firebase token available!")
        print(
            "Set FIREBASE_TEST_TOKEN environment variable with a valid Firebase ID token"
        )
        print("Or implement token acquisition in the get_firebase_token() function")
        return None

    return token


def make_authenticated_request(method, endpoint, data=None):
    """Make an authenticated API request"""
    token = get_firebase_token()

    if not token:
        return None

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    url = f"{API_BASE_URL}{endpoint}"

    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")

        return response
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return None


def test_owner_registration():
    """Test owner profile registration"""
    print("🧪 Testing owner registration...")

    profile_data = {
        "preferences": {
            "notifications": True,
            "marketing_emails": False,
            "preferred_communication": "email",
        }
    }

    response = make_authenticated_request("POST", "/owners/register", profile_data)

    if response and response.status_code == 201:
        print("✅ Owner registration successful")
        return response.json()
    else:
        print(
            f"❌ Owner registration failed: {
                response.status_code if response else 'No response'}"
        )
        if response:
            print(f"Response: {response.text}")
        return None


def test_owner_profile():
    """Test getting owner profile"""
    print("🧪 Testing owner profile retrieval...")

    response = make_authenticated_request("GET", "/owners/profile")

    if response and response.status_code == 200:
        print("✅ Owner profile retrieved successfully")
        return response.json()
    else:
        print(
            f"❌ Owner profile retrieval failed: {
                response.status_code if response else 'No response'}"
        )
        if response:
            print(f"Response: {response.text}")
        return None


def test_dog_registration():
    """Test dog registration"""
    print("🧪 Testing dog registration...")

    dog_data = {
        "name": "Test Dog",
        "breed": "Labrador",
        "age": 3,
        "size": "large",
        "vaccination_status": "up_to_date",
        "special_needs": ["none"],
    }

    response = make_authenticated_request("POST", "/dogs", dog_data)

    if response and response.status_code == 201:
        print("✅ Dog registration successful")
        return response.json()
    else:
        print(
            f"❌ Dog registration failed: {
                response.status_code if response else 'No response'}"
        )
        if response:
            print(f"Response: {response.text}")
        return None


def test_dog_list():
    """Test listing dogs"""
    print("🧪 Testing dog list retrieval...")

    response = make_authenticated_request("GET", "/dogs")

    if response and response.status_code == 200:
        print("✅ Dog list retrieved successfully")
        return response.json()
    else:
        print(
            f"❌ Dog list retrieval failed: {
                response.status_code if response else 'No response'}"
        )
        if response:
            print(f"Response: {response.text}")
        return None


def test_venue_list():
    """Test listing venues (should work without auth)"""
    print("🧪 Testing venue list retrieval...")

    # Note: Venue listing might not require authentication
    response = requests.get(f"{API_BASE_URL}/venues")

    if response and response.status_code == 200:
        print("✅ Venue list retrieved successfully")
        return response.json()
    else:
        print(
            f"❌ Venue list retrieval failed: {
                response.status_code if response else 'No response'}"
        )
        if response:
            print(f"Response: {response.text}")
        return None


def test_booking_creation(dog_id=None, venue_id=None):
    """Test booking creation"""
    print("🧪 Testing booking creation...")

    if not dog_id or not venue_id:
        print("❌ Need dog_id and venue_id for booking test")
        return None

    booking_data = {
        "dog_id": dog_id,
        "venue_id": venue_id,
        "service_type": "daycare",
        "start_time": "2024-12-15T09:00:00Z",
        "end_time": "2024-12-15T17:00:00Z",
        "special_instructions": "Test booking",
    }

    response = make_authenticated_request("POST", "/bookings", booking_data)

    if response and response.status_code == 201:
        print("✅ Booking creation successful")
        return response.json()
    else:
        print(
            f"❌ Booking creation failed: {
                response.status_code if response else 'No response'}"
        )
        if response:
            print(f"Response: {response.text}")
        return None


def main():
    """Run all tests"""
    print("🚀 Starting Dog Care API Authentication Tests\n")

    # Check if API URL is configured
    if "YOUR_API_GATEWAY_URL" in API_BASE_URL:
        print("❌ Please update API_BASE_URL with your actual API Gateway URL")
        return

    # Test sequence
    results = {}

    # 1. Register owner profile
    results["owner_registration"] = test_owner_registration()
    print()

    # 2. Get owner profile
    results["owner_profile"] = test_owner_profile()
    print()

    # 3. Register a dog
    results["dog_registration"] = test_dog_registration()
    print()

    # 4. List dogs
    results["dog_list"] = test_dog_list()
    print()

    # 5. List venues
    results["venue_list"] = test_venue_list()
    print()

    # 6. Create booking (if we have dog and venue)
    if (
        results["dog_registration"]
        and results["venue_list"]
        and results["venue_list"].get("venues")
    ):

        dog_id = results["dog_registration"].get("id")
        venue_id = results["venue_list"]["venues"][0].get("id")

        if dog_id and venue_id:
            results["booking_creation"] = test_booking_creation(dog_id, venue_id)

    print("\n📊 Test Summary:")
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")


if __name__ == "__main__":
    main()
