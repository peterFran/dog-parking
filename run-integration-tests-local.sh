#!/bin/bash

# Local Integration Test Runner with Firebase Emulator
# This script helps developers run integration tests locally against Firebase emulator

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Dog Care App - Local Integration Test Runner${NC}"
echo "================================================"

# Configuration
API_BASE_URL=${API_BASE_URL:-"http://127.0.0.1:3000"}
FIREBASE_PROJECT_ID=${FIREBASE_PROJECT_ID:-"demo-dog-care"}
FIREBASE_AUTH_EMULATOR_HOST=${FIREBASE_AUTH_EMULATOR_HOST:-"localhost:9099"}

echo -e "${BLUE}📋 Configuration:${NC}"
echo "  API Base URL: $API_BASE_URL"
echo "  Firebase Project ID: $FIREBASE_PROJECT_ID"
echo "  Firebase Emulator Host: $FIREBASE_AUTH_EMULATOR_HOST"
echo ""

# Check if Firebase CLI is installed
if ! command -v firebase &> /dev/null; then
    echo -e "${RED}❌ Firebase CLI not found${NC}"
    echo "Please install Firebase CLI: npm install -g firebase-tools"
    exit 1
fi

# Check if API is running (if local)
if [[ "$API_BASE_URL" == "http://127.0.0.1:3000" ]]; then
    echo -e "${YELLOW}🔍 Checking if local API is running...${NC}"
    if ! curl -s "$API_BASE_URL/venues" > /dev/null 2>&1; then
        echo -e "${RED}❌ Local API not running at $API_BASE_URL${NC}"
        echo "Please start the API first:"
        echo "  sam local start-api"
        exit 1
    fi
    echo -e "${GREEN}✅ Local API is running${NC}"
fi

# Start Firebase emulator in background
echo -e "${YELLOW}🔥 Starting Firebase Auth emulator...${NC}"
firebase emulators:start --only auth --project "$FIREBASE_PROJECT_ID" &
FIREBASE_PID=$!

# Function to cleanup
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"
    if [[ ! -z "$FIREBASE_PID" ]]; then
        kill $FIREBASE_PID 2>/dev/null || true
    fi
    # Kill any remaining Firebase processes
    pkill -f "firebase emulators" 2>/dev/null || true
}

# Set trap to cleanup on exit
trap cleanup EXIT

# Wait for Firebase emulator to start
echo -e "${YELLOW}⏳ Waiting for Firebase emulator to start...${NC}"
timeout 60 bash -c "until curl -s http://$FIREBASE_AUTH_EMULATOR_HOST/ > /dev/null 2>&1; do sleep 2; done"
echo -e "${GREEN}✅ Firebase emulator is ready${NC}"

# Set environment variables for tests
export API_BASE_URL="$API_BASE_URL"
export FIREBASE_PROJECT_ID="$FIREBASE_PROJECT_ID"
export FIREBASE_AUTH_EMULATOR_HOST="$FIREBASE_AUTH_EMULATOR_HOST"

# Run integration tests
echo -e "${BLUE}🧪 Running integration tests...${NC}"
echo "Environment variables:"
echo "  API_BASE_URL=$API_BASE_URL"
echo "  FIREBASE_PROJECT_ID=$FIREBASE_PROJECT_ID"
echo "  FIREBASE_AUTH_EMULATOR_HOST=$FIREBASE_AUTH_EMULATOR_HOST"
echo ""

if python -m pytest tests/integration/test_api_with_firebase_emulator.py -v --tb=short; then
    echo -e "${GREEN}✅ Integration tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Integration tests failed!${NC}"
    exit 1
fi