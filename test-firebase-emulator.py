#!/usr/bin/env python3
"""
Simple test script to verify Firebase Auth emulator setup
Run this to test the emulator without the full integration test suite
"""

import requests
import json
import os


def test_firebase_emulator():
    """Test Firebase Auth emulator basic functionality"""

    emulator_host = os.environ.get("FIREBASE_AUTH_EMULATOR_HOST", "localhost:9099")
    api_key = "fake-api-key"

    print(f"🔥 Testing Firebase Auth emulator at: {emulator_host}")

    # Test 1: Check if emulator is running
    try:
        response = requests.get(f"http://{emulator_host}/", timeout=5)
        print("✅ Firebase emulator is running")
    except requests.exceptions.RequestException as e:
        print(f"❌ Firebase emulator not accessible: {e}")
        print("💡 Start it with: firebase emulators:start --only auth")
        return False

    # Test 2: Create test user
    print("\n🧪 Creating test user...")
    signup_url = f"http://{emulator_host}/identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}"

    user_data = {
        "email": "test@example.com",
        "password": "password123",
        "returnSecureToken": True,
    }

    response = requests.post(signup_url, json=user_data)

    if response.status_code == 200:
        user_info = response.json()
        print("✅ Test user created successfully")
        print(f"   User ID: {user_info.get('localId')}")
        local_id = user_info.get("localId")
    else:
        print(f"❌ Failed to create user: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

    # Test 3: Verify user email
    print("\n📧 Verifying user email...")
    verify_url = f"http://{emulator_host}/identitytoolkit.googleapis.com/v1/accounts:update?key={api_key}"

    verify_data = {"localId": local_id, "emailVerified": True}

    response = requests.post(verify_url, json=verify_data)

    if response.status_code == 200:
        print("✅ Email verified successfully")
    else:
        print(f"❌ Failed to verify email: {response.status_code}")

    # Test 4: Sign in and get ID token
    print("\n🔑 Signing in user...")
    signin_url = f"http://{emulator_host}/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"

    signin_data = {
        "email": "test@example.com",
        "password": "password123",
        "returnSecureToken": True,
    }

    response = requests.post(signin_url, json=signin_data)

    if response.status_code == 200:
        signin_info = response.json()
        id_token = signin_info.get("idToken")
        print("✅ User signed in successfully")
        print(f"   ID Token (first 50 chars): {id_token[:50]}...")

        # Test 5: Verify the token format
        try:
            import base64

            # JWT tokens have 3 parts separated by dots
            parts = id_token.split(".")
            if len(parts) == 3:
                # Decode header (add padding if needed)
                header_b64 = parts[0]
                header_b64 += "=" * (4 - len(header_b64) % 4)  # Add padding
                header = json.loads(base64.b64decode(header_b64))
                print(f"   Token header: {header}")

                # Decode payload (add padding if needed)
                payload_b64 = parts[1]
                payload_b64 += "=" * (4 - len(payload_b64) % 4)  # Add padding
                payload = json.loads(base64.b64decode(payload_b64))
                print(
                    f"   Token payload (user): {payload.get('user_id')} / {payload.get('sub')}"
                )
                print(f"   Email verified: {payload.get('email_verified')}")
                print("✅ Token format is valid")
            else:
                print("⚠️  Token doesn't appear to be JWT format")
        except Exception as e:
            print(f"⚠️  Could not decode token: {e}")

        return True
    else:
        print(f"❌ Failed to sign in: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def test_api_with_token():
    """Test the API with Firebase emulator token"""

    api_base_url = os.environ.get("API_BASE_URL", "http://127.0.0.1:3000")

    print(f"\n🚀 Testing API at: {api_base_url}")

    # Check if API is available
    try:
        response = requests.get(f"{api_base_url}/venues", timeout=5)
        print("✅ API is accessible")
    except requests.exceptions.RequestException as e:
        print(f"❌ API not accessible: {e}")
        print("💡 Start it with: sam local start-api")
        return False

    # Get Firebase token
    emulator_host = os.environ.get("FIREBASE_AUTH_EMULATOR_HOST", "localhost:9099")
    signin_url = f"http://{emulator_host}/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=fake-api-key"

    signin_data = {
        "email": "test@example.com",
        "password": "password123",
        "returnSecureToken": True,
    }

    response = requests.post(signin_url, json=signin_data)

    if response.status_code != 200:
        print("❌ Could not get Firebase token")
        return False

    id_token = response.json().get("idToken")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {id_token}",
    }

    # Test authenticated endpoint
    print("🧪 Testing authenticated endpoint...")
    response = requests.get(f"{api_base_url}/owners/profile", headers=headers)

    print(f"   Response status: {response.status_code}")
    print(f"   Response body: {response.text}")

    if response.status_code in [200, 401]:
        print("✅ API is responding to authenticated requests")
        return True
    else:
        print("❌ Unexpected API response")
        return False


if __name__ == "__main__":
    print("🔥 Firebase Auth Emulator Test")
    print("=" * 40)

    # Set default environment variables
    os.environ.setdefault("FIREBASE_AUTH_EMULATOR_HOST", "localhost:9099")
    os.environ.setdefault("API_BASE_URL", "http://127.0.0.1:3000")

    success = test_firebase_emulator()

    if success:
        test_api_with_token()

    print("\n" + "=" * 40)
    if success:
        print("🎉 Firebase emulator setup looks good!")
        print("💡 You can now run the full integration tests with:")
        print("   ./start-emulator-tests.sh")
    else:
        print("❌ Firebase emulator setup needs attention")
        print("💡 Make sure to start the emulator with:")
        print("   firebase emulators:start --only auth")
