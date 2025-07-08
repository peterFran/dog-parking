#!/bin/bash

# Test script for the Dog Care API
# Works with either SAM Local (port 3000) or Simple Server (port 8080)

API_BASE=${1:-"http://localhost:3000"}

echo "🧪 Testing Dog Care API at $API_BASE"
echo "===================================="

# Test 1: Register a new owner
echo "1️⃣  Registering a new owner..."
OWNER_RESPONSE=$(curl -s -X POST "$API_BASE/owners/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890"
  }')

echo "Response: $OWNER_RESPONSE"
OWNER_ID=$(echo $OWNER_RESPONSE | jq -r '.id')
echo "Owner ID: $OWNER_ID"
echo ""

# Test 2: Register a dog
echo "2️⃣  Registering a dog..."
DOG_RESPONSE=$(curl -s -X POST "$API_BASE/dogs" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Buddy\",
    \"breed\": \"Golden Retriever\",
    \"age\": 3,
    \"size\": \"large\",
    \"owner_id\": \"$OWNER_ID\"
  }")

echo "Response: $DOG_RESPONSE"
DOG_ID=$(echo $DOG_RESPONSE | jq -r '.id')
echo "Dog ID: $DOG_ID"
echo ""

# Test 3: Create a booking
echo "3️⃣  Creating a booking..."
BOOKING_RESPONSE=$(curl -s -X POST "$API_BASE/bookings" \
  -H "Content-Type: application/json" \
  -d "{
    \"dog_id\": \"$DOG_ID\",
    \"owner_id\": \"$OWNER_ID\",
    \"service_type\": \"daycare\",
    \"start_time\": \"2024-12-01T09:00:00Z\",
    \"end_time\": \"2024-12-01T17:00:00Z\",
    \"special_instructions\": \"Feed at 12pm\"
  }")

echo "Response: $BOOKING_RESPONSE"
BOOKING_ID=$(echo $BOOKING_RESPONSE | jq -r '.id')
echo "Booking ID: $BOOKING_ID"
echo ""

# Test 4: Process payment
echo "4️⃣  Processing payment..."
PAYMENT_RESPONSE=$(curl -s -X POST "$API_BASE/payments" \
  -H "Content-Type: application/json" \
  -d "{
    \"booking_id\": \"$BOOKING_ID\",
    \"amount\": 120.00,
    \"payment_method\": \"credit_card\",
    \"payment_token\": \"test_success\"
  }")

echo "Response: $PAYMENT_RESPONSE"
echo ""

echo "✅ API tests completed!"
echo ""
echo "💡 Tips:"
echo "  - Use 'jq' to format JSON responses: curl ... | jq ."
echo "  - Check the logs in your SAM Local terminal for debugging"
echo "  - Payment tokens: 'test_success', 'test_decline', 'test_insufficient_funds'"